---
name: write-code
description: Implement, update, or refine code from an approved spec—whether an experiment notebook (jupytext .py paired with .ipynb), standalone script/pipeline, interactive app/API (Streamlit, FastAPI), or unit test suite. Triggers whenever writing, implementing, revising, modifying, or fixing code.
---

# Write Code

Implements an approved spec (`specs/<NN-name>.md`) into `notebooks/py/<NN-name>.py`, `scripts/`, `apps/`, and/or `tests/`, following the spec-first rule, minimal-code ladder, and execution ban in `AGENTS.md`.

## Process

1. **Verify spec & prior outputs first:**
   - If following up on a notebook run, inspect actual outputs first via `uv run python .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`.
   - Confirm `specs/<NN-name>.md` exists and is `Status: approved` for this change. If missing or not yet updated, run `experiment-spec` *first*.
   - If the spec sets `Builds on: <prev-name>`, reuse logic from `notebooks/py/<prev-name>.py`, `scripts/`, `models/`, or `data/<prev-name>.parquet`.

2. **Implement by target type** *(keep scope strictly limited to the spec; prefer built-ins over custom wrappers)*:
   - **Option A — Experiment Notebooks (`notebooks/py/<NN-name>.py`):**
     Start from `assets/skeleton.py` and keep the standard cell order:
     1. **Title Cell (Markdown):** Initiative name, one-sentence overview from the spec, link to `specs/<NN-name>.md` (and baseline to beat if modeling).
     2. **Install Cell:** `# %pip install -q <packages>` listing every third-party package imported or needed implicitly (`tabulate`, `pyarrow`, `openpyxl`).
     3. **Imports & Config Cells:** Standard/third-party/`scripts/` imports, then `NAME`, `ROOT`, `DATA`, `MODELS`, `FIGURES`, `REFRESH_DATA = False` (set `True` when `## Data & Inputs` changes), and `SEED`.
     4. **Get Data → Execution Steps → Summary & Artifacts:** Cache to `DATA / f"{NAME}.parquet"`, precede each step cell with a 1–2 sentence markdown cell, save figures to `FIGURES / f"{NAME}_<what>.png"`, and display the primary summary table.
     - **Notebook guardrails:** Flat inline code only (no classes, no `try/except`), at most **220** total code lines, **35** code lines per cell, and **15** lines per local `def` (move larger/reusable logic to `scripts/`).
   - **Option B — Standalone Scripts & Pipelines (`scripts/`):**
     Keep functions small, pure/importable, and free of import-time side effects. Resolve paths from repo root (`pyproject.toml`) and add tests in `tests/test_<name>.py`.
   - **Option C — Interactive Apps & APIs (`apps/`, e.g., Streamlit, FastAPI):**
     Keep UI/route handlers thin by importing data/feature/inference logic from `scripts/`. Validate inputs, load artifacts from `models/` or `data/`, and add tests (e.g., FastAPI `TestClient`) in `tests/test_<name>.py`.
   - **Option D — Tests (`tests/test_<name>.py`):**
     Use `pytest` fixtures with small synthetic data; never depend on large raw files in `data/`.

3. **Verify static checks & tests (hooks run automatically):**
   - `PostToolUse` (`.agents/hooks/lint.py`) automatically runs `check_notebook.py` (formatting, AST/budget/install checks, and `.ipynb` sync) on `notebooks/py/*.py` edits, and `ruff format` + `ruff check` on all other `.py` edits.
   - `Stop` (`.agents/hooks/stop_tests.py`) automatically runs `pytest -x -q` when `.py` files changed and `tests/test_*.py` exists.
   - Fix any issues reported by hooks (or run `uv run pytest` manually while iterating on tests).

4. **Handoff for user execution:**
   Do **not** run notebooks, experiment scripts, or app servers yourself. Tell the user the code is statically checked (and synced to `notebooks/<NN-name>.ipynb` or tested via `pytest`), ask them to run it (`uv run jupyter lab`, `uv run python scripts/<name>.py`, or `uv run <app-command>`), and wait for results.
