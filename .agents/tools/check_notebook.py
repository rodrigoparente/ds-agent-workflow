#!/usr/bin/env python3
"""Format, check, and sync an experiment notebook (jupytext percent .py file).

Usage: python3 .agents/tools/check_notebook.py notebooks/py/<name>.py [more.py ...]
Runs ruff format + ruff check, enforces size/structure rules from code/SKILL.md,
checks that imported packages are listed in cell 1 (`# # %pip install -q ...`), catches bare
relative project paths, and syncs the paired .ipynb in notebooks/.
"""

import ast
import importlib.metadata
import re
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agents" / "hooks"))
from common import run_project_tool, run_ruff  # noqa: E402

# Single source of truth for notebook size limits (code/SKILL.md points here).
MAX_LINES = 220
MAX_CELL = 35
MAX_DEF_LINES = 15

PIP_NAME = {
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
    "PIL": "pillow",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "skimage": "scikit-image",
    "dotenv": "python-dotenv",
    "pptx": "python-pptx",
    "docx": "python-docx",
    "dateutil": "python-dateutil",
}
PROVIDED = {"IPython", "scripts", "apps"}
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
STRING = re.compile(r'("""|\'\'\').*?\1', re.S)


def run(*cmd):
    """Run a tool through .venv/bin, venv/bin, VIRTUAL_ENV, or PATH."""
    return run_project_tool(ROOT, *cmd)


def parse_cells(text: str) -> list[tuple[str, list[str]]]:
    """Split a jupytext percent file into [(kind, body_lines)]."""
    cells = []
    for part in re.split(r"^# %%", text, flags=re.M)[1:]:
        header, _, body = part.partition("\n")
        kind = "md" if "[markdown]" in header else "code"
        cells.append((kind, [ln for ln in body.splitlines() if ln.strip()]))
    return cells


def _code_lines(cells: list[tuple[str, list[str]]]) -> list[str]:
    return [
        ln
        for kind, lines in cells
        if kind == "code"
        for ln in lines
        if not ln.lstrip().startswith("#")
    ]


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


@lru_cache(maxsize=1)
def _dist_map() -> dict[str, list[str]]:
    return importlib.metadata.packages_distributions()


def _pip_name(name: str) -> str:
    dists = _dist_map().get(name)
    return dists[0] if dists else PIP_NAME.get(name, name)


def installed_packages(text: str) -> set[str]:
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


def _is_external(name: str, path: str) -> bool:
    return (
        name not in sys.stdlib_module_names
        and name not in PROVIDED
        and not _is_local_module(name, path)
    )


def missing_installs(tree, text: str, path: str, code_str: str = "") -> list[str]:
    """Third-party packages the notebook needs that the install cell does not list."""
    if tree is None:
        return []
    have = installed_packages(text)
    need = [_pip_name(n) for n in sorted(_imported_roots(tree)) if _is_external(n, path)]
    need += [pkg for call, pkg in IMPLICIT.items() if call in code_str and pkg not in need]
    return [pkg for pkg in need if norm(pkg) not in have]


