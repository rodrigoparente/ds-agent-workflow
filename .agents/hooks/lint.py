#!/usr/bin/env python3
"""PostToolUse hook: formats/lints edited Python files and syncs Jupytext notebooks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    HookContext,
    emit_post_tool_feedback,
    parse_payload,
    run_project_tool,
    run_ruff,
)


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
        return (r.stdout + "\n" + r.stderr).strip() if r.returncode != 0 else ""

    _, errs = run_ruff(lambda *args: run_project_tool(ctx.root, *args), str(target))
    return f"Lint issues in {rel}:\n" + "\n".join(errs) if errs else ""


def main() -> None:
    ctx = parse_payload()
    emit_post_tool_feedback(ctx, check_edited_file(ctx))


if __name__ == "__main__":
    main()
