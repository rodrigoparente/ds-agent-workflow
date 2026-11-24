#!/usr/bin/env python3
"""Stop hook: runs `pytest -x -q` when Python code or hook/tool/skill files changed."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HookContext, emit_stop_decision, git_stdout, parse_payload, run_project_tool


def _changed_python_paths(root: Path) -> list[str]:
    out = git_stdout(root, "status", "--porcelain", "-uall")
    if not out:
        return []
    paths: list[str] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().split(" -> ")[-1].strip('"')
        if path.endswith(".py"):
            paths.append(path)
    return paths


def _select_test_targets(root: Path, changed: list[str]) -> list[str]:
    has_project_tests = (root / "tests").exists() and any((root / "tests").glob("test_*.py"))
    has_hook_tests = (root / ".agents" / "hooks" / "test_hooks.py").exists()
    targets: list[str] = []
    if has_project_tests and any(p.startswith(("scripts/", "apps/", "tests/")) for p in changed):
        targets.append("tests")
    if has_hook_tests and any(
        p.startswith((".agents/hooks/", ".agents/tools/", ".agents/skills/")) for p in changed
    ):
        targets.append(".agents/hooks/test_hooks.py")
    return targets


def check_tests_on_stop(ctx: HookContext) -> tuple[bool, str]:
    """Return (should_continue, reason). True means tests failed and agent must fix them."""
    if ctx.stop_active:
        return (False, "")
    if (
        ctx.agent == "antigravity"
        and ctx.termination_reason
        and ctx.termination_reason != "NO_TOOL_CALL"
    ):
        return (False, "")

    changed = _changed_python_paths(ctx.root)
    targets = _select_test_targets(ctx.root, changed) if changed else []
    if not targets:
        return (False, "")

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
