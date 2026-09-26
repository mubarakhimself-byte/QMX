"""Story 65.5 / J-KIT-06 — thin host-retry kit-journey fixture.

J-KIT-06: a ``read`` op flakes with typed retryability that is not ``NO``.
The host retries. The operator is not paged. An ``external-egress`` without
a receipt becomes ``unknown`` with no second send. Stories invent no
ceiling number (GAP-0108). Tests may inject a registry value (AR-PG-10).
Hardcoding ``3`` as the sitting's cap fails (SCN-0026 Branch C).

Given Stories 62.1–62.3. Class/test existence is not e2e at inspect SHA
``34c148b`` (DEC-0465; SCN-0026 Branch D). Does not fill GAP-0081 chrome.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Literal

from qma.core.operations import public_operation_descriptors
from qma.core.operations.descriptor import OperationDescriptor
from qma.core.operations.effects import parse_retryability
from qma.core.ports.copilot import GAP_0081_CHROME_FILLED
from qma.core.refusals.variants import BlindRetryRefused
from qma.core.vocabulary.enums import JobHandleState
from qma.daemon.journal.variables import (
    HOST_RETRY_ATTEMPT_CEILING_KEY,
    HOST_RETRY_ATTEMPT_CEILING_REGISTRY_KEY,
    GovernedVariableRegistry,
)
from qma.daemon.retry import (
    BLIND_EXTERNAL_EGRESS_RETRY,
    EFFECT_CLASS_TYPES_EXISTED_AT_INSPECT_SHA,
    HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA,
    HOST_RETRY_LOOP_OWNER,
    OPERATOR_IS_RECOVERY_LOOP,
    HostRetryLoop,
    HostRetryStopReason,
)
from qma.daemon.sessions.copilot import CopilotHost
from qma.wire import compute_input_hash
from qma.wire.invocation_envelope import InvocationEnvelope
from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "BLIND_EXTERNAL_EGRESS_RETRY",
    "EFFECT_CLASS_TYPES_EXISTED_AT_INSPECT_SHA",
    "GAP_0081_CHROME_FILLED",
    "HOST_RETRY_ATTEMPT_CEILING_KEY",
    "HOST_RETRY_ATTEMPT_CEILING_REGISTRY_KEY",
    "HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA",
    "HOST_RETRY_LOOP_OWNER",
    "INVENTED_CEILING_NUMBER",
    "J_KIT_06",
    "KIT_JOURNEY_06_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_06_INSPECT_SHA",
    "KIT_JOURNEY_06_OWNER",
    "OPERATOR_IS_RECOVERY_LOOP",
    "OPERATOR_PAGED_FOR_READ_FLAKE",
    "JKit06EgressReport",
    "JKit06Fixture",
    "JKit06ReadRetryReport",
    "claim_j_kit_06_e2e_at_inspect_sha",
    "refuse_blind_j_kit_06_second_send",
    "refuse_gap_0081_retry_chrome",
    "refuse_invented_ceiling_number",
    "refuse_operator_paged_for_read_flake",
]


J_KIT_06: Final[str] = "J-KIT-06"
KIT_JOURNEY_06_OWNER: Final[str] = HOST_RETRY_LOOP_OWNER
KIT_JOURNEY_06_INSPECT_SHA: Final[str] = "34c148b"
KIT_JOURNEY_06_E2E_AT_INSPECT_SHA: Final[bool] = False
OPERATOR_PAGED_FOR_READ_FLAKE: Final[bool] = False
# GAP-0108: registry row exists; this fixture mints no number.
INVENTED_CEILING_NUMBER: Final[None] = None
_OP_ID: Final[str] = "qmb.analysis.project"
_INSTANCE_ID: Final[str] = "inst:1"
_CONFIG_REVISION: Final[int] = 4
_GRANT_ID: Final[str] = "grant:j-kit-06"
_READ_INV: Final[str] = "inv:j-kit-06-read"
_EGRESS_INV: Final[str] = "inv:j-kit-06-egress"
_INPUT: Final[Mapping[str, str]] = MappingProxyType({"run_fp1": "run-1"})
_CONTRIBUTION: Final[Mapping[str, str]] = MappingProxyType(
    {"package_version": "0.1.0", "qualified_id": "research-corpus:inspect"}
)


def refuse_operator_paged_for_read_flake(**extra: object) -> TypedRefusal:
    """SCN-0026 Then 1 — ordinary read flakes retry in the host; operator is not paged."""
    extra.setdefault("operator_paged", OPERATOR_PAGED_FOR_READ_FLAKE)
    extra.setdefault("operator_is_recovery_loop", OPERATOR_IS_RECOVERY_LOOP)
    extra.setdefault("journey", J_KIT_06)
    extra.setdefault("branch", "1")
    return policy_rejection(
        str(extra.pop("field", "operator")),
        "ordinary read flakes retry in the host; the operator is not paged "
        "(J-KIT-06; SCN-0026 Then 1; DEC-0457)",
        **extra,
    )


def refuse_blind_j_kit_06_second_send(
    *,
    logical_invocation_id: str = _EGRESS_INV,
    **extra: object,
) -> BlindRetryRefused:
    """SCN-0026 Then 2 / Branch B — no second send without a receipt."""
    extra.setdefault("branch", "B")
    extra.setdefault("second_send", False)
    extra.setdefault("blind_retry", BLIND_EXTERNAL_EGRESS_RETRY)
    extra.setdefault("journey", J_KIT_06)
    return BlindRetryRefused.of(
        logical_invocation_id=logical_invocation_id,
        reconcile_policy="query-then-decide",
        **extra,
    )


def refuse_invented_ceiling_number(**extra: object) -> TypedRefusal:
    """SCN-0026 Branch C — stories mint no ceiling number (GAP-0108)."""
    extra.setdefault("branch", "C")
    extra.setdefault("invented_default", False)
    extra.setdefault("invented_number", INVENTED_CEILING_NUMBER)
    extra.setdefault("hardcoded_three", False)
    extra.setdefault("gap_0108", True)
    extra.setdefault("journey", J_KIT_06)
    extra.setdefault("registry_key", HOST_RETRY_ATTEMPT_CEILING_REGISTRY_KEY)
    extra.setdefault("default", None)
    return policy_rejection(
        str(extra.pop("field", "attempt_ceiling")),
        "stories invent no ceiling number; tests may inject a registry value "
        "(GAP-0108; cheap-veto A9; SCN-0026 Branch C; AR-PG-10; NFR-PG-13)",
        **extra,
    )


def refuse_gap_0081_retry_chrome(**extra: object) -> TypedRefusal:
    """J-KIT-06 does not fill GAP-0081 chrome (FR-PG-42)."""
    extra.setdefault("gap_0081_chrome_filled", GAP_0081_CHROME_FILLED)
    extra.setdefault("journey", J_KIT_06)
    return policy_rejection(
        str(extra.pop("field", "chrome")),
        "J-KIT-06 does not fill GAP-0081 chrome (FR-PG-40; FR-PG-42)",
        **extra,
    )


def claim_j_kit_06_e2e_at_inspect_sha(claimed: object) -> Result[bool]:
    """Class/test existence is not e2e at inspect SHA ``34c148b``."""
    if claimed is True or claimed == "true":
        return policy_rejection(
            "e2e",
            "J-KIT-06 fixtures are not e2e adoption at inspect SHA 34c148b; "
            "the host retry loop was absent there (DEC-0465; SCN-0026 "
            "Branch D; FR-PG-40)",
            claimed=True,
            e2e_at_inspect_sha=False,
            inspect_sha=KIT_JOURNEY_06_INSPECT_SHA,
            class_test_existence_is_e2e=False,
            host_retry_loop_existed_at_inspect_sha=HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA,
            effect_class_types_existed_at_inspect_sha=EFFECT_CLASS_TYPES_EXISTED_AT_INSPECT_SHA,
            gap_0081_chrome_filled=GAP_0081_CHROME_FILLED,
            journey=J_KIT_06,
            branch="D",
        )
    if claimed is not False:
        return invalid_input(
            "e2e_at_inspect_sha",
            "inspect-SHA e2e claim is a boolean",
            given=repr(claimed),
        )
    return Ok(False)


def _descriptor() -> Result[OperationDescriptor]:
    for item in public_operation_descriptors():
        if item.op_id == _OP_ID and item.version == 1:
            return Ok(item)
    return invalid_input("op_id", "qmb.analysis.project v1 missing")


def _flake(retryability: Retryability, *, reason: str = "flake") -> TypedRefusal:
    extra: dict[str, object] = {"reason": reason, "journey": J_KIT_06}
    if retryability is Retryability.AFTER_CONDITION:
        return TypedRefusal(
            category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
            retryability=retryability,
            context=extra,
            after_condition_descriptor="dependency-returns",
        )
    return TypedRefusal(
        category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
        retryability=retryability,
        context=extra,
    )


@dataclass(frozen=True, slots=True)
class JKit06ReadRetryReport:
    """J-KIT-06: host retried a flaking ``read``; operator was not paged."""

    logical_invocation_id: str
    attempt_ids: tuple[int, ...]
    attempt_id: int
    stop_reason: HostRetryStopReason
    retryability: str
    operator_paged: Literal[False] = False
    operator_is_recovery_loop: Literal[False] = False
    value: object | None = None

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "attempt_id": self.attempt_id,
                "attempt_ids": list(self.attempt_ids),
                "journey": J_KIT_06,
                "logical_invocation_id": self.logical_invocation_id,
                "operator_is_recovery_loop": self.operator_is_recovery_loop,
                "operator_paged": self.operator_paged,
                "retryability": self.retryability,
                "stop_reason": self.stop_reason.value,
            }
        )


@dataclass(frozen=True, slots=True)
class JKit06EgressReport:
    """J-KIT-06: ``external-egress`` without a receipt is ``unknown``."""

    logical_invocation_id: str
    attempt_ids: tuple[int, ...]
    send_count: int
    stop_reason: HostRetryStopReason
    disposition: str
    handle_state: str
    receipt: bool
    second_send: Literal[False] = False
    operator_paged: Literal[False] = False

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "attempt_ids": list(self.attempt_ids),
                "disposition": self.disposition,
                "handle_state": self.handle_state,
                "journey": J_KIT_06,
                "logical_invocation_id": self.logical_invocation_id,
                "operator_paged": self.operator_paged,
                "receipt": self.receipt,
                "second_send": self.second_send,
                "send_count": self.send_count,
                "stop_reason": self.stop_reason.value,
            }
        )


@dataclass
class JKit06Fixture:
    """Read flakes retry in the host; external-egress has no second send."""

    variables: GovernedVariableRegistry = field(
        default_factory=GovernedVariableRegistry.with_builtins
    )
    loop: HostRetryLoop = field(init=False)
    host: CopilotHost = field(init=False)
    _injected_ceiling: int | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._bind_loop()

    def _bind_loop(self) -> None:
        self.loop = HostRetryLoop(
            variables=self.variables,
            injected_ceiling=self._injected_ceiling,
        )
        self.host = CopilotHost(retry_loop=self.loop)

    @property
    def owner(self) -> str:
        return KIT_JOURNEY_06_OWNER

    @property
    def journey(self) -> str:
        return J_KIT_06

    @property
    def e2e_at_inspect_sha(self) -> bool:
        return KIT_JOURNEY_06_E2E_AT_INSPECT_SHA

    @property
    def operator_paged(self) -> bool:
        return OPERATOR_PAGED_FOR_READ_FLAKE

    @property
    def invented_ceiling_number(self) -> None:
        return INVENTED_CEILING_NUMBER

    def attempt_ceiling(self) -> Result[int]:
        """Host-registered ceiling. Unfilled until a test injects a registry value."""
        return self.loop.attempt_ceiling()

    def inject_registry_ceiling(self, value: object) -> Result[int]:
        """AR-PG-10: tests may inject a host-registered ceiling. Production mints none."""
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            return invalid_input(
                "attempt_ceiling",
                "tests may inject a positive host-registered ceiling (AR-PG-10); "
                "production mints no number (GAP-0108)",
                given=repr(value),
                invented_default=False,
                registry_key=HOST_RETRY_ATTEMPT_CEILING_REGISTRY_KEY,
                journey=J_KIT_06,
            )
        # AR-PG-10: tests inject a host-registered value. Production default stays None.
        self._injected_ceiling = value
        self._bind_loop()
        return Ok(value)

    def invent_ceiling_number(self, value: object) -> TypedRefusal:
        """SCN-0026 Branch C — hardcoding a sitting-invented cap fails the fixture."""
        return refuse_invented_ceiling_number(given=repr(value), value=value)

    def page_operator(self) -> TypedRefusal:
        """Ordinary hiccups are not a page (SCN-0026 Then 1)."""
        return refuse_operator_paged_for_read_flake()

    def fill_gap_0081_chrome(self) -> TypedRefusal:
        return refuse_gap_0081_retry_chrome()

    def flake_read(
        self,
        *,
        retryability: object = "yes",
        succeed_on: int | None = None,
        logical_invocation_id: str = _READ_INV,
    ) -> Result[JKit06ReadRetryReport]:
        """Host-retry a flaking ``read`` on one ``logical_invocation_id``."""
        parsed = parse_retryability(retryability)
        if is_refusal(parsed):
            return parsed
        token = parsed.value
        recover_at = succeed_on if succeed_on is not None else 2

        def call(envelope: InvocationEnvelope) -> Result[object]:
            if token is Retryability.NO:
                return _flake(Retryability.NO, reason="terminal")
            if envelope.attempt_id < recover_at:
                return _flake(token)
            return Ok({"ok": True})

        envelope = self._envelope(
            effect_class="read",
            logical_invocation_id=logical_invocation_id,
        )
        if is_refusal(envelope):
            return envelope
        ran = self.host.retry_public_call(envelope.value, call)
        if is_refusal(ran):
            return ran
        outcome = ran.value
        return Ok(
            JKit06ReadRetryReport(
                logical_invocation_id=outcome.logical_invocation_id,
                attempt_ids=outcome.attempt_ids,
                attempt_id=outcome.attempt_id,
                stop_reason=outcome.stop_reason,
                retryability=token.value,
                operator_paged=False,
                operator_is_recovery_loop=False,
                value=outcome.value,
            )
        )

    def send_external_egress(
        self,
        *,
        receipt: object | None = None,
        logical_invocation_id: str = _EGRESS_INV,
    ) -> Result[JKit06EgressReport]:
        """One ``external-egress`` send. Missing receipt is ``unknown``."""

        def call(_envelope: InvocationEnvelope) -> Result[object]:
            if receipt is not None:
                return Ok({"order": "acked", "receipt": receipt})
            return Ok({"order": "maybe-sent"})

        envelope = self._envelope(
            effect_class="external-egress",
            logical_invocation_id=logical_invocation_id,
        )
        if is_refusal(envelope):
            return envelope
        ran = self.host.retry_public_call(envelope.value, call, receipt=receipt)
        if is_refusal(ran):
            return ran
        outcome = ran.value
        effect = outcome.effect_outcome
        handle_state = (
            effect.handle_state.value
            if effect is not None and effect.handle_state is not None
            else JobHandleState.UNKNOWN.value
        )
        disposition = effect.disposition if effect is not None else "unknown"
        got_receipt = bool(effect.receipt) if effect is not None else False
        return Ok(
            JKit06EgressReport(
                logical_invocation_id=outcome.logical_invocation_id,
                attempt_ids=outcome.attempt_ids,
                send_count=len(outcome.attempt_ids),
                stop_reason=outcome.stop_reason,
                disposition=disposition,
                handle_state=handle_state,
                receipt=got_receipt,
                second_send=False,
                operator_paged=False,
            )
        )

    def second_send(
        self,
        *,
        logical_invocation_id: str = _EGRESS_INV,
        attempt_id: int = 2,
    ) -> Result[JKit06EgressReport]:
        """Blind second ``external-egress`` send is refused (SCN-0026 Branch B)."""

        def boom(_envelope: InvocationEnvelope) -> Result[object]:
            raise AssertionError("J-KIT-06 must not blind-retry external-egress")

        envelope = self._envelope(
            effect_class="external-egress",
            logical_invocation_id=logical_invocation_id,
            attempt_id=attempt_id,
        )
        if is_refusal(envelope):
            return envelope
        ran = self.host.retry_public_call(envelope.value, boom)
        if is_refusal(ran):
            return ran
        return refuse_blind_j_kit_06_second_send(logical_invocation_id=logical_invocation_id)

    def _envelope(
        self,
        *,
        effect_class: str,
        logical_invocation_id: str,
        attempt_id: int = 1,
    ) -> Result[dict[str, object]]:
        descriptor = _descriptor()
        if is_refusal(descriptor):
            return descriptor
        hashed = compute_input_hash(_INPUT, descriptor=descriptor.value)
        if is_refusal(hashed):
            return hashed
        payload: dict[str, object] = {
            "logical_invocation_id": logical_invocation_id,
            "attempt_id": attempt_id,
            "op_id": _OP_ID,
            "op_version": 1,
            "contribution": dict(_CONTRIBUTION),
            "instance_id": _INSTANCE_ID,
            "config_revision": _CONFIG_REVISION,
            "grant_id": _GRANT_ID,
            "effect_class": effect_class,
            "idempotency_key": f"idem:{logical_invocation_id}",
            "reconcile_policy": "query-then-decide",
            "input_hash": hashed.value,
            "call_depth": 0,
            "caller_kind": "user",
        }
        return Ok(payload)
