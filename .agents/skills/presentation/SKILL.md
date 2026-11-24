---
name: presentation
description: Build a clean executive .pptx slide deck (white & blue, one idea per slide) with presenter notes from a report, research brief, or technical work. Supports auto and guided outline modes. Use whenever the user wants slides, a deck, a presentation, or a talk.
---

# Presentation

Turn the user's report, research brief, or technical findings into a deck that tells a clear story. The look is fixed in `scripts/deck.py`, so every deck stays consistent.

Deck order: title → TL;DR → agenda → (section divider → slides) × N → conclusion → thank you.

Two modes (the user chooses):

| Mode | How structure happens | Best when |
|---|---|---|
| `auto` | Agent proposes a slide outline and asks for approval before generating `.pptx` | You want the agent to draft the structure first |
| `guided` | Agent summarizes available material and asks for your outline (in plain language); agent refines it and asks for approval before generating `.pptx` | You want to see everything on the table and shape the outline yourself |

## 1. Read source & gather material

If the user hasn't named the source file(s) (report in `docs/reports/`, research brief in `docs/research/`, or scripts/notebooks), ask which ones to use. Read them fully and scan `docs/figures/` for saved charts related to the work (even if some were omitted from the report). Note the key findings, numbers, tables, caveats, figure paths, and any relevant code snippets (e.g., bugs or proposed fixes).

## 2. Quick setup (1 short round)

Use `ask_question` / `AskUserQuestion` to collect only what the user hasn't already specified:

1. **Mode:** `auto` or `guided`.
2. **Audience, goal & setting:** who is listening, what they should understand or decide, target duration (~1 slide per 1–2 minutes), and technical depth.
3. **Language & deck name:** match the source language unless told otherwise; ask what to name the deck (`docs/presentations/<name>/`, don't auto-name).

## 3. Outline & approval (HARD GATE)

Read `references/story.md` before structuring slides.

- **`auto` mode:** Draft the full section arc and numbered slide outline yourself, then stop at the approval gate below.
- **`guided` mode:** Present a compact, scannable brief of everything available to work with—grouped into:
  - **Core findings & metrics** (headline numbers, benchmarks, tables)
  - **Context & approach** (problem framing, pipeline/architecture, key trade-offs)
  - **Available figures** (`docs/figures/` paths with 1-line descriptions)
  - **Code highlights** (bugs, refactors, or key snippets, if relevant)
  - **Caveats & next steps**
  Ask the user for their outline in plain language (without worrying about renderers or layouts). Adjust and polish their outline into clean sections, concise informative titles, and chosen layouts/renderers, then present the refined outline and stop at the approval gate below.

**Outline format & approval gate (both modes):**

- Show the complete numbered slide-by-slide outline:
  `Slide # · Title (informative topic label) · Layout/evidence (and figure path if used) · Brief focus`
- Ask for explicit approval via `ask_question` / `AskUserQuestion` (`(Recommended) Approve outline and build deck` vs. `Make changes`).
- **Any request to add, remove, reorder, or edit slides is a revision—NOT approval.** Update and show the revised outline, then **STOP again** for explicit approval.
- **Do NOT create `slides.json` or run `deck.py` until the latest outline is explicitly approved with no pending edits.**

## 4. Build

Create `docs/presentations/<name>/` and copy any used figures into `docs/presentations/<name>/figures/`. Write `docs/presentations/<name>/slides.json` using the layouts and JSON schema in `references/story.md` and `assets/example.json`:

- Include a closing `thanks` slide after `conclusion`.
- For non-English decks, override `title` on `tldr`, `agenda`, `conclusion`, and `thanks` (e.g., `"Obrigado"`).
- **Do not prefix section titles with numbers** (`1.`, `01`, `Section 1:`)—`deck.py` auto-numbers section dividers and the agenda.

Build the deck:

```bash
uv run python .agents/skills/presentation/scripts/deck.py docs/presentations/<name>/slides.json
```

Fix every `WARNING` the script prints. The output is `docs/presentations/<name>/<name>.pptx` with editable text.

## 5. Self-check & iterate with the user

First check the rendered slides yourself: convert to images (`soffice --headless --convert-to pdf --outdir /tmp/deck docs/presentations/<name>/<name>.pptx`, then `pdftoppm -png -r 60 /tmp/deck/<name>.pdf /tmp/deck/slide`) and inspect every slide for cut-off text, overlaps, and crowding. Keep preview images outside the repo. If LibreOffice isn't installed, note that and review `slides.json` carefully.

Share the `.pptx` path with the user and review it together: apply any requested edits to `slides.json`, rebuild, and repeat until approved.

## 6. Export and stop

Use `ask_question` / `AskUserQuestion` to ask which format to deliver: **pptx**, **pdf**, or **both**. PDF: `soffice --headless --convert-to pdf --outdir docs/presentations/<name> docs/presentations/<name>/<name>.pptx`. Keep only the chosen files next to `slides.json`.

Tell the user the output paths and stop. Do not start anything else.
