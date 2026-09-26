"""Reference usage — J-KIT-06 read retries; external-egress does not; no invented ceiling."""

from __future__ import annotations

from qma.core.refusals.variants import BlindRetryRefused
from qma.daemon.kit_journey import (
    HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA,
    INVENTED_CEILING_NUMBER,
    J_KIT_06,
    KIT_JOURNEY_06_E2E_AT_INSPECT_SHA,
    OPERATOR_PAGED_FOR_READ_FLAKE,
    JKit06Fixture,
    claim_j_kit_06_e2e_at_inspect_sha,
    refuse_invented_ceiling_number,
    refuse_operator_paged_for_read_flake,
)
from qma.daemon.retry import HostRetryStopReason
from qmf.core import is_ok, is_refusal


def main() -> None:
    assert J_KIT_06 == "J-KIT-06"
    assert KIT_JOURNEY_06_E2E_AT_INSPECT_SHA is False
    assert HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA is False
    assert OPERATOR_PAGED_FOR_READ_FLAKE is False
    assert INVENTED_CEILING_NUMBER is None
    assert is_refusal(claim_j_kit_06_e2e_at_inspect_sha(True))
    assert is_ok(claim_j_kit_06_e2e_at_inspect_sha(False))
    assert is_refusal(refuse_operator_paged_for_read_flake())
    assert is_refusal(refuse_invented_ceiling_number(value=3))

    fixture = JKit06Fixture()
    assert is_refusal(fixture.attempt_ceiling())
    assert is_refusal(fixture.invent_ceiling_number(3))
    injected = fixture.inject_registry_ceiling(2)
    assert is_ok(injected)
    assert injected.value == 2

    read = fixture.flake_read(retryability="yes")
    assert is_ok(read)
    assert read.value.attempt_ids == (1, 2)
    assert read.value.stop_reason is HostRetryStopReason.SUCCESS
    assert read.value.operator_paged is False
    assert is_refusal(fixture.page_operator())

    lost = fixture.send_external_egress()
    assert is_ok(lost)
    assert lost.value.send_count == 1
    assert lost.value.stop_reason is HostRetryStopReason.UNKNOWN
    assert lost.value.disposition == "unknown"
    second = fixture.second_send()
    assert is_refusal(second)
    assert BlindRetryRefused.matches(second)
    assert is_refusal(fixture.fill_gap_0081_chrome())


if __name__ == "__main__":
    main()
