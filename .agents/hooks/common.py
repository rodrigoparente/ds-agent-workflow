#!/usr/bin/env python3
"""Shared lifecycle hook helpers for Antigravity and Claude Code (plus Cursor via .claude/)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class HookContext:
    agent: str  # "antigravity" | "claude"
    root: Path
    file_path: str = ""
    stop_active: bool = False
    termination_reason: str = ""
    command: str = ""  # Bash command (Claude Code PreToolUse only)

    def rel_path(self) -> str:
        """Return project-relative forward-slash path, or empty string."""
        if not self.file_path:
            return ""
        expanded = os.path.expanduser(self.file_path)
        abs_p = (
            Path(expanded).resolve()
            if os.path.isabs(expanded)
            else (self.root / expanded).resolve()
        )
        try:
            return abs_p.relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return abs_p.as_posix()


def _detect_root(payload: dict[str, Any]) -> Path:
    ws = payload.get("workspacePaths")
    if isinstance(ws, list) and ws:
        return Path(ws[0]).resolve()
    if env_root := os.environ.get("CLAUDE_PROJECT_DIR"):
        return Path(env_root).resolve()
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        p = Path(cwd).resolve()
        for parent in [p, *p.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        return p
    return Path(__file__).resolve().parents[2]


def _venv_candidates(venv_dir: Path, tool: str) -> tuple[Path, Path]:
    return (venv_dir / "bin" / tool, venv_dir / "Scripts" / f"{tool}.exe")


def find_project_tool(root: Path, tool: str) -> str | None:
    """Locate a CLI executable in `.venv/`, `venv/`, `VIRTUAL_ENV`, or `PATH`."""
    venv_dirs = [root / ".venv", root / "venv"]
    if active := os.environ.get("VIRTUAL_ENV"):
        venv_dirs.append(Path(active))
    for venv_dir in venv_dirs:
        for candidate in _venv_candidates(venv_dir, tool):
            if candidate.is_file():
                return str(candidate)
    return shutil.which(tool)


def _extract_path(mapping: Any, *keys: str) -> str:
    if not isinstance(mapping, dict):
        return ""
    for key in keys:
        if val := mapping.get(key):
            return str(val)
    return ""


def parse_payload(stream: Any = None) -> HookContext:
    """Parse stdin JSON into a normalized HookContext."""
    raw_text = (sys.stdin if stream is None else stream).read().strip()
    try:
        data = json.loads(raw_text) if raw_text else {}
    except json.JSONDecodeError:
        data = {}

    root = _detect_root(data)
    if any(k in data for k in ("toolCall", "workspacePaths", "continuationActive")):
        tool_call = data.get("toolCall")
        args = tool_call.get("args") if isinstance(tool_call, dict) else None
        return HookContext(
            agent="antigravity",
            root=root,
            file_path=_extract_path(args, "Path", "TargetFile"),
            stop_active=bool(data.get("continuationActive", False)),
            termination_reason=str(data.get("terminationReason", "")),
        )

    return HookContext(
        agent="claude",
        root=root,
        file_path=_extract_path(data.get("tool_input"), "file_path", "notebook_path", "path"),
        stop_active=bool(data.get("stop_hook_active", False)),
        command=_extract_path(data.get("tool_input"), "command"),
    )


def git_stdout(root: Path, *args: str) -> str | None:
    """Run `git <args>` in `root` and return stdout on success, else None."""
    if not (root / ".git").exists() or not shutil.which("git"):
        return None
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=root)
    return r.stdout if r.returncode == 0 else None


def run_project_tool(
    root: Path, *args: str, timeout: int | None = None
) -> subprocess.CompletedProcess[str] | None:
    """Run a CLI tool via `.venv/`, `venv/`, `VIRTUAL_ENV`, or PATH; None if missing."""
    exe = find_project_tool(root, args[0])
    if exe is None:
        return None
    cmd = (exe, *args[1:])
    return subprocess.run(cmd, capture_output=True, text=True, cwd=root, timeout=timeout)


def run_ruff(runner: Any, target: str) -> tuple[bool, list[str]]:
    """Run ruff format and check via `runner`. Return `(fatal_format_error, errors)`."""
    fmt = runner("ruff", "format", "--quiet", target)
    if fmt is None:
        return False, ["ruff is not installed (run `uv sync`)."]
    if fmt.returncode != 0:
        out = (fmt.stderr or fmt.stdout).strip()
        return True, [f"ruff format:\n{out}"]
    chk = runner("ruff", "check", "--fix", "--unfixable", "F401", "--quiet", target)
    if chk is not None and chk.returncode != 0:
        out = (chk.stdout or chk.stderr).strip()
        return False, [f"ruff check:\n{out}"]
    return False, []


def emit_post_tool_feedback(ctx: HookContext, problem_text: str = "") -> None:
    """Emit PostToolUse result (feedback on lint failures) and exit."""
    if ctx.agent == "antigravity":
        print("{}")
        if problem_text:
            print(problem_text, file=sys.stderr)
        sys.exit(0)
    if problem_text:
        print(problem_text, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


def emit_stop_decision(ctx: HookContext, should_continue: bool, reason: str = "") -> None:
    """Emit Stop hook result (block stop & force retry when checks fail) and exit."""
    if ctx.agent == "antigravity":
        payload = (
            {"decision": "continue", "reason": reason} if should_continue else {"decision": "allow"}
        )
        print(json.dumps(payload))
        sys.exit(0)
    if should_continue:
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


def emit_session_start(ctx: HookContext, message: str) -> None:
    """Emit SessionStart context injection and exit."""
    msg = message.strip()
    if not msg:
        if ctx.agent == "antigravity":
            print("{}")
        sys.exit(0)
    if ctx.agent == "antigravity":
        print(json.dumps({"injectSteps": [{"systemMessage": {"systemMessage": msg}}]}))
        sys.exit(0)
    print(msg)
    sys.exit(0)
