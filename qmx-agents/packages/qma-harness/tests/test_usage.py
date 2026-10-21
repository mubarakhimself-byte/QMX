from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import claude_agent_sdk
import pytest
from claude_agent_sdk import AssistantMessage, TextBlock
from claude_agent_sdk._internal.message_parser import parse_message
from qmx_ledger.journal import RunJournal
from qmx_router.readings import usage_page

from qma.harness.home import DoctorLine
from qma.harness.project import (
    Limits,
    PlanMeter,
    Reading,
    TurnUsage,
    UnreadableLimits,
    project,
)
from qma.harness.usage import (
    Totals,
    UsageLedger,
    plan_base,
    plan_row,
    token_sums,
    usage_lines,
)

T0 = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)
LATER = T0 + timedelta(hours=5)
"""Every fact below resets then unless the test says otherwise."""


class Clock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now


def ledger() -> tuple[UsageLedger, Clock]:
    clock = Clock()
    return UsageLedger(clock), clock


def at(minutes: int) -> datetime:
    return T0 + timedelta(minutes=minutes)


def event(**info: Any) -> Limits | UnreadableLimits:
    """One `rate_limit_event` as the CLI writes it, through the SDK parser and `project`."""
    message = parse_message(
        {
            "type": "rate_limit_event",
            "rate_limit_info": {"resetsAt": int(LATER.timestamp()), **info},
            "uuid": "u",
            "session_id": "s",
        }
    )
    assert message is not None
    (fact,) = project(message)
    assert isinstance(fact, Limits | UnreadableLimits)
    return fact


def stop_after(*events: dict[str, Any]) -> str | None:
    usage, _ = ledger()
    for minute, info in enumerate(events, start=1):
        usage.record(event(**info), at(minute))
    return usage.hard_stop()


def test_the_newest_fact_per_window_wins() -> None:
    usage, _ = ledger()
    usage.record(event(status="allowed", rateLimitType="five_hour"), at(1))
    usage.record(
        event(status="rejected", rateLimitType="five_hour", overageStatus="rejected"), at(2)
    )
    usage.record(event(status="allowed_warning", rateLimitType="seven_day"), at(3))
    assert [(view.limits.window, view.limits.status) for view in usage.windows()] == [
        ("five_hour", "rejected"),
        ("seven_day", "allowed_warning"),
    ]


def test_a_replayed_older_fact_changes_nothing() -> None:
    usage, _ = ledger()
    newer = event(status="allowed", rateLimitType="five_hour", isUsingOverage=False)
    older = event(status="allowed", rateLimitType="five_hour", isUsingOverage=True)
    usage.record(newer, at(2))
    usage.record(older, at(1))
    usage.record(newer, at(2))
    assert usage.hard_stop() is None
    assert [(view.limits, view.as_of) for view in usage.windows()] == [(newer, at(2))]


def test_a_fact_past_its_reset_is_dropped_on_read_and_its_stop_with_it() -> None:
    usage, clock = ledger()
    usage.record(
        event(
            status="allowed",
            rateLimitType="five_hour",
            isUsingOverage=True,
            resetsAt=int(at(10).timestamp()),
        ),
        at(1),
    )
    assert usage.hard_stop() == "rule 1: the plan is drawing paid extra usage (five_hour window)"
    clock.now = at(10)
    assert usage.windows() == ()
    assert usage.hard_stop() is None


def test_a_stop_lasts_until_the_later_of_the_two_resets() -> None:
    usage, clock = ledger()
    usage.record(
        event(
            status="rejected",
            rateLimitType="five_hour",
            overageStatus="allowed",
            resetsAt=int(at(10).timestamp()),
            overageResetsAt=int(at(20).timestamp()),
        ),
        at(1),
    )
    clock.now = at(15)
    assert usage.hard_stop() == (
        "rule 2: the five_hour window is used up and paid extra usage is allowed, "
        "so the next request could bill"
    )
    clock.now = at(20)
    assert usage.hard_stop() is None


