#!/usr/bin/env python3
"""Format, check and sync an experiment notebook (jupytext percent .py file).

Usage: python3 .agents/tools/check_notebook.py notebooks/py/<name>.py [more.py ...]
Runs ruff format + ruff check, enforces the size/documentation budget from write-code/SKILL.md,
checks that every imported package is in the install cell, catches bare relative project
paths and unsaved plots, then syncs the paired .ipynb in notebooks/. Prints problems
and exits 1 if anything is wrong. Any tool or person can run it; coding agents also run
it automatically through .agents/hooks/lint.py.
"""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agents" / "hooks"))
from common import run_project_tool, run_ruff  # noqa: E402

# Keep these thresholds in sync with .agents/skills/write-code/SKILL.md
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
PROVIDED = {"IPython", "scripts", "apps"}  # workspace & notebook builtins
# calls that need a package which is never imported explicitly
IMPLICIT = {
    ".to_markdown(": "tabulate",
    "_parquet(": "pyarrow",
    "read_excel(": "openpyxl",
    ".to_excel(": "openpyxl",
    ".write_image(": "kaleido",
}
BARE_DIRS = {"models", "data", "docs/figures"}
LOG_CALLS = {"print", "warn", "debug", "info", "warning", "error"}
REL_PATH_PREFIXES = (
    "models/",
    "data/",
    "docs/figures/",
    "./models",
    "./data",
    "../models",
    "../data",
    "../docs/figures",
)
PLOT_ROOTS = {"plt", "sns", "px"}
PLOT_NON_DRAW = {
    "show",
    "close",
    "tight_layout",
    "savefig",
    "rc",
    "rcdefaults",
    "set",
    "set_theme",
    "set_style",
    "set_context",
    "set_palette",
    "color_palette",
    "despine",
    "ion",
    "ioff",
    "switch_backend",
    "use",
}
PLOT_CALLS = {
    "subplots",
    "figure",
    "ConfusionMatrixDisplay",
    "RocCurveDisplay",
    "PrecisionRecallDisplay",
}
DISPLAY_FNS = {"from_estimator", "from_predictions"}

STRING = re.compile(r'("""|\'\'\').*?\1', re.S)  # long SQL lives in triple-quoted strings


def collapse_strings(text):
    """Replace each triple-quoted string with a one-line stub so SQL doesn't count as code."""
    return STRING.sub('"""..."""', text)


def run(*cmd):
    """Run a tool through .venv/bin, venv/bin, VIRTUAL_ENV, or PATH. Returns None if missing."""
    return run_project_tool(ROOT, *cmd)


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
    """Package names listed on `# # %pip install ...` or `# %pip install ...` lines."""
    pkgs = set()
    for line in text.splitlines():
        m = re.match(r"\s*#(?:\s*#)?\s*[%!]pip install(.*)", line)
        for tok in m.group(1).split() if m else []:
            tok = tok.strip("\"'")
            name = re.match(r"[A-Za-z0-9_.-]+", tok)
            if not tok.startswith("-") and name:
                pkgs.add(norm(name.group(0)))
    return pkgs


def _imported_roots(tree) -> set[str]:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def _is_local_module(name: str, path: str) -> bool:
    here = [
        Path(path).parent / f"{name}.py",
        ROOT / name,
        ROOT / "scripts" / f"{name}.py",
        ROOT / "scripts" / name,
    ]
    return any(p.exists() for p in here)


def _code_text(text: str) -> str:
    """Return non-comment code lines across code cells (excluding triple-quoted strings)."""
    return "\n".join(
        ln
        for kind, lines in parse_cells(collapse_strings(text))
        if kind == "code"
        for ln in lines
        if not ln.lstrip().startswith("#")
    )


def missing_installs(tree, text, path):
    """Third-party packages the notebook needs that the install cell does not list."""
    if tree is None:
        return []
    have = installed_packages(text)
    code = _code_text(text)
    need = [
        PIP_NAME.get(name, name)
        for name in sorted(_imported_roots(tree))
        if name not in sys.stdlib_module_names
        and name not in PROVIDED
        and not _is_local_module(name, path)
    ]
    need += [pkg for call, pkg in IMPLICIT.items() if call in code and pkg not in need]
    return [pkg for pkg in need if norm(pkg) not in have]


