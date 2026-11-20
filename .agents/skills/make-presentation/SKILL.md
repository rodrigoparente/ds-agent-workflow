---
name: make-presentation
description: Turn an experiment report into an executive slide deck with speaker notes. Triggers whenever the user asks for a presentation, slides, an executive deck, a briefing deck, or slides based on an experiment or report.
---

# Make Presentation

Transforms experiment reports and data science findings into clean, executive-ready presentations.

## Design Rules

- **One Slide = One Center Idea + One Supporting Layout:** State the takeaway in an action headline (e.g., *"Proposed Approach Cuts Error by 12% While Halving Latency"*). Never cram a chart, table, and multiple cards onto one slide; split multi-facet explanations across slides and vary layouts across consecutive slides.
- **Continuous Orientation:** Use `add_roadmap_slide` for both the Agenda (`active_idx=None`) and Section Dividers (`active_idx=0, 1, ...`), and set a bold uppercase `section_kicker` (e.g., `01 / CONTEXT & PROBLEM`) on every content slide.
- **Executive Scannability:** Bold the first 2–4 words of every bullet (e.g., `**Sub-20ms latency:** Executes pure NumPy dot products on CPU...`).
- **Editorial Styling via `deck_components.py`:** Let `.agents/skills/make-presentation/assets/deck_components.py` handle surfaces, typography, and accent striping. Reserve highlights strictly for active roadmap sections and winning comparisons; do not add clutter badges like `[CURRENT SECTION]`.
- **Mandatory Presenter Notes:** Attach speaker notes to every slide covering *what to say aloud*, *nuance & context*, *anticipated Q&A*, and a *transition cue*.

## Narrative Arc

Structure decks around `Title → Agenda → 01 Context & Objective → 02 Data & Methodology → 03 Key Findings & Evidence → 04 Recommendations & Next Steps` (see `assets/outline-template.md`), flexing slide count and section titles naturally to fit the report.

## Process

1. **Align on narrative & scope:**
   Read `docs/reports/<NN-name>.md` (and `specs/<NN-name>.md` if needed). Clarify target audience (Executive, Product, or Technical) and the primary narrative angle or decision ask via `ask_question`.
2. **Draft the outline (`docs/slides/<NN-name>.md`):**
   Adapt `assets/outline-template.md` into `docs/slides/<NN-name>.md`, specifying each slide's `section_kicker`, layout component, content, and Presenter Guide.
3. **Review with the user:**
   Share a concise summary of the narrative arc and slide count in chat with a link to `docs/slides/<NN-name>.md`, and wait for confirmation before building `.pptx`.
4. **Build the `.pptx` deck:**
   - Read `assets/example_build_deck.py` for the `deck_components.py` import and layout call patterns, then write `scripts/build_<NN-name>_deck.py`.
   - Run `uv run python scripts/build_<NN-name>_deck.py` to generate `docs/slides/<NN-name>.pptx`.
