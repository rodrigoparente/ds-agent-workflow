---
name: presentation
description: Build a clean executive slide deck (white, shades of blue, one idea per slide) from a report or research the user wrote. Interviews the user about audience, goal and story, builds the narrative with them, then generates an editable .pptx with title, TL;DR, agenda, section dividers, conclusion and presenter notes. Use whenever the user wants slides, a deck, a presentation or a talk based on their work, even if they don't know yet what to present or how.
---

# Presentation

Turn the user's report or research brief into a deck that tells a story. Content comes from a conversation; the look is fixed in `scripts/deck.py`, so every deck looks the same.

Deck order: title → TL;DR → agenda → (section divider → slides) × N → conclusion.

## 1. Read the source & inventory figures

If the user didn't name the report or research file, ask which one. Read it fully, and also scan `docs/figures/` for saved charts related to the work (even if some were not embedded in the report). Note the main findings, numbers, caveats, and available figure paths so you can propose them during the story step.

## 2. Interview (adaptive)

The interview is the most important step. Don't outline or write slides until you truly understand what the user wants to achieve.

- Use `ask_question` / `AskUserQuestion` with concrete options drawn from the report (1-3 questions per round, as many rounds as needed).
- Skip what the user already specified, and cover:
  1. **Audience & concerns:** who they are, what they already know, and what objections or skepticism they might raise.
  2. **Goal / decision:** what the audience should understand, decide, or approve after the talk.
  3. **Setting:** duration in minutes (~1 slide per 1-2 minutes) and technical depth.
  4. **Emphasis & cuts:** which findings, tradeoffs, or figures matter most, and what to leave out.
  5. **Language & deck name:** follow the report language unless told otherwise; ask the user what to name the deck (don't auto-name).
- **Understanding checkpoint:** Summarize your understanding of the audience, core message, and desired outcome in 3-4 lines and confirm before building the story outline.

## 3. Build & approve the story outline (HARD GATE)

Read `references/story.md`. Co-design the narrative section by section (context → problem → what we did → results → conclusion), starting from what the audience needs to understand.

- When there is a real framing choice (e.g., executive verdict-first vs. technical walk-through, or which saved charts from `docs/figures/` to highlight), offer 2-3 concrete options via `ask_question` / `AskUserQuestion` rather than guessing.
- Present the **complete numbered slide-by-slide outline** showing for every slide:
  `Slide # · Title (full-sentence message) · Layout/evidence (and figure path if used) · 1-line spoken talking point`
- **HARD STOP — wait for explicit user approval:** Ask the user to approve or adjust the outline. **Do NOT create `slides.json` or run `deck.py` until the user explicitly approves the slide outline.**

## 4. Build

Create `docs/presentations/<name>/` and copy any used figures into `docs/presentations/<name>/figures/`. Write `docs/presentations/<name>/slides.json` following `assets/example.json`:

- Supported evidence layouts: `bullets`, `image`, `image`+`bullets`, `images`, `stats`, `callout`, `bars`, `compare`, `table`, `flow`, `timeline`, `grid`.
- **Presenter notes:** Write full, natural **read-aloud spoken text** (3-6 sentences per slide) that explains *why*, adds methodology/business context beyond the slide, and transitions smoothly to the next slide—never meta-instructions like *"Explain X"*.

Then build:

```bash
.venv/bin/python .agents/skills/presentation/scripts/deck.py docs/presentations/<name>/slides.json
```

Fix every `WARNING` the script prints. The result is `docs/presentations/<name>/<name>.pptx` with editable text.

## 5. Review

First check it yourself: render to images (`soffice --headless --convert-to pdf --outdir /tmp/deck docs/presentations/<name>/<name>.pptx`, then `pdftoppm -png -r 60 /tmp/deck/<name>.pdf /tmp/deck/slide`) and inspect every slide for cut-off text, overlaps, and crowding. Keep preview images outside the repo. If LibreOffice isn't installed, say so and review the outline instead.

Then review with the user: walk through the deck, collect changes, edit `slides.json`, rebuild, and repeat until approved.

## 6. Export and stop

Ask (interactive) which format to deliver: **pptx**, **pdf**, or **both**. PDF: `soffice --headless --convert-to pdf --outdir docs/presentations/<name> docs/presentations/<name>/<name>.pptx`. Keep only the chosen files next to `slides.json`.

Tell the user the paths and stop. Do not start anything else.
