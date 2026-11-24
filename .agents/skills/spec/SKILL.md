---
name: spec
description: Draft and agree on a spec before writing code—for EDA, models, pipelines, apps, APIs, or prototypes. Triggers whenever the user wants to analyze, build, test, or change something.
---

# Spec

Captures what we are doing, what data is involved, and what will be produced before any code is written. Exploratory analyses, pipelines, and prototypes without formal metrics are first-class citizens.

## Process

1. **Context & output check:**
   List `specs/` to find the next sequential number (`NN` = highest existing number + 1, starting with `01`).
   If continuing or debugging previous work, read the relevant `specs/<NN-name>.md`, its code (`notebooks/py/<NN-name>.py`, `scripts/`, or `apps/`), and—for notebooks—inspect executed outputs with `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`.
2. **Clarify scope & route deliverables:**
   The user does not need to know folder conventions (`specs/`, `models/`, `apps/`, `scripts/`, `tests/`), initiative names (`01-name`), or exact evaluation mechanics. When a prompt is open-ended:
   - Propose 2–3 concrete, opinionated options (scope, evaluation, baseline, or approach) via `ask_question` / `AskUserQuestion`.
   - Propose a clean kebab-case initiative name (e.g., `01-sales-eda`, `02-baseline-model`) and route deliverables to the right folder.
3. **Draft the spec (`Status: draft`):**
   Copy `assets/spec-template.md` to `specs/<NN-name>.md` and fill in every section (including sources, deduplication, filters, transforms, joins, and any defaults under `## Assumptions (confirm)`). Always set `Status: draft` when creating or revising a spec.
4. **Approve before coding (`Status: approved` — HARD GATE):**
   - Share a concise summary and link to `specs/<NN-name>.md` (highlighting data inputs, approach, deliverable, and any remaining assumptions/trade-offs), then ask for explicit approval via `ask_question` / `AskUserQuestion` (e.g., `(Recommended) Approve spec and implement code` vs. `Make changes`).
   - Answering clarifying/assumption questions or requesting any change to the spec is a revision—not approval to code. Update `specs/<NN-name>.md` (keep `Status: draft`), re-summarize, and wait for explicit approval.
   - Do **not** set `Status: approved` or create/edit code (`notebooks/`, `scripts/`, `apps/`, `tests/`) until the user explicitly approves the latest written spec with no pending edits or unanswered questions.

## Iterating vs. New Specs

- **Iterating on an existing initiative (`<NN-name>`):** Use this for bug fixes, filter/feature tweaks, or follow-up steps on the *same* initiative—even if `Status` was `executed`. Update `specs/<NN-name>.md` *before* touching code, append `- *[v2 - Summary]:* ...` under `## Updates`, set `Status: draft`, link any research via `Research: docs/research/<name>.md`, and note `REFRESH_DATA = True` if `## Data & Inputs` changed. Follow Step 4 before flipping to `Status: approved` and editing code.
- **Starting a new initiative (`<(NN+1)-name>`):** Use this for a new phase, distinct modeling approach, separate question, or operationalizing prior work into `scripts/` or `apps/`. Create `specs/<(NN+1)-name>.md` with `Builds on: <NN-name>` and reference reused data, `models/`, or `scripts/`.
- **Cross-initiative feedback (`<(NN+1)-name>` → `<NN-name>`):** When downstream work exposes an upstream bug or missing requirement, update the upstream spec and code first, then update the downstream spec and code.

## Spec Lifecycle

`Status: draft` (drafting) → `Status: approved` (ready for code / has unexecuted updates) → `Status: executed` (run complete and summarized in `docs/reports/<NN-name>.md`).
