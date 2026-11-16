# Data Science Workflow & Agent Guidelines

## How We Work

We follow a collaborative, human-in-the-loop workflow: **Research (optional) → Spec → Code → Run → Report → Slides**.
- **Flexible & Intuitive:** You do not need to use rigid magic words. Saying "I want to know more about X", "Let's explore X", "Can we build X?", or "How would we do X?" naturally routes to the right skill (Research, Spec, or Code).
- **Interactive First, Never Robotic:** The agent is an interactive collaborative partner—not an automated batch script. It discusses ideas, asks clarifying questions, presents trade-offs, and confirms direction before making unilateral assumptions.
- **Spec First:** Every piece of work begins with an agreed spec in `specs/` so context is clear, documented, and easy to evolve.
- **User in the Driver's Seat (Execution):** The agent **never executes notebooks or scripts autonomously**. The agent writes/updates code and verifies formatting with `check_notebook.py`. The user runs the notebook in Jupyter Lab (`uv run jupyter lab`), reviews results, and directs adjustments.
- **No Forced Goals:** Exploratory data analysis (EDA), data pipelines, prototypes, and open-ended investigations without fixed metrics are fully supported.
- **Start Simple:** Establish the simplest working solution first, adding complexity only when data or user requirements justify it.

| Step | Skill | Deliverable | Execution Owner |
|---|---|---|---|
| Research (optional) | `researcher` | `research/<topic>.md` | Agent searches & summarizes |
| Spec | `experiment-spec` | `specs/<NN-name>.md` | Collaborative agreement |
| Data Reference | `data-catalog` | Reference for lake tables, schemas & recipes | Reference guide |
| Code | `write-notebook` (or writing scripts) | `jupytext/<NN-name>.py` / `scripts/<name>.py` | Agent formats & syncs |
| Execution | User runs code | Execution outputs in `notebooks/` or terminal | **User runs always** |
| Report | `experiment-report` | `reports/<NN-name>.md` (Word / PDF on request) | Agent reads outputs |
| Presentation | `make-presentation` | `slides/<NN-name>.md` outline, then `.pptx` | Collaborative alignment & deck build |

## Specs & Iterations

- **Lifecycle:** `Status: draft` (in discussion) → `Status: approved` (confirmed by user) → `Status: executed` (run complete, report written).
- **Clear Data Management:** When working with lake tables, consult `data-catalog` for standard PySpark loading, deduplication, and cleaning recipes. Clearly document data sources, transformations, and join logic in the spec's `## Data & Inputs` section.
- **Iterating on Active Work:** When refining, fixing, or adding to current work, update the **existing spec** `specs/<NN-name>.md` and its code.
- **Follow-up Work:** Once work is `Status: executed`, new directions start in a **new spec** `specs/<(NN+1)-name>.md` with `Builds on: <NN-name>`.

## Repository Layout

```
specs/       <NN-name>.md           spec for each initiative
jupytext/    <NN-name>.py           notebook source (when using notebooks, edit this)
notebooks/   <NN-name>.ipynb        executed notebook (run by user, git-ignored)
scripts/     <name>.py              standalone scripts, pipelines, helper modules
reports/     <NN-name>.md           results and analysis summary
slides/      <NN-name>.md           executive slide outline and deck (.pptx)
figures/     <NN-name>_<what>.png   saved charts and visualizations
research/    <topic>.md             optional research briefs
data/                               cached local data (git-ignored)
```

- **Naming:** Initiatives are named in kebab-case with a two-digit sequential number (`01-sales-eda`, `02-baseline`). Every associated file uses this exact prefix.
- **Notebooks:** When using notebooks, `jupytext/<NN-name>.py` is the source of truth. Run results are inspected through `.agents/tools/nb_summary.py`.

## Collaboration Principles

- **Dialog Boxes for Strategic Decisions & Brainstorming (Use Judiciously):** Use the interactive dialog box (`ask_question` tool) specifically when **brainstorming ideas, clarifying open-ended requirements, choosing between technical trade-offs, or aligning on narrative framing/direction**.
  - Present structured, actionable choices with a recommended option first (`(Recommended) ...`).
  - Do not add manual "Other" options in the array—the UI automatically adds an "Other" option and freeform chat input so the user can easily type anything not listed or elaborate.
  - **Do NOT spam dialog boxes for routine updates:** Never show a dialog box just to ask "What should we do next?" after completing a routine request or file edit. When work is completed, simply summarize the outcome in plain chat text and let the user direct the next action.
- **Engage and Clarify:** Don't rush into full implementation silently. Present clear trade-offs and options via the dialog box when requirements are genuinely open-ended.
- **Interactive Presentations:** Never generate a slide deck in isolation. Converse with the user via dialog box when aligning on the target audience (executives, product, engineering) and narrative angle before drafting.
- **One Step at a Time:** Complete the specific step requested, summarize status in chat, and wait for the user. Do not execute subsequent workflow steps without user confirmation.
- **User Owns Execution:** Never execute notebooks headlessly (`nbconvert`, background python execution) to produce outputs. Stop after syncing the code and ask the user to run the notebook.
- **Concise Chat Outputs:** Keep chat responses focused and readable. Avoid dumping entire multi-page slide decks or massive logs into chat—provide high-level summaries and link directly to markdown documents (`slides/<name>.md`, `reports/<name>.md`).
- **Transparent Assumptions:** Every metric, data filter, and decision not explicitly specified by the user is documented under "Assumptions" for user confirmation.

## Code Standards (Notebooks & Scripts)

Follow a minimal-code ladder:
1. Only implement what the spec explicitly requires.
2. Reuse existing project code from `scripts/` or earlier work where applicable.
3. Use Python standard library, pandas, numpy, and scikit-learn built-ins over custom functions.
4. Keep code flat and readable: avoid single-use functions, classes, config objects, and defensive wrappers.
5. Protect data integrity: retain essential validation checks (shapes, column types, split leak prevention, random seeds).

## Core Commands

- **Environment setup:** `uv sync`
- **Jupyter Lab:** `uv run jupyter lab`
- **Verify & sync notebook:** `uv run python .agents/tools/check_notebook.py jupytext/<name>.py`
- **Summarize run outputs:** `uv run python .agents/tools/nb_summary.py notebooks/<name>.ipynb`
- **Fetch report export skills on-demand:** `uv run python .agents/tools/fetch_skill.py <docx|pdf>`
