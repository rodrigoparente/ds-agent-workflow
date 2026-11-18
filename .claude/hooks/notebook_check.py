#!/usr/bin/env python3
"""Claude Code PostToolUse hook: run .agents/tools/check_notebook.py on an edited notebooks/py/*.py.
Exit 2 sends the problems back to Claude so it fixes them."""
import json
import os
import subprocess
import sys

data = json.load(sys.stdin)
path = data.get("tool_input", {}).get("file_path", "")
root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
rel = os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/") if path else ""

if rel.startswith("notebooks/py/") and rel.endswith(".py"):
    r = subprocess.run(
        [sys.executable, os.path.join(root, ".agents/tools/check_notebook.py"), path],
        capture_output=True,
        text=True,
        cwd=root,
    )
    if r.returncode != 0:
        print(r.stdout + r.stderr, file=sys.stderr)
        sys.exit(2)
