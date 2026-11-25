#!/usr/bin/env python3
"""PreToolUse hook (Bash): blocks shell reads of secrets and raw notebooks.

The `deny` rules in .claude/settings.json only cover the Read/Edit tools; this closes the shell
gap. It is a guardrail against accidents, not a sandbox.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HookContext, parse_payload

# `.env` / `.env.local` (but not `.env.example`, `.env.template`, or `.venv`)
ENV_FILE = re.compile(r"(?:^|[\s/='\"])\.env(?:\.(?!example\b|template\b)\w+)?(?=$|[\s'\";|&<>)])")
SSH_DIR = re.compile(r"(?:^|[\s/='\"~])\.ssh(?=$|[\s/'\";|&<>)])")
# Raw notebook JSON read/edited by a shell tool. `nb_summary.py <nb>.ipynb` is not matched.
RAW_NOTEBOOK = re.compile(
    r"\b(?:cat|head|tail|less|more|sed|awk|grep|rg|jq|tee|vi|vim|nano)\b[^|;&]*"
    r"notebooks/[^\s'\"]*\.ipynb"
)

RULES = (
    (ENV_FILE, "reads of `.env*` files are blocked (secrets)"),
    (SSH_DIR, "access to `~/.ssh` is blocked (secrets)"),
    (
        RAW_NOTEBOOK,
        "raw `.ipynb` access is blocked; edit `notebooks/py/<NN-name>.py` and inspect outputs "
        "with `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`",
    ),
)


def check_command(command: str) -> str:
    """Return a block reason for a sensitive shell command, or an empty string."""
    for pattern, reason in RULES:
        if pattern.search(command):
            return f"Blocked: {reason}."
    return ""


def main() -> None:
    ctx: HookContext = parse_payload()
    if reason := check_command(ctx.command):
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
