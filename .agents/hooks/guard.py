#!/usr/bin/env python3
"""PreToolUse guardrail hook for Antigravity, Claude Code, and Cursor.

Enforces project rules deterministically across all three coding agents:
1. Block direct reads/edits of notebooks/*.ipynb (use notebooks/py/*.py and nb_summary.py).
2. Block reads of raw datasets in data/ (use data-catalog schemas) and secrets (.env, ~/.ssh).
3. Block autonomous execution of notebooks, scripts, apps, or inline Python (user runs experiments).
4. Block raw `pip install` (use notebook `# %pip install` cell or ask the user to run `uv add`).
5. Block destructive shell commands (`rm -rf`, `git push --force`, `git reset --hard`).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HookContext, emit_pre_tool_decision, parse_payload

MSG_IPYNB = (
    "Blocked: do not open or edit notebooks/*.ipynb directly. Edit the paired "
    "notebooks/py/<NN-name>.py file; read executed outputs with "
    "`uv run python .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`."
)
MSG_DATA = (
    "Blocked: do not read raw files in data/ directly (PII & context bloat risk). "
    "Consult `.agents/skills/data-catalog/SKILL.md` for schemas and sample rows, or ask the user."
)
MSG_SECRETS = "Blocked: reading secret or credential files (.env, ~/.ssh) is not allowed."
MSG_EXEC = (
    "Blocked: Do not execute experiments, notebooks, apps, or data scripts—the user runs "
    "all experiments themselves. Only static verification (`check_notebook.py`, `ruff`), "
    "output inspection (`nb_summary.py`), unit tests (`pytest`), report export (`export_docx.py`), "
    "and slide deck compilation (`scripts/build_*_deck.py`) are allowed."
)
MSG_PIP = (
    "Blocked: do not run `pip install` directly in the workspace environment. "
    "For notebook dependencies, add the package to the `# %pip install -q ...` cell in "
    "`notebooks/py/<NN-name>.py`. For workspace tooling, ask the user or use `uv add`."
)
MSG_DESTRUCTIVE = (
    "Blocked: destructive command (`rm -rf`, `git push --force`, or `git reset --hard`) "
    "is not allowed. Delete specific files or ask the user to run the command manually."
)

UV_PREFIX = r"^(?:uv\s+run\s+(?:--[\w=-]+\s+)*)?"

# Segment prefixes that are explicitly allowed to invoke Python or project tools
SAFE_SEGMENT_PATTERNS = (
    UV_PREFIX
    + r"(?:python3?\s+)?(?:\./)?\.agents/tools/"
    + r"(?:check_notebook|nb_summary|export_docx)\.py(?:\s|$)",
    UV_PREFIX + r"(?:python3?\s+)?(?:\./)?\.agents/hooks/\w+\.py(?:\s|$)",
    UV_PREFIX + r"(?:python3?\s+)?(?:\./)?scripts/build_[\w-]*deck\.py(?:\s|$)",
    UV_PREFIX + r"(?:python3?\s+-m\s+)?pytest(?:\s|$)",
    UV_PREFIX + r"(?:python3?\s+-m\s+)?ruff\s+(?:check|format)(?:\s|$)",
    UV_PREFIX + r"jupytext\s+--sync(?:\s|$)",
    UV_PREFIX + r"nbstripout(?:\s|$)",
    r"^uv\s+(?:sync|lock|venv|tree|version)(?:\s|$)",
)

FORBIDDEN_RUNTIMES = (
    UV_PREFIX + r"python3?(?:\s|$)",
    r"^uv\s+run\b",
    r"^uvx\b",
    r"^(?:uv\s+run\s+.*)?\b(?:ipython|jupyter|nbconvert|papermill|marimo|streamlit|uvicorn|gunicorn|fastapi|flask|gradio|panel|voila)\b",
    r"\bjupytext\b.*--execute\b",
    r"^(?:\./)?(?:scripts|notebooks|apps)/\S+\.py\b",
)

# Shell commands that read files (`cat notebooks/x.ipynb`, `cat .env`, `head data/x.csv`)
FILE_READ_CMDS = r"\b(?:cat|head|tail|less|more|grep|rg|awk|sed|jq|strings|base64)\b"
ENV_PREFIX_RE = re.compile(
    r"^(?:env\s+|[A-Za-z_][A-Za-z0-9_]*=(?:\"[^\"]*\"|'[^']*'|\S+)\s+|time\s+)+"
)


def check_file_path(rel: str, raw_path: str) -> tuple[str, str] | None:
    """Check a normalized project-relative path (and raw path) against file access rules."""
    if not rel and not raw_path:
        return None
    norm_raw = os.path.expanduser(raw_path).replace(os.sep, "/")
    base = Path(rel or norm_raw).name

    if base == ".env" or (
        base.startswith(".env.") and not base.endswith((".example", ".sample", ".template"))
    ):
        return ("deny", MSG_SECRETS)
    if "/.ssh/" in norm_raw or norm_raw.endswith("/.ssh") or rel.startswith(".ssh/"):
        return ("deny", MSG_SECRETS)

    if (rel.startswith("notebooks/") or "/notebooks/" in norm_raw) and (
        rel.endswith(".ipynb") or norm_raw.endswith(".ipynb")
    ):
        return ("deny", MSG_IPYNB)

    if rel == "data" or rel.startswith("data/"):
        return ("deny", MSG_DATA)

    return None


def _strip_comments_and_split(cmd: str) -> list[str]:
    """Strip end-of-line comments and split a shell command into independent segments."""
    cleaned = [re.sub(r"(?:^|\s)#.*$", "", line).strip() for line in cmd.splitlines()]
    joined = "\n".join(line for line in cleaned if line)
    subshells = re.findall(r"\$\(([^)]+)\)|`([^`]+)`", joined)
    parts = re.split(r"\s*(?:&&|\|\||;|\||\n)\s*", joined)
    for s0, s1 in subshells:
        parts.extend(re.split(r"\s*(?:&&|\|\||;|\||\n)\s*", s0 or s1))
    return [p.strip() for p in parts if p.strip()]


def _normalize_segment(seg: str) -> str:
    """Strip leading env assignments, time, or harmless wrappers from a command segment."""
    s = seg.strip()
    while m := ENV_PREFIX_RE.match(s):
        s = s[m.end() :].strip()
    return s


def _check_shell_file_reads(s: str) -> tuple[str, str] | None:
    """Check whether a shell segment reads protected files (.ipynb, data/, .env, ~/.ssh)."""
    if not (re.search(FILE_READ_CMDS, s) or re.match(r"^(?:<|cat\b)", s)):
        return None
    if re.search(r"(?:^|[\s\"'=])(?:\./)?notebooks/[^\s\"']*\.ipynb\b", s):
        return ("deny", MSG_IPYNB)
    if re.search(r"(?:^|[\s\"'=])(?:\./)?data/", s):
        return ("deny", MSG_DATA)
    env_pat = (
        r"(?:^|[\s\"'=/])\.env(?:\.(?!example\b|sample\b|template\b)[A-Za-z0-9_-]+)?(?:\s|\"|'|$)"
    )
    if re.search(env_pat, s) or re.search(r"(?:~|\$HOME)/\.ssh\b", s):
        return ("deny", MSG_SECRETS)
    return None


def _check_destructive_or_pkg(s: str) -> tuple[str, str] | None:
    """Check a shell segment for destructive commands or raw pip/uv package installs."""
    if (
        re.search(r"\brm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive)\b", s)
        or re.search(r"\bgit\s+push\b.*(?:\s--force\b|\s--force-with-lease\b|\s-f\b)", s)
        or re.search(r"\bgit\s+reset\s+--hard\b", s)
    ):
        return ("deny", MSG_DESTRUCTIVE)

    if re.search(r"^(?:uv\s+)?pip3?\s+install\b", s) or re.search(
        r"\bpython3?\s+-m\s+pip\s+install\b", s
    ):
        return ("deny", MSG_PIP)

    if re.match(r"^uv\s+(?:add|remove)\b", s):
        return ("ask", "Modify project dependencies in pyproject.toml?")
    return None


def _check_segment(seg: str) -> tuple[str, str] | None:
    """Evaluate a single command segment. Returns (decision, reason) or None if allowed."""
    s = _normalize_segment(seg)
    if not s:
        return None

    m_shell = re.match(r"^(?:ba|z|da|k)?sh\s+-c\s+(['\"])(.*)\1\s*$", s, flags=re.S)
    if m_shell:
        return check_shell_command(m_shell.group(2))

    res = _check_destructive_or_pkg(s) or _check_shell_file_reads(s)
    if res is not None:
        return res

    if (
        "<<" not in s
        and not re.search(r"--execute\b", s)
        and any(re.match(pat, s) for pat in SAFE_SEGMENT_PATTERNS)
    ):
        return None

    if any(re.search(pat, s) for pat in FORBIDDEN_RUNTIMES):
        return ("deny", MSG_EXEC)
    return None


def _update_cd_state(norm: str, in_code_dir: bool) -> tuple[bool, bool]:
    """Return (is_cd_command, new_in_code_dir_state)."""
    m_cd = re.match(r"^cd\s+(['\"]?)([^'\";]+)\1$", norm)
    if not m_cd:
        return (False, in_code_dir)
    target = m_cd.group(2).strip().strip("/")
    if target.startswith(("notebooks", "scripts", "apps")):
        return (True, True)
    if target in ("..", "-", "~"):
        return (True, False)
    return (True, in_code_dir)


def check_shell_command(cmd: str) -> tuple[str, str] | None:
    """Validate a shell command string across all segments, tracking `cd` into protected dirs."""
    if not cmd or not cmd.strip():
        return None
    if re.search(r"\b(?:uv\s+run\s+)?python3?\b[^;\n]*<<", cmd):
        return ("deny", MSG_EXEC)

    in_code_dir = False
    for seg in _strip_comments_and_split(cmd):
        norm = _normalize_segment(seg)
        is_cd, in_code_dir = _update_cd_state(norm, in_code_dir)
        if is_cd:
            continue
        if in_code_dir and re.search(r"\b(?:python3?|uv\s+run)\b", norm):
            return ("deny", MSG_EXEC)
        res = _check_segment(norm)
        if res is not None:
            return res
    return None


def evaluate(ctx: HookContext) -> tuple[str, str]:
    """Return (decision, reason) for a HookContext ('allow' | 'deny' | 'ask')."""
    if ctx.kind in ("read", "write") or ctx.file_path:
        file_res = check_file_path(ctx.rel_path(), ctx.file_path)
        if file_res is not None:
            return file_res
    if ctx.kind == "shell" or ctx.command:
        cmd_res = check_shell_command(ctx.command)
        if cmd_res is not None:
            return cmd_res
    return ("allow", "")


def main() -> None:
    ctx = parse_payload()
    decision, reason = evaluate(ctx)
    emit_pre_tool_decision(ctx, decision, reason)


if __name__ == "__main__":
    main()
