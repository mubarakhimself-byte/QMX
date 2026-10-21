# ruff: noqa: S101
"""Each probe's verdict on its recorded observation from the live run (`fixtures/records/`), and
on that observation with the one fact changed that flips the verdict. Run with
`uv run --no-sync python -m pytest scripts/probes/harness -q`."""

from __future__ import annotations

import copy
import json
from typing import Any

import p_nm
import p_perm
import p_pk
import p_pl
import p_set
import p_sys
import p_tg
from common import FIXTURES


def recorded(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / "records" / f"{name}.json").read_text(encoding="utf-8"))


def changed(name: str, edit: Any) -> dict[str, Any]:
    observation = copy.deepcopy(recorded(name))
    edit(observation)
    return observation


def test_p_nm_passes_when_64_loads_and_fails_when_it_does_not() -> None:
    assert p_nm.verdict(recorded("p_nm")).passed is True
    assert p_nm.longest_that_works(recorded("p_nm")) == 80

    def refused(o: dict[str, Any]) -> None:
        o["names"]["64"]["answered"] = False

    assert p_nm.verdict(changed("p_nm", refused)).failed() == [
        "the 64-character name loads and answers"
    ]


def test_p_set_passes_and_names_the_cache_fallback_when_only_the_cache_misses() -> None:
    assert p_set.verdict(recorded("p_set")).passed is True

    def no_read(o: dict[str, Any]) -> None:
        o["cache"]["eds"]["b"]["cache_read"] = 0

    missed = p_set.verdict(changed("p_set", no_read))
    assert missed.failed() == [
        "the second folder's chat reads the first chat's system prefix from cache"
    ]
    assert missed.fallback == p_set.CACHE_FALLBACK


def test_p_sys_passes_and_names_the_resume_fallback_when_the_old_text_comes_back() -> None:
    assert p_sys.verdict(recorded("p_sys")).passed is True

    def stale(o: dict[str, Any]) -> None:
        o["resume"]["snapshot_false"]["reply"] = o["resume"]["snapshot_false"]["old"]

    kept = p_sys.verdict(changed("p_sys", stale))
    assert kept.failed() == ["snapshot false: after a resume the model quotes the new append"]
    assert kept.fallback == p_sys.RESUME_FALLBACK


def test_p_perm_fails_on_the_undeclared_bash_the_cli_runs_without_asking() -> None:
    found = p_perm.verdict(recorded("p_perm"))
    assert found.failed() == [
        "A3 an undeclared Bash, read-only (A3) and writing (A3W), reaches the policy and is "
        "denied with its reason"
    ]
    assert found.fallback == p_perm.FALLBACK

    def guard_late(o: dict[str, Any]) -> None:
        call = o["a"]["steps"]["A2"]["call"]
        o["a"]["calls"][call]["guard_at"] = o["a"]["calls"][call]["asked_at"] + 1

    assert (
        "the guard saw every call first" in p_perm.verdict(changed("p_perm", guard_late)).failed()
    )


def test_p_perm_passes_when_the_undeclared_bash_reaches_the_policy() -> None:
    def denied(o: dict[str, Any]) -> None:
        for step in ("A3", "A3W"):
            call = o["a"]["steps"][step]["call"]
            reason = p_perm.POLICY_UNDECLARED.format(tool="Bash")
            o["a"]["calls"][call] |= {
                "asked_at": o["a"]["calls"][call]["guard_at"] + 0.01,
                "policy": "deny",
                "reason": reason,
                "ran": False,
            }
            o["a"]["steps"][step]["result"] = {"text": reason}
        o["a"]["files"].remove("attempt-1/a3.txt")

    assert p_perm.verdict(changed("p_perm", denied)).passed is True


def test_p_pk_fails_both_paths_and_passes_when_reconnect_relists() -> None:
    found = p_pk.verdict(recorded("p_pk"))
    assert found.failed() == ["(a) or (b) holds"]
    assert found.fallback == p_pk.FALLBACK

    def relisted(o: dict[str, Any]) -> None:
        row = o["paths"]["b_reconnect"]
        row["server_calls"].append("beta")
        row["after"] |= {"reply": "BETA-RAN", "offered": ["mcp__qmx__beta"]}

    assert p_pk.verdict(changed("p_pk", relisted)).passed is True


def test_p_tg_passes_and_fails_when_a_switch_off_reaches_the_second_chat() -> None:
    assert p_tg.verdict(recorded("p_tg")).passed is True

    def leaked(o: dict[str, Any]) -> None:
        o["second_chat"]["pack_x"] = "disabled"

    assert p_tg.verdict(changed("p_tg", leaked)).failed() == [
        "a switch-off in one chat leaves the server on in a second chat on the workspace"
    ]


def test_p_pl_passes_and_fails_when_a_pack_outside_the_set_lists_its_agent() -> None:
    assert p_pl.verdict(recorded("p_pl")).passed is True

    def leaked(o: dict[str, Any]) -> None:
        o["resume"]["before"]["agents"].append("pack-beta:beta-agent")

    found = p_pl.verdict(changed("p_pl", leaked))
    assert found.failed() == ["an enabled pack outside the set lists no agent, command or skill"]
    assert found.fallback == "PACK materialises one combined plugin view per pack set"
