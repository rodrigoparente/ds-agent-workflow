# Data Science AI Workflow Starter Pack (`ds-starter-pack`)

A lightweight, human-in-the-loop framework for Data Science, ML, and Data Engineering projects paired with AI coding assistants (Google Antigravity, Claude Code, Cursor).

$$\textbf{Research} \longrightarrow \textbf{Spec} \longrightarrow \textbf{Code} \longrightarrow \textbf{Run (User)} \longrightarrow \textbf{Report} \longrightarrow \textbf{Presentation}$$

---

## Key Design Choices

- **Human-in-the-Loop Execution (*"Agent Generates, You Run"*):** Autonomous agent compute loops break down in data work due to long-running queries/training, warehouse/GPU costs, data privacy, and empirical judgment. Here, the agent collaborates on specs, writes and lints code, and runs fast synthetic `pytest` suites—while **you always execute** notebooks, scripts, and apps. After runs, `.agents/tools/nb_summary.py` lets the agent inspect executed outputs without reading `.env*` or raw `data/`.
- **Pragmatic [Cookiecutter Data Science](https://cookiecutter-data-science.drivendata.org/) Folder Structure:** Preserves CCDS's proven separation of immutable, git-ignored `data/` and `models/`, `notebooks/`, `docs/reports/`, `docs/figures/`, and `tests/`, while flattening deeply nested `src/<pkg>/...` boilerplate into plain `scripts/` (reusable modules and pipelines), thin `apps/` (dashboards/APIs), and `specs/`—linked end-to-end by sequential `<NN-name>` prefixes (`01-sales-eda`, `02-baseline`).
- **Agent- and Git-Friendly Notebooks ([Jupytext](https://jupytext.readthedocs.io/) + [nbstripout](https://github.com/kynan/nbstripout) + [uv](https://docs.astral.sh/uv/)):** Raw `.ipynb` JSON causes base64 diff bloat, merge conflicts, and fragile LLM edits. Instead, agents edit flat Python percent files in `notebooks/py/<NN-name>.py`—formatted, checked, and synced to `notebooks/<NN-name>.ipynb` via `check_notebook.py`. Both are tracked in Git: `nbstripout` strips outputs on commit/diff while keeping your executed outputs on disk for `nb_summary.py`. Dependencies live in `pyproject.toml` (managed via `uv`), and Cell 1 carries `# # %pip install -q ...` (commented in `.ipynb`) so local runs stay fast while shared `.ipynb` files remain runnable standalone.
- **Empirical Spec-Driven Workflow ([OpenSpec](https://github.com/Fission-AI/OpenSpec) + [Superpowers](https://github.com/obra/superpowers)):** Pure software SDD frameworks assume deterministic requirements and upfront unit tests, which misfires on empirical data exploration. `spec` combines the best of both:
  - *From OpenSpec:* Concise initiative contracts (`specs/<NN-name>.md`: `draft → approved → executed`) paired with a living project truth snapshot (`specs/context.md`) updated via `[ADD]`/`[MODIFY]`/`[REMOVE]` **Context Deltas**, plus **Fast-Forward** updates on unambiguous tweaks (spec goes straight to `approved`, then the agent stops and you trigger `code`).
  - *From Superpowers:* Socratic brainstorming before drafting open scope, clean **draft-vs-approval separation** (scoping answers and draft edits keep `Status: draft` until confirmed, while follow-up comparisons extend the active initiative in place), proportional task breakdowns, and **data-contract / invariant gates** (`assert` checks on table grain, joins, and split leakage plus synthetic `pytest` suites) as DS/DE's equivalent of TDD—while keeping open-ended EDA without artificial metrics first-class.
- **Cross-Agent Lifecycle Hooks:** Shared `.agents/hooks/` run across **Google Antigravity** (`.agents/hooks.json`), **Claude Code** (`.claude/settings.json`), and **Cursor** (which imports `.claude/settings.json` and `.agents/skills/`).

---

## Starting a New Project from This Template

**Prerequisite:** Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it yet (no pre-installed Python needed):

- **macOS / Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`)
- **Windows (PowerShell):** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` *(run `git config --global core.symlinks true` before cloning so `.claude/skills` stays symlinked)*

```bash
# 1. Clone into your new project folder with a fresh Git history
git clone <template-repo-url> my-ds-project && cd my-ds-project
rm -rf .git && git init

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
specs/                        <NN-name>.md (draft → approved → executed) & optional living context.md
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
data/                         local datasets, run logs, and outputs (git-ignored)
```

---

## Workflow & Skills

Skills live in `.agents/skills/` (linked at `.claude/skills`); full agent rules and handoff boundaries are in [AGENTS.md](AGENTS.md).

| Stage | Skill | Deliverable | Execution Owner |
|---|---|---|:---:|
| **1. Research** *(optional)* | `research` | `docs/research/<name>.md` | Agent |
| **2. Spec** | `spec` | `specs/<NN-name>.md` (`+ specs/context.md`) | Collaborative |
| **3. Code** | `code` | `notebooks/py/<NN-name>.py` $\leftrightarrow$ `.ipynb`, `scripts/`, `apps/`, `tests/` | Agent |
| **4. Run** | *User executes* | Outputs in `notebooks/`, `models/`, `data/`, or terminal | **User (Always)** |
| **5. Report** | `report` | `docs/reports/<NN-name>.md` (`.docx` on request) | Agent |
| **6. Presentation** | `presentation` | `docs/presentations/<name>/<name>.pptx` | Collaborative & Agent |

---

## Lifecycle Hooks & Permissions

- **`lint.py` (`PostToolUse`):** Runs `check_notebook.py` on `notebooks/py/*.py` edits (`ruff format`, `ruff check`, line/function/class budgets, `# # %pip` + `importlib.metadata` package checks, `ROOT`-anchored path checks, `.ipynb` sync) and `ruff format` + `ruff check` on all other `.py` edits.
- **`stop_tests.py` (`Stop`):** Catches unresolved Python/notebook lint issues on `Stop` in Antigravity (where `PostToolUse` does not feed errors back to the model) and runs `pytest -x -q` before finishing when Python files under `scripts/`, `apps/`, `tests/` or `.agents/{hooks,tools,skills}/` changed.
- **`session_start.py` (`SessionStart`):** Injects active Git branch, spec statuses, living `specs/context.md` presence, and next `NN-` prefix, installs the `nbstripout` Git filter, and warns if workspace tooling is missing.
- **Permissions (`.claude/settings.json`):** Keeps shell execution lean for Auto Mode (no brittle command lists) while denying reads of `.env*` and `~/.ssh/**` and direct reads/edits of `notebooks/*.ipynb`.
