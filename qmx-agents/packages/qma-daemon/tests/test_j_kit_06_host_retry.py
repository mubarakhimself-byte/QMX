"""Story 65.5 — J-KIT-06 read retries; external-egress does not; no invented ceiling."""

from __future__ import annotations

import ast
import runpy
from pathlib import Path
from typing import cast

from qma.core.ports.copilot import GAP_0081_CHROME_FILLED
from qma.core.refusals.variants import BlindRetryRefused
from qma.daemon.journal.variables import (
    HOST_RETRY_ATTEMPT_CEILING_KEY,
    HOST_RETRY_ATTEMPT_CEILING_REGISTRY_KEY,
    GovernedVariableRegistry,
)
from qma.daemon.kit_journey import (
    HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA,
    INVENTED_CEILING_NUMBER,
    J_KIT_06,
    KIT_JOURNEY_06_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_06_INSPECT_SHA,
    KIT_JOURNEY_06_OWNER,
    OPERATOR_PAGED_FOR_READ_FLAKE,
    JKit06Fixture,
    claim_j_kit_06_e2e_at_inspect_sha,
    refuse_blind_j_kit_06_second_send,
    refuse_invented_ceiling_number,
    refuse_operator_paged_for_read_flake,
)
from qma.daemon.retry import (
    BLIND_EXTERNAL_EGRESS_RETRY,
    EFFECT_CLASS_TYPES_EXISTED_AT_INSPECT_SHA,
    OPERATOR_IS_RECOVERY_LOOP,
    HostRetryStopReason,
)
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import Result, Retryability

_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "kit_journey_retry.py"
_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "j_kit_06_host_retry_usage.py"
_RETRY_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "retry.py"
_VARIABLES_SRC = (
    Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "journal" / "variables.py"
)


