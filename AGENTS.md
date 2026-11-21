# Data Science Workflow & Agent Guidelines

Human-in-the-loop lifecycle: **Research (optional) → Spec → Code → Run (User) → Report → Presentation**. Skills live in `.agents/skills/` and trigger from natural prompts.

- **Spec first (even on edits):** Start every initiative and follow-up change by updating `specs/<NN-name>.md` (`draft → approved → executed`) via `experiment-spec` before editing code. EDA, pipelines, and prototypes without formal metrics are first-class.
- **Start simple & stay transparent:** Build the simplest working solution first; document any unconfirmed metric, filter, or default in the spec.
- **Interactive, one step at a time:** Use `ask_question` / `AskUserQuestion` (recommended option first) for brainstorming, ambiguous requirements, or trade-offs—not for routine "what next?" prompts. Complete the requested step, summarize concisely with file links, and wait for the user.

## Repository Layout

```text
specs/<NN-name>.md            authoritative specs (experiment-spec)
notebooks/
  ├── <NN-name>.ipynb         user-executed notebook (outputs stripped in Git via nbstripout)
  └── py/<NN-name>.py         notebook source edited by agent (auto-synced via Jupytext)
models/                       serialized models & artifacts (git-ignored)
apps/                         interactive apps, dashboards, and APIs
scripts/                      standalone scripts, pipelines, and shared modules
tests/test_<name>.py          unit and integration tests
docs/
  ├── reports/<NN-name>.md    verified findings report (+ .docx on request; experiment-report)
  ├── presentations/<name>/   executive deck: slides.json, <name>.pptx, optional .pdf (presentation)
  ├── research/<name>.md      optional literature & concept briefs (research)
  └── figures/<NN-name>_*.png saved charts and visualizations
data/                         cached local datasets (<NN-name>.parquet, git-ignored)
```

- **Naming:** Experiment initiatives use a two-digit kebab-case prefix (`01-sales-eda`, `02-baseline`) across `specs/`, `notebooks/`, `docs/reports/`, and `docs/figures/`. Standalone `docs/research/<name>.md` and `docs/presentations/<name>/` use user-chosen names.
- **Notebooks:** Edit only `notebooks/py/<NN-name>.py` (`check_notebook.py` syncs `.ipynb`). Cell 1 lists third-party packages via `# # %pip install -q ...` (stays commented in `.ipynb` locally; recipients uncomment to run standalone).

## Code Standards

1. Only implement what the approved spec requires.
2. Reuse existing code from `scripts/` or earlier initiatives where applicable.
3. Prefer Python stdlib, pandas, numpy, and scikit-learn built-ins over custom functions.
4. Keep code flat and readable: avoid single-use functions, classes, config objects, and defensive wrappers.
5. Keep essential data-integrity checks (shapes, types, split leak prevention, random seeds).

## Agent Boundaries

- **You generate, the user runs.** Never run generated code in `notebooks/`, `scripts/`, or `apps/` unless explicitly asked. Hand off with the exact command to run inside `.venv` (`jupyter lab`, `python scripts/<name>.py`, or `<app-command>`).
- **Allowed commands:** Quick synthetic-data probes (`python3 -c`, a few seconds), `pytest`, `ruff`, `.agents/tools/*`, `.agents/skills/research/scripts/papers.py`, `.agents/skills/presentation/scripts/deck.py` (plus `soffice`/`pdftoppm` for slide previews), and read-only shell commands.
- **Never read** `data/` (consult `data-catalog` instead), `.env*`, or `~/.ssh`.
- **Never open or edit `notebooks/*.ipynb`.** Edit `notebooks/py/<NN-name>.py` and inspect run outputs via `nb_summary.py`.
- **Confirm first** before destructive or irreversible actions (`rm -rf`, `git push --force`, `git reset --hard`, `pip install/uninstall`) unless explicitly asked.

## Helper Commands

- **Check & sync notebook (no execution):** `python3 .agents/tools/check_notebook.py notebooks/py/<NN-name>.py`
- **Read executed notebook outputs:** `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`
- **Export report to `.docx`:** `.venv/bin/python .agents/tools/export_docx.py docs/reports/<NN-name>.md`
- **Build slide deck:** `.venv/bin/python .agents/skills/presentation/scripts/deck.py docs/presentations/<name>/slides.json`
- **Search academic papers:** `python3 .agents/skills/research/scripts/papers.py search "query"`
