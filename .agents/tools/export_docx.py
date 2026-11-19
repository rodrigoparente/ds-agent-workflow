#!/usr/bin/env python3
"""Convert a Markdown report to a Word (.docx) document using Pandoc.

Usage: uv run python .agents/tools/export_docx.py docs/reports/<NN-name>.md
Requires the optional 'docs' dependency group (`uv sync --group docs`).
"""

import sys
from pathlib import Path

import pypandoc


def main(paths: list[str]) -> None:
    for arg in paths:
        md_path = Path(arg).resolve()
        if not md_path.exists():
            sys.exit(f"File not found: {arg}")
        out_path = md_path.with_suffix(".docx")
        pypandoc.convert_file(
            str(md_path),
            "docx",
            outputfile=str(out_path),
            extra_args=[f"--resource-path={md_path.parent}"],
        )
        print(f"Exported: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
