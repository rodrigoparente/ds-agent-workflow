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


def test_common_payload_detection_across_agents() -> None:
    # 1. Antigravity CLI payload (`Path` + `terminationReason`)
    agy_payload = {
        "hookEventName": "PostToolUse",
        "workspacePaths": [str(ROOT)],
        "terminationReason": "USER_CANCELED",
        "toolCall": {"name": "edit_file", "args": {"Path": "scripts/helpers.py"}},
    }
    ctx_agy = common.parse_payload(io.StringIO(json.dumps(agy_payload)))
    assert ctx_agy.agent == "antigravity"
    assert ctx_agy.rel_path() == "scripts/helpers.py"
    assert ctx_agy.termination_reason == "USER_CANCELED"

    # 2. Antigravity IDE payload (`TargetFile`)
    agy_ide_payload = {
        "hookEventName": "PostToolUse",
        "workspacePaths": [str(ROOT)],
        "toolCall": {
            "name": "replace_file_content",
            "args": {"TargetFile": "scripts/helpers.py"},
        },
    }
    ctx_ide = common.parse_payload(io.StringIO(json.dumps(agy_ide_payload)))
    assert ctx_ide.agent == "antigravity"
    assert ctx_ide.rel_path() == "scripts/helpers.py"

    # 3. Claude Code payload
    claude_payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": "scripts/helpers.py"},
    }
    ctx_claude = common.parse_payload(io.StringIO(json.dumps(claude_payload)))
    assert ctx_claude.agent == "claude"
    assert ctx_claude.rel_path() == "scripts/helpers.py"

    # 4. Cursor native afterFileEdit / Stop payload
    cursor_edit = {"file_path": "scripts/helpers.py", "edits": []}
    ctx_cursor = common.parse_payload(io.StringIO(json.dumps(cursor_edit)))
    assert ctx_cursor.agent == "cursor"
    assert ctx_cursor.rel_path() == "scripts/helpers.py"

    cursor_stop = {"loop_count": 1}
    ctx_cursor_stop = common.parse_payload(io.StringIO(json.dumps(cursor_stop)))
    assert ctx_cursor_stop.agent == "cursor"
    assert ctx_cursor_stop.stop_active is True


def test_common_find_project_tool_priority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dot_venv_tool = tmp_path / ".venv" / "bin" / "ruff"
    venv_tool = tmp_path / "venv" / "bin" / "ruff"
    active_venv = tmp_path / "active_env"
    active_tool = active_venv / "bin" / "ruff"

    for p in (dot_venv_tool, venv_tool, active_tool):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("#!/bin/sh\n")

    monkeypatch.setenv("VIRTUAL_ENV", str(active_venv))
    monkeypatch.setattr(common.shutil, "which", lambda _name: "/usr/bin/ruff")

    assert common.find_project_tool(tmp_path, "ruff") == str(dot_venv_tool)
    dot_venv_tool.unlink()
    assert common.find_project_tool(tmp_path, "ruff") == str(venv_tool)
    venv_tool.unlink()
    assert common.find_project_tool(tmp_path, "ruff") == str(active_tool)
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    assert common.find_project_tool(tmp_path, "ruff") == "/usr/bin/ruff"
    monkeypatch.setattr(common.shutil, "which", lambda _name: None)
    assert common.find_project_tool(tmp_path, "ruff") is None


def test_check_notebook_ast_and_install_detection() -> None:
    bad_nb = (
        "# %% [markdown]\n"
        "# # Title\n"
        "# %% \n"
        "# # %pip install -q pandas\n"
        "# %%\n"
        "import pandas as pd\n"
        "import sklearn.metrics\n"
        "# %% [markdown]\n"
        "# Step 1\n"
        "# %%\n"
        "class Foo:\n"
        "    pass\n"
    )
    problems = check_notebook.problems_in(bad_nb, "notebooks/py/01-test.py")
    assert any("scikit-learn" in p for p in problems)
    assert any("Class 'Foo'" in p for p in problems)
    assert not any("install cell" in p and "double-hash" in p for p in problems)

    live_pip_nb = (
        "# %% [markdown]\n"
        "# # Title\n"
        "# %%\n"
        "# %pip install -q pandas\n"
        "# %%\n"
        "import pandas as pd\n"
    )
    live_problems = check_notebook.problems_in(live_pip_nb, "notebooks/py/02-test.py")
    assert any("double-hash" in p for p in live_problems)


