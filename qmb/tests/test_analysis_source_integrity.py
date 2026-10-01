"""Projection source provenance controls over a real CT-13/CT-29 close witness."""

import json
from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

from qmb.analysis import CT29ProjectionSource, cite_projection, project
from qmb.results.ct32 import PerformanceResult
from qmf.core import Result, WriterId, fingerprint, is_ok, is_refusal
from replay_fixture_support import ProjectionReplayFixture, build_projection_replay
from test_analysis_project import (
    _at,  # pyright: ignore[reportPrivateUsage]
    _trade,  # pyright: ignore[reportPrivateUsage]
)

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _durable_close(tmp_path: Path) -> tuple[CT29ProjectionSource, PerformanceResult]:
    built: Result[ProjectionReplayFixture] = build_projection_replay(
        tmp_path, registry_as_of=_at(hour=0)
    )
    execution = _ok(built)
    assert len(execution.closed_trades) == 1
    return execution.source, execution.performance_result


def test_projection_resolves_only_durable_ct29_rows_and_saved_view_stays_reference_only(
    tmp_path: Path,
) -> None:
    source, artifact = _durable_close(tmp_path)
    as_of = _at(hour=0)
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
            "records": (),
        },
        predicate=predicate,
        as_of=as_of,
    )
    assert is_refusal(mapped_substitution)
    foreign_config_fp = _ok(fingerprint({"foreign": "run-config"}))
    foreign_label = replace(
        artifact.result_label,
        input_fingerprints=(foreign_config_fp, *artifact.result_label.input_fingerprints[1:]),
    )
    foreign_metrics = replace(artifact, result_label=foreign_label)
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
            run_config=source.run_config,
            replay_request=source.replay_request,
            terminal_ledger_root=source.terminal_ledger_root,
            ledger_role=source.ledger_role,
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
            run_config=source.run_config,
            replay_request=source.replay_request,
            terminal_ledger_root=source.terminal_ledger_root,
            ledger_role=source.ledger_role,
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
            run_config=source.run_config,
            replay_request=source.replay_request,
            terminal_ledger_root=source.terminal_ledger_root,
            ledger_role=source.ledger_role,
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
