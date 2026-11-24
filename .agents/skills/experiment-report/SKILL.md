---
name: experiment-report
description: Generate a clear, verified summary report from executed notebook or script outputs. Triggers whenever the user requests results, summaries, findings, analysis write-ups, or reports after running code.
---

# Experiment Report

Transforms executed notebook or script outputs into a concise, verified summary report in `docs/reports/<NN-name>.md`.

## Process

1. **Verify inputs & outputs:**
   Read `specs/<NN-name>.md`, list saved charts in `docs/figures/<NN-name>_*.png` (and artifacts in `models/`), and extract actual outputs:
   - *Notebooks (`notebooks/<NN-name>.ipynb`):* Run `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`. If `nb_summary.py` shows no outputs, partial execution, or an error **while saved charts or models for `<NN-name>` already exist**, tell the user the `.ipynb` on disk looks unsaved/stale and ask them to save (`Ctrl+S`) in Jupyter Lab rather than assuming packages are missing or the notebook wasn't run. If neither outputs nor artifacts exist, STOP and ask the user to run the notebook in Jupyter Lab first.
   - *Scripts or apps (`scripts/`, `apps/`):* Run `uv run pytest` (if tests exist) and review user-shared outputs, run logs/metrics/summaries in `data/`, or saved charts in `docs/figures/`.
2. **Draft or update report (`docs/reports/<NN-name>.md`):**
   Populate `assets/report-template.md` under 2 pages:
   - Ground every metric, table, and claim in observed outputs; give caveats, failure modes, and open questions equal weight as successes.
   - Embed relevant saved charts from `docs/figures/` as `../figures/<NN-name>_<what>.png`.
3. **Audit claims before finalizing:**
   - Trace every number, percentage lift, and comparison to an observed output; remove unsupported causal or speculative claims.
   - Confirm baseline comparisons (if applicable) and all `## Verification` items in `specs/<NN-name>.md` are addressed.
4. **Update spec, sync context & present summary:**
   Update `specs/<NN-name>.md` to `Status: executed` and fold newly confirmed truths or `## Context Deltas` (schemas, domain quirks/filters, shared modules, baselines) into `specs/context.md` (creating it if needed, edited in place as a concise snapshot). Share the TL;DR and key observations in chat with a link to `docs/reports/<NN-name>.md`, mention that a `.docx` export is available on request, and wait for user direction.
5. **Optional Word (`.docx`) export:**
   If requested, run `uv run python .agents/tools/export_docx.py docs/reports/<NN-name>.md` (for PDF, open the `.docx` and Save as PDF; Markdown remains the source of truth).
