---
name: experiment-report
description: Generate a clear, verified summary report from executed notebook or script outputs. Triggers whenever the user requests results, summaries, findings, analysis write-ups, or reports after running code.
---

# Experiment Report

Transforms executed notebook or script outputs into a concise, verified summary report.

## Process

1. **Verify inputs (STRICT: Agent NEVER executes notebooks):**
   Read `specs/<NN-name>.md`.
   Extract run outputs:
   - *For notebooks:* Run `uv run python .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`.
   - **If no outputs are present:** STOP and ask the user to execute the notebook in Jupyter Lab (`uv run jupyter lab`) first. The agent must NEVER execute or re-run the notebook autonomously (no `jupyter nbconvert --execute`, no headless python runs).
   - *For scripts:* Review execution logs, generated data files in `data/`, or figures in `figures/`.
2. **Draft report:**
   Populate `assets/report-template.md` and save to `reports/<NN-name>.md`:
   - Ground every metric, pattern, and claim directly in the actual outputs.
   - Summarize key findings, visual trends, or benchmark tables.
   - Include caveats, failure modes, and open questions with equal weight as successes.
   - Reference figures as `../figures/<NN-name>_<what>.png`.
   - Keep total length under two pages.
3. **Verify claims against outputs:**
   Audit `reports/<NN-name>.md` against `specs/<NN-name>.md` and the `nb_summary.py` (or script) outputs before finalizing:
   - **Numerical accuracy:** Trace every stated metric, percentage lift, and comparison back to its originating cell output; fix any discrepancy.
   - **Grounded conclusions:** Remove any causal or speculative claims not directly backed by the executed run.
   - **Completeness:** Ensure baseline comparisons (for modeling experiments) and all spec `## Done When` items are addressed.
4. **Update spec lifecycle:**
   Update `specs/<NN-name>.md` from `Status: approved` to `Status: executed`.
5. **Present summary:**
   Share the TL;DR and key observations in chat with a direct link to `reports/<NN-name>.md`. Mention that Word (`.docx`) or PDF versions can be generated on request, and wait for the user's direction in chat.
6. **Optional document export:**
   If the user requests a Word or PDF version:
   - Check if the required skill exists (`.agents/skills/docx` or `.agents/skills/pdf`). If not, download it on demand:
     ```bash
     uv run python .agents/tools/fetch_skill.py docx   # or pdf
     ```
   - Use the downloaded Anthropic skill to compile `reports/<NN-name>.docx` or `reports/<NN-name>.pdf`. The markdown report remains the primary source of truth.
