#!/usr/bin/env python3
"""Modern, clean slide design engine for python-pptx presentations.

Design Specifications:
- Card surfaces: Background #f8fafc (CARD_BG).
- Card borders: Hairline #e2e8f0 (CARD_BORDER) with small modern rounded corners.
- Unified full-width Roadmap: Agenda and Section Dividers share the exact same template.
  No redundant [CURRENT SECTION] text—the visual blue highlight is the clean cue.
- 1 Slide = 1 Idea + 1 Purposeful Visual Layout.
"""

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# -------------------------------------------------------------
# Color Palette: Modern High-Contrast SaaS / Editorial
# -------------------------------------------------------------
BG_WHITE = RGBColor(255, 255, 255)  # Pure White slide background (#FFFFFF)
TEXT_INK = RGBColor(15, 23, 42)  # Deep Ink for headlines (#0F172A)
TEXT_BODY = RGBColor(51, 65, 85)  # Crisp Slate for body copy (#334155)
TEXT_MUTED = RGBColor(100, 116, 139)  # Medium Slate for subtitles & kickers (#64748B)
TEXT_FAINT = RGBColor(148, 163, 184)  # Light Slate for dimmed items & page numbers (#94A3B8)

ACCENT_BLUE = RGBColor(37, 99, 235)  # Sharp Cobalt for active accents & numbers (#2563EB)

# Modern Card Surfaces (User Specified: #f8fafc background, #e2e8f0 border)
CARD_BG = RGBColor(248, 250, 252)  # Ultra-light crisp gray (#f8fafc)
CARD_BORDER = RGBColor(226, 232, 240)  # Clean subtle hairline border (#e2e8f0)
CARD_BORDER_ACTIVE = RGBColor(37, 99, 235)  # Cobalt border for active/winning items (#2563EB)

# Small modern corner radius (subtle 6-8px equivalent, NOT bubbly oval clipart)
CORNER_RADIUS_WIDE = 0.035  # For wide cards (Roadmap, 11.3 in)
CORNER_RADIUS_STANDARD = 0.025  # For standard columns & cards

# Semantic Badge Colors
GREEN_TEXT = RGBColor(22, 101, 52)  # #166534
AMBER_TEXT = RGBColor(146, 64, 14)  # #92400E
RED_TEXT = RGBColor(153, 27, 27)  # #991B1B

FONT_PRIMARY = "Arial"


# -------------------------------------------------------------
# Helper: Modern Clean Card with Small Rounded Border
# -------------------------------------------------------------
def add_card_box(
    slide,
    left,
    top,
    width,
    height,
    bg_color=CARD_BG,
    border_color=CARD_BORDER,
    border_width=Pt(1),
    radius=CORNER_RADIUS_STANDARD,
):
    """Draws a flat modern card with #f8fafc background, #e2e8f0 border, and rounded corners."""
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    box.adjustments[0] = radius
    box.fill.solid()
    box.fill.fore_color.rgb = bg_color
    box.line.color.rgb = border_color
    box.line.width = border_width
    return box


# -------------------------------------------------------------
# Presentation Setup & Base Slide
# -------------------------------------------------------------
def create_deck(widescreen: bool = True) -> Presentation:
    """Initializes a 16:9 widescreen presentation."""
    prs = Presentation()
    if widescreen:
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
    return prs


def set_presenter_notes(slide, notes_text: str):
    """Embeds presenter talking points into PowerPoint Presenter View notes."""
    if not notes_text:
        return
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = notes_text.strip()


