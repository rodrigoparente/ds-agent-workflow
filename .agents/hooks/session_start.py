#!/usr/bin/env python3
"""SessionStart hook: ensures nbstripout is installed and injects git/spec context."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import emit_session_start, parse_payload, run_project_tool


def _git_stdout(root: Path, *args: str) -> str | None:
    if not (root / ".git").exists() or not shutil.which("git"):
        return None
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=root)
    return r.stdout if r.returncode == 0 else None


def _has_nbstripout_filter(root: Path) -> bool:
    out = _git_stdout(root, "config", "--get", "filter.nbstripout.clean")
    return bool(out and out.strip())


def ensure_nbstripout_installed(root: Path) -> None:
    """Idempotently register nbstripout git filter in `.git/config`."""
    if (root / ".git").exists() and shutil.which("git") and not _has_nbstripout_filter(root):
        run_project_tool(root, "nbstripout", "--install")


def _read_spec_status(spec_path: Path) -> str:
    try:
        head = spec_path.read_text(encoding="utf-8", errors="ignore")[:1500]
    except OSError:
        return "unknown"
    m = re.search(r"status:\s*(draft|approved|executed)", head, flags=re.I)
    return m.group(1).lower() if m else "unknown"


def _toolchain_warnings(root: Path) -> list[str]:
    warnings: list[str] = []
    has_uv = bool(shutil.which("uv"))
    has_venv = (root / ".venv").exists()
    if not has_uv and not has_venv:
        warnings.append(
            "Warning: `uv` not found on PATH and `.venv/` is missing; "
            "install `uv` and run `uv sync`."
        )
    elif not has_uv:
        warnings.append(
            "Warning: `uv` not found on PATH; hooks will fall back to `.venv/bin/` where present."
        )
    elif not has_venv:
        warnings.append(
            "Warning: `.venv/` is missing; run `uv sync` to enable lint, notebook sync, and tests."
        )
    if (root / ".git").exists() and shutil.which("git") and not _has_nbstripout_filter(root):
        warnings.append(
            "Warning: `nbstripout` git filter is not configured; run `uv run nbstripout --install`."
        )
    return warnings


def build_context_summary(root: Path) -> str:
    """Build a compact workspace status summary."""
    lines: list[str] = []

    if (branch_out := _git_stdout(root, "branch", "--show-current")) is not None:
        branch = branch_out.strip() or "HEAD"
        status_out = _git_stdout(root, "status", "--porcelain") or ""
        dirty = len([ln for ln in status_out.splitlines() if ln.strip()])
        lines.append(f"Git: branch `{branch}` ({dirty} uncommitted file(s))")

    specs_dir = root / "specs"
    spec_files = sorted(specs_dir.glob("*.md")) if specs_dir.exists() else []
    highest_num = 0
    spec_items: list[str] = []
    for sp in spec_files:
        if m := re.match(r"^(\d+)-", sp.stem):
            highest_num = max(highest_num, int(m.group(1)))
        spec_items.append(f"{sp.stem} ({_read_spec_status(sp)})")

    next_nn = f"{highest_num + 1:02d}"
    specs_text = " · ".join(spec_items[-10:]) if spec_items else "none yet"
    lines.append(f"Specs: {specs_text} | Next initiative prefix: `{next_nn}-`")
    lines.extend(_toolchain_warnings(root))
    return "\n".join(lines)


def main() -> None:
    ctx = parse_payload()
    ensure_nbstripout_installed(ctx.root)
    emit_session_start(ctx, build_context_summary(ctx.root))


if __name__ == "__main__":
    main()
