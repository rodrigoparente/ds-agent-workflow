#!/usr/bin/env python3
"""Build an executive blue-and-white deck from a JSON spec.

Usage: uv run python .agents/skills/presentation/scripts/deck.py slides.json [out.pptx]

The look lives here and nowhere else, so every deck looks the same.
"""

import json
import re
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

# --- Look ---
NAVY, BLUE, MID, LIGHT, PALE, TEXT, MUTED, WHITE = (
    RGBColor.from_string(c)
    for c in ("0A2540", "1F5FBF", "5B9BD5", "DCEBFA", "F2F7FD", "1F2937", "64748B", "FFFFFF")
)
FONT = "Calibri"
W, H = 13.333, 7.5  # 16:9, inches
LEFT, WIDTH = 0.7, 11.93  # content margins
BODY_TOP, BODY_H = 1.95, 4.45  # content area below the title
LEFT_, CENTER = PP_ALIGN.LEFT, PP_ALIGN.CENTER


# --- Building blocks ---
def fill_text(tf, value, size, color=TEXT, bold=False, align=LEFT_):
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = value
    r.font.size, r.font.bold, r.font.name = Pt(size), bold, FONT
    r.font.color.rgb = color


def textbox(s, x, y, w, h, value, size=18, color=TEXT, bold=False, align=LEFT_, anchor=None):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.vertical_anchor = anchor or MSO_ANCHOR.TOP
    tb.text_frame.margin_left = 0  # text lines up with shapes at the same x
    fill_text(tb.text_frame, value, size, color, bold, align)
    return tb


def box(s, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE):
    b = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    b.fill.solid()
    b.fill.fore_color.rgb = fill
    b.line.fill.background()
    if (style := b._element.find(qn("p:style"))) is not None:
        b._element.remove(style)  # drop theme style: flat shapes, no shadow
    return b


def new_slide(prs, title, x=LEFT, y=0.55, w=WIDTH, h=1.2, size=30, anchor=None):
    s = prs.slides.add_slide(prs.slide_layouts[5])  # "Title Only": keeps the title in outline view
    t = s.shapes.title
    t.left, t.top, t.width, t.height = (Inches(v) for v in (x, y, w, h))
    t.text_frame.vertical_anchor = anchor or MSO_ANCHOR.TOP
    t.text_frame.margin_left = 0
    fill_text(t.text_frame, title, size, NAVY, bold=True)
    return s


def chrome(s, deck_title, bar=True):
    """Accent bar above the title, deck name bottom-left, live slide number bottom-right."""
    if bar:
        box(s, LEFT, 0.38, 0.9, 0.07, BLUE)
    textbox(s, LEFT, 7.0, 8, 0.3, deck_title, 11, MUTED)
    p = textbox(
        s, W - 1.7, 7.0, 1.0, 0.3, "", 11, MUTED, align=PP_ALIGN.RIGHT
    ).text_frame.paragraphs[0]
    fld = etree.SubElement(
        p._p, qn("a:fld"), id="{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}", type="slidenum"
    )
    rpr = etree.SubElement(fld, qn("a:rPr"), lang="en-US", sz="1100")
    etree.SubElement(etree.SubElement(rpr, qn("a:solidFill")), qn("a:srgbClr"), val=str(MUTED))
    etree.SubElement(fld, qn("a:t")).text = "1"


# --- Evidence: the one thing that backs a slide's idea ---
def bullets(s, items, x, y, w, size=28, space=18, h=BODY_H):
    tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(space)
        r = p.add_run()
        r.text = item
        r.font.size, r.font.name = Pt(size), FONT
        r.font.color.rgb = TEXT
        ppr = p._p.get_or_add_pPr()
        ppr.set("marL", str(Inches(0.35)))
        ppr.set("indent", str(-Inches(0.35)))
        etree.SubElement(etree.SubElement(ppr, qn("a:buClr")), qn("a:srgbClr"), val=str(BLUE))
        etree.SubElement(ppr, qn("a:buChar"), char="•")