def create_base_slide(
    prs: Presentation,
    page_num: int,
    section_kicker: str = None,  # e.g. "02 / METHODOLOGY"
    title: str = None,  # The single center idea / takeaway headline
    subtitle: str = None,  # Optional 1-line context
    notes: str = "",
):
    """Creates a clean base slide with consistent header hierarchy and section breadcrumb."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG_WHITE

    # Page number (Bottom-right)
    tx_page = slide.shapes.add_textbox(Inches(11.8), Inches(6.9), Inches(1.0), Inches(0.4))
    p_page = tx_page.text_frame.paragraphs[0]
    p_page.text = str(page_num)
    p_page.alignment = PP_ALIGN.RIGHT
    p_page.font.size = Pt(10)
    p_page.font.color.rgb = TEXT_FAINT
    p_page.font.name = FONT_PRIMARY

    # Header block
    if title:
        tx_title = slide.shapes.add_textbox(Inches(1.0), Inches(0.5), Inches(11.3), Inches(1.2))
        tf = tx_title.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0)
        tf.margin_bottom = Inches(0)
        tf.margin_left = Inches(0)

        # Section breadcrumb / kicker
        if section_kicker:
            p_kick = tf.paragraphs[0]
            p_kick.text = section_kicker.upper()
            p_kick.font.size = Pt(10)
            p_kick.font.bold = True
            p_kick.font.color.rgb = ACCENT_BLUE
            p_kick.font.name = FONT_PRIMARY
            p_kick.space_after = Pt(4)
            p_title = tf.add_paragraph()
        else:
            p_title = tf.paragraphs[0]

        # Action Title
        p_title.text = title
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_INK
        p_title.font.name = FONT_PRIMARY

        # Optional Subtitle
        if subtitle:
            p_title.space_after = Pt(4)
            p_sub = tf.add_paragraph()
            p_sub.text = subtitle
            p_sub.font.size = Pt(13)
            p_sub.font.color.rgb = TEXT_MUTED
            p_sub.font.name = FONT_PRIMARY

    if notes:
        set_presenter_notes(slide, notes)

    return slide


# -------------------------------------------------------------
# Unified Full-Width Roadmap Slide (Agenda & Section Dividers)
# -------------------------------------------------------------
def add_roadmap_slide(
    prs: Presentation,
    page_num: int,
    sections: list,
    active_idx: int = None,  # None = Agenda overview; 0, 1, 2... = Section divider
    notes: str = "",
):
    """Draws a clean, full-width unified roadmap slide without redundant split columns or badges.

    Layout:
    - Top: Clean header with eyebrow, title, and context.
    - Center: 4 full-width horizontal cards spanning across the slide.
    - Subtle blue border (#e2e8f0) with small rounded corners on #f8fafc.
    - Active section has a cobalt left bar and bold blue text. Visual cue is clean and clear.
    """
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG_WHITE

    # Page number
    tx_page = slide.shapes.add_textbox(Inches(11.8), Inches(6.9), Inches(1.0), Inches(0.4))
    p_page = tx_page.text_frame.paragraphs[0]
    p_page.text = str(page_num)
    p_page.alignment = PP_ALIGN.RIGHT
    p_page.font.size = Pt(10)
    p_page.font.color.rgb = TEXT_FAINT

    # Top Header Block
    tx_hdr = slide.shapes.add_textbox(Inches(1.0), Inches(0.6), Inches(11.3), Inches(1.2))
    tf_hdr = tx_hdr.text_frame
    tf_hdr.word_wrap = True
    tf_hdr.margin_top = Inches(0)
    tf_hdr.margin_left = Inches(0)

    p_eyebrow = tf_hdr.paragraphs[0]
    if active_idx is None:
        p_eyebrow.text = "EXECUTIVE ROADMAP"
        headline = "Agenda & Discussion Roadmap"
        subtitle = "Structured walkthrough covering context, methodology, findings, and next steps."
    else:
        p_eyebrow.text = (
            f"ROADMAP PROGRESS · SECTION {active_idx + 1:02d} OF {len(sections):02d}".upper()
        )
        headline = sections[active_idx]
        subtitle = (
            f"Section {active_idx + 1:02d} of {len(sections):02d} · Key evaluation and findings."
        )

    p_eyebrow.font.size = Pt(10)
    p_eyebrow.font.bold = True
    p_eyebrow.font.color.rgb = ACCENT_BLUE
    p_eyebrow.font.name = FONT_PRIMARY
    p_eyebrow.space_after = Pt(4)

    p_title = tf_hdr.add_paragraph()
    p_title.text = headline
    p_title.font.size = Pt(25)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_INK
    p_title.font.name = FONT_PRIMARY
    p_title.space_after = Pt(4)

    p_sub = tf_hdr.add_paragraph()
    p_sub.text = subtitle
    p_sub.font.size = Pt(13)
    p_sub.font.color.rgb = TEXT_MUTED
    p_sub.font.name = FONT_PRIMARY

    # Full-Width Section Cards (Stacked cleanly below header)
    c_left = Inches(1.0)
    c_width = Inches(11.3)
    start_top = 2.1
    card_h = 0.95
    gap = 0.20

    for i, sec in enumerate(sections):
        top_pos = Inches(start_top + i * (card_h + gap))
        is_active = (active_idx == i) if active_idx is not None else False
        is_dimmed = active_idx is not None and active_idx != i

        # Full-width card container (#f8fafc background, #e2e8f0 border, small rounded corners)
        border_col = CARD_BORDER_ACTIVE if is_active else CARD_BORDER
        border_w = Pt(1.5 if is_active else 1)
        add_card_box(
            slide,
            c_left,
            top_pos,
            c_width,
            Inches(card_h),
            bg_color=CARD_BG,
            border_color=border_col,
            border_width=border_w,
            radius=CORNER_RADIUS_WIDE,
        )

        # Cobalt accent stripe on active card
        if is_active:
            stripe = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                c_left,
                top_pos + Inches(0.1),
                Inches(0.08),
                Inches(card_h) - Inches(0.2),
            )
            stripe.fill.solid()
            stripe.fill.fore_color.rgb = ACCENT_BLUE
            stripe.line.fill.background()

        # Text inside card
        tx_card = slide.shapes.add_textbox(
            c_left + Inches(0.4),
            top_pos + Inches(0.18),
            c_width - Inches(0.8),
            Inches(card_h) - Inches(0.36),
        )
        tf_card = tx_card.text_frame
        tf_card.word_wrap = False
        p_c = tf_card.paragraphs[0]

        # Numeral
        r_num = p_c.add_run()
        r_num.text = f"{i + 1:02d}    "
        r_num.font.size = Pt(18)
        r_num.font.bold = True
        r_num.font.color.rgb = (
            ACCENT_BLUE if is_active else (TEXT_FAINT if is_dimmed else ACCENT_BLUE)
        )

        # Section Title
        r_txt = p_c.add_run()
        r_txt.text = sec
        r_txt.font.size = Pt(17)
        r_txt.font.bold = is_active or (active_idx is None)
        r_txt.font.color.rgb = (
            (ACCENT_BLUE if is_active else TEXT_INK)
            if (is_active or active_idx is None)
            else TEXT_FAINT
        )

    if notes:
        set_presenter_notes(slide, notes)
    return slide


# -------------------------------------------------------------
# Component: Stat + Story (Hero Metric + Supporting Narrative)
# -------------------------------------------------------------
def add_stat_and_bullets(
    slide,
    stat_value: str,  # e.g. "24.5%"
    stat_label: str,  # e.g. "Primary Metric Improvement"
    stat_subtext: str,  # e.g. "Measured across the held-out evaluation split"
    bullets: list,  # list of ("Anchor:", "Text")
    top: Inches = Inches(2.0),
    left: Inches = Inches(1.0),
    total_width: Inches = Inches(11.3),
):
    """Layout: Asymmetrical Stat + Narrative Story in #f8fafc boxes with #e2e8f0 borders."""
    col_w = (total_width - Inches(0.5)) / 2
    height = Inches(4.5)

    # Left Column Card (Hero Stat)
    add_card_box(slide, left, top, col_w, height, radius=CORNER_RADIUS_STANDARD)

    tx_stat = slide.shapes.add_textbox(
        left + Inches(0.4), top + Inches(0.6), col_w - Inches(0.8), height - Inches(1.2)
    )
    tf_stat = tx_stat.text_frame
    tf_stat.word_wrap = True

    p_val = tf_stat.paragraphs[0]
    p_val.text = stat_value
    p_val.font.size = Pt(64)
    p_val.font.bold = True
    p_val.font.color.rgb = ACCENT_BLUE
    p_val.space_after = Pt(12)

    p_lbl = tf_stat.add_paragraph()
    p_lbl.text = stat_label
    p_lbl.font.size = Pt(20)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = TEXT_INK
    p_lbl.space_after = Pt(8)

    if stat_subtext:
        p_sub = tf_stat.add_paragraph()
        p_sub.text = stat_subtext
        p_sub.font.size = Pt(13)
        p_sub.font.color.rgb = TEXT_MUTED

    # Right Column Card (Narrative Bullets)
    r_left = left + col_w + Inches(0.5)
    add_card_box(slide, r_left, top, col_w, height, radius=CORNER_RADIUS_STANDARD)

    tx_b = slide.shapes.add_textbox(
        r_left + Inches(0.4), top + Inches(0.4), col_w - Inches(0.8), height - Inches(0.8)
    )
    tf_b = tx_b.text_frame
    tf_b.word_wrap = True

    for i, (anc, txt) in enumerate(bullets):
        p = tf_b.paragraphs[0] if i == 0 else tf_b.add_paragraph()
        p.space_after = Pt(18)
        if anc:
            r_anc = p.add_run()
            r_anc.text = anc.strip() + "  "
            r_anc.font.bold = True
            r_anc.font.size = Pt(12.5)
            r_anc.font.color.rgb = TEXT_INK
        if txt:
            r_txt = p.add_run()
            r_txt.text = txt.strip()
            r_txt.font.size = Pt(12.5)
            r_txt.font.color.rgb = TEXT_BODY


# -------------------------------------------------------------
# Component: Horizontal Architecture Pipeline (Step-by-Step Flow)
# -------------------------------------------------------------
def add_horizontal_pipeline(
    slide,
    steps: list,  # list of dicts: {"num": "01", "title": "...", "bullets": [...]}
    top: Inches = Inches(2.0),
    left: Inches = Inches(1.0),
    total_width: Inches = Inches(11.3),
    card_height: Inches = Inches(4.5),
):
    """Layout: Horizontal Step Pipeline / Phased Roadmap.

    All steps share consistent styling with #f8fafc fill, #e2e8f0 border, and rounded corners.
    """
    n = len(steps)
    if n == 0:
        return
    gap = Inches(0.35)
    step_w = (total_width - (gap * (n - 1))) / n

    for i, s in enumerate(steps):
        s_left = left + i * (step_w + gap)

        # Card container
        add_card_box(slide, s_left, top, step_w, card_height, radius=CORNER_RADIUS_STANDARD)

        # Text Frame
        tx = slide.shapes.add_textbox(
            s_left + Inches(0.3), top + Inches(0.3), step_w - Inches(0.6), card_height - Inches(0.6)
        )
        tf = tx.text_frame
        tf.word_wrap = True

        p_num = tf.paragraphs[0]
        p_num.text = f"STEP {s.get('num', f'{i + 1:02d}')}".upper()
        p_num.font.size = Pt(10)
        p_num.font.bold = True
        p_num.font.color.rgb = ACCENT_BLUE
        p_num.space_after = Pt(4)

        p_title = tf.add_paragraph()
        p_title.text = s.get("title", "")
        p_title.font.size = Pt(16)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_INK
        p_title.space_after = Pt(12)

        for anc, txt in s.get("bullets", []):
            p_b = tf.add_paragraph()
            p_b.space_after = Pt(8)
            if anc:
                r_anc = p_b.add_run()
                r_anc.text = anc.strip() + "  "
                r_anc.font.bold = True
                r_anc.font.size = Pt(11.5)
                r_anc.font.color.rgb = TEXT_INK
            if txt:
                r_txt = p_b.add_run()
                r_txt.text = txt.strip()
                r_txt.font.size = Pt(11.5)
                r_txt.font.color.rgb = TEXT_BODY


# -------------------------------------------------------------
# Component: Two-Card Bento Showcase (Side-by-Side Flat Cards)
# -------------------------------------------------------------
def add_two_column_cards(
    slide,
    left_card: dict,  # {"eyebrow": "...", "title": "...", "bullets": [...]}
    right_card: dict,  # {"eyebrow": "...", "title": "...", "bullets": [...]}
    top: Inches = Inches(2.0),
    left: Inches = Inches(1.0),
    total_width: Inches = Inches(11.3),
    height: Inches = Inches(4.5),
    bottom_note: str = None,
):
    """Layout: Two clean cards (#f8fafc fill, #e2e8f0 border, small rounded corners)."""
    col_w = (total_width - Inches(0.5)) / 2
    actual_h = height if not bottom_note else (height - Inches(0.6))

    for c_data, c_left in [(left_card, left), (right_card, left + col_w + Inches(0.5))]:
        add_card_box(slide, c_left, top, col_w, actual_h, radius=CORNER_RADIUS_STANDARD)

        tx = slide.shapes.add_textbox(
            c_left + Inches(0.35), top + Inches(0.3), col_w - Inches(0.7), actual_h - Inches(0.6)
        )
        tf = tx.text_frame
        tf.word_wrap = True

        if "eyebrow" in c_data:
            p_eye = tf.paragraphs[0]
            p_eye.text = c_data["eyebrow"].upper()
            p_eye.font.size = Pt(10)
            p_eye.font.bold = True
            p_eye.font.color.rgb = ACCENT_BLUE
            p_eye.space_after = Pt(4)
            p_t = tf.add_paragraph()
        else:
            p_t = tf.paragraphs[0]

        p_t.text = c_data.get("title", "")
        p_t.font.size = Pt(18)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_INK
        p_t.space_after = Pt(12)

        for anc, txt in c_data.get("bullets", []):
            p_b = tf.add_paragraph()
            p_b.space_after = Pt(8)
            if anc:
                r_a = p_b.add_run()
                r_a.text = anc.strip() + "  "
                r_a.font.bold = True
                r_a.font.size = Pt(12)
                r_a.font.color.rgb = TEXT_INK
            if txt:
                r_txt = p_b.add_run()
                r_txt.text = txt.strip()
                r_txt.font.size = Pt(12)
                r_txt.font.color.rgb = TEXT_BODY

    if bottom_note:
        tx_bn = slide.shapes.add_textbox(
            left, top + actual_h + Inches(0.15), total_width, Inches(0.45)
        )
        p_bn = tx_bn.text_frame.paragraphs[0]
        p_bn.text = bottom_note
        p_bn.font.size = Pt(11)
        p_bn.font.italic = True
        p_bn.font.color.rgb = TEXT_MUTED


# -------------------------------------------------------------
# Component: Flat Comparison Split (Before vs. After)
# -------------------------------------------------------------
def add_comparison_split(
    slide,
    left_col: dict,  # {"kicker": "STATUS QUO", "title": "...", "bullets": [...]}
    right_col: dict,  # {"kicker": "RECOMMENDED", "title": "...", "bullets": [...]}
    top: Inches = Inches(2.0),
    left: Inches = Inches(1.0),
    total_width: Inches = Inches(11.3),
    height: Inches = Inches(4.5),
):
    """Layout: Clean comparison with small rounded borders on #f8fafc."""
    col_w = (total_width - Inches(0.5)) / 2

    # Left Column (Status Quo)
    add_card_box(slide, left, top, col_w, height, radius=CORNER_RADIUS_STANDARD)

    tx1 = slide.shapes.add_textbox(
        left + Inches(0.4), top + Inches(0.35), col_w - Inches(0.8), height - Inches(0.7)
    )
    tf1 = tx1.text_frame
    tf1.word_wrap = True

    p_k1 = tf1.paragraphs[0]
    p_k1.text = left_col.get("kicker", "STATUS QUO").upper()
    p_k1.font.size = Pt(10)
    p_k1.font.bold = True
    p_k1.font.color.rgb = TEXT_MUTED
    p_k1.space_after = Pt(4)

    p_t1 = tf1.add_paragraph()
    p_t1.text = left_col.get("title", "")
    p_t1.font.size = Pt(18)
    p_t1.font.bold = True
    p_t1.font.color.rgb = TEXT_INK
    p_t1.space_after = Pt(14)

    for anc, txt in left_col.get("bullets", []):
        p = tf1.add_paragraph()
        p.space_after = Pt(10)
        if anc:
            r = p.add_run()
            r.text = anc.strip() + "  "
            r.font.bold = True
            r.font.size = Pt(12)
            r.font.color.rgb = TEXT_INK
        if txt:
            r = p.add_run()
            r.text = txt.strip()
            r.font.size = Pt(12)
            r.font.color.rgb = TEXT_BODY

    # Right Column (Recommended: cobalt border highlight)
    r_left = left + col_w + Inches(0.5)
    add_card_box(
        slide,
        r_left,
        top,
        col_w,
        height,
        border_color=CARD_BORDER_ACTIVE,
        border_width=Pt(1.5),
        radius=CORNER_RADIUS_STANDARD,
    )

    # Accent stripe on winning left edge
    stripe = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, r_left, top + Inches(0.1), Inches(0.08), height - Inches(0.2)
    )
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = ACCENT_BLUE
    stripe.line.fill.background()

    tx2 = slide.shapes.add_textbox(
        r_left + Inches(0.4), top + Inches(0.35), col_w - Inches(0.8), height - Inches(0.7)
    )
    tf2 = tx2.text_frame
    tf2.word_wrap = True

    p_k2 = tf2.paragraphs[0]
    p_k2.text = right_col.get("kicker", "RECOMMENDED WINNER").upper()
    p_k2.font.size = Pt(10)
    p_k2.font.bold = True
    p_k2.font.color.rgb = ACCENT_BLUE
    p_k2.space_after = Pt(4)

    p_t2 = tf2.add_paragraph()
    p_t2.text = right_col.get("title", "")
    p_t2.font.size = Pt(18)
    p_t2.font.bold = True
    p_t2.font.color.rgb = TEXT_INK
    p_t2.space_after = Pt(14)

    for anc, txt in right_col.get("bullets", []):
        p = tf2.add_paragraph()
        p.space_after = Pt(10)
        if anc:
            r = p.add_run()
            r.text = anc.strip() + "  "
            r.font.bold = True
            r.font.size = Pt(12)
            r.font.color.rgb = TEXT_INK
        if txt:
            r = p.add_run()
            r.text = txt.strip()
            r.font.size = Pt(12)
            r.font.color.rgb = TEXT_BODY


