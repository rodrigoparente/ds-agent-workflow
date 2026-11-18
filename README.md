# Data Science AI Workflow Starter Pack (`ds-starter-pack`)

A disciplined, collaborative, and human-in-the-loop framework for data science and AI projects paired with AI coding assistants (Google Antigravity, Claude Code, Cursor, and beyond).

---

## Philosophy: Human-in-the-Loop Data Science

Most AI coding setups treat the model either as an autocomplete assistant or as a fragile batch runner that hallucinates ungrounded code and runs wild without supervision. 

This starter pack establishes a structured, professional workflow:

$$\textbf{Research} \longrightarrow \textbf{Spec} \longrightarrow \textbf{Code} \longrightarrow \textbf{Run (User)} \longrightarrow \textbf{Report} \longrightarrow \textbf{Slides}$$

### Core Tenets

1. **Interactive First, Never Robotic:** The AI assistant is a thoughtful collaborative partner—not an automated script. It engages in conversation, uses interactive dialog choices (`ask_question`) to clarify open-ended requirements, surfaces trade-offs, and aligns on direction before writing code.
2. **User in the Driver's Seat (Execution Control):** The agent writes, formats, and syncs clean code, but **the data scientist always runs the code**. The agent never executes notebooks autonomously headlessly. You inspect outputs in Jupyter Lab, validate results, and guide iterations.
3. **Flexible & Spec-First:** Works naturally for exploratory data analysis (EDA), data pipelines, prototypes, and modeling experiments alike—no forced metrics when doing open-ended exploration. Every initiative begins with a lightweight agreement in `specs/<NN-name>.md`, and any iteration updates the spec first.
4. **Clean Code & Git-Friendly Notebooks:** Code is kept flat, readable, and minimal—enforced via AST structural checks (no classes, no `try/except` bloat, short helper functions) and code-only budgets (max 220 code lines per notebook, 35 code lines per cell, excluding markdown, comments, and SQL). Jupytext pairs clean `.py` files in `notebooks/py/` with `.ipynb` in `notebooks/`. Git tracks the readable python code; messy binary outputs stay local and git-ignored.
5. **Verified Evidence & Executive Storytelling:** Experiment reports are strictly verified against actual execution outputs. Presentations are built with `deck_components.py` around executive narrative arcs with complete presenter notes embedded for PowerPoint Presenter View.

---

## Repository Layout

Every initiative is organized with a two-digit prefix (`01-name`, `02-name`) inside a clean, 5-folder layout:

```
specs/                        <NN-name>.md (authoritative specs, OpenSpec-style)
notebooks/
  ├── <NN-name>.ipynb         executed notebook outputs (run by user, git-ignored)
  └── py/<NN-name>.py         notebook source of truth (flat, clean, git-tracked)
docs/
  ├── reports/<NN-name>.md    results and analysis summary (plus .docx / .pdf on request)
  ├── slides/<NN-name>.md     executive slide outline and deck (.pptx)
  ├── research/<topic>.md     optional research briefs
  └── figures/<NN-name>_*.png saved charts and visualizations
scripts/                      standalone scripts, pipelines, helper modules, deck builders
data/                         cached local data (git-ignored)
```

---

## The Collaborative Workflow

| Step | Skill | What Happens | Owner |
|---|---|---|:---:|
| **1. Research (Optional)** | `researcher` | Explores literature (arXiv), benchmark datasets, and open-source approaches. Triggers naturally on *"I want to know more about X"* or *"Explore algorithms for X"*. Produces `docs/research/<topic>.md`. | Agent |
| **2. Spec** | `experiment-spec` | Clarifies scope, data sources, and approach (for EDA, pipelines, or experiments). Converses to resolve choices, then writes `specs/<NN-name>.md` (`Status: draft` $\to$ `Status: approved`). | Collaborative |
| **3. Code** | `write-notebook` | Implements the spec as a clean Jupytext file in `notebooks/py/<NN-name>.py` (or `scripts/`). Validates formatting, line budgets, and auto-syncs `notebooks/<NN-name>.ipynb`. | Agent |
| **4. Execution** | User runs code | You open Jupyter Lab (`uv run jupyter lab`), run the notebook cells, inspect outputs, and direct any adjustments or additions. | **User (Always)** |
| **5. Report** | `experiment-report` | Inspects executed cell outputs via `nb_summary.py`, verifies every stated metric against actual outputs, writes `docs/reports/<NN-name>.md`, and updates the spec to `Status: executed`. | Agent |
| **6. Presentation** | `make-presentation` | Converses to align on audience and narrative angle, drafts `docs/slides/<NN-name>.md`, and compiles a widescreen `docs/slides/<NN-name>.pptx` via `deck_components.py` with embedded speaker notes. | Collaborative & Agent |