def structural_problems(tree) -> list[str]:
    """Detect classes and oversized helper functions via AST."""
    if tree is None:
        return []
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            out.append(
                f"Class '{node.name}' defined in notebook (line {node.lineno}). "
                "Keep notebook code flat; move reusable classes/helpers to scripts/."
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            span = (node.end_lineno or node.lineno) - node.lineno + 1
            if span > MAX_DEF_LINES:
                out.append(
                    f"Function '{node.name}' is {span} lines (max {MAX_DEF_LINES}). "
                    "Inline as flat cell steps or move reusable helpers to scripts/."
                )
    return out


def _install_cell_problem(lines: list[str]) -> str | None:
    if any(re.match(r"\s*#\s*#\s*%pip install\b", ln) for ln in lines):
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


def _total_budget_problem(
    total_code_lines: int, cell_sizes: list, before: int | None
) -> str | None:
    if total_code_lines <= MAX_LINES:
        return None
    top = ", ".join(f"Cell {idx} ({cnt})" for cnt, idx in sorted(cell_sizes, reverse=True)[:3])
    fmt_note = (
        f" Note: `ruff format` expanded code from {before} to {total_code_lines} lines."
        if before is not None and total_code_lines > before
        else ""
    )
    return (
        f"{total_code_lines} total code lines (max {MAX_LINES}). "
        f"Cut scope creep or move reusable helpers to scripts/. Largest cells: {top}.{fmt_note}"
    )


def cell_problems(cells: list[tuple[str, list[str]]], before_code_lines=None) -> list[str]:
    """Check install cell, per-cell limits, and total code-line budget."""
    out: list[str] = []
    n_code = 0
    total = 0
    sizes: list[tuple[int, int]] = []
    for i, (kind, lines) in enumerate(cells):
        if kind != "code":
            continue
        n_code += 1
        if n_code == 1 and (pip_msg := _install_cell_problem(lines)):
            out.append(pip_msg)
        n_lines = sum(1 for ln in lines if not ln.lstrip().startswith("#"))
        if n_lines > MAX_CELL:
            out.append(
                f"Cell {i + 1} has {n_lines} code lines (max {MAX_CELL}). "
                "Split into logical cells or simplify."
            )
        total += n_lines
        sizes.append((n_lines, i + 1))
    if total_msg := _total_budget_problem(total, sizes, before_code_lines):
        out.append(total_msg)
    return out


def _str_prefix(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        return _str_prefix(node.values[0])
    return None


def _call_name(node: ast.AST | None) -> str:
    if not isinstance(node, ast.Call):
        return ""
    if isinstance(node.func, ast.Name):
        return node.func.id
    return node.func.attr if isinstance(node.func, ast.Attribute) else ""


def _is_ignored_path_node(node: ast.AST, parent: ast.AST | None) -> bool:
    if isinstance(parent, ast.JoinedStr) or _call_name(parent) in LOG_CALLS:
        return True
    return isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div) and parent.right is node


def _rel_path_msg(node: ast.AST, parent: ast.AST | None) -> str | None:
    if _is_ignored_path_node(node, parent):
        return None
    if (
        _call_name(node) in {"Path", "mkdir", "makedirs"}
        and node.args
        and (bad := _str_prefix(node.args[0])) in BARE_DIRS
    ):
        return (
            f"Relative path '{bad}' (line {node.lineno}) breaks when Jupyter runs from "
            "notebooks/. Use DATA, MODELS, or FIGURES (anchored to ROOT)."
        )
    if (p := _str_prefix(node)) and p.startswith(REL_PATH_PREFIXES):
        return (
            f"Relative path '{p}...' (line {node.lineno}) breaks when Jupyter runs from "
            "notebooks/. Use DATA / ..., MODELS / ..., or FIGURES / ... (anchored to ROOT)."
        )
    return None


def relative_path_problems(tree) -> list[str]:
    """Flag bare project-relative paths that break when Jupyter executes from notebooks/."""
    if tree is None:
        return []
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    return [msg for n in ast.walk(tree) if (msg := _rel_path_msg(n, parents.get(n)))]


def problems_in(text: str, path: str = ".", before_code_lines=None) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None  # ruff reports syntax errors
    cells = parse_cells(STRING.sub('"""..."""', text))
    code_str = "\n".join(_code_lines(cells))
    out: list[str] = []
    if missing := missing_installs(tree, text, path, code_str):
        out.append(
            f"Not in the install cell: {', '.join(missing)}. Add to `# # %pip install -q ...`."
        )
    out += structural_problems(tree) + relative_path_problems(tree)
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
        before_code_lines = len(_code_lines(parse_cells(STRING.sub('"""..."""', f.read()))))

    fatal, problems = run_ruff(run, path)
    if fatal:
        return problems

    with open(path, encoding="utf-8") as f:
        problems += problems_in(f.read(), path, before_code_lines=before_code_lines)
    return problems if problems else _sync_ipynb(path)


def main(paths: list[str]) -> None:
    failed = False
    for path in paths:
        if problems := check_one_notebook(path):
            failed = True
            print(f"{path} breaks the notebook rules in code/SKILL.md:")
            for item in problems:
                print(f"- {item}")
        else:
            print(f"{path}: ok")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
