"""Persisted replay request to CT-32 terminal integration coverage."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

import pytest
from qmb._refuse import invalid
from qmb.config import STARTING_CAPITAL_KEY, compile_run_config
from qmb.execution import (
    SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
    SLIPPAGE_ADAPTER_ZERO,
    bind_execution_ports,
)
from qmb.host.replay_execution import execute_recorded_replay_request
from qmb.host.replay_request import (
    ReplayInputRequest,
    persist_replay_request,
    resolve_replay_request,
)
from qmb.orchestrator.ledger import read_merge_view
from qmb.results.measures import MEASURE_IDENTITIES, PerformanceMeasure
from qmb.runloop.loop import STREAM_SET_KEY
from qmf.core import Ok, Result, World, WriterId, fingerprint, is_ok
from qmf.data.journal_producer import JournalAppendReceipt, JournalReader, JournalWriter
from qmf.data.splits import SegmentRole
from qmf.data.store import JournalStore, jsonl_opener
from replay_fixture_support import (
    RecordedReplayFixture,
    make_recorded_replay_fixture,
    make_trial_ledger,
)
from test_ql7_host import _SEED, _fragments_with_bot  # pyright: ignore[reportPrivateUsage]

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


@pytest.mark.parametrize(
    "receipt_case",
    (
        "append-refusal",
        "ok-none",
        "world-string",
        "payload-object",
        "logical-bool",
        "writer-none",
        "physical-bool",
        "edge-receipt",
    ),
)
def test_persisted_request_runs_through_economic_terminal_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, receipt_case: str
) -> None:
    fixture = make_recorded_replay_fixture(tmp_path, slippage_adapter=SLIPPAGE_ADAPTER_ZERO)
    request = _ok(
        ReplayInputRequest.try_create(
            split=fixture.split,
            split_role=SegmentRole.TRAIN,
            archive_fingerprints=fixture.archive_fingerprints,
            stream_id="primary",
            price_metadata=fixture.price_metadata,
            bot_identity=fixture.declaration.identity_payload(),
            source_tree=fixture.source_tree,
            assignment={"lookback": 20, "sma_period": 20},
            state_scope=fixture.state_scope.to_mapping(),
            state_bound=256,
            conformance_timeout_seconds=30,
        )
    )
    request_ref = _ok(
        persist_replay_request(request_root=fixture.request_root, request=request)
    )
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
    book_fragment, bms_fragment, port, _ = _fragments_with_bot(fixture.bot_record)
    config = _ok(
        compile_run_config(
            port,
            book_fragment=book_fragment,
            bms_fragment=bms_fragment,
            run_spec={
                "bot": fixture.bot_record.stable_id,
                STARTING_CAPITAL_KEY: _SEED,
                "lookback": 20,
                "sma_period": 20,
                STREAM_SET_KEY: (resolved.source.stream_id,),
            },
            workspace_defaults=RecordedReplayFixture._workspace_defaults(  # pyright: ignore[reportPrivateUsage]
                fixture.slippage_adapter
            ),
        )
    )
    bound = _ok(bind_execution_ports(config))
    binding = config.replay_binding
    assert binding is not None
    journal = JournalStore(
        World.REPLAY,
        journal_dir=tmp_path / "ct13-confirmation",
        open_stream=jsonl_opener(),
    )
    writer_id = _ok(WriterId.try_create("qmb-service-test", "replay", "positions", "boot-1"))
    writer = JournalWriter(journal, writer_id, stream_name="positions")
    reader = JournalReader(journal)
    admission = _ok(RecordedReplayFixture._admission(  # pyright: ignore[reportPrivateUsage]
        binding, writer, reader
    ))
    ledger = make_trial_ledger(tmp_path / "terminal-ledger")

    original_record_data_quality = JournalWriter.record_data_quality

    def malformed_source_witness(
        self: JournalWriter,
        payload: Mapping[str, object] | None = None,
        *,
        instant: object,
        correlation_id: object = None,
        display_time: object = None,
    ) -> Result[JournalAppendReceipt]:
        if receipt_case == "append-refusal":
            return invalid("injected", "CT-13 source provenance did not persist")
        if receipt_case == "ok-none":
            return cast(Result[JournalAppendReceipt], Ok(None))
        actual = original_record_data_quality(
            self,
            payload,
            instant=instant,
            correlation_id=correlation_id,
            display_time=display_time,
        )
        if not is_ok(actual):
            return actual
        receipt = actual.value
        if receipt_case == "world-string":
            event = replace(receipt.event, world="replay")  # pyright: ignore[reportArgumentType]
            return Ok(replace(receipt, event=event))
        if receipt_case == "payload-object":
            event = replace(receipt.event, payload=object())  # pyright: ignore[reportArgumentType]
            return Ok(replace(receipt, event=event))
        if receipt_case == "logical-bool":
            event = replace(receipt.event, sequence=True)  # pyright: ignore[reportArgumentType]
            return Ok(replace(receipt, event=event))
        if receipt_case == "writer-none":
            event = replace(receipt.event, writer=None)  # pyright: ignore[reportArgumentType]
            return Ok(replace(receipt, event=event))
        if receipt_case == "physical-bool":
            store_receipt = replace(
                receipt.store_receipt, sequence=True  # pyright: ignore[reportArgumentType]
            )
            return Ok(replace(receipt, store_receipt=store_receipt))
        if receipt_case == "edge-receipt":
            return Ok(replace(receipt, edge_receipts=(receipt.store_receipt,)))
        raise AssertionError(f"unknown receipt case {receipt_case}")

    monkeypatch.setattr(JournalWriter, "record_data_quality", malformed_source_witness)
    refused_before_run = execute_recorded_replay_request(
        request=resolved,
        expected_request_ref=request_ref,
        request_root=fixture.request_root,
        raw_store_root=fixture.raw_store_root,
        holdout_months=18,
        expected_split_fp1=fixture.expected_split_fp1,
        config=config,
        bound_execution=bound,
        admission=admission,
        journal_reader=reader,
        terminal_ledger=ledger,
    )
    assert not is_ok(refused_before_run)
    events_before_run = _ok(reader.read_checked("positions", for_world=World.REPLAY))
    assert all(event.event_type.value == "data quality" for event in events_before_run)
    assert all(
        event.payload.get("kind") == "qmb-recorded-replay-source-binding-v1"
        for event in events_before_run
    )
    if receipt_case in {"append-refusal", "ok-none"}:
        assert events_before_run == []
    else:
        assert len(events_before_run) == 1
    assert _ok(read_merge_view(ledger.root, world=World.REPLAY, role="confirmation")) == ()
    monkeypatch.setattr(JournalWriter, "record_data_quality", original_record_data_quality)

    outcome = execute_recorded_replay_request(
        request=resolved,
        expected_request_ref=request_ref,
        request_root=fixture.request_root,
        raw_store_root=fixture.raw_store_root,
        holdout_months=18,
        expected_split_fp1=fixture.expected_split_fp1,
        config=config,
        bound_execution=bound,
        admission=admission,
        journal_reader=reader,
        terminal_ledger=ledger,
    )

    result = _ok(outcome)
    assert result.request_ref == request_ref
    assert result.source_fp1 == resolved.source.fingerprint
    assert len(result.closed_trades) == 1
    trade = result.closed_trades[0].closed_trade
    assert trade.realized_pnl.currency == "USD"
    assert trade.realized_pnl.as_fraction() == -106
    assert trade.fees.as_fraction() == 2
    assert result.closed_trades[0].record.realized_pnl.as_fraction() == -104
    realized_r = _ok(result.closed_trades[0].record.realized_r())
    assert realized_r.numerator == -53
    assert realized_r.denominator == 50
    net_profit = result.performance_result.measure_set[MEASURE_IDENTITIES.index("net_profit")]
    assert isinstance(net_profit, PerformanceMeasure)
    assert getattr(net_profit.quantity, "as_fraction", lambda: None)() == -106
    assert result.performance_result.measure_set
    assert result.terminal_line.ct32_fingerprint is not None
    durable = _ok(read_merge_view(ledger.root, world=World.REPLAY, role="confirmation"))
    assert len(durable) == 1
    assert durable[0].fp1_identity() == result.terminal_line.fp1_identity()

    final_path = resolved.source.execution_paths[-1]
    assert final_path.bid is not None
    altered_bid = replace(final_path.bid, value=final_path.bid.value - 500)
    altered_paths = (*resolved.source.execution_paths[:-1], replace(final_path, bid=altered_bid))
    altered_source = replace(resolved.source, execution_paths=altered_paths)
    altered_result = execute_recorded_replay_request(
        request=replace(resolved, source=altered_source),
        expected_request_ref=request_ref,
        request_root=fixture.request_root,
        raw_store_root=fixture.raw_store_root,
        holdout_months=18,
        expected_split_fp1=fixture.expected_split_fp1,
        config=config,
        bound_execution=bound,
        admission=admission,
        journal_reader=reader,
        terminal_ledger=ledger,
    )
    assert not is_ok(altered_result)
    malformed_sources = (
        replace(resolved.source, observations=(object(),)),  # pyright: ignore[reportArgumentType]
        replace(resolved.source, slices=(object(),)),  # pyright: ignore[reportArgumentType]
        replace(
            resolved.source,
            execution_paths=(object(),),  # pyright: ignore[reportArgumentType]
        ),
        replace(
            resolved.source,
            read_surfaces={"primary": object()},  # pyright: ignore[reportArgumentType]
        ),
    )
    for malformed_source in malformed_sources:
        malformed_result = execute_recorded_replay_request(
            request=replace(resolved, source=malformed_source),
            expected_request_ref=request_ref,
            request_root=fixture.request_root,
            raw_store_root=fixture.raw_store_root,
            holdout_months=18,
            expected_split_fp1=fixture.expected_split_fp1,
            config=config,
            bound_execution=bound,
            admission=admission,
            journal_reader=reader,
            terminal_ledger=ledger,
        )
        assert not is_ok(malformed_result)
    foreign_ref = _ok(fingerprint({"foreign": True}))
    forged_reference_result = execute_recorded_replay_request(
        request=replace(resolved, request_ref=foreign_ref),
        expected_request_ref=request_ref,
        request_root=fixture.request_root,
        raw_store_root=fixture.raw_store_root,
        holdout_months=18,
        expected_split_fp1=fixture.expected_split_fp1,
        config=config,
        bound_execution=bound,
        admission=admission,
        journal_reader=reader,
        terminal_ledger=ledger,
    )
    assert not is_ok(forged_reference_result)


def test_one_basis_point_quote_path_is_a_real_nofill_control(tmp_path: Path) -> None:
    fixture = make_recorded_replay_fixture(
        tmp_path,
        slippage_adapter=SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
    )
    # A persisted quote-only path has no synthetic print with which to price
    # post-quote slippage, so this configured adapter correctly yields no fill.
    # The service must record zero trades instead of silently substituting a
    # zero-slippage execution model.
    request = _ok(
        ReplayInputRequest.try_create(
            split=fixture.split,
            split_role=SegmentRole.TRAIN,
            archive_fingerprints=fixture.archive_fingerprints,
            stream_id="primary",
            price_metadata=fixture.price_metadata,
            bot_identity=fixture.declaration.identity_payload(),
            source_tree=fixture.source_tree,
            assignment={"lookback": 20, "sma_period": 20},
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
    book_fragment, bms_fragment, port, _ = _fragments_with_bot(fixture.bot_record)
    config = _ok(
        compile_run_config(
            port,
            book_fragment=book_fragment,
            bms_fragment=bms_fragment,
            run_spec={
                "bot": fixture.bot_record.stable_id,
                STARTING_CAPITAL_KEY: _SEED,
                "lookback": 20,
                "sma_period": 20,
                STREAM_SET_KEY: (resolved.source.stream_id,),
            },
            workspace_defaults=RecordedReplayFixture._workspace_defaults(  # pyright: ignore[reportPrivateUsage]
                fixture.slippage_adapter
            ),
        )
    )
    bound = _ok(bind_execution_ports(config))
    binding = config.replay_binding
    assert binding is not None
    journal = JournalStore(
        World.REPLAY,
        journal_dir=tmp_path / "ct13-nofill",
        open_stream=jsonl_opener(),
    )
    writer_id = _ok(WriterId.try_create("qmb-service-test", "replay", "positions", "boot-1"))
    writer = JournalWriter(journal, writer_id, stream_name="positions")
    reader = JournalReader(journal)
    admission = _ok(RecordedReplayFixture._admission(  # pyright: ignore[reportPrivateUsage]
        binding, writer, reader
    ))
    ledger = make_trial_ledger(tmp_path / "terminal-ledger-nofill")
    result = _ok(
        execute_recorded_replay_request(
            request=resolved,
            expected_request_ref=request_ref,
            request_root=fixture.request_root,
            raw_store_root=fixture.raw_store_root,
            holdout_months=18,
            expected_split_fp1=fixture.expected_split_fp1,
            config=config,
            bound_execution=bound,
            admission=admission,
            journal_reader=reader,
            terminal_ledger=ledger,
        )
    )
    assert result.closed_trades == ()
    assert result.performance_result.measure_set is not None
    total_trades = result.performance_result.measure_set[MEASURE_IDENTITIES.index("total_trades")]
    assert isinstance(total_trades, PerformanceMeasure)
    assert getattr(total_trades.quantity, "numerator", None) == 0
