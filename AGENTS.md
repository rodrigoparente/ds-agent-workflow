# Data Science Workflow & Agent Guidelines

## How We Work

We follow a collaborative, human-in-the-loop workflow: **Research (optional) → Spec → Code → Run → Report → Slides**.
- **Flexible & Intuitive:** You do not need to use rigid magic words. Natural prompts ("I want to know more about X", "Let's explore X", "Can we build X?", "Why did X happen?") route directly to the right skill.
- **Interactive First, Never Robotic:** Discuss ideas, ask clarifying questions, present trade-offs, and confirm direction before making unilateral assumptions.
- **Spec First (Even on Edits):** Every piece of work begins with an agreed spec in `specs/<NN-name>.md`. Whenever modifying, fixing, or adding to an existing experiment, **update the spec FIRST** (via `experiment-spec`) before editing code.
- **User in the Driver's Seat (Experiment Execution Ban):** The agent is a **code copilot, never an experiment runner**. The agent **NEVER executes notebooks (`notebooks/py/*.py`, `notebooks/*.ipynb`), data/experiment scripts (`scripts/*.py`), apps (`apps/*.py`), or inline Python (`python -c`)**—not even as a smoke test. The agent writes/edits code, runs static checks (`check_notebook.py` / `ruff`), auto-syncs `.ipynb`, runs unit/contract tests (`pytest`), and compiles slide decks (`scripts/build_*_deck.py`). The user **always** runs experiments in Jupyter Lab or their terminal.
- **No Forced Goals:** Exploratory data analysis (EDA), data pipelines, prototypes, and open-ended investigations without fixed metrics are fully supported.
- **Start Simple:** Establish the simplest working solution first, adding complexity only when data or user requirements justify it.

| Step | Skill | Deliverable | Execution Owner |
|---|---|---|---|
| Research (optional) | `researcher` | `docs/research/<topic>.md` | Agent searches & summarizes |
| Spec | `experiment-spec` | `specs/<NN-name>.md` (`draft → approved → executed`) | Collaborative agreement |
| Data Reference | `data-catalog` | Reference for lake tables, schemas & recipes | Reference guide |
| Code | `write-notebook` (or scripts/apps) | `notebooks/py/<NN-name>.py` → `notebooks/<NN-name>.ipynb`, `scripts/`, `apps/`, `tests/` | Agent formats, lints & auto-syncs |
| Execution | User runs code | Execution outputs in `notebooks/`, `models/`, `data/`, or terminal | **User runs always** |
| Report | `experiment-report` | `docs/reports/<NN-name>.md` (Word / PDF on request) | Agent reads outputs |
| Presentation | `make-presentation` | `docs/slides/<NN-name>.md` outline, then `.pptx` | Collaborative alignment & deck build |

## Repository Layout

```
specs/                        <NN-name>.md (authoritative specs, OpenSpec-style)
notebooks/
  ├── <NN-name>.ipynb         executed notebook (run by user, git-ignored)
  └── py/<NN-name>.py         notebook source of truth (git-tracked, auto-synced)
models/                       serialized models and artifacts (git-ignored)
apps/                         interactive apps, dashboards, and API services
scripts/                      standalone scripts, pipelines, shared modules, deck builders
tests/                        test_<name>.py (unit and integration tests)
docs/
  ├── reports/<NN-name>.md    results and analysis summary (+ .docx / .pdf)
  ├── slides/<NN-name>.md     executive slide outline and deck (.pptx)
  ├── research/<topic>.md     optional research briefs
  └── figures/<NN-name>_*.png saved charts and visualizations
data/                         cached local datasets (<NN-name>.parquet, git-ignored)
```

- **Naming:** Initiatives are named in kebab-case with a two-digit sequential number (`01-sales-eda`, `02-baseline`). Every associated file uses this exact prefix.
- **Notebooks:** `notebooks/py/<NN-name>.py` is the source of truth; `check_notebook.py` automatically generates and syncs `notebooks/<NN-name>.ipynb`. Run results are inspected through `.agents/tools/nb_summary.py`.

## Collaboration Principles

- **Dialog Boxes for Strategic Decisions & Brainstorming (Use Judiciously):** Use the interactive dialog box (`ask_question` tool) specifically when **brainstorming ideas, clarifying open-ended requirements, choosing between technical trade-offs, or aligning on narrative framing/direction**.
  - Present structured, actionable choices with a recommended option first (`(Recommended) ...`).
  - Do not add manual "Other" options in the array—the UI automatically adds an "Other" option and freeform chat input.
  - **Do NOT spam dialog boxes for routine updates:** Never show a dialog box just to ask "What should we do next?" after completing a routine request or file edit. Simply summarize the outcome in plain chat text and let the user direct the next action.
- **One Step at a Time:** Complete the specific step requested, summarize status in chat, and wait for the user. Do not execute subsequent workflow steps without user confirmation.
- **Concise Chat Outputs:** Keep chat responses focused and readable. Avoid dumping multi-page documents or massive logs into chat—provide high-level summaries and link directly to files (`specs/<NN-name>.md`, `docs/reports/<NN-name>.md`, `docs/slides/<NN-name>.md`).
- **Transparent Assumptions:** Document any default metric, data filter, or design choice not explicitly specified by the user in the spec for confirmation.

## Code Standards (Notebooks, Scripts & Apps)

Follow a minimal-code ladder:
1. Only implement what the spec explicitly requires.
2. Reuse existing project code from `scripts/` or earlier work where applicable.
3. Use Python standard library, pandas, numpy, and scikit-learn built-ins over custom functions.
4. Keep code flat and readable: avoid single-use functions, classes, config objects, and defensive wrappers.
5. Protect data integrity: retain essential validation checks (shapes, column types, split leak prevention, random seeds).

## Core Commands

### User Commands (Run by the User)
- **Environment setup:** `uv sync`
- **Launch Jupyter Lab:** `uv run jupyter lab`
- **Run standalone script:** `uv run python scripts/<name>.py`
- **Run application / service:** `uv run <app-command>` (e.g. `streamlit`, `uvicorn`, or `python apps/<name>.py`)

### Agent Allowed Operations & CLI Tools
- **File & Directory Operations (Allowed):** Reading, writing, editing, and listing project files (`specs/`, `notebooks/py/`, `models/`, `apps/`, `scripts/`, `tests/`, `docs/`) and running static linters (`uv run ruff check`, `uv run ruff format`) or unit tests (`uv run pytest`) are always allowed. *(Never read/edit `notebooks/*.ipynb` directly—use `notebooks/py/*.py` and `nb_summary.py`).*
- **Static check & auto-sync notebook (does NOT execute code):** `uv run python .agents/tools/check_notebook.py notebooks/py/<NN-name>.py`
- **Read executed notebook outputs (after user runs it):** `uv run python .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`
- **Compile PowerPoint slide deck:** `uv run python scripts/build_<NN-name>_deck.py`
