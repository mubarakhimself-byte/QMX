# ruff: noqa: S101
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import p_resume
from common import Log, Provider
from p_providers import Budget
from p_resume import final_text, linked_home, s36_verdict, signed_thinking


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


def entry(kind: str, model: str, *blocks: dict[str, str]) -> str:
    return json.dumps({"type": kind, "message": {"model": model, "content": list(blocks)}})


PLAN_TURN = [
    entry("user", "", {"type": "text", "text": "Remember persimmon-a1b2c3"}),
    entry(
        "assistant", "claude-sonnet-5", {"type": "thinking", "thinking": "", "signature": "EqQB"}
    ),
    entry("assistant", "claude-sonnet-5", {"type": "text", "text": "noted."}),
]


def test_a_signed_thinking_block_counts_only_with_its_signature() -> None:
    unsigned = entry("assistant", "claude-haiku-5-5", {"type": "thinking", "thinking": "x"})
    assert signed_thinking(PLAN_TURN) == 1
    assert signed_thinking([unsigned, PLAN_TURN[2]]) == 0
    assert signed_thinking(["not json", ""]) == 0


def test_recall_reads_the_last_reply_text_past_a_closing_thinking_block_and_blank_text() -> None:
    deepseek = "deepseek/deepseek-v4.1-flash"
    recall = [
        *PLAN_TURN,
        entry("assistant", deepseek, {"type": "text", "text": "persimmon-a1b2c3"}),
        entry("assistant", deepseek, {"type": "thinking", "thinking": "", "signature": ""}),
        entry("assistant", deepseek, {"type": "text", "text": " "}),
    ]
    assert final_text(recall) == "persimmon-a1b2c3"
    assert s36_verdict(PLAN_TURN, recall, "persimmon-a1b2c3") == "PASS"
    assert s36_verdict(PLAN_TURN, PLAN_TURN, "persimmon-a1b2c3") == "FAIL"


def test_s36_is_unmeasured_when_the_plan_turn_carried_no_signed_thinking() -> None:
    text_only = [PLAN_TURN[0], PLAN_TURN[2]]
    recall = [
        *text_only,
        entry("assistant", "deepseek", {"type": "text", "text": "persimmon-a1b2c3"}),
    ]
    assert s36_verdict(text_only, recall, "persimmon-a1b2c3") == "UNMEASURED"


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
        assert asyncio.run(p_resume.main_async(log, Budget(0.1, tmp_path / "spend.tsv"))) == 0
    assert log.path.read_text(encoding="utf-8").splitlines()[-1] == (
        "FINDING\tS36 plan to OpenRouter resume\tkeyring qmx/openrouter empty\tBLOCKED NO KEY"
    )