def image(s, path, x, y, w, h):
    pic = s.shapes.add_picture(str(path), Inches(x), Inches(y))
    scale = min(Inches(w) / pic.width, Inches(h) / pic.height)
    pic.width, pic.height = int(pic.width * scale), int(pic.height * scale)
    pic.left = Inches(x) + (Inches(w) - pic.width) // 2
    pic.top = Inches(y) + (Inches(h) - pic.height) // 2


def images(s, items, x, y, w, h, base):
    if not items:
        return
    gap = 0.4
    cw = (w - gap * (len(items) - 1)) / len(items)
    img_h = h - 0.5
    for i, item in enumerate(items):
        if isinstance(item, str):
            rel, cap = item, ""
        else:
            rel, cap = item["path"], item.get("caption", "")
        cx = x + i * (cw + gap)
        image(s, base / rel, cx, y, cw, img_h)
        if cap:
            textbox(s, cx, y + img_h + 0.08, cw, 0.4, cap, 14, MUTED, align=CENTER)


def table(s, rows, x, y, w):
    if not rows or not rows[0]:
        return
    n_rows, n_cols = len(rows), len(rows[0])
    shape = s.shapes.add_table(
        n_rows, n_cols, Inches(x), Inches(y), Inches(w), Inches(0.7 * n_rows)
    )
    t = shape.table
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            c = t.cell(i, j)
            c.fill.solid()
            c.fill.fore_color.rgb = BLUE if i == 0 else (PALE if i % 2 == 0 else WHITE)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            fill_text(
                c.text_frame,
                str(value),
                18,
                WHITE if i == 0 else TEXT,
                i == 0,
                LEFT_ if j == 0 else CENTER,
            )


def flow(s, steps, x, y, w):
    if not steps:
        return
    gap = 0.15
    sw = (w - gap * (len(steps) - 1)) / len(steps)
    for i, step in enumerate(steps):
        sx = x + i * (sw + gap)
        arrow = box(s, sx, y + 0.3, sw, 1.0, BLUE if i % 2 == 0 else NAVY, MSO_SHAPE.PENTAGON)
        fill_text(arrow.text_frame, step["label"], 18, WHITE, True, CENTER)
        textbox(s, sx, y + 1.5, sw, 2.2, step.get("text", ""), 18)


