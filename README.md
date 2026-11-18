# Data Science AI Workflow Starter Pack (`ds-starter-pack`)

A lightweight, human-in-the-loop template for Data Science, ML, and AI projects paired with AI coding assistants (Google Antigravity, Claude Code, Cursor).

$$\textbf{Research} \longrightarrow \textbf{Spec} \longrightarrow \textbf{Code} \longrightarrow \textbf{Run (User)} \longrightarrow \textbf{Report} \longrightarrow \textbf{Slides}$$

---

## Key Design Choices

- **Human-in-the-Loop Execution:** The agent collaborates on specs, writes and lints code, runs unit tests, and summarizes results—but **you always run experiments** in Jupyter Lab or your terminal.
- **Spec-First Workflow ([OpenSpec](https://github.com/Fission-AI/OpenSpec)-inspired):** Every initiative starts with a lightweight agreement in `specs/<NN-name>.md` (`draft → approved → executed`). Follow-up changes update the spec first so documentation and code never drift.
- **Git-Friendly Notebooks ([Jupytext](https://jupytext.readthedocs.io/)):** The agent edits clean, flat Python files in `notebooks/py/<NN-name>.py` (tracked in Git), which automatically sync to `notebooks/<NN-name>.ipynb` (git-ignored) so binary cell outputs never pollute Git diffs or LLM context.
- **Pragmatic Layout ([Cookiecutter Data Science](https://cookiecutter-data-science.drivendata.org/)-inspired):** Sequentially numbered initiatives (`01-`, `02-`) across a flat folder structure without heavy boilerplate packages. Workspace tooling is managed by [uv](https://docs.astral.sh/uv/), while each notebook declares its own libraries via `# %pip install`.

---

## Quick Start

```bash
# 1. Install workspace tooling (JupyterLab, Jupytext, Ruff, Pytest, python-pptx)
uv sync

# 2. Launch Jupyter Lab to run notebooks interactively
uv run jupyter lab
```

Open the repository in your AI assistant and ask in plain language:
- *"I want to explore the data in table X"*
- *"What are the simplest fast baselines for X?"*
- *"Let's build a baseline model and evaluate it"*
- *"Write the report and build a slide deck for leadership"*

---

## Repository Layout

```text
specs/                        <NN-name>.md (authoritative specs: draft → approved → executed)
notebooks/
  ├── <NN-name>.ipynb         executed notebook with outputs (run by user, git-ignored)
  └── py/<NN-name>.py         notebook source of truth (flat, clean, git-tracked)
models/                       serialized models and artifacts (git-ignored)
apps/                         interactive apps, dashboards, and API services
scripts/                      standalone scripts, pipelines, shared modules, deck builders
tests/                        test_<name>.py (unit and integration tests)
docs/
  ├── reports/<NN-name>.md    verified findings report (+ .docx / .pdf on request)
  ├── slides/<NN-name>.md     executive slide outline and deck (.pptx)
  ├── research/<topic>.md     optional literature & benchmark briefs
  └── figures/<NN-name>_*.png saved charts and visualizations
data/                         cached local datasets (<NN-name>.parquet, git-ignored)
```

---

## Workflow & Skills

Skills live in `.agents/skills/` and follow the rules in [AGENTS.md](AGENTS.md):

| Stage | Skill | Deliverable | Execution Owner |
|---|---|---|:---:|
| **1. Research** *(optional)* | `researcher` | `docs/research/<topic>.md` | Agent |
| **2. Spec** | `experiment-spec` | `specs/<NN-name>.md` | Collaborative |
| **3. Data Reference** | `data-catalog` | Lake table schemas & loading recipes | Reference |
| **4. Code** | `write-notebook` | `notebooks/py/<NN-name>.py` $\leftrightarrow$ `.ipynb`, `scripts/`, `apps/`, `tests/` | Agent |
| **5. Run** | *User executes* | Outputs in `notebooks/`, `models/`, `data/`, or terminal | **User (Always)** |
| **6. Report** | `experiment-report` | `docs/reports/<NN-name>.md` (`.docx` / `.pdf` on request) | Agent |
| **7. Presentation** | `make-presentation` | `docs/slides/<NN-name>.md` $\to$ `docs/slides/<NN-name>.pptx` | Collaborative & Agent |

---

## Built-in Helper Tools

- **Format, lint & sync notebook:** `uv run python .agents/tools/check_notebook.py notebooks/py/<NN-name>.py`
- **Inspect executed notebook outputs:** `uv run python .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`
- **Fetch optional Word/PDF export skills:** `uv run python .agents/tools/fetch_skill.py docx` *(or `pdf`)*
