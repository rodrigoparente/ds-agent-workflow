#!/usr/bin/env python3
"""Format, check and sync an experiment notebook (jupytext percent .py file).

Usage: python .agents/tools/check_notebook.py notebooks/py/<name>.py [more.py ...]
Runs ruff format, enforces the size/documentation budget from AGENTS.md, checks that every
imported package is in the install cell, then syncs the paired .ipynb in notebooks/.
Prints problems and exits 1 if anything is wrong. Any tool or person can run it; Claude Code
also runs it automatically through .claude/hooks/notebook_check.py."""
import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

MAX_LINES = 220  # max code lines across notebook (excluding markdown, comments, SQL)
MAX_CELL = 35  # max code lines per cell (excluding comments, blank lines, SQL)
MAX_DEF_LINES = 15  # max lines per local helper function (move larger ones to scripts/)
SETUP_CELLS = 2  # first two code cells (pip install, imports) need no markdown before them

# import name -> pip name, when they differ
PIP_NAME = {
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
    "PIL": "pillow",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "skimage": "scikit-image",
    "dotenv": "python-dotenv",
}
PROVIDED = {"pyspark", "IPython"}  # the notebook environment already has these
# calls that need a package which is never imported explicitly
IMPLICIT = {".to_markdown(": "tabulate", "_parquet(": "pyarrow", "read_excel(": "openpyxl"}

STRING = re.compile(r'("""|\'\'\').*?\1', re.S)  # long SQL lives in triple-quoted strings


def collapse_strings(text):
    """Replace each triple-quoted string with a one-line stub so SQL doesn't count as code."""
    return STRING.sub('"""..."""', text)


def run(*cmd):
    """Run a tool through uv if available, else directly. Returns None if not installed."""
    if shutil.which("uv"):
        sync_flag = ("--no-sync",) if Path(".venv").exists() else ()
        cmd = ("uv", "run", *sync_flag, "--quiet") + cmd
    elif not shutil.which(cmd[0]):
        return None
    return subprocess.run(cmd, capture_output=True, text=True)


def parse_cells(text):
    """Split a jupytext percent file into [(kind, body_lines)]."""
    cells = []
    for part in re.split(r"^# %%", text, flags=re.M)[1:]:
        header, _, body = part.partition("\n")
        kind = "md" if "[markdown]" in header else "code"
        cells.append((kind, [ln for ln in body.splitlines() if ln.strip()]))
    return cells


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def installed_packages(text):
    """Package names listed on `# %pip install ...` lines."""
    pkgs = set()
    for line in text.splitlines():
        m = re.match(r"#\s*[%!]pip install(.*)", line)
        for tok in (m.group(1).split() if m else []):
            tok = tok.strip("\"'")
            name = re.match(r"[A-Za-z0-9_.-]+", tok)
            if not tok.startswith("-") and name:
                pkgs.add(norm(name.group(0)))
    return pkgs


def missing_installs(text, path):
    """Third-party packages the notebook needs that the install cell does not list."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []  # ruff reports syntax errors
    have = installed_packages(text)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    need = []
    p = Path(path).resolve()
    proj_root = p.parents[2] if p.parent.name == "py" and len(p.parents) >= 3 else Path.cwd()
    for name in sorted(names):
        here = [
            p.parent / f"{name}.py",
            Path(name),
            proj_root / "scripts" / f"{name}.py",
            proj_root / "scripts" / name,
            proj_root / name,
            Path("scripts") / f"{name}.py",
            Path("scripts") / name,
        ]
        local = any(p.exists() for p in here)  # the project's own code, e.g. scripts/helpers.py
        if name in sys.stdlib_module_names or name in PROVIDED or local:
            continue
        need.append(PIP_NAME.get(name, name))
    need += [pkg for call, pkg in IMPLICIT.items() if call in text and pkg not in need]
    return [pkg for pkg in need if norm(pkg) not in have]


def structural_problems(text):
    """Detect classes, oversized helper functions, and defensive try/except bloat via AST."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            out.append(
                f"Class '{node.name}' defined in notebook (line {node.lineno}). "
                "Keep notebook code flat; use plain functions or move reusable code to scripts/."
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            span = (node.end_lineno or node.lineno) - node.lineno + 1
            if span > MAX_DEF_LINES:
                out.append(
                    f"Function '{node.name}' is {span} lines (max {MAX_DEF_LINES}). "
                    "Inline as flat cell steps or move reusable helpers to scripts/."
                )
        elif isinstance(node, ast.Try):
            out.append(
                f"Avoid try/except in notebooks (line {node.lineno}). "
                "Let errors fail visibly in cell outputs instead of wrapping them."
            )
    return out


def cell_problems(cells):
    """Check per-cell and total code-line budgets and markdown headers."""
    out = []
    n_code = 0
    total_code_lines = 0
    for i, (kind, lines) in enumerate(cells):
        if kind != "code":
            continue
        n_code += 1
        if n_code == 1 and not any("%pip install" in ln for ln in lines):
            out.append("The first code cell must be `# %pip install -q <packages>`.")
        code_lines = [ln for ln in lines if not ln.lstrip().startswith("#")]
        total_code_lines += len(code_lines)
        if len(code_lines) > MAX_CELL:
            out.append(
                f"Cell {i + 1} has {len(code_lines)} code lines (max {MAX_CELL}). "
                "Split into logical cells or simplify."
            )
        if n_code > SETUP_CELLS and cells[i - 1][0] != "md":
            out.append(
                f"Cell {i + 1} has no markdown cell before it (what + why in 1-2 sentences)."
            )
    if total_code_lines > MAX_LINES:
        out.append(
            f"{total_code_lines} total code lines (max {MAX_LINES}). "
            "Cut scope creep or move reusable helpers to scripts/."
        )
    return out


def problems_in(text, path="."):
    out = []
    missing = missing_installs(text, path)
    if missing:
        out.append(
            f"Not in the install cell: {', '.join(missing)}. Add to `# %pip install -q ...`. "
            "(If pip name differs from import name, add to PIP_NAME in check_notebook.py.)"
        )
    out += structural_problems(text)
    cells = parse_cells(collapse_strings(text))
    if not cells or cells[0][0] != "md":
        out.append("First cell must be markdown: title, overview/question, and spec link.")
    return out + cell_problems(cells)


def main(paths):
    failed = False
    for path in paths:
        problems = []
        run("ruff", "format", path)
        r = run("ruff", "check", "--fix", "--quiet", path)
        if r is not None and r.returncode != 0:
            problems.append("ruff:\n" + (r.stdout or r.stderr).strip())

        with open(path) as f:
            problems += problems_in(f.read(), path)

        p = Path(path)
        nb_dir = p.parent.parent if p.parent.name == "py" else Path("notebooks")
        nb_dir.mkdir(parents=True, exist_ok=True)
        sync_res = run("jupytext", "--sync", path)
        if sync_res is None:
            problems.append(
                "jupytext is not installed or not found in environment (run `uv sync`)."
            )
        elif sync_res.returncode != 0:
            err = (sync_res.stdout or sync_res.stderr).strip()
            problems.append(f"jupytext --sync failed:\n{err}")
        else:
            expected_ipynb = nb_dir / f"{p.stem}.ipynb"
            if p.parent.name == "py" and not expected_ipynb.exists():
                problems.append(
                    f"jupytext --sync completed but {expected_ipynb} was not generated. "
                    "Check jupytext.toml pairing."
                )

        if problems:
            failed = True
            print(f"{path} breaks the notebook rules in AGENTS.md:")
            for p in problems:
                print(f"- {p}")
        else:
            print(f"{path}: ok")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
