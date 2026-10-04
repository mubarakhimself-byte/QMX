"""Actual offline intake-to-QMB replay; no CT47/CT40 authority claim.

Synthetic provider bytes declare side-specific native IDs. This is the existing
single-observation CT15 path, not a workaround that rewrites Dukascopy identities.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import TypeVar

from qmb.data import catalog, download, verify
from qmb.data.ports import DownloadSide, ProviderFetchRequest
from qmb.host.operator_replay import project_operator_replay
from qmb.host.qma_cli import decode_qma_backtest_context
from qmb.host.replay import read_recorded_replay_source
from qmb.host.replay_request import resolve_replay_request
from qmf.core import Fingerprint, Ok, Result, World, WriterId, fingerprint, is_ok, is_refusal
from qmf.data.ingest import ProviderRecord
from qmf.data.seal import HoldoutSeal
from qmf.data.source_boundary import ObservationReceipt, SourceObservationBoundary
from qmf.data.splits import SegmentRole
from qmf.data.store import EvidenceStore
from replay_fixture_support import make_recorded_replay_fixture
from test_alternative_execution import STUDY_FIXTURE_EPOCH_NS
from test_operator_replay_process import prepare_operator_replay_runtime

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


class _RecordingBoundary(SourceObservationBoundary):
    def __init__(self, store: EvidenceStore) -> None:
        super().__init__(store)
        self.receipts: list[ObservationReceipt] = []

    def admit(self, observation: object) -> Result[ObservationReceipt]:
        result = super().admit(observation)
        if is_ok(result):
            self.receipts.append(result.value)
        return result


class _SyntheticBytes:
    """Test-local adapter decoding an explicit synthetic provider response."""

    source = "recorded-synthetic-provider-fixture-v1"
    batch_count = 1
    rate_limit_per_second = None

    def __init__(self, path: Path, instrument: object) -> None:
        self.path = path
        self.instrument = instrument

    def list_symbols(self) -> Result[tuple[str, ...]]:
        return Ok(("EURUSD",))

    def earliest_available(self, symbol: object, /) -> Result[int | None]:
        del symbol
        return Ok(STUDY_FIXTURE_EPOCH_NS)

    def fetch(self, request: ProviderFetchRequest, /) -> Result[tuple[ProviderRecord, ...]]:
        rows = json.loads(self.path.read_bytes())
        return Ok(
            tuple(
                ProviderRecord(
                    source=self.source,
                    source_native_id=row["native_id"],
                    revision=request.revision,
                    event_time=row["event_ns"],
                    known_at=row["event_ns"],
                    instrument=self.instrument,
                    foreign_money={"verbatim": row["price"], "scale": 5},
                    correction_of=row.get("correction_of"),
                )
                for row in rows
                if row["side"] == request.side.value
            )
        )


def test_synthetic_bytes_intake_restart_revision_to_real_qmb_and_projection(tmp_path: Path) -> None:
    template = make_recorded_replay_fixture(tmp_path / "diagnostic-definition")
    rows = [
        {
            "native_id": f"quote-{index}-{side}",
            "side": side,
            "event_ns": STUDY_FIXTURE_EPOCH_NS + index,
            "price": price,
        }
        for index in range(3)
        for side, price in (
            ("bid", 109000 if index == 2 else 109500),
            ("ask", 109020 if index == 2 else 109520),
        )
    ]
    provider_path = tmp_path / "synthetic-provider.json"
    provider_path.write_text(json.dumps(rows), encoding="utf-8")
    archive = tmp_path / "actual-download"
    instrument = template.price_metadata.instrument
    writer = _ok(WriterId.try_create("offline-test", "qmb", "download", "boot-1"))
    original_refs: list[str] = []
    original_observations: dict[str, Fingerprint] = {}
    receipts: list[dict[str, object]] = []
    for side in (DownloadSide.BID, DownloadSide.ASK):
        store = EvidenceStore(archive)
        recorder = _RecordingBoundary(store)
        request: dict[str, object] = {
            "destination": str(archive),
            "venue": instrument.venue.value,
            "symbol": "EURUSD",
            "start": STUDY_FIXTURE_EPOCH_NS,
            "end": STUDY_FIXTURE_EPOCH_NS + 3,
            "side": side.value,
            "resolution": "tick",
            "world": World.REPLAY,
            "license_tag": "internal-only",
            "writer": writer,
            "receive_wall_time": STUDY_FIXTURE_EPOCH_NS + 10,
            "adapter": _SyntheticBytes(provider_path, instrument),
            "store": store,
            "boundary": recorder,
        }
        initial = _ok(download(request))
        assert initial.produced == initial.admitted == 3
        receipts.append(initial.as_mapping())
        original_refs.extend(row.archive.fingerprint.value for row in recorder.receipts)
        for receipt in recorder.receipts:
            observation = _ok(
                recorder.read(
                    receipt.archive.fingerprint, in_world=World.REPLAY, for_world=World.REPLAY
                )
            )
            original_observations[observation.source_native_id] = observation.fingerprint
        restarted = {
            **request,
            "store": EvidenceStore(archive),
            "adapter": _SyntheticBytes(provider_path, instrument),
        }
        restarted.pop("boundary")
        rerun = _ok(download(restarted))
        assert rerun.produced == 0 and rerun.idempotent == 3

    quality = _ok(
        verify(
            {
                "archive": str(archive),
                "venue": instrument.venue.value,
                "symbol": "EURUSD",
                "start": STUDY_FIXTURE_EPOCH_NS,
                "end": STUDY_FIXTURE_EPOCH_NS + 3,
                "side": "both",
                "world": World.REPLAY,
                "store": EvidenceStore(archive),
                "writer": writer,
                "journal_instant": STUDY_FIXTURE_EPOCH_NS + 10,
            }
        )
    )
    assert quality.verdict == "pass" and quality.journaled
    coverage = _ok(catalog({"destination": str(archive), "side": "both"}))
    assert {row.side: row.observation_count for row in coverage.entries} == {"bid": 3, "ask": 3}
    prefix = {path: path.read_bytes() for path in archive.rglob("*.parquet")}

    # Preserve original pins while admitting an explicitly linked correction.
    correction_row = {
        **rows[0],
        "price": 109501,
        "correction_of": original_observations["quote-0-bid"].value,
    }
    correction_path = tmp_path / "synthetic-correction.json"
    correction_path.write_text(json.dumps([correction_row]), encoding="utf-8")
    corrected_store = EvidenceStore(archive)
    correction_recorder = _RecordingBoundary(corrected_store)
    revision = _ok(
        download(
            {
                **request,
                "side": "bid",
                "revision": "r2",
                "overwrite": True,
                "adapter": _SyntheticBytes(correction_path, instrument),
                "store": corrected_store,
                "boundary": correction_recorder,
            }
        )
    )
    assert revision.produced == 1 and correction_recorder.receipts[0].is_correction
    assert all(path.read_bytes() == data for path, data in prefix.items())

    fixture = replace(template, raw_store_root=archive, archive_fingerprints=tuple(original_refs))
    # This identity labels a domain diagnostic; it is not a registered CT47.
    spec = _ok(fingerprint({"class": "domain-diagnostic-without-ct47-authority"}))
    env, roots, request_ref = prepare_operator_replay_runtime(
        tmp_path / "qmb", spec, recorded_fixture=fixture
    )
    payload = json.loads(env["QMA_QMB_DOOR_PAYLOAD"])
    cli = Path(sys.executable).with_name("qmb")
    environment = {**os.environ, **env}
    preflight = subprocess.run(
        [str(cli), "backtest", "run"],
        capture_output=True,
        text=True,
        env={**environment, "QMA_QMB_PREFLIGHT": "1"},
        timeout=30,
    )
    assert preflight.returncode == 0, preflight.stderr
    payload["operator_descriptor_fp1"] = json.loads(preflight.stdout)["operator_descriptor_fp1"]
    environment["QMA_QMB_DOOR_PAYLOAD"] = json.dumps(payload)
    executed = subprocess.run(
        [str(cli), "backtest", "run"], capture_output=True, text=True, env=environment, timeout=60
    )
    assert executed.returncode == 0, executed.stderr
    result = json.loads(executed.stdout)
    assert result["evidence_ref"] == request_ref.value
    context = _ok(
        decode_qma_backtest_context(
            payload_text=environment["QMA_QMB_DOOR_PAYLOAD"], environ=environment
        )
    )
    before = {path: path.read_bytes() for path in roots["journal"].rglob("*") if path.is_file()}
    view = _ok(
        project_operator_replay(
            runtime_root=env["QMB_REPLAY_RUNTIME_ROOT"],
            context=context,
            predicate={"max_trades": 1},
        )
    )
    assert view.matched_count == 1 and view.source_ct32 == result["ct32_fp1"]
    assert {
        path: path.read_bytes() for path in roots["journal"].rglob("*") if path.is_file()
    } == before
    verification = subprocess.run(
        [str(cli), "backtest", "run"],
        capture_output=True,
        text=True,
        env={**environment, "QMA_QMB_VERIFY": "1", "QMA_QMB_VERIFY_DURABLE": "1"},
        timeout=60,
    )
    assert verification.returncode == 0, verification.stderr
    assert json.loads(verification.stdout) == result
    corrected = read_recorded_replay_source(
        store_root=archive,
        archive_fingerprints=(
            *original_refs,
            correction_recorder.receipts[0].archive.fingerprint.value,
        ),
        stream_id="primary",
        instrument_metadata=fixture.price_metadata,
        split_manifest=fixture.split,
        split_role=SegmentRole.TRAIN,
        holdout_seal=_ok(HoldoutSeal.from_manifest(fixture.split, 18)),
        world=World.REPLAY,
    )
    assert is_refusal(corrected) and corrected.context["field"] == "correction_of"
    resolved = _ok(
        resolve_replay_request(
            request_root=roots["requests"],
            request_ref=request_ref,
            expected_split_fp1=fixture.expected_split_fp1,
            raw_store_root=archive,
            holdout_months=18,
        )
    )
    assert len(resolved.source.observations) == 6
    projection_script = """import json, os
