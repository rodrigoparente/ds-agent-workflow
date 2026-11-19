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


def ensure_nbstripout_installed(root: Path) -> None:
    """Idempotently register nbstripout git filter in `.git/config` if not already configured."""
    git_dir = root / ".git"
    if not git_dir.exists() or not shutil.which("git"):
        return
    chk = subprocess.run(
        ["git", "config", "--get", "filter.nbstripout.clean"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    if chk.returncode == 0 and chk.stdout.strip():
        return
    if shutil.which("uv"):
        sync_flag = ("--no-sync",) if (root / ".venv").exists() else ()
        subprocess.run(
            ["uv", "run", *sync_flag, "--quiet", "nbstripout", "--install"],
            capture_output=True,
            text=True,
            cwd=root,
        )
    elif shutil.which("nbstripout"):
        subprocess.run(
            ["nbstripout", "--install"],
            capture_output=True,
            text=True,
            cwd=root,
        )


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

    return "\n".join(lines)


def main() -> None:
    ctx = parse_payload()
    ensure_nbstripout_installed(ctx.root)
    summary = build_context_summary(ctx.root)
    emit_session_start(ctx, summary)


if __name__ == "__main__":
    main()
