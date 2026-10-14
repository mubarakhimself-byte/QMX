# ruff: noqa: S101
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from unittest.mock import patch

import p_providers
from common import Log, Provider
from p_providers import (
    b1_verdict,
    b3_verdict,
    b4_verdict,
    collect_toolsearch,
    perf_verdict,
    tool_search_state,
    websearch_verdict,
)


def findings(log: Log) -> list[str]:
    return [
        line
        for line in log.path.read_text(encoding="utf-8").splitlines()
        if line.startswith("FINDING")
    ]


def test_a_row_without_a_keyring_entry_prints_no_key_for_every_probe(tmp_path: Path) -> None:
    def no_key(_provider: Provider) -> None:
        return None

    with patch.object(p_providers, "read_key", no_key), patch.dict("os.environ", {}, clear=False):
        log = Log("hp1-glm", tmp_path)
        assert asyncio.run(p_providers.row(log, "glm")) == 0
    assert findings(log) == [
        "FINDING\tB1 glm\tkeyring qmx/glm empty\tNO KEY",
        "FINDING\tB3 glm\tkeyring qmx/glm empty\tNO KEY",
        "FINDING\tB4 glm\tkeyring qmx/glm empty\tNO KEY",
        "FINDING\tWebSearch glm\tkeyring qmx/glm empty\tNO KEY",
        "FINDING\ttool search glm\tkeyring qmx/glm empty\tNO KEY",
    ]


def test_no_provider_row_pins_a_claude_or_gpt_model_or_a_router_slug() -> None:
    assert [
        p.name
        for p in p_providers.PROVIDERS.values()
        if re.search(r"claude|gpt|opus|sonnet|haiku|fable", p.model, re.I) or "~" in p.model
    ] == []


def test_tool_search_state_reads_the_init_tool_list() -> None:
    assert tool_search_state(["Bash", "ToolSearch", "mcp__probe__ping"]) == "ToolSearch=on"
    assert tool_search_state(["Bash", "mcp__probe__ping"]) == "ToolSearch=off"
    assert tool_search_state([]) == "no init"


def test_probe_verdicts_need_the_signal_02b_names() -> None:
    assert b1_verdict(1, True, True) == "PASS"
    assert b1_verdict(1, False, True) == "FAIL"
    assert b1_verdict(0, True, True) == "FAIL"
    assert b3_verdict([0, 0, 512]) == "PASS"
    assert b3_verdict([0, 512, 0]) == "FAIL"
    assert b3_verdict([0, 0]) == "FAIL"
    assert b4_verdict(True, 2, []) == "PASS"
    assert b4_verdict(True, 2, ["status=400 thinking block signature invalid"]) == "FAIL"
    assert b4_verdict(True, 1, []) == "FAIL"
    assert websearch_verdict(1, ["Messages - Anthropic"], True) == "PASS"
    assert websearch_verdict(1, ["Error: web search is not supported"], True) == "REFUSED"
    assert websearch_verdict(0, [], True) == "NOT CALLED"


def test_perf_marks_a_row_slow_past_three_times_the_plan_median() -> None:
    assert perf_verdict([100.0, 200.0, 300.0], [500.0, 600.0, 700.0]) == "PASS"
    assert perf_verdict([100.0, 200.0, 300.0], [500.0, 700.0, 900.0]) == "SLOW"
    assert perf_verdict([100.0, 200.0, 300.0], []) == "FAIL"


def test_toolsearch_collects_the_latest_rows_of_each_provider_log(tmp_path: Path) -> None:
    (tmp_path / "hp1-openrouter.log").write_text(
        "FINDING\ttool search openrouter\told\tFAIL\n"
        "FINDING\tB1 openrouter\tx\tPASS\n"
        "FINDING\ttool search openrouter\tnew\tPASS\n"
        "FINDING\tWebSearch openrouter\tcalls 1\tREFUSED\n",
        encoding="utf-8",
    )
    with patch.object(p_providers, "HP1_EVIDENCE", tmp_path):
        log = Log("hp1-toolsearch", tmp_path)
        collect_toolsearch(log)
    assert findings(log) == [
        "FINDING\ttool search openrouter\tnew\tPASS",
        "FINDING\tWebSearch openrouter\tcalls 1\tREFUSED",
    ]
