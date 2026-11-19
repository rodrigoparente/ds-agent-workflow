# Data Science AI Workflow Starter Pack (`ds-starter-pack`)

A lightweight, human-in-the-loop template for Data Science, ML, and AI projects paired with AI coding assistants (Google Antigravity, Claude Code, Cursor).

$$\textbf{Research} \longrightarrow \textbf{Spec} \longrightarrow \textbf{Code} \longrightarrow \textbf{Run (User)} \longrightarrow \textbf{Report} \longrightarrow \textbf{Slides}$$

---

## Key Design Choices

- **Human-in-the-Loop Execution:** The agent collaborates on specs, writes and lints code, runs unit tests, and summarizes results—but **you always run code** in Jupyter Lab or your terminal.
- **Spec-First Workflow ([OpenSpec](https://github.com/Fission-AI/OpenSpec)-inspired):** Every initiative starts with a lightweight agreement in `specs/<NN-name>.md` (`draft → approved → executed`). Follow-up changes update the spec first so documentation and code never drift.
- **Agent and Git-Friendly Notebooks ([Jupytext](https://jupytext.readthedocs.io/) + [nbstripout](https://github.com/kynan/nbstripout)):** The agent edits clean, flat Python files in `notebooks/py/<NN-name>.py`, which automatically sync to `notebooks/<NN-name>.ipynb`. Both are tracked in Git: `nbstripout` automatically strips heavy cell outputs on `git commit` / `git diff` while preserving your local executed outputs on disk so `.agents/tools/nb_summary.py` can read them.
- **Cross-Agent Guardrails & Hooks:** Shared lifecycle hooks in `.agents/hooks/` run across **Google Antigravity** (`.agents/hooks.json`), **Claude Code** (`.claude/settings.json`), and **Cursor** (which natively imports `.claude/settings.json` and `.agents/skills/`).
- **Pragmatic Layout ([Cookiecutter Data Science](https://cookiecutter-data-science.drivendata.org/)-inspired):** Sequentially numbered initiatives (`01-`, `02-`) across a flat folder structure without heavy boilerplate packages. Workspace tooling is managed by [uv](https://docs.astral.sh/uv/), while each notebook declares its own libraries via `# %pip install`.

---

## Starting a New Project from This Template

```bash
# 1. Clone into your new project folder with a fresh Git history
git clone <template-repo-url> my-ds-project && cd my-ds-project
rm -rf .git && git init

# 2. Install workspace tooling (JupyterLab, Jupytext, nbstripout, Ruff, Pytest, python-pptx)
uv sync

# 3. Activate the nbstripout Git filter (also runs automatically on agent SessionStart)
uv run nbstripout --install

# 4. Launch Jupyter Lab to run notebooks interactively
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
  ├── <NN-name>.ipynb         executed notebook (tracked in Git; outputs stripped via nbstripout)
  └── py/<NN-name>.py         notebook source of truth (flat, clean, edited by agent)
models/                       serialized models and artifacts (git-ignored)
apps/                         interactive apps, dashboards, and API services
scripts/                      standalone scripts, pipelines, shared modules, deck builders
tests/                        test_<name>.py (unit and integration tests)
docs/
  ├── reports/<NN-name>.md    verified findings report (+ .docx on request)
  ├── slides/<NN-name>.md     executive slide outline and deck (.pptx)
  ├── research/<topic>.md     optional literature & benchmark briefs
  └── figures/<NN-name>_*.png saved charts and visualizations
data/                         cached local datasets (<NN-name>.parquet, git-ignored)
```

---

## Workflow & Skills

Skills live in `.agents/skills/` (linked at `.claude/skills`) and follow the rules in [AGENTS.md](AGENTS.md):

| Stage | Skill | Deliverable | Execution Owner |
|---|---|---|:---:|
| **1. Research** *(optional)* | `researcher` | `docs/research/<topic>.md` | Agent |
| **2. Spec** | `experiment-spec` | `specs/<NN-name>.md` | Collaborative |
| **3. Data Reference** | `data-catalog` | Lake table schemas & loading recipes | Reference |
| **4. Code** | `write-code` | `notebooks/py/<NN-name>.py` $\leftrightarrow$ `.ipynb`, `scripts/`, `apps/`, `tests/` | Agent |
| **5. Run** | *User executes* | Outputs in `notebooks/`, `models/`, `data/`, or terminal | **User (Always)** |
| **6. Report** | `experiment-report` | `docs/reports/<NN-name>.md` (`.docx` on request) | Agent |
| **7. Presentation** | `make-presentation` | `docs/slides/<NN-name>.md` $\to$ `docs/slides/<NN-name>.pptx` | Collaborative & Agent |

---

## Built-in Helper Tools & Lifecycle Hooks

### Helper Tools (`.agents/tools/`)
- **Format, lint & sync notebook:** `uv run python .agents/tools/check_notebook.py notebooks/py/<NN-name>.py`
- **Inspect executed notebook outputs:** `uv run python .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`
- **Export report to Word (`.docx`):** `uv sync --group docs && uv run python .agents/tools/export_docx.py docs/reports/<NN-name>.md`

### Automated Lifecycle Hooks (`.agents/hooks/`)
- **`guard.py` (`PreToolUse`):** Enforces the experiment execution ban, blocks direct reads/edits of `notebooks/*.ipynb`, protects raw `data/` (PII) and `.env` / `~/.ssh` secrets, blocks raw `pip install`, and prevents destructive git/shell commands.
- **`lint.py` (`PostToolUse`):** Automatically runs `check_notebook.py` when `notebooks/py/*.py` is edited, and runs `ruff format` + `ruff check` on any other edited `.py` file.
- **`stop_tests.py` (`Stop`):** Runs `uv run pytest -x -q` before the agent finishes a turn whenever Python files were modified and unit tests exist in `tests/`.
- **`session_start.py` (`SessionStart`):** Injects a compact 2-line summary of the active Git branch, existing specs (`draft` / `approved` / `executed`), and next sequential initiative number (`NN`), and ensures the `nbstripout` Git filter is installed.

### Customizing Permissions & Guardrails
To add project- or company-specific credential paths or blocked CLI tools:
1. **Claude Code permissions:** Edit the `allow`, `ask`, and `deny` arrays in [`.claude/settings.json`](.claude/settings.json).
2. **Cross-agent shell/file guard:** Edit `SAFE_SEGMENT_PATTERNS`, `FORBIDDEN_RUNTIMES`, or `check_file_path()` in [`.agents/hooks/guard.py`](.agents/hooks/guard.py) and verify with `uv run pytest .agents/hooks/test_hooks.py`.
