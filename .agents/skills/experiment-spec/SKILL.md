---
name: experiment-spec
description: Plan and agree on an experiment, pipeline, or analysis spec before writing code. Works for exploratory data analysis (EDA), data pipelines, prototypes, model experiments, and open-ended investigations. Triggers whenever the user wants to experiment with, test, build, try, implement, or analyze a dataset, model, algorithm, or pipeline.
---

# Experiment Spec

The spec is a simple agreement capturing what we are doing, what data is involved, and what will be produced. It keeps work documented, clear to follow, and easy to evolve over time.

No artificial goals or formal metrics are required—it is completely valid to do exploratory data analysis (EDA), build a script/pipeline, or investigate open-ended questions without a predetermined target.

## Process

1. **Context check:**
   List `specs/` to find the next sequential number (`NN` = highest existing number + 1, starting with `01`).
   If continuing or building on previous work, check the relevant spec and code.
2. **Converse and clarify before drafting (Never be robotic — Use Dialog Box):**
   Do NOT rush to generate a full draft spec in isolation without talking to the user. Use the **dialog box (`ask_question` tool)** to align on direction:
   - Present 2–3 structured options for scope, evaluation split, or implementation flavor with `(Recommended)` first.
   - The user can pick with one click or type custom nuance via the dialog box's "Other" option.
   - Agree on a short kebab-case name (the agent adds the two-digit number, e.g. `01-sales-eda`).
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
  - Use this when fixing bugs, adjusting filters/features, or adding follow-up charts/steps to the *same* question/dataset—even if `Status` is already `executed`.
  - Update the relevant sections of `specs/<NN-name>.md`, add a 1-line note under `## Updates` (optional, minimal), and set `Status: approved` so it is clear the spec has unexecuted changes.
  - If `## Data & Inputs` changed, note that cached data (`data/<NN-name>.parquet`) must be refreshed (`REFRESH_DATA = True`).
- **Starting a new experiment (`<(NN+1)-name>`):**
  - Use this when starting a new phase, testing a different modeling family, or investigating a separate question.
  - Create `specs/<(NN+1)-name>.md` with `Builds on: <NN-name>`.

## Spec Lifecycle

`Status: draft` (drafting) → `Status: approved` (ready for code / has unexecuted updates) → `Status: executed` (run complete and summarized in `docs/reports/<NN-name>.md`).
