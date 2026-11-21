---
name: presentation
description: Build a clean executive slide deck (white, shades of blue, one idea per slide) from a report or research the user wrote. Interviews the user about audience, goal and story, builds the narrative with them, then generates an editable .pptx with title, TL;DR, agenda, section dividers, conclusion and presenter notes. Use whenever the user wants slides, a deck, a presentation or a talk based on their work, even if they don't know yet what to present or how.
---

# Presentation

Turn the user's report or research brief into a deck that tells a story. Content comes from a conversation; the look is fixed in `scripts/deck.py`, so every deck looks the same.

Deck order: title → TL;DR → agenda → (section divider → slides) × N → conclusion.

## 1. Read the source

If the user didn't name the report or research file, ask which one. Read it fully. Note the main findings, numbers, and the figures and tables available (with their paths).

## 2. Interview (adaptive)

The interview is the most important step. Don't write slides until the goal is clear.

- Use the interactive question tool (`ask_question` / `AskUserQuestion`) with selectable options; the user can add their own answer. 1-3 questions per round, as many rounds as needed.
- Skip what the user or the report already answered. Offer options drawn from the report instead of open questions.
- Cover, in this order:
  1. **Audience**: who they are and what they already know about the topic.
  2. **Goal**: what should the audience understand, decide or do afterwards?
  3. **Setting**: duration in minutes (about one slide per 1-2 minutes) and technical depth.
  4. **Emphasis**: which findings matter most, what to leave out.
  5. **Language** of the deck: follow the report unless told otherwise.
  6. **Name** of the deck: ask the user. Don't auto-name.
- Never invent the goal or the message. If something is missing, ask or offer options.

## 3. Build the story with the user

Read `references/story.md`. Construct the story section by section (context → problem → what we did → results → conclusion), starting from what the audience needs to understand, even if the report assumes it. For each section, offer 2-3 ways to tell it (key messages taken from the report) and let the user pick or adjust. Then show the full outline as a numbered list (slide message → evidence type) and revise until the user approves. The user decides; don't present a finished plan to accept.

## 4. Build

Create `docs/presentations/<name>/` and copy the figures you use into `docs/presentations/<name>/figures/`. Write `docs/presentations/<name>/slides.json` (format: `assets/example.json`; evidence types: `bullets`, `image`, `table`, `flow`, `stats`). Then run:

```bash
.venv/bin/python .agents/skills/presentation/scripts/deck.py docs/presentations/<name>/slides.json
```

Fix every `WARNING` the script prints. The result is `docs/presentations/<name>/<name>.pptx` with editable text.

## 5. Review

First check it yourself: render to images (`soffice --headless --convert-to pdf --outdir /tmp/deck docs/presentations/<name>/<name>.pptx`, then `pdftoppm -png -r 60 /tmp/deck/<name>.pdf /tmp/deck/slide`) and look at every slide for cut-off text, overlaps and crowding. Keep the images outside the repo. If LibreOffice isn't installed, say so and review the outline instead.

Then review with the user: walk through the deck, collect changes, edit `slides.json`, rebuild. Repeat until approved.

## 6. Export and stop

Ask (interactive) which format to deliver: **pptx**, **pdf**, or **both**. PDF: `soffice --headless --convert-to pdf --outdir docs/presentations/<name> docs/presentations/<name>/<name>.pptx`. Keep only the chosen files next to `slides.json`.

Tell the user the paths and stop. Do not start anything else.