def structural_problems(tree):
    """Detect classes, oversized helper functions, and defensive try/except bloat via AST."""
    if tree is None:
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


def _count_code_lines(text):
    """Return total non-comment code lines across all code cells in text."""
    total = 0
    for kind, lines in parse_cells(collapse_strings(text)):
        if kind == "code":
            total += sum(1 for ln in lines if not ln.lstrip().startswith("#"))
    return total


def _install_cell_problem(lines: list[str]) -> str | None:
    has_commented = any(re.match(r"\s*#\s*#\s*%pip install\b", ln) for ln in lines)
    if has_commented:
        return None
    if any(re.match(r"\s*#\s*%pip install\b", ln) for ln in lines):
        return (
            "Use double-hash `# # %pip install -q <packages>` in cell 1 so Jupytext keeps it "
            "commented inside `.ipynb` (single `#` runs live on every execution)."
        )
    return (
        "The first code cell must list packages via `# # %pip install -q <packages>` "
        "(stays commented in `.ipynb` so the notebook can be shared standalone)."
    )


def _total_budget_problem(total_code_lines, cell_sizes, before_code_lines) -> str | None:
    if total_code_lines <= MAX_LINES:
        return None
    top = ", ".join(f"Cell {idx} ({cnt})" for cnt, idx in sorted(cell_sizes, reverse=True)[:3])
    fmt_note = ""
    if before_code_lines is not None and total_code_lines > before_code_lines:
        fmt_note = (
            f" Note: `ruff format` expanded code from {before_code_lines} "
            f"to {total_code_lines} lines."
        )
    return (
        f"{total_code_lines} total code lines (max {MAX_LINES}). "
        f"Cut scope creep or move reusable helpers to scripts/. Largest cells: {top}.{fmt_note}"
    )


def _check_code_cell(
    idx: int, n_code: int, lines: list[str], prev_kind: str | None
) -> tuple[list[str], int]:
    issues: list[str] = []
    if n_code == 1 and (pip_msg := _install_cell_problem(lines)):
        issues.append(pip_msg)
    code_lines = [ln for ln in lines if not ln.lstrip().startswith("#")]
    if len(code_lines) > MAX_CELL:
        issues.append(
            f"Cell {idx + 1} has {len(code_lines)} code lines (max {MAX_CELL}). "
            "Split into logical cells or simplify."
        )
    if n_code > SETUP_CELLS and prev_kind != "md":
        issues.append(
            f"Cell {idx + 1} has no markdown cell before it (what + why in 1-2 sentences)."
        )
    return issues, len(code_lines)


def cell_problems(cells, before_code_lines=None):
    """Check per-cell and total code-line budgets and markdown headers."""
    out = []
    n_code = 0
    total_code_lines = 0
    cell_sizes = []
    for i, (kind, lines) in enumerate(cells):
        if kind != "code":
            continue
        n_code += 1
        prev_kind = cells[i - 1][0] if i > 0 else None
        issues, n_lines = _check_code_cell(i, n_code, lines, prev_kind)
        out.extend(issues)
        total_code_lines += n_lines
        cell_sizes.append((n_lines, i + 1))
    if total_msg := _total_budget_problem(total_code_lines, cell_sizes, before_code_lines):
        out.append(total_msg)
    return out


