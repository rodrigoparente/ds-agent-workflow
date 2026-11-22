---
name: experiment-report
description: Generate a clear, verified summary report from executed notebook or script outputs. Triggers whenever the user requests results, summaries, findings, analysis write-ups, or reports after running code.
---

# Experiment Report

Transforms executed notebook or script outputs into a concise, verified summary report in `docs/reports/<NN-name>.md`.

## Process

1. **Verify inputs & outputs:**
   Read `specs/<NN-name>.md` and extract actual outputs:
   - *Notebooks (`notebooks/<NN-name>.ipynb`):* Run `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`. If no outputs are present, STOP and ask the user to run the notebook in Jupyter Lab first.
   - *Scripts or apps (`scripts/`, `apps/`):* Run `.venv/bin/pytest` (if tests exist) and review user-shared outputs, terminal logs, or saved charts in `docs/figures/` (do not read `data/` directly).
   - *Figures (`docs/figures/`):* List `<NN-name>_*.png` in `docs/figures/` so all saved charts are accounted for.
2. **Draft or update report (`docs/reports/<NN-name>.md`):**
   Populate `assets/report-template.md` under 2 pages:
   - Ground every metric, table, and claim in observed outputs; give caveats, failure modes, and open questions equal weight as successes.
   - Embed relevant saved charts from `docs/figures/` as `../figures/<NN-name>_<what>.png`.
3. **Audit claims before finalizing:**
   - Trace every number, percentage lift, and comparison to an observed output; remove unsupported causal or speculative claims.
   - Confirm baseline comparisons (if modeling) and all `## Done When` items in `specs/<NN-name>.md` are addressed.
4. **Update spec & present summary:**
   Update `specs/<NN-name>.md` to `Status: executed`. Share the TL;DR and key observations in chat with a link to `docs/reports/<NN-name>.md`, mention that a `.docx` export is available on request, and wait for user direction.
5. **Optional Word (`.docx`) export:**
   If requested, run `.venv/bin/python .agents/tools/export_docx.py docs/reports/<NN-name>.md` (for PDF, open the `.docx` and Save as PDF; Markdown remains the source of truth).
