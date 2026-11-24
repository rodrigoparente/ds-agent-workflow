# Data Science Workflow & Agent Guidelines

## Workflow

Human-in-the-loop lifecycle: **Research (optional) → Spec → Code → Run (User) → Report → Presentation** (`.agents/skills/`):

- **Route by intent:** Conceptual, method, or literature understanding uses `research` (`docs/research/<name>.md`); empirical data exploration, experiments, pipelines, scripts, and apps go through `spec` → `code`; post-run write-ups use `report`; slide decks use `presentation`.
- **Spec first & iterate in place:** Keep specs (`specs/<NN-name>.md`: `draft`, `approved`, `executed`) and living context (`specs/context.md`) synced via `spec`. Extend the active `<NN-name>` initiative in place (even after execution) when adding or comparing models, features, metrics, or fixes on the same setup; start `<(NN+1)-name>` only when the goal, dataset/design, or deliverable shifts. Pause for plain-text approval on `draft` specs; fast-forward clear, unambiguous follow-ups on an existing spec straight to `code` in one turn.
- **Start simple & stay transparent:** Build the simplest flat solution first using Python stdlib, pandas, numpy, and scikit-learn built-ins; isolate unconfirmed defaults in the spec.
- **Natural interaction:** Use your structured question tool (`ask_question` / `AskUserQuestion`, recommended option first) only to clarify genuine open choices or missing scope—never for yes/no confirmations, approvals, or "what next?" prompts (handle those in plain text). Answering clarifying questions shapes a draft; wait for confirmation of the written draft before coding.

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
