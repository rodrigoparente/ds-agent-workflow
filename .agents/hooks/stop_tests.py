#!/usr/bin/env python3
"""Stop hook for Antigravity, Claude Code, and Cursor.

When the agent finishes a turn, if `tests/` has unit tests and Python files were modified,
runs `pytest -x -q` and blocks completion once if tests fail so the agent can fix them.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HookContext, emit_stop_decision, parse_payload


def _has_modified_python_files(root: Path) -> bool:
    """Return True if git status shows modified or untracked .py files."""
    if not (root / ".git").exists() or not shutil.which("git"):
        return True
    r = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    if r.returncode != 0:
        return False
    return any(line.strip().endswith(".py") for line in r.stdout.splitlines())


def check_tests_on_stop(ctx: HookContext) -> tuple[bool, str]:
    """Return (should_continue, reason). True means tests failed and agent must fix them."""
    if ctx.stop_active:
        return (False, "")

    tests_dir = ctx.root / "tests"
    if not tests_dir.exists() or not any(tests_dir.glob("test_*.py")):
        return (False, "")

    if not _has_modified_python_files(ctx.root):
        return (False, "")

    if shutil.which("uv"):
        sync_flag = ("--no-sync",) if (ctx.root / ".venv").exists() else ()
        cmd = ["uv", "run", *sync_flag, "pytest", "-x", "-q"]
    elif shutil.which("pytest"):
        cmd = ["pytest", "-x", "-q"]
    else:
        return (False, "")

    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=ctx.root,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return (False, "")

    if r.returncode != 0:
        combined = (r.stdout + "\n" + r.stderr).strip().splitlines()
        tail = "\n".join(combined[-30:])
        return (
            True,
            f"Unit tests in `tests/` failed. Please fix them before finishing:\n{tail}",
        )
    return (False, "")


def main() -> None:
    ctx = parse_payload()
    should_continue, reason = check_tests_on_stop(ctx)
    emit_stop_decision(ctx, should_continue, reason)


if __name__ == "__main__":
    main()
