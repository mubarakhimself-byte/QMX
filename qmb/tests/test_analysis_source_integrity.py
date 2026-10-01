"""Projection source provenance controls over a real CT-13/CT-29 close witness."""

import json
from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

from qmb.analysis import CT29ProjectionSource, cite_projection, project
from qmb.host.book_handler import read_replay_positions
from qmb.results.ct29 import read_ct29_closed_trades
from qmb.results.measures import ClosedTrade
from qmf.core import Instant, Result, WriterId, fingerprint, is_ok, is_refusal
from qmf.risk.door import Direction, EntryIntent, ExitIntent, ExitKind, ReasonCode
from test_analysis_project import (
    _at,  # pyright: ignore[reportPrivateUsage]
    _result,  # pyright: ignore[reportPrivateUsage]
    _trade,  # pyright: ignore[reportPrivateUsage]
)
from test_book_handler import (
    _handler,  # pyright: ignore[reportPrivateUsage]
    _instrument,  # pyright: ignore[reportPrivateUsage]
    _path,  # pyright: ignore[reportPrivateUsage]
)

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _durable_close(tmp_path: Path) -> tuple[CT29ProjectionSource, ClosedTrade]:
    handler, bot, reader, writer = _handler(tmp_path)
    opened_at = _ok(Instant.try_create(1_700_000_000_000_000_000))
    closed_at = _ok(Instant.try_create(opened_at.value_ns + 1_000_000_000))
    entry = _ok(
        EntryIntent.try_create(
            _instrument(),
            Direction.LONG,
            _ok(ReasonCode.try_create("breakout", "family")),
            handler.admission.execution_target,
        )
    )
    bot.proposals = (entry,)
    _ok(handler.bind_paths(((opened_at, _path(110_000, 110_100, 109_900)),)))
    resting = _ok(handler.mint_intents("eurusd", opened_at))[0]
    _ok(handler.execute_resting(resting, None, opened_at))
    opened = handler.receipts[-1].position
    assert opened is not None
    close_intent = _ok(
        ExitIntent.try_create(
            ExitKind.CLOSE_FULL,
            _ok(ReasonCode.try_create("target", "family")),
            opened.position_ref,
        )
    )
    bot.proposals = (close_intent,)
    _ok(handler.bind_paths(((closed_at, _path(110_000, 110_100, 109_800)),)))
    closing = _ok(handler.mint_intents("eurusd", closed_at))[0]
    _ok(handler.execute_resting(closing, None, closed_at))
    recovered = _ok(
        read_replay_positions(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=opened.binding_epoch,
            result_label=handler.admission.result_label,
        )
    )
    trades = _ok(
        read_ct29_closed_trades(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            record_resolver=recovered.record_resolver,
            position_sides=recovered.position_sides,
            binding_epoch=opened.binding_epoch,
            result_label=handler.admission.result_label,
        )
    )
    assert len(trades) == 1
    source = _ok(
        CT29ProjectionSource.try_create(
            journal_reader=reader,
            stream_name="positions",
            writer=writer,
            binding_epoch=opened.binding_epoch,
            result_label=handler.admission.result_label,
        )
    )
    return source, trades[0].closed_trade


def test_projection_resolves_only_durable_ct29_rows_and_saved_view_stays_reference_only(
    tmp_path: Path,
) -> None:
    as_of = _at(hour=0)
    source, original = _durable_close(tmp_path)
    artifact = _result(registry_as_of=as_of, trades=(original,))
    artifact = replace(
        artifact,
        trade_event_references=(f"ct-13:ct-29:{source.binding_epoch.value}",),
    )
    predicate = {"max_trades": 1}
    positive = project(
        source_ct32=artifact,
        source_ct29=source,
        predicate=predicate,
        as_of=as_of,
        home="governed",
        run_dir=tmp_path,
    )
    assert is_ok(positive), positive
    assert positive.value.durable is True
    assert positive.value.matched_count == 1
    sidecar = Path(cast(str, positive.value.path))
    body = cast(dict[str, object], json.loads(sidecar.read_text(encoding="utf-8")))
    assert "trades" not in body and "trade_list" not in body
    reopened_view = _ok(cite_projection(body=body))
    assert reopened_view.body() == body
    substituted = project(
        source_ct32=artifact,
        source_ct29=(_trade(hour=18, pnl=999999),),
        predicate=predicate,
        as_of=as_of,
    )
    assert is_refusal(substituted), (
        "unverified substituted CT29 rows must not inherit the artifact's binding cite",
        substituted,
    )
    mapped_substitution = project(
        source_ct32=artifact,
        source_ct29={
            "source_ct29": artifact.trade_event_references[0],
            "records": (original,),
        },
        predicate=predicate,
        as_of=as_of,
    )
    assert is_refusal(mapped_substitution)
    foreign_metrics = replace(
        _result(registry_as_of=as_of, trades=(_trade(hour=18, pnl=999999),)),
        trade_event_references=artifact.trade_event_references,
    )
    assert is_refusal(
        project(
            source_ct32=foreign_metrics,
            source_ct29=source,
            predicate=predicate,
            as_of=as_of,
        )
    )
    foreign_stream = _ok(
        CT29ProjectionSource.try_create(
            journal_reader=source.journal_reader,
            stream_name="foreign-empty-stream",
            writer=source.writer,
            binding_epoch=source.binding_epoch,
            result_label=source.result_label,
        )
    )
    assert is_refusal(
        project(source_ct32=artifact, source_ct29=foreign_stream, predicate=predicate, as_of=as_of)
    )
    foreign_writer = _ok(
        WriterId.try_create(
            "foreign-machine",
            source.writer.role,
            source.writer.stream,
            source.writer.boot_epoch_id,
        )
    )
    forged_writer = _ok(
        source.try_create(
            journal_reader=source.journal_reader,
            stream_name=source.stream_name,
            writer=foreign_writer,
            binding_epoch=source.binding_epoch,
            result_label=source.result_label,
        )
    )
    assert is_refusal(
        project(source_ct32=artifact, source_ct29=forged_writer, predicate=predicate, as_of=as_of)
    )
    wrong_binding = _ok(fingerprint({"binding": "foreign"}))
    mismatched_binding = _ok(
        source.try_create(
            journal_reader=source.journal_reader,
            stream_name=source.stream_name,
            writer=source.writer,
            binding_epoch=wrong_binding,
            result_label=source.result_label,
        )
    )
    assert is_refusal(
        project(
            source_ct32=artifact,
            source_ct29=mismatched_binding,
            predicate=predicate,
            as_of=as_of,
        )
    )
