"""Source QMB CLI child execution through the trusted delegated door."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import TypeVar, cast

from qmb.config.compiler import ResolvedRunConfig
from qmb.execution.binder import BoundExecution
from qmb.host.book_handler import BookAdmissionContext
from qmb.host.operator_replay import (
    OPERATOR_BINDING_FORMAT_VERSION,
    OPERATOR_BINDING_KIND,
    _canonical_registry,  # pyright: ignore[reportPrivateUsage]
    _decode_binding,  # pyright: ignore[reportPrivateUsage]
    _entrypoint,  # pyright: ignore[reportPrivateUsage]
    _load_builder,  # pyright: ignore[reportPrivateUsage]
    _materialize_builder,  # pyright: ignore[reportPrivateUsage]
    _runtime_policy_identity,  # pyright: ignore[reportPrivateUsage]
)
from qmb.host.qma_cli import QmaBacktestContext
from qmb.host.replay_request import ReplayInputRequest, persist_replay_request
from qmb.orchestrator.ledger import read_merge_view
from qmf.core import Fingerprint, Result, World, fingerprint, is_ok
from qmf.data.splits import SegmentRole
from qmf.data.store import EvidenceStore
from qmf.registry import RegistryPersistence
from replay_fixture_support import make_recorded_replay_fixture
from test_ql7_host import (  # pyright: ignore[reportPrivateUsage]
    _SEVERITY,  # pyright: ignore[reportPrivateUsage]
    _bms,  # pyright: ignore[reportPrivateUsage]
    _book,  # pyright: ignore[reportPrivateUsage]
    study_fixture_record,
)

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _builder_source() -> str:
    return '''from pathlib import Path
from qmb.config import STARTING_CAPITAL_KEY, compile_run_config
from qmb.execution import (COST_ADAPTER_KEY, COST_ADAPTER_PER_LOT, COST_CALIBRATION_KEY,
    FILL_ADAPTER_DECLARED_PATH, FILL_ADAPTER_KEY, FILL_BASIS_KEY,
    FILL_BASIS_OPTIMISTIC_EXACT, FINANCING_SCHEDULE_KEY, SLIPPAGE_ADAPTER_KEY,
    SLIPPAGE_ADAPTER_ZERO, CommissionCalibration, bind_execution_ports)
from qmb.execution.fill import OrderType
from qmb.host.book_handler import BookAdmissionContext, BookOrderPolicy
from qmb.host.operator_replay import OPERATOR_BINDING_CONFIG_KEY
from qmb.host.replay_request import resolve_replay_request
from qmb.orchestrator.ledger import LedgerSink
from qmb.runloop import STREAM_SET_KEY
from qmf.core import (
    AccountRole, ExactRational, Instrument, Ok, Quantity, Result, UnitKind,
    ValueFactor, VenueId, World,
)
from qmf.core.chrono import Instant, WriterId
from qmf.core.exact import Money, Price
from qmf.core.refusal import is_refusal
from qmf.data.journal_producer import JournalReader, JournalWriter
from qmf.data.store import JournalStore, jsonl_opener
from qmf.risk.door import Direction, ExitLogicRef, ReasonCode
from qmf.risk.exit_record import CloseReason, ExitResultLabel
from qmf.risk.paper import ExecutionTarget

class StopLogic:
    def derive_full_loss_price(self, *, entry_price: Price, direction: Direction,
                               cited_evidence: object) -> Result[Price]:
        del cited_evidence
        offset = 500 if direction is Direction.LONG else -500
        return Price.try_create(
            entry_price.value - offset, entry_price.instrument, entry_price.scale
        )

class RecordedCalendar:
    def fp1_identity(self):
        return {"class": "recorded-no-rollover-calendar-v1", "fixture": "three-quote-replay"}
    def is_rollover_instant(self, instant: Instant) -> Result[bool]:
        del instant
        return Ok(False)
    def trading_date_of(self, instant: Instant) -> Result[TradingDate]:
        del instant
        return Ok(None)
    def weekday_of(self, trading_date: TradingDate) -> Result[str]:
        del trading_date
        return Ok("tuesday")
    def is_weekend_or_holiday(self, trading_date: TradingDate) -> Result[bool]:
        del trading_date
        return Ok(False)

def build(context, binding, port, book_fragment, bms_fragment):
    request = resolve_replay_request(request_root=binding.roots["requests"],
        request_ref=context.evidence_ref, split=None,
        expected_split_fp1=context.split_manifest_fp1,
        raw_store_root=binding.roots["raw"], holdout_months=binding.holdout_months)
    if is_refusal(request):
        return request
    commission = CommissionCalibration.try_create(COST_ADAPTER_PER_LOT, "replay-broker",
        currency="USD", per_lot=Money.try_create(100, "USD", 2).value)
    if is_refusal(commission):
        return commission
    defaults = {
        "account_id": "acct-replay", "clock": "replay",
        "data_provenance": "recorded", "fill": "default-fill", "venue_id": "venue-replay",
        COST_ADAPTER_KEY: COST_ADAPTER_PER_LOT, COST_CALIBRATION_KEY: commission.value,
        FILL_ADAPTER_KEY: FILL_ADAPTER_DECLARED_PATH, FILL_BASIS_KEY: FILL_BASIS_OPTIMISTIC_EXACT,
        FINANCING_SCHEDULE_KEY: "replay-swap-table", SLIPPAGE_ADAPTER_KEY: SLIPPAGE_ADAPTER_ZERO,
        STREAM_SET_KEY: (request.value.source.stream_id,),
    }
    compiled = compile_run_config(port, book_fragment=book_fragment, bms_fragment=bms_fragment,
        run_spec={
            "bot": binding.record_refs["bot"].value,
            STARTING_CAPITAL_KEY: Money.try_create(1000000, "USD", 2).value,
            **dict(request.value.hosted.assignment),
            STREAM_SET_KEY: (request.value.source.stream_id,),
        },
        invocation_flags={OPERATOR_BINDING_CONFIG_KEY: binding.descriptor_fp1.value},
        workspace_defaults=defaults)
    if is_refusal(compiled):
        return compiled
    bound = bind_execution_ports(compiled.value)
    if is_refusal(bound):
        return bound
    journal = JournalStore(World.REPLAY, journal_dir=binding.roots["journal"] / context.job_id,
        open_stream=jsonl_opener())
    writer_id = WriterId.try_create("qmb-cli-fixture", "replay", "positions", "boot-1")
    if is_refusal(writer_id):
        return writer_id
    writer = JournalWriter(journal, writer_id.value, stream_name="positions")
    reader = JournalReader(journal)
    config_binding = compiled.value.replay_binding
    if config_binding is None:
        return compiled
    instrument = Instrument(VenueId("replay-venue"), "EURUSD")
    stop_reason = ReasonCode.try_create("protective_stop", "family")
    target = ExecutionTarget.try_create(AccountRole.DEMO.value,
        config_binding.record.venue_id, config_binding.record.account_id)
    exit_ref = ExitLogicRef.try_create("book.stop", {})
    result_label = ExitResultLabel.try_create(AccountRole.DEMO, World.REPLAY)
    rate = ExactRational.try_create(100, 1, UnitKind.RATE)
    risk = ExactRational.try_create(1, 1, UnitKind.R_MULTIPLE)
    factor = ValueFactor.try_create(20000, 1, instrument, "USD")
    step = Quantity.try_create(1, "lot", 0)
    cap = Quantity.try_create(5, "lot", 0)
    values = (stop_reason, target, exit_ref, result_label, rate, risk, factor, step, cap)
    if any(is_refusal(value) for value in values):
        return values[0]
    admission = BookAdmissionContext.try_create(binding=config_binding,
        exit_logic_ref=exit_ref.value, exit_logic_module=StopLogic(), requested_r=risk.value,
        r_unit_price=rate.value, value_factor=factor.value, money_scale=2,
        lot_step=step.value, position_cap=cap.value, execution_target=target.value,
        result_label=result_label.value, opening_bot_id="qmb-cli-fixture-bot",
        close_reason_by_code={"exit:family:protective_stop": CloseReason.PROTECTIVE_STOP_FILL},
        order_policy_by_code={"entry:family:breakout": BookOrderPolicy(OrderType.MARKET),
            "exit:family:protective_stop": BookOrderPolicy(OrderType.STOP)},
        journal_writer=writer, journal_reader=reader, rollover_calendar=RecordedCalendar(),
        protective_stop_reason=stop_reason.value)
    if is_refusal(admission):
        return admission
    ledger = LedgerSink.try_create(binding.roots["terminal_ledger"],
        machine="qmb-cli-fixture", worker_slot=f"{context.job_id}-{context.attempt_id}",
        boot_epoch_id="boot-1")
    if is_refusal(ledger):
        return ledger
    return Ok({"request": request.value, "config": compiled.value,
        "bound_execution": bound.value, "admission": admission.value,
        "journal_reader": reader, "terminal_ledger": ledger.value})
'''


def _context_payload(request_ref: Fingerprint, split_fp: Fingerprint) -> dict[str, object]:
    spec = _ok(fingerprint({"class": "registered-experiment-spec-test"}))
    return {
        "job_id": "job-cli-replay",
        "attempt_id": 1,
        "experiment_spec_fp1": spec.value,
        "evidence_ref": request_ref.value,
        "environment_ref": "env:local-recorded-fixture",
        "occupancy_key": "qmb:job-cli-replay",
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
        "split_manifest_fp1": split_fp.value,
    }


def _environment(payload: dict[str, object], runtime_root: Path) -> dict[str, str]:
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
        "QMB_REPLAY_RUNTIME_ROOT": str(runtime_root),
    }


def _initial_descriptor(
    context: QmaBacktestContext,
    roots: dict[str, Path],
    bot_ref: Fingerprint,
    book_ref: Fingerprint,
    bms_ref: Fingerprint,
) -> dict[str, object]:
    files = {"runtime_builder.py": _builder_source()}
    builder_stamp = _ok(
        fingerprint({"class": "qmb-operator-builder-source-v1", "files": files})
    )
    policy_identity: dict[str, object] = {}
    body: dict[str, object] = {
        "class": OPERATOR_BINDING_KIND,
        "format_version": OPERATOR_BINDING_FORMAT_VERSION,
        "experiment_spec_fp1": context.experiment_spec_fp1.value,
        "evidence_ref": context.evidence_ref.value,
        "split_manifest_fp1": context.split_manifest_fp1.value,
        "holdout_months": 18,
        "record_refs": {"bot": bot_ref.value, "book": book_ref.value, "bms": bms_ref.value},
        "roots": {key: str(value) for key, value in roots.items()},
        "registry_as_of_ns": 1_800_000_000_000_000_000,
        "registry_writer": {
            "actor": "node-a",
            "role": "authoring",
            "stream": "config-fragment",
            "boot_epoch": "boot-1",
        },
        "registry_stale_evidence_severity": _SEVERITY,
        "policy_identity": policy_identity,
        "policy_fp1": _ok(fingerprint(policy_identity)).value,
        "builder_files": files,
        "builder_fp1": builder_stamp.value,
        "entrypoint": "runtime_builder:build",
    }
    body["descriptor_fp1"] = _ok(fingerprint(body)).value
    return body


def _binding(body: dict[str, object], context: QmaBacktestContext):
    return _ok(_decode_binding(body, context))


def _persist_registry(root: Path, records: tuple[object, ...]) -> None:
    persistence = _ok(RegistryPersistence.open(EvidenceStore(root), World.REPLAY))
    for record in records:
        _ok(persistence.persist_record(record))
    persistence.close()


def test_installed_qmb_cli_executes_registered_replay_to_durable_economic_result(
    tmp_path: Path,
) -> None:
    fixture = make_recorded_replay_fixture(tmp_path / "data")
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
    book_record = study_fixture_record("book-definition", _book())
    bms_record = study_fixture_record("bms-definition", _bms())
    registry_root = tmp_path / "registry"
    _persist_registry(registry_root, (fixture.bot_record, book_record, bms_record))
    roots = {
        "registry": registry_root,
        "raw": fixture.raw_store_root,
        "requests": fixture.request_root,
        "journal": tmp_path / "journal",
        "terminal_ledger": tmp_path / "ledger",
    }
    payload = _context_payload(request_ref, fixture.expected_split_fp1)
    from qmb.host.qma_cli import decode_qma_backtest_context

    env = _environment(payload, tmp_path / "runtime")
    context = _ok(
        decode_qma_backtest_context(
            payload_text=env["QMA_QMB_DOOR_PAYLOAD"], environ=env
        )
    )
    body = _initial_descriptor(
        context,
        roots,
        fixture.bot_record.stable_id,
        book_record.stable_id,
        bms_record.stable_id,
    )
    binding = _binding(body, context)
    registry = _ok(_canonical_registry(binding))
    with tempfile.TemporaryDirectory(prefix="qmb-operator-test-builder-") as temporary:
        builder_root = Path(temporary)
        _ok(_materialize_builder(binding.builder_files, builder_root))
        module = _ok(_load_builder(builder_root, binding.builder_files, binding.entrypoint))
        builder = _ok(_entrypoint(module, binding.entrypoint))
        built = _ok(builder(context, binding, *registry))
        built_mapping = cast(Mapping[str, object], built)
        policy_identity = _ok(
            _runtime_policy_identity(
                cast(ResolvedRunConfig, built_mapping["config"]),
                cast(BoundExecution, built_mapping["bound_execution"]),
                cast(BookAdmissionContext, built_mapping["admission"]),
                binding.builder_fp1,
                binding.builder_files,
            )
        )
    body["policy_identity"] = dict(policy_identity)
    body["policy_fp1"] = _ok(fingerprint(policy_identity)).value
    identity = {key: value for key, value in body.items() if key != "descriptor_fp1"}
    body["descriptor_fp1"] = _ok(fingerprint(identity)).value
    binding_directory = (
        Path(env["QMB_REPLAY_RUNTIME_ROOT"])
        / context.experiment_spec_fp1.value.replace(":", "-")
        / request_ref.value.replace(":", "-")
    )
    binding_directory.mkdir(parents=True)
    (binding_directory / "operator-binding.json").write_text(json.dumps(body), encoding="utf-8")
    cli = Path(sys.executable).with_name("qmb")
    environment = os.environ.copy()
    environment.update(env)
    execution = subprocess.run(
        [str(cli), "backtest", "run"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        timeout=60,
    )
    assert execution.returncode == 0, execution.stderr
    response = json.loads(execution.stdout)
    assert response["class"] == "qmb-recorded-replay-result-v1"
    assert response["evidence_ref"] == request_ref.value
    assert response["ct32_fp1"].startswith("fp1:sha256:")
    assert response["terminal_line_fp1"].startswith("fp1:sha256:")
    terminal_lines = _ok(
        read_merge_view(roots["terminal_ledger"], world=World.REPLAY, role="confirmation")
    )
    assert len(terminal_lines) == 1
    assert terminal_lines[0].ct32_fingerprint is not None
    assert terminal_lines[0].ct32_fingerprint.value == response["ct32_fp1"]
    assert terminal_lines[0].measures
