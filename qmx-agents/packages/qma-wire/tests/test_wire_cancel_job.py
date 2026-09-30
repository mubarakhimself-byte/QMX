"""Epic 73 — originating-session cancel wire contract."""

from __future__ import annotations

from qma.wire import (
    ADDABLE_COMMAND_COUNT,
    CANCEL_JOB_CAPABILITY,
    CANCEL_JOB_COMMAND,
    WireCommand,
    cancel_job_command_hash,
    durable_cancel_command_id,
    parse_cancel_job_payload,
    require_cancel_job_capability,
)
from qma.wire.schemas import validate_family_payload, validate_instance
from qma.wire.vocabulary import WIRE_COMMANDS
from qmf.core.refusal import is_ok, is_refusal


def _payload(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "handle_id": "job:cancel-73",
        "logical_run_id": "run:cancel-73",
        "attempt_id": 2,
        "command_id": "cancel:one",
        "expected_state": "queued",
    }
    values.update(overrides)
    return values


def test_cancel_job_is_addable_ct40_not_a_seed_alias() -> None:
    assert CANCEL_JOB_COMMAND == WireCommand.CANCEL_JOB.value == "cancel_job"
    assert CANCEL_JOB_COMMAND in WIRE_COMMANDS
    assert ADDABLE_COMMAND_COUNT == 5
    assert "stop_run" in WIRE_COMMANDS
    assert CANCEL_JOB_COMMAND != "stop_run"


def test_payload_fences_alias_and_expected_state() -> None:
    parsed = parse_cancel_job_payload(_payload(job_id="job:cancel-73"))
    assert is_ok(parsed), parsed
    assert parsed.value["handle_id"] == parsed.value["job_id"]
    assert parsed.value["expected_state"] == "queued"
    assert is_refusal(parse_cancel_job_payload(_payload(job_id="job:other")))
    assert is_refusal(parse_cancel_job_payload(_payload(attempt_id=True)))
    assert is_refusal(parse_cancel_job_payload(_payload(expected_state="unknown-ish")))


def test_expected_state_is_excluded_from_stable_cancel_identity() -> None:
    queued = parse_cancel_job_payload(_payload(expected_state="queued"))
    running = parse_cancel_job_payload(_payload(expected_state="running"))
    assert is_ok(queued) and is_ok(running)
    assert cancel_job_command_hash(
        queued.value,
        originating_product_session_ref="psess:origin-73",
    ) == cancel_job_command_hash(
        running.value,
        originating_product_session_ref="psess:origin-73",
    )
    changed_command = parse_cancel_job_payload(_payload(command_id="cancel:two"))
    assert is_ok(changed_command)
    assert cancel_job_command_hash(
        queued.value,
        originating_product_session_ref="psess:origin-73",
    ) != cancel_job_command_hash(
        changed_command.value,
        originating_product_session_ref="psess:origin-73",
    )
    assert durable_cancel_command_id("cancel:one", "psess:origin-73") == (
        "psess:origin-73/cancel:one"
    )


def test_missing_cancel_capability_is_a_typed_mismatch() -> None:
    missing = require_cancel_job_capability({})
    assert is_refusal(missing)
    assert missing.context["missing"] == CANCEL_JOB_CAPABILITY
    assert is_ok(require_cancel_job_capability({CANCEL_JOB_CAPABILITY: True}))


def test_cancel_job_schema_describes_the_required_payload() -> None:
    assert is_ok(validate_family_payload("cancel_job", _payload()))
    assert is_refusal(validate_family_payload("cancel_job", {"handle_id": "job:missing"}))
    assert is_refusal(validate_instance({"family": "command", "name": "cancel_job"}, "command"))
