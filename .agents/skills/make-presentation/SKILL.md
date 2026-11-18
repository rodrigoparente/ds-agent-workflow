---
name: make-presentation
description: Turn an experiment report into an executive slide deck with speaker notes. Triggers whenever the user asks for a presentation, slides, an executive deck, a briefing deck, or slides based on an experiment or report.
---

# Make Presentation

Transforms experiment reports and data science findings into modern, clean, executive-ready presentations.

Follows a strict minimalist design philosophy: **One Slide = One Center Idea + One Supporting Element**, backed by **continuous section orientation (Agenda, Section Dividers, Section Kickers)** and **modern editorial aesthetics** (generous whitespace, zero ugly bubbly boxes).

---

## 1. Core Principles: Modern, Clean & Focused

### A. The Golden Rule: One Slide = One Center Idea + One Purposeful Layout
- **Every slide must have a single center idea:** Stated clearly in the action headline (e.g., *"Item-Based CF Cuts Recommendation Error by 7.6%"*).
- **Avoid boring bullet list monotony:** Never repeat the same plain bullet list on consecutive slides. Choose from a rich palette of purposeful visual layouts:
  1. **Stat + Story (Asymmetrical):** Giant 64pt metric on the left + 2 clean narrative bullets on the right.
  2. **Two-Card Bento Showcase:** Two flat side-by-side cards (e.g. Operational vs. Business Impact, or Two Movie Clusters).
  3. **Horizontal Architecture Pipeline:** 3-stage step-by-step flow with step numbers and deliverables.
  4. **Flat Comparison Split:** Before vs. After on flat surfaces with subtle accent striping.
  5. **Double Hero Stat:** Two massive 56pt numbers floating in whitespace.
  6. **Centered Visual Chart:** Large centered figure with safe aspect-ratio clearance and 1-line takeaway note.
  7. **Clean Minimalist Table:** Thin hairlines, centered metrics, and colored status tags.
- **Never cram multiple things on one slide:** Do NOT put a chart AND a table AND multiple bullet cards on the same slide.
- **Break complex ideas into multiple slides:** If an explanation has multiple facets, give each facet its own dedicated slide.

### B. Continuous Section Orientation (Unified Full-Width Roadmap)
- **Identical Visual DNA for Agenda & Section Dividers:** The Agenda and Section Dividers share the **exact same visual template** (`add_roadmap_slide`) without redundant split columns:
  - Top: Clean header with section kicker, title, and subtitle context.
  - Center: Full-width horizontal cards spanning across the slide. When active, the current section displays a cobalt left accent bar, bold blue title, and active border; when inactive, sections are softly dimmed.
- **Section Kicker / Breadcrumb on EVERY Content Slide:** The top-left of every content slide displays the section tracker in bold cobalt uppercase (e.g., `01 / CONTEXT & PROBLEM`, `02 / METHODOLOGY`), grounding the audience instantly.

### C. Modern, Editorial Aesthetics (#f8fafc Surfaces + #e2e8f0 Small Rounded Borders)
- **Small Modern Rounded Corners:** Cards use subtle, modern corner radii (equivalent to 6–8px in CSS, `adjustments[0] = 0.025–0.035`), avoiding both sharp rigid corners and bubbly oval clipart.
- **Card Surfaces & Palette:**
  - **Slide Background:** Pure White (`#FFFFFF`).
  - **Card Fill:** Ultra-light crisp gray (`#f8fafc`).
  - **Card Border:** Subtle hairline border (`#e2e8f0`, 1pt stroke).
  - **Headlines & Numbers:** Deep Ink (`#0F172A`) for sharp, modern contrast.
  - **Body Copy:** Dark Slate (`#334155`).
  - **Section Kickers & Subtitles:** Medium Slate (`#64748B`).
  - **Active Accent:** Sharp Vibrant Cobalt (`#2563EB`) for the active roadmap card border and accent stripes.
- **No Arbitrary Box Highlighting:** Multi-step pipelines and card grids must be styled cohesively and uniformly. Highlights are strictly reserved for active sections in roadmap dividers and winning comparisons.
- **Clean Visual Cues (No Clutter Badges):** On roadmap dividers, the active section is signaled cleanly by its blue border, blue text, and left cobalt bar—no text badges like `[CURRENT SECTION]`.

### D. Executive Scannability (Bold Keyword Anchors)
- Every bullet point bolds the first 2–4 words (e.g. `**Sub-20ms latency:** Executes pure NumPy dot products on CPU...`).
- An executive skimming the deck in 10 seconds should grasp the entire story just by reading the headlines and bold anchors.

### E. Mandatory Presenter Guide (Speaker Notes on Every Slide)
- **Every single slide MUST attach detailed talking notes to PowerPoint Presenter View:**
  - *What to say aloud:* The spoken narrative behind the slide.
  - *Nuance & context:* Details explaining why the numbers look that way.
  - *Anticipated questions & answers:* Pre-empting executive inquiries.
  - *Transition cue:* Smooth bridge into the next slide.

---

## 2. Flexible Narrative Structure

