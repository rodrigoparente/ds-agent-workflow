# Data Science Workflow & Agent Guidelines

## Workflow

Human-in-the-loop lifecycle: **Research (optional) → Spec → Code → Run (User) → Report → Presentation**. Skills live in `.agents/skills/` and trigger from natural prompts.

- **Spec first (proportional ceremony):** Keep specs and code in sync via `spec` (`specs/<NN-name>.md` + living `specs/context.md`). New or ambiguous scope starts at `Status: draft` and waits for explicit user approval (`Status: approved`) before coding (answering clarifying questions or requesting edits refines the draft). Clear, unambiguous tweaks on an existing spec—or explicit fast-forward requests—update the spec and code in one turn. Exploratory work, pipelines, and prototypes without formal metrics are first-class.
- **Start simple & stay transparent:** Build the simplest working solution first; document any unconfirmed metric, filter, or default in the spec.
- **Interactive, one step at a time:** Use `ask_question` / `AskUserQuestion` (recommended option first) for brainstorming, ambiguous requirements, or trade-offs—not for routine "what next?" prompts. Complete the requested step, summarize concisely with file links, and wait for the user.

## Repository Layout

```text
specs/
  ├── <NN-name>.md            initiative specs (draft → approved → executed; spec)
  └── context.md              living project truth synced as work executes (optional)
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
data/                         local datasets, run logs, & outputs (git-ignored)
```

- **Naming:** Experiment initiatives use a two-digit kebab-case prefix (`01-sales-eda`, `02-baseline`) across `specs/`, `notebooks/`, `docs/reports/`, and `docs/figures/`. Standalone `docs/research/<name>.md` and `docs/presentations/<name>/` use user-chosen names.
- **Notebooks:** `check_notebook.py` syncs `notebooks/py/<NN-name>.py` to `.ipynb`. Cell 1 lists third-party packages via `# # %pip install -q ...` (stays commented in `.ipynb` locally so it never conflicts with `uv`; standalone recipients uncomment it).

## Code Standards

1. Only implement what the approved spec requires.
2. Reuse existing code from `scripts/` or earlier initiatives where applicable.
3. Prefer Python stdlib, pandas, numpy, and scikit-learn built-ins over custom functions.
4. Keep code flat and readable: avoid single-use functions, classes, config objects, and defensive wrappers.
5. Enforce verification checks from the spec (invariants/assertions, split/schema checks, random seeds, or unit tests).

## Agent Boundaries

- **You generate, the user runs.** Never run generated code in `notebooks/`, `scripts/`, or `apps/` unless explicitly asked. Hand off with the exact `uv` command (`uv run jupyter lab`, `uv run python scripts/<name>.py`, or `uv run <app-command>`, preceded by `uv sync` if dependencies changed).
- **Allowed commands:** Lightweight schema/log/sample inspection, quick probes (`python3 -c`, a few seconds), `uv run pytest`, `uv run ruff`, the helper commands below (plus `soffice`/`pdftoppm` for slide previews), and read-only shell commands.
- **Never read** `.env*` or `~/.ssh`. In `data/`, inspect schemas, logs, summaries, and small samples rather than dumping large raw files whole into context.
- **Never open or edit `notebooks/*.ipynb`.** Edit `notebooks/py/<NN-name>.py` and inspect run outputs via `nb_summary.py`.
- **Confirm first** before destructive or irreversible actions (`rm -rf`, `git push --force`, `git reset --hard`, `uv add/remove/sync`) unless explicitly asked.

## Helper Commands

- **Check & sync notebook (no execution):** `python3 .agents/tools/check_notebook.py notebooks/py/<NN-name>.py`
- **Read executed notebook outputs:** `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`
- **Export report to `.docx`:** `uv run python .agents/tools/export_docx.py docs/reports/<NN-name>.md`
- **Build slide deck:** `uv run python .agents/skills/presentation/scripts/deck.py docs/presentations/<name>/slides.json`
- **Search academic papers:** `python3 .agents/skills/research/scripts/papers.py search "query"`
