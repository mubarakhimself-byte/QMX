"""Host-owned retry is wired through the authenticated CT-40 product-session route."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import cast

from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.operations import OperationDescriptor, public_operation_descriptors
from qma.core.ports.execution import ExecutionEnvironmentDeclaration
from qma.core.vocabulary.enums import (
    ExecutionEnvironmentKind,
    PrincipalClass,
)
from qma.daemon.journal.variables import HOST_RETRY_ATTEMPT_CEILING_KEY
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.initialize import WIRE_PROTOCOL_VERSION, WireConnection
from qma.wire.invocation_envelope import BoundInvocation, compute_input_hash
from qma.wire.vocabulary import WireCommand
from qmf.core import Ok, Result, is_ok
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal


def _compose(root: Path) -> DaemonProcess:
    seed = root / "seed-corpus"
    seed.mkdir(exist_ok=True)
    result = DaemonProcess.compose(
        root,
        machine="host-retry-test",
        boot_epoch_id="boot-host-retry-test",
        bind_port=0,
        plugin_load_configs=research_corpus_plugin_load_config(seed),
    )
    assert is_ok(result), result
    return result.value


def _request(
    process: DaemonProcess,
    connection: WireConnection,
    *,
    session_id: str,
    contribution: Mapping[str, str],
    instance_id: str,
    revision: int,
    descriptor: OperationDescriptor,
    grant_id: str,
    logical_id: str,
    attempt_id: int = 1,
    payload: Mapping[str, object],
    request_id: int,
) -> dict[str, object] | None:
    descriptor_payload = descriptor.to_payload()
    input_hash = compute_input_hash(payload, descriptor=descriptor)
    assert is_ok(input_hash), input_hash
    envelope = {
        "logical_invocation_id": logical_id,
        "attempt_id": attempt_id,
        "op_id": descriptor_payload["op_id"],
        "op_version": descriptor_payload["version"],
        "contribution": dict(contribution),
        "instance_id": instance_id,
        "config_revision": revision,
        "grant_id": grant_id,
        "effect_class": descriptor_payload["effect_class"],
        "idempotency_key": f"idem:{logical_id}",
        "reconcile_policy": "query-then-decide",
        "input_hash": input_hash.value,
        "call_depth": 0,
        "caller_kind": "user",
        "caller_session_ref": session_id,
    }
    return process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
        connection,
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": WireCommand.START_MISSION.value,
                "params": {
                    "product_session_ref": session_id,
                    "envelope": envelope,
                    "payload": dict(payload),
                },
            }
        ).encode(),
        session_key="prid:host-retry-test",
        connection_token="host-retry-test-connection",
    )


def test_authenticated_read_retries_same_invocation_and_place_run_does_not_retry(
    tmp_path: Path,
) -> None:
    process = _compose(tmp_path)
    try:
        loaded = process.roster.loader.get("analysis-backtest")
        assert loaded is not None
        published = next(
            row
            for row in loaded.published
            if row.point == "tool" and row.qualified_id == "analysis-backtest:qmb"
        )
        assert published.qualified_id is not None
        assert published.package_version is not None
        contribution = {
            "qualified_id": published.qualified_id,
            "package_version": published.package_version,
        }
        descriptors = {item.op_id: item for item in public_operation_descriptors()}
        read_descriptor = descriptors["qmb.analysis.project"]
        place_descriptor = descriptors["qmb.backtest.run"]
        actor = ActorId.mint(DeskSlug.ANALYSIS, "retry-owner")
        assert is_ok(actor)
        owner = Quant(
            actor_id=actor.value,
            desk=DeskSlug.ANALYSIS,
            quant_slug="retry-owner",
            role=RoleName.ANALYST,
            name="Retry owner",
        )
        assert is_ok(process.mailboxes.open_for_quant(owner))
        assert is_ok(
            process.execution_environments.register_declaration(
                ExecutionEnvironmentDeclaration.isolated(
                    ExecutionEnvironmentKind.LOCAL,
                    provider_ref="local-host-retry-test",
                )
            )
        )
        (tmp_path / "operator-config.json").write_text(
            json.dumps(
                {
                    "qmb_bindings": {
                        loaded.instance_id: {
                            "owner_actor_id": actor.value.value,
                            "environment_ref": "env:local",
                            "config_revision": 2,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        connection = WireConnection()
        assert is_ok(connection.authenticate_pairing("prid:hostretrytest"))
        initialized = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": WIRE_PROTOCOL_VERSION,
                        "capabilities": {},
                    },
                }
            ).encode(),
            session_key="prid:host-retry-test",
            connection_token="host-retry-test-connection",
        )
        assert initialized is not None and "error" not in initialized
        opened = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "open_product_session",
                    "params": {
                        "instance_id": loaded.instance_id,
                        "qualified_id": published.qualified_id,
                        "package_version": published.package_version,
                    },
                }
            ).encode(),
            session_key="prid:host-retry-test",
            connection_token="host-retry-test-connection",
        )
        assert opened is not None and "error" not in opened
        session_id = cast(str, cast(dict[str, object], opened["result"])["product_session_id"])
        granted = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "grant_product_session",
                    "params": {
                        "product_session_ref": session_id,
                        "expected_revision": 0,
                        "op_id": read_descriptor.op_id,
                        "op_version": read_descriptor.version,
                        "parameter_ceiling": {"allow_keys": ["run_fp1"]},
                        "expires_at": "2099-01-01T00:00:00Z",
                    },
                }
            ).encode(),
            session_key="prid:host-retry-test",
            connection_token="host-retry-test-connection",
        )
        assert granted is not None and "error" not in granted
        read_grant = cast(str, cast(dict[str, object], granted["result"])["grant_id"])

        calls: list[tuple[int, str, str]] = []

        def flaky_read(
            bound: BoundInvocation,
            *,
            originating_product_session_ref: str | None = None,
        ) -> Result[object]:
            envelope = bound.envelope
            calls.append(
                (
                    envelope.attempt_id,
                    envelope.logical_invocation_id,
                    envelope.input_hash,
                )
            )
            if len(calls) == 1:
                revoked = process.product_sessions.revoke_grant(
                    session_id,
                    grant_id=read_grant,
                    principal="operator",
                    reason="accepted-read-already-in-flight",
                    revoked_at="2026-10-01T00:00:00Z",
                )
                assert is_ok(revoked), revoked
                return TypedRefusal(
                    category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                    retryability=Retryability.AFTER_CONDITION,
                    context=MappingProxyType({"reason": "transient read outage"}),
                )
            return Ok({"artifact_ref": "artifact:host-retry-read"})

        process._execute_bound_product_operation = flaky_read  # pyright: ignore[reportPrivateUsage]
        payload = {"run_fp1": "fp1:sha256:" + "a" * 64}
        missing_ceiling = _request(
            process,
            connection,
            session_id=session_id,
            contribution=contribution,
            instance_id=loaded.instance_id,
            revision=2,
            descriptor=read_descriptor,
            grant_id=read_grant,
            logical_id="inv:host-retry-read",
            payload=payload,
            request_id=4,
        )
        assert missing_ceiling is not None and "error" in missing_ceiling
        assert calls == []

        configured = process.variables.variable_set(
            HOST_RETRY_ATTEMPT_CEILING_KEY,
            2,
            principal_class=PrincipalClass.OPERATOR,
            journal=process.journal,
        )
        assert is_ok(configured), configured
        retried = _request(
            process,
            connection,
            session_id=session_id,
            contribution=contribution,
            instance_id=loaded.instance_id,
            revision=2,
            descriptor=read_descriptor,
            grant_id=read_grant,
            logical_id="inv:host-retry-read",
            payload=payload,
            request_id=5,
        )
        assert retried is not None and "error" not in retried, retried
        assert [attempt for attempt, _, _ in calls] == [1, 2]
        assert {logical for _, logical, _ in calls} == {"inv:host-retry-read"}
        assert len({input_hash for _, _, input_hash in calls}) == 1

        events = process.journal.read_events()
        assert is_ok(events), events
        attempts = [
            event.payload["attempt_id"]
            for event in events.value
            if event.event == "product_session.grant_accepted"
            and event.payload.get("logical_invocation_id") == "inv:host-retry-read"
        ]
        assert attempts == [1, 2]

        duplicate_calls: list[int] = []

        def altered_duplicate_executor(
            bound: BoundInvocation,
            *,
            originating_product_session_ref: str | None = None,
        ) -> Result[object]:
            del originating_product_session_ref
            duplicate_calls.append(bound.envelope.attempt_id)
            return Ok({"artifact_ref": "artifact:must-not-repeat"})

        process._execute_bound_product_operation = altered_duplicate_executor  # pyright: ignore[reportPrivateUsage]
        changed_duplicate = _request(
            process,
            connection,
            session_id=session_id,
            contribution=contribution,
            instance_id=loaded.instance_id,
            revision=2,
            descriptor=read_descriptor,
            grant_id=read_grant,
            logical_id="inv:host-retry-read",
            payload={"run_fp1": "fp1:sha256:" + "b" * 64},
            request_id=51,
        )
        assert changed_duplicate is not None and "error" in changed_duplicate
        assert duplicate_calls == []

        no_retry_grant = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "grant_product_session",
                    "params": {
                        "product_session_ref": session_id,
                        "expected_revision": 1,
                        "op_id": read_descriptor.op_id,
                        "op_version": read_descriptor.version,
                        "parameter_ceiling": {"allow_keys": ["run_fp1"]},
                        "expires_at": "2099-01-01T00:00:00Z",
                    },
                }
            ).encode(),
            session_key="prid:host-retry-test",
            connection_token="host-retry-test-connection",
        )
        assert no_retry_grant is not None and "error" not in no_retry_grant
        no_retry_calls: list[int] = []

        def nonretryable_read(
            bound: BoundInvocation,
            *,
            originating_product_session_ref: str | None = None,
        ) -> Result[object]:
            del originating_product_session_ref
            no_retry_calls.append(bound.envelope.attempt_id)
            return TypedRefusal(
                category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                retryability=Retryability.NO,
                context=MappingProxyType({"reason": "read is terminally unavailable"}),
            )

        process._execute_bound_product_operation = nonretryable_read  # pyright: ignore[reportPrivateUsage]
        skipped_first_attempt = _request(
            process,
            connection,
            session_id=session_id,
            contribution=contribution,
            instance_id=loaded.instance_id,
            revision=2,
            descriptor=read_descriptor,
            grant_id=cast(str, cast(dict[str, object], no_retry_grant["result"])["grant_id"]),
            logical_id="inv:host-retry-start-at-two",
            attempt_id=2,
            payload=payload,
            request_id=7,
        )
        assert skipped_first_attempt is not None and "error" in skipped_first_attempt
        assert no_retry_calls == []
        no_retry_response = _request(
            process,
            connection,
            session_id=session_id,
            contribution=contribution,
            instance_id=loaded.instance_id,
            revision=2,
            descriptor=read_descriptor,
            grant_id=cast(str, cast(dict[str, object], no_retry_grant["result"])["grant_id"]),
            logical_id="inv:host-retry-no-retry",
            payload=payload,
            request_id=8,
        )
        assert no_retry_response is not None and "error" in no_retry_response
        assert no_retry_calls == [1]

        duplicate_calls: list[int] = []

        def duplicate_success(
            bound: BoundInvocation,
            *,
            originating_product_session_ref: str | None = None,
        ) -> Result[object]:
            del originating_product_session_ref
            duplicate_calls.append(bound.envelope.attempt_id)
            return Ok({"artifact_ref": "artifact:must-not-run-again"})

        process._execute_bound_product_operation = duplicate_success  # pyright: ignore[reportPrivateUsage]
        altered_duplicate = _request(
            process,
            connection,
            session_id=session_id,
            contribution=contribution,
            instance_id=loaded.instance_id,
            revision=2,
            descriptor=read_descriptor,
            grant_id=cast(str, cast(dict[str, object], no_retry_grant["result"])["grant_id"]),
            logical_id="inv:host-retry-no-retry",
            payload={"run_fp1": "fp1:sha256:" + "c" * 64},
            request_id=9,
        )
        assert altered_duplicate is not None and "error" in altered_duplicate
        assert duplicate_calls == []

        place_grant = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 10,
                    "method": "grant_product_session",
                    "params": {
                        "product_session_ref": session_id,
                        "expected_revision": 2,
                        "op_id": place_descriptor.op_id,
                        "op_version": place_descriptor.version,
                        "parameter_ceiling": {"allow_keys": ["run_fp1"]},
                        "expires_at": "2099-01-01T00:00:00Z",
                    },
                }
            ).encode(),
            session_key="prid:host-retry-test",
            connection_token="host-retry-test-connection",
        )
        assert place_grant is not None and "error" not in place_grant
        place_grant_result = cast(dict[str, object], place_grant["result"])
        place_calls: list[int] = []

        def failed_place_run(
            bound: BoundInvocation,
            *,
            originating_product_session_ref: str | None = None,
        ) -> Result[object]:
            del originating_product_session_ref
            place_calls.append(bound.envelope.attempt_id)
            return TypedRefusal(
                category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                retryability=Retryability.AFTER_CONDITION,
                context=MappingProxyType({"reason": "place-run acknowledgement unavailable"}),
            )

        process._execute_bound_product_operation = failed_place_run  # pyright: ignore[reportPrivateUsage]
        place_response = _request(
            process,
            connection,
            session_id=session_id,
            contribution=contribution,
            instance_id=loaded.instance_id,
            revision=2,
            descriptor=place_descriptor,
            grant_id=cast(str, place_grant_result["grant_id"]),
            logical_id="inv:host-retry-place-run",
            payload={"run_fp1": "fp1:sha256:" + "b" * 64},
            request_id=11,
        )
        assert place_response is not None and "error" in place_response
        assert place_calls == [1]
    finally:
        process.close()