---

## Architecture & Design Choices (Why This Stack?)

Every tool and constraint in this repository solves a specific failure mode of AI-assisted data science:

### 1. Why Jupytext (`notebooks/py/*.py` $\leftrightarrow$ `notebooks/*.ipynb`)?
Raw `.ipynb` files are massive JSON documents packed with execution metadata, HTML tables, and base64-encoded PNG images. They produce unreadable Git diffs, frequent merge conflicts, and easily corrupt when edited directly by LLMs.
- **How it works here:** The agent only edits clean, human-readable `# %%` percent-format Python files in `notebooks/py/<NN-name>.py` (tracked by Git). `jupytext --sync` automatically mirrors code changes into `notebooks/<NN-name>.ipynb` (git-ignored) while preserving your executed cell outputs in Jupyter Lab.

### 2. Why `nb_summary.py` (and Hook Guards) Instead of Reading `.ipynb`?
When an agent reads an executed `.ipynb` file directly, a single matplotlib chart or large dataframe dump can flood the LLM context window with tens of thousands of tokens of base64 strings.
- **How it works here:** `.agents/tools/nb_summary.py` parses the executed notebook and outputs a compact, token-efficient transcript of markdown cells, code headers, and truncated text/table outputs (noting `[image output]` instead of dumping binary strings). In Claude Code, `.claude/hooks/guard.py` actively blocks direct `.ipynb` reads/edits so the agent always uses `notebooks/py/*.py` and `nb_summary.py`.

### 3. Why `ruff` + `check_notebook.py` (Smart Structural Guardrails)?
Left unchecked, LLMs tend to over-engineer data science notebooks: writing 500-line scripts, wrapping one-off pandas calls in classes or `try/except` blocks, and forgetting to add newly imported libraries to the install cell. At the same time, overly tight line limits (like 20 lines/cell) backfire by forcing ugly one-liners on readable PySpark chains and multi-panel `matplotlib` charts.
- **How it works here:** Every edit to `notebooks/py/<NN-name>.py` runs through `.agents/tools/check_notebook.py`, which enforces:
  - **Ruff formatting, simplification & complexity (`pyproject.toml`):** Auto-formats code, sorts imports, catches bugs and redundant patterns (`E`, `F`, `I`, `B`, `SIM`), caps cyclomatic complexity (`C901`, `max-complexity = 8`), and pre-declares Spark/notebook builtins (`spark`, `sc`, `display`).
  - **Code-only size budgets:** Counts *only* actual Python code lines—never penalizing markdown explanations, comments, blank lines, or triple-quoted SQL strings. Caps notebooks at **220 code lines total** and **35 code lines per cell**, leaving plenty of room for vertical PySpark chains and plots while stopping monolithic bloat.
  - **AST structural checks:** Uses Python's AST to block `class` definitions, block defensive `try/except` wrappers (so notebook errors fail transparently), cap helper functions (`def`) at **15 lines** (longer reusable logic belongs in `scripts/`), and require a 1–2 sentence markdown explanation before every analysis cell.
  - **AST import verification:** Parses the AST to ensure every third-party `import` (and implicit dependency like `pyarrow` for `.to_parquet()` or `tabulate` for `.to_markdown()`) is declared in the `# %pip install` cell.