def test_rule_1_using_overage_from_either_raw_key() -> None:
    assert stop_after(
        {"status": "allowed", "rateLimitType": "seven_day", "isUsingOverage": True}
    ) == ("rule 1: the plan is drawing paid extra usage (seven_day window)")
    assert stop_after(
        {"status": "allowed", "rateLimitType": "five_hour", "overageInUse": True}
    ) == ("rule 1: the plan is drawing paid extra usage (five_hour window)")


def test_rule_2_a_rejected_plan_window_with_extra_usage_allowed() -> None:
    allowed = {"status": "rejected", "rateLimitType": "five_hour", "overageStatus": "allowed"}
    warning = {**allowed, "overageStatus": "allowed_warning"}
    assert stop_after(allowed) == (
        "rule 2: the five_hour window is used up and paid extra usage is allowed, "
        "so the next request could bill"
    )
    assert stop_after(warning) == (
        "rule 2: the five_hour window is used up and paid extra usage is allowed_warning, "
        "so the next request could bill"
    )


def test_rule_2_fails_closed_when_the_overage_status_is_missing() -> None:
    assert stop_after({"status": "rejected", "rateLimitType": "seven_day"}) == (
        "rule 2: the seven_day window is used up and paid extra usage is not reported, "
        "so the next request could bill"
    )


def test_rule_3_an_overage_window_not_rejected() -> None:
    assert stop_after({"status": "allowed", "rateLimitType": "overage"}) == (
        "rule 3: the overage window is allowed"
    )
    assert (
        stop_after({"status": "allowed", "rateLimitType": "overage", "isUsingOverage": False})
        is None
    )


def test_rule_4_credits_required() -> None:
    assert (
        stop_after(
            {
                "status": "rejected",
                "rateLimitType": "five_hour",
                "overageStatus": "rejected",
                "errorCode": "credits_required",
            }
        )
        == "rule 4: the CLI reports that credits are required (five_hour window)"
    )


def test_a_rejected_plan_with_extra_usage_rejected_is_no_overage_stop() -> None:
    usage, _ = ledger()
    usage.record(
        event(
            status="rejected",
            rateLimitType="five_hour",
            overageStatus="rejected",
            overageDisabledReason="out_of_credits",
        ),
        at(1),
    )
    assert usage.hard_stop() is None
    assert usage.rejected() is True


def test_a_newer_clean_fact_clears_the_stop() -> None:
    assert (
        stop_after(
            {"status": "allowed", "rateLimitType": "five_hour", "isUsingOverage": True},
            {"status": "allowed", "rateLimitType": "five_hour", "isUsingOverage": False},
        )
        is None
    )


@pytest.mark.parametrize(
    ("info", "reason"),
    [
        ({"status": "paused"}, "status is 'paused'"),
        ({"status": "allowed", "rateLimitType": "monthly"}, "rateLimitType is 'monthly'"),
        ({"status": "allowed", "overageStatus": "on"}, "overageStatus is 'on'"),
        ({"status": "allowed", "isUsingOverage": "yes"}, "isUsingOverage is 'yes'"),
        ({"status": "allowed", "overageInUse": 1}, "overageInUse is 1"),
        ({"status": "allowed", "overageEnabled": "true"}, "overageEnabled is 'true'"),
        ({"status": "allowed", "errorCode": "spend_cap"}, "errorCode is 'spend_cap'"),
        ({"status": "allowed", "resetsAt": "soon"}, "resetsAt is 'soon'"),
        ({"status": "allowed", "utilization": "half"}, "utilization is 'half'"),
        ({"status": "allowed", "unifiedWindows": []}, "unifiedWindows is []"),
    ],
)
def test_an_event_outside_the_schema_is_unreadable_and_stops_the_plan(
    info: dict[str, Any], reason: str
) -> None:
    fact = event(**info)
    assert fact == UnreadableLimits(f"a rate-limit event could not be read: {reason}")
    usage, _ = ledger()
    usage.record(event(status="allowed", rateLimitType="five_hour"), at(1))
    usage.record(fact, at(2))
    assert usage.hard_stop() == f"a rate-limit event could not be read: {reason}"


