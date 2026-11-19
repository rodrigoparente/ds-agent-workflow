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
import guard  # noqa: E402
import nb_summary  # noqa: E402
import session_start  # noqa: E402
import stop_tests  # noqa: E402


@pytest.mark.parametrize(
    "cmd",
    [
        "uv run python scripts/train.py",
        "uv run python scripts/train.py && uv run pytest",
        "python -c 'print(1)'  # pytest",
        "uv run scripts/train.py",
        "cd notebooks/py && python 01-eda.py",
        "uv run python -m scripts.train",
        "uv run python - <<'EOF'\nimport pandas\nEOF",
        "uv run jupytext --execute notebooks/py/01-eda.py",
        "uv run marimo run apps/app.py",
        "uv run fastapi dev apps/api.py",
        "uv run streamlit run apps/dashboard.py",
        "uv run uvicorn apps.api:app",
        "cat notebooks/01-eda.ipynb",
        "head -n 20 data/01-sales.parquet",
        "cat .env",
        "cat .env.production",
        "cat ~/.ssh/id_rsa",
        "uv run ruff check scripts/ ; uv run python scripts/train.py",
        "pip install pandas",
        "uv pip install scikit-learn",
        "python3 -m pip install torch",
        "rm -rf data/",
        "git push --force origin main",
        "git reset --hard HEAD~1",
        "bash -c 'python scripts/train.py'",
        'timeout 120s uv run --quiet python -c "print(1)"',
        "timeout 300s env CI=true uv pip install lightgbm",
        "nice -n 10 python3.14 scripts/train.py",
        "nohup .venv/bin/python apps/api.py",
        "env -u PYTHONPATH uv run scripts/train.py",
        "curl https://example.com && rm -rf data/",
        "cp .env /tmp/leak",
        "echo secret > .env",
    ],
)
def test_guard_blocks_forbidden_shell_commands(cmd: str) -> None:
    res = guard.check_shell_command(cmd)
    assert res is not None, f"Expected command to be blocked: {cmd}"
    assert res[0] == "deny"


@pytest.mark.parametrize(
    "cmd",
    [
        "uv run python .agents/tools/check_notebook.py notebooks/py/01-eda.py",
        "uv run python .agents/tools/nb_summary.py notebooks/01-eda.ipynb",
        "uv run python .agents/tools/export_docx.py docs/reports/01-eda.md",
        "uv run python scripts/build_01_eda_deck.py",
        "uv run pytest",
        "uv run pytest .agents/hooks",
        "timeout 30 uv run pytest",
        "uv run pytest --collect-only -q 2>&1 | tail -2",
        "uv run ruff check .",
        "uv run ruff format notebooks/py/01-eda.py",
        "uv run jupytext --sync notebooks/py/01-eda.py",
        "uv run nbstripout --install",
        "uv sync",
        "git status --short",
        "git diff",
        "git log -n 5 --oneline",
        "ls -la",
        "mkdir -p docs/figures",
        'grep "a -> b" README.md',
        "cat .env.example",
    ],
)
def test_guard_allows_safe_shell_commands(cmd: str) -> None:
    res = guard.check_shell_command(cmd)
    assert res is None, f"Expected command to be allowed: {cmd} (got {res})"


@pytest.mark.parametrize(
    "cmd",
    [
        "uv add lightgbm",
        "timeout 10s uv add lightgbm",
        "curl https://example.com",
        "./custom_script.sh",
        "git commit -m 'update spec'",
        "find . -exec python3 {} +",
        "echo hello > notes.txt",
    ],
)
def test_guard_asks_for_unlisted_and_dep_commands(cmd: str) -> None:
    res = guard.check_shell_command(cmd)
    assert res is not None and res[0] == "ask", f"Expected 'ask' for {cmd}, got {res}"


@pytest.mark.parametrize(
    ("rel", "expected"),
    [
        ("notebooks/01-eda.ipynb", "deny"),
        ("data/01-sales.parquet", "deny"),
        (".env", "deny"),
        (".env.local", "deny"),
        (".env.example", None),
        ("notebooks/py/01-eda.py", None),
        ("specs/01-eda.md", None),
        ("scripts/helpers.py", None),
    ],
)
def test_guard_file_path_checks(rel: str, expected: str | None) -> None:
    res = guard.check_file_path(rel, rel)
    if expected is None:
        assert res is None
    else:
        assert res is not None and res[0] == expected


def test_common_payload_detection_across_agents() -> None:
    # 1. Antigravity payload
    agy_payload = {
        "hookEventName": "PreToolUse",
        "workspacePaths": [str(ROOT)],
        "toolCall": {"name": "run_command", "args": {"CommandLine": "uv run pytest"}},
    }
    ctx_agy = common.parse_payload(io.StringIO(json.dumps(agy_payload)))
    assert ctx_agy.agent == "antigravity"
    assert ctx_agy.kind == "shell"
    assert ctx_agy.command == "uv run pytest"

    # 2. Claude Code payload
    claude_payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": "notebooks/01-eda.ipynb"},
    }
    ctx_claude = common.parse_payload(io.StringIO(json.dumps(claude_payload)))
    assert ctx_claude.agent == "claude"
    assert ctx_claude.kind == "read"
    assert ctx_claude.rel_path() == "notebooks/01-eda.ipynb"
    assert guard.evaluate(ctx_claude)[0] == "deny"


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


def test_stop_tests_runs_hook_suite_without_tests_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hook_file = tmp_path / ".agents" / "hooks" / "test_hooks.py"
    hook_file.parent.mkdir(parents=True)
    hook_file.write_text("def test_ok(): pass\n")
    called: list[list[str]] = []

    def fake_run(cmd: list[str], root: Path) -> tuple[bool, str]:
        called.append(cmd)
        return (True, "1 failed")

    monkeypatch.setattr(stop_tests, "_has_modified_python_files", lambda _root: True)
    monkeypatch.setattr(stop_tests, "_resolve_pytest_cmd", lambda _root: ["pytest", "-x", "-q"])
    monkeypatch.setattr(stop_tests, "_run_pytest", fake_run)
    ctx = common.HookContext(
        agent="claude",
        event="Stop",
        root=tmp_path,
        kind="other",
        tool_name="",
        command="",
        file_path="",
        stop_active=False,
        raw={},
    )
    should_continue, reason = stop_tests.check_tests_on_stop(ctx)
    assert should_continue is True
    assert "Unit tests failed" in reason
    assert called == [["pytest", "-x", "-q", str(hook_file)]]


def test_check_notebook_reports_format_expansion() -> None:
    body = "\n".join(f"x_{i} = {i}" for i in range(225))
    nb = (
        "# %% [markdown]\n# # Title\n# %%\n# %pip install -q pandas\n"
        "# %%\nimport pandas\n# %% [markdown]\n# Step\n# %%\n" + body
    )
    problems = check_notebook.problems_in(nb, "notebooks/py/01-test.py", before_code_lines=180)
    assert any("ruff format` expanded code from 180 to" in p for p in problems)
    assert any("Largest cells:" in p for p in problems)
