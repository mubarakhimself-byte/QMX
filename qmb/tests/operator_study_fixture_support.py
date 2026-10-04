"""Persisted offline inputs and pinned source for the production Alternative Study door."""

from __future__ import annotations

import inspect
import json
from dataclasses import replace
from pathlib import Path
from typing import TypeVar

from qmb.execution.alternative_terminal import AlternativeTerminalStore
from qmb.host.operator_alternative import OperatorAlternativeInputs
from qmb.host.operator_alternative_study import OperatorAlternativeStudyPlan
from qmb.host.operator_study_replay import STUDY_BINDING_CLASS, STUDY_BINDING_FILENAME
from qmb.host.qma_cli import QmaBacktestContext
from qmb.host.replay_request import (
    ReplayInputRequest,
    persist_replay_request,
    resolve_replay_request,
)
from qmf.core import Instant, Result, World, WriterId, fingerprint, is_ok
from qmf.data.journal_producer import JournalWriter
from qmf.data.splits import SegmentRole
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener
from qmf.registry import RegistryPersistence
from replay_fixture_support import (  # pyright: ignore[reportMissingTypeStubs]
    make_recorded_replay_fixture,
)
from test_operator_alternative_study import (  # pyright: ignore[reportMissingTypeStubs]
    _config_payload,  # pyright: ignore[reportPrivateUsage] - reuse explicit offline fixtures
    _LocalStudyInterpreter,  # pyright: ignore[reportPrivateUsage]
    _plan,  # pyright: ignore[reportPrivateUsage]
    _registry,  # pyright: ignore[reportPrivateUsage]
    _writer,  # pyright: ignore[reportPrivateUsage]
)

T = TypeVar("T")


def ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def builder_source() -> str:
    """Builder source is pinned bytes and reads existing data; it never creates observations."""
    imports = """from pathlib import Path
from qmf.core import (Fingerprint, Instant, Result, Ok, UnitKind, ExactRational, World,
    fingerprint, is_ok, is_refusal)
from qmf.core.chrono import WriterId
from qmf.data.journal_producer import JournalWriter
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener
from qmf.registry import RegistryPersistence
from qmb.config.alternative import ADAPTER_INTERNAL_SIMULATE, validate_alternative_run_config
from qmb.execution.alternative import (AlternativeEvaluationRequest, AlternativeInterpreterRegistry,
 AlternativeMeasure, AlternativeMeasureDeclaration, AlternativePolicyEvaluation,
 PolicyInterpreterRegistration)
from qmb.execution.alternative_terminal import AlternativeTerminalStore
from qmb.host.operator_alternative import OperatorAlternativeInputs
from qmb.host.replay_request import resolve_replay_request

def _ok(result):
    assert is_ok(result), result
    return result.value

def _fp(label):
    return _ok(fingerprint({"class": "operator-alternative-study-test", "label": label}))

def writer(body):
    return _ok(WriterId.try_create(body['machine'],body['role'],body['stream'],
        body['boot_epoch_id']))

"""
    functions = (
        inspect.getsource(_config_payload)
        + "\n"
        + inspect.getsource(_LocalStudyInterpreter)
        + "\n"
        + inspect.getsource(_registry)
    )
    build = """
def build(context, binding):
    identity = binding.identity
    roots = {key: Path(value) for key,value in identity['roots'].items()}
    request = resolve_replay_request(request_root=roots['raw']/'replay-requests',
        request_ref=context.evidence_ref, split=None, expected_split_fp1=context.split_manifest_fp1,
        raw_store_root=roots['raw'], holdout_months=18)
    if is_refusal(request):
        return request
    registry = RegistryPersistence.open(EvidenceStore(roots['registry']), World.REPLAY)
    if is_refusal(registry):
        return registry
    journal = JournalStore(World.REPLAY, journal_dir=roots['journal'], open_stream=jsonl_opener())
    jw = JournalWriter.resume(journal, writer(identity['journal_writer']))
    if is_refusal(jw):
        return jw
    terminal = AlternativeTerminalStore.try_create(roots['alternative_terminal'],
        writer=writer({'machine':'study-fixture','role':'qmb','stream':'study-terminal','boot_epoch_id':'boot-1'}))
    if is_refusal(terminal):
        return terminal
    return Ok(OperatorAlternativeInputs(context=context,
        config=_ok(validate_alternative_run_config(_config_payload())),
        recorded_source=request.value.source, registry=_registry(),
        initial_accounting_state=identity['initial_accounting_state'],
        expected_command_owner_epoch=identity['command_owner_epoch'],
        runtime_descriptor_fp1=binding.descriptor_fp1,
        registry_as_of=Instant(value_ns=identity['registry_as_of_ns']),
        registry_writer=writer(identity['registry_writer']), raw_store_root=roots['raw'],
        journal_root=roots['journal'], journal_writer=jw.value, journal_store=journal,
        terminal_store=terminal.value, registry_persistence=registry.value,
        lineage_writer=writer(identity['lineage_writer'])))
"""
    return imports + functions + build