A complete presentation typically progresses through 4 core sections, adapting naturally to whether the initiative is a **modeling experiment**, an **exploratory data analysis (EDA)**, or a **data pipeline / engineering prototype**:

```
[Slide 01] Title Slide (Initiative, Scope, Team, Date)
[Slide 02] Executive Agenda (Unified Roadmap of the sections)

─── SECTION 01: CONTEXT & OBJECTIVE ───
[Slide 03] Section 01 Divider
[Slide 04] Current Landscape / Status Quo (Stat + Story or Two-Card Bento)
[Slide 05] Why This Matters / Problem Scope (Two-Card Bento or Comparison)

─── SECTION 02: DATA & METHODOLOGY ───
[Slide 06] Section 02 Divider
[Slide 07] Architecture / Analytical Approach (Comparison Split or Horizontal Pipeline)
[Slide 08] Data Scope, Filters & Guardrails (Two-Card Bento or Stat + Story)

─── SECTION 03: KEY FINDINGS & EVIDENCE ───
[Slide 09] Section 03 Divider
[Slide 10] Headline Quantitative Outcome (Double Hero Stat or Stat + Story)
[Slide 11] Primary Visual Evidence (Centered Chart + Takeaway Card)
[Slide 12] Comparative Breakdown / Segment Analysis (Clean Minimalist Table)
[Slide 13] Concrete Examples / Qualitative Insights (Two-Card Bento)

─── SECTION 04: RECOMMENDATIONS & NEXT STEPS ───
[Slide 14] Section 04 Divider
[Slide 15] Rollout Plan / Next Iteration Roadmap (Horizontal Pipeline)
[Slide 16] Concrete Decision Ask & Ownership (Two-Card Bento or Stat + Story)
```
*(Slide count and section titles flex naturally based on the report: if an insight has multiple facets, break it across slides; if an EDA is concise, use fewer slides. Every slide always follows 1 Center Idea + 1 Supporting Layout).*

---

## 3. Process

### Step 1: Align on Narrative & Scope (Converse First)
1. Read `docs/reports/<NN-name>.md` (and `specs/<NN-name>.md` if helpful for context).
2. Converse with the user via the interactive dialog box (`ask_question`) to align on target audience (Executive, Product, or Technical) and the primary narrative angle or decision ask.

### Step 2: Draft the Outline in `docs/slides/<NN-name>.md`
1. Copy or adapt `assets/outline-template.md` to `docs/slides/<NN-name>.md` following the **One Idea + One Supporting Layout** rule.
2. Ensure every content slide specifies its section kicker (`01 / CONTEXT`, `02 / METHODOLOGY`, etc.) and layout component.
3. Populate detailed **Presenter Guides** for every slide.

### Step 3: Present Concise Summary in Chat
- Share a high-level summary of the narrative arc and slide count in chat.
- Provide a direct link to `docs/slides/<NN-name>.md` for the user to review.
- Wait for user confirmation before building the `.pptx` deck.

### Step 4: Build the Deck Using `deck_components.py`
1. Write a clean builder script (e.g. `scripts/build_<NN-name>_deck.py`) importing from `.agents/skills/make-presentation/assets/deck_components.py`.
2. Available layout components in `deck_components.py`:
   - `create_deck(widescreen=True)` — Initializes a 16:9 widescreen presentation.
   - `create_base_slide(prs, page_num, section_kicker, title, subtitle, notes)` — Base content slide with header hierarchy, section breadcrumb, page number, and presenter notes.
   - `add_roadmap_slide(prs, page_num, sections, active_idx, notes)` — Unified full-width roadmap for the Agenda (`active_idx=None`) and Section Dividers (`active_idx=0, 1, ...`).
   - `add_stat_and_bullets(slide, stat_value, stat_label, stat_subtext, bullets)` — Asymmetrical hero stat card on the left + narrative bullets card on the right.
   - `add_two_column_cards(slide, left_card, right_card, bottom_note)` — Two side-by-side cards with eyebrow, title, and anchored bullets.
   - `add_horizontal_pipeline(slide, steps)` — Multi-stage horizontal flow (`STEP 01`, `STEP 02`, `STEP 03`...) for pipelines, methodology, or rollout phases.
   - `add_comparison_split(slide, left_col, right_col)` — Before vs. After / Status Quo vs. Recommended split with cobalt winner accent stripe.
   - `add_double_stat(slide, stat1, stat2)` — Two large side-by-side metric cards.
   - `add_chart_element(slide, image_path, takeaways)` — Aspect-ratio-safe centered figure with an optional takeaway card underneath.
   - `add_clean_table(slide, headers, rows, col_widths)` — Minimalist alternating-row table supporting `(text, "success"|"warning"|"danger")` status tags.
3. Run the builder script (`uv run python scripts/build_<NN-name>_deck.py`) to generate `docs/slides/<NN-name>.pptx`.

---

## 4. Reference Code Pattern (`deck_components.py`)

