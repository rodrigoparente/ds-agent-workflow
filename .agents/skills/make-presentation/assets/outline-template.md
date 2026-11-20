# <NN-name> — Slide Deck Outline

Available layout components in `deck_components.py`: `create_base_slide`, `add_roadmap_slide`, `add_stat_and_bullets`, `add_two_column_cards`, `add_horizontal_pipeline`, `add_comparison_split`, `add_double_stat`, `add_chart_element`, `add_clean_table`.

---

## Slide 1: Title & Context
- **Section Kicker:** `INITIATIVE BRIEFING`
- **Title:** <Outcome-oriented title>
- **Subtitle:** <Scope / Dataset / Evaluation> · <Date> · <Team / Author>
- **Layout:** `create_base_slide`
- **Presenter Guide:** *Say:* "<Opening framing & goal>" · *Transition:* "Let's review today's roadmap."

## Slide 2: Agenda & Discussion Roadmap
- **Section Kicker:** `EXECUTIVE ROADMAP`
- **Layout:** `add_roadmap_slide(active_idx=None)`
- **Sections:** 1. Context & Problem Scope · 2. Data & Methodology · 3. Key Findings & Evidence · 4. Recommendations & Next Steps
- **Presenter Guide:** *Say:* "<4-part walkthrough>" · *Transition:* "Starting with context."

---

## Section 01: Context & Problem Scope
- **Divider (Slide 3):** `add_roadmap_slide(active_idx=0)`
- **Slide 4 (`01 / CONTEXT & PROBLEM`, `add_stat_and_bullets`):**
  - **Headline:** <Action headline stating core challenge or baseline>
  - **Hero Stat:** `<Value>` · `<Label>` (*<Subtext>*) | **Bullets:** `**Anchor:** Detail`
  - **Presenter Guide:** *Say:* "<Practical meaning>" · *Q&A / Transition:* "<Bridge>"
- **Slide 5 (Optional, `add_two_column_cards`):**
  - **Headline:** <Operational vs. business facets>
  - **Left (`<EYEBROW>` — `<Title>`) / Right (`<EYEBROW>` — `<Title>`):** 2–3 bold-anchored bullets each.
  - **Presenter Guide:** *Say:* "<Contrast facets>" · *Transition:* "Next, data and methodology."

## Section 02: Data & Methodology
- **Divider (Slide 6):** `add_roadmap_slide(active_idx=1)`
- **Slide 7 (`02 / METHODOLOGY`, `add_comparison_split`):**
  - **Headline:** <How proposed approach resolves baseline limitations>
  - **Left (`STATUS QUO` — `<Baseline>`) vs. Right (`RECOMMENDED` — `<Approach>`):** 2–3 bullets each.
  - **Presenter Guide:** *Say:* "<Why simplest effective choice>" · *Transition:* "<To data hygiene>"
- **Slide 8 (`02 / METHODOLOGY`, `add_horizontal_pipeline`):**
  - **Headline:** <Data filtering, deduplication, and validation stages>
  - **Steps 01–03:** `<Stage Title>` — `**Anchor:** Detail`
  - **Presenter Guide:** *Say:* "<Guardrails & split hygiene>" · *Transition:* "Now, empirical findings."

## Section 03: Key Findings & Evidence
- **Divider (Slide 9):** `add_roadmap_slide(active_idx=2)`
- **Slide 10 (`03 / FINDINGS`, `add_double_stat`):**
  - **Headline:** <Primary quantitative outcome>
  - **Stat 1 & Stat 2:** `<Value>` · `<Label>` (*<Baseline context>*)
  - **Presenter Guide:** *Say:* "<Measurement & impact>" · *Transition:* "<To visual evidence>"
- **Slide 11 (`03 / FINDINGS`, `add_chart_element`):**
  - **Headline:** <Pattern shown in chart>
  - **Figure:** `docs/figures/<NN-name>_<what>.png` · **Takeaway:** `**Key Takeaway:** <1 sentence>`
  - **Presenter Guide:** *Say:* "<Guide eyes to axes & trend>" · *Transition:* "<To benchmark table>"
- **Slide 12 (`03 / FINDINGS`, `add_clean_table`):**
  - **Headline:** <Trade-off verdict across options>
  - **Table:** `Option | Primary Metric | Secondary Metric | Cost | Verdict (`BASELINE` / `RECOMMENDED`)`
  - **Presenter Guide:** *Say:* "<Trade-offs & caveats>" · *Transition:* "Finally, recommended next steps."

## Section 04: Recommendations & Next Steps
- **Divider (Slide 13):** `add_roadmap_slide(active_idx=3)`
- **Slide 14 (`04 / RECOMMENDATIONS`, `add_horizontal_pipeline` or `add_two_column_cards`):**
  - **Headline:** <Recommended action plan & decision ask>
  - **Steps 01–03:** `<Immediate Action>` / `<Validation>` / `<Rollout Gate>`
  - **Presenter Guide:** *Say:* "<Recap, decision needed today, open for Q&A>"
