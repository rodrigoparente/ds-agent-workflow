---
name: experiment-spec
description: Plan and agree on an experiment, pipeline, analysis, application, or service spec before writing code. Works for exploratory data analysis (EDA), data pipelines, prototypes, model experiments, interactive apps, APIs, and open-ended investigations. Triggers whenever the user wants to experiment with, test, build, try, implement, analyze, or operationalize a dataset, model, algorithm, pipeline, or application—even when the user's prompt is vague or high-level.
---

# Experiment Spec

Captures what we are doing, what data is involved, and what will be produced before any code is written. Exploratory analyses, pipelines, and prototypes without formal metrics are first-class citizens.

## Process

1. **Context & output check:**
   List `specs/` to find the next sequential number (`NN` = highest existing number + 1, starting with `01`).
   If continuing or debugging previous work, read the relevant `specs/<NN-name>.md`, its code (`notebooks/py/<NN-name>.py`, `scripts/`, or `apps/`), and—for notebooks—inspect executed outputs with `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`.
2. **Clarify scope & route deliverables:**
   The user does not need to know folder conventions (`specs/`, `models/`, `apps/`, `scripts/`, `tests/`), initiative names (`01-name`), or exact evaluation mechanics. When a prompt is open-ended:
   - Propose 2–3 concrete, opinionated options (scope, evaluation, baseline, or approach) via `ask_question` / `AskUserQuestion`.
   - Propose a clean kebab-case initiative name (e.g., `01-sales-eda`, `02-baseline-model`) and route deliverables to the right folder.
   - Consult `data-catalog` when project tables/data sources are involved.
3. **Draft the spec (`Status: draft`):**
   Copy `assets/spec-template.md` to `specs/<NN-name>.md` and fill in every section (including sources, deduplication, filters, transforms, joins, and any defaults under `## Assumptions (confirm)`).
4. **Confirm before coding (`Status: approved`):**
   Share a concise summary of the draft spec in chat, highlighting assumptions and trade-offs. Once confirmed by the user, set `Status: approved`.

## Iterating vs. New Specs

- **Iterating on an existing initiative (`<NN-name>`):** Use this for bug fixes, filter/feature tweaks, or follow-up steps on the *same* initiative—even if `Status` was `executed`. Update `specs/<NN-name>.md` *before* touching code, append `- *[v2 - Summary]:* ...` under `## Updates`, set `Status: approved`, link any research via `Research: docs/research/<name>.md`, and note `REFRESH_DATA = True` if `## Data & Inputs` changed.
- **Starting a new initiative (`<(NN+1)-name>`):** Use this for a new phase, distinct modeling approach, separate question, or operationalizing prior work into `scripts/` or `apps/`. Create `specs/<(NN+1)-name>.md` with `Builds on: <NN-name>` and reference reused data, `models/`, or `scripts/`.
- **Cross-initiative feedback (`<(NN+1)-name>` → `<NN-name>`):** When downstream work exposes an upstream bug or missing requirement, update the upstream spec and code first, then update the downstream spec and code.

## Spec Lifecycle

`Status: draft` (drafting) → `Status: approved` (ready for code / has unexecuted updates) → `Status: executed` (run complete and summarized in `docs/reports/<NN-name>.md`).