def test_only_a_newer_readable_event_lifts_an_unreadable_stop() -> None:
    usage, _ = ledger()
    unreadable = UnreadableLimits("a rate-limit event could not be read: status is 'paused'")
    usage.record(unreadable, at(2))
    usage.record(event(status="allowed", rateLimitType="seven_day"), at(1))
    assert usage.hard_stop() == "a rate-limit event could not be read: status is 'paused'"
    usage.record(event(status="allowed", rateLimitType="seven_day"), at(3))
    assert usage.hard_stop() is None
    usage.record(unreadable, at(2))
    assert usage.hard_stop() is None


def pinned_cli() -> bytes:
    folder = Path(claude_agent_sdk.__file__).parent / "_bundled"
    cli = folder / ("claude.exe" if os.name == "nt" else "claude")
    if not cli.exists():
        pytest.skip("the SDK wheel bundles no CLI here")
    return cli.read_bytes()


def test_the_raw_overage_keys_match_the_pinned_cli_schema() -> None:
    schema = pinned_cli()
    assert (
        b"isUsingOverage:M().optional(),overageInUse:M().optional(),overageEnabled:M().optional()"
    ) in schema
    assert b'errorCode:U(["credits_required"]).optional()' in schema
    fact = event(
        status="allowed",
        rateLimitType="five_hour",
        isUsingOverage=False,
        overageInUse=True,
        overageEnabled=True,
        errorCode="credits_required",
    )
    assert isinstance(fact, Limits)
    assert (fact.using_overage, fact.overage_enabled, fact.credits_required) == (True, True, True)


def test_the_pinned_cli_window_names_are_the_ones_read() -> None:
    assert (
        b'rateLimitType:U(["five_hour","seven_day","seven_day_opus","seven_day_sonnet",'
        b'"seven_day_overage_included","overage"]).optional()'
    ) in pinned_cli()


def test_extra_usage_on_reads_the_newest_fact() -> None:
    usage, _ = ledger()
    assert usage.extra_usage_on() is None
    usage.record(event(status="allowed", rateLimitType="five_hour"), at(1))
    assert usage.extra_usage_on() is None
    usage.record(
        event(
            status="allowed_warning",
            rateLimitType="seven_day",
            overageStatus="rejected",
            overageDisabledReason="out_of_credits",
            isUsingOverage=False,
            overageEnabled=True,
        ),
        at(2),
    )
    assert usage.extra_usage_on() is True
    assert usage.hard_stop() is None
    assert usage_lines(usage) == [
        DoctorLine("plan overage stop", True, "no stop"),
        DoctorLine(
            "plan extra usage",
            False,
            "extra usage is on for this account; switch it off at claude.ai so the plan can "
            "never bill",
        ),
    ]
    usage.record(
        event(
            status="allowed",
            rateLimitType="five_hour",
            overageStatus="rejected",
            overageEnabled=False,
        ),
        at(3),
    )
    assert usage.extra_usage_on() is False


def reading_ledger(utilization: float) -> UsageLedger:
    usage, _ = ledger()
    usage.record(
        event(
            status="allowed",
            rateLimitType="seven_day",
            unifiedWindows={
                "five_hour": {"utilization": utilization, "resetsAt": int(LATER.timestamp())}
            },
        ),
        at(1),
    )
    return usage


def test_a_saved_reading_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "plan-usage.json"
    first = UsageLedger(Clock(), path)
    first.record(
        event(
            status="allowed",
            rateLimitType="seven_day",
            unifiedWindows={"five_hour": {"utilization": 0.2, "resetsAt": int(LATER.timestamp())}},
        ),
        at(1),
    )
    again = UsageLedger(Clock(), path)
    held = again.reading("five_hour")
    assert held is not None
    assert held.reading.utilization == 0.2


USAGE_TEXT = (
    "You are currently using your subscription to power your Claude Code usage\n\n"
    "Current session: 25% used · resets Oct 14, 8:20pm (Africa/Nairobi)\n"
    "Current week (all models): 1% used · resets Oct 21, 4pm (Africa/Nairobi)"
)


