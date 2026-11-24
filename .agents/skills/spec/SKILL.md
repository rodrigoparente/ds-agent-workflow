---
name: spec
description: Draft, refine, or fast-forward a spec before writing code, and keep living project context synced. Triggers whenever the user wants to explore, build, test, or change something.
---

# Spec

Aligns on what we are doing, what inputs and rules apply, and how correctness will be verified before writing code. Exploratory analyses, pipelines, and prototypes without formal metrics are first-class citizens.

## Process

1. **Check context & reality first:**
   List `specs/` to find the next sequential `NN-` prefix (starting with `01`). Read `specs/context.md` (if present) and any relevant prior specs, code, or outputs (`python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb` for notebooks, or logs/summaries in `data/`). Inspect schemas, headers, or small samples in `data/` rather than guessing what can be checked directly.
2. **Brainstorm when open-ended:**
   If goals, scope, or trade-offs are unclear, do **not** create `specs/<NN-name>.md` yet. Ask 1–2 focused questions at a time (offering 2–3 concrete options via `ask_question` / `AskUserQuestion`, recommended first) until direction is clear. Adapt naturally to the work—key questions and cohorts for exploration, baseline and evaluation setup for experiments, interfaces and edge cases for pipelines/apps/modules.
3. **Write or update `specs/<NN-name>.md`:**
   Copy `assets/spec-template.md` and fill each relevant section concisely:
   - Size `## Approach & Tasks` to complexity (flat steps for single-file work; explicit file/module breakdown for multi-file builds).
   - Define concrete checks in `## Verification` (runtime assertions/invariants, unit tests, or expected outputs/logs).
   - List any `## Context Deltas` (`[ADD]`, `[MODIFY]`, `[REMOVE]`) to fold into `specs/context.md` once verified, and isolate unconfirmed choices under `## Assumptions (confirm)`.
4. **Match ceremony to ambiguity (Draft vs. Fast-Forward):**
   - **Draft & confirm (`Status: draft`):** Use for new initiatives or changes with open trade-offs or `## Assumptions (confirm)`. Share a concise summary and link to `specs/<NN-name>.md`, then ask for explicit approval via `ask_question` / `AskUserQuestion` before creating/editing code. Answering clarifying questions or requesting spec edits is a revision—update the draft and re-confirm.
   - **Fast-forward (`Status: approved`):** Use for clear, unambiguous updates or fixes on an existing spec with zero open assumptions—or when the user explicitly asks to fast-forward or implement directly. Update `specs/<NN-name>.md` first (log `- *[vN]:* ...` under `## Updates`, set `Status: approved`) and proceed straight to code in the same turn.
5. **Sync living truth (`specs/context.md`):**
   Once work is verified/executed (via `experiment-report`, test/log verification, or user confirmation), set `Status: executed` and fold confirmed `## Context Deltas` into `specs/context.md` (create lazily; keep concise and edit in place as a current snapshot of schemas, domain rules/quirks, shared modules, and baselines—not a changelog).

## Iterating vs. New Specs

- **Same initiative (`<NN-name>`):** Refinements, bug fixes, or follow-up tweaks (note `REFRESH_DATA = True` if cached inputs changed).
- **New initiative (`<(NN+1)-name>`):** Distinct phase, new approach, or operationalizing exploratory work into `scripts/` or `apps/` (`Builds on: <NN-name>`).
- **Upstream fix (`<(NN+1)-name>` → `<NN-name>`):** Fix the upstream spec and code first when downstream work exposes an upstream bug.