def test_check_notebook_stops_on_format_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nb_file = tmp_path / "01-broken.py"
    nb_file.write_text("def broken(:\n")

    class FailFmt:
        returncode = 2
        stdout = ""
        stderr = "error: Failed to parse"

    monkeypatch.setattr(check_notebook, "run", lambda *args: FailFmt())
    problems = check_notebook.check_one_notebook(str(nb_file))
    assert problems == ["ruff format:\nerror: Failed to parse"]


def test_nb_summary_tracebacks_and_out_of_order(tmp_path: Path) -> None:
    nb_data = {
        "cells": [
            {"cell_type": "markdown", "source": ["# 01 Test"]},
            {
                "cell_type": "code",
                "execution_count": 3,
                "source": ["x = 1"],
                "outputs": [
                    {
                        "output_type": "display_data",
                        "data": {"application/vnd.plotly.v1+json": {"data": []}},
                    }
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
    assert "[plotly output]" in out
    assert "ERROR ZeroDivisionError: division by zero" in out
    assert "\x1b" not in out  # ANSI stripped
    assert "WARNING: cells were executed out of order" in out
    assert "Ctrl+S" in out

    clean_nb = {
        "cells": [
            {"cell_type": "markdown", "source": ["# 01 Clean"]},
            {"cell_type": "code", "execution_count": 1, "source": ["x = 1"], "outputs": []},
        ]
    }
    clean_file = tmp_path / "clean.ipynb"
    clean_file.write_text(json.dumps(clean_nb))
    clean_out = nb_summary.summarize_notebook(str(clean_file))
    assert "[Execution summary: 1/1 code cells run]" in clean_out
    assert "Ctrl+S" not in clean_out


def test_session_start_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "01-eda.md").write_text("# 01\nStatus: executed\n")
    (specs / "02-baseline.md").write_text("# 02\nStatus: approved\n")
    monkeypatch.setattr(session_start, "find_project_tool", lambda _root, tool: f"/venv/{tool}")
    summary = session_start.build_context_summary(tmp_path)
    assert "01-eda (executed)" in summary
    assert "02-baseline (approved)" in summary
    assert "Context:" not in summary
    assert "`03-`" in summary
    assert "Warning:" not in summary

    (specs / "context.md").write_text("# Project Context\n")
    summary_with_ctx = session_start.build_context_summary(tmp_path)
    assert "context (unknown)" not in summary_with_ctx
    assert "Context: `specs/context.md`" in summary_with_ctx
    assert "`03-`" in summary_with_ctx


def test_session_start_warns_when_toolchain_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(session_start, "find_project_tool", lambda _root, _tool: None)
    summary = session_start.build_context_summary(tmp_path)
    assert "Warning: missing workspace tools" in summary
    assert "uv sync" in summary


def test_lint_routes_python_and_notebook_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Non-python file is skipped
    md_file = tmp_path / "README.md"
    md_file.write_text("# hi\n")
    assert lint.check_edited_file(common.HookContext("claude", tmp_path, "README.md")) == ""

    # Regular .py file invokes ruff format + check
    py_file = tmp_path / "scripts" / "helpers.py"
    py_file.parent.mkdir(parents=True)
    py_file.write_text("x = 1\n")
    calls: list[tuple[str, ...]] = []

    class OkResult:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_tool(_root: Path, *args: str, timeout: int | None = None) -> OkResult:
        calls.append(args)
        return OkResult()

    monkeypatch.setattr(lint, "run_project_tool", fake_tool)
    assert (
        lint.check_edited_file(common.HookContext("claude", tmp_path, "scripts/helpers.py")) == ""
    )
    assert calls[0][:2] == ("ruff", "format")
    assert calls[1][:2] == ("ruff", "check")

    # Format failure stops early without calling ruff check
    calls.clear()

    class FailFmt:
        returncode = 2
        stdout = ""
        stderr = "syntax error"

    monkeypatch.setattr(lint, "run_project_tool", lambda _r, *a, **kw: calls.append(a) or FailFmt())
    err = lint.check_edited_file(common.HookContext("claude", tmp_path, "scripts/helpers.py"))
    assert "ruff format:" in err
    assert len(calls) == 1


def test_stop_tests_runs_project_tests_on_code_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test_file = tmp_path / "tests" / "test_app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok(): pass\n")
    called: list[tuple[str, ...]] = []

    class FakeResult:
        returncode = 1
        stdout = "1 failed"
        stderr = ""

    def fake_run(root: Path, *args: str, timeout: int | None = None) -> FakeResult:
        called.append(args)
        return FakeResult()

    monkeypatch.setattr(stop_tests, "_changed_python_paths", lambda _root: ["scripts/a.py"])
    monkeypatch.setattr(stop_tests, "run_project_tool", fake_run)
    ctx = common.HookContext(agent="claude", root=tmp_path)
    should_continue, reason = stop_tests.check_tests_on_stop(ctx)
    assert should_continue is True
    assert "Unit tests failed" in reason
    assert called == [("pytest", "-x", "-q", "tests")]


def test_stop_tests_runs_hook_tests_when_hooks_or_skills_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hook_tests = tmp_path / ".agents" / "hooks" / "test_hooks.py"
    hook_tests.parent.mkdir(parents=True)
    hook_tests.write_text("def test_ok(): pass\n")
    called: list[tuple[str, ...]] = []

    class OkResult:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(root: Path, *args: str, timeout: int | None = None) -> OkResult:
        called.append(args)
        return OkResult()

    monkeypatch.setattr(
        stop_tests,
        "_changed_python_paths",
        lambda _root: [".agents/skills/presentation/scripts/deck.py"],
    )
    monkeypatch.setattr(stop_tests, "run_project_tool", fake_run)
    ctx = common.HookContext(agent="claude", root=tmp_path)
    should_continue, reason = stop_tests.check_tests_on_stop(ctx)
    assert should_continue is False
    assert reason == ""
    assert called == [("pytest", "-x", "-q", ".agents/hooks/test_hooks.py")]


def test_stop_tests_skips_without_git_or_canceled_or_notebook_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Missing .git does not trigger pytest
    test_file = tmp_path / "tests" / "test_app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok(): pass\n")
    assert stop_tests.check_tests_on_stop(common.HookContext("claude", tmp_path)) == (False, "")

    # Antigravity USER_CANCELED skips pytest even when code changed
    ctx_canceled = common.HookContext(
        agent="antigravity", root=tmp_path, termination_reason="USER_CANCELED"
    )
    assert stop_tests.check_tests_on_stop(ctx_canceled) == (False, "")

    # Notebook-only changes in git skip pytest
    (tmp_path / ".git").mkdir()
    git_cmds: list[list[str]] = []

    class FakeResult:
        returncode = 0
        stdout = " M notebooks/py/01-eda.py\n?? docs/reports/01-eda.md\n"

    def fake_git(cmd, **_kw):
        git_cmds.append(cmd)
        return FakeResult()

    monkeypatch.setattr(
        common.shutil, "which", lambda name: "/usr/bin/git" if name == "git" else None
    )
    monkeypatch.setattr(common.subprocess, "run", fake_git)
    ctx = common.HookContext(agent="claude", root=tmp_path)
    assert stop_tests.check_tests_on_stop(ctx) == (False, "")
    assert git_cmds == [["git", "status", "--porcelain", "-uall"]]

    # Untracked files inside brand-new scripts/ and tests/ folders trigger pytest
    FakeResult.stdout = "?? scripts/new_mod.py\n?? tests/test_new_mod.py\n"
    assert stop_tests._changed_python_paths(tmp_path) == [
        "scripts/new_mod.py",
        "tests/test_new_mod.py",
    ]


def test_check_notebook_reports_format_expansion() -> None:
    body = "\n".join(f"x_{i} = {i}" for i in range(225))
    nb = (
        "# %% [markdown]\n# # Title\n# %%\n# # %pip install -q pandas\n"
        "# %%\nimport pandas\n# %% [markdown]\n# Step\n# %%\n" + body
    )
    problems = check_notebook.problems_in(nb, "notebooks/py/01-test.py", before_code_lines=180)
    assert any("ruff format` expanded code from 180 to" in p for p in problems)
    assert any("Largest cells:" in p for p in problems)


def test_papers_xml_parsing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    sample_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2401.00001v1</id>
        <published>2024-01-01T00:00:00Z</published>
        <title>Test Paper Title</title>
        <summary>Short abstract summary.</summary>
        <author><name>Ada Lovelace</name></author>
      </entry>
    </feed>"""
    monkeypatch.setattr(papers, "get", lambda _url: sample_xml)
    papers.search_arxiv("test query", 1)
    out = capsys.readouterr().out
    assert "Test Paper Title (2024)" in out
    assert "Ada Lovelace" in out
    assert "arXiv:2401.00001v1" in out


def test_presentation_example_json_schema() -> None:
    example_path = ROOT / ".agents" / "skills" / "presentation" / "assets" / "example.json"
    spec = json.loads(example_path.read_text(encoding="utf-8"))
    assert spec["title"]
    assert spec.get("notes")
    assert spec["slides"][-1]["type"] == "thanks"
    seen_types: set[str] = set()
    for slide in spec["slides"]:
        min_words = 6 if slide["type"] == "section" else 15
        assert slide.get("notes") and len(slide["notes"].split()) >= min_words
        for key in (
            "flow",
            "callout",
            "stats",
            "bars",
            "compare",
            "table",
            "grid",
            "timeline",
            "code",
        ):
            if key in slide:
                seen_types.add(key)
    assert seen_types == {
        "flow",
        "callout",
        "stats",
        "bars",
        "compare",
        "table",
        "grid",
        "timeline",
        "code",
    }


def test_deck_check_example_json_no_warnings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("pptx")
    import deck

    example_path = ROOT / ".agents" / "skills" / "presentation" / "assets" / "example.json"
    spec = json.loads(example_path.read_text(encoding="utf-8"))
    deck.check(spec, example_path.parent)
    assert capsys.readouterr().out == ""

    prs = deck.build(spec, example_path.parent)
    assert len(prs.slides) == len(spec["slides"]) + 1
    # Deck title appears on slide 1 only, not repeated in slide footers
    for slide in list(prs.slides)[1:]:
        texts = [sh.text_frame.text for sh in slide.shapes if sh.has_text_frame]
        assert spec["title"] not in texts

    no_sections = {
        "title": "Demo",
        "slides": [{"type": "agenda", "notes": "Agenda without sections."}],
    }
    prs_no_sec = deck.build(no_sections, example_path.parent)
    assert len(prs_no_sec.slides) == 2


def test_deck_check_warnings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("pptx")
    import deck

    bad_spec = {
        "title": "Bad",
        "slides": [
            {
                "type": "section",
                "title": "1. What is Collaborative Filtering?",
                "notes": "Section intro.",
            },
            {
                "type": "content",
                "title": "Bad slide",
                "image": "missing.png",
                "compare": [{"title": str(i), "bullets": []} for i in range(4)],
                "notes": "Spoken note here.",
            },
            {
                "type": "content",
                "title": "Too many stats",
                "stats": [{"value": str(i), "label": "k"} for i in range(5)],
                "notes": "Stats note.",
            },
            {
                "type": "content",
                "title": "Too many flow steps",
                "flow": [{"label": str(i), "text": "step"} for i in range(6)],
                "notes": "Flow note.",
            },
            {
                "type": "bogus",
                "title": "Bad grid & images",
                "grid": [{"title": str(i), "text": "x"} for i in range(5)],
                "images": ["missing.png"],
                "notes": "Grid and images warning note.",
            },
        ],
    }
    deck.check(bad_spec, tmp_path)
    warnings = capsys.readouterr().out
    assert "slide 1 (title): no presenter notes" in warnings
    assert "auto-numbers sections" in warnings
    assert "more than 3 columns" in warnings
    assert "missing image missing.png" in warnings
    assert "more than 4 stats" in warnings
    assert "more than 5 steps" in warnings
    assert "unknown slide type 'bogus'" in warnings
    assert "grid expects 2, 3, 4, or 6 cards" in warnings
    assert "images expects 2 figures" in warnings

    three_models = {
        "title": "Three Models",
        "slides": [
            {
                "type": "content",
                "title": "Three columns fit",
                "compare": [{"title": f"M{i}", "bullets": ["A", "B"]} for i in range(3)],
                "notes": "Three models side by side.",
            },
            {
                "type": "content",
                "title": "Three cards fit cleanly",
                "grid": [{"title": f"M{i}", "text": "Desc"} for i in range(3)],
                "notes": "Three cards in one row.",
            },
        ],
    }
    assert len(deck.build(three_models, tmp_path).slides) == 3


def test_deck_code_thanks_and_validation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pytest.importorskip("pptx")
    import deck
    from pptx.oxml.ns import qn

    valid_spec = {
        "title": "Code & Thanks Demo",
        "author": "Ana",
        "date": "Nov 2026",
        "notes": "Opening title slide notes.",
        "slides": [
            {
                "type": "content",
                "title": "Indented Snippet",
                "code": {
                    "title": "helper.py",
                    "tone": "info",
                    "start_line": 10,
                    "highlight": [11],
                    "snippet": "def f():\n    return 1",
                },
                "notes": "Single code block with indentation.",
            },
            {
                "type": "content",
                "title": "Code With Takeaways",
                "code": {"lines": ["x = 1", "y = x + 2"], "tone": "fix"},
                "bullets": ["Clean assignment", "Zero side effects"],
                "notes": "Code paired with concise bullets.",
            },
            {
                "type": "thanks",
                "notes": "Default English thank-you slide.",
            },
            {
                "type": "thanks",
                "title": "Obrigado",
                "subtitle": "Dúvidas?",
                "contact": "ana@example.com",
                "notes": "Localized thank-you slide.",
            },
        ],
    }
    deck.check(valid_spec, tmp_path)
    assert capsys.readouterr().out == ""

    prs = deck.build(valid_spec, tmp_path)
    assert len(prs.slides) == 5

    # Verify OOXML <a:tcPr> order (borders before solidFill) and preserved indentation
    code_tbl = next(sh.table for sh in prs.slides[1].shapes if sh.has_table)
    tc_pr = code_tbl.cell(1, 1)._tc.tcPr
    tags = [el.tag for el in tc_pr]
    assert tags.index(qn("a:lnB")) < tags.index(qn("a:solidFill"))
    t_el = code_tbl.cell(1, 1).text_frame.paragraphs[0].runs[0]._r.t
    assert t_el.get("{http://www.w3.org/XML/1998/namespace}space") == "preserve"
    assert t_el.text == "    return 1"

    # Verify default and custom thanks slides have no slide-number field
    for idx, expected_title in ((3, "Thank you"), (4, "Obrigado")):
        thanks_slide = prs.slides[idx]
        assert thanks_slide.shapes.title.text == expected_title
        assert not any(
            sh.has_text_frame and sh.text_frame._txBody.findall(f".//{qn('a:fld')}")
            for sh in thanks_slide.shapes
        )

    invalid_spec = {
        "title": "Invalid Code",
        "slides": [
            {
                "type": "content",
                "title": "A" * 85,
                "code": [{"snippet": "a"} for _ in range(3)],
                "bullets": ["Not allowed with 3 blocks"],
                "notes": "Too many blocks.",
            },
            {
                "type": "content",
                "title": "Too long & bad tone",
                "code": {"lines": [str(i) for i in range(15)], "tone": "warn"},
                "notes": "Too many lines.",
            },
        ],
    }
    deck.check(invalid_spec, tmp_path)
    warnings = capsys.readouterr().out
    assert "title is long" in warnings
    assert "code supports 1 or 2 blocks" in warnings
    assert "combine bullets with a single code block only" in warnings
    assert "code block has more than 14 lines" in warnings
    assert "unknown code tone 'warn'" in warnings


def test_claude_settings_has_no_write_deny_rules() -> None:
    settings_path = ROOT / ".claude" / "settings.json"
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    deny_rules = data["permissions"]["deny"]
    assert not any(rule.startswith("Write(") for rule in deny_rules)
    assert "Read(data/**)" not in deny_rules
    assert "Read(./data/**)" not in deny_rules
    assert "Read(**/.env)" in deny_rules
    assert "Edit(notebooks/*.ipynb)" in deny_rules
    assert "Edit(./notebooks/*.ipynb)" in deny_rules


def test_check_notebook_flags_unsaved_plots() -> None:
    unsaved_nb = (
        "# %% [markdown]\n# # Title\n"
        "# %%\n# # %pip install -q matplotlib\n"
        "# %%\nimport matplotlib.pyplot as plt\n"
        "# %% [markdown]\n# ## Plot\n"
        "# %%\nfig, ax = plt.subplots()\nax.plot([1, 2], [3, 4])\nplt.show()\n"
    )
    problems = check_notebook.problems_in(unsaved_nb, "notebooks/py/01-test.py")
    assert any("without saving any figure" in p for p in problems)

    saved_nb = unsaved_nb + 'fig.savefig(FIGURES / "01_plot.png", dpi=150, bbox_inches="tight")\n'
    assert check_notebook.problems_in(saved_nb, "notebooks/py/01-test.py") == []

    no_plot_nb = (
        "# %% [markdown]\n# # Title\n"
        "# %%\n# # %pip install -q pandas\n"
        "# %%\nimport pandas as pd\n"
        "# %% [markdown]\n# ## Print\n"
        "# %%\nprint(pd.__name__)\n"
    )
    assert check_notebook.problems_in(no_plot_nb, "notebooks/py/01-test.py") == []

    skeleton_path = ROOT / ".agents" / "skills" / "write-code" / "assets" / "skeleton.py"
    skeleton_problems = check_notebook.problems_in(skeleton_path.read_text(encoding="utf-8"))
    assert not [p for p in skeleton_problems if "without saving any figure" in p]


def test_check_notebook_flags_relative_project_paths() -> None:
    bad_nb = (
        "# %% [markdown]\n# # Title\n"
        "# %%\n# # %pip install -q joblib pandas\n"
        "# %%\nfrom pathlib import Path\nimport joblib\nimport pandas as pd\n"
        "# %% [markdown]\n# ## Save\n"
        "# %%\n"
        'NAME = "01-test"\n'
        'Path("models").mkdir(exist_ok=True)\n'
        'joblib.dump({}, "models/best.joblib")\n'
        'joblib.dump({}, f"models/{NAME}.joblib")\n'
        'df = pd.read_parquet("data/01.parquet")\n'
    )
    problems = check_notebook.problems_in(bad_nb, "notebooks/py/01-test.py")
    rel_errors = [p for p in problems if p.startswith("Relative path")]
    assert len(rel_errors) == 4

    good_nb = (
        "# %% [markdown]\n# # Title\n"
        "# %%\n# # %pip install -q joblib\n"
        "# %%\nfrom pathlib import Path\nimport joblib\n"
        "# %% [markdown]\n# ## Config\n"
        "# %%\n"
        'NAME = "01-test"\n'
        "ROOT = Path.cwd().parent\n"
        'MODELS = ROOT / "models"\n'
        'DATA = ROOT / "data"\n'
        'FIGURES = ROOT / "docs" / "figures"\n'
        'joblib.dump({}, MODELS / f"{NAME}.joblib")\n'
        'joblib.dump({}, ROOT / f"models/{NAME}.joblib")\n'
        'print("Saved to models/best.joblib")\n'
    )
    assert check_notebook.problems_in(good_nb, "notebooks/py/01-test.py") == []

    skeleton_path = ROOT / ".agents" / "skills" / "write-code" / "assets" / "skeleton.py"
    skeleton_problems = check_notebook.problems_in(skeleton_path.read_text(encoding="utf-8"))
    assert not [p for p in skeleton_problems if p.startswith("Relative path")]


def test_common_detect_root_workspace_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "env_dir"))
    ws = tmp_path / "ws_dir"
    assert common._detect_root({"workspacePaths": [str(ws)]}) == ws.resolve()
    assert common._detect_root({}) == (tmp_path / "env_dir").resolve()


def test_common_emit_helpers(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        common.emit_post_tool_feedback(common.HookContext("antigravity", ROOT), "lint err")
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "{}"
    assert "lint err" in captured.err

    with pytest.raises(SystemExit) as exc:
        common.emit_post_tool_feedback(common.HookContext("claude", ROOT), "lint err")
    assert exc.value.code == 2
    assert "lint err" in capsys.readouterr().err

    with pytest.raises(SystemExit) as exc:
        common.emit_stop_decision(common.HookContext("antigravity", ROOT), True, "fix tests")
    assert exc.value.code == 0
    assert json.loads(capsys.readouterr().out) == {"decision": "continue", "reason": "fix tests"}

    with pytest.raises(SystemExit) as exc:
        common.emit_stop_decision(common.HookContext("cursor", ROOT), True, "fix tests")
    assert exc.value.code == 0
    assert json.loads(capsys.readouterr().out) == {"followup_message": "fix tests"}

    with pytest.raises(SystemExit) as exc:
        common.emit_session_start(common.HookContext("antigravity", ROOT), "hello")
    assert exc.value.code == 0
    assert json.loads(capsys.readouterr().out) == {
        "injectSteps": [{"systemMessage": {"systemMessage": "hello"}}]
    }


def test_check_notebook_edge_cases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # 1. Path("docs/figures") is flagged; print(...) paths and sns.set_theme() are not
    nb_ok = (
        "# %% [markdown]\n# # Title\n"
        "# %%\n# # %pip install -q seaborn\n"
        "# %%\nimport seaborn as sns\n"
        "# %% [markdown]\n# ## Note: read_excel( in markdown is ignored\n"
        "# %%\n"
        'NAME = "01-test"\n'
        "sns.set_theme()\n"
        'print("models/best.joblib")\n'
        'print(f"models/{NAME}.joblib")\n'
    )
    assert check_notebook.problems_in(nb_ok, "notebooks/py/01-test.py") == []

    # 2. Path("docs/figures"), .to_excel(, and .write_image( are caught
    nb_bad = (
        "# %% [markdown]\n# # Title\n"
        "# %%\n# # %pip install -q pandas\n"
        "# %%\nfrom pathlib import Path\nimport pandas as pd\n"
        "# %% [markdown]\n# ## Step\n"
        "# %%\n"
        'Path("docs/figures").mkdir(parents=True, exist_ok=True)\n'
        'pd.DataFrame().to_excel("out.xlsx")\n'
        'fig.write_image("x.png")\n'
    )
    errs = check_notebook.problems_in(nb_bad, "notebooks/py/01-test.py")
    assert any("Relative path 'docs/figures'" in e for e in errs)
    assert any("openpyxl" in e and "kaleido" in e for e in errs)

    # 3. check_one_notebook skips _sync_ipynb when problems_in finds violations
    nb_file = tmp_path / "01-bad.py"
    nb_file.write_text("# %%\nx = 1\n", encoding="utf-8")

    class OkResult:
        returncode = 0
        stdout = ""
        stderr = ""

    sync_called: list[str] = []
    monkeypatch.setattr(check_notebook, "run", lambda *args: OkResult())
    monkeypatch.setattr(check_notebook, "_sync_ipynb", lambda p: sync_called.append(p) or [])
    problems = check_notebook.check_one_notebook(str(nb_file))
    assert problems
    assert sync_called == []


def test_export_docx_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[tuple[tuple[str, ...], dict[str, object]]] = []

    class FakePypandoc:
        @staticmethod
        def convert_file(*args: str, **kwargs: object) -> None:
            called.append((args, kwargs))

    monkeypatch.setitem(sys.modules, "pypandoc", FakePypandoc)
    with pytest.raises(SystemExit):
        export_docx.main([str(tmp_path / "missing.md")])

    report = tmp_path / "01-eda.md"
    report.write_text("# Report\n", encoding="utf-8")
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


def test_claude_settings_and_spec_rename() -> None:
    settings_path = ROOT / ".claude" / "settings.json"
    allow_rules = json.loads(settings_path.read_text(encoding="utf-8"))["permissions"]["allow"]
    assert {"Bash(git status)", "Bash(git diff)", "Bash(git log)"}.issubset(allow_rules)
    assert "Bash(uv run nbstripout *)" not in allow_rules
    assert (ROOT / ".agents" / "skills" / "spec" / "SKILL.md").is_file()
    assert not (ROOT / ".agents" / "skills" / "experiment-spec").exists()


