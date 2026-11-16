#!/usr/bin/env python3
"""Print a run notebook as readable text: markdown, code (first line, or all with --code), outputs.

Usage: python .agents/tools/nb_summary.py notebooks/x.ipynb [--code] [--max 1500]
Outputs are truncated to --max characters each; images are listed, not dumped.
"""
import json
import sys

args = sys.argv[1:]
path = next((a for a in args if a.endswith(".ipynb")), None)
if not path:
    sys.exit(__doc__)
show_code = "--code" in args
limit = int(args[args.index("--max") + 1]) if "--max" in args else 1500
nb = json.load(open(path))


def text(x):
    return "".join(x) if isinstance(x, list) else x


def clip(s):
    return s if len(s) <= limit else s[:limit] + f"\n... [truncated, {len(s)} chars]"


n_outputs = 0
for i, cell in enumerate(nb["cells"]):
    src = text(cell["source"])
    if cell["cell_type"] == "markdown":
        print(f"\n[md {i}]\n{src}")
        continue
    first = src.splitlines()[0] if src.strip() else ""
    print(f"\n[code {i}]\n{src}" if show_code else f"\n[code {i}] {first} ...")
    for out in cell.get("outputs", []):
        n_outputs += 1
        kind = out["output_type"]
        if kind == "stream":
            print(clip(text(out["text"])))
        elif kind == "error":
            print(f"ERROR {out['ename']}: {out['evalue']}")
        else:
            data = out.get("data", {})
            if "text/plain" in data:
                print(clip(text(data["text/plain"])))
            if "image/png" in data:
                print("[image output]")

if n_outputs == 0:
    print("\nNO OUTPUTS: this notebook has not been run yet.")
