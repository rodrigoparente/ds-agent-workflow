#!/usr/bin/env python3
"""Stop hook for Antigravity, Claude Code, and Cursor.

When the agent finishes a turn after modifying Python files, runs `pytest -x -q` on
`tests/` (if present) and `.agents/hooks/test_hooks.py` (if present, in a separate
subprocess to avoid module-name collisions), blocking completion once on failure.
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


def _resolve_pytest_cmd(root: Path) -> list[str] | None:
    """Return the base pytest command using uv, .venv/bin/pytest, or PATH."""
    if shutil.which("uv"):
        sync_flag = ("--no-sync",) if (root / ".venv").exists() else ()
        return ["uv", "run", *sync_flag, "pytest", "-x", "-q"]
    venv_pytest = root / ".venv" / "bin" / "pytest"
    if venv_pytest.exists():
        return [str(venv_pytest), "-x", "-q"]
    if shutil.which("pytest"):
        return ["pytest", "-x", "-q"]
    return None


def _run_pytest(cmd: list[str], root: Path) -> tuple[bool, str]:
    """Run one pytest command and return (failed, failure_tail)."""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=root,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return (False, "")
    if r.returncode != 0:
        combined = (r.stdout + "\n" + r.stderr).strip().splitlines()
        return (True, "\n".join(combined[-30:]))
    return (False, "")


def check_tests_on_stop(ctx: HookContext) -> tuple[bool, str]:
    """Return (should_continue, reason). True means tests failed and agent must fix them."""
    if ctx.stop_active or not _has_modified_python_files(ctx.root):
        return (False, "")

    tests_dir = ctx.root / "tests"
    has_project_tests = tests_dir.exists() and any(tests_dir.glob("test_*.py"))
    hook_tests = ctx.root / ".agents" / "hooks" / "test_hooks.py"
    has_hook_tests = hook_tests.exists()
    if not has_project_tests and not has_hook_tests:
        return (False, "")

    base_cmd = _resolve_pytest_cmd(ctx.root)
    if base_cmd is None:
        return (False, "")

    suites: list[list[str]] = []
    if has_project_tests:
        suites.append(base_cmd)
    if has_hook_tests:
        suites.append([*base_cmd, str(hook_tests)])

    for cmd in suites:
        failed, tail = _run_pytest(cmd, ctx.root)
        if failed:
            return (
                True,
                f"Unit tests failed. Please fix them before finishing:\n{tail}",
            )
    return (False, "")


def main() -> None:
    ctx = parse_payload()
    should_continue, reason = check_tests_on_stop(ctx)
    emit_stop_decision(ctx, should_continue, reason)


if __name__ == "__main__":
    main()
