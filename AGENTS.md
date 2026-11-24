# Data Science Workflow & Agent Guidelines

## Workflow

Human-in-the-loop lifecycle: **Research (optional) → Spec → Code → Run (User) → Report → Presentation**. Detailed procedures live in `.agents/skills/`.

- **Spec first (proportional ceremony):** Keep specs (`specs/<NN-name>.md`: `draft → approved → executed`) and living context (`specs/context.md`) synced via `spec`. Wait for explicit approval on drafts before coding; fast-forward unambiguous tweaks in one turn. Exploratory work without formal metrics is first-class.
- **Start simple & stay transparent:** Build the simplest flat solution first using Python stdlib, pandas, numpy, and scikit-learn built-ins; isolate unconfirmed defaults in the spec.
- **Interactive, one step at a time:** Use your structured question tool (`ask_question` / `AskUserQuestion`, recommended option first) for open scope or trade-offs—not routine "what next?" prompts. Summarize concisely with file links and wait for the user.

## Repository Layout

```text
specs/
  ├── <NN-name>.md            initiative specs (draft → approved → executed)
  └── context.md              living project truth snapshot (optional)
notebooks/
  ├── <NN-name>.ipynb         user-executed notebook (outputs stripped in Git via nbstripout)
  └── py/<NN-name>.py         notebook source edited by agent (synced via check_notebook.py)
models/                       serialized models & artifacts (git-ignored)
apps/                         interactive apps, dashboards, and APIs
scripts/                      standalone scripts, pipelines, and shared modules
tests/test_<name>.py          unit and integration tests
docs/
  ├── reports/<NN-name>.md    verified findings report (+ .docx on request)
  ├── presentations/<name>/   executive deck: slides.json, <name>.pptx, optional .pdf
  ├── research/<name>.md      optional literature & concept briefs
  └── figures/<NN-name>_*.png saved charts and visualizations
data/                         local datasets, run logs, & outputs (git-ignored)
```

- **Naming:** Sequential two-digit prefixes (`01-sales-eda`, `02-baseline`) across `specs/`, `notebooks/`, `docs/reports/`, and `docs/figures/`; user-chosen `<name>` for `scripts/`, `apps/`, `docs/research/`, and `docs/presentations/`.

## Agent Boundaries

- **You generate, the user runs:** Never execute generated code in `notebooks/`, `scripts/`, or `apps/` unless explicitly asked. Hand off with the exact `uv run ...` command (prefixed with `uv sync && ` if unsynced dependencies were added).
- **Allowed commands:** Lightweight schema/log/sample inspection, quick probes (`python3 -c`), `uv run [--no-sync] pytest`, `uv run [--no-sync] ruff`, `.agents/` helper scripts (`check_notebook.py`, `nb_summary.py`, skill scripts), `soffice`/`pdftoppm` for slide previews, and read-only shell/git commands.
- **Data & secrets:** Never read `.env*` or `~/.ssh`. In `data/`, inspect schemas, logs, and small samples rather than dumping raw files into context.
- **Notebooks:** Never open or edit `notebooks/*.ipynb` directly—edit `notebooks/py/<NN-name>.py` (synced via `python3 .agents/tools/check_notebook.py`) and inspect outputs via `python3 .agents/tools/nb_summary.py notebooks/<NN-name>.ipynb`.
- **Confirm first:** Ask before destructive git/filesystem commands (`rm -rf`, `git push --force`, `git reset --hard`) or environment/lockfile changes (`uv add`, `uv remove`, `uv sync`) unless explicitly requested.
