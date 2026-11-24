# Data Science AI Workflow Starter Pack (`ds-starter-pack`)

A lightweight, human-in-the-loop template for Data Science, ML, and AI projects paired with AI coding assistants (Google Antigravity, Claude Code, Cursor).

$$\textbf{Research} \longrightarrow \textbf{Spec} \longrightarrow \textbf{Code} \longrightarrow \textbf{Run (User)} \longrightarrow \textbf{Report} \longrightarrow \textbf{Presentation}$$

---

## Key Design Choices

- **Human-in-the-Loop Execution:** The agent collaborates on specs, writes and lints code, runs unit tests, and summarizes results—but **you always run code** in Jupyter Lab or your terminal.
- **Spec-First Workflow ([OpenSpec](https://github.com/Fission-AI/OpenSpec)-inspired):** Every initiative starts with a lightweight agreement in `specs/<NN-name>.md` (`draft → approved → executed`). Follow-up changes update the spec first so documentation and code never drift.
- **Agent and Git-Friendly Notebooks ([Jupytext](https://jupytext.readthedocs.io/) + [nbstripout](https://github.com/kynan/nbstripout)):** The agent edits clean, flat Python files in `notebooks/py/<NN-name>.py`, which automatically sync to `notebooks/<NN-name>.ipynb`. Both are tracked in Git: `nbstripout` automatically strips heavy cell outputs on `git commit` / `git diff` while preserving your local executed outputs on disk so `.agents/tools/nb_summary.py` can read them.
- **Managed with `uv` + Shareable Notebooks:** Project packages live in `pyproject.toml` and `uv.lock` (managed with [uv](https://docs.astral.sh/uv/), with zero `build/` or `*.egg-info/` artifacts). Every notebook also carries a commented `# %pip install` cell at the top (`# # %pip install` in `.py`) so local runs stay fast via `uv sync` while anyone you share `.ipynb` with can uncomment and run standalone.
- **Cross-Agent Automation Hooks:** Shared lifecycle hooks in `.agents/hooks/` run across **Google Antigravity** (`.agents/hooks.json`), **Claude Code** (`.claude/settings.json`), and **Cursor** (which imports `.claude/settings.json` and `.agents/skills/`).

---

## Starting a New Project from This Template

**Prerequisite:** Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it yet (no pre-installed Python needed):

- **macOS / Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`)
- **Windows (PowerShell):** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

```bash
# 1. Clone into your new project folder with a fresh Git history
git clone <template-repo-url> my-ds-project && cd my-ds-project
rm -rf .git README.md && git init

# 2. Install workspace tooling (JupyterLab, Jupytext, nbstripout, Ruff, Pytest, python-pptx, pandoc)
uv sync

# 3. Activate the nbstripout Git filter (also runs automatically on agent SessionStart)
uv run nbstripout --install

# 4. Launch Jupyter Lab to run notebooks interactively
uv run jupyter lab
```

Open the repository in your AI assistant and ask in plain language:
- *"I want to understand how X works"*
- *"I want to explore the data in table X"*
- *"Let's build a baseline model and evaluate it"*
- *"Write the report and build a slide deck for leadership"*

---

## Repository Layout

```text
specs/                        <NN-name>.md (authoritative specs: draft → approved → executed)
notebooks/
  ├── <NN-name>.ipynb         executed notebook (tracked in Git; outputs stripped via nbstripout)
  └── py/<NN-name>.py         notebook source of truth (flat, clean, edited by agent)
models/                       serialized models and artifacts (git-ignored)
apps/                         interactive apps, dashboards, and API services
scripts/                      standalone scripts, pipelines, and shared modules
tests/                        test_<name>.py (unit and integration tests)
docs/
  ├── reports/<NN-name>.md    verified findings report (+ .docx on request)
  ├── presentations/<name>/   executive slide deck (slides.json, <name>.pptx, optional .pdf)
  ├── research/<name>.md      optional literature & concept briefs
  └── figures/<NN-name>_*.png saved charts and visualizations
data/                         cached local datasets (<NN-name>.parquet, git-ignored)
```

---

## Workflow & Skills

Skills live in `.agents/skills/` (linked at `.claude/skills`); full agent rules, collaboration principles, and handoff commands are in [AGENTS.md](AGENTS.md).

| Stage | Skill | Deliverable | Execution Owner |
|---|---|---|:---:|
| **1. Research** *(optional)* | `research` | `docs/research/<name>.md` | Agent |
| **2. Spec** | `spec` | `specs/<NN-name>.md` | Collaborative |
| **3. Code** | `write-code` | `notebooks/py/<NN-name>.py` $\leftrightarrow$ `.ipynb`, `scripts/`, `apps/`, `tests/` | Agent |
| **4. Run** | *User executes* | Outputs in `notebooks/`, `models/`, `data/`, or terminal | **User (Always)** |
| **5. Report** | `experiment-report` | `docs/reports/<NN-name>.md` (`.docx` on request) | Agent |
| **6. Presentation** | `presentation` | `docs/presentations/<name>/<name>.pptx` | Collaborative & Agent |

---

## Lifecycle Hooks & Permissions

- **`lint.py` (`PostToolUse`):** Runs `check_notebook.py` on `notebooks/py/*.py` edits (`ruff format`, `ruff check`, AST/budget/install/path/plot checks, `.ipynb` sync) and `ruff format` + `ruff check` on all other `.py` edits.
- **`stop_tests.py` (`Stop`):** Runs `pytest -x -q` before the agent finishes when Python files under `scripts/`, `apps/`, `tests/` (if `tests/test_*.py` exists) or `.agents/hooks/`, `.agents/tools/`, `.agents/skills/` were modified (skipped on interrupted Antigravity stops).
- **`session_start.py` (`SessionStart`):** Injects active Git branch, spec statuses, and next `NN-` prefix, installs the `nbstripout` Git filter, and warns if workspace tooling is missing.
- **Permissions (`.claude/settings.json`):** Allows safe helper/test commands (`uv run pytest`, `uv run ruff`, `.agents/tools/*`, skill helpers), asks before `git commit`/`push` or `uv add`/`remove`/`sync`, and denies reads of `.env*`, `~/.ssh`, `./data/`, or direct edits to `notebooks/*.ipynb`.