def test_the_usage_command_reply_is_a_meter_reading() -> None:
    synthetic = AssistantMessage(content=[TextBlock(USAGE_TEXT)], model="<synthetic>")
    model = AssistantMessage(content=[TextBlock(USAGE_TEXT)], model="claude-haiku-5-5")
    meters = [fact for fact in project(synthetic) if isinstance(fact, PlanMeter)]
    assert meters == [
        PlanMeter((Reading("five_hour", 0.25, None), Reading("seven_day", 0.01, None)))
    ]
    assert [fact for fact in project(model) if isinstance(fact, PlanMeter)] == []


def test_the_newest_reading_wins_across_sources() -> None:
    usage = reading_ledger(0.2)
    usage.record(PlanMeter((Reading("five_hour", 0.25, None),)), at(2))
    view = usage.reading("five_hour")
    assert view is not None
    assert (view.reading.utilization, view.source) == (0.25, "usage_command")


def turn(cost: float, tokens: tuple[int, int, int, int], turns: int = 1) -> TurnUsage:
    inputs, outputs, read, write = tokens
    return TurnUsage(
        session_id="s",
        model_usage={
            "claude-haiku-5-5": {
                "inputTokens": inputs,
                "outputTokens": outputs,
                "cacheReadInputTokens": read,
                "cacheCreationInputTokens": write,
                "costUSD": cost,
            }
        },
        total_cost_usd=cost,
        num_turns=turns,
    )


def test_plan_rows_are_per_turn_differences_of_the_running_totals() -> None:
    first, totals = plan_row(turn(0.0001172, (2, 4, 0, 575)), Totals())
    second, totals = plan_row(turn(0.000368, (1172, 28, 0, 1184)), totals)
    usage_command, totals = plan_row(turn(0.000368, (1172, 28, 0, 1184), turns=0), totals)
    assert first is not None
    assert second is not None
    assert {key: first[key] for key in ("input_tokens", "output_tokens", "cache_write_tokens")} == {
        "input_tokens": 2,
        "output_tokens": 4,
        "cache_write_tokens": 575,
    }
    assert first["metadata"] == {"cost": 0.0001172}
    assert (second["input_tokens"], second["cache_write_tokens"]) == (1170, 609)
    assert second["metadata"] == {"cost": 0.0002508}
    assert usage_command is None
    assert totals == Totals(0.000368, 1172, 28, 0, 1184)


def test_a_fresh_process_below_the_base_counts_all_it_reports() -> None:
    row, _ = plan_row(turn(0.0001, (5, 5, 0, 0)), Totals(0.0003, 100, 10, 0, 0))
    assert row is not None
    assert (row["input_tokens"], row["metadata"]) == (5, {"cost": 0.0001})


def test_a_resumed_chat_starts_from_its_journaled_totals(tmp_path: Path) -> None:
    path = tmp_path / "runs" / "s" / "journal.jsonl"
    with RunJournal(path, "s") as journal:
        row, _ = plan_row(turn(0.00000795, (2, 4, 575, 0)), Totals())
        assert row is not None
        journal.append("model_call", row)
    base = plan_base(path)
    assert base == Totals(0.00000795, 2, 4, 575, 0)
    resumed, _ = plan_row(turn(0.00013215, (4, 8, 575, 610)), base)
    assert resumed is not None
    assert (resumed["input_tokens"], resumed["cache_write_tokens"]) == (2, 610)
    assert resumed["metadata"] == {"cost": 0.0001242}


def test_token_sums_add_model_call_rows_per_profile(tmp_path: Path) -> None:
    with RunJournal(tmp_path / "runs" / "a" / "journal.jsonl", "a") as journal:
        for cost, tokens in ((0.0001, (2, 4, 0, 575)), (0.0003, (10, 20, 30, 40))):
            row, _ = plan_row(turn(cost, tokens), Totals())
            assert row is not None
            journal.append("model_call", row)
    with RunJournal(tmp_path / "runs" / "b" / "journal.jsonl", "b") as journal:
        journal.append(
            "model_call",
            {
                "profile": "kimi",
                "input_tokens": 7,
                "output_tokens": 1,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
            },
        )
        journal.append("token_count", {"profile": "kimi", "input_tokens": 99})
    assert token_sums(tmp_path / "runs") == {
        "claude": {
            "input_tokens": 12,
            "output_tokens": 24,
            "cache_read_tokens": 30,
            "cache_write_tokens": 615,
            "calls": 2,
        },
        "kimi": {
            "input_tokens": 7,
            "output_tokens": 1,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "calls": 1,
        },
    }


