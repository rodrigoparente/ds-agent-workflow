"""Reference pattern for building a presentation with deck_components.py."""

import sys
from pathlib import Path

sys.path.append(str(Path(".agents/skills/make-presentation/assets").resolve()))

from deck_components import (  # noqa: E402
    add_chart_element,
    add_clean_table,
    add_comparison_split,
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
create_base_slide(
    prs,
    page_num=1,
    section_kicker="INITIATIVE BRIEFING",
    title="Initiative Title: Clear Executive Headline",
    subtitle="Scope & Evaluation Summary · Date · Team",
    notes="Welcome everyone. Today we are reviewing our findings and recommended next steps.",
)

# Slide 2: Agenda (Unified Roadmap, active_idx=None)
add_roadmap_slide(
    prs, page_num=2, sections=SECTIONS, active_idx=None, notes="Our four-part agenda."
)

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
    stat_value="24.5%",
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
    left_card={
        "eyebrow": "FACET ONE",
        "title": "Operational Bottleneck",
        "bullets": [("Key point:", "Detail.")],
    },
    right_card={
        "eyebrow": "FACET TWO",
        "title": "Business Impact",
        "bullets": [("Key point:", "Detail.")],
    },
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
    left_col={
        "kicker": "STATUS QUO",
        "title": "Current Baseline",
        "bullets": [("Limitation:", "Detail.")],
    },
    right_col={
        "kicker": "RECOMMENDED",
        "title": "Proposed Approach",
        "bullets": [("Advantage:", "Detail.")],
    },
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
        {
            "num": "01",
            "title": "Ingest & Clean",
            "bullets": [("Deduplication:", "Remove duplicate records.")],
        },
        {
            "num": "02",
            "title": "Transform & Score",
            "bullets": [("Feature logic:", "Compute normalized scores.")],
        },
        {
            "num": "03",
            "title": "Validate & Export",
            "bullets": [("Guardrails:", "Verify coverage thresholds.")],
        },
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
