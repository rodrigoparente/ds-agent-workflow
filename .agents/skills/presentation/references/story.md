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

Adapt section names and count to the story. Each section divider carries a one-line subtitle: the question that section answers. The TL;DR (right after the title) gives the whole story in 3-5 lines; the conclusion repeats it with the "so what".

## One idea per slide

- **Title = the message**, as a full sentence ("Adding the image lifts accuracy by 8 points"), not a label ("Results"). Two lines at most.
- **One piece of evidence** backs it: pick the single layout that proves the message best (only `image` + `bullets` may be combined).
- Two ideas means two slides. A complex idea is built across several slides, one step each.
- No paragraphs on slides. Detail goes in the presenter notes.

## Choosing the evidence

| Evidence | Use for | Example DS experiment slide |
|---|---|---|
| `bullets` | A few parallel points, reasons, or takeaways (max 5) | Why sparse listings fail; final recommendations |
| `image` | A saved chart from `docs/figures/` that proves the message | ROC / PR curve, SHAP summary, calibration plot |
| `image` + `bullets` | One saved chart paired with 2-4 concise takeaways | Confusion matrix + key misclassification takeaways |
| `images` | 2 saved figures side-by-side with captions | Baseline vs. tuned ROC; train vs. validation curves |
| `stats` | 2-4 headline KPIs (optional `delta` line per card) | AUC, F1, precision/recall with lift vs. baseline |
| `callout` | One hero verdict/metric card + 3-4 supporting bullets | `+0.07 AUC` headline lift + split & latency guardrails |
| `bars` | Horizontal ranked comparison (max 8 bars, `highlight` winner) | Model benchmark leaderboard, top feature importances |
| `compare` | 2-3 side-by-side cards (baseline vs. candidate, pros vs. cons) | Logistic Regression baseline vs. LightGBM candidate |
| `table` | Exact cross-cuts across a few rows and columns | Metrics broken down by segment or threshold |
| `flow` | A 3-5 step pipeline, architecture, or modeling process | Data prep -> features -> split -> model -> serving |
| `timeline` | 3-5 sequential iterations, milestones, or rollout phases | v1 baseline -> v2 features -> shadow test -> launch |
| `grid` | 4 or 6 structured cards (`2x2` or `3x2`, optional `tag`) | Caveats & mitigations, error buckets, feature groups |

## Presenter notes

Write **actual spoken words the presenter can read aloud**—not stage directions or bullet summaries.

- **Length & voice:** 3-6 natural, conversational sentences per slide (spoken in 30-60 seconds).
- **Add what isn't on the slide:** Explain *why* the result happened, share key methodology or data caveats, state business impact, and end with a spoken bridge to the next slide.
- **Never write meta-instructions:** Avoid phrasing like *"Explain X"*, *"Quote these numbers"*, or *"Walk left to right"*. Write the exact explanation the speaker would say out loud.
- **Never repeat the slide verbatim:** Slides show the headline evidence; notes tell the story behind it.

## Length

Roughly one slide per 1-2 minutes of the allotted time. Fewer, clearer slides beat more.

## Figures from the report & `docs/figures/`

Reuse saved experiment figures whenever they carry the message better than text or tables. One figure per slide (`image`), or two comparable figures (`images`), and state in the title what to look at. If one chart carries two distinct findings, show it on two slides with different titles and notes.
