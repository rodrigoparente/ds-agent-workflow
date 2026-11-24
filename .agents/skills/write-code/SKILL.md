---
name: write-code
description: Implement, update, or refine code from an approved spec—whether an experiment notebook (jupytext .py paired with .ipynb), standalone script/pipeline, interactive app/API (Streamlit, FastAPI), or unit test suite. Triggers whenever writing, implementing, revising, modifying, or fixing code.
---

# Write Code

Implements an approved spec (`specs/<NN-name>.md`) into `notebooks/py/<NN-name>.py`, `scripts/`, `apps/`, and/or `tests/`, following `AGENTS.md`.

## Process

1. **Verify spec & context:**
   - Read `specs/context.md` (if present) and `specs/<NN-name>.md` (plus `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb` or logs/outputs in `data/` when iterating).
   - Confirm `specs/<NN-name>.md` is `Status: approved` and matches this change; otherwise run `spec` first.
   - Reuse modules, artifacts, or cached data when `Builds on:` is set.
2. **Implement tasks & verification:**
   Follow `## Approach & Tasks` and turn `## Verification` into runtime assertions (`assert` on grain/splits/invariants) or synthetic `pytest` tests (`tests/test_<name>.py`):
   - **Dependencies & paths:** Add third-party packages to `[project].dependencies` in `pyproject.toml` (and cell 1 `# # %pip install -q ...` in notebooks so local runs use `uv` while standalone shares stay runnable). Anchor `DATA`, `MODELS`, and `FIGURES` to repo `ROOT` (walking up to `pyproject.toml`), never bare relative paths.
   - **Experiment notebooks (`notebooks/py/<NN-name>.py`):** Start from `assets/skeleton.py`. Use markdown headers for sections, save key charts to `FIGURES / f"{NAME}_<what>.png"` before `plt.show()`, keep code flat within `check_notebook.py` limits (≤220 code lines total, ≤35/cell, ≤15/def, no classes), and move reusable helpers to `scripts/`.
   - **Scripts (`scripts/`) & apps (`apps/`):** Keep functions small, pure/importable, and free of import-time side effects. Keep UI/API handlers thin by importing logic from `scripts/`, validate inputs, and add tests in `tests/test_<name>.py`.
3. **Verify static checks & tests:**
   - Fix any `check_notebook.py` or `ruff` errors (run `python3 .agents/tools/check_notebook.py notebooks/py/<NN-name>.py` and `uv run --no-sync ruff check`).
   - Run `uv run --no-sync pytest` (use `--no-sync` when `pyproject.toml` has unsynced additions; ask first before running `uv sync`) and quick probes (`python3 -c`) to verify logic.
4. **Handoff & context sync:**
   - Do **not** execute generated `notebooks/`, `scripts/`, or `apps/` unless explicitly asked. Hand off with the exact `uv run ...` command (`uv sync && ...` if unsynced packages were added) and wait for results.
   - Once user-confirmed runs or tests finish an initiative without a separate report, update the spec and `specs/context.md` per `spec` Step 5.
