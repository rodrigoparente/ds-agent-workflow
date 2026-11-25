#!/usr/bin/env python3
"""Stop hook: catches unresolved lint/notebook issues (Antigravity) and runs pytest."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    HookContext,
    emit_stop_decision,
    find_project_tool,
    git_stdout,
    parse_payload,
    run_project_tool,
)
from lint import check_edited_file

PYTEST_TIMEOUT = 120  # keep below the Stop hook timeout in settings.json / hooks.json


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


def _antigravity_lint_failure(ctx: HookContext, changed: list[str]) -> str:
    if ctx.agent != "antigravity" or find_project_tool(ctx.root, "ruff") is None:
        return ""
    errors: list[str] = []
    for rel in changed:
        if not (ctx.root / rel).is_file():
            continue
        err = check_edited_file(HookContext(agent="antigravity", root=ctx.root, file_path=rel))
        if err:
            errors.append(err)
    if not errors:
        return ""
    return "Fix lint/notebook issues before finishing:\n" + "\n\n".join(errors)


def _skip_stop(ctx: HookContext) -> bool:
    if ctx.stop_active:
        return True
    return (
        ctx.agent == "antigravity"
        and bool(ctx.termination_reason)
        and ctx.termination_reason != "NO_TOOL_CALL"
    )


def _run_pytest(root: Path, targets: list[str]) -> tuple[bool, str]:
    try:
        r = run_project_tool(root, "pytest", "-x", "-q", *targets, timeout=PYTEST_TIMEOUT)
    except subprocess.TimeoutExpired:
        return (
            True,
            f"Unit tests timed out after {PYTEST_TIMEOUT}s. Tell the user instead of retrying.",
        )
    if r is None:
        return (True, "pytest is not installed. Tell the user to run `uv sync`.")
    if r.returncode != 0:
        tail = "\n".join((r.stdout + "\n" + r.stderr).strip().splitlines()[-30:])
        return (True, f"Unit tests failed. Please fix them before finishing:\n{tail}")
    return (False, "")


def check_tests_on_stop(ctx: HookContext) -> tuple[bool, str]:
    """Return (should_continue, reason). True means checks failed and agent must fix them."""
    if _skip_stop(ctx) or not (changed := _changed_python_paths(ctx.root)):
        return (False, "")
    if lint_msg := _antigravity_lint_failure(ctx, changed):
        return (True, lint_msg)
    if not (targets := _select_test_targets(ctx.root, changed)):
        return (False, "")
    return _run_pytest(ctx.root, targets)


def main() -> None:
    ctx = parse_payload()
    should_continue, reason = check_tests_on_stop(ctx)
    emit_stop_decision(ctx, should_continue, reason)


if __name__ == "__main__":
    main()
