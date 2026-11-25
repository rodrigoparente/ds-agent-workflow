# Evidence

Does the workflow actually work? This folder runs it end to end on three public datasets with a
**real model and a scripted user**, and logs everything so you can inspect what happened.

Nothing here is simulated except the human: the prompts and replies are fixed in files, the agent
is a real `claude` run, and the runner does the "Run (User)" step (`uv sync`, execute notebooks,
`pytest`) so the agent still never executes project code.

## Scenarios

Same six stages for each, different data and deployment:

| Scenario | Task | Deployment |
|---|---|---|
| `adult-income` | Binary classification, mixed tabular features | FastAPI |
| `california-housing` | Regression, numeric features | Streamlit |
| `newsgroups-topics` | Multiclass text classification | FastAPI |

Stages (`stages.toml`): **problem** (spec only) → **data** → **eda** → **modeling** →
**deployment** (`apps/` + `scripts/` + tests) → **communicate** (report, then slide deck).
Prompts are plain language with no skill names, so routing to the right skill is part of the test.

## How a run works

```
runner copies the template to a throwaway workspace (git init, uv sync)
for each stage:
    fresh `claude -p` session  <- stage prompt          (state lives only in specs/ and context.md)
    same session (--resume)    <- scripted replies      ("approved", "use your recommended option")
    runner does the human step: uv sync, execute the notebooks the agent changed, pytest
    if something fails: the runner reports the error back, up to 2 times (like a user would)
final checks, then the evidence bundle is written to runs/<scenario>/<date>-<model>/
```

Each stage starts a new session on purpose: if the specs and `context.md` are good, the next
stage can pick up from them. If a stage only works because of chat history, this will show it.

## Run it

You need the `claude` CLI (logged in), `uv`, `git` and internet access (datasets and packages).
`soffice` is optional (the deck skill uses it for its self-check).

```bash
uv run python evidence/run.py adult-income --dry-run              # print the user turns, no model
uv run python evidence/run.py adult-income --model sonnet --max-budget-usd 5
uv run python evidence/run.py adult-income --only problem data    # a few stages
uv run python evidence/run.py adult-income --workspace /tmp/evidence-adult-income-xxxx --only eda
```

Start with one scenario and a budget cap. The summary logs the cost per stage, so you will see
what a full run costs before you run all three.

- **Permissions:** the default is `--permission-mode auto`, matching the repo's settings. If your
  plan or CLI version does not support it in headless mode, use `--permission-mode
  bypassPermissions`, and only inside a container or VM: the agent then runs shell commands
  without asking.
- **The workspace is a temp copy** (printed at start, kept for inspection). `evidence/` itself is
  excluded from it, so the agent never sees the prompts, the checks or earlier runs.
- Run the runner's own tests with `uv run pytest evidence/test_run.py`.

## What you get

`runs/<scenario>/<date>-<model>/`:

| File | What it is |
|---|---|
| `SUMMARY.md` | Table per stage (turns, fix rounds, cost, time, missing artifacts), final checks |
| `results.json` | Same data, machine-readable (model, CLI version, template commit, date) |
| `transcript.md` | Every user turn, the agent's tool use and shell commands, and its answers |
| `workspace/` | The produced specs, notebooks (`.py` + text summary of the executed outputs), `scripts/`, `apps/`, `tests/`, `docs/` (reports, figures, deck) |
| `raw/` | Full stream-json logs (git-ignored; may contain data samples) |

Commit everything except `raw/`.

### Mechanical checks (automatic)

- Expected artifacts exist after each stage (specs, notebooks, figures, model, app, tests, report, `.pptx`).
- Notebooks execute cleanly, pass `check_notebook.py`, `ruff` and `pytest` pass.
- **Ran code** column: shell commands where the agent executed notebooks, scripts or apps itself.
  It should be `0`. **Guard** counts commands blocked by the Bash guard hook.
- Spec statuses at the end (informational).

### Human review (5 minutes per run)

The checks say it finished, not that the work is good. Read the bundle and answer:

1. **Boundaries:** did each stage stop where it should (spec without code, no chaining)?
2. **Honesty:** does the framing spec invent goals the prompt did not give? Are assumptions flagged?
3. **Evaluation:** baseline compared fairly, a proper split, no leakage, test data untouched during model selection?
4. **Report:** pick 3 numbers and trace each to the notebook summary. Any unsupported claim?
5. **App:** do the tests check behavior, or only that it imports? Is the handler thin?
6. **Deck:** one idea per slide, informative titles, spoken-style notes?

## What this does and does not prove

It shows the workflow can take a project from problem to deck on three different problems, and
where it breaks. It does not prove it works for every project: a scripted user cannot react to
unexpected questions, and one run is one sample of a non-deterministic model. Run each scenario a
few times (and with more than one model) and report the pass rate, not the best run. When the
agent asks something the replies do not cover, "use your recommended option" is the answer it
gets; check the transcript for runs where that went badly.

## Add a scenario

Copy a file in `scenarios/`, change the values, and run it by name. It needs only a public
dataset with a simple download. Keep the placeholders in `stages.toml` intact.
