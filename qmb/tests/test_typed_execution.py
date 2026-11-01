"""The trading replay takes typed partitions and a request written as JSON (B4).

The fixture bot enters twice, once on each side of a month boundary, and its stop fills two
milliseconds later. The same rows replay once as CT-10 receipts and once as two typed tick
months named in a JSON request, and both paths close the same trades.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar, cast

from qmb.config import STARTING_CAPITAL_KEY, compile_run_config
from qmb.config.compiler import ResolvedRunConfig
from qmb.execution import SLIPPAGE_ADAPTER_ZERO, bind_execution_ports
from qmb.execution.binder import (
    BoundExecution,
    bind_requested_execution,
    execution_keys_from_request,
)
from qmb.host.book_handler import BookAdmissionContext
from qmb.host.replay import PinnedInstrumentPriceMetadata
from qmb.host.replay_execution import (
    RecordedExecutionResult,
    execute_recorded_replay_request,
    execute_typed_replay_request,
)
from qmb.host.replay_request import (
    TYPED_REQUEST_CLASS,
    ReplayInputRequest,
    load_typed_replay_request,
    persist_replay_request,
    resolve_replay_request,
)
from qmb.orchestrator.ledger import LedgerSink
from qmb.runloop.loop import STREAM_SET_KEY
from qmf.core import Instrument, Result, VenueId, World, WriterId, fingerprint, is_ok
from qmf.core.fingerprint import canonical_bytes
from qmf.core.refusal import RefusalCategory, is_refusal
from qmf.data.journal_producer import JournalReader, JournalWriter
from qmf.data.series import SeriesKey, SeriesStore
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.splits import SegmentRole, SplitManifest
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener
from replay_fixture_support import (
    RecordedReplayFixture,
    _entry_bot_definition,  # pyright: ignore[reportPrivateUsage]
    _entry_source_tree,  # pyright: ignore[reportPrivateUsage]
    _observation_at,  # pyright: ignore[reportPrivateUsage]
    _projection_split,  # pyright: ignore[reportPrivateUsage]
    make_trial_ledger,
)
from test_ql7_host import (
    study_fixture_defaults,
    study_fixture_fragments_with_bot,
    study_fixture_record,
    study_fixture_scope,
    study_fixture_seed,
)

T = TypeVar("T")

_START_NS = 1_738_324_800_000_000_000
"""2025-01-31 12:00 UTC: the first entry, one day before the month boundary."""
_HOUR_NS = 3_600_000_000_000
_MS_NS = 1_000_000
_ENTRIES = (_START_NS, _START_NS + 24 * _HOUR_NS)
_ASSIGNMENT: dict[str, object] = {"lookback": 20, "sma_period": 20}
_EXECUTION: dict[str, object] = {
    "fill_model": "declared-path@1",
    "fill_basis": "optimistic-exact",
    "slippage": {"adapter": "zero@1"},
    "cost_profile": {
        "adapter": "per-lot/per-1k-units@1",
        "broker": "replay-broker",
        "currency": "USD",
        "per_lot": {"amount": 100, "currency": "USD", "scale": 2},
    },
    "carry": {"schedule": "replay-swap-table"},
}


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _rows() -> tuple[tuple[int, int, int], ...]:
    """(event_ns, bid, ask): entry, hold, then the bid falls through the 500-point stop."""
    rows: list[tuple[int, int, int]] = []
    for entry in _ENTRIES:
        rows.append((entry, 1_09500, 1_09520))
        rows.append((entry + _MS_NS, 1_09500, 1_09520))
        rows.append((entry + 2 * _MS_NS, 1_09000, 1_09020))
    return tuple(rows)


def _metadata_identity() -> dict[str, object]:
    instrument = _ok(Instrument.try_create(_ok(VenueId.try_create("replay-venue")), "EURUSD"))
    return {
        "instrument": instrument.fp1_identity(),
        "metadata_version": "b4-typed-execution-fixture-v1",
        "price_scale": 5,
        "source_policy": {"kind": "persisted-test-fixture"},
    }


def _fixture(root: Path) -> RecordedReplayFixture:
    split, seal = _projection_split(_START_NS)
    boundary = SourceObservationBoundary(EvidenceStore(root / "ct10-room", seal=seal))
    refs: list[str] = []
    for index, (event_ns, bid, ask) in enumerate(_rows()):
        for offset, side, price in ((0, "bid", bid), (1, "ask", ask)):
            observation = _observation_at(side, index * 2 + offset, event_ns, price)
            refs.append(_ok(boundary.admit(observation)).archive.fingerprint.value)
    identity = _metadata_identity()
    instrument = _ok(Instrument.try_create(_ok(VenueId.try_create("replay-venue")), "EURUSD"))
    metadata = _ok(
        PinnedInstrumentPriceMetadata.try_create(
            instrument=instrument,
            price_scale=5,
            metadata_identity=identity,
            metadata_fp1=_ok(fingerprint(identity)),
        )
    )
    source_tree = _entry_source_tree(_ENTRIES)
    declaration = _entry_bot_definition(source_tree)
    return RecordedReplayFixture(
        expected_split_fp1=split.fingerprint,
        split=split,
        archive_fingerprints=tuple(refs),
        price_metadata=metadata,
        declaration=declaration,
        source_tree=source_tree,
        state_scope=study_fixture_scope(declaration),
        raw_store_root=root / "ct10-room",
        request_root=root / "replay-requests",
        bot_record=study_fixture_record("bot-definition", declaration.body()),
        slippage_adapter=SLIPPAGE_ADAPTER_ZERO,
    )


def _config(fixture: RecordedReplayFixture, execution_keys: dict[str, object]) -> ResolvedRunConfig:
    book_fragment, bms_fragment, port, _ = study_fixture_fragments_with_bot(fixture.bot_record)
    return _ok(
        compile_run_config(
            port,
            book_fragment=book_fragment,
            bms_fragment=bms_fragment,
            run_spec={
                "bot": fixture.bot_record.stable_id,
                STARTING_CAPITAL_KEY: study_fixture_seed(),
                **_ASSIGNMENT,
                STREAM_SET_KEY: ("primary",),
            },
            workspace_defaults={
                **study_fixture_defaults(),
                STREAM_SET_KEY: ("primary",),
                **execution_keys,
            },
        )
    )


def _receipts_config(fixture: RecordedReplayFixture) -> ResolvedRunConfig:
    return _config(
        fixture,
        RecordedReplayFixture._workspace_defaults(  # pyright: ignore[reportPrivateUsage]
            SLIPPAGE_ADAPTER_ZERO
        ),
    )


def _json_config(fixture: RecordedReplayFixture) -> ResolvedRunConfig:
    return _config(fixture, dict(_ok(execution_keys_from_request(_EXECUTION))))


def _book(
    root: Path, name: str, config: ResolvedRunConfig
) -> tuple[BookAdmissionContext, JournalReader, LedgerSink]:
    binding = config.replay_binding
    assert binding is not None
    journal = JournalStore(
        World.REPLAY, journal_dir=root / f"ct13-{name}", open_stream=jsonl_opener()
    )
    writer_id = _ok(WriterId.try_create("qmb-b4-test", "replay", "positions", "boot-1"))
    writer = JournalWriter(journal, writer_id, stream_name="positions")
    reader = JournalReader(journal)
    admission = _ok(
        RecordedReplayFixture._admission(  # pyright: ignore[reportPrivateUsage]
            binding, writer, reader
        )
    )
    return admission, reader, make_trial_ledger(root / f"ledger-{name}")


def _run_receipts(root: Path, fixture: RecordedReplayFixture) -> RecordedExecutionResult:
    request = _ok(
        ReplayInputRequest.try_create(
            split=fixture.split,
            split_role=SegmentRole.TRAIN,
            archive_fingerprints=fixture.archive_fingerprints,
            stream_id="primary",
            price_metadata=fixture.price_metadata,
            bot_identity=fixture.declaration.identity_payload(),
            source_tree=fixture.source_tree,
            assignment=_ASSIGNMENT,
            state_scope=fixture.state_scope.to_mapping(),
            state_bound=256,
            conformance_timeout_seconds=30,
        )
    )
    request_ref = _ok(persist_replay_request(request_root=fixture.request_root, request=request))
    resolved = _ok(
        resolve_replay_request(
            request_root=fixture.request_root,
            request_ref=request_ref,
            split=fixture.split,
            expected_split_fp1=fixture.expected_split_fp1,
            raw_store_root=fixture.raw_store_root,
            holdout_months=18,
        )
    )
    config = _receipts_config(fixture)
    admission, reader, ledger = _book(root, "receipts", config)
    return _ok(
        execute_recorded_replay_request(
            request=resolved,
            expected_request_ref=request_ref,
            request_root=fixture.request_root,
            raw_store_root=fixture.raw_store_root,
            holdout_months=18,
            expected_split_fp1=fixture.expected_split_fp1,
            config=config,
            bound_execution=_ok(bind_execution_ports(config)),
            admission=admission,
            journal_reader=reader,
            terminal_ledger=ledger,
        )
    )


def _write_typed_input(
    input_dir: Path, fixture: RecordedReplayFixture, *, execution: dict[str, object]
) -> Path:
    """Write two typed tick months and the JSON request naming them into a run's input folder."""
    store = SeriesStore(input_dir / "typed")
    partitions: list[dict[str, object]] = []
    for year, month in ((2025, 1), (2025, 2)):
        key = _ok(SeriesKey.try_create("dukascopy", "EURUSD", "ticks", year, month))
        rows = [
            (event_ns // _MS_NS, bid, ask, 1.0, 1.0)
            for event_ns, bid, ask in _rows()
            if (year, month) == ((2025, 1) if event_ns < _ENTRIES[1] else (2025, 2))
        ]
        receipt = _ok(store.commit(key, rows))
        partitions.append(
            {
                "series": key.series,
                "month": f"{year:04d}-{month:02d}",
                "file": receipt.path.relative_to(input_dir).as_posix(),
                "fingerprint": receipt.fingerprint,
            }
        )
    body: dict[str, object] = {
        "class": TYPED_REQUEST_CLASS,
        "format_version": 1,
        "stream_id": "primary",
        "split_identity": cast(SplitManifest, fixture.split).fp1_identity(),
        "split_role": "train",
        "price_metadata_identity": _metadata_identity(),
        "partitions": partitions,
        "bot_identity": fixture.declaration.identity_payload(),
        "source_tree": fixture.source_tree,
        "assignment": _ASSIGNMENT,
        "state_scope": fixture.state_scope.to_mapping(),
        "state_bound": 256,
        "conformance_timeout_seconds": 30,
        "execution": execution,
    }
    request_path = input_dir / "request.json"
    request_path.write_bytes(_ok(canonical_bytes(body)))
    return request_path


def _run_typed(
    root: Path,
    fixture: RecordedReplayFixture,
    request_path: Path,
    config: ResolvedRunConfig,
    bound: BoundExecution,
) -> Result[RecordedExecutionResult]:
    request = _ok(
        load_typed_replay_request(request_path=request_path, input_dir=request_path.parent)
    )
    admission, reader, ledger = _book(root, "typed", config)
    return execute_typed_replay_request(
        request=request,
        expected_request_ref=request.fingerprint,
        holdout_months=18,
        expected_split_fp1=fixture.expected_split_fp1,
        config=config,
        bound_execution=bound,
        admission=admission,
        journal_reader=reader,
        terminal_ledger=ledger,
    )


def _trades(result: RecordedExecutionResult) -> list[tuple[str, int, int, int]]:
    return [
        (
            str(item.closed_trade.side),
            item.closed_trade.closed_at.value_ns,
            item.closed_trade.realized_pnl.value,
            item.closed_trade.fees.value,
        )
        for item in result.closed_trades
    ]


def test_two_typed_months_from_a_json_request_trade_the_receipts_list(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    receipts = _run_receipts(tmp_path, fixture)
    json_config = _json_config(fixture)
    request_path = _write_typed_input(tmp_path / "run-input", fixture, execution=_EXECUTION)

    typed = _ok(
        _run_typed(
            tmp_path,
            fixture,
            request_path,
            json_config,
            _ok(bind_requested_execution(json_config, _EXECUTION)),
        )
    )

    assert json_config.fingerprint == _receipts_config(fixture).fingerprint
    assert _trades(receipts) == [
        ("long", _ENTRIES[0] + 2 * _MS_NS, -106 * 10**18, 2 * 10**18),
        ("long", _ENTRIES[1] + 2 * _MS_NS, -106 * 10**18, 2 * 10**18),
    ]
    assert _trades(typed) == _trades(receipts)
    assert typed.performance_result == receipts.performance_result
    assert typed.source_fp1 != receipts.source_fp1


def test_a_request_naming_a_missing_partition_refuses_by_name(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    input_dir = tmp_path / "run-input"
    request_path = _write_typed_input(input_dir, fixture, execution=_EXECUTION)
    body = json.loads(request_path.read_text(encoding="utf-8"))
    body["partitions"].append(
        {
            "series": "dukascopy/EURUSD/ticks/-",
            "month": "2025-03",
            "file": "typed/absent.parquet",
            "fingerprint": "sha256:" + "0" * 64,
        }
    )
    request_path.write_text(json.dumps(body), encoding="utf-8")

    refused = load_typed_replay_request(request_path=request_path, input_dir=input_dir)

    assert is_refusal(refused)
    assert refused.category is RefusalCategory.INVALID_INPUT
    assert refused.context["field"] == "partitions"
    assert refused.context["series"] == "dukascopy/EURUSD/ticks/-"
    assert refused.context["month"] == "2025-03"
    assert refused.context["file"] == "typed/absent.parquet"


def test_a_partition_outside_the_input_folder_is_refused(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    input_dir = tmp_path / "run-input"
    request_path = _write_typed_input(input_dir, fixture, execution=_EXECUTION)
    (tmp_path / "elsewhere.parquet").write_bytes(b"")
    body = json.loads(request_path.read_text(encoding="utf-8"))
    body["partitions"][0]["file"] = "../elsewhere.parquet"
    request_path.write_text(json.dumps(body), encoding="utf-8")

    refused = load_typed_replay_request(request_path=request_path, input_dir=input_dir)

    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["file"] == "../elsewhere.parquet"


def test_a_config_that_does_not_bind_the_requested_inputs_is_refused(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    zero_cost = {**_EXECUTION, "cost_profile": {"adapter": "zero@1"}}
    request_path = _write_typed_input(tmp_path / "run-input", fixture, execution=zero_cost)
    config = _json_config(fixture)

    refused = _run_typed(tmp_path, fixture, request_path, config, _ok(bind_execution_ports(config)))

    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "execution"
    assert refused.context["differing"] == ("cost_adapter", "cost_calibration")


def test_execution_inputs_refuse_an_unshipped_version_and_a_margin_adapter() -> None:
    version = execution_keys_from_request({**_EXECUTION, "fill_model": "declared-path@2"})
    margin = execution_keys_from_request({**_EXECUTION, "margin": "cross@1"})

    assert is_refusal(version)
    assert version.context["field"] == "execution.fill_model"
    assert version.context["given"] == "2"
    assert is_refusal(margin)
    assert margin.category is RefusalCategory.UNSUPPORTED_CAPABILITY
    assert margin.context["field"] == "execution.margin"