def test_the_page_holds_every_field_and_the_last_reading_note() -> None:
    usage = reading_ledger(0.2)
    document = usage_page(usage, {"claude": {"calls": 1}}).document()
    assert document == {
        "windows": {
            "claude": [
                {
                    "window": "seven_day",
                    "status": "allowed",
                    "utilization": None,
                    "resets_at": "2026-10-15T17:00:00+00:00",
                    "overage_status": None,
                    "overage_resets_at": None,
                    "overage_disabled_reason": None,
                    "using_overage": None,
                    "overage_enabled": None,
                    "credits_required": False,
                    "as_of": "2026-10-15T12:01:00+00:00",
                }
            ]
        },
        "readings": {
            "claude": [
                {
                    "window": "five_hour",
                    "utilization": 0.2,
                    "resets_at": "2026-10-15T17:00:00+00:00",
                    "as_of": "2026-10-15T12:01:00+00:00",
                    "source": "rate_limit_event",
                }
            ]
        },
        "tokens": {"claude": {"calls": 1}},
        "hard_stop": None,
        "extra_usage_on": None,
        "extra_usage_note": None,
    }


def test_a_stop_survives_a_restart_until_a_newer_clean_fact(tmp_path: Path) -> None:
    path = tmp_path / "state" / "plan-usage.json"
    clock = Clock()
    first = UsageLedger(clock, path)
    first.record(
        event(status="rejected", rateLimitType="five_hour", overageStatus="allowed"), at(1)
    )
    restarted = UsageLedger(clock, path)
    assert restarted.hard_stop() == (
        "rule 2: the five_hour window is used up and paid extra usage is allowed, "
        "so the next request could bill"
    )
    restarted.record(
        event(status="allowed", rateLimitType="five_hour", overageStatus="rejected"), at(2)
    )
    assert UsageLedger(clock, path).hard_stop() is None


def test_an_unreadable_mark_survives_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "plan-usage.json"
    clock = Clock()
    UsageLedger(clock, path).record(event(status="paused"), at(1))
    assert UsageLedger(clock, path).hard_stop() == (
        "a rate-limit event could not be read: status is 'paused'"
    )


def test_a_saved_stop_lifts_when_its_reset_passes(tmp_path: Path) -> None:
    path = tmp_path / "plan-usage.json"
    clock = Clock()
    UsageLedger(clock, path).record(
        event(status="allowed", isUsingOverage=True, resetsAt=int(at(10).timestamp())), at(1)
    )
    clock.now = at(10)
    assert UsageLedger(clock, path).hard_stop() is None


@pytest.mark.parametrize(
    "saved",
    [
        "not json",
        '{"windows": [{"limits": {"status": "paused"}, "as_of": "2026-10-15T12:00:00+00:00"}],'
        ' "unreadable": null}',
        '{"unreadable": null}',
    ],
)
def test_a_saved_file_that_cannot_be_read_stops_the_plan(tmp_path: Path, saved: str) -> None:
    path = tmp_path / "plan-usage.json"
    path.write_text(saved, encoding="utf-8")
    stop = UsageLedger(Clock(), path).hard_stop()
    assert stop is not None
    assert stop.startswith(f"the saved plan usage at {path} could not be read")


def test_every_sdk_parse_failure_carries_its_message() -> None:
    from claude_agent_sdk._errors import MessageParseError
    from claude_agent_sdk._internal import message_parser

    import qma.harness.chat  # noqa: F401  # pyright: ignore[reportUnusedImport]

    broken: dict[str, Any] = {
        "type": "rate_limit_event",
        "rate_limit_info": [],
        "uuid": "u",
        "session_id": "s",
    }
    with pytest.raises(MessageParseError) as raised:
        message_parser.parse_message(broken)
    assert (str(raised.value), raised.value.data) == (
        "TypeError: list indices must be integers or slices, not str",
        broken,
    )
