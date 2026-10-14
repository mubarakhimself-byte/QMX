# ruff: noqa: S101
from __future__ import annotations

from common import (
    is_final_release,
    oq5_home_verdict,
    parse_version,
    s19_scrub_verdict,
    s25_verdict,
    s38_verdict,
)

PLANTED = ("HTTPS_PROXY", "OPENAI_API_KEY")


def test_parse_version_reads_release_part_of_cli_and_prerelease_strings() -> None:
    assert parse_version("2.1.299 (Claude Code)") == (2, 1, 299)
    assert parse_version("0.3.0rc1") == (0, 3, 0)
    assert [is_final_release(v) for v in ("0.2.166", "0.3.0rc1", "0.3.0.dev1")] == [
        True,
        False,
        False,
    ]


def test_s19_passes_only_when_bash_ran_and_every_planted_name_was_scrubbed() -> None:
    listing = {"PATH", "HOME"}
    assert s19_scrub_verdict(PLANTED, PLANTED, 1, True, listing) == ([], "PASS")
    assert s19_scrub_verdict(PLANTED, PLANTED, 0, True, listing) == ([], "FAIL")
    assert s19_scrub_verdict(PLANTED, ("HTTPS_PROXY",), 1, True, listing) == ([], "FAIL")
    assert s19_scrub_verdict(PLANTED, PLANTED, 1, True, listing | {"OPENAI_API_KEY"}) == (
        ["OPENAI_API_KEY"],
        "FAIL",
    )


def test_s38_passes_only_on_an_attempted_bash_call_blocked_by_the_timeout() -> None:
    assert s38_verdict(bash_calls=1, timeout_texts=1, ran=False) == "PASS"
    assert s38_verdict(bash_calls=0, timeout_texts=0, ran=False) == "FAIL"
    assert s38_verdict(bash_calls=1, timeout_texts=0, ran=False) == "FAIL"
    assert s38_verdict(bash_calls=1, timeout_texts=1, ran=True) == "FAIL"


def test_s25_passes_only_when_the_control_compacts_and_the_model_answered_verbatim() -> None:
    assert s25_verdict(control=True, answered=True, turns=1, boundary=False) == "PASS"
    assert s25_verdict(control=False, answered=True, turns=1, boundary=False) == "FAIL"
    assert s25_verdict(control=True, answered=False, turns=1, boundary=False) == "FAIL"
    assert s25_verdict(control=True, answered=True, turns=0, boundary=False) == "FAIL"
    assert s25_verdict(control=True, answered=True, turns=1, boundary=True) == "FAIL"


HOME = frozenset({"hp0-plant-plugin", "hp0-plant-skill", "hp0-plant-cmd", "hp0-plant-agent"})
CONTROL = {
    "commands": ["hp0-plant-skill", "hp0-plant-cmd", "hp0-plant-plugin:hp0-plant-plugin-cmd"],
    "agents": ["hp0-plant-agent"],
}
PROBE = {"commands": ["hp0-sdk-plugin:hp0-sdk-plugin-cmd"], "agents": []}


def test_oq5_passes_only_when_the_control_loads_every_plant_and_the_probe_loads_none() -> None:
    assert oq5_home_verdict(HOME, CONTROL, PROBE, home_hook=0, hook_control=True) == "PASS"
    skill = {"commands": [*PROBE["commands"], "hp0-plant-skill"], "agents": []}
    assert oq5_home_verdict(HOME, CONTROL, skill, home_hook=0, hook_control=True) == "FAIL"
    agent = {"commands": PROBE["commands"], "agents": ["hp0-plant-agent"]}
    assert oq5_home_verdict(HOME, CONTROL, agent, home_hook=0, hook_control=True) == "FAIL"
    assert oq5_home_verdict(HOME, CONTROL, CONTROL, home_hook=0, hook_control=True) == "FAIL"
    assert oq5_home_verdict(HOME, CONTROL, PROBE, home_hook=1, hook_control=True) == "FAIL"
    no_agent = {"commands": CONTROL["commands"], "agents": []}
    assert oq5_home_verdict(HOME, no_agent, PROBE, home_hook=0, hook_control=True) == "UNMEASURED"
    assert oq5_home_verdict(HOME, CONTROL, PROBE, home_hook=0, hook_control=False) == "UNMEASURED"