# -------------------------------------------------------------
# Component: Double Hero Stat (Two Big Metrics Side-by-Side)
# -------------------------------------------------------------
def add_double_stat(
    slide,
    stat1: dict,
    stat2: dict,
    top: Inches = Inches(2.0),
    left: Inches = Inches(1.0),
    total_width: Inches = Inches(11.3),
    height: Inches = Inches(4.5),
):
    """Layout: Two giant metrics in #f8fafc cards with small rounded #e2e8f0 borders."""
    col_w = (total_width - Inches(0.5)) / 2

    for idx, (st, c_left) in enumerate([(stat1, left), (stat2, left + col_w + Inches(0.5))]):
        add_card_box(slide, c_left, top, col_w, height, radius=CORNER_RADIUS_STANDARD)

        tx = slide.shapes.add_textbox(
            c_left + Inches(0.4), top + Inches(0.6), col_w - Inches(0.8), height - Inches(1.2)
        )
        tf = tx.text_frame
        tf.word_wrap = True

        p_val = tf.paragraphs[0]
        p_val.text = st.get("value", "")
        p_val.font.size = Pt(56)
        p_val.font.bold = True
        p_val.font.color.rgb = ACCENT_BLUE if idx == 0 else TEXT_INK
        p_val.space_after = Pt(10)

        p_lbl = tf.add_paragraph()
        p_lbl.text = st.get("label", "")
        p_lbl.font.size = Pt(19)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = TEXT_INK

        if "subtext" in st:
            p_lbl.space_after = Pt(8)
            p_sub = tf.add_paragraph()
            p_sub.text = st["subtext"]
            p_sub.font.size = Pt(13)
            p_sub.font.color.rgb = TEXT_MUTED


