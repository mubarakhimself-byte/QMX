"""QMA delegated runs accept only trusted CT-47 identifiers."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from click.testing import CliRunner
from qmb.doors.cli import main
from qmb.host.qma_cli import decode_qma_backtest_context, validate_qma_backtest_context
from qmf.core import Fingerprint, fingerprint, is_ok, is_refusal


def _fp(label: str) -> str:
    result = fingerprint({"class": "qmb-qma-cli-test", "label": label})
    assert is_ok(result), result
    return result.value.value


def _payload() -> dict[str, object]:
    return {
        "job_id": "job-1",
        "attempt_id": 1,
        "experiment_spec_fp1": _fp("experiment"),
        "evidence_ref": _fp("request"),
        "environment_ref": "env:paper-fixture",
        "occupancy_key": "qmb:job-1",
        "world": "replay",
        "recorded": True,
        "import_edge": False,
        "owned_by": "qmb",
        "qma_re_specifies": False,
        "qmb_owned": ["artifact_contract", "intra_node_parallelism", "run_ledger"],
        "route": ["agent", "qma_backtest_tool", "backtesting_service", "qmb_door", "qmb"],
        "command": "backtest.run",
        "occupancy": "run",
        "mints_ct32": True,
        "mints_experiment_spec": False,
        "children_are_qma_jobs": False,
        "opens_daemon_sqlite": False,
        "split_manifest_fp1": _fp("split"),
        "operator_descriptor_fp1": None,
    }


def _environ(payload: dict[str, object]) -> dict[str, str]:
    return {
        "QMA_QMB_DOOR": "cli",
        "QMA_QMB_DOOR_PAYLOAD": json.dumps(payload),
        "QMA_QMB_JOB_ID": str(payload["job_id"]),
        "QMA_QMB_ATTEMPT_ID": str(payload["attempt_id"]),
        "QMA_QMB_EXPERIMENT_SPEC_FP1": str(payload["experiment_spec_fp1"]),
        "QMA_QMB_EVIDENCE_REF": str(payload["evidence_ref"]),
        "QMA_QMB_SPLIT_MANIFEST_FP1": str(payload["split_manifest_fp1"]),
        "QMA_QMB_ENVIRONMENT_REF": str(payload["environment_ref"]),
        "QMA_QMB_OCCUPANCY_KEY": str(payload["occupancy_key"]),
    }


def test_delegated_envelope_carries_only_registered_and_persisted_refs() -> None:
    payload = _payload()
    result = decode_qma_backtest_context(
        payload_text=json.dumps(payload), environ=_environ(payload)
    )
    assert is_ok(result), result
    assert result.value.evidence_ref.value == payload["evidence_ref"]
    assert result.value.split_manifest_fp1.value == payload["split_manifest_fp1"]


def test_delegated_envelope_rejects_runtime_roots_or_policy_overrides() -> None:
    payload = {**_payload(), "registry_root": "/operator/registry"}
    result = decode_qma_backtest_context(
        payload_text=json.dumps(payload), environ=_environ(payload)
    )
    assert not hasattr(result, "value")


def test_delegated_envelope_rejects_duplicate_keys_and_bool_integer_aliases() -> None:
    payload = _payload()
    duplicate = json.dumps(payload)[:-1] + ',"attempt_id":2}'
    assert not is_ok(decode_qma_backtest_context(payload_text=duplicate, environ=_environ(payload)))
    malformed = {**payload, "attempt_id": True}
    assert not is_ok(
        decode_qma_backtest_context(payload_text=json.dumps(malformed), environ=_environ(payload))
    )


def test_delegated_envelope_requires_exact_result_mode_and_descriptor_slot() -> None:
    payload = _payload()
    malformed_mode = {**payload, "mints_ct32": 1}
    assert not is_ok(
        decode_qma_backtest_context(
            payload_text=json.dumps(malformed_mode), environ=_environ(payload)
        )
    )
    missing_descriptor = dict(payload)
    del missing_descriptor["operator_descriptor_fp1"]
    assert not is_ok(
        decode_qma_backtest_context(
            payload_text=json.dumps(missing_descriptor), environ=_environ(payload)
        )
    )


def test_nominal_context_is_revalidated_after_direct_construction() -> None:
    payload = _payload()
    decoded = decode_qma_backtest_context(
        payload_text=json.dumps(payload), environ=_environ(payload)
    )
    assert is_ok(decoded), decoded
    malformed: tuple[tuple[str, object], ...] = (
        ("job_id", []),
        ("attempt_id", True),
        ("experiment_spec_fp1", None),
        ("evidence_ref", Fingerprint("invalid")),
        ("split_manifest_fp1", None),
        ("environment_ref", None),
        ("occupancy_key", []),
        ("mints_ct32", 1),
        ("operator_descriptor_fp1", Fingerprint("invalid")),
    )
    for field, value in malformed:
        candidate = replace(cast(Any, decoded.value), **{field: value})
        result = validate_qma_backtest_context(candidate)
        assert is_refusal(result), (field, result)


def test_actual_cli_entry_dispatches_to_operator_binding_without_legacy_fallback(
    tmp_path: Path,
) -> None:
    payload = _payload()
    runtime_root = tmp_path / "runtime"
    binding_dir = runtime_root / str(payload["experiment_spec_fp1"]).replace(":", "-")
    binding_dir = binding_dir / str(payload["evidence_ref"]).replace(":", "-")
    binding_dir.mkdir(parents=True)
    (binding_dir / "operator-binding.json").write_text("{}", encoding="utf-8")
    env = _environ(payload)
    env["QMB_REPLAY_RUNTIME_ROOT"] = str(runtime_root)
    env["QMA_QMB_PREFLIGHT"] = "1"
    result = CliRunner().invoke(
        main,
        ["backtest", "run"],
        env=env,
    )
    assert result.exit_code == 1
    assert "operator_binding" in result.output
    assert "orchestrator" not in result.output


def test_actual_cli_entry_refuses_modified_environment_reference() -> None:
    payload = _payload()
    env = _environ(payload)
    env["QMA_QMB_EVIDENCE_REF"] = _fp("different-request")
    result = CliRunner().invoke(main, ["backtest", "run"], env=env)
    assert result.exit_code == 1
    assert "evidence_ref" in result.output
