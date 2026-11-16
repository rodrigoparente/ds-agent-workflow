#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block direct reads and edits of notebooks/*.ipynb. Exit 2 = block.

Edit jupytext/<name>.py instead. Run results are read through .agents/tools/nb_summary.py."""
import json
import os
import sys

tool_input = json.load(sys.stdin).get("tool_input", {})
path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
rel = os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/") if path else ""

if rel.startswith("notebooks/") and rel.endswith(".ipynb"):
    print(
        "Blocked: do not open notebooks/*.ipynb. Edit the paired jupytext/*.py file; "
        "run results are read with .agents/tools/nb_summary.py (report steps only).",
        file=sys.stderr,
    )
    sys.exit(2)