# -------------------------------------------------------------
# Component: Centered Visual Chart Element
# -------------------------------------------------------------
def add_chart_element(
    slide,
    image_path,
    takeaways: list = None,
    left: Inches = Inches(1.0),
    top: Inches = Inches(1.8),
    width: Inches = Inches(11.3),
    max_img_height: Inches = Inches(3.9),
):
    """Layout: Large, centered visual chart with safe aspect ratio clearance."""
    img_path = Path(image_path)
    if not img_path.exists():
        return

    with Image.open(img_path) as im:
        aspect = im.size[1] / im.size[0]

    img_h = max_img_height
    img_w = img_h / aspect
    if img_w > width:
        img_w = width
        img_h = img_w * aspect

    img_left = left + (width - img_w) / 2
    slide.shapes.add_picture(str(img_path), img_left, top, width=img_w, height=img_h)

    if takeaways:
        gap = Inches(0.20)
        tx_top = top + img_h + gap
        add_card_box(slide, left, tx_top, width, Inches(0.95), radius=CORNER_RADIUS_WIDE)

        tx = slide.shapes.add_textbox(
            left + Inches(0.3), tx_top + Inches(0.12), width - Inches(0.6), Inches(0.7)
        )
        tf = tx.text_frame
        tf.word_wrap = True

        for i, (anc, txt) in enumerate(takeaways):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(4)
            if anc:
                r_anc = p.add_run()
                r_anc.text = anc.strip() + "  "
                r_anc.font.bold = True
                r_anc.font.size = Pt(12)
                r_anc.font.color.rgb = TEXT_INK
            if txt:
                r_txt = p.add_run()
                r_txt.text = txt.strip()
                r_txt.font.size = Pt(12)
                r_txt.font.color.rgb = TEXT_BODY


