# Story and slide rules

A deck is a story the audience can follow without reading ahead. Build it from the ground: start where the audience is, not where the report starts.

## The arc

| Section | Answers | Notes |
|---|---|---|
| Context | Why are we here? What do you need to know first? | Define the concepts the audience lacks, even if the report assumes them |
| Problem | What is wrong or missing, and why does it matter? | One problem, stated plainly |
| What we did | How did we approach it? | Simple to detailed; only the depth the audience needs |
| Results | What did we find? | Lead with the strongest finding |
| Conclusion | So what? | What it means, and what comes next if the user wants it |

Adapt section names and count to the story. Each section divider carries a one-line subtitle: the question that section answers. The TL;DR (right after the title) gives the whole story in 3–5 lines; the conclusion repeats it with the "so what", followed by a closing `thanks` slide.

## One idea per slide

- **Title = informative topic label:** State concisely *what the slide shows* (typically 2–6 words; 1 line preferred, 2 max)—neither forced commentary nor a vague generic word. Let the slide's evidence and presenter notes deliver the commentary.
  - Good: *"Application HTTP Statuses"*, *"Accuracy by Title Length"*, *"Multimodal Embedding Pipeline"*
  - Bad: *"Each status is triggered by a different condition"* (filler commentary) or *"Results"* (too vague)
- **One piece of evidence** backs it: pick the single layout that shows the idea best (only `image` + `bullets` or a single `code` block + `bullets` may be combined).
- Two ideas means two slides. A complex idea is built across several slides, one step each.
- No paragraphs on slides. Detail goes in the presenter notes.

## Choosing the evidence

| Evidence | Use for | Example slide |
|---|---|---|
| `bullets` | A few parallel points, reasons, or takeaways (max 5) | Why sparse listings fail; final recommendations |
| `image` | A saved chart from `docs/figures/` that carries the message | ROC / PR curve, SHAP summary, calibration plot |
| `image` + `bullets` | One saved chart paired with 2–4 concise takeaways | Confusion matrix + key misclassification takeaways |
| `images` | 2 saved figures side-by-side with captions | Baseline vs. tuned ROC; train vs. validation curves |
| `stats` | 2–4 headline KPIs (optional `delta` line per card) | AUC, F1, precision/recall with lift vs. baseline |
| `callout` | One hero verdict/metric card + 3–4 supporting bullets | `+0.07 AUC` headline lift + split & latency guardrails |
| `bars` | Horizontal ranked comparison (max 8 bars, `highlight` winner) | Model benchmark leaderboard, top feature importances |
| `compare` | 2–3 side-by-side cards (baseline vs. candidate, pros vs. cons) | Logistic Regression baseline vs. LightGBM candidate |
| `table` | Exact cross-cuts across a few rows and columns | Metrics broken down by segment or threshold |
| `flow` | A 3–5 step pipeline, architecture, or modeling process | Data prep -> features -> split -> model -> serving |
| `timeline` | 3–5 sequential iterations, milestones, or rollout phases | v1 baseline -> v2 features -> shadow test -> launch |
| `grid` | 2, 3, 4, or 6 structured cards (`2x1`, `3x1`, `2x2`, `3x2`, optional `tag`) | 3 model families (`3x1`), caveats & mitigations (`2x2`) |
| `code` | 1 snippet (max 14 lines; optional `highlight` line numbers, `start_line`, `tone`: `info` \| `bug` \| `fix`) or 2 snippets side-by-side | Buggy query vs. fixed query; fallback logic refactor |
| `code` + `bullets` | 1 code snippet on the left + 2–4 concise takeaways on the right | Highlighting a bottleneck or fix with key implications |

**Layout selection guardrails:**
- **Match slots to items:** Never cram 3 distinct models or techniques into a 2-column `compare`—use a 3-column `compare`, a 3-card `grid` (`3x1`), or 1 slide per technique when each needs explanation.
- **Keep code readable:** Trim snippets to the 6–14 lines that matter and highlight only the 1–3 critical line numbers.
- **Give datasets & concepts text context:** Use `image` + `bullets` (or a context/`stats` slide before the chart) when introducing a dataset, split, or unfamiliar concept; reserve bare `image` slides for self-explanatory charts whose takeaway is clear from the title alone.

## Presenter notes

Write **actual spoken words the presenter can read aloud**—not stage directions or bullet summaries.

- **Length & voice:** 3–6 natural, conversational sentences per slide (spoken in 30–60 seconds).
- **Add what isn't on the slide:** Explain *why* the result happened, share key methodology or data caveats, state business impact, and end with a spoken bridge to the next slide.
- **Never write meta-instructions:** Avoid phrasing like *"Explain X"*, *"Quote these numbers"*, or *"Walk left to right"*. Write the exact explanation the speaker would say out loud.
- **Never repeat the slide verbatim:** Slides show the headline evidence; notes tell the story behind it.

## Length

Roughly one slide per 1–2 minutes of the allotted time. Fewer, clearer slides beat more.

## Figures from the report & `docs/figures/`

Reuse saved experiment figures whenever they carry the message better than text or tables. One figure per slide (`image`), or two comparable figures (`images`), with a title that clearly names what the chart shows (e.g., *"Validation ROC Curve by Model"*). If one chart carries two distinct findings, show it on two slides with different titles and notes.
