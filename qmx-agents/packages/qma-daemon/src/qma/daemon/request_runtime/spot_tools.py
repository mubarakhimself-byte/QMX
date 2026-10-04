"""Host-injected read-only spot operation; no venue or node import/authority.

Normal daemon composition also publishes this read descriptor when an operator
has configured a retained QMN view. No submit/cancel is exposed to any agent.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

from qma.core.operations import OperationDescriptor
from qma.daemon.sessions.product_session import ProductSessionService
from qma.wire.invocation_envelope import (
    ContributionRecord,
    InstanceRecord,
    PublicCallTransport,
)
from qmf.core import Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection


def spot_query_descriptor() -> OperationDescriptor:
    parsed = OperationDescriptor.from_payload(
        {
            "op_id": "qmn.spot.paper.query",
            "owner": "COMP-QMN",
            "version": 1,
            "input_schema": "qmn.spot.paper.query.v1",
            "output_shape": "value",
            "input_cardinality": "one",
            "output_cardinality": "one",
            "empty_policy": "refuse",
            "configuration": {
                "defaults": {},
                "required_keys": ["account_id", "provider_connection_id", "venue_id"],
                "optional_keys": [],
            },
            "declared_operation_dependencies": [],
            "resource_needs": {
                "occupancy": "query",
                "memory_class": "light",
                "requires_environment": False,
            },
            "documentation_refs": ["release/evidence/spot-paper-design.md"],
            "validation_class": "schema+semantic",
            "units": None,
            "compatibility": {"qmn": ">=0.1"},
            "effect_class": "read",
            "permission_requests": ["evidence.read"],
            "placement": "node",
            "error_refusal_shape": {
                "family": "CT-04",
                "codes": [
                    "INVALID_INPUT",
                    "UNAVAILABLE",
                    "UNSUPPORTED_DOOR",
                    "STALE_OBSERVATION",
                    "GRANT_MISMATCH",
                ],
            },
            "progress": False,
            "lifecycle_verbs": ["query-state"],
            "supported_doors": [
                {"adapter": "library", "door": "qmn.spot.paper.query"},
                {"adapter": "qma-wire", "door": "start_mission"},
            ],
        }
    )
    if is_refusal(parsed):
        raise ValueError(f"spot descriptor violates the operation contract: {parsed}")
    return parsed.value


@dataclass(frozen=True, slots=True)
class SpotQueryDoor:
    """The host pins account/config/callback; callers only supply data/envelope."""

    sessions: ProductSessionService
    provider_connection_id: str
    venue_id: str
    account_id: str
    contribution: ContributionRecord
    instance: InstanceRecord
    read: Callable[[], Result[Mapping[str, object]]]

    def invoke(
        self, product_session_id: str, *, envelope: object, payload: object, now: str
    ) -> Result[Mapping[str, object]]:
        if not isinstance(payload, Mapping):
            return invalid_input("payload", "spot query requires an object")
        expected = {
            "provider_connection_id": self.provider_connection_id,
            "venue_id": self.venue_id,
            "account_id": self.account_id,
        }
        if dict(cast("Mapping[str, object]", payload)) != expected:
            return policy_rejection("account_scope", "query cannot retarget its host-owned account")
        descriptor = spot_query_descriptor()
        result: list[Result[Mapping[str, object]]] = []

        def execute(_bound: object) -> None:
            result.append(self.read())

        accepted = self.sessions.dispatch_public_call(
            product_session_id,
            transport=PublicCallTransport.IN_PROCESS,
            envelope=envelope,
            payload=expected,
            now=now,
            contributions={self.contribution.as_tuple(): self.contribution},
            descriptors={descriptor.door_key: descriptor},
            instances={(self.instance.instance_id, self.instance.config_revision): self.instance},
            execute=execute,
        )
        if is_refusal(accepted):
            return accepted
        return (
            result[0] if result else policy_rejection("dispatch", "read callback was not executed")
        )
