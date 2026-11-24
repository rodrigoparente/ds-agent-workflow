#!/usr/bin/env python3
"""Unit tests for .agents/hooks/, .agents/tools/, and .agents/skills/ scripts."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agents" / "hooks"))
sys.path.insert(0, str(ROOT / ".agents" / "tools"))
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "research" / "scripts"))
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "presentation" / "scripts"))

import check_notebook  # noqa: E402
import common  # noqa: E402
import export_docx  # noqa: E402
import lint  # noqa: E402
import nb_summary  # noqa: E402
import papers  # noqa: E402
import session_start  # noqa: E402
import stop_tests  # noqa: E402


def test_common_payloads_and_emitters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    agy_cli = {
        "workspacePaths": [str(ROOT)],
        "terminationReason": "USER_CANCELED",
        "toolCall": {"name": "edit_file", "args": {"Path": "scripts/helpers.py"}},
    }
    ctx_cli = common.parse_payload(io.StringIO(json.dumps(agy_cli)))
    assert ctx_cli.agent == "antigravity"
    assert ctx_cli.rel_path() == "scripts/helpers.py"
    assert ctx_cli.termination_reason == "USER_CANCELED"

    agy_ide = {
        "workspacePaths": [str(ROOT)],
        "toolCall": {"name": "replace_file_content", "args": {"TargetFile": "scripts/helpers.py"}},
    }
    assert common.parse_payload(io.StringIO(json.dumps(agy_ide))).rel_path() == "scripts/helpers.py"

    claude = {"tool_name": "Edit", "tool_input": {"file_path": "scripts/helpers.py"}}
    ctx_claude = common.parse_payload(io.StringIO(json.dumps(claude)))
    assert ctx_claude.agent == "claude" and ctx_claude.rel_path() == "scripts/helpers.py"

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "env_dir"))
    assert common._detect_root({"workspacePaths": [str(tmp_path / "ws")]}) == (tmp_path / "ws")
    assert common._detect_root({}) == (tmp_path / "env_dir").resolve()

    tools = [
        tmp_path / ".venv" / "bin" / "ruff",
        tmp_path / "venv" / "bin" / "ruff",
        tmp_path / "active_env" / "bin" / "ruff",
    ]
    for p in tools:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("#!/bin/sh\n")
    monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path / "active_env"))
    monkeypatch.setattr(common.shutil, "which", lambda _n: "/usr/bin/ruff")
    for p in tools:
        assert common.find_project_tool(tmp_path, "ruff") == str(p)
        p.unlink()
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    assert common.find_project_tool(tmp_path, "ruff") == "/usr/bin/ruff"
    monkeypatch.setattr(common.shutil, "which", lambda _n: None)
    assert common.find_project_tool(tmp_path, "ruff") is None

    for fn, ctx, args, exp_code in (
        (common.emit_post_tool_feedback, common.HookContext("antigravity", ROOT), ("err",), 0),
        (common.emit_post_tool_feedback, common.HookContext("claude", ROOT), ("err",), 2),
        (common.emit_stop_decision, common.HookContext("antigravity", ROOT), (True, "fix"), 0),
        (common.emit_stop_decision, common.HookContext("claude", ROOT), (True, "fix"), 2),
        (common.emit_session_start, common.HookContext("antigravity", ROOT), ("hello",), 0),
    ):
        with pytest.raises(SystemExit) as exc:
            fn(ctx, *args)
        assert exc.value.code == exp_code
    out = capsys.readouterr().out
    assert '"decision": "continue"' in out and '"injectSteps"' in out


def test_session_start_summary_and_warnings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "01-eda.md").write_text("# 01\nStatus: executed\n")
    (specs / "02-baseline.md").write_text("# 02\nStatus: approved\n")
    monkeypatch.setattr(session_start, "find_project_tool", lambda _r, tool: f"/venv/{tool}")
    summary = session_start.build_context_summary(tmp_path)
    assert "01-eda (executed)" in summary and "02-baseline (approved)" in summary
    assert "Context:" not in summary and "`03-`" in summary and "Warning:" not in summary

    (specs / "context.md").write_text("# Project Context\n")
    with_ctx = session_start.build_context_summary(tmp_path)
    assert "context (unknown)" not in with_ctx and "Context: `specs/context.md`" in with_ctx

    monkeypatch.setattr(session_start, "find_project_tool", lambda _r, _t: None)
    missing = session_start.build_context_summary(tmp_path)
    assert "Warning: missing workspace tools" in missing and "uv sync" in missing


def test_lint_routing_and_early_stop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "README.md").write_text("# hi\n")
    assert lint.check_edited_file(common.HookContext("claude", tmp_path, "README.md")) == ""

    py_file = tmp_path / "scripts" / "helpers.py"
    py_file.parent.mkdir(parents=True)
    py_file.write_text("x = 1\n")
    calls: list[tuple[str, ...]] = []

    class Res:
        returncode, stdout, stderr = 0, "", ""

    monkeypatch.setattr(
        lint, "run_project_tool", lambda _r, *a, **_kw: calls.append(a) or Res()
    )
    err0 = lint.check_edited_file(common.HookContext("claude", tmp_path, "scripts/helpers.py"))
    assert err0 == ""
    assert [c[:2] for c in calls] == [("ruff", "format"), ("ruff", "check")]

    calls.clear()
    Res.returncode, Res.stderr = 2, "syntax error"
    err = lint.check_edited_file(common.HookContext("claude", tmp_path, "scripts/helpers.py"))
    assert "ruff format:" in err and len(calls) == 1


def test_stop_tests_routing_and_antigravity_lint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("def test_ok(): pass\n")
    (tmp_path / ".agents" / "hooks").mkdir(parents=True)
    (tmp_path / ".agents" / "hooks" / "test_hooks.py").write_text("def test_ok(): pass\n")
    assert stop_tests.check_tests_on_stop(common.HookContext("claude", tmp_path)) == (False, "")

    canceled = common.HookContext("antigravity", tmp_path, termination_reason="USER_CANCELED")
    assert stop_tests.check_tests_on_stop(canceled) == (False, "")

    called: list[tuple[str, ...]] = []

    class FakeRun:
        def __init__(self, rc: int, out: str = "") -> None:
            self.returncode, self.stdout, self.stderr = rc, out, ""

    monkeypatch.setattr(stop_tests, "_changed_python_paths", lambda _r: ["scripts/a.py"])
    monkeypatch.setattr(
        stop_tests, "run_project_tool", lambda _r, *a, **_kw: called.append(a) or FakeRun(1, "fail")
    )
    cont, reason = stop_tests.check_tests_on_stop(common.HookContext("claude", tmp_path))
    assert cont is True and "Unit tests failed" in reason
    assert called == [("pytest", "-x", "-q", "tests")]

    called.clear()
    monkeypatch.setattr(
        stop_tests,
        "_changed_python_paths",
        lambda _r: [".agents/skills/presentation/scripts/deck.py"],
    )
    monkeypatch.setattr(
        stop_tests, "run_project_tool", lambda _r, *a, **_kw: called.append(a) or FakeRun(0)
    )
    assert stop_tests.check_tests_on_stop(common.HookContext("claude", tmp_path)) == (False, "")
    assert called == [("pytest", "-x", "-q", ".agents/hooks/test_hooks.py")]

    # Notebook-only change skips pytest in Claude Code
    (tmp_path / ".git").mkdir()
    monkeypatch.undo()
    monkeypatch.setattr(
        common.shutil, "which", lambda name: "/usr/bin/git" if name == "git" else None
    )
    monkeypatch.setattr(
        common.subprocess, "run", lambda *_a, **_kw: FakeRun(0, " M notebooks/py/01-eda.py\n")
    )
    assert stop_tests.check_tests_on_stop(common.HookContext("claude", tmp_path)) == (False, "")

    # Antigravity catches unresolved lint/notebook issues on Stop and passes once clean
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "a.py").write_text("x = 1\n")
    monkeypatch.setattr(stop_tests, "_changed_python_paths", lambda _r: ["scripts/a.py"])
    monkeypatch.setattr(stop_tests, "find_project_tool", lambda _r, _t: "/venv/ruff")
    monkeypatch.setattr(stop_tests, "check_edited_file", lambda _c: "Lint issues in scripts/a.py")
    cont_agy, msg_agy = stop_tests.check_tests_on_stop(common.HookContext("antigravity", tmp_path))
    assert cont_agy is True and "Fix lint/notebook issues" in msg_agy

    monkeypatch.setattr(stop_tests, "check_edited_file", lambda _c: "")
    monkeypatch.setattr(stop_tests, "run_project_tool", lambda _r, *a, **_kw: FakeRun(0))
    agy_ok = stop_tests.check_tests_on_stop(common.HookContext("antigravity", tmp_path))
    assert agy_ok == (False, "")


def test_check_notebook_rules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    skel = ROOT / ".agents" / "skills" / "code" / "assets" / "skeleton.py"
    assert check_notebook.problems_in(skel.read_text(encoding="utf-8")) == []

    # try/except and consecutive code cells are permitted
    clean = (
        "# %% [markdown]\n# # Title\n# %%\n# # %pip install -q pandas\n"
        "# %%\nimport pandas as pd\n# %%\ntry:\n    x = 1\nexcept ValueError:\n    x = 2\n"
    )
    assert check_notebook.problems_in(clean, "notebooks/py/01-ok.py") == []

    dists = {"custom_mod": ["custom-pkg"], "sklearn": ["scikit-learn"]}
    monkeypatch.setattr(check_notebook, "_dist_map", lambda: dists)
    bad = (
        "# %% [markdown]\n# # Title\n# %%\n# %pip install -q pandas\n"
        "# %%\nimport custom_mod\nimport sklearn.metrics\nimport pandas as pd\n"
        "class Foo:\n    pass\n"
        'pd.DataFrame().to_excel("out.xlsx")\n'
        'fig.write_image("x.png")\n'
        'Path("models").mkdir()\n'
        'open("models/best.joblib")\n'
        'open(f"models/{NAME}.joblib")\n'
        'pd.read_parquet("data/01.parquet")\n'
        'Path("docs/figures").mkdir()\n'
    )
    errs = check_notebook.problems_in(bad, "notebooks/py/01-bad.py")
    joined = "\n".join(errs)
    assert "double-hash" in joined
    assert "custom-pkg" in joined and "scikit-learn" in joined
    assert "openpyxl" in joined and "kaleido" in joined
    assert "Class 'Foo'" in joined
    assert len([e for e in errs if e.startswith("Relative path")]) == 5

    ok_paths = (
        "# %% [markdown]\n# # Title\n# %%\n# # %pip install -q joblib\n"
        '# %%\nfrom pathlib import Path\nimport joblib\nNAME = "01"\nROOT = Path.cwd()\n'
        'MODELS = ROOT / "models"\njoblib.dump({}, MODELS / f"{NAME}.joblib")\n'
        'joblib.dump({}, ROOT / f"models/{NAME}.joblib")\nprint("models/best.joblib")\n'
    )
    assert check_notebook.problems_in(ok_paths, "notebooks/py/01-paths.py") == []

    body = "\n".join(f"x_{i} = {i}" for i in range(225))
    big = "# %% [markdown]\n# # T\n# %%\n# # %pip install -q pandas\n# %%\n" + body
    big_errs = check_notebook.problems_in(big, "notebooks/py/01-big.py", before_code_lines=180)
    assert any("ruff format` expanded code from 180 to" in e for e in big_errs)

    nb_file = tmp_path / "01-bad.py"
    nb_file.write_text("# %%\nx = 1\n", encoding="utf-8")

    class Ok:
        returncode, stdout, stderr = 0, "", ""

    synced: list[str] = []
    monkeypatch.setattr(check_notebook, "run", lambda *_a: Ok())
    monkeypatch.setattr(check_notebook, "_sync_ipynb", lambda p: synced.append(p) or [])
    assert check_notebook.check_one_notebook(str(nb_file))
    assert synced == []


def test_nb_summary_and_export_docx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    nb_data = {
        "cells": [
            {"cell_type": "markdown", "source": ["# 01 Test"]},
            {
                "cell_type": "code",
                "execution_count": 3,
                "source": ["x = 1"],
                "outputs": [
                    {"output_type": "display_data", "data": {"application/vnd.plotly.v1+json": {}}}
                ],
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "source": ["1 / 0"],
                "outputs": [
                    {
                        "output_type": "error",
                        "ename": "ZeroDivisionError",
                        "evalue": "division by zero",
                        "traceback": ["\x1b[0;31mZeroDivisionError\x1b[0m: division by zero"],
                    }
                ],
            },
        ]
    }
    nb_file = tmp_path / "test.ipynb"
    nb_file.write_text(json.dumps(nb_data))
    out = nb_summary.summarize_notebook(str(nb_file))
    assert "[plotly output]" in out and "ERROR ZeroDivisionError: division by zero" in out
    assert "\x1b" not in out and "out of order" in out and "Ctrl+S" in out

    clean = tmp_path / "clean.ipynb"
    clean.write_text(
        json.dumps({"cells": [{"cell_type": "code", "execution_count": 1, "source": ["1"]}]})
    )
    clean_out = nb_summary.summarize_notebook(str(clean))
    assert "[Execution summary: 1/1 code cells run]" in clean_out and "Ctrl+S" not in clean_out

    called: list[tuple[tuple[str, ...], dict[str, object]]] = []

    class FakePypandoc:
        @staticmethod
        def convert_file(*args: str, **kwargs: object) -> None:
            called.append((args, kwargs))

    monkeypatch.setitem(sys.modules, "pypandoc", FakePypandoc)
    with pytest.raises(SystemExit):
        export_docx.main([str(tmp_path / "missing.md")])
    report = tmp_path / "01-eda.md"
    report.write_text("# Report\n")
    export_docx.main([str(report)])
    assert called == [
        (
            (str(report.resolve()), "docx"),
            {
                "outputfile": str(report.resolve().with_suffix(".docx")),
                "extra_args": [f"--resource-path={report.resolve().parent}"],
            },
        )
    ]


def test_papers_arxiv_parsing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    xml = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
        b"<id>http://arxiv.org/abs/2401.00001v1</id><published>2024-01-01T00:00:00Z</published>"
        b"<title>Test Paper</title><summary>Short abstract.</summary>"
        b"<author><name>Ada Lovelace</name></author></entry></feed>"
    )
    monkeypatch.setattr(papers, "get", lambda _url: xml)
    papers.search_arxiv("test", 1)
    out = capsys.readouterr().out
    assert "Test Paper (2024)" in out and "Ada Lovelace" in out and "arXiv:2401.00001v1" in out


def test_presentation_deck_and_validation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("pptx")
    import deck
    from pptx.oxml.ns import qn

    example_path = ROOT / ".agents" / "skills" / "presentation" / "assets" / "example.json"
    spec = json.loads(example_path.read_text(encoding="utf-8"))
    deck.check(spec, example_path.parent)
    assert capsys.readouterr().out == ""
    prs = deck.build(spec, example_path.parent)
    assert len(prs.slides) == len(spec["slides"]) + 1
    assert spec["slides"][-1]["type"] == "thanks"
    for slide in list(prs.slides)[1:]:
        assert spec["title"] not in [sh.text_frame.text for sh in slide.shapes if sh.has_text_frame]

    code_spec = {
        "title": "Code Demo",
        "notes": "Opening.",
        "slides": [
            {
                "type": "content",
                "title": "Snippet",
                "code": {"start_line": 10, "highlight": [11], "snippet": "def f():\n    return 1"},
                "notes": "Code slide.",
            },
            {"type": "thanks", "title": "Obrigado", "notes": "Closing."},
        ],
    }
    deck.check(code_spec, tmp_path)
    assert capsys.readouterr().out == ""
    code_prs = deck.build(code_spec, tmp_path)
    tbl = next(sh.table for sh in code_prs.slides[1].shapes if sh.has_table)
    tags = [el.tag for el in tbl.cell(1, 1)._tc.tcPr]
    assert tags.index(qn("a:lnB")) < tags.index(qn("a:solidFill"))
    assert tbl.cell(1, 1).text_frame.paragraphs[0].runs[0]._r.t.text == "    return 1"
    assert code_prs.slides[2].shapes.title.text == "Obrigado"
    assert not any(
        sh.has_text_frame and sh.text_frame._txBody.findall(f".//{qn('a:fld')}")
        for sh in code_prs.slides[2].shapes
    )

    bad_spec = {
        "title": "Bad",
        "slides": [
            {"type": "section", "title": "1. Intro", "notes": "n"},
            {
                "type": "bogus",
                "title": "A" * 85,
                "image": "missing.png",
                "images": ["missing.png"],
                "stats": [{}] * 5,
                "flow": [{}] * 6,
                "compare": [{"title": str(i)} for i in range(4)],
                "grid": [{"title": str(i)} for i in range(5)],
                "code": [{"lines": [str(i) for i in range(15)], "tone": "warn"}, {"snippet": "x"}],
                "bullets": ["a"] * 6,
                "notes": "n",
            },
        ],
    }
    deck.check(bad_spec, tmp_path)
    warn = capsys.readouterr().out
    for msg in (
        "slide 1 (title): no presenter notes",
        "auto-numbers sections",
        "unknown slide type 'bogus'",
        "title is long",
        "missing image missing.png",
        "more than 4 stats",
        "more than 5 steps",
        "more than 3 columns",
        "grid expects 2, 3, 4, or 6 cards",
        "images expects 2 figures",
        "combine bullets with a single code block only",
        "code block has more than 14 lines",
        "unknown code tone 'warn'",
        "more than 5 bullets",
    ):
        assert msg in warn
