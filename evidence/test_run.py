"""Tests for the evidence runner. Run: uv run pytest evidence/test_run.py"""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run  # noqa: E402

SCENARIOS = sorted(p.stem for p in (HERE / "scenarios").glob("*.toml"))


@pytest.mark.parametrize("name", SCENARIOS)
def test_every_scenario_renders_every_stage(name: str) -> None:
    variables, stages = run.load(name)
    assert [s["id"] for s in stages] == [
        "problem", "data", "eda", "modeling", "deployment", "communicate"
    ]  # fmt: skip
    for stage in stages:
        turns = run.render(stage, variables)
        assert len(turns) >= 2 and all(t.strip() for t in turns)
        assert stage["expect"]


def test_scenarios_cover_the_deployment_targets() -> None:
    apps = [run.load(n)[0]["app"].lower() for n in SCENARIOS]
    assert len(SCENARIOS) == 3
    assert any("fastapi" in a for a in apps) and any("streamlit" in a for a in apps)


def test_summarize_parses_stream_and_counts_tools_and_blocks() -> None:
    lines = [
        '\x1b[?1004l{"type":"system","subtype":"init","session_id":"s1"}',
        "not json",
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "hi"},
                        {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
                    ]
                },
            }
        ),
        json.dumps(
            {
                "type": "user",
                "message": {"content": [{"type": "tool_result", "content": "Blocked: no"}]},
            }
        ),
        json.dumps({"type": "user", "message": {"content": "plain string"}}),
        json.dumps({"type": "result", "result": "done", "total_cost_usd": 0.5, "session_id": "s1"}),
    ]
    s = run.summarize("\n".join(lines))
    assert (s["session_id"], s["text"], s["cost_usd"], s["blocked"]) == ("s1", "done", 0.5, 1)
    assert s["tools"] == [{"name": "Bash", "input": {"command": "ls"}}]


@pytest.mark.parametrize(
    ("command", "ran"),
    [
        ("uv run python scripts/train.py", True),
        ("uv run --no-sync python apps/main.py", True),
        ("uv run scripts/train.py", True),
        ("python3 notebooks/py/01-eda.py", True),
        ("uv run jupyter nbconvert --execute x.ipynb", True),
        ("uv run uvicorn apps.api:app", True),
        ("uv run --no-sync pytest -x -q", False),
        ("python3 -c 'print(1)'", False),
        ("python3 .agents/tools/check_notebook.py notebooks/py/01-eda.py", False),
        ("uv run python .agents/skills/presentation/scripts/deck.py x.json", False),
    ],
)
def test_violations_flag_only_agent_executed_project_code(command: str, ran: bool) -> None:
    tools = [{"name": "Bash", "input": {"command": command}}, {"name": "Read", "input": {}}]
    assert bool(run.violations(tools)) is ran


def test_tail_strips_ansi_and_keeps_the_last_lines() -> None:
    assert run.tail("a\n\x1b[31mb\x1b[39m\nc", 2) == "b\nc"


def test_notebook_and_spec_checks(tmp_path: Path) -> None:
    def nb(name: str, count: int | None, outputs: list) -> None:
        cell = {"cell_type": "code", "source": ["x = 1"], "execution_count": count}
        cell["outputs"] = outputs
        (tmp_path / "notebooks").mkdir(exist_ok=True)
        (tmp_path / "notebooks" / name).write_text(json.dumps({"cells": [cell]}))

    nb("ok.ipynb", 1, [])
    nb("unrun.ipynb", None, [])
    nb("error.ipynb", 2, [{"output_type": "error"}])
    assert run.notebooks_not_executed(tmp_path) == ["error.ipynb", "unrun.ipynb"]

    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "01-framing.md").write_text("# 01-framing\n\nStatus: executed\n")
    (tmp_path / "specs" / "02-data.md").write_text("# 02-data\n")
    assert run.spec_statuses(tmp_path) == {"01-framing": "executed", "02-data": "unknown"}


def _stub(path: Path, body: str) -> None:
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def test_end_to_end_with_stub_agent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Plumbing only: a fake `claude` and `uv`, no model."""
    bin_dir, log = tmp_path / "bin", tmp_path / "claude.log"
    bin_dir.mkdir()
    reply = (
        '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash",'
        '"input":{"command":"uv run python scripts/train.py"}}]},"session_id":"s1"}'
    )
    _stub(
        bin_dir / "claude",
        'echo "$@" >> "$STUB_LOG"\n'
        'echo \'{"type":"system","session_id":"s1"}\'\n'
        f"echo '{reply}'\n"
        'echo \'{"type":"result","result":"ok","total_cost_usd":0.01,"session_id":"s1"}\'\n',
    )
    _stub(bin_dir / "uv", "exit 0\n")
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("STUB_LOG", str(log))
    monkeypatch.setattr(run.tempfile, "tempdir", str(tmp_path))  # keep the workspace here

    runs = tmp_path / "runs"
    code = run.main(["adult-income", "--only", "problem", "data", "--runs-dir", str(runs)])

    calls = [ln for ln in log.read_text().splitlines() if ln.startswith("-p ")]
    assert len(calls) == 6  # 2 stages x (prompt + 2 replies)
    assert sum("--resume s1" in c for c in calls) == 4  # replies resume, prompts start fresh
    assert all("--output-format stream-json --verbose" in c for c in calls)
    (out,) = (runs / "adult-income").iterdir()
    record = json.loads((out / "results.json").read_text())
    assert [s["id"] for s in record["stages"]] == ["problem", "data"]
    assert record["stages"][0]["ran_code"]  # the stub "ran" a script: logged as a violation
    assert record["stages"][0]["missing"] == ["specs/*framing*.md"]
    assert (out / "SUMMARY.md").exists() and (out / "transcript.md").exists()
    assert code == 0
