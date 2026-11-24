---
name: write-code
description: Implement, update, or refine code from an approved spec—whether an experiment notebook (jupytext .py paired with .ipynb), standalone script/pipeline, interactive app/API (Streamlit, FastAPI), or unit test suite. Triggers whenever writing, implementing, revising, modifying, or fixing code.
---

# Write Code

Implements an approved spec (`specs/<NN-name>.md`) into `notebooks/py/<NN-name>.py`, `scripts/`, `apps/`, and/or `tests/`, following the spec-first rule, code standards, and agent boundaries in `AGENTS.md`.

## Process

1. **Verify spec & prior outputs first:**
   - If following up on a notebook run, inspect actual outputs first via `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`.
   - Confirm `specs/<NN-name>.md` exists and is `Status: approved` for this change. If missing, `draft`, or needing updates, run `spec` *first* and stop for explicit user approval.
   - If the spec sets `Builds on: <prev-name>`, reuse logic from `notebooks/py/<prev-name>.py`, `scripts/`, `models/`, or `data/<prev-name>.parquet`.

2. **Implement by target type** *(keep scope strictly limited to the spec; prefer built-ins over custom wrappers)*:
   - **Dependencies (all target types):** Whenever code in `notebooks/`, `scripts/`, or `apps/` introduces a third-party package not yet in `pyproject.toml`, **add it to `[project].dependencies` in `pyproject.toml`** (and for notebooks, list it in cell 1 `# # %pip install -q ...`).
   - **Paths (all target types):** Resolve `DATA`, `MODELS`, and `FIGURES` from repo `ROOT` (walking up to `pyproject.toml`)—never use bare relative paths like `"models/..."`, `"data/..."`, or `"docs/figures/..."`.
   - **Option A — Experiment Notebooks (`notebooks/py/<NN-name>.py`):**
     Start from `assets/skeleton.py` and keep the standard cell order:
     1. **Title Cell (Markdown):** Initiative name, one-sentence overview from the spec, link to `specs/<NN-name>.md` (and baseline to beat if modeling).
     2. **Install Cell:** `# # %pip install -q <packages>` listing every third-party package imported or needed implicitly (`tabulate`, `pyarrow`, `openpyxl`, `kaleido`).
     3. **Imports Cell:** Standard/third-party/`scripts/` imports.
     4. **Config → Get Data → Execution Steps → Summary & Artifacts:**
        - Precede `Config` (`NAME`, `ROOT`, `DATA`, `MODELS`, `FIGURES`, `REFRESH_DATA = False`, `SEED`) and every step cell with a 1–2 sentence markdown cell.
        - Cache data to `DATA / f"{NAME}.parquet"`.
        - Save key charts to `FIGURES / f"{NAME}_<what>.png"` (`fig.savefig(..., dpi=150, bbox_inches="tight")` before `plt.show()`, since inline plots are stripped in Git) and display the primary summary table.
     - **Notebook guardrails:** Flat inline code only (no classes, no `try/except`), at most **220** total code lines and **35** code lines per cell (excluding markdown, comments, and triple-quoted SQL strings), and **15** lines per local `def` (move larger/reusable logic to `scripts/`).
   - **Option B — Standalone Scripts & Pipelines (`scripts/`):**
     Keep functions small, pure/importable, and free of import-time side effects. Add tests in `tests/test_<name>.py`.
   - **Option C — Interactive Apps & APIs (`apps/`, e.g., Streamlit, FastAPI):**
     Keep UI/route handlers thin by importing data/feature/inference logic from `scripts/`. Validate inputs and add tests (e.g., FastAPI `TestClient`) in `tests/test_<name>.py`.
   - **Option D — Tests (`tests/test_<name>.py`):**
     Use `pytest` fixtures with small synthetic data; never depend on large raw files in `data/`.

3. **Verify static checks & tests:**
   - Fix any formatting, lint, notebook-budget, relative-path, or `.ipynb` sync issues reported by automated hooks (or run `python3 .agents/tools/check_notebook.py notebooks/py/<NN-name>.py` directly).
   - If new dependencies were added to `pyproject.toml` and aren't installed in `.venv` yet, ask the user for confirmation to run `uv sync` before running `uv run pytest`, or include `uv sync` as the first handoff command below.
   - Run `uv run pytest` and quick synthetic-data probes via `python3 -c` (or `uv run python -c`) to verify helper/app logic before handoff.

4. **Handoff for user execution:**
   Do **not** run what you create in `notebooks/`, `scripts/`, or `apps/` unless explicitly asked. Tell the user the code is statically checked (and synced to `notebooks/<NN-name>.ipynb` or tested via `pytest`), hand off the exact run command (`uv run jupyter lab`, `uv run python scripts/<name>.py`, or `uv run <app-command>`, prefixed with `uv sync && ` if unsynced dependencies were added), and wait for results.
