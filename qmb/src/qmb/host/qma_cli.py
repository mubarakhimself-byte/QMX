"""Validate the trusted QMA-to-QMB CLI envelope before operator resolution."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from qmf.core import Fingerprint, Ok, Result, World

from qmb._refuse import invalid, policy

__all__ = [
    "QmaBacktestContext",
    "decode_qma_backtest_context",
    "validate_qma_backtest_context",
]

_OWNED_CONCERNS = ("artifact_contract", "intra_node_parallelism", "run_ledger")
_ROUTE = ("agent", "qma_backtest_tool", "backtesting_service", "qmb_door", "qmb")
_REQUIRED_PAYLOAD_KEYS = frozenset(
    {
        "job_id",
        "attempt_id",
        "experiment_spec_fp1",
        "evidence_ref",
        "environment_ref",
        "occupancy_key",
        "world",
        "recorded",
        "import_edge",
        "owned_by",
        "qma_re_specifies",
        "qmb_owned",
        "route",
        "command",
        "occupancy",
        "mints_ct32",
        "mints_experiment_spec",
        "children_are_qma_jobs",
        "opens_daemon_sqlite",
        "split_manifest_fp1",
        "operator_descriptor_fp1",
    }
)


@dataclass(frozen=True, slots=True)
class QmaBacktestContext:
    """Validated identifiers QMA may carry to the existing QMB backtest door."""

    job_id: str
    attempt_id: int
    experiment_spec_fp1: Fingerprint
    evidence_ref: Fingerprint
    split_manifest_fp1: Fingerprint
    environment_ref: str
    occupancy_key: str
    mints_ct32: bool = True
    operator_descriptor_fp1: Fingerprint | None = None
    command: str = "backtest.run"


def validate_qma_backtest_context(context: object) -> Result[QmaBacktestContext]:
    """Revalidate the decoded CT-47 value at every public runtime boundary.

    Frozen dataclasses can still be constructed directly or altered with
    ``dataclasses.replace``. A nominal instance therefore carries no validation
    authority by itself.
    """

    if type(context) is not QmaBacktestContext:
        return invalid("qma_context", "the QMB runtime receives a decoded CT-47 context")
    value = context
    if type(value.command) is not str or value.command not in {"backtest.run", "optimize.run"}:
        return policy("command", "delegated QMB runs use the backtest or Study door")
    if value.command == "optimize.run" and value.mints_ct32 is not False:
        return policy("mints_ct32", "Alternative Study is explicitly non-CT-32")
    for field, item in (
        ("job_id", value.job_id),
        ("environment_ref", value.environment_ref),
        ("occupancy_key", value.occupancy_key),
    ):
        if type(item) is not str or not item.strip():
            return invalid(
                field,
                "delegated job, environment, and occupancy IDs are non-empty text",
            )
    if type(value.attempt_id) is not int or value.attempt_id < 1:
        return invalid("attempt_id", "the delegated QMA attempt is a positive integer")
    if type(value.mints_ct32) is not bool:
        return invalid("mints_ct32", "the delegated result mode is an exact boolean")
    for field in ("experiment_spec_fp1", "evidence_ref", "split_manifest_fp1"):
        item = getattr(value, field)
        if type(item) is not Fingerprint:
            return invalid(field, "the delegated registered reference is an fp1 Fingerprint")
        parsed = Fingerprint.try_create(item.value)
        if not isinstance(parsed, Ok) or parsed.value != item:
            return invalid(field, "the delegated registered reference is a valid fp1 Fingerprint")
    descriptor = value.operator_descriptor_fp1
    if descriptor is not None:
        if type(descriptor) is not Fingerprint:
            return invalid(
                "operator_descriptor_fp1", "the operator runtime pin is an fp1 Fingerprint"
            )
        parsed_descriptor = Fingerprint.try_create(descriptor.value)
        if not isinstance(parsed_descriptor, Ok) or parsed_descriptor.value != descriptor:
            return invalid(
                "operator_descriptor_fp1", "the operator runtime pin is a valid fp1 Fingerprint"
            )
    return Ok(value)


def decode_qma_backtest_context(
    *, payload_text: object, environ: object
) -> Result[QmaBacktestContext]:
    """Decode only the registered run/evidence/split envelope, never runtime inputs.

    Runtime roots, config keys, Book policy, and callbacks are intentionally not
    accepted in this envelope. They come from the operator binding selected by
    the QMB process after this boundary succeeds.
    """
    if not isinstance(payload_text, str) or not isinstance(environ, Mapping):
        return invalid("qma_payload", "the delegated QMB door receives JSON and process env")
    try:
        payload = json.loads(payload_text, object_pairs_hook=_unique_object)
    except (ValueError, TypeError):
        return invalid("qma_payload", "the delegated QMB door payload is valid JSON")
    if not isinstance(payload, Mapping):
        return invalid("qma_payload", "the delegated QMB door payload is an object")
    body = cast(Mapping[str, object], payload)
    if set(body) != set(_REQUIRED_PAYLOAD_KEYS):
        return invalid(
            "qma_payload",
            "the delegated backtest envelope has the exact QMB-owned identifier fields",
            missing=sorted(_REQUIRED_PAYLOAD_KEYS.difference(body)),
            extra=sorted(set(body).difference(_REQUIRED_PAYLOAD_KEYS)),
        )
    expected_literals = {
        "world": World.REPLAY.value,
        "recorded": True,
        "import_edge": False,
        "owned_by": "qmb",
        "qma_re_specifies": False,
        "qmb_owned": list(_OWNED_CONCERNS),
        "route": list(_ROUTE),
        "occupancy": "run",
        "mints_experiment_spec": False,
        "children_are_qma_jobs": False,
        "opens_daemon_sqlite": False,
    }
    for key, expected in expected_literals.items():
        if type(body.get(key)) is not type(expected) or body.get(key) != expected:
            return policy("qma_payload", "delegated QMB command semantics are fixed", key=key)
    mints_ct32 = body.get("mints_ct32")
    command = body.get("command")
    if type(command) is not str or command not in {"backtest.run", "optimize.run"}:
        return policy("command", "delegated QMB runs use the backtest or Study door")
    if command == "optimize.run" and mints_ct32 is not False:
        return policy("mints_ct32", "Alternative Study is explicitly non-CT-32")
    if type(mints_ct32) is not bool:
        return invalid("mints_ct32", "the QMB result mode is an exact boolean")
    text_fields = ("job_id", "environment_ref", "occupancy_key")
    values: dict[str, str] = {}
    for key in text_fields:
        value = body.get(key)
        if not isinstance(value, str) or not value.strip():
            return invalid(key, "delegated QMB identifiers are non-empty text")
        values[key] = value
    attempt_id = body.get("attempt_id")
    if isinstance(attempt_id, bool) or not isinstance(attempt_id, int) or attempt_id < 1:
        return invalid("attempt_id", "the delegated QMA attempt is a positive integer")
    parsed: dict[str, Fingerprint] = {}
    for key in (
        "experiment_spec_fp1",
        "evidence_ref",
        "split_manifest_fp1",
        "operator_descriptor_fp1",
    ):
        if key == "operator_descriptor_fp1" and body.get(key) is None:
            continue
        result = Fingerprint.try_create(body.get(key))
        if isinstance(result, Ok):
            parsed[key] = result.value
        else:
            return result
    for field, env_key in (
        ("job_id", "QMA_QMB_JOB_ID"),
        ("attempt_id", "QMA_QMB_ATTEMPT_ID"),
        ("experiment_spec_fp1", "QMA_QMB_EXPERIMENT_SPEC_FP1"),
        ("evidence_ref", "QMA_QMB_EVIDENCE_REF"),
        ("split_manifest_fp1", "QMA_QMB_SPLIT_MANIFEST_FP1"),
        ("environment_ref", "QMA_QMB_ENVIRONMENT_REF"),
        ("occupancy_key", "QMA_QMB_OCCUPANCY_KEY"),
    ):
        env_value = cast(Mapping[object, object], environ).get(env_key)
        body_value = body.get(field)
        expected_env_value = str(body_value) if field == "attempt_id" else body_value
        if not isinstance(env_value, str) or env_value != expected_env_value:
            return policy(
                field,
                "JSON and dedicated process fields identify the same QMA placement",
                environment_field=env_key,
            )
    return Ok(
        QmaBacktestContext(
            job_id=values["job_id"],
            attempt_id=attempt_id,
            experiment_spec_fp1=parsed["experiment_spec_fp1"],
            evidence_ref=parsed["evidence_ref"],
            split_manifest_fp1=parsed["split_manifest_fp1"],
            environment_ref=values["environment_ref"],
            occupancy_key=values["occupancy_key"],
            mints_ct32=mints_ct32,
            operator_descriptor_fp1=parsed.get("operator_descriptor_fp1"),
            command=command,
        )
    )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value