def prepare_study_inputs(root: Path) -> OperatorAlternativeInputs:
    fixture = make_recorded_replay_fixture(root / "data")
    request = ok(
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
    request_root = fixture.raw_store_root / "replay-requests"
    request_ref = ok(persist_replay_request(request_root=request_root, request=request))
    source = ok(
        resolve_replay_request(
            request_root=request_root,
            request_ref=request_ref,
            split=None,
            expected_split_fp1=fixture.expected_split_fp1,
            raw_store_root=fixture.raw_store_root,
            holdout_months=18,
        )
    ).source
    context = QmaBacktestContext(
        job_id="qmb:local:task-study",
        attempt_id=1,
        experiment_spec_fp1=ok(fingerprint({"class": "pending-admitted-authoring"})),
        evidence_ref=request_ref,
        split_manifest_fp1=fixture.expected_split_fp1,
        environment_ref="env:local",
        occupancy_key="local",
        mints_ct32=False,
        operator_descriptor_fp1=ok(fingerprint({"class": "pending-private-descriptor"})),
        command="optimize.run",
    )
    assert context.operator_descriptor_fp1 is not None
    journal_root = root / "journal"
    journal_root.mkdir(parents=True)
    journal = JournalStore(World.REPLAY, journal_dir=journal_root, open_stream=jsonl_opener())
    (root / "registry").mkdir()
    registry = ok(RegistryPersistence.open(EvidenceStore(root / "registry"), World.REPLAY))
    from qmb.config.alternative import validate_alternative_run_config

    return OperatorAlternativeInputs(
        context=context,
        config=ok(validate_alternative_run_config(_config_payload())),
        recorded_source=source,
        registry=_registry(),
        initial_accounting_state={"cash_units": 100, "position_units": 0},
        expected_command_owner_epoch=7,
        runtime_descriptor_fp1=context.operator_descriptor_fp1,
        registry_as_of=Instant(value_ns=1_800_000_000_000_000_000),
        registry_writer=_writer("study-registry"),
        raw_store_root=fixture.raw_store_root,
        journal_root=journal_root,
        journal_writer=ok(JournalWriter.resume(journal, _writer("study-decisions"))),
        journal_store=journal,
        terminal_store=ok(
            AlternativeTerminalStore.try_create(
                root / "terminals", writer=_writer("study-terminal")
            )
        ),
        registry_persistence=registry,
        lineage_writer=_writer("study-lineage"),
    )


def write_study_binding(
    root: Path, inputs: OperatorAlternativeInputs
) -> tuple[Path, OperatorAlternativeInputs, OperatorAlternativeStudyPlan]:
    def writer_body(writer: WriterId) -> dict[str, str]:
        return {
            "machine": writer.machine,
            "role": writer.role,
            "stream": writer.stream,
            "boot_epoch_id": writer.boot_epoch_id,
        }

    context = inputs.context
    registration = ok(inputs.registry.resolve(inputs.config))
    identity: dict[str, object] = {
        "class": "qmb-operator-alternative-binding-v1",
        "format_version": 1,
        "experiment_spec_fp1": context.experiment_spec_fp1.value,
        "evidence_ref": context.evidence_ref.value,
        "split_manifest_fp1": context.split_manifest_fp1.value,
        "composition_fp1": inputs.config.composition_fp.value,
        "policy_pair_identity": inputs.config.policy_pair.identity(),
        "source_fp1": inputs.recorded_source.fingerprint.value,
        "split_fp1": context.split_manifest_fp1.value,
        "split_role": "train",
        "registry_fp1": inputs.registry.fingerprint.value,
        "interpreter_registration_fp1": registration.fingerprint.value,
        "journal_writer": writer_body(inputs.journal_writer.writer),
        "journal_stream": inputs.journal_writer.stream_name,
        "terminal_root": str(inputs.terminal_store.root),
        "lineage_writer": writer_body(inputs.lineage_writer),
        "roots": {
            "raw": str(inputs.raw_store_root),
            "registry": str(inputs.registry_persistence.root),
            "journal": str(inputs.journal_root),
            "alternative_terminal": str(inputs.terminal_store.root),
        },
        "registry_as_of_ns": inputs.registry_as_of.value_ns,
        "registry_writer": writer_body(inputs.registry_writer),
        "initial_accounting_state": dict(inputs.initial_accounting_state),
        "initial_accounting_state_fp1": ok(fingerprint(inputs.initial_accounting_state)).value,
        "command_owner_epoch": inputs.expected_command_owner_epoch,
        "trial_label": {
            "class": "qmb-alternative-trial-label-v1",
            "present": False,
            "label": dict[str, object](),
        },
    }
    files = {"builder.py": builder_source()}
    base: dict[str, object] = {
        "class": "qmb-operator-alternative-binding-v1",
        "format_version": 1,
        "composition_class": "alternative",
        "experiment_spec_fp1": context.experiment_spec_fp1.value,
        "evidence_ref": context.evidence_ref.value,
        "split_manifest_fp1": context.split_manifest_fp1.value,
        "operator_binding": identity,
        "operator_binding_fp1": ok(fingerprint(identity)).value,
        "builder_files": files,
        "builder_fp1": ok(
            fingerprint({"class": "qmb-operator-alternative-builder-v1", "files": files})
        ).value,
        "entrypoint": "builder:build",
    }
    base["descriptor_fp1"] = ok(fingerprint(base)).value
    plan = _plan(inputs)
    plan = ok(
        OperatorAlternativeStudyPlan.try_create(
            inputs,
            parameter_space=plan.parameter_space,
            seed=plan.seed,
            direction=plan.direction,
            rounding=plan.rounding,
            batch_size=1,
            generation_count=2,
            objective=plan.objective,
            bindings=plan.bindings,
        )
    )
    row: dict[str, object] = {
        "class": STUDY_BINDING_CLASS,
        "format_version": 1,
        "composition_class": "alternative-study",
        "alternative_binding": base,
        "study_fp1": plan.fingerprint.value,
        "study": {
            "parameter_space": plan.parameter_space.fp1_identity(),
            "seed": plan.seed,
            "direction": plan.direction,
            "rounding": plan.rounding.value,
            "batch_size": plan.batch_size,
            "generation_count": plan.generation_count,
            "objective": plan.objective.fp1_identity(),
            "parameter_bindings": [b.fp1_identity() for b in plan.bindings],
        },
    }
    descriptor = ok(fingerprint(row))
    row["descriptor_fp1"] = descriptor.value
    directory = (
        root
        / context.experiment_spec_fp1.value.replace(":", "-")
        / context.evidence_ref.value.replace(":", "-")
    )
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / STUDY_BINDING_FILENAME
    path.write_text(json.dumps(row), encoding="utf-8")
    inputs = replace(
        inputs,
        context=replace(context, operator_descriptor_fp1=descriptor),
        runtime_descriptor_fp1=descriptor,
    )
    plan = ok(
        OperatorAlternativeStudyPlan.try_create(
            inputs,
            parameter_space=plan.parameter_space,
            seed=plan.seed,
            direction=plan.direction,
            rounding=plan.rounding,
            batch_size=plan.batch_size,
            generation_count=plan.generation_count,
            objective=plan.objective,
            bindings=plan.bindings,
        )
    )
    return path, inputs, plan
