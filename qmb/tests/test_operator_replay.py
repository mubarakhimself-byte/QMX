"""Operator replay descriptor is selected only by trusted CT-47 identifiers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from qmb.host.operator_replay import (
    OPERATOR_BINDING_FORMAT_VERSION,
    OPERATOR_BINDING_KIND,
    read_operator_replay_binding,
)
from qmb.host.qma_cli import QmaBacktestContext
from qmf.core import Fingerprint, Result, fingerprint, is_ok

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(value: object) -> str:
    return _ok(fingerprint(value)).value


def _context() -> QmaBacktestContext:
    return QmaBacktestContext(
        job_id="job-1",
        attempt_id=2,
        experiment_spec_fp1=_ok(Fingerprint.try_create(_fp({"spec": 1}))),
        evidence_ref=_ok(Fingerprint.try_create(_fp({"request": 1}))),
        split_manifest_fp1=_ok(Fingerprint.try_create(_fp({"split": 1}))),
        environment_ref="env-1",
        occupancy_key="qmb-backtest-run",
    )


def _descriptor(tmp_path: Path, context: QmaBacktestContext) -> dict[str, object]:
    files = {"runtime_builder.py": "def build(*args):\n    return None\n"}
    policy_identity = {"admission": "fixture-policy-v1"}
    body: dict[str, object] = {
        "class": OPERATOR_BINDING_KIND,
        "format_version": OPERATOR_BINDING_FORMAT_VERSION,
        "experiment_spec_fp1": context.experiment_spec_fp1.value,
        "evidence_ref": context.evidence_ref.value,
        "split_manifest_fp1": context.split_manifest_fp1.value,
        "holdout_months": 18,
        "record_refs": {
            "bot": _fp({"bot-record": 1}),
            "book": _fp({"book-record": 1}),
            "bms": _fp({"bms-record": 1}),
        },
        "roots": {
            name: str(tmp_path / name)
            for name in ("registry", "raw", "requests", "journal", "terminal_ledger")
        },
        "registry_as_of_ns": 1_700_000_000_000_000_000,
        "registry_writer": {
            "actor": "operator",
            "role": "registry",
            "stream": "records",
            "boot_epoch": "boot-1",
        },
        "registry_stale_evidence_severity": "refuse",
        "policy_identity": policy_identity,
        "policy_fp1": _fp(policy_identity),
        "builder_files": files,
        "builder_fp1": _fp({"class": "qmb-operator-builder-source-v1", "files": files}),
        "entrypoint": "runtime_builder:build",
    }
    body["descriptor_fp1"] = _fp(body)
    return body


def _write(root: Path, context: QmaBacktestContext, body: dict[str, object]) -> None:
    directory = root / context.experiment_spec_fp1.value.replace(":", "-")
    directory = directory / context.evidence_ref.value.replace(":", "-")
    directory.mkdir(parents=True)
    (directory / "operator-binding.json").write_text(json.dumps(body), encoding="utf-8")


def test_operator_binding_requires_exact_ct47_refs_and_pinned_policy(tmp_path: Path) -> None:
    context = _context()
    body = _descriptor(tmp_path, context)
    _write(tmp_path / "runtime", context, body)

    loaded = _ok(
        read_operator_replay_binding(
            runtime_root=str(tmp_path / "runtime"), context=context
        )
    )

    assert loaded.experiment_spec_fp1 == context.experiment_spec_fp1
    assert loaded.evidence_ref == context.evidence_ref
    assert loaded.split_manifest_fp1 == context.split_manifest_fp1
    assert loaded.holdout_months == 18
    assert loaded.entrypoint == "runtime_builder:build"
    assert loaded.policy_fp1.value == body["policy_fp1"]


def test_operator_binding_rejects_changed_or_extra_policy_content(tmp_path: Path) -> None:
    context = _context()
    body = _descriptor(tmp_path, context)
    body["policy_identity"] = {"admission": "changed"}
    _write(tmp_path / "runtime", context, body)

    result = read_operator_replay_binding(runtime_root=str(tmp_path / "runtime"), context=context)

    assert not is_ok(result)


def test_operator_binding_refuses_unregistered_ct47_request(tmp_path: Path) -> None:
    context = _context()
    body = _descriptor(tmp_path, context)
    body["evidence_ref"] = _fp({"request": "other"})
    identity = {key: value for key, value in body.items() if key != "descriptor_fp1"}
    body["descriptor_fp1"] = _fp(identity)
    _write(tmp_path / "runtime", context, body)

    result = read_operator_replay_binding(runtime_root=str(tmp_path / "runtime"), context=context)

    assert not is_ok(result)
