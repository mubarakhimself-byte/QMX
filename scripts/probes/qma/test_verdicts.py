# ruff: noqa: S101
from __future__ import annotations

from common import is_final_release, parse_version, s19_scrub_verdict, s25_verdict, s38_verdict

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


def test_s25_passes_only_when_the_control_compacts_and_the_verbatim_compact_was_answered() -> None:
    assert s25_verdict(control=True, compact_answered=True, boundary=False) == "PASS"
    assert s25_verdict(control=False, compact_answered=True, boundary=False) == "FAIL"
    assert s25_verdict(control=True, compact_answered=False, boundary=False) == "FAIL"
    assert s25_verdict(control=True, compact_answered=True, boundary=True) == "FAIL"
