#!/usr/bin/env python3
"""Shared lifecycle hook payload adapter for Antigravity, Claude Code, and Cursor.

Normalizes stdin JSON payloads across tools and writes the appropriate exit code / stdout JSON.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

READ_TOOLS = {
    "Read",
    "read_file",
    "view_file",
    "view_file_outline",
    "view_code_item",
}
WRITE_TOOLS = {
    "Edit",
    "Write",
    "MultiEdit",
    "NotebookEdit",
    "edit_file",
    "write_file",
    "replace_file_content",
    "multi_replace_file_content",
}
SHELL_TOOLS = {"Bash", "run_command"}


@dataclass
class HookContext:
    agent: str  # "antigravity" | "claude" | "cursor"
    event: str
    root: Path
    kind: str  # "shell" | "read" | "write" | "other"
    tool_name: str
    command: str
    file_path: str
    stop_active: bool
    raw: dict[str, Any]

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
    env_root = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_root:
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
    here = Path(__file__).resolve()
    return here.parents[2]


def parse_payload(stream: Any = None) -> HookContext:
    """Parse JSON from stdin (or provided stream) into a normalized HookContext."""
    raw_text = (stream or sys.stdin).read()
    try:
        data = json.loads(raw_text) if raw_text.strip() else {}
    except json.JSONDecodeError:
        data = {}

    root = _detect_root(data)
    event = data.get("hookEventName") or data.get("hook_event_name") or ""

    if "toolCall" in data or "workspacePaths" in data or "continuationActive" in data:
        agent = "antigravity"
        tc = data.get("toolCall") or {}
        tool_name = tc.get("name", "")
        args = tc.get("args") or {}
        cmd = args.get("CommandLine") or args.get("command") or ""
        path = (
            args.get("Path")
            or args.get("TargetFile")
            or args.get("file_path")
            or args.get("notebook_path")
            or ""
        )
        stop_active = bool(data.get("continuationActive", False))
    elif "loop_count" in data or (
        "command" in data and "tool_name" not in data and "tool_input" not in data
    ):
        agent = "cursor"
        tool_name = data.get("tool_name", "")
        cmd = data.get("command", "")
        path = data.get("file_path") or data.get("file") or data.get("path") or ""
        stop_active = int(data.get("loop_count", 0) or 0) > 0
    else:
        agent = "claude"
        tool_name = data.get("tool_name", "")
        ti = data.get("tool_input") or {}
        cmd = ti.get("command", "")
        path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
        stop_active = bool(data.get("stop_hook_active", False))

    if tool_name in SHELL_TOOLS or (cmd and not tool_name):
        kind = "shell"
    elif tool_name in READ_TOOLS:
        kind = "read"
    elif tool_name in WRITE_TOOLS or (path and not tool_name):
        kind = "write"
    else:
        kind = "other"

    return HookContext(
        agent=agent,
        event=event,
        root=root,
        kind=kind,
        tool_name=tool_name,
        command=cmd,
        file_path=path,
        stop_active=stop_active,
        raw=data,
    )


def emit_pre_tool_decision(ctx: HookContext, decision: str, reason: str = "") -> None:
    """Emit allow / deny / ask for PreToolUse and exit."""
    if ctx.agent == "antigravity":
        out: dict[str, Any] = {"decision": decision}
        if reason:
            out["reason"] = reason
        print(json.dumps(out))
        sys.exit(0)
    if ctx.agent == "cursor":
        out = {"permission": decision}
        if reason:
            out["agentMessage"] = reason
        print(json.dumps(out))
        sys.exit(2 if decision == "deny" else 0)
    # Claude Code
    if decision == "deny":
        print(reason, file=sys.stderr)
        sys.exit(2)
    if decision == "ask":
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "ask",
                        "permissionDecisionReason": reason,
                    }
                }
            )
        )
    sys.exit(0)


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
        if should_continue:
            print(json.dumps({"decision": "continue", "reason": reason}))
        else:
            print(json.dumps({"decision": "allow"}))
        sys.exit(0)
    if ctx.agent == "cursor":
        if should_continue:
            print(json.dumps({"followup_message": reason}))
        else:
            print("{}")
        sys.exit(0)
    if should_continue:
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


def emit_session_start(ctx: HookContext, message: str) -> None:
    """Emit SessionStart context injection and exit."""
    if not message.strip():
        if ctx.agent == "antigravity":
            print("{}")
        sys.exit(0)
    if ctx.agent == "antigravity":
        print(
            json.dumps(
                {
                    "injectSteps": [
                        {"systemMessage": {"systemMessage": message.strip()}},
                    ]
                }
            )
        )
        sys.exit(0)
    print(message.strip())
    sys.exit(0)