```python
import sys
from pathlib import Path

sys.path.append(str(Path(".agents/skills/make-presentation/assets").resolve()))

from deck_components import (
    add_chart_element,
    add_clean_table,
    add_comparison_split,
    add_double_stat,
    add_horizontal_pipeline,
    add_roadmap_slide,
    add_stat_and_bullets,
    add_two_column_cards,
    create_base_slide,
    create_deck,
)

SECTIONS = [
    "Context & Business Problem",
    "Data & Methodology",
    "Key Findings & Benchmarks",
    "Recommendations & Next Steps",
]

prs = create_deck(widescreen=True)

# Slide 1: Title Slide
s1 = create_base_slide(
    prs,
    page_num=1,
    section_kicker="INITIATIVE BRIEFING",
    title="Initiative Title: Clear Executive Headline",
    subtitle="Scope & Evaluation Summary · Date · Team",
    notes="Welcome everyone. Today we are reviewing our findings and recommended next steps.",
)

# Slide 2: Agenda (Unified Roadmap, active_idx=None)
add_roadmap_slide(prs, page_num=2, sections=SECTIONS, active_idx=None, notes="Our four-part agenda.")

# Slide 3: Section 01 Divider (Unified Roadmap, Section 01 active)
add_roadmap_slide(prs, page_num=3, sections=SECTIONS, active_idx=0, notes="Starting with context.")

# Slide 4: Stat + Story (Hero Metric + Supporting Narrative)
s4 = create_base_slide(
    prs,
    page_num=4,
    section_kicker="01 / CONTEXT & PROBLEM",
    title="Action Headline Stating the Core Baseline Challenge",
    subtitle="One-line context explaining why this metric matters.",
    notes="Walk through the primary metric and the two drivers on the right.",
)
add_stat_and_bullets(
    s4,
    stat_value="94.9%",
    stat_label="Primary Metric Label",
    stat_subtext="Supporting context for the hero number.",
    bullets=[
        ("First key driver:", "Explanation of the operational or data factor."),
        ("Second key driver:", "Quantified impact on the current baseline."),
    ],
)

# Slide 5: Two-Card Bento Showcase
s5 = create_base_slide(
    prs,
    page_num=5,
    section_kicker="01 / CONTEXT & PROBLEM",
    title="Two Complementary Facets of the Problem or Dataset",
    notes="Compare operational vs. business impact.",
)
add_two_column_cards(
    s5,
    left_card={"eyebrow": "FACET ONE", "title": "Operational Bottleneck", "bullets": [("Key point:", "Detail.")]},
    right_card={"eyebrow": "FACET TWO", "title": "Business Impact", "bullets": [("Key point:", "Detail.")]},
)

# Slide 6: Flat Comparison Split (Before vs. After)
s6 = create_base_slide(
    prs,
    page_num=6,
    section_kicker="02 / METHODOLOGY",
    title="Proposed Approach Resolves Key Limitations of the Status Quo",
    notes="Contrast the legacy baseline on the left with the proposed approach on the right.",
)
add_comparison_split(
    s6,
    left_col={"kicker": "STATUS QUO", "title": "Current Baseline", "bullets": [("Limitation:", "Detail.")]},
    right_col={"kicker": "RECOMMENDED", "title": "Proposed Approach", "bullets": [("Advantage:", "Detail.")]},
)

# Slide 7: Horizontal Pipeline (3-Stage Flow)
s7 = create_base_slide(
    prs,
    page_num=7,
    section_kicker="02 / METHODOLOGY",
    title="3-Stage Pipeline Filters Noise and Standardizes Outputs",
    notes="Explain each stage of the pipeline from ingestion to output.",
)
add_horizontal_pipeline(
    s7,
    steps=[
        {"num": "01", "title": "Ingest & Clean", "bullets": [("Deduplication:", "Remove duplicate records.")]},
        {"num": "02", "title": "Transform & Score", "bullets": [("Feature logic:", "Compute normalized scores.")]},
        {"num": "03", "title": "Validate & Export", "bullets": [("Guardrails:", "Verify coverage thresholds.")]},
    ],
)

# Slide 8: Centered Visual Chart + Takeaway
s8 = create_base_slide(
    prs,
    page_num=8,
    section_kicker="03 / FINDINGS",
    title="Visual Distribution Confirms Target Signal Concentration",
    notes="Direct attention to the chart and the key takeaway below.",
)
add_chart_element(
    s8,
    image_path="docs/figures/01-name_summary.png",
    takeaways=[("Key Takeaway:", "One-sentence interpretation of the visual pattern.")],
)

# Slide 9: Clean Minimalist Table
s9 = create_base_slide(
    prs,
    page_num=9,
    section_kicker="03 / FINDINGS",
    title="Proposed Method Achieves Best Trade-Off Across Accuracy and Cost",
    notes="Walk through the rows and highlight the recommended row.",
)
add_clean_table(
    s9,
    headers=["Approach", "Primary Metric", "Latency", "Verdict"],
    rows=[
        ["Baseline", "1.04", "<5 ms", ("BASELINE", "warning")],
        ["Proposed Approach", "0.96", "<20 ms", ("RECOMMENDED", "success")],
    ],
)

Path("docs/slides").mkdir(parents=True, exist_ok=True)
prs.save("docs/slides/01-name.pptx")
```
