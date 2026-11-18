---
name: experiment-spec
description: Plan and agree on an experiment, pipeline, analysis, application, or service spec before writing code. Works for exploratory data analysis (EDA), data pipelines, prototypes, model experiments, interactive apps, APIs, and open-ended investigations. Triggers whenever the user wants to experiment with, test, build, try, implement, analyze, or operationalize a dataset, model, algorithm, pipeline, or application—even when the user's prompt is vague or high-level.
---

# Experiment Spec

The spec is a simple agreement capturing what we are doing, what data is involved, and what will be produced. It keeps work documented, clear to follow, and easy to evolve over time.

No artificial goals or formal metrics are required—it is completely valid to do exploratory data analysis (EDA), build a script/pipeline, or investigate open-ended questions without a predetermined target.

## Process

1. **Context & output check:**
   List `specs/` to find the next sequential number (`NN` = highest existing number + 1, starting with `01`).
   If continuing, debugging, or building on previous work, read the relevant `specs/<NN-name>.md`, `notebooks/py/<NN-name>.py` (or `scripts/` / `apps/`), and run `uv run python .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb` to inspect actual executed outputs before proposing changes.
2. **Converse and clarify when prompts are vague (Never be robotic — Use Dialog Box):**
   The user does NOT need to know folder conventions (`specs/`, `models/`, `apps/`, `scripts/`, `tests/`), file names (`01-name`), split strategies, or exact metrics. When a prompt is open-ended:
   - Use the **dialog box (`ask_question` tool)** to propose 2–3 concrete, opinionated options for scope, evaluation strategy, baseline, or implementation approach with `(Recommended)` first.
   - Automatically propose a clean kebab-case initiative name (e.g., `01-sales-eda`, `02-baseline-model`) and route deliverables to the appropriate folder (`notebooks/py/`, `models/`, `apps/`, `scripts/`, `tests/`).
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

- **Never edit code without updating the spec first:** Whenever the user asks to modify, fix, or add steps to existing work, **update `specs/<NN-name>.md` FIRST** before touching code.
- **Iterating on an existing initiative (`<NN-name>`):**
  - Use this when fixing bugs, adjusting filters/features, or adding follow-up steps to the *same* initiative—even if `Status` was already `executed` or the adjustment was prompted by downstream testing.
  - Update the relevant sections of `specs/<NN-name>.md`, append a brief revision note under `## Updates` (`- *[v2 - Summary]:* ...`), and set `Status: approved` so it is clear the spec has unexecuted changes.
  - If literature research was conducted in `docs/research/<topic>.md`, link it via `Research: docs/research/<topic>.md` in the header metadata.
  - If `## Data & Inputs` changed, note that cached data (`data/<NN-name>.parquet`) must be refreshed (`REFRESH_DATA = True`).
- **Starting a new initiative (`<(NN+1)-name>`):**
  - Use this when starting a new phase, testing a distinct modeling approach, investigating a separate question, or operationalizing prior work into a standalone script (`scripts/`), application, or service (`apps/`).
  - Create `specs/<(NN+1)-name>.md` with `Builds on: <NN-name>` and reference any reused data, models (`models/`), or helper modules (`scripts/`).
- **Cross-initiative feedback loops (`<(NN+1)-name>` → `<NN-name>`):**
  - When testing a downstream script, app, or test suite exposes a flaw or missing requirement in an upstream initiative, update the upstream spec (`specs/<NN-name>.md`) and upstream code first, then update the downstream spec (`specs/<(NN+1)-name>.md`) and downstream code.

## Spec Lifecycle

`Status: draft` (drafting) → `Status: approved` (ready for code / has unexecuted updates) → `Status: executed` (run complete and summarized in `docs/reports/<NN-name>.md`).
