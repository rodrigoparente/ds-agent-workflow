#!/usr/bin/env python3
"""PostToolUse hook for Antigravity, Claude Code, and Cursor.

- On edited `notebooks/py/*.py`: runs `.agents/tools/check_notebook.py` (which formats, checks
  notebook structure & package installs, and syncs the paired `notebooks/*.ipynb`).
- On any other edited `*.py` file (`scripts/`, `apps/`, `tests/`): runs `ruff format` and
  `ruff check --fix --unfixable F401` (preserving unused imports during multi-step edits while
  reporting remaining lint issues back to the agent).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HookContext, emit_post_tool_feedback, parse_payload


def _run_tool(root: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    if shutil.which("uv"):
        sync_flag = ("--no-sync",) if (root / ".venv").exists() else ()
        cmd = ("uv", "run", *sync_flag, "--quiet", *args)
    elif shutil.which(args[0]):
        cmd = args
    else:
        return None
    return subprocess.run(cmd, capture_output=True, text=True, cwd=root)


def check_edited_file(ctx: HookContext) -> str:
    """Run static checks on an edited Python file and return error output (or empty string)."""
    rel = ctx.rel_path()
    if not rel or not rel.endswith(".py"):
        return ""
    target = ctx.root / rel
    if not target.exists():
        return ""

    if rel.startswith("notebooks/py/"):
        r = subprocess.run(
            [sys.executable, str(ctx.root / ".agents/tools/check_notebook.py"), str(target)],
            capture_output=True,
            text=True,
            cwd=ctx.root,
        )
        if r.returncode != 0:
            return (r.stdout + "\n" + r.stderr).strip()
        return ""

    # Standard Python files (scripts/, apps/, tests/, etc.)
    _run_tool(ctx.root, "ruff", "format", "--quiet", str(target))
    r = _run_tool(
        ctx.root,
        "ruff",
        "check",
        "--fix",
        "--unfixable",
        "F401",
        "--quiet",
        str(target),
    )
    if r is not None and r.returncode != 0:
        out = (r.stdout or r.stderr).strip()
        return f"ruff check issues in {rel}:\n{out}"
    return ""


def main() -> None:
    ctx = parse_payload()
    problems = check_edited_file(ctx)
    emit_post_tool_feedback(ctx, problems)


if __name__ == "__main__":
    main()