def _ok[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_inspect_sha_honesty_fixtures_are_not_e2e() -> None:
    assert J_KIT_06 == "J-KIT-06"
    assert KIT_JOURNEY_06_INSPECT_SHA == "34c148b"
    assert KIT_JOURNEY_06_E2E_AT_INSPECT_SHA is False
    assert HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA is False
    assert EFFECT_CLASS_TYPES_EXISTED_AT_INSPECT_SHA is True
    assert OPERATOR_PAGED_FOR_READ_FLAKE is False
    assert OPERATOR_IS_RECOVERY_LOOP is False
    assert BLIND_EXTERNAL_EGRESS_RETRY is False
    assert INVENTED_CEILING_NUMBER is None
    assert GAP_0081_CHROME_FILLED is False
    claimed = claim_j_kit_06_e2e_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert claimed.context["e2e_at_inspect_sha"] is False
    assert claimed.context["class_test_existence_is_e2e"] is False
    assert claimed.context["inspect_sha"] == "34c148b"
    assert claimed.context["host_retry_loop_existed_at_inspect_sha"] is False
    assert claimed.context["branch"] == "D"
    assert _ok(claim_j_kit_06_e2e_at_inspect_sha(False)) is False
    assert is_refusal(claim_j_kit_06_e2e_at_inspect_sha("wired"))


def test_read_flake_retries_in_host_operator_not_paged() -> None:
    fixture = JKit06Fixture()
    assert fixture.owner == KIT_JOURNEY_06_OWNER == "COMP-QMA-DAEMON"
    assert fixture.journey == J_KIT_06
    assert fixture.e2e_at_inspect_sha is False
    assert fixture.operator_paged is False
    unfilled = fixture.flake_read()
    assert is_refusal(unfilled)
    assert unfilled.context["invented_default"] is False
    assert unfilled.context["registry_key"] == HOST_RETRY_ATTEMPT_CEILING_REGISTRY_KEY

    injected = _ok(fixture.inject_registry_ceiling(2))
    assert injected == 2
    assert _ok(fixture.attempt_ceiling()) == 2
    recovered = _ok(fixture.flake_read(retryability=Retryability.YES))
    assert recovered.logical_invocation_id == "inv:j-kit-06-read"
    assert recovered.attempt_ids == (1, 2)
    assert recovered.attempt_id == 2
    assert recovered.stop_reason is HostRetryStopReason.SUCCESS
    assert recovered.operator_paged is False
    assert recovered.operator_is_recovery_loop is False
    assert recovered.value == {"ok": True}
    body = dict(recovered.to_payload())
    assert body["journey"] == J_KIT_06
    assert body["operator_paged"] is False
    assert body["attempt_ids"] == [1, 2]
    paged = fixture.page_operator()
    assert is_refusal(paged)
    assert paged.context["operator_paged"] is False
    assert is_refusal(refuse_operator_paged_for_read_flake())
    chrome = fixture.fill_gap_0081_chrome()
    assert is_refusal(chrome)
    assert chrome.context["gap_0081_chrome_filled"] is False


def test_after_condition_read_retries_retryability_no_does_not() -> None:
    fixture = JKit06Fixture()
    _ok(fixture.inject_registry_ceiling(4))
    recovered = _ok(fixture.flake_read(retryability="after-condition"))
    assert recovered.attempt_ids == (1, 2)
    assert recovered.stop_reason is HostRetryStopReason.SUCCESS
    assert recovered.retryability == "after-condition"
    assert recovered.operator_paged is False

    terminal = JKit06Fixture()
    _ok(terminal.inject_registry_ceiling(4))
    stopped = _ok(terminal.flake_read(retryability=Retryability.NO))
    assert stopped.attempt_ids == (1,)
    assert stopped.stop_reason is HostRetryStopReason.RETRYABILITY_NO
    assert stopped.operator_paged is False


def test_external_egress_without_receipt_is_unknown_no_second_send() -> None:
    fixture = JKit06Fixture()
    _ok(fixture.inject_registry_ceiling(4))
    lost = _ok(fixture.send_external_egress())
    assert lost.send_count == 1
    assert lost.attempt_ids == (1,)
    assert lost.stop_reason is HostRetryStopReason.UNKNOWN
    assert lost.disposition == "unknown"
    assert lost.handle_state == "unknown"
    assert lost.receipt is False
    assert lost.second_send is False
    assert lost.operator_paged is False
    body = dict(lost.to_payload())
    assert body["journey"] == J_KIT_06
    assert body["send_count"] == 1
    assert body["second_send"] is False

    second = fixture.second_send()
    assert is_refusal(second)
    assert BlindRetryRefused.matches(second)
    assert second.context["effect_class"] == "external-egress"
    assert second.context.get("blind_retry") is False
    assert is_refusal(refuse_blind_j_kit_06_second_send())

    acked = JKit06Fixture()
    _ok(acked.inject_registry_ceiling(4))
    receipted = _ok(acked.send_external_egress(receipt={"ack": "ok"}))
    assert receipted.receipt is True
    assert receipted.stop_reason is HostRetryStopReason.SUCCESS
    assert receipted.send_count == 1
    assert receipted.second_send is False


def test_fixture_invents_no_ceiling_number_tests_inject_registry_value() -> None:
    registry = GovernedVariableRegistry.with_builtins()
    row = _ok(registry.get(HOST_RETRY_ATTEMPT_CEILING_KEY))
    assert row.registry_key == HOST_RETRY_ATTEMPT_CEILING_REGISTRY_KEY
    assert row.default is None
    assert row.default != 3
    assert INVENTED_CEILING_NUMBER is None
    fixture = JKit06Fixture(variables=registry)
    unfilled = fixture.attempt_ceiling()
    assert is_refusal(unfilled)
    assert unfilled.context["invented_default"] is False
    injected = _ok(fixture.inject_registry_ceiling(4))
    assert injected == 4
    assert _ok(fixture.attempt_ceiling()) == 4
    recovered = _ok(fixture.flake_read(retryability="yes", succeed_on=2))
    assert recovered.attempt_ids == (1, 2)
    assert recovered.operator_paged is False
    other = JKit06Fixture()
    _ok(other.inject_registry_ceiling(2))
    again = _ok(other.flake_read())
    assert again.attempt_ids == (1, 2)


def test_hardcoding_three_fails_the_fixture() -> None:
    fixture = JKit06Fixture()
    invented = fixture.invent_ceiling_number(3)
    assert is_refusal(invented)
    assert invented.context["branch"] == "C"
    assert invented.context["hardcoded_three"] is False
    assert invented.context["invented_default"] is False
    assert invented.context["gap_0108"] is True
    assert invented.context["invented_number"] is None
    assert is_refusal(refuse_invented_ceiling_number(value=3))
    also = fixture.invent_ceiling_number(5)
    assert is_refusal(also)
    assert also.context["branch"] == "C"

    source = _SRC.read_text(encoding="utf-8")
    retry_text = _RETRY_SRC.read_text(encoding="utf-8")
    variables_text = _VARIABLES_SRC.read_text(encoding="utf-8")
    assert "DEFAULT_ATTEMPT_CEILING = 3" not in source
    assert "injected_ceiling: int = 3" not in source
    assert "injected_ceiling=3" not in source
    assert "registry_ceiling: int = 3" not in source
    assert "CEILING = 3" not in source
    assert "DEFAULT_ATTEMPT_CEILING = 3" not in retry_text
    assert "injected_ceiling: int = 3" not in retry_text
    ceiling_block = variables_text.split(HOST_RETRY_ATTEMPT_CEILING_KEY, 1)[1][:400]
    assert "default=3" not in ceiling_block


def test_module_never_imports_qmb() -> None:
    source = _SRC.read_text(encoding="utf-8")
    assert "import qmb" not in source
    assert "from qmb" not in source
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    assert not any(name == "qmb" or name.startswith("qmb.") for name in imports)


def test_reference_usage_example_runs() -> None:
    namespace = runpy.run_path(str(_EXAMPLE))
    main = cast("object", namespace["main"])
    assert callable(main)
    main()
