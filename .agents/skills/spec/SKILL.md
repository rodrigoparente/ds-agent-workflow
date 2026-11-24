---
name: spec
description: Draft, update, or fast-forward an initiative spec before writing or modifying code, and keep living project context synced. Use whenever the user wants to explore project data, run or extend an experiment, add or compare models/metrics, or build/modify notebooks, scripts, pipelines, or apps.
---

# Spec

Aligns on what we are doing, what inputs and rules apply, and how correctness will be verified before writing code. Exploratory analyses, pipelines, and prototypes without formal metrics are first-class citizens.

## Process

1. **Check context & choose extend vs. new:**
   Read `specs/context.md` (if present), existing `specs/`, relevant outputs (`python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb` or logs/summaries in `data/`), and small schemas/samples in `data/`. Decide whether to update an existing `<NN-name>` spec or create `<(NN+1)-name>` (starting at `01`):
   - **Extend `<NN-name>` (default for follow-ups, even if already run or `executed`):** Adding or comparing models, features, metrics, slices, plots, or fixes on the same problem, dataset, or evaluation split stays in `<NN-name>` (`REFRESH_DATA = True` only if cached inputs changed). When an upstream bug surfaces during downstream work, fix the upstream spec and code first.
   - **Start `<(NN+1)-name>`:** Only for the first initiative, a distinct phase or experimental setup (e.g., EDA → modeling), or operationalizing notebook work into standalone `scripts/` or `apps/` (`Builds on: <NN-name>`).
2. **Clarify open scope first (if needed):**
   If goals, scope, or key trade-offs are unclear, do **not** write the spec yet. Ask 1–2 focused questions via your structured question tool (2–3 concrete options, recommended first). When the user answers scoping questions, use those answers to write or update the `draft` spec next—do **not** treat scoping answers as approval to jump straight to code.
3. **Write or update `specs/<NN-name>.md`:**
   Use `assets/spec-template.md` and keep sections proportional to complexity:
   - Flat steps in `## Approach & Tasks` for single-file work; file/module breakdown for multi-file builds.
   - Concrete checks in `## Verification` (runtime assertions/invariants, unit tests, or expected outputs/logs).
   - Confirmed truth updates under `## Context Deltas` (`[ADD]`, `[MODIFY]`, `[REMOVE]`) and any open defaults under `## Assumptions (confirm)`.
4. **Confirm or fast-forward:**
   - **Draft & confirm (`Status: draft`):** Use for new initiatives or updates with open trade-offs or `## Assumptions (confirm)`. Share a concise summary and link to `specs/<NN-name>.md` in **plain text** (do not open a question dialog for approval) and wait for the user's go-ahead in chat. If the user answers an assumption or requests edits without asking to implement yet, update the `draft` and confirm in plain text; move to `Status: approved` and `code` only once confirmed.
   - **Fast-forward (`Status: approved`):** Use for clear, well-specified follow-ups on an existing `<NN-name>` spec with zero open assumptions (e.g., adding a specified model or metric comparison on an existing split), or when the user explicitly asks to implement directly. Update `specs/<NN-name>.md` first (log `- *[vN]:* ...` under `## Updates`, set `Status: approved`) and proceed straight to `code` in the same turn.
5. **Sync living truth (`specs/context.md`):**
   Once work is verified/executed (via `report`, test/log verification, or user confirmation), set `Status: executed` and fold confirmed `## Context Deltas` into `specs/context.md` (create lazily; keep concise and edit in place as a current snapshot of schemas, domain rules/quirks, shared modules, and baselines—not a changelog).
