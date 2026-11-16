# <NN-name> — Slide Deck Outline

Clean, modern presentation outline following the **One Slide = One Center Idea + One Purposeful Layout** rule.
Every slide communicates one clear concept backed by ONE layout component (`add_stat_and_bullets`, `add_two_column_cards`, `add_horizontal_pipeline`, `add_comparison_split`, `add_double_stat`, `add_chart_element`, or `add_clean_table`).
Slide count and section titles flex naturally based on the scope of the initiative.
Continuous orientation is maintained via the **Unified Roadmap** (`add_roadmap_slide`) for the Agenda and Section Dividers, plus **Section Kickers** on every content slide.

---

## Slide 1: Title & Context
- **Section Kicker:** `INITIATIVE BRIEFING`
- **Title:** <Clear, outcome-oriented title of the initiative>
- **Subtitle:** <Scope / Dataset / Evaluation> · <Date> · <Team / Author>
- **Layout Component:** `create_base_slide`
- **Presenter Guide:**
  - *What to say aloud:* "<Opening framing: what we investigated or built, why it matters, and the goal of today's session.>"
  - *Transition:* "Let's look at the roadmap for today's discussion."
- **Page Number:** 1

---

## Slide 2: Agenda & Discussion Roadmap
- **Section Kicker:** `EXECUTIVE ROADMAP`
- **Title:** Agenda & Discussion Roadmap
- **Layout Component:** `add_roadmap_slide(active_idx=None)`
- **Sections:**
  1. Context & Problem Scope
  2. Data & Methodology
  3. Key Findings & Evidence
  4. Recommendations & Next Steps
- **Presenter Guide:**
  - *What to say aloud:* "<Brief walkthrough of the 4 sections.>"
  - *Transition:* "Starting with the context and problem scope."
- **Page Number:** 2

---

# SECTION 01: CONTEXT & PROBLEM SCOPE

## Slide 3: Section 01 Divider
- **Layout Component:** `add_roadmap_slide(active_idx=0)`
- **Section Title:** Context & Problem Scope
- **Presenter Guide:**
  - *What to say aloud:* "<Introduce the current baseline, dataset context, or operational challenge.>"
  - *Transition:* "Let's look at the key numbers shaping our starting point."
- **Page Number:** 3

## Slide 4: Current Landscape / Baseline Friction
- **Section Kicker:** `01 / CONTEXT & PROBLEM`
- **Title:** <Action headline stating the core problem or baseline observation>
- **Subtitle:** <1-line supporting context>
- **Layout Component (`add_stat_and_bullets`):**
  - **Hero Stat:** `<Value>` · `<Label>` (*<Subtext>*)
  - **Supporting Bullets:**
    - **<Bold anchor 1>:** <Explanation of the first key driver or limitation.>
    - **<Bold anchor 2>:** <Explanation of the second key driver or quantified baseline gap.>
- **Presenter Guide:**
  - *What to say aloud:* "<Explain what the hero metric means in practice and why the status quo falls short or needs investigation.>"
  - *Transition:* "<Bridge to the next slide.>"
- **Page Number:** 4

## Slide 5: Operational & Business Context (Optional — Include if multi-faceted)
- **Section Kicker:** `01 / CONTEXT & PROBLEM`
- **Title:** <Action headline summarizing the operational or business implications>
- **Subtitle:** <1-line supporting context>
- **Layout Component (`add_two_column_cards`):**
  - **Left Card (`<EYEBROW>` — `<Card Title>`):**
    - **<Bold anchor>:** <Supporting detail.>
    - **<Bold anchor>:** <Supporting detail.>
  - **Right Card (`<EYEBROW>` — `<Card Title>`):**
    - **<Bold anchor>:** <Supporting detail.>
    - **<Bold anchor>:** <Supporting detail.>
- **Presenter Guide:**
  - *What to say aloud:* "<Contrast the two facets shown in the cards.>"
  - *Transition:* "Now let's walk through the data and methodology we used."
- **Page Number:** 5

---

# SECTION 02: DATA & METHODOLOGY

## Slide 6: Section 02 Divider
- **Layout Component:** `add_roadmap_slide(active_idx=1)`
- **Section Title:** Data & Methodology
- **Presenter Guide:**
  - *What to say aloud:* "<Introduce the data sources, cleaning rules, or modeling/analytical approach.>"
  - *Transition:* "Here is how our approach compares to the baseline / how the pipeline is structured."
- **Page Number:** 6

## Slide 7: Architecture / Approach Comparison
- **Section Kicker:** `02 / METHODOLOGY`
- **Title:** <Action headline explaining how the approach solves the problem>
- **Subtitle:** <1-line methodological summary>
- **Layout Component (`add_comparison_split` or `add_horizontal_pipeline`):**
  - **Left Column (`STATUS QUO` — `<Baseline Name>`):**
    - **<Bold anchor>:** <Limitation or assumption.>
    - **<Bold anchor>:** <Operational or accuracy drawback.>
  - **Right Column (`RECOMMENDED` — `<Proposed Approach>`):**
    - **<Bold anchor>:** <Core methodological improvement.>
    - **<Bold anchor>:** <Efficiency, quality, or scalability advantage.>
