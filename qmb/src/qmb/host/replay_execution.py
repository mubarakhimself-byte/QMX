"""Run one resolved recorded request through QMB's Book and CT-32 paths.

This is the provider-free application seam shared by the QMB backtest door and
ATC replay studies. It accepts only already-resolved run configuration, execution
ports, and Book policy; it never invents a fill/order/risk policy from the bot.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import cast

from qmf.core import (
    Fingerprint,
    Instant,
    Money,
    Ok,
    Result,
    World,
    WriterId,
    fingerprint,
    is_refusal,
)
from qmf.data.journal_producer import JournalReader
from qmf.registry import RegistrationRecord
from qmf.risk.performance import PerformanceResult

from qmb._refuse import invalid, policy
from qmb.config.compiler import ASSIGNMENT_KEY, STUDY_TRIAL_LABEL_KEY, ResolvedRunConfig
from qmb.execution.binder import BoundExecution
from qmb.execution.ports import SlicePath
from qmb.host.book_handler import (
    BookAdmissionContext,
    BookExecutionSliceHandler,
    ReplayPositionRecovery,
    read_replay_positions,
)
from qmb.host.replay import RecordedReplaySource
from qmb.host.replay_request import ResolvedReplayRequest, resolve_replay_request
from qmb.ledger.line import LedgerLine
from qmb.results.ct29 import CT29ClosedTrade, read_ct29_closed_trades
from qmb.results.ct32 import mint_run_performance_result
from qmb.results.measures import ClosedTrade, EquityPoint
from qmb.runloop.loop import LoopOutcome, run

__all__ = ["RecordedExecutionResult", "execute_recorded_replay_request"]


@dataclass(frozen=True, slots=True)
class RecordedExecutionResult:
    """Completed run plus CT-13-resolved CT-29 trades and economic CT-32."""

    request_ref: Fingerprint
    source_fp1: Fingerprint
    run_fp1: Fingerprint
    outcome: LoopOutcome
    position_recovery: ReplayPositionRecovery
    closed_trades: tuple[CT29ClosedTrade, ...]
    performance_result: PerformanceResult
    terminal_line: LedgerLine


def execute_recorded_replay_request(
    *,
    request: object,
    expected_request_ref: object,
    request_root: object,
    raw_store_root: object,
    holdout_months: object,
    config: object,
    bound_execution: object,
    admission: object,
    journal_reader: object,
    terminal_ledger: object,
    expected_split_fp1: object,
    role: object = "confirmation",
    initial_resting: object = (),
    cancel: object = None,
    limits: object = None,
    probe: object = None,
    trial_proposal: object = None,
    trial_label: object = None,
    trial_generation: object = None,
) -> Result[RecordedExecutionResult]:
    """Execute selected CT-33 logic on its pinned CT-10 path and mint real economics.

    The request must already have been resolved with the trusted ExperimentSpec
    data_ref and configured QMF raw-room root. CT-13 is read before execution and
    again after successful end-of-input; aborts return their original refusal and
    never mint a completed CT-32 result.
    """
    if not isinstance(request, ResolvedReplayRequest):
        return invalid("request", "execution consumes a validated persisted replay request")
    expected_request = (
        Ok(expected_request_ref)
        if isinstance(expected_request_ref, Fingerprint)
        else Fingerprint.try_create(expected_request_ref)
    )
    if is_refusal(expected_request):
        return expected_request
    if request.request_ref != expected_request.value:
        return policy("request_ref", "resolved request matches trusted CT-47 evidence_ref")
    supplied_source: object = getattr(request, "source", None)
    if not isinstance(supplied_source, RecordedReplaySource):
        return invalid("source", "resolved replay source is the typed CT-10 materialization")
    canonical_request = resolve_replay_request(
        request_root=request_root,
        request_ref=expected_request.value,
        expected_split_fp1=expected_split_fp1,
        raw_store_root=raw_store_root,
        holdout_months=holdout_months,
    )
    if is_refusal(canonical_request):
        return canonical_request
    if not _same_materialized_source(supplied_source, canonical_request.value.source):
        return policy(
            "source_materialization",
            "execution paths, slices, and read surfaces match fresh CT-10 readback",
        )
    request = canonical_request.value
    if not isinstance(config, ResolvedRunConfig) or config.world is not World.REPLAY:
        return invalid("config", "recorded QMB execution uses a resolved world=replay config")
    if role == "trial":
        raw_trial_label = config.keys.get(STUDY_TRIAL_LABEL_KEY)
        if raw_trial_label is None:
            return invalid(
                "study_trial_label",
                "optimizer ledger trials require a sampler-minted label in the run-config",
            )
        from qmb.optimize.sampler import validate_trial_label  # noqa: PLC0415

        checked_trial_label = validate_trial_label(raw_trial_label)
        if is_refusal(checked_trial_label):
            return checked_trial_label
        if checked_trial_label.value.get("role") != "trial":
            return policy("study_trial_label", "optimizer replay is labeled role=trial")
        from qmb.optimize import validate_trial_binding  # noqa: PLC0415

        if trial_proposal is None or trial_label is None or trial_generation is None:
            return invalid(
                "trial_binding",
                "optimizer execution carries its typed proposal, sampler label, and generation",
            )
        checked_binding = validate_trial_binding(
            config,
            trial_proposal,
            trial_label,
            generation=trial_generation,
        )
        if is_refusal(checked_binding):
            return checked_binding
    elif (
        STUDY_TRIAL_LABEL_KEY in config.keys
        or trial_proposal is not None
        or trial_label is not None
        or trial_generation is not None
    ):
        return policy(
            "study_trial_label",
            "a sampler-labeled run is written only through the optimizer trial role",
        )
    if not isinstance(bound_execution, BoundExecution) or bound_execution.config != config:
        return policy("bound_execution", "Book execution ports are bound to this resolved config")
    if not isinstance(admission, BookAdmissionContext):
        return invalid("admission", "all Book risk, order, and close policies are explicit")
    binding = config.replay_binding
    if binding is None or binding != admission.binding:
        return policy("binding", "the run config and Book policy share the exact CT-28 epoch")
    config_stamp = fingerprint(config.fp1_identity())
    if is_refusal(config_stamp):
        return config_stamp
    if config_stamp.value != config.fingerprint:
        return policy("config_fp1", "resolved run-config fields match their CT-28 run identity")
    binding_stamp = binding.record.fingerprint()
    if is_refusal(binding_stamp):
        return binding_stamp
    if binding_stamp.value != binding.fingerprint:
        return policy("binding_fp1", "CT-28 replay epoch matches its typed binding record")
    from qml.declaration import BotDefinition  # noqa: PLC0415

    declared_bot = BotDefinition.try_from_mapping(request.hosted.declaration)
    if is_refusal(declared_bot):
        return declared_bot
    bot_identity = declared_bot.value.identity_payload()
    bot_kind = bot_identity.get("kind")
    bot_contract_version = bot_identity.get("contract_format_version")
    bot_body = bot_identity.get("body")
    bot_parents = bot_identity.get("at_birth_parent_refs", [])
    raw_parent_refs = cast(list[object], bot_parents) if isinstance(bot_parents, list) else []
    if (
        not isinstance(bot_kind, str)
        or isinstance(bot_contract_version, bool)
        or not isinstance(bot_contract_version, int)
        or not isinstance(bot_body, Mapping)
        or not isinstance(bot_parents, list)
        or any(not isinstance(parent, str) for parent in raw_parent_refs)
    ):
        return invalid("bot_identity", "selected CT-33 definition has a canonical CT-06 identity")
    parent_refs = [cast(str, parent) for parent in raw_parent_refs]
    body_mapping = cast(Mapping[str, object], bot_body)
    identity_writer = WriterId.try_create("qmb-runtime", "identity-check", "bot", "ephemeral")
    if is_refusal(identity_writer):
        return identity_writer
    identity_instant = Instant.try_create(0)
    if is_refusal(identity_instant):
        return identity_instant
    registered_bot = RegistrationRecord.try_create(
        bot_kind,
        bot_contract_version,
        parent_refs,
        body_mapping,
        identity_writer.value,
        0,
        identity_instant.value,
    )
    if is_refusal(registered_bot):
        return registered_bot
    bot_stamp = Ok(registered_bot.value.stable_id)
    if is_refusal(bot_stamp):
        return bot_stamp
    if bot_stamp.value != config.bot_fp1:
        return policy("bot_fp1", "selected hosted source is the Bot pinned by run-config")
    assignment = config.keys.get(ASSIGNMENT_KEY)
    if assignment is None and not request.hosted.assignment:
        assignment = {}
    if not isinstance(assignment, Mapping) or dict(cast(Mapping[str, object], assignment)) != dict(
        request.hosted.assignment
    ):
        return policy(
            "assignment",
            "hosted Bot parameters equal the compiled CT-33 assignment in run-config",
        )
    if not isinstance(journal_reader, JournalReader):
        return invalid("journal_reader", "CT-13 recovery uses the configured QMF JournalReader")
    # Local import avoids making the replay host module part of orchestrator's
    # import cycle while still requiring its canonical durable writer.
    from qmb.ledger.line import (  # noqa: PLC0415
        WORKBENCH_LANE_GOVERNED,
        mint_completed_line,
    )
    from qmb.orchestrator.ledger import (  # noqa: PLC0415
        LedgerSink,
        read_merge_view,
    )

    if not isinstance(terminal_ledger, LedgerSink):
        return invalid("terminal_ledger", "successful replay requires the governed LedgerSink")
    source_stamp = fingerprint(request.source.fp1_identity())
    if is_refusal(source_stamp):
        return source_stamp
    source_fp = source_stamp.value
    if source_fp != request.source.fingerprint:
        return policy("source_fp1", "materialized source content matches its pinned identity")
    if request.source.split_fp1 is None or request.source.split_role is None:
        return policy("split", "the governed execution request carries its CT-12 split and role")
    expected_split = (
        Ok(expected_split_fp1)
        if isinstance(expected_split_fp1, Fingerprint)
        else Fingerprint.try_create(expected_split_fp1)
    )
    if is_refusal(expected_split):
        return expected_split
    if (
        request.split_fp1 != expected_split.value
        or request.source.split_fp1 != expected_split.value
    ):
        return policy(
            "split_fp1",
            "the request's CT-12 source identity equals the trusted registered data_ref",
        )
    if (
        config.book_fp1 != binding.record.book_definition_fingerprint
        or config.bms_fp1 != binding.record.bms_definition_fingerprint
    ):
        return policy("book_fp1", "the resolved Book and ReplayBinding identify the same Book")
    recovery = read_replay_positions(
        journal_reader=journal_reader,
        stream_name=admission.journal_writer.stream_name,
        writer=admission.journal_writer.writer,
        binding_epoch=binding.fingerprint,
        result_label=admission.result_label,
    )
    if is_refusal(recovery):
        return recovery
    handler = BookExecutionSliceHandler.try_create(
        hosted=request.hosted,
        stream_id=request.source.stream_id,
        bound_execution=bound_execution,
        admission=admission,
        recovery=recovery.value,
    )
    if is_refusal(handler):
        return handler
    paths = _bind_source_paths(request.source)
    if is_refusal(paths):
        return paths
    bound_paths = handler.value.bind_paths(paths.value)
    if is_refusal(bound_paths):
        return bound_paths
    outcome = run(
        slices=request.source.slices,
        config=config,
        handler=handler.value,
        initial_resting=initial_resting,
        cancel=cancel,
        limits=limits,
        probe=probe,
    )
    if is_refusal(outcome):
        cause = outcome.context.get("cause")
        if cause in {"cancel", "time-limit", "memory-limit"}:
            last_frontier = handler.value.last_processed_frontier
            if handler.value.pending_entry_tickets:
                if last_frontier is None:
                    return policy(
                        "terminal_frontier",
                        "known cancellation terminalizes partial entries only at a "
                        "processed frontier",
                    )
                cancelled = handler.value.cancel_pending_entries(at=last_frontier)
                if is_refusal(cancelled):
                    return cancelled
            aborted_recovery = read_replay_positions(
                journal_reader=journal_reader,
                stream_name=admission.journal_writer.stream_name,
                writer=admission.journal_writer.writer,
                binding_epoch=binding.fingerprint,
                result_label=admission.result_label,
            )
            if is_refusal(aborted_recovery):
                return aborted_recovery
            aborted_line = _persist_aborted_terminal(
                terminal_ledger=terminal_ledger,
                config=config,
                refusal=outcome,
            )
            if is_refusal(aborted_line):
                return aborted_line
        return outcome
    if not outcome.value.slices:
        return invalid("slices", "economic execution requires at least one completed slice")
    terminal_at = outcome.value.slices[-1].frontier
    finalized = handler.value.finalize_pending_entries(at=terminal_at)
    if is_refusal(finalized):
        return finalized
    if handler.value.positions:
        return policy(
            "open_positions",
            "a completed CT-32 result requires all replay positions to close in recorded data",
            count=len(handler.value.positions),
        )
    final_recovery = read_replay_positions(
        journal_reader=journal_reader,
        stream_name=admission.journal_writer.stream_name,
        writer=admission.journal_writer.writer,
        binding_epoch=binding.fingerprint,
        result_label=admission.result_label,
    )
    if is_refusal(final_recovery):
        return final_recovery
    if any(not position.closed for position in final_recovery.value.positions):
        return policy("position_recovery", "CT-13 terminal fold contains no open positions")
    closed = read_ct29_closed_trades(
        journal_reader=journal_reader,
        stream_name=admission.journal_writer.stream_name,
        writer=admission.journal_writer.writer,
        record_resolver=final_recovery.value.record_resolver,
        position_sides=final_recovery.value.position_sides,
        binding_epoch=binding.fingerprint,
        result_label=admission.result_label,
    )
    if is_refusal(closed):
        return closed
    journal_events = journal_reader.read_checked(
        admission.journal_writer.stream_name,
        for_world=World.REPLAY,
    )
    if is_refusal(journal_events):
        return journal_events
    trades = tuple(item.closed_trade for item in closed.value)
    equity = _realized_equity_curve(
        binding.starting_capital,
        outcome.value.evidence_range.start,
        outcome.value.evidence_range.end,
        trades,
    )
    if is_refusal(equity):
        return equity
    economic_result = mint_run_performance_result(
        config,
        evidence_range=outcome.value.evidence_range,
        stream_order=outcome.value.stream_order,
        slice_count=len(outcome.value.slices),
        filled_count=len(outcome.value.filled),
        resting_count=len(outcome.value.resting),
        data_points_processed=outcome.value.data_points_processed,
        outcome_identity=outcome.value.fp1_identity(),
        trades=trades,
        equity_curve=equity.value,
        starting_capital=binding.starting_capital,
        journal_events=journal_events.value,
    )
    if is_refusal(economic_result):
        return economic_result
    terminalized = set(handler.value.finalized_resting_intent_ids)
    completed = replace(
        outcome.value,
        resting=tuple(
            intent for intent in outcome.value.resting if intent.intent_id not in terminalized
        ),
        performance_result=economic_result.value,
    )
    ct32_fp = economic_result.value.fingerprint()
    if is_refusal(ct32_fp):
        return ct32_fp
    terminal = mint_completed_line(
        config,
        outcome_identity=outcome.value.fp1_identity(),
        ct32_fingerprint=ct32_fp.value,
        performance_result=economic_result.value,
        role=role,
        workbench_lane=WORKBENCH_LANE_GOVERNED,
    )
    if is_refusal(terminal):
        return terminal
    persisted = terminal_ledger.append(terminal.value)
    if is_refusal(persisted):
        return persisted
    if (
        type(persisted.value) is not LedgerLine
        or persisted.value.fp1_identity() != terminal.value.fp1_identity()
    ):
        return policy(
            "terminal_ledger",
            "the durable writer acknowledgement matches the actual CT-32 terminal line",
        )
    readback = read_merge_view(
        terminal_ledger.root,
        world=config.world,
        role=role,
    )
    if is_refusal(readback):
        return readback
    matching_lines = tuple(line for line in readback.value if line.run_id == config.fingerprint)
    if (
        len(matching_lines) != 1
        or matching_lines[0].fp1_identity() != terminal.value.fp1_identity()
    ):
        return policy(
            "terminal_ledger",
            "the terminal CT-32 line is present exactly once in durable ledger readback",
        )
    return Ok(
        RecordedExecutionResult(
            request_ref=request.request_ref,
            source_fp1=source_fp,
            run_fp1=config.fingerprint,
            outcome=completed,
            position_recovery=final_recovery.value,
            closed_trades=closed.value,
            performance_result=economic_result.value,
            terminal_line=persisted.value,
        )
    )


def _bind_source_paths(
    source: RecordedReplaySource,
) -> Result[tuple[tuple[Instant, SlicePath], ...]]:
    if len(source.slices) != len(source.execution_paths):
        return invalid("execution_paths", "each materialized replay slice has one source path")
    pairs: list[tuple[Instant, SlicePath]] = []
    for event_slice, path in zip(source.slices, source.execution_paths, strict=True):
        if len(event_slice.observations) != 1:
            return invalid("slice", "recorded replay paths bind to one stream observation")
        pairs.append((event_slice.observations[0].instant, path))
    return Ok(tuple(pairs))


def _persist_aborted_terminal(
    *,
    terminal_ledger: object,
    config: ResolvedRunConfig,
    refusal: object,
) -> Result[None]:
    """Write/read back a known cooperative abort without minting CT-32."""
    from qmb.ledger.line import (  # noqa: PLC0415
        WORKBENCH_LANE_GOVERNED,
        mint_aborted_line,
    )
    from qmb.orchestrator.ledger import LedgerSink, read_merge_view  # noqa: PLC0415

    if not isinstance(terminal_ledger, LedgerSink):
        return invalid("terminal_ledger", "abort terminal requires the governed LedgerSink")
    line = mint_aborted_line(
        config,
        refusal,
        workbench_lane=WORKBENCH_LANE_GOVERNED,
    )
    if is_refusal(line):
        return line
    appended = terminal_ledger.append(line.value)
    if is_refusal(appended):
        return appended
    if type(appended.value) is not LedgerLine or (
        appended.value.fp1_identity() != line.value.fp1_identity()
    ):
        return policy("terminal_ledger", "abort acknowledgement matches the durable line")
    rows = read_merge_view(
        terminal_ledger.root,
        world=config.world,
        role="aborted",
    )
    if is_refusal(rows):
        return rows
    matching = tuple(row for row in rows.value if row.run_id == config.fingerprint)
    if len(matching) != 1 or matching[0].fp1_identity() != line.value.fp1_identity():
        return policy("terminal_ledger", "aborted line appears exactly once in ledger readback")
    return Ok(None)


def _realized_equity_curve(
    starting_capital: Money,
    period_start: Instant,
    period_end: Instant,
    trades: tuple[ClosedTrade, ...],
) -> Result[tuple[EquityPoint, ...]]:
    first = EquityPoint.try_create(period_start, starting_capital)
    if is_refusal(first):
        return first
    points = [first.value]
    balance = starting_capital
    ordered = sorted(trades, key=lambda item: item.closed_at.value_ns)
    for trade in ordered:
        updated = balance.add(trade.realized_pnl)
        if is_refusal(updated):
            return updated
        balance = updated.value
        point = EquityPoint.try_create(trade.closed_at, balance)
        if is_refusal(point):
            return point
        points.append(point.value)
    if points[-1].at.value_ns < period_end.value_ns:
        closing = EquityPoint.try_create(period_end, balance)
        if is_refusal(closing):
            return closing
        points.append(closing.value)
    return Ok(tuple(points))


def _same_materialized_source(
    supplied: RecordedReplaySource,
    authoritative: RecordedReplaySource,
) -> bool:
    """Compare derived runtime surfaces against a fresh canonical CT-10 materialization."""
    if supplied.fp1_identity() != authoritative.fp1_identity():
        return False
    if tuple(item.fingerprint for item in supplied.observations) != tuple(
        item.fingerprint for item in authoritative.observations
    ):
        return False
    if tuple(item.fp1_identity() for item in supplied.slices) != tuple(
        item.fp1_identity() for item in authoritative.slices
    ):
        return False
    if tuple(item.fp1_identity() for item in supplied.execution_paths) != tuple(
        item.fp1_identity() for item in authoritative.execution_paths
    ):
        return False
    if set(supplied.read_surfaces) != set(authoritative.read_surfaces):
        return False
    return all(
        supplied.read_surfaces[name].frames == authoritative.read_surfaces[name].frames
        for name in supplied.read_surfaces
    )
