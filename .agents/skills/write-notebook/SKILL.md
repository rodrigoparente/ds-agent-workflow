---
name: write-notebook
description: Write, update, or refine an experiment notebook as a clean jupytext .py file that pairs with .ipynb. Implements an approved spec in specs/<NN-name>.md. Triggers whenever writing, implementing, revising, modifying, or fixing notebook code.
---

# Write Notebook

Implement the approved spec `specs/<NN-name>.md` as a clean, self-contained jupytext file in `jupytext/<NN-name>.py` (jupytext percent format). The file automatically pairs with `notebooks/<NN-name>.ipynb`.

## Process

1. **Verify spec:**
   Confirm `specs/<NN-name>.md` exists and is `Status: approved` (or `Status: executed` when editing active work). If still in `draft`, run `experiment-spec` first.
   If the spec has `Builds on: <prev-name>`, reuse the relevant logic from `jupytext/<prev-name>.py` or cached data from `DATA / "<prev-name>.parquet"`.
2. **Structure the notebook (using `assets/skeleton.py` as reference):**
   Follow the standard section order (adapting naturally to whether the spec is an EDA, pipeline, or modeling experiment):
   - **Title Cell (Markdown):** Initiative name, one-sentence overview/question from the spec, link to `specs/<NN-name>.md` (and baseline to beat if running a modeling experiment).
   - **Install Cell:** `# %pip install -q <packages>` listing all required third-party packages (including `tabulate`, `pyarrow`, `openpyxl` when used).
   - **Imports Cell:** Standard library, then third-party imports.
   - **Config Cell:** Always define `NAME = "<NN-name>"`, `ROOT = next((p for p in [Path.cwd(), *Path.cwd().parents] if (p / "pyproject.toml").exists()), Path.cwd())`, `DATA = ROOT / "data"`, `FIGURES = ROOT / "figures"`, and `SEED`. Never nest `data/` or `figures/` inside `notebooks/`—they must strictly reside at the project root. Include uppercase constants only for parameters listed in the spec.
   - **Get Data:** Load data following the sources, filters, and transformations specified in the spec's `## Data & Inputs`, and cache to `DATA / f"{NAME}.parquet"` for fast reruns.
   - **Execution Steps:** One markdown cell (1–2 sentences explaining what and why) followed by one code cell per spec step or visual output.
   - **Summary:**
     - *Modeling Experiments:* A single comparative table or chart comparing evaluated steps against the baseline on the target metric.
     - *EDA / Pipelines / Analyses:* Display the primary summary table, distribution, or key chart answering the spec's overview.
3. **Keep code minimal and flat:**
   - Prefer inline top-to-bottom cell execution over custom functions, classes, or `try/except` wrappers.
   - Build all paths using `ROOT`, `DATA`, and `FIGURES`.
   - Save visualizations to `FIGURES / f"{NAME}_<what>.png"`.
   - Keep code within structural guardrails: at most 220 total code lines (excluding markdown, comments, and SQL), at most 35 code lines per cell, and at most 15 lines for any local helper `def` (move larger reusable functions to `scripts/`).
4. **Simplification & scope check:**
   Review the code against `specs/<NN-name>.md` and trim any bloat:
   - **No scope creep:** Remove metrics, models, or explorations not requested in the spec.
   - **Built-ins over custom logic:** Replace custom loops or wrappers with standard pandas, numpy, PySpark, or scikit-learn calls.
   - **No premature abstraction:** Inline single-use helper functions.
5. **Format, validate & sync:**
   Run the notebook validator to enforce formatting, AST structural rules, code-line budgets, and package installs, and sync the `.ipynb` file:
   ```bash
   uv run python .agents/tools/check_notebook.py jupytext/<NN-name>.py
   ```
   Resolve any warnings or errors reported.
6. **User Execution Handoff (STRICT: Agent NEVER executes notebooks):**
   - **The agent must NEVER run or execute the notebook** (no `jupyter nbconvert --execute`, no background execution, no test scripts). The user is always in complete control of running code.
   - Inform the user that the notebook has been formatted and synced to `notebooks/<NN-name>.ipynb`.
   - Remind the user to open Jupyter Lab via `uv run jupyter lab`, run the notebook, inspect the outputs, and give feedback.
   - Ask: *"Please run `notebooks/<NN-name>.ipynb` and let me know if you want to make any adjustments, add/remove steps, or proceed to report generation."*