- **Presenter Guide:**
  - *What to say aloud:* "<Walk through the core design choice and why it is the simplest effective solution.>"
  - *Transition:* "<Bridge to data hygiene, guardrails, or pipeline steps.>"
- **Page Number:** 7

## Slide 8: Data Hygiene, Pipeline Steps & Guardrails
- **Section Kicker:** `02 / METHODOLOGY`
- **Title:** <Action headline on data filtering, deduplication, or validation stages>
- **Subtitle:** <1-line context on dataset scope and split>
- **Layout Component (`add_horizontal_pipeline`):**
  - **Step 01 (`<Stage 1 Title>`):** **<Anchor>:** <Detail on ingestion/deduplication.>
  - **Step 02 (`<Stage 2 Title>`):** **<Anchor>:** <Detail on transformation/modeling.>
  - **Step 03 (`<Stage 3 Title>`):** **<Anchor>:** <Detail on evaluation/validation checks.>
- **Presenter Guide:**
  - *What to say aloud:* "<Explain the validation checks and data filters that ensure reliable results.>"
  - *Transition:* "Let's look at the findings and empirical evidence."
- **Page Number:** 8

---

# SECTION 03: KEY FINDINGS & EVIDENCE

## Slide 9: Section 03 Divider
- **Layout Component:** `add_roadmap_slide(active_idx=2)`
- **Section Title:** Key Findings & Evidence
- **Presenter Guide:**
  - *What to say aloud:* "<Frame the main empirical takeaways—quantitative results, visual distributions, and trade-offs.>"
  - *Transition:* "Starting with the headline numbers."
- **Page Number:** 9

## Slide 10: Primary Quantitative Outcome
- **Section Kicker:** `03 / FINDINGS`
- **Title:** <Action headline stating the primary quantitative result or discovery>
- **Subtitle:** <Evaluation dataset and split / scope>
- **Layout Component (`add_double_stat`):**
  - **Stat 1:** `<Value 1>` · `<Label 1>` (*<Comparison vs. baseline or key context>*)
  - **Stat 2:** `<Value 2>` · `<Label 2>` (*<Secondary metric or volume context>*)
- **Presenter Guide:**
  - *What to say aloud:* "<Highlight the two numbers, how they were measured, and what they mean practically.>"
  - *Transition:* "Let's examine the visual evidence behind these numbers."
- **Page Number:** 10

## Slide 11: Primary Visual Evidence
- **Section Kicker:** `03 / FINDINGS`
- **Title:** <Action headline summarizing the pattern shown in the chart>
- **Subtitle:** <Chart context or sample size>
- **Layout Component (`add_chart_element`):**
  - **Figure:** `figures/<NN-name>_<what>.png`
  - **Takeaway Card Below Chart:** **<Key Takeaway>:** <1-sentence explanation of the visual trend or threshold.>
- **Presenter Guide:**
  - *What to say aloud:* "<Guide the audience's eyes to the axes and the main pattern in the figure.>"
  - *Transition:* "Now let's compare all evaluated options side by side."
- **Page Number:** 11

## Slide 12: Comparative Breakdown / Benchmark Table
- **Section Kicker:** `03 / FINDINGS`
- **Title:** <Action headline stating the trade-off conclusion across options or segments>
- **Subtitle:** <Comparison dimensions>
- **Layout Component (`add_clean_table`):**
  | Option / Segment | Primary Metric | Secondary Metric | Complexity / Cost | Verdict |
  |---|:---:|:---:|:---:|:---:|
  | **<Baseline / Group A>** | <val> | <val> | <Low> | `[BASELINE]` |
  | **<Candidate / Group B>** | **<val>** | **<val>** | **<Low/Med>** | `[RECOMMENDED]` |
- **Presenter Guide:**
  - *What to say aloud:* "<Explain the trade-off matrix and why the recommended option or insight stands out, including any caveats.>"
  - *Transition:* "Based on these findings, here are our recommended next steps."
- **Page Number:** 12

---

# SECTION 04: RECOMMENDATIONS & NEXT STEPS

## Slide 13: Section 04 Divider
- **Layout Component:** `add_roadmap_slide(active_idx=3)`
- **Section Title:** Recommendations & Next Steps
- **Presenter Guide:**
  - *What to say aloud:* "<Summarize how we turn these findings into concrete action.>"
  - *Transition:* "Here is the proposed roadmap and decision ask."
- **Page Number:** 13

## Slide 14: Action Plan & Decision Ask
- **Section Kicker:** `04 / RECOMMENDATIONS`
- **Title:** <Action headline stating the recommended next steps and decision needed>
- **Subtitle:** <Timeline, owners, or scope of the next iteration>
- **Layout Component (`add_horizontal_pipeline` or `add_two_column_cards`):**
  - **Step 01 (`<Immediate Action>`):** **<Owner / Scope>:** <Concrete deliverable.>
  - **Step 02 (`<Validation / Follow-up>`):** **<Success Criteria>:** <What we will measure or verify next.>
  - **Step 03 (`<Production / Scale>`):** **<Decision Gate>:** <Criteria for broader rollout.>
- **Presenter Guide:**
  - *What to say aloud:* "<Recap the core takeaway, state the specific decision or feedback needed today, and open the floor for questions.>"
  - *Open for Q&A:* Pause and invite stakeholder questions.
- **Page Number:** 14
