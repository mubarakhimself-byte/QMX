"""Expected QMB result context in the daemon's declared artifact sink.

These immutable CT-11 artifacts are operational metadata, not QMB completion
evidence. Their fp1 references are attached to the durable JobHandle before the
child starts and reopened only through the configured QMF AppendStore.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import cast

from qmf.core import Fingerprint, Ok, Result, World, is_refusal
from qmf.data.store import AppendStore
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "read_expected_context",
    "read_verified_context",
    "write_expected_context",
    "write_verified_context",
]

_JOB_ID = re.compile(r"[A-Za-z0-9._:-]{1,240}\Z")
_FP1 = re.compile(r"fp1:sha256:[0-9a-f]{64}\Z")
_MAX_BYTES = 262_144


def _canonical(value: Mapping[str, object]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":")).encode("utf-8")


def _admit_store(store: object) -> Result[AppendStore]:
    if type(store) is not AppendStore or store.world is not World.LIVE:
        return invalid_input(
            "artifact_store", "expected-context artifacts use the daemon's live CT-11 store"
        )
    return Ok(store)


def _validate_job(job_id: object) -> Result[str]:
    if not isinstance(job_id, str) or _JOB_ID.fullmatch(job_id) is None:
        return invalid_input("job_id", "expected context uses a safe durable job id")
    return Ok(job_id)


def _write_record(
    *, store: AppendStore, class_name: str, job_id: str, body: Mapping[str, object]
) -> Result[Mapping[str, str]]:
    try:
        base = dict(body)
        base["class"] = class_name
        base["format_version"] = 1
        base["job_id"] = job_id
        stamp = hashlib.sha256(_canonical(base)).hexdigest()
        stored = {**base, "sha256": stamp}
        if len(_canonical(stored)) > _MAX_BYTES:
            return invalid_input("artifact", "expected-context artifact stays size bounded")
        receipt = store.append_raw([stored])
    except (TypeError, ValueError) as exc:
        return invalid_input(
            "artifact", "expected-context artifact is canonical JSON", error=str(exc)
        )
    if is_refusal(receipt):
        return receipt
    return Ok({"fp1": receipt.value.fingerprint.value, "sha256": stamp})


def _read_record(
    *, store: AppendStore, reference_fp1: object, class_name: str, job_id: str
) -> Result[Mapping[str, object]]:
    if not isinstance(reference_fp1, str) or _FP1.fullmatch(reference_fp1) is None:
        return invalid_input("artifact_ref", "durable artifact reference is canonical fp1")
    key = Fingerprint.try_create(reference_fp1)
    if is_refusal(key):
        return key
    rows = store.read_raw(key.value, for_world=World.LIVE)
    if is_refusal(rows):
        return rows
    if len(rows.value) != 1:
        return policy_rejection("artifact", "expected-context reference resolves one object row")
    stored = dict(cast(Mapping[str, object], rows.value[0]))
    digest = stored.pop("sha256", None)
    if (
        stored.get("class") != class_name
        or type(stored.get("format_version")) is not int
        or stored.get("format_version") != 1
        or stored.get("job_id") != job_id
        or not isinstance(digest, str)
        or hashlib.sha256(_canonical(stored)).hexdigest() != digest
    ):
        return policy_rejection("artifact", "expected-context artifact schema and digest verify")
    stored["sha256"] = digest
    return Ok(stored)


def write_expected_context(
    *, store: object, job_id: object, payload: object
) -> Result[Mapping[str, str]]:
    """Persist the exact pre-execution context as one immutable CT-11 artifact."""
    checked_store = _admit_store(store)
    if is_refusal(checked_store):
        return checked_store
    checked_job = _validate_job(job_id)
    if is_refusal(checked_job):
        return checked_job
    if not isinstance(payload, Mapping):
        return invalid_input("expected_context", "expected context is an object")
    body = dict(cast(Mapping[str, object], payload))
    if body.get("job_id") != checked_job.value:
        return invalid_input("job_id", "context payload matches its durable key")
    return _write_record(
        store=checked_store.value,
        class_name="qma-qmb-expected-context-v1",
        job_id=checked_job.value,
        body=body,
    )


def read_expected_context(
    *, store: object, reference_fp1: object, job_id: object
) -> Result[Mapping[str, object]]:
    """Reopen and verify the expected context by its JobHandle artifact reference."""
    checked_store = _admit_store(store)
    if is_refusal(checked_store):
        return checked_store
    checked_job = _validate_job(job_id)
    if is_refusal(checked_job):
        return checked_job
    return _read_record(
        store=checked_store.value,
        reference_fp1=reference_fp1,
        class_name="qma-qmb-expected-context-v1",
        job_id=checked_job.value,
    )


def write_verified_context(
    *,
    store: object,
    job_id: object,
    expected_reference_fp1: object,
    expected_sha256: object,
    result: object,
) -> Result[Mapping[str, str]]:
    """Persist QMB's independently reopened terminal result as another CT-11 artifact."""
    checked_store = _admit_store(store)
    if is_refusal(checked_store):
        return checked_store
    checked_job = _validate_job(job_id)
    if is_refusal(checked_job):
        return checked_job
    if (
        not isinstance(expected_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
    ):
        return invalid_input("expected_sha256", "verification links to the exact expected context")
    if not isinstance(result, Mapping):
        return invalid_input("verified_result", "QMB verification result is an object")
    expected = read_expected_context(
        store=checked_store.value,
        reference_fp1=expected_reference_fp1,
        job_id=checked_job.value,
    )
    if is_refusal(expected) or expected.value.get("sha256") != expected_sha256:
        return policy_rejection(
            "expected_sha256", "verification references the intact expected-context artifact"
        )
    result_map = cast(Mapping[str, object], result)
    expected_result = expected.value.get("expected_result")
    expected_result_map: Mapping[str, object] = (
        cast(Mapping[str, object], expected_result)
        if isinstance(expected_result, Mapping)
        else dict[str, object]()
    )
    study_matches = (
        expected_result_map.get("class") == "qmb-operator-alternative-study-result-v1"
        and result_map.get("class") == expected_result_map.get("class")
        and result_map.get("study_fp1") == expected_result_map.get("study_fp1")
        and result_map.get("operational_fp1") == expected_result_map.get("operational_fp1")
    )
    if not study_matches and result_map.get("job_id") != checked_job.value:
        return invalid_input("job_id", "verified result matches its durable QMA job")
    return _write_record(
        store=checked_store.value,
        class_name="qma-qmb-verified-context-v1",
        job_id=checked_job.value,
        body={
            "expected_fp1": expected_reference_fp1,
            "expected_sha256": expected_sha256,
            "result": dict(result_map),
        },
    )


def read_verified_context(
    *,
    store: object,
    reference_fp1: object,
    job_id: object,
    expected_reference_fp1: object,
    expected_sha256: object,
) -> Result[Mapping[str, object]]:
    """Read a verified result referenced by a COMPLETE JobHandle artifact row."""
    checked_store = _admit_store(store)
    if is_refusal(checked_store):
        return checked_store
    checked_job = _validate_job(job_id)
    if is_refusal(checked_job):
        return checked_job
    record = _read_record(
        store=checked_store.value,
        reference_fp1=reference_fp1,
        class_name="qma-qmb-verified-context-v1",
        job_id=checked_job.value,
    )
    if is_refusal(record):
        return record
    if (
        record.value.get("expected_fp1") != expected_reference_fp1
        or record.value.get("expected_sha256") != expected_sha256
        or not isinstance(record.value.get("result"), Mapping)
    ):
        return policy_rejection("verified_context", "verification binds the exact expected context")
    return Ok(dict(record.value))
