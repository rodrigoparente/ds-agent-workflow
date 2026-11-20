#!/usr/bin/env python3
"""Stop hook: runs `pytest -x -q` when Python code or hook/tool files changed."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HookContext, emit_stop_decision, parse_payload, run_project_tool


def _changed_python_paths(root: Path) -> list[str]:
    if not (root / ".git").exists() or not shutil.which("git"):
        return []
    r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=root)
    if r.returncode != 0:
        return []
    paths: list[str] = []
    for line in r.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().split(" -> ")[-1].strip('"')
        if path.endswith(".py"):
            paths.append(path)
    return paths


def check_tests_on_stop(ctx: HookContext) -> tuple[bool, str]:
    """Return (should_continue, reason). True means tests failed and agent must fix them."""
    if ctx.stop_active:
        return (False, "")

    changed = _changed_python_paths(ctx.root)
    if not changed:
        return (False, "")

    has_project_tests = (ctx.root / "tests").exists() and any(
        (ctx.root / "tests").glob("test_*.py")
    )
    has_hook_tests = (ctx.root / ".agents" / "hooks" / "test_hooks.py").exists()

    run_project = has_project_tests and any(
        p.startswith(("scripts/", "apps/", "tests/")) for p in changed
    )
    run_hooks = has_hook_tests and any(
        p.startswith((".agents/hooks/", ".agents/tools/")) for p in changed
    )

    if not (run_project or run_hooks):
        return (False, "")

    targets: list[str] = []
    if run_project:
        targets.append("tests")
    if run_hooks:
        targets.append(".agents/hooks/test_hooks.py")

    try:
        r = run_project_tool(ctx.root, "pytest", "-x", "-q", *targets, timeout=120)
    except subprocess.TimeoutExpired:
        return (False, "")

    if r is not None and r.returncode != 0:
        tail = "\n".join((r.stdout + "\n" + r.stderr).strip().splitlines()[-30:])
        return (True, f"Unit tests failed. Please fix them before finishing:\n{tail}")
    return (False, "")


def main() -> None:
    ctx = parse_payload()
    should_continue, reason = check_tests_on_stop(ctx)
    emit_stop_decision(ctx, should_continue, reason)


if __name__ == "__main__":
    main()
