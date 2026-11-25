#!/usr/bin/env python3
"""Run one evidence scenario end to end with a scripted "user" and log what happened.

The runner plays the human. It sends the stage prompts and scripted replies to a headless agent
(`claude -p`), then does the "Run (User)" step itself (uv sync, execute notebooks, pytest), so the
agent never executes project code. Everything is logged to evidence/runs/<scenario>/<run>/.

Usage:
    uv run python evidence/run.py adult-income --model sonnet
    uv run python evidence/run.py adult-income --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
# Shell commands that execute project code. The agent must hand these off to the user.
RUNS_CODE = re.compile(
    r"(?:python3?|uv run(?: --no-sync)?)\s+(?:\./)?(?:scripts|apps|notebooks)/"
    r"|\buvicorn\b|streamlit run|nbconvert|jupyter\s+execute"
)
SKIP = shutil.ignore_patterns(
    ".git", ".venv", "evidence", "data", "models", "__pycache__", ".ruff_cache", ".pytest_cache"
)
MAX_FIX_ROUNDS = 2  # how many times the "user" reports a failed run back to the agent
STATUS = re.compile(r"status:\s*(draft|approved|executed)", re.I)


# ---------- helpers ----------


def sh(cmd: list[str], cwd: Path, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def tail(text: str, n: int = 25) -> str:
    return "\n".join(ANSI.sub("", text).strip().splitlines()[-n:])


def load(scenario: str) -> tuple[dict, list[dict]]:
    path = Path(scenario)
    if not path.is_file():
        path = HERE / "scenarios" / f"{scenario}.toml"
    with path.open("rb") as f:
        variables = tomllib.load(f)
    with (HERE / "stages.toml").open("rb") as f:
        stages = tomllib.load(f)["stages"]
    return variables, stages


def render(stage: dict, variables: dict) -> list[str]:
    """The user turns of a stage: the prompt, then the scripted replies."""
    return [t.format_map(variables) for t in [stage["prompt"], *stage.get("replies", [])]]


# ---------- talking to the agent ----------


def _events(stdout: str):
    for line in ANSI.sub("", stdout).splitlines():
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _tally(summary: dict, block: dict) -> None:
    if block.get("type") == "tool_use":
        summary["tools"].append({"name": block.get("name"), "input": block.get("input", {})})
    elif block.get("type") == "tool_result" and "Blocked:" in str(block.get("content")):
        summary["blocked"] += 1


def summarize(stdout: str) -> dict:
    """Condense a `--output-format stream-json` run into what we want to log."""
    s = {"session_id": None, "text": "", "is_error": False, "cost_usd": 0.0, "tools": []}
    s["blocked"] = 0
    for ev in _events(stdout):
        s["session_id"] = ev.get("session_id") or s["session_id"]
        if ev.get("type") == "result":
            s["text"] = ev.get("result", "")
            s["is_error"] = bool(ev.get("is_error"))
            s["cost_usd"] = ev.get("total_cost_usd") or 0.0
        content = ev.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            _tally(s, block)
    return s


def violations(tools: list[dict]) -> list[str]:
    """Bash commands in which the agent ran project code instead of handing it off."""
    cmds = [t["input"].get("command", "") for t in tools if t["name"] == "Bash"]
    return [c for c in cmds if RUNS_CODE.search(c)]


def ask(ws: Path, text: str, sid: str | None, opts: argparse.Namespace, raw: Path) -> dict:
    cmd = ["claude", "-p", text, "--output-format", "stream-json", "--verbose"]
    cmd += ["--permission-mode", opts.permission_mode, "--max-turns", str(opts.max_turns)]
    if opts.model:
        cmd += ["--model", opts.model]
    if opts.max_budget_usd:
        cmd += ["--max-budget-usd", str(opts.max_budget_usd)]
    if sid:
        cmd += ["--resume", sid]
    try:
        p = sh(cmd, ws, timeout=opts.timeout)
    except subprocess.TimeoutExpired:
        return {**summarize(""), "is_error": True, "text": f"timeout after {opts.timeout}s"}
    raw.write_text(p.stdout)
    s = summarize(p.stdout)
    if p.returncode and not s["text"]:
        s.update(is_error=True, text=f"claude exited {p.returncode}: {tail(p.stderr, 5)}")
    return s


def one_turn(ws: Path, text: str, sid: str | None, opts: argparse.Namespace, raw: Path) -> dict:
    turn = ask(ws, text, sid, opts, raw)
    turn["user"] = text
    turn["violations"] = violations(turn["tools"])
    return turn


# ---------- the "Run (User)" step ----------


def run_notebooks(ws: Path, since: float) -> list[str]:
    problems = []
    for nb in sorted((ws / "notebooks").glob("*.ipynb")):
        if nb.stat().st_mtime < since:
            continue
        cmd = ["uv", "run", "--no-sync", "jupyter", "nbconvert", "--to", "notebook", "--execute"]
        r = sh([*cmd, "--inplace", "--ExecutePreprocessor.timeout=1800", str(nb)], ws)
        if r.returncode:
            problems.append(f"Running notebooks/{nb.name} failed:\n{tail(r.stderr)}")
    return problems


def verify(ws: Path, stage: dict, since: float) -> list[str]:
    """What a human does after the agent hands off. Returns the problems they would report."""
    if not (stage.get("execute") or stage.get("pytest")):
        return []
    sh(["uv", "sync", "-q"], ws)
    problems = run_notebooks(ws, since) if stage.get("execute") else []
    if stage.get("pytest"):
        r = sh(["uv", "run", "--no-sync", "pytest", "-x", "-q"], ws)
        if r.returncode:
            problems.append(f"pytest failed:\n{tail(r.stdout + r.stderr)}")
    return problems


def run_stage(ws: Path, stage: dict, variables: dict, opts, raw_dir: Path) -> tuple[dict, list]:
    t0 = time.time()
    turns: list[dict] = []
    sid = None
    for i, text in enumerate(render(stage, variables)):
        turns.append(one_turn(ws, text, sid, opts, raw_dir / f"{stage['id']}-{i}.jsonl"))
        sid = turns[-1]["session_id"] or sid
    problems, rounds = verify(ws, stage, t0), 0
    while problems and rounds < MAX_FIX_ROUNDS:
        rounds += 1
        msg = "I ran it and hit problems. Please fix them:\n\n" + "\n\n".join(problems)
        raw = raw_dir / f"{stage['id']}-fix{rounds}.jsonl"
        turns.append(one_turn(ws, msg, sid, opts, raw))
        sid = turns[-1]["session_id"] or sid
        problems = verify(ws, stage, t0)
    record = {
        "id": stage["id"],
        "turns": len(turns),
        "fix_rounds": rounds,
        "cost_usd": round(sum(t["cost_usd"] for t in turns), 4),
        "duration_s": round(time.time() - t0),
        "agent_errors": [t["text"] for t in turns if t["is_error"]],
        "unresolved_problems": problems,
        "missing": [g for g in stage.get("expect", []) if not list(ws.glob(g))],
        "ran_code": [c for t in turns for c in t["violations"]],
        "blocked_by_guard": sum(t["blocked"] for t in turns),
    }
    return record, turns


# ---------- final checks ----------


def notebooks_not_executed(ws: Path) -> list[str]:
    bad = []
    for nb in sorted((ws / "notebooks").glob("*.ipynb")):
        cells = json.loads(nb.read_text())["cells"]
        code = [c for c in cells if c["cell_type"] == "code" and "".join(c["source"]).strip()]
        errors = any(o.get("output_type") == "error" for c in code for o in c.get("outputs", []))
        if errors or any(c.get("execution_count") is None for c in code):
            bad.append(nb.name)
    return bad


def spec_statuses(ws: Path) -> dict[str, str]:
    out = {}
    for spec in sorted((ws / "specs").glob("*.md")):
        m = STATUS.search(spec.read_text()[:1500])
        out[spec.stem] = m.group(1).lower() if m else "unknown"
    return out


def final_checks(ws: Path) -> dict:
    nb_rules = [
        p.name
        for p in sorted((ws / "notebooks" / "py").glob("*.py"))
        if sh(["python3", ".agents/tools/check_notebook.py", str(p)], ws).returncode
    ]
    dirs = [d for d in ("scripts", "apps", "tests") if (ws / d).is_dir()]
    ruff = (
        sh(["uv", "run", "--no-sync", "ruff", "check", *dirs], ws).returncode == 0 if dirs else True
    )
    tests = sh(["uv", "run", "--no-sync", "pytest", "-q"], ws).returncode == 0
    checks = {
        "notebook_rule_failures": nb_rules,
        "notebooks_not_executed": notebooks_not_executed(ws),
        "ruff_ok": ruff,
        "pytest_ok": tests,
        "specs": spec_statuses(ws),
    }
    checks["passed"] = not (nb_rules or checks["notebooks_not_executed"]) and ruff and tests
    return checks


# ---------- logging ----------


def render_transcript(all_turns: list[tuple[str, dict]]) -> str:
    lines = ["# Transcript\n"]
    for stage_id, t in all_turns:
        lines += [f"## `{stage_id}`\n", f"**User:** {t['user']}\n"]
        counts = Counter(x["name"] for x in t["tools"])
        lines.append(f"**Agent tools:** {dict(counts) or 'none'}\n")
        cmds = [x["input"].get("command", "") for x in t["tools"] if x["name"] == "Bash"]
        lines += [f"- `{c[:110]}`" for c in cmds[:25]]
        lines.append(f"\n**Agent:** {t['text'][:1500]}\n")
    return "\n".join(lines)


def render_summary(record: dict) -> str:
    f = record["final"]
    rows = ["| Stage | Turns | Fix rounds | Cost (USD) | Time (s) | Missing | Ran code | Guard |"]
    rows.append("|---|---|---|---|---|---|---|---|")
    for s in record["stages"]:
        miss = ", ".join(s["missing"]) or "-"
        rows.append(
            f"| {s['id']} | {s['turns']} | {s['fix_rounds']} | {s['cost_usd']} | {s['duration_s']} "
            f"| {miss} | {len(s['ran_code'])} | {s['blocked_by_guard']} |"
        )
    head = [
        f"# {record['scenario']}: {'PASSED' if f['passed'] else 'FAILED'}",
        f"\nModel: {record['model']} · {record['claude_version']} · template {record['template']}"
        f" · {record['date']}\n",
    ]
    final = [
        "\n## Final checks\n",
        f"- Notebook rule failures: {f['notebook_rule_failures'] or 'none'}",
        f"- Notebooks not executed cleanly: {f['notebooks_not_executed'] or 'none'}",
        f"- ruff: {'ok' if f['ruff_ok'] else 'FAILED'}"
        f" · pytest: {'ok' if f['pytest_ok'] else 'FAILED'}",
        f"- Spec statuses: {f['specs']}",
        "\nMechanical checks only. Review the artifacts with the rubric in evidence/README.md.",
    ]
    return "\n".join([*head, *rows, *final]) + "\n"


def bundle(ws: Path, out: Path, record: dict, all_turns: list[tuple[str, dict]]) -> None:
    keep = shutil.ignore_patterns("__pycache__")
    (out / "workspace").mkdir(parents=True, exist_ok=True)
    for d in ("specs", "docs", "apps", "scripts", "tests", "notebooks/py"):
        if (ws / d).is_dir():
            shutil.copytree(ws / d, out / "workspace" / d, ignore=keep, dirs_exist_ok=True)
    shutil.copy(ws / "pyproject.toml", out / "workspace" / "pyproject.toml")
    for nb in sorted((ws / "notebooks").glob("*.ipynb")):
        text = sh(["python3", ".agents/tools/nb_summary.py", str(nb)], ws).stdout
        (out / "workspace" / "notebooks").mkdir(parents=True, exist_ok=True)
        (out / "workspace" / "notebooks" / f"{nb.stem}.summary.txt").write_text(text)
    (out / "results.json").write_text(json.dumps(record, indent=2))
    (out / "transcript.md").write_text(render_transcript(all_turns))
    (out / "SUMMARY.md").write_text(render_summary(record))


# ---------- main ----------


def new_workspace(name: str) -> Path:
    ws = Path(tempfile.mkdtemp(prefix=f"evidence-{name}-"))
    shutil.copytree(ROOT, ws, ignore=SKIP, symlinks=True, dirs_exist_ok=True)
    who = ["-c", "user.name=evidence", "-c", "user.email=evidence@local"]
    sh(["git", "init", "-q"], ws)
    sh(["git", "add", "-A"], ws)
    sh(["git", *who, "commit", "-qm", "baseline"], ws)
    sh(["uv", "sync", "-q"], ws)  # the human installs the tooling once, like the README says
    return ws


def meta(opts: argparse.Namespace, name: str) -> dict:
    version = sh(["claude", "--version"], ROOT).stdout.strip() if shutil.which("claude") else "n/a"
    commit = sh(["git", "rev-parse", "--short", "HEAD"], ROOT).stdout.strip() or "unknown"
    return {
        "scenario": name,
        "model": opts.model or "default",
        "claude_version": version,
        "template": commit,
        "permission_mode": opts.permission_mode,
        "date": datetime.now().isoformat(timespec="minutes"),
    }


def parse(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("scenario", help="name in evidence/scenarios/ or a path to a .toml")
    p.add_argument("--model", help="passed to `claude --model` (e.g. sonnet, opus)")
    p.add_argument("--only", nargs="+", metavar="STAGE", help="run only these stages")
    p.add_argument("--workspace", type=Path, help="reuse a workspace (to resume or run one stage)")
    p.add_argument("--permission-mode", default="auto", help="default: auto (see README)")
    p.add_argument("--max-turns", type=int, default=40, help="agent turns per call")
    p.add_argument("--max-budget-usd", type=float, help="spend cap per call")
    p.add_argument("--timeout", type=int, default=3600, help="seconds per call")
    p.add_argument("--runs-dir", type=Path, default=HERE / "runs")
    p.add_argument("--dry-run", action="store_true", help="print the user turns and exit")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    opts = parse(argv)
    variables, stages = load(opts.scenario)
    stages = [s for s in stages if not opts.only or s["id"] in opts.only]
    if opts.dry_run:
        for s in stages:
            print(f"\n== {s['id']} ==")
            print("\n---\n".join(render(s, variables)))
        return 0
    ws = opts.workspace or new_workspace(variables["name"])
    stamp = f"{datetime.now():%Y%m%d-%H%M}-{opts.model or 'default'}"
    out = opts.runs_dir / variables["name"] / stamp
    (out / "raw").mkdir(parents=True)
    print(f"workspace: {ws}\nlogging to: {out}")
    records, all_turns = [], []
    for stage in stages:
        print(f"-> {stage['id']}", flush=True)
        record, turns = run_stage(ws, stage, variables, opts, out / "raw")
        records.append(record)
        all_turns += [(stage["id"], t) for t in turns]
    record = {**meta(opts, variables["name"]), "stages": records, "final": final_checks(ws)}
    bundle(ws, out, record, all_turns)
    print(f"{'PASSED' if record['final']['passed'] else 'FAILED'}: {out / 'SUMMARY.md'}")
    return 0 if record["final"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
