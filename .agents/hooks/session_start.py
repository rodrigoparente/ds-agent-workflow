#!/usr/bin/env python3
"""SessionStart hook for Antigravity, Claude Code, and Cursor.

1. Automatically registers the `nbstripout` git filter in `.git/config` when `.git` is present
   so committed `notebooks/*.ipynb` files always have cell outputs stripped in Git while
   retaining local outputs on disk for `nb_summary.py`.
2. Injects a compact 2-3 line summary of the current git branch, existing specs (with their
   lifecycle status), and the next sequential initiative number (`NN`).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import emit_session_start, parse_payload


def _has_nbstripout_filter(root: Path) -> bool:
    """Return True if git filter.nbstripout.clean is configured in this repository."""
    if not (root / ".git").exists() or not shutil.which("git"):
        return False
    chk = subprocess.run(
        ["git", "config", "--get", "filter.nbstripout.clean"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    return chk.returncode == 0 and bool(chk.stdout.strip())


def ensure_nbstripout_installed(root: Path) -> None:
    """Idempotently register nbstripout git filter in `.git/config` if not already configured."""
    if not (root / ".git").exists() or not shutil.which("git") or _has_nbstripout_filter(root):
        return
    venv_nbstripout = root / ".venv" / "bin" / "nbstripout"
    if shutil.which("uv"):
        sync_flag = ("--no-sync",) if (root / ".venv").exists() else ()
        cmd = ["uv", "run", *sync_flag, "--quiet", "nbstripout", "--install"]
    elif venv_nbstripout.exists():
        cmd = [str(venv_nbstripout), "--install"]
    elif shutil.which("nbstripout"):
        cmd = ["nbstripout", "--install"]
    else:
        return
    subprocess.run(cmd, capture_output=True, text=True, cwd=root)


def _read_spec_status(spec_path: Path) -> str:
    try:
        head = spec_path.read_text(encoding="utf-8", errors="ignore")[:1500]
    except OSError:
        return "unknown"
    m = re.search(r"status:\s*(draft|approved|executed)", head, flags=re.I)
    return m.group(1).lower() if m else "unknown"


def build_context_summary(root: Path) -> str:
    """Build a compact 2-3 line workspace status summary."""
    lines: list[str] = []

    if (root / ".git").exists() and shutil.which("git"):
        br = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=root,
        )
        st = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=root,
        )
        branch = br.stdout.strip() or "HEAD"
        dirty = len([ln for ln in st.stdout.splitlines() if ln.strip()])
        lines.append(f"Git: branch `{branch}` ({dirty} uncommitted file(s))")

    specs_dir = root / "specs"
    spec_files = sorted(specs_dir.glob("*.md")) if specs_dir.exists() else []
    highest_num = 0
    spec_items: list[str] = []
    for sp in spec_files:
        m = re.match(r"^(\d+)-", sp.stem)
        if m:
            highest_num = max(highest_num, int(m.group(1)))
        spec_items.append(f"{sp.stem} ({_read_spec_status(sp)})")

    next_nn = f"{highest_num + 1:02d}"
    if spec_items:
        shown = " · ".join(spec_items[-10:])
        lines.append(f"Specs: {shown} | Next initiative prefix: `{next_nn}-`")
    else:
        lines.append(f"Specs: none yet | Next initiative prefix: `{next_nn}-`")

    warnings = _toolchain_warnings(root)
    lines.extend(warnings)
    return "\n".join(lines)


def _toolchain_warnings(root: Path) -> list[str]:
    """Return concise warning lines only when required workspace tooling is missing."""
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


def main() -> None:
    ctx = parse_payload()
    ensure_nbstripout_installed(ctx.root)
    summary = build_context_summary(ctx.root)
    emit_session_start(ctx, summary)


if __name__ == "__main__":
    main()
