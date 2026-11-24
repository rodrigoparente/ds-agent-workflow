---
name: write-code
description: Implement, update, or refine code from an approved spec—whether an experiment notebook (jupytext .py paired with .ipynb), standalone script/pipeline, interactive app/API (Streamlit, FastAPI), or unit test suite. Triggers whenever writing, implementing, revising, modifying, or fixing code.
---

# Write Code

Implements an approved spec (`specs/<NN-name>.md`) into `notebooks/py/<NN-name>.py`, `scripts/`, `apps/`, and/or `tests/`, following the workflow and boundaries in `AGENTS.md`.

## Process

1. **Verify spec & context:**
   - Read `specs/context.md` (if present) and `specs/<NN-name>.md` (plus `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb` or logs/outputs in `data/` when iterating).
   - Confirm `specs/<NN-name>.md` reflects this change and is `Status: approved`. If missing or needing updates, run `spec` first (fast-forwarding in the same turn only for unambiguous tweaks with zero open assumptions).
   - Reuse code, artifacts, or cached data from prior work when `Builds on:` is set.
2. **Implement tasks & verification:**
   Follow `## Approach & Tasks` and turn `## Verification` into concrete runtime checks (`assert` statements on data invariants/grains/splits) or `pytest` tests (`tests/test_<name>.py` with small synthetic fixtures):
   - **Dependencies & paths (all targets):** Add new third-party packages to `[project].dependencies` in `pyproject.toml` (and `# # %pip install -q ...` in notebook cell 1). Anchor `DATA`, `MODELS`, and `FIGURES` to repo `ROOT` (walking up to `pyproject.toml`), never bare relative paths.
   - **Experiment notebooks (`notebooks/py/<NN-name>.py`):** Start from `assets/skeleton.py`. Precede step cells with 1–2 sentence markdown context, save key charts to `FIGURES / f"{NAME}_<what>.png"` before `plt.show()`, and keep code flat within `check_notebook.py` limits (≤220 lines total, ≤35/cell, ≤15/def, no classes or `try/except`).
   - **Scripts (`scripts/`) & apps (`apps/`):** Keep functions small, pure/importable, and free of import-time side effects. Keep UI/API handlers thin by importing core logic from `scripts/`, validate inputs, and add tests in `tests/test_<name>.py`.
3. **Verify static checks & tests:**
   - Fix any `check_notebook.py` or `ruff` issues reported by hooks (or run `python3 .agents/tools/check_notebook.py notebooks/py/<NN-name>.py`).
   - Confirm with the user before running `uv sync` if new packages aren't installed yet (or include `uv sync` in the handoff command).
   - Run `uv run pytest` and quick probes (`python3 -c`) to verify helper/app logic before handoff.
4. **Handoff & context sync:**
   - Do **not** execute generated `notebooks/`, `scripts/`, or `apps/` unless explicitly asked. Hand off the exact `uv run ...` command (prefixed with `uv sync && ` if unsynced dependencies were added) and wait for results.
   - When user-confirmed runs or passing suite runs complete an initiative without a separate report, set `Status: executed` and fold confirmed `## Context Deltas` into `specs/context.md`.
