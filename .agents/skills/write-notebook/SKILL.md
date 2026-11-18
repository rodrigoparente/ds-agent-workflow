---
name: write-notebook
description: Write, update, or refine an experiment notebook as a clean jupytext .py file in notebooks/py/ that pairs with notebooks/*.ipynb. Implements an approved spec in specs/<NN-name>.md. Triggers whenever writing, implementing, revising, modifying, or fixing notebook code.
---

# Write Notebook

Implement the approved spec `specs/<NN-name>.md` as a clean, self-contained jupytext file in `notebooks/py/<NN-name>.py` (jupytext percent format). Running `check_notebook.py` automatically pairs and generates `notebooks/<NN-name>.ipynb`.

## Process

1. **Verify spec first (STRICT Spec-First Rule):**
   Confirm `specs/<NN-name>.md` exists and is `Status: approved` (if still in `draft`, run `experiment-spec` first).
   - **When modifying or adding to an existing experiment:** If the user asked for a change, fix, or new step not yet reflected in `specs/<NN-name>.md`, **update the spec FIRST** (and set `Status: approved` if it was `executed`) before editing `notebooks/py/<NN-name>.py`.
   - If the spec has `Builds on: <prev-name>`, reuse the relevant logic from `notebooks/py/<prev-name>.py`, shared helpers in `scripts/`, or cached data from `DATA / "<prev-name>.parquet"`.
2. **Structure the notebook (using `assets/skeleton.py` as reference):**
   Follow the standard section order (adapting naturally to whether the spec is an EDA, pipeline, or modeling experiment):
   - **Title Cell (Markdown):** Initiative name, one-sentence overview/question from the spec, link to `specs/<NN-name>.md` (and baseline to beat if running a modeling experiment).
   - **Install Cell:** `# %pip install -q <packages>` listing all required third-party packages (including `tabulate`, `pyarrow`, `openpyxl` when used).
   - **Imports Cell:** Standard library, then third-party imports.
   - **Config Cell:** Always define `NAME = "<NN-name>"`, `ROOT = next((p for p in [Path.cwd(), *Path.cwd().parents] if (p / "pyproject.toml").exists()), Path.cwd())`, `DATA = ROOT / "data"`, `FIGURES = ROOT / "docs" / "figures"`, `REFRESH_DATA = False` (set `True` whenever `## Data & Inputs` changes in an iteration!), and `SEED`. Include uppercase constants only for parameters listed in the spec.
   - **Get Data:** Load data following the sources, filters, and transformations specified in the spec's `## Data & Inputs`, and cache to `DATA / f"{NAME}.parquet"` (`if path.exists() and not REFRESH_DATA:`).
   - **Execution Steps:** One markdown cell (1–2 sentences explaining what and why) followed by one code cell per spec step or visual output.
   - **Summary:**
     - *Modeling Experiments:* A single comparative table or chart comparing evaluated steps against the baseline on the target metric.
     - *EDA / Pipelines / Analyses:* Display the primary summary table, distribution, or key chart answering the spec's overview.
3. **Keep code minimal and flat:**
   - Prefer inline top-to-bottom cell execution over custom functions, classes, or `try/except` wrappers.
   - Build all paths using `ROOT`, `DATA`, and `FIGURES`.
   - Save visualizations to `FIGURES / f"{NAME}_<what>.png"`.
   - Keep code within structural guardrails: at most 220 total code lines (excluding markdown, comments, and SQL), at most 35 code lines per cell, and at most 15 lines for any local helper `def` (move larger or cross-experiment reusable functions to `scripts/`).
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
   *(If writing a standalone script in `scripts/<name>.py`, run `uv run ruff format scripts/<name>.py && uv run ruff check scripts/<name>.py`; if writing unit tests in `tests/`, you may run `uv run pytest`.)*
   Resolve any static warnings or errors reported.
6. **User Execution Handoff (STRICT: Agent NEVER executes experiment code):**
   - **The agent must NEVER run or execute the notebook or data/experiment script**—no `python notebooks/py/<NN-name>.py`, no `python scripts/<NN-name>.py`, no `python -c`, no `jupyter nbconvert --execute`, and no "quick test runs" to see if the code works. You are a copilot; the user is always in 100% control of executing experiments.
   - Inform the user that the code has been statically checked and synced to `notebooks/<NN-name>.ipynb` (or saved to `scripts/<NN-name>.py`).
   - Stop calling tools and ask: *"Please run `notebooks/<NN-name>.ipynb` in Jupyter Lab (or `scripts/<NN-name>.py`) and let me know if you want to make any adjustments, add/remove steps, or proceed to report generation."*
