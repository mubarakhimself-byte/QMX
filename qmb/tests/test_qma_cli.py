"""QMA delegated runs accept only trusted CT-47 identifiers."""

from __future__ import annotations

import json

from click.testing import CliRunner
from qmb.doors.cli import main
from qmb.host.qma_cli import decode_qma_backtest_context
from qmf.core import fingerprint, is_ok


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


def test_actual_cli_entry_does_not_fall_back_to_legacy_spawn() -> None:
    payload = _payload()
    result = CliRunner().invoke(
        main,
        ["backtest", "run"],
        env=_environ(payload),
    )
    assert result.exit_code == 1
    assert "operator_runtime" in result.output
    assert "orchestrator" not in result.output


def test_actual_cli_entry_refuses_modified_environment_reference() -> None:
    payload = _payload()
    env = _environ(payload)
    env["QMA_QMB_EVIDENCE_REF"] = _fp("different-request")
    result = CliRunner().invoke(main, ["backtest", "run"], env=env)
    assert result.exit_code == 1
    assert "evidence_ref" in result.output
