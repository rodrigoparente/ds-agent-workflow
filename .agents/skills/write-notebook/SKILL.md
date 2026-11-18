---
name: write-notebook
description: Write, update, or refine an experiment notebook as a clean jupytext .py file in notebooks/py/ that pairs with notebooks/*.ipynb (or implement standalone scripts/apps/tests from an approved spec). Triggers whenever writing, implementing, revising, modifying, or fixing notebook or experiment code.
---

# Write Notebook

Implement the approved spec `specs/<NN-name>.md` as a clean, self-contained jupytext file in `notebooks/py/<NN-name>.py` (jupytext percent format). Running `check_notebook.py` automatically pairs and generates `notebooks/<NN-name>.ipynb`.

## Process

1. **Verify spec & inspect prior outputs first:**
   - If the user reports an issue, unexpected metric, or follow-up question after running a notebook, first run `uv run python .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb` to inspect actual cell outputs.
   - Confirm `specs/<NN-name>.md` exists and is `Status: approved`. If no spec exists yet, or if modifying an existing experiment whose spec has not yet been updated for this change, **follow `experiment-spec` to create or update `specs/<NN-name>.md` FIRST** before editing code.
   - If the spec has `Builds on: <prev-name>`, reuse relevant logic from `notebooks/py/<prev-name>.py`, shared helpers in `scripts/`, serialized models in `MODELS / "<prev-name>.joblib"`, or cached data from `DATA / "<prev-name>.parquet"`.
2. **Structure the notebook (using `assets/skeleton.py` as reference):**
   Follow the standard section order (adapting naturally to whether the spec is an EDA, pipeline, or modeling experiment):
   - **Title Cell (Markdown):** Initiative name, one-sentence overview/question from the spec, link to `specs/<NN-name>.md` (and baseline to beat if running a modeling experiment).
   - **Install Cell:** `# %pip install -q <packages>` listing all required third-party packages (including `tabulate`, `pyarrow`, `openpyxl` when used).
   - **Imports Cell:** Standard library, then third-party imports (plus local imports from `scripts/`).
   - **Config Cell:** Always define `NAME = "<NN-name>"`, `ROOT = next((p for p in [Path.cwd(), *Path.cwd().parents] if (p / "specs").exists() or (p / "pyproject.toml").exists()), Path.cwd())`, `DATA = ROOT / "data"`, `MODELS = ROOT / "models"`, `FIGURES = ROOT / "docs" / "figures"`, `REFRESH_DATA = False` (set `True` whenever `## Data & Inputs` changed in a spec iteration), and `SEED`. Include uppercase constants only for parameters listed in the spec.
   - **Get Data:** Load data following the sources, filters, and transformations specified in the spec's `## Data & Inputs`, and cache to `DATA / f"{NAME}.parquet"` (`if path.exists() and not REFRESH_DATA:`).
   - **Execution Steps:** One markdown cell (1–2 sentences explaining what and why) followed by one code cell per spec step or visual output.
   - **Summary & Model Export:**
     - *Modeling Experiments:* A single comparative table or chart comparing evaluated steps against the baseline on the target metric. When exporting a trained model or pipeline for downstream apps/APIs/CLIs, serialize it to `MODELS / f"{NAME}.joblib"`.
     - *EDA / Pipelines / Analyses:* Display the primary summary table, distribution, or key chart answering the spec's overview.
3. **Keep code minimal and flat (Shared Feature Bridge):**
   - Prefer inline top-to-bottom cell execution over custom functions, classes, or `try/except` wrappers.
   - Build all paths using `ROOT`, `DATA`, `MODELS`, and `FIGURES`.
   - Save visualizations to `FIGURES / f"{NAME}_<what>.png"` and trained model bundles to `MODELS / f"{NAME}.joblib"`.
   - Keep code within structural guardrails: at most 220 total code lines (excluding markdown, comments, and SQL), at most 35 code lines per cell, and at most 15 lines for any local helper `def` (move larger or cross-experiment/app reusable feature transformations to `scripts/<domain>_features.py` with unit tests in `tests/test_<name>.py`).
4. **Simplification & scope check:**
   Review the code against `specs/<NN-name>.md` and trim any bloat:
   - **No scope creep:** Remove metrics, models, or explorations not requested in the spec.
   - **Built-ins over custom logic:** Replace custom loops or wrappers with standard pandas, numpy, PySpark, or scikit-learn calls.
   - **No premature abstraction:** Inline single-use helper functions.
5. **Static format, validate & auto-sync `.ipynb` (DO NOT execute the notebook):**
   ALWAYS run the static notebook validator after every edit to enforce formatting, AST structural rules, code-line budgets, package installs, and **generate/sync `notebooks/<NN-name>.ipynb`**:
   ```bash
   uv run python .agents/tools/check_notebook.py notebooks/py/<NN-name>.py
   ```
   *(If writing a standalone script in `scripts/` or an app in `apps/`, run `uv run ruff format <path> && uv run ruff check <path>`; if writing unit/contract tests in `tests/`, run `uv run pytest`.)*
   Resolve any static warnings or errors reported.
6. **User Execution Handoff:**
   - Do NOT execute the notebook or experiment script yourself (see `AGENTS.md`).
   - Inform the user that the code has been statically checked and synced to `notebooks/<NN-name>.ipynb` (or saved to `scripts/` / `apps/`).
   - Stop calling tools and ask: *"Please run `notebooks/<NN-name>.ipynb` in Jupyter Lab (or `scripts/<NN-name>.py`) and let me know if you want to make any adjustments, add/remove steps, or proceed to report generation."*