def stats(s, items, x, y, w):
    if not items:
        return
    gap = 0.3
    cw = (w - gap * (len(items) - 1)) / len(items)
    has_delta = any(it.get("delta") for it in items)
    val_y, val_h, lbl_y, lbl_h = (0.55, 1.25, 1.85, 0.85) if has_delta else (0.7, 1.4, 2.2, 1.2)
    for i, item in enumerate(items):
        cx = x + i * (cw + gap)
        box(s, cx, y + 0.3, cw, 3.2, PALE, MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.08
        textbox(
            s, cx, y + val_y, cw, val_h, item["value"], 54, BLUE, True, CENTER, MSO_ANCHOR.MIDDLE
        )
        textbox(s, cx + 0.2, y + lbl_y, cw - 0.4, lbl_h, item["label"], 18, TEXT, align=CENTER)
        if delta := item.get("delta"):
            textbox(s, cx + 0.2, y + 2.75, cw - 0.4, 0.5, delta, 15, NAVY, True, CENTER)


def compare(s, cols, x, y, w):
    if not cols:
        return
    gap = 0.35
    cw = (w - gap * (len(cols) - 1)) / len(cols)
    title_sz, body_sz, space = (18, 16, 10) if len(cols) >= 3 else (20, 18, 12)
    for i, col in enumerate(cols):
        cx = x + i * (cw + gap)
        hdr_col = BLUE if col.get("highlight") else NAVY
        sub = col.get("subtitle", "")
        hdr_h = 0.95 if sub else 0.7
        box(s, cx, y, cw, BODY_H, PALE)
        box(s, cx, y, cw, hdr_h, hdr_col)
        textbox(s, cx + 0.2, y + 0.1, cw - 0.4, 0.45, col["title"], title_sz, WHITE, True)
        if sub:
            textbox(s, cx + 0.2, y + 0.55, cw - 0.4, 0.35, sub, 14, LIGHT)
        bullets(
            s,
            col.get("bullets", []),
            cx + 0.2,
            y + hdr_h + 0.2,
            cw - 0.4,
            size=body_sz,
            space=space,
            h=BODY_H - hdr_h - 0.3,
        )


def bars(s, items, x, y, w):
    if not items:
        return
    step = min(0.75, BODY_H / len(items))
    bh = min(0.42, step * 0.58)
    label_w, val_w = 3.5, 1.6
    track_x, track_w = x + label_w + 0.2, w - label_w - val_w - 0.4
    max_val = max((abs(float(it["value"])) for it in items), default=1.0) or 1.0
    for i, it in enumerate(items):
        ry = y + i * step
        hi = bool(it.get("highlight"))
        lbl_c, bar_c, val_c = (NAVY, BLUE, BLUE) if hi else (TEXT, MID, MUTED)
        textbox(
            s, x, ry, label_w, bh, it["label"], 17, lbl_c, hi, PP_ALIGN.RIGHT, MSO_ANCHOR.MIDDLE
        )
        box(s, track_x, ry, track_w, bh, PALE)
        bw = max(0.08, track_w * abs(float(it["value"])) / max_val)
        box(s, track_x, ry, bw, bh, bar_c)
        disp = it.get("display", str(it["value"]))
        textbox(s, track_x + track_w + 0.2, ry, val_w, bh, disp, 17, val_c, hi, LEFT_)


def callout(s, item, x, y, w):
    lw, lh, cy = 4.3, 4.1, y + 0.15
    box(s, x, cy, lw, lh, PALE, MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.06
    box(s, x, cy, 0.12, lh, BLUE)
    v_size = 40 if len(item["value"]) > 7 else 54
    textbox(
        s, x + 0.2, cy + 0.65, lw - 0.3, 1.5, item["value"], v_size, BLUE, True, CENTER,
        MSO_ANCHOR.MIDDLE,
    )
    textbox(s, x + 0.3, cy + 2.3, lw - 0.5, 1.4, item.get("label", ""), 18, TEXT, align=CENTER)
    bullets(s, item.get("bullets", []), x + lw + 0.5, cy, w - lw - 0.5, size=22, h=lh)


def timeline(s, steps, x, y, w):
    if not steps:
        return
    gap = 0.25
    sw = (w - gap * (len(steps) - 1)) / len(steps)
    if len(steps) > 1:
        box(s, x + sw / 2, y + 1.12, w - sw, 0.06, LIGHT)
    for i, step in enumerate(steps):
        cx = x + i * (sw + gap)
        if phase := step.get("phase"):
            textbox(s, cx, y + 0.2, sw, 0.45, phase, 15, BLUE, True, CENTER)
        fill, fg = (BLUE, WHITE) if step.get("done") else (LIGHT, NAVY)
        node = box(s, cx + sw / 2 - 0.27, y + 0.88, 0.54, 0.54, fill, MSO_SHAPE.OVAL)
        fill_text(node.text_frame, str(i + 1), 16, fg, True, CENTER)
        textbox(s, cx, y + 1.6, sw, 0.5, step["title"], 19, NAVY, True, CENTER)
        textbox(s, cx, y + 2.2, sw, 2.1, step.get("text", ""), 15, TEXT, align=CENTER)


def grid(s, cards, x, y, w):
    if not cards:
        return
    cols = len(cards) if len(cards) <= 3 else (2 if len(cards) == 4 else 3)
    rows = (len(cards) + cols - 1) // cols
    gx, gy = 0.3, 0.25
    cw, ch = (w - gx * (cols - 1)) / cols, (BODY_H - gy * (rows - 1)) / rows
    for i, card in enumerate(cards):
        r, c = divmod(i, cols)
        cx, cy = x + c * (cw + gx), y + r * (ch + gy)
        box(s, cx, cy, cw, ch, PALE, MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.06
        box(s, cx, cy, cw, 0.08, BLUE)
        tag = card.get("tag", "")
        title_w = cw - 1.5 if tag else cw - 0.4
        textbox(s, cx + 0.2, cy + 0.2, title_w, 0.45, card["title"], 19, NAVY, True)
        if tag:
            textbox(s, cx + cw - 1.35, cy + 0.22, 1.15, 0.4, tag, 14, BLUE, True, PP_ALIGN.RIGHT)
        textbox(s, cx + 0.2, cy + 0.72, cw - 0.4, ch - 0.85, card.get("text", ""), 15, TEXT)


RENDERERS = {
    "image": lambda s, d, base: image(s, base / d["image"], LEFT, BODY_TOP, WIDTH, BODY_H),
    "images": lambda s, d, base: images(s, d["images"], LEFT, BODY_TOP, WIDTH, BODY_H, base),
    "bullets": lambda s, d, _b: bullets(s, d["bullets"], LEFT, BODY_TOP, WIDTH),
    "table": lambda s, d, _b: table(s, d["table"], LEFT, BODY_TOP, WIDTH),
    "flow": lambda s, d, _b: flow(s, d["flow"], LEFT, BODY_TOP, WIDTH),
    "stats": lambda s, d, _b: stats(s, d["stats"], LEFT, BODY_TOP, WIDTH),
    "compare": lambda s, d, _b: compare(s, d["compare"], LEFT, BODY_TOP, WIDTH),
    "bars": lambda s, d, _b: bars(s, d["bars"], LEFT, BODY_TOP, WIDTH),
    "callout": lambda s, d, _b: callout(s, d["callout"], LEFT, BODY_TOP, WIDTH),
    "timeline": lambda s, d, _b: timeline(s, d["timeline"], LEFT, BODY_TOP, WIDTH),
    "grid": lambda s, d, _b: grid(s, d["grid"], LEFT, BODY_TOP, WIDTH),
}


def evidence(s, d, base):
    if "image" in d and "bullets" in d:
        bullets(s, d["bullets"], LEFT, BODY_TOP, 5.2, 22)
        image(s, base / d["image"], LEFT + 5.6, BODY_TOP, WIDTH - 5.6, BODY_H)
    else:
        for key, fn in RENDERERS.items():
            if key in d:
                fn(s, d, base)
                break
    if "source" in d:
        textbox(s, LEFT, 6.5, WIDTH, 0.3, d["source"], 11, MUTED)


# --- Deck ---
TITLES = {"tldr": "TL;DR", "conclusion": "Conclusion", "agenda": "Agenda"}
SECTION_NUM_RE = re.compile(r"^(?:section\s*)?\d+[\.\)\-:\s]+", re.I)
LIMITS = {
    "stats": (4, "stats"),
    "flow": (5, "steps"),
    "compare": (3, "columns"),
    "grid": (6, "cards"),
    "timeline": (5, "steps"),
    "bars": (8, "bars"),
}


def _check_image_paths(name, d, base):
    paths = [d["image"]] if "image" in d else []
    paths += [it if isinstance(it, str) else it["path"] for it in d.get("images", [])]
    for rel in paths:
        if not (base / rel).exists():
            print(f"WARNING {name}: missing image {rel}")


def _check_layout_limits(name, d, base):
    if d.get("type") == "section" and SECTION_NUM_RE.match(d.get("title", "").strip()):
        print(
            f"WARNING {name}: section title starts with a number "
            "(deck.py auto-numbers sections and agenda)"
        )
    for key, (limit, unit) in LIMITS.items():
        if len(d.get(key, [])) > limit:
            print(f"WARNING {name}: more than {limit} {unit}")
    if "images" in d and not (1 <= len(d["images"]) <= 2):
        print(f"WARNING {name}: images supports 1 or 2 figures")
    if base is not None:
        _check_image_paths(name, d, base)


def check(spec, base=None):
    """Warn when a slide drifts from the rules: one idea, one piece of evidence, notes."""
    for n, d in enumerate(spec["slides"], 2):
        name = f"slide {n} ({d.get('title') or d['type']})"
        if not d.get("notes"):
            print(f"WARNING {name}: no presenter notes")
        if len(d.get("title", "")) > 100:
            print(f"WARNING {name}: title is long")
        if len(d.get("bullets", [])) > 5:
            print(f"WARNING {name}: more than 5 bullets")
        kinds = {k for k in RENDERERS if k in d}
        if len(kinds) > 1 and kinds != {"image", "bullets"}:
            print(f"WARNING {name}: more than one kind of evidence {sorted(kinds)}")
        _check_layout_limits(name, d, base)


def _add_title_slide(prs, spec):
    s = new_slide(prs, spec["title"], 0.9, 1.6, 7.4, 2.6, 40, MSO_ANCHOR.BOTTOM)
    textbox(s, 0.9, 4.4, 7.4, 1.0, spec.get("subtitle", ""), 22, BLUE)
    meta = " · ".join(filter(None, [spec.get("author"), spec.get("date")]))
    textbox(s, 0.9, 5.6, 7.4, 0.5, meta, 16, MUTED)
    if spec.get("notes"):
        s.notes_slide.notes_text_frame.text = spec["notes"]
    for x, color in ((9.2, LIGHT), (10.5, MID), (11.8, BLUE)):
        box(s, x, 0, W - x, H, color)


def _add_section_slide(prs, d, deck, count):
    s = new_slide(prs, d["title"], 5.4, 2.4, 7.2, 1.4, 38, MSO_ANCHOR.BOTTOM)
    box(s, 0, 0, 4.6, H, LIGHT)
    textbox(s, 0.6, 2.6, 3.4, 2.2, f"{count:02d}", 96, BLUE, True, CENTER, MSO_ANCHOR.MIDDLE)
    textbox(s, 5.4, 3.95, 7.0, 1.0, d.get("subtitle", ""), 20, MUTED)
    chrome(s, deck, bar=False)
    return s


def _add_agenda_slide(prs, d, deck, sections):
    s = new_slide(prs, d.get("title", TITLES["agenda"]))
    if sections:
        step = min(0.8, BODY_H / len(sections))
        for i, name in enumerate(sections):
            textbox(s, LEFT, BODY_TOP + i * step, 1.0, step, f"{i + 1:02d}", 28, BLUE, True)
            textbox(s, LEFT + 1.2, BODY_TOP + i * step, 10, step, name, 26, NAVY)
    chrome(s, deck)
    return s


def _add_content_slide(prs, d, deck, base):
    s = new_slide(prs, d.get("title", TITLES.get(d["type"], "")))
    evidence(s, d, base)
    chrome(s, deck)
    return s


def build(spec, base):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    deck = spec["title"]
    _add_title_slide(prs, spec)

    sections = [d["title"] for d in spec["slides"] if d["type"] == "section"]
    count = 0
    for d in spec["slides"]:
        kind = d["type"]
        if kind == "section":
            count += 1
            s = _add_section_slide(prs, d, deck, count)
        elif kind == "agenda":
            s = _add_agenda_slide(prs, d, deck, sections)
        else:
            s = _add_content_slide(prs, d, deck, base)
        if d.get("notes"):
            s.notes_slide.notes_text_frame.text = d["notes"]
    return prs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    spec_path = Path(sys.argv[1])
    out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else spec_path.with_name(spec_path.parent.name + ".pptx")
    )
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    check(spec, spec_path.parent)
    build(spec, spec_path.parent).save(out)
    print(f"Saved {out}")