# -------------------------------------------------------------
# Component: Minimalist Clean Table
# -------------------------------------------------------------
def add_clean_table(
    slide,
    headers: list,
    rows: list,
    top: Inches = Inches(2.0),
    left: Inches = Inches(1.0),
    width: Inches = Inches(11.3),
    height: Inches = Inches(4.2),
    col_widths: list = None,
):
    """Layout: Modern table with subtle border and clean alternating rows."""
    num_rows = len(rows) + 1
    num_cols = len(headers)

    table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, height)
    table = table_shape.table

    if col_widths and len(col_widths) == num_cols:
        for idx, w in enumerate(col_widths):
            table.columns[idx].width = (
                Inches(w) if isinstance(w, float) or (isinstance(w, int) and w < 50) else w
            )

    # Header Row
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = TEXT_INK
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE

        p = cell.text_frame.paragraphs[0]
        p.text = h_text.upper()
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = BG_WHITE
        p.font.name = FONT_PRIMARY
        if col_idx in (1, 2, 3) or col_idx == num_cols - 1:
            p.alignment = PP_ALIGN.CENTER

    # Data Rows
    for row_idx, r_data in enumerate(rows):
        is_even = row_idx % 2 == 0
        row_bg = BG_WHITE if is_even else CARD_BG

        for col_idx, val in enumerate(r_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = row_bg
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE

            p = cell.text_frame.paragraphs[0]

            if isinstance(val, tuple):
                tag_text, tag_type = val
                p.text = f"[{tag_text}]"
                p.alignment = PP_ALIGN.CENTER
                p.font.size = Pt(10.5)
                p.font.bold = True
                if tag_type == "success":
                    p.font.color.rgb = GREEN_TEXT
                elif tag_type == "danger":
                    p.font.color.rgb = RED_TEXT
                elif tag_type == "warning":
                    p.font.color.rgb = AMBER_TEXT
                else:
                    p.font.color.rgb = TEXT_MUTED
            else:
                p.text = str(val)
                p.font.size = Pt(12)
                p.font.color.rgb = TEXT_BODY
                if col_idx == 0:
                    p.font.bold = True
                    p.font.color.rgb = TEXT_INK
                if col_idx in (1, 2, 3) or col_idx == num_cols - 1:
                    p.alignment = PP_ALIGN.CENTER

    return table_shape