def _string_prefix(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        first = node.values[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return first.value
    return None


def _is_div_rhs(node: ast.AST, parent: ast.AST | None) -> bool:
    return isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div) and parent.right is node


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _relative_path_error(node: ast.AST, parent: ast.AST | None) -> str | None:
    if _is_div_rhs(node, parent):
        return None
    is_log = isinstance(parent, ast.Call) and _call_name(parent) in LOG_CALLS
    prefix = _string_prefix(node)
    if (
        prefix
        and not is_log
        and prefix.startswith(REL_PATH_PREFIXES)
        and not isinstance(parent, ast.JoinedStr)
    ):
        return (
            f"Relative path '{prefix}...' (line {node.lineno}) breaks when Jupyter runs from "
            "notebooks/. Use DATA / ..., MODELS / ..., or FIGURES / ... (anchored to ROOT)."
        )
    if (
        isinstance(node, ast.Call)
        and _call_name(node) in {"Path", "mkdir", "makedirs"}
        and node.args
        and (bad := _string_prefix(node.args[0])) in BARE_DIRS
    ):
        return (
            f"Relative path '{bad}' (line {node.lineno}) breaks when Jupyter runs from "
            "notebooks/. Use DATA, MODELS, or FIGURES (anchored to ROOT)."
        )
    return None


def relative_path_problems(tree) -> list[str]:
    """Flag bare project-relative paths that break when Jupyter executes from notebooks/."""
    if tree is None:
        return []
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    out: list[str] = []
    for node in ast.walk(tree):
        if msg := _relative_path_error(node, parents.get(node)):
            out.append(msg)
    return out


def _is_plot_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in PLOT_CALLS
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr in PLOT_CALLS or func.attr == "plot":
        return True
    if func.attr in DISPLAY_FNS and isinstance(func.value, ast.Name):
        return "Display" in func.value.id
    if isinstance(func.value, ast.Name) and func.value.id in PLOT_ROOTS:
        return func.attr not in PLOT_NON_DRAW
    if isinstance(func.value, ast.Attribute) and func.value.attr == "plot":
        return True
    return False


def _is_save_call(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Name):
        return node.func.id == "savefig"
    if isinstance(node.func, ast.Attribute):
        return node.func.attr in {"savefig", "write_image"}
    return False


def unsaved_plot_problems(tree) -> list[str]:
    """Flag notebooks that create plots without saving any figure to FIGURES."""
    if tree is None:
        return []
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    has_plot = any(_is_plot_call(c) for c in calls)
    has_save = any(_is_save_call(c) for c in calls)
    if has_plot and not has_save:
        return [
            "Notebook creates plot(s) without saving any figure. Save key charts to "
            'FIGURES / f"{NAME}_<what>.png" (e.g. fig.savefig(..., dpi=150, bbox_inches="tight")) '
            "before plt.show() so reports and presentations can reuse them."
        ]
    return []


def problems_in(text, path=".", before_code_lines=None):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None  # ruff reports syntax errors
    out = []
    missing = missing_installs(tree, text, path)
    if missing:
        out.append(
            f"Not in the install cell: {', '.join(missing)}. Add to `# # %pip install -q ...`. "
            "(If pip name differs from import name, add to PIP_NAME in check_notebook.py.)"
        )
    out += structural_problems(tree)
    out += relative_path_problems(tree)
    out += unsaved_plot_problems(tree)
    cells = parse_cells(collapse_strings(text))
    if not cells or cells[0][0] != "md":
        out.append("First cell must be markdown: title, overview/question, and spec link.")
    return out + cell_problems(cells, before_code_lines=before_code_lines)


def _sync_ipynb(path: str) -> list[str]:
    """Sync paired .ipynb via jupytext and return any sync errors."""
    nb_path = Path(path)
    nb_dir = nb_path.parent.parent if nb_path.parent.name == "py" else ROOT / "notebooks"
    nb_dir.mkdir(parents=True, exist_ok=True)
    sync_res = run("jupytext", "--sync", path)
    if sync_res is None:
        return ["jupytext is not installed or not found (run `uv sync`)."]
    if sync_res.returncode != 0:
        err = (sync_res.stdout or sync_res.stderr).strip()
        return [f"jupytext --sync failed:\n{err}"]
    expected_ipynb = nb_dir / f"{nb_path.stem}.ipynb"
    if nb_path.parent.name == "py" and not expected_ipynb.exists():
        return [
            f"jupytext --sync completed but {expected_ipynb} was not generated. "
            "Check jupytext.toml pairing."
        ]
    return []


def check_one_notebook(path: str) -> list[str]:
    """Format, lint, validate, and sync a single notebook .py file."""
    with open(path, encoding="utf-8") as f:
        before_code_lines = _count_code_lines(f.read())

    fatal, problems = run_ruff(run, path)
    if fatal:
        return problems

    with open(path, encoding="utf-8") as f:
        problems += problems_in(f.read(), path, before_code_lines=before_code_lines)
    return problems if problems else _sync_ipynb(path)


def main(paths):
    failed = False
    for path in paths:
        problems = check_one_notebook(path)
        if problems:
            failed = True
            print(f"{path} breaks the notebook rules in write-code/SKILL.md:")
            for item in problems:
                print(f"- {item}")
        else:
            print(f"{path}: ok")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
