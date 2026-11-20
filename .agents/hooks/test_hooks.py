#!/usr/bin/env python3
"""Unit tests for .agents/hooks/ and .agents/tools/."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agents" / "hooks"))
sys.path.insert(0, str(ROOT / ".agents" / "tools"))

import check_notebook  # noqa: E402
import common  # noqa: E402
import lint  # noqa: E402
import nb_summary  # noqa: E402
import session_start  # noqa: E402
import stop_tests  # noqa: E402


def test_common_payload_detection_across_agents() -> None:
    # 1. Antigravity CLI payload (`Path`)
    agy_payload = {
        "hookEventName": "PostToolUse",
        "workspacePaths": [str(ROOT)],
        "toolCall": {"name": "edit_file", "args": {"Path": "scripts/helpers.py"}},
    }
    ctx_agy = common.parse_payload(io.StringIO(json.dumps(agy_payload)))
    assert ctx_agy.agent == "antigravity"
    assert ctx_agy.rel_path() == "scripts/helpers.py"

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


def test_check_notebook_ast_and_install_detection() -> None:
    bad_nb = (
        "# %% [markdown]\n"
        "# # Title\n"
        "# %% \n"
        "# %pip install -q pandas\n"
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


def test_session_start_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    (tmp_path / ".venv").mkdir()
    (specs / "01-eda.md").write_text("# 01\nStatus: executed\n")
    (specs / "02-baseline.md").write_text("# 02\nStatus: approved\n")
    monkeypatch.setattr(
        session_start.shutil, "which", lambda name: "/usr/bin/uv" if name == "uv" else None
    )
    summary = session_start.build_context_summary(tmp_path)
    assert "01-eda (executed)" in summary
    assert "02-baseline (approved)" in summary
    assert "`03-`" in summary
    assert "Warning:" not in summary


def test_session_start_warns_when_toolchain_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(session_start.shutil, "which", lambda _name: None)
    summary = session_start.build_context_summary(tmp_path)
    assert "Warning:" in summary
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


def test_stop_tests_runs_hook_tests_when_hooks_change(
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
        stop_tests, "_changed_python_paths", lambda _root: [".agents/hooks/common.py"]
    )
    monkeypatch.setattr(stop_tests, "run_project_tool", fake_run)
    ctx = common.HookContext(agent="claude", root=tmp_path)
    should_continue, reason = stop_tests.check_tests_on_stop(ctx)
    assert should_continue is False
    assert reason == ""
    assert called == [("pytest", "-x", "-q", ".agents/hooks/test_hooks.py")]


def test_stop_tests_skips_without_git_or_on_notebook_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Missing .git does not trigger pytest
    test_file = tmp_path / "tests" / "test_app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok(): pass\n")
    assert stop_tests.check_tests_on_stop(common.HookContext("claude", tmp_path)) == (False, "")

    # Notebook-only changes in git skip pytest
    (tmp_path / ".git").mkdir()

    class FakeResult:
        returncode = 0
        stdout = " M notebooks/py/01-eda.py\n?? docs/reports/01-eda.md\n"

    monkeypatch.setattr(
        stop_tests.shutil, "which", lambda name: "/usr/bin/git" if name == "git" else None
    )
    monkeypatch.setattr(stop_tests.subprocess, "run", lambda *a, **kw: FakeResult())
    ctx = common.HookContext(agent="claude", root=tmp_path)
    assert stop_tests.check_tests_on_stop(ctx) == (False, "")


def test_check_notebook_reports_format_expansion() -> None:
    body = "\n".join(f"x_{i} = {i}" for i in range(225))
    nb = (
        "# %% [markdown]\n# # Title\n# %%\n# %pip install -q pandas\n"
        "# %%\nimport pandas\n# %% [markdown]\n# Step\n# %%\n" + body
    )
    problems = check_notebook.problems_in(nb, "notebooks/py/01-test.py", before_code_lines=180)
    assert any("ruff format` expanded code from 180 to" in p for p in problems)
    assert any("Largest cells:" in p for p in problems)
