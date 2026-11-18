#!/usr/bin/env python3
"""PreToolUse hook:
1. Block direct reads/edits of notebooks/*.ipynb (use notebooks/py/*.py and nb_summary.py).
2. Block autonomous execution of notebooks, notebooks/py/*.py, data scripts, or python -c.
Exit 2 = block and return message to the agent."""

import json
import os
import re
import sys

payload = json.load(sys.stdin)
tool_name = payload.get("tool_name", "")
tool_input = payload.get("tool_input", {})
root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

# 1. Guard file reads/edits on notebooks/*.ipynb
path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
rel = os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/") if path else ""

if rel.startswith("notebooks/") and rel.endswith(".ipynb"):
    print(
        "Blocked: do not open notebooks/*.ipynb directly. Edit the paired notebooks/py/*.py file; "
        "read executed outputs with .agents/tools/nb_summary.py.",
        file=sys.stderr,
    )
    sys.exit(2)

# 2. Guard Bash commands from executing user/project experiment code
cmd = tool_input.get("command", "")
if tool_name == "Bash" and cmd:
    # Allow static checker, output summarizer, skill fetcher, deck compilation, ruff, and unit tests
    SAFE_PATTERNS = (
        r"\.agents/tools/(check_notebook|nb_summary|fetch_skill)\.py\b",
        r"\bscripts/build_[\w-]*deck\.py\b",
        r"\bruff\s+(check|format)\b",
        r"\bpytest\b",
    )
    if not any(re.search(pat, cmd) for pat in SAFE_PATTERNS):
        FORBIDDEN_PATTERNS = [
            r"\bpython3?\b.*\b(scripts|notebooks|apps)/",
            r"\bpython3?\s+-c\b",
            r"\b(nbconvert|jupyter\s+execute|jupyter\s+run|papermill|ipython|streamlit\s+run|uvicorn)\b",
        ]
        if any(re.search(pat, cmd) for pat in FORBIDDEN_PATTERNS):
            print(
                "Blocked: Do not execute experiments, notebooks, or data scripts—the user runs "
                "all experiments themselves. Only static verification (check_notebook.py), "
                "unit tests (pytest), and slide deck compilation (scripts/build_*_deck.py) "
                "are allowed.",
                file=sys.stderr,
            )
            sys.exit(2)