### 4. Why `uv` + Per-Notebook `%pip install`?
Data science projects often span different environments (local laptop, remote VM, Databricks, or Colab), and different experiments may need conflicting libraries.
- **How it works here:** `uv` manages the core workspace tooling (`jupyterlab`, `jupytext`, `ruff`, `python-pptx`) rapidly and reproducibly via `pyproject.toml`, while each notebook declares its own experiment packages in its first cell (`# %pip install -q ...`). This makes every notebook self-contained and portable across local and cloud runtimes.

### 5. Why a Two-Tier `data-catalog` (`SKILL.md` + `assets/tables/*.md`)?
Real data lakes contain dozens or hundreds of tables. Dumping every table's full `printSchema()`, sample rows, and PySpark cleaning logic into a single rules file wastes context tokens on every turn.
- **How it works here:** `data-catalog/SKILL.md` serves as a lightweight directory of tables, primary/foreign keys, and common join patterns. The agent only reads `assets/tables/<table_name>.md` when a task actually touches that specific table.

### 6. Why Verified Reports & Programmatic Slides (`deck_components.py`)?
Two common last-mile failures with LLMs are (1) subtle numerical hallucinations when summarizing results, and (2) messy, overlapping text boxes when generating PowerPoint slides from scratch.
- **How it works here:**
  - `experiment-report` enforces a mandatory verification pass tracing every claim and metric in `docs/reports/<NN-name>.md` back to its exact cell output in `nb_summary.py`.
  - `deck_components.py` provides opinionated, pre-aligned `python-pptx` building blocks (unified section roadmaps, stat + story cards, bento splits, aspect-ratio-safe charts, and presenter notes) so generated `.pptx` decks look cohesive every time.

---

## Quick Start

### 1. Requirements
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (fast Python package manager)
- Node.js (optional, for slide/document export tools)

### 2. Environment Setup
```bash
# Clone and enter directory
git clone <repo-url> ds-starter-pack
cd ds-starter-pack

# Install dependencies and setup virtual environment
uv sync

# Launch Jupyter Lab for interactive notebook execution
uv run jupyter lab
```

### 3. Start Working with Your Agent
Open this workspace in your agent environment (Antigravity, Claude Code, Cursor) and start with natural language:
- *"I want to explore the data in table X"*
- *"How should we approach customer churn prediction?"*
- *"I want to know more about common search and recommendation algorithms"*
- *"Let's build an experiment testing item-based collaborative filtering"*

---

## Skills & Agent Scaffolding

Custom agent skills live in `.agents/skills/` and map 1-to-1 to the workflow stages in `AGENTS.md`:

- **`researcher`**: Literature search, academic papers, and benchmark dataset surveys.
- **`experiment-spec`**: Spec-first agreement template and interactive scoping protocol.
- **`data-catalog`**: Reference guide for lake tables, schemas, and flat PySpark data loading recipes.
- **`write-notebook`**: Implements specs as flat Jupytext notebooks with inline simplification, AST structural guardrails, and `.ipynb` synchronization.
- **`experiment-report`**: Evidence-grounded reporting template with strict cell-output verification and on-demand Word/PDF export.
- **`make-presentation`**: Audience-aligned executive slide builder with unified roadmap tracking and presenter talking points.

### Report Export Skills On-Demand
To keep the repository lightweight, optional report export skills (`docx` and `pdf`) can be fetched on demand via:
```bash
uv run python .agents/tools/fetch_skill.py docx   # or pdf
```
Optional dependencies for Word/PDF export:
- `uv sync --group docs` (installs `pypdf`, `reportlab`, and PDF utilities)
- `npm install` (installs Node `docx` package)

---

## Built-in CLI Tools

- **Verify & Sync Notebooks:**
  ```bash
  uv run python .agents/tools/check_notebook.py notebooks/py/<name>.py
  ```
  Runs `ruff` formatting, enforces line/cell budgets, checks imports, and auto-syncs `notebooks/<name>.ipynb`.

- **Summarize Run Outputs:**
  ```bash
  uv run python .agents/tools/nb_summary.py notebooks/<name>.ipynb
  ```
  Extracts cell outputs for report generation and audit checking.
