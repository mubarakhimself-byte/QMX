# ruff: noqa: S101
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import p_resume
from common import Log, Provider
from p_resume import linked_home, recall_verdict


def test_linked_home_shares_projects_and_a_reset_keeps_the_plan_transcripts(
    tmp_path: Path,
) -> None:
    projects = tmp_path / "plan" / "projects"
    (projects / "D--Temp-qma-hp0").mkdir(parents=True)
    (projects / "D--Temp-qma-hp0" / "s1.jsonl").write_text("plan turn\n", encoding="utf-8")
    root = tmp_path / "relayed" / "claude"

    linked_home(root, projects)
    assert (root / "projects" / "D--Temp-qma-hp0" / "s1.jsonl").read_text(
        encoding="utf-8"
    ) == "plan turn\n"
    (root / "projects" / "D--Temp-qma-hp0" / "s1.jsonl").write_text(
        "plan turn\nopenrouter turn\n", encoding="utf-8"
    )
    (root / ".claude.json").write_text("{}", encoding="utf-8")

    linked_home(root, projects)
    assert sorted(p.name for p in root.iterdir()) == ["projects"]
    assert (projects / "D--Temp-qma-hp0" / "s1.jsonl").read_text(
        encoding="utf-8"
    ) == "plan turn\nopenrouter turn\n"


def test_recall_needs_the_codeword_in_the_answer() -> None:
    assert recall_verdict("persimmon-a1b2c3", "persimmon-a1b2c3") == "PASS"
    assert recall_verdict("I do not know", "persimmon-a1b2c3") == "FAIL"
    assert recall_verdict(None, "persimmon-a1b2c3") == "FAIL"


def test_no_openrouter_key_stops_before_any_plan_turn(tmp_path: Path) -> None:
    def no_key(_provider: Provider) -> None:
        return None

    def no_plan_turn(*_args: object) -> None:
        raise AssertionError("plan login checked without a key")

    with (
        patch.object(p_resume, "read_key", no_key),
        patch.object(p_resume, "require_plan_login", no_plan_turn),
        patch.dict("os.environ", {}, clear=False),
    ):
        log = Log("hp1-resume", tmp_path)
        assert asyncio.run(p_resume.main_async(log)) == 0
    assert log.path.read_text(encoding="utf-8").splitlines()[-1] == (
        "FINDING\tS36 plan to OpenRouter resume\tkeyring qmx/openrouter empty\tBLOCKED NO KEY"
    )
