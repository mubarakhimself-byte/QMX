"""Durable expected-result context survives QMA process replacement."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from qma.core.ontology import ActorId, DeskSlug
from qma.core.ports.jobs import JobArtifact
from qma.core.ports.qmb import QmbDoorTransport
from qma.core.vocabulary.enums import ArtifactCompleteness, JobHandleState, PrincipalClass
from qma.daemon.backtest.expected import (
    read_expected_context,
    read_verified_context,
    write_expected_context,
    write_verified_context,
)
from qma.daemon.backtest.service import BacktestingService
from qma.daemon.envs.jobs import JobHandleService
from qmf.core import Fingerprint, Ok, Result, World, is_ok, is_refusal
from qmf.data.store import EvidenceStore
from qmf.data.store.refusals import invalid_input


def _append_store(root: Path):
    bundle = EvidenceStore(root).for_world(World.LIVE)
    assert isinstance(bundle, Ok)
    return bundle.value.append_store


class _VerifyOnlyDouble:
    """Unit double for QMB's verify-only process; no live completion claim."""

    def __init__(self, result: dict[str, object]) -> None:
        self.result = result

    def verify_persisted_result(self, job_id: str, invocation: object) -> Result[dict[str, object]]:
        _ = invocation
        if self.result.get("job_id") != job_id:
            return invalid_input("job_id", "verification double matches the requested job")
        return Ok(self.result)


def test_expected_context_and_reopened_result_survive_store_reconstruction(
    tmp_path: Path,
) -> None:
    body: dict[str, object] = {
        "job_id": "job:replay:task-1",
        "attempt_id": 1,
        "request": {"task_id": "task-1", "experiment_spec_fp1": "spec", "evidence_ref": "data"},
        "invocation": {"argv": ["backtest", "run"], "payload": {"job_id": "job:replay:task-1"}},
        "mints_ct32": True,
        "operator_descriptor_fp1": "fp1:sha256:" + "a" * 64,
    }
    store = _append_store(tmp_path)
    written = write_expected_context(store=store, job_id="job:replay:task-1", payload=body)
    assert isinstance(written, Ok)

    restored = read_expected_context(
        store=store, reference_fp1=written.value["fp1"], job_id="job:replay:task-1"
    )
    assert isinstance(restored, Ok)
    assert restored.value["sha256"] == written.value["sha256"]
    assert restored.value["invocation"] == body["invocation"]

    result = {
        "class": "qmb-recorded-replay-result-v1",
        "job_id": "job:replay:task-1",
        "attempt_id": 1,
        "terminal_line_fp1": "fp1:sha256:" + "b" * 64,
    }
    proof = write_verified_context(
        store=store,
        job_id="job:replay:task-1",
        expected_reference_fp1=written.value["fp1"],
        expected_sha256=written.value["sha256"],
        result=result,
    )
    assert isinstance(proof, Ok)
    reopened = read_verified_context(
        store=store,
        reference_fp1=proof.value["fp1"],
        job_id="job:replay:task-1",
        expected_reference_fp1=written.value["fp1"],
        expected_sha256=written.value["sha256"],
    )
    assert isinstance(reopened, Ok)
    assert reopened.value["result"] == result


def test_context_mutation_or_foreign_proof_refuses(tmp_path: Path) -> None:
    store = _append_store(tmp_path)
    saved = write_expected_context(
        store=store,
        job_id="job:replay:task-2",
        payload={"job_id": "job:replay:task-2", "attempt_id": 2, "identity": {"evidence": "A"}},
    )
    assert isinstance(saved, Ok)
    fp = Fingerprint.try_create(saved.value["fp1"])
    assert isinstance(fp, Ok)
    changed = store.append_raw(
        [
            {
                "class": "qma-qmb-expected-context-v1",
                "format_version": 1,
                "job_id": "job:replay:task-2",
                "attempt_id": 2,
                "identity": {"evidence": "B"},
            }
        ],
        presented_fingerprint=fp.value,
    )
    assert is_refusal(changed)
    assert is_refusal(
        read_expected_context(
            store=store,
            reference_fp1="fp1:sha256:" + "0" * 64,
            job_id="job:replay:task-2",
        )
    )

    assert is_refusal(
        write_verified_context(
            store=store,
            job_id="job:replay:task-2",
            expected_reference_fp1=saved.value["fp1"],
            expected_sha256="0" * 64,
            result={"job_id": "job:replay:task-2"},
        )
    )


