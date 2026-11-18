---
name: experiment-spec
description: Plan and agree on an experiment, pipeline, analysis, app/dashboard (Streamlit), or API endpoint (FastAPI) spec before writing code. Works for exploratory data analysis (EDA), data pipelines, prototypes, model experiments, interactive apps, and open-ended investigations. Triggers whenever the user wants to experiment with, test, build, try, implement, analyze, or operationalize a dataset, model, algorithm, pipeline, dashboard, or API—even when the user's prompt is vague or high-level.
---

# Experiment Spec

The spec is a simple agreement capturing what we are doing, what data is involved, and what will be produced. It keeps work documented, clear to follow, and easy to evolve over time.

No artificial goals or formal metrics are required—it is completely valid to do exploratory data analysis (EDA), build a script/pipeline, or investigate open-ended questions without a predetermined target.

## Process

1. **Context & output check:**
   List `specs/` to find the next sequential number (`NN` = highest existing number + 1, starting with `01`).
   If continuing, debugging, or building on previous work, read the relevant `specs/<NN-name>.md`, `notebooks/py/<NN-name>.py`, and run `uv run python .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb` to inspect actual executed outputs before proposing changes.
2. **Converse and clarify when prompts are vague (Never be robotic — Use Dialog Box):**
   The user does NOT need to know folder conventions (`specs/`, `models/`, `apps/`, `scripts/`), file names (`01-name`), split strategies, or exact metrics. When a prompt is open-ended (e.g., *"Let's build a recommender"*, *"The results look weird, can we fix it?"*, or *"Can we make an app for this?"*):
   - Use the **dialog box (`ask_question` tool)** to propose 2–3 concrete, opinionated options for scope, evaluation split (e.g. temporal vs. stratified), baseline, or architecture with `(Recommended)` first.
   - Automatically propose a clean kebab-case initiative name (`01-sales-eda`, `02-churn-api`) and route deliverables to the right folder (`notebooks/py/`, `models/`, `apps/`, `scripts/`, `tests/`).
   - Check data sources. When lake tables are involved, consult `data-catalog` for standard schemas and recipes.
3. **Draft the spec:**
   Copy `assets/spec-template.md` to `specs/<NN-name>.md`.
   In `## Data & Inputs`, detail the data management process clearly: source tables/files, deduplication, filtering, transformations, and join conditions.
   Fill in the remaining sections and set `Status: draft`.
   Document any default choices or assumptions under `Assumptions (confirm)`.
4. **Interactive review & confirmation:**
   Present the draft spec summary in chat, highlighting key assumptions and trade-offs.
   Invite the user to confirm or adjust in chat. Once confirmed by the user, update status to `Status: approved`.

## Iterating vs. New Specs (STRICT Spec-First Rule)

- **Never edit code without updating the spec first:** Whenever the user asks to modify, fix, or add steps to an existing experiment (`01-sales-eda`), **update `specs/<NN-name>.md` FIRST** before touching `notebooks/py/<NN-name>.py`.
- **Iterating on an existing experiment (`<NN-name>`):**
  - Use this when fixing bugs, adjusting filters/features, or adding follow-up charts/steps to the *same* question/dataset—even if `Status` is already `executed` or triggered by discoveries in a downstream app/experiment.
  - Update the relevant sections of `specs/<NN-name>.md`, append a structured 1-line entry under `## Updates` (`- *[v2 - Reason]:* ...`), and set `Status: approved` so it is clear the spec has unexecuted changes.
  - If mid-stream literature research was conducted, add `Research: docs/research/<topic>.md` in the header metadata.
  - If `## Data & Inputs` changed, note that cached data (`data/<NN-name>.parquet`) must be refreshed (`REFRESH_DATA = True`).
- **Starting a new experiment, app, or API (`<(NN+1)-name>`):**
  - Use this when starting a new phase, testing a different modeling family, investigating a separate question, or operationalizing a model into a Streamlit app (`apps/<NN>_<name>_app.py`), FastAPI service (`apps/<NN>_<name>_api.py`), or batch CLI (`scripts/<NN>_<name>_cli.py`).
  - Create `specs/<(NN+1)-name>.md` with `Builds on: <NN-name>` (and reference any serialized model artifact from `models/<NN-name>.joblib` and shared feature helpers in `scripts/<domain>_features.py`).

## Spec Lifecycle

`Status: draft` (drafting) → `Status: approved` (ready for code / has unexecuted updates) → `Status: executed` (run complete and summarized in `docs/reports/<NN-name>.md`).
