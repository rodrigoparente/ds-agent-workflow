#!/usr/bin/env python3
"""Print a run notebook as readable text: markdown, code (first line, or all with --code), outputs.

Usage: python .agents/tools/nb_summary.py notebooks/x.ipynb [--code] [--max 1500]
Outputs are truncated to --max characters each; images and rich media are listed, not dumped.
"""

import argparse
import json
import re
import sys

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

RICH_MIME_LABELS = (
    ("image/png", "[image output]"),
    ("image/jpeg", "[image output]"),
    ("image/svg+xml", "[svg output]"),
    ("application/vnd.plotly.v1+json", "[plotly output]"),
    ("application/vnd.jupyter.widget-view+json", "[widget output]"),
    ("text/html", "[html output]"),
)


def text(x):
    return "".join(x) if isinstance(x, list) else str(x)


def clip(s, limit):
    return s if len(s) <= limit else s[:limit] + f"\n... [truncated, {len(s)} chars]"


def strip_ansi(s):
    return ANSI_RE.sub("", s)


def _format_output(out: dict, limit: int) -> list[str]:
    """Format a single notebook cell output into readable summary lines."""
    kind = out.get("output_type", "")
    if kind == "stream":
        return [clip(text(out.get("text", "")), limit)]
    if kind == "error":
        lines = [f"ERROR {out.get('ename', 'Error')}: {out.get('evalue', '')}"]
        tb = [strip_ansi(line) for line in out.get("traceback", [])]
        if tb:
            lines.append("\n".join(tb[-5:]))
        return lines

    lines = []
    data = out.get("data", {})
    if "text/plain" in data:
        lines.append(clip(text(data["text/plain"]), limit))
    for mime, label in RICH_MIME_LABELS:
        if mime in data and (mime != "text/html" or "text/plain" not in data):
            lines.append(label)
    return lines


def _execution_footer(
    n_outputs: int, executed: int, total: int, counts: list[int], has_error: bool = False
) -> str:
    if n_outputs == 0 and executed == 0:
        return (
            "\nNO OUTPUTS: this notebook has not been run yet "
            "(or was run in JupyterLab without saving via Ctrl+S)."
        )
    summary = f"\n[Execution summary: {executed}/{total} code cells run]"
    if counts != sorted(counts) or len(set(counts)) != len(counts):
        summary += " — WARNING: cells were executed out of order; consider Restart & Run All."
    if executed < total or has_error:
        summary += (
            " — NOTE: if you already ran all cells in JupyterLab, "
            "save (Ctrl+S) so disk outputs update."
        )
    return summary


def _format_code_cell(
    idx: int, cell: dict, show_code: bool, limit: int
) -> tuple[list[str], int, int | None, bool, bool]:
    src = text(cell.get("source", ""))
    ec = cell.get("execution_count")
    cell_outputs = cell.get("outputs", [])
    was_run = ec is not None or bool(cell_outputs)
    has_error = any(out.get("output_type") == "error" for out in cell_outputs)
    tag = f" (exec #{ec})" if ec is not None else (" [UNRUN]" if not cell_outputs else "")
    first = src.splitlines()[0] if src.strip() else ""
    header = f"\n[code {idx}{tag}]\n{src}" if show_code else f"\n[code {idx}{tag}] {first} ..."
    lines = [header]
    for out in cell_outputs:
        lines.extend(_format_output(out, limit))
    return lines, len(cell_outputs), ec if isinstance(ec, int) else None, was_run, has_error


def summarize_notebook(path: str, show_code: bool = False, limit: int = 1500) -> str:
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)

    out_lines: list[str] = []
    n_outputs = 0
    total_code_cells = 0
    executed_code_cells = 0
    has_error = False
    exec_counts: list[int] = []

    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") == "markdown":
            out_lines.append(f"\n[md {i}]\n{text(cell.get('source', ''))}")
            continue
        total_code_cells += 1
        lines, cell_n_out, ec, was_run, cell_err = _format_code_cell(i, cell, show_code, limit)
        out_lines.extend(lines)
        n_outputs += cell_n_out
        executed_code_cells += int(was_run)
        has_error = has_error or cell_err
        if ec is not None:
            exec_counts.append(ec)

    out_lines.append(
        _execution_footer(n_outputs, executed_code_cells, total_code_cells, exec_counts, has_error)
    )
    return "\n".join(out_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", help="Path to the .ipynb file")
    parser.add_argument("--code", action="store_true", help="Print full cell code")
    parser.add_argument("--max", type=int, default=1500, help="Max characters per text output")
    args = parser.parse_args()
    if not args.notebook.endswith(".ipynb"):
        sys.exit(__doc__)
    print(summarize_notebook(args.notebook, show_code=args.code, limit=args.max))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main()