def test_restored_unknown_stays_gated_after_durable_verification(tmp_path: Path) -> None:
    expected_result: dict[str, object] = {
        "class": "qmb-recorded-replay-result-v1",
        "job_id": "job:replay:restart-1",
        "attempt_id": 3,
        "experiment_spec_fp1": "spec:registered",
        "evidence_ref": "evidence:recorded",
        "split_manifest_fp1": "fp1:sha256:" + "a" * 64,
        "mints_ct32": True,
        "operator_descriptor_fp1": "fp1:sha256:" + "b" * 64,
    }
    fp = "fp1:sha256:" + "c" * 64
    terminal = {
        **expected_result,
        "ct32_fp1": fp,
        "run_fp1": fp,
        "terminal_line_fp1": fp,
    }
    context = {
        "job_id": "job:replay:restart-1",
        "attempt_id": 3,
        "task_id": "task-restart-1",
        "owner": "actor:test",
        "request": {"task_id": "task-restart-1"},
        "invocation": {
            "program": "qmb",
            "kind": "cli",
            "argv": ["backtest", "run"],
            "payload": {"job_id": "job:replay:restart-1"},
            "import_edge": False,
        },
        "expected_result": expected_result,
    }
    store = _append_store(tmp_path)
    saved = write_expected_context(store=store, job_id="job:replay:restart-1", payload=context)
    assert isinstance(saved, Ok)

    first_jobs = JobHandleService()
    owner = ActorId.mint(DeskSlug.ANALYSIS, "restart-test")
    assert isinstance(owner, Ok)
    submitted = first_jobs.submit(
        owner=owner.value,
        task_id="task-restart-1",
        job_id="job:replay:restart-1",
        attempt_id=3,
    )
    assert isinstance(submitted, Ok)
    first_jobs.start(submitted.value.job_id)
    first_jobs.observe_lost_certainty(submitted.value.job_id, trigger="daemon_restart")
    first_jobs.attach_artifact(
        submitted.value.job_id,
        JobArtifact(saved.value["fp1"], ArtifactCompleteness.PARTIAL),
    )
    durable_handle = first_jobs.handle_for(submitted.value.job_id)
    assert durable_handle is not None

    restarted_jobs = JobHandleService()
    assert is_ok(restarted_jobs.store.restore((durable_handle.to_payload(),)))
    restored = restarted_jobs.recover_after_restart()
    assert is_ok(restored)
    assert restored.value[0].state is JobHandleState.UNKNOWN

    service = BacktestingService(
        jobs=restarted_jobs,
        transport=cast(QmbDoorTransport, _VerifyOnlyDouble(terminal)),
        artifact_root=tmp_path,
    )
    reconciled = service.reconcile_restored_jobs()
    assert isinstance(reconciled, Ok)
    assert reconciled.value == ("job:replay:restart-1",)
    after_verify = restarted_jobs.handle_for("job:replay:restart-1")
    assert after_verify is not None
    assert after_verify.state is JobHandleState.UNKNOWN
    assert is_refusal(
        service.resolve_verified_unknown("job:replay:restart-1", principal=PrincipalClass.MACHINE)
    )
    resolved = service.resolve_verified_unknown(
        "job:replay:restart-1", principal=PrincipalClass.OPERATOR
    )
    assert isinstance(resolved, Ok)
    assert resolved.value.state is JobHandleState.DONE
    assert is_refusal(
        service.resolve_verified_unknown("job:replay:restart-1", principal=PrincipalClass.OPERATOR)
    )