from qmf.core import is_ok
from qmb.host.qma_cli import decode_qma_backtest_context
from qmb.host.operator_replay import project_operator_replay
context = decode_qma_backtest_context(
    payload_text=os.environ['QMA_QMB_DOOR_PAYLOAD'], environ=os.environ)
assert is_ok(context), context
view = project_operator_replay(runtime_root=os.environ['QMB_REPLAY_RUNTIME_ROOT'],
    context=context.value, predicate={'max_trades': 1})
assert is_ok(view), view
print(json.dumps({'body': view.value.body(), 'fp1': view.value.fingerprint.value,
    'matched_count': view.value.matched_count}))
"""
    reopened = subprocess.run(
        [sys.executable, "-c", projection_script],
        capture_output=True,
        text=True,
        env=environment,
        timeout=30,
    )
    assert reopened.returncode == 0, reopened.stderr
    reopened_view = json.loads(reopened.stdout)
    assert reopened_view == {"body": view.body(), "fp1": view.fingerprint.value, "matched_count": 1}
    assert {
        path: path.read_bytes() for path in roots["journal"].rglob("*") if path.is_file()
    } == before
    (tmp_path / "request-result.json").write_text(
        json.dumps(
            {
                "claim_scope": "actual synthetic intake/QMB domain CLI; no CT47/CT40 acceptance",
                "accepted_full_ct40_journey": False,
                "agent_or_model_records_minted": 0,
                "downloads": receipts,
                "revision": revision.as_mapping(),
                "request": payload,
                "result": result,
                "projection": view.body(),
                "projection_fp1": view.fingerprint.value,
                "matched_count": view.matched_count,
                "fresh_process_projection": reopened_view,
                "correction_refusal": {
                    "category": corrected.category.value,
                    "context": dict(corrected.context),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
