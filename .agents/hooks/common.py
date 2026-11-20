#!/usr/bin/env python3
"""Shared lifecycle hook helpers for Antigravity, Claude Code, and Cursor."""

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
    agent: str  # "antigravity" | "claude" | "cursor"
    root: Path
    file_path: str = ""
    stop_active: bool = False

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
    if env_root := os.environ.get("CLAUDE_PROJECT_DIR"):
        return Path(env_root).resolve()
    ws = payload.get("workspacePaths")
    if isinstance(ws, list) and ws:
        return Path(ws[0]).resolve()
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        p = Path(cwd).resolve()
        for parent in [p, *p.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        return p
    return Path(__file__).resolve().parents[2]


def parse_payload(stream: Any = None) -> HookContext:
    """Parse stdin JSON into a normalized HookContext."""
    raw_text = (stream or sys.stdin).read()
    try:
        data = json.loads(raw_text) if raw_text.strip() else {}
    except json.JSONDecodeError:
        data = {}

    root = _detect_root(data)

    if "toolCall" in data or "workspacePaths" in data or "continuationActive" in data:
        agent = "antigravity"
        args = (data.get("toolCall") or {}).get("args") or {}
        path = (
            args.get("Path")
            or args.get("TargetFile")
            or args.get("file_path")
            or args.get("notebook_path")
            or ""
        )
        stop_active = bool(data.get("continuationActive", False))
    elif "loop_count" in data or (
        "tool_input" not in data and ("file_path" in data or "file" in data)
    ):
        agent = "cursor"
        path = data.get("file_path") or data.get("file") or data.get("path") or ""
        stop_active = int(data.get("loop_count", 0) or 0) > 0
    else:
        agent = "claude"
        ti = data.get("tool_input") or {}
        path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
        stop_active = bool(data.get("stop_hook_active", False))

    return HookContext(agent=agent, root=root, file_path=path, stop_active=stop_active)


def run_project_tool(
    root: Path, *args: str, timeout: int | None = None
) -> subprocess.CompletedProcess[str] | None:
    """Run a CLI tool via `uv run`, `.venv/bin/`, or PATH; return None if unavailable."""
    venv_tool = root / ".venv" / "bin" / args[0]
    if shutil.which("uv"):
        sync_flag = ("--no-sync",) if (root / ".venv").exists() else ()
        cmd = ("uv", "run", *sync_flag, "--quiet", *args)
    elif venv_tool.exists():
        cmd = (str(venv_tool), *args[1:])
    elif shutil.which(args[0]):
        cmd = args
    else:
        return None
    return subprocess.run(cmd, capture_output=True, text=True, cwd=root, timeout=timeout)


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
    """Emit Stop hook result (block stop & force retry when tests fail) and exit."""
    if ctx.agent == "antigravity":
        payload = (
            {"decision": "continue", "reason": reason} if should_continue else {"decision": "allow"}
        )
        print(json.dumps(payload))
        sys.exit(0)
    if ctx.agent == "cursor":
        print(json.dumps({"followup_message": reason} if should_continue else {}))
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
