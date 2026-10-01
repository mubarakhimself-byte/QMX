"""Local source-bound two-Bot registration and restart journey.

The fixture authors two small policies in source manifests, admits each through
the public QML conformance path, stamps CT-06 records through QMB, and restores
the authored callback from the saved manifest after a fresh registry open. It is
an offline fixture; it does not exercise a provider or deployment.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol, TypeVar, cast

from qmb.host.bot_registration import (
    install_bot_domain_kinds,
    register_bot_definition,
    register_confluence,
    register_strategy_family,
)
from qmb.host.runner import FACTORY_KIND_SOURCE, FactorySpec, load_factory, run_sandbox
from qmf.core.chrono import CalendarIdentity, Instant, WriterId
from qmf.core.exact import UnitKind
from qmf.core.fingerprint import World, fingerprint
from qmf.core.refusal import Result, is_ok, is_refusal
from qmf.data.store import EvidenceStore
from qmf.registry import KindRegistry, Registrar, RegistryPersistence
from qml.conformance import (
    gate_registration,
    generate_golden_slice,
    lint_declaration,
    read_surfaces_for_slice,
)
from qml.declaration import (
    BotDefinition,
    Confluence,
    mint_bot_definition,
    mint_confluence,
)
from qml.families import StrategyFamilyRecord, mint_strategy_family
from qml.footprint import ProducerBinding, mint_footprint
from qml.logic import LogicIdentity, fingerprint_source_manifest, mint_logic_identity
from qml.protocol import (
    PROTOCOL_FORMAT_VERSION,
    BotStateSnapshot,
    HostedBot,
    construct_bot,
    intent_identity,
    mint_state_scope,
    restore_bot,
)

T = TypeVar("T")
_ASSIGNMENT: Mapping[str, object] = {"lookback": 3}
_STATE_BOUND = 512
_ARITHMETIC = "fixture-arithmetic-v1"
_ENTRYPOINT = "fixture_policy.factory:factory"
_CREATED_NS = 1_800_000_000_000_000_000


class _ConstructFactory(Protocol):
    def construct(self, **kwargs: object) -> Result[object]: ...


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _writer() -> WriterId:
    return _ok(WriterId.try_create("local-fixture", "authoring", "bot-records", "boot-1"))


def _source(policy: str, family: str) -> dict[str, str]:
    # This is the actual declared source loaded by both Layer 2 and the host.
    # It emits typed CT-23 intents and keeps only a bounded callback counter.
    return {
        "fixture_policy/__init__.py": "",
        "fixture_policy/factory.py": f'''\
from qmf.core.exact import ExactRational, PriceDelta, UnitKind
from qmf.core.fingerprint import fingerprint
from qmf.core.identity import Instrument, VenueId
from qmf.core.refusal import is_ok
from qmf.risk.door import Direction, EntryIntent, ExitIntent, ExitKind, ReasonCode
from qmf.risk.paper import ExecutionTarget

POLICY = {policy!r}
FAMILY = {family!r}

def _v(result):
    if not is_ok(result):
        raise ValueError("fixture intent construction failed")
    return result.value

class Callback:
    def __init__(self):
        self.n = 0

    def export_state(self):
        return {{"n": self.n}}

    def import_state(self, payload):
        self.n = payload["n"]

    def on_instant(self, evidence):
        del evidence
        self.n += 1
        if self.n == 1:
            venue = _v(VenueId.try_create("fixture-venue"))
            instrument = _v(Instrument.try_create(venue, "EURUSD"))
            target = _v(ExecutionTarget.try_create("live", venue, "fixture-account"))
            reason = _v(ReasonCode.try_create(POLICY + "-entry", FAMILY))
            stop = _v(PriceDelta.try_create(500, instrument, 5))
            intent = _v(EntryIntent.try_create(
                instrument, Direction.LONG, reason, target,
                proposed_r=_v(ExactRational.try_create(1, 1, UnitKind.R_MULTIPLE)),
                advisory_stop_proposal=stop,
            ))
            return (intent,)
        if self.n == 2:
            reason = _v(ReasonCode.try_create(POLICY + "-close", FAMILY))
            position = _v(fingerprint({{"class": "fixture-position", "policy": POLICY}}))
            return (_v(ExitIntent.try_create(ExitKind.CLOSE_FULL, reason, position)),)
        return ()

class Factory:
    def construct(self, *, declaration, assignment, read_surfaces):
        del declaration, assignment, read_surfaces
        return Callback()

factory = Factory()
''',
    }


def _world(
    policy: str,
) -> tuple[BotDefinition, LogicIdentity, StrategyFamilyRecord, Confluence, dict[str, str]]:
    family = _ok(mint_strategy_family("family-" + policy))
    producer = _ok(
        ProducerBinding.try_create(_ok(fingerprint({"class": "local-source", "policy": policy})))
    )
    confluence = _ok(mint_confluence([{"role": "trigger", "producer_binding": producer}]))
    calendar = _ok(CalendarIdentity.try_create("fixture-calendar", "v1", "local-1"))
    footprint = _ok(
        mint_footprint(
            [{
                "instrument_role": "primary",
                "bar_specs": [{"kind": "time-interval", "seconds": 60}],
                "stream_role": "trading",
            }],
            [calendar],
            [producer],
        )
    )
    source = _source(policy, family.family_id.value)
    logic = _ok(mint_logic_identity("local-" + policy, "1.0.0", source))
    declaration = _ok(
        mint_bot_definition(
            {
                "strategy_family_id": family.family_id.value,
                "confluence_set": [confluence],
                "parameter_space": [{
                    "name": "lookback", "type": "exact integer",
                    "bounds": {"min": 1, "max": 8}, "step": 1,
                    "default": 3, "unit_kind": UnitKind.COUNT,
                    "ui": "ui-editable",
                }],
                "footprint": footprint,
                "permitted_exit_intents": ["close_full"],
                "logic_reference": logic,
            }
        )
    )
    return declaration, logic, family, confluence, source


def _scope(logic: LogicIdentity):
    return _ok(mint_state_scope(
        os="local-test-host",
        logic_identity=logic,
        protocol_format_version=PROTOCOL_FORMAT_VERSION,
        arithmetic_reference_build=_ARITHMETIC,
    ))


def _candidate(declaration: BotDefinition, logic: LogicIdentity, family: object,
               confluence: object, source: Mapping[str, str]):
    layer1 = _ok(lint_declaration(
        declaration,
        family_catalog=[family],
        confluence_catalog=[confluence],
        producer_catalog=declaration.footprint.producer_bindings,
        logic_catalog=[logic],
    ))
    layer2 = _ok(run_sandbox(
        declaration=declaration,
        source_tree=source,
        assignment=_ASSIGNMENT,
        state_scope=_scope(logic),
        state_bound=_STATE_BOUND,
    ))
    return _ok(gate_registration(layer1=layer1, layer2=layer2))


def _trace(
    hosted: HostedBot, instants: tuple[object, ...]
) -> tuple[tuple[dict[str, object], ...], ...]:
    return tuple(
        tuple(intent_identity(item) for item in _ok(hosted.on_instant(instant)))
        for instant in instants
    )


def test_two_source_bound_bots_register_reopen_and_restore_independently(tmp_path: Path) -> None:
    worlds = {name: _world(name) for name in ("alpha", "beta")}
    candidates = {
        name: _candidate(*world[:4], world[4]) for name, world in worlds.items()
    }
    assert candidates["alpha"].fingerprint != candidates["beta"].fingerprint
    assert candidates["alpha"].logic != candidates["beta"].logic

    kinds = KindRegistry()
    _ok(install_bot_domain_kinds(kinds))
    registrar = Registrar(kinds)
    registry_root = tmp_path / "registry"
    persistence = _ok(RegistryPersistence.open(EvidenceStore(registry_root), World.REPLAY))
    created = _ok(Instant.try_create(_CREATED_NS))
    writer = _writer()
    refs: dict[str, dict[str, object]] = {}
    next_sequence = 0
    for name, (declaration, logic, family, confluence, source) in worlds.items():
        candidate = candidates[name]
        # The ticket alone contains only booleans; the caller proves that the
        # candidate is for these exact source/declaration identities first.
        assert candidate.declaration.identity_payload() == declaration.identity_payload()
        assert candidate.logic == logic
        assert candidate.fingerprint == _ok(declaration.fingerprint_content())
        assert _ok(fingerprint_source_manifest(source)) == logic.source_manifest

        family_receipt = _ok(register_strategy_family(
            family.family_id.value, registrar=registrar, writer=writer,
            sequence=next_sequence, created_at=created,
        ))
        next_sequence += 1
        confluence_receipt = _ok(register_confluence(
            confluence.legs, registrar=registrar, writer=writer,
            sequence=next_sequence, created_at=created,
        ))
        next_sequence += 1
        bot_receipt = _ok(register_bot_definition(
            declaration, registrar=registrar, writer=writer,
            sequence=next_sequence, created_at=created, ticket=candidate.ticket,
        ))
        next_sequence += 1
        for receipt in (family_receipt, confluence_receipt, bot_receipt):
            _ok(persistence.persist_record(receipt.record))
        refs[name] = {
            "family": family_receipt.record.stable_id,
            "confluence": confluence_receipt.record.stable_id,
            "bot": bot_receipt.record.stable_id,
            "semantic_bot": candidate.fingerprint,
            "semantic_confluence": _ok(confluence.fingerprint_content()),
        }

        source_path = tmp_path / "saved-source" / name / "manifest.json"
        source_path.parent.mkdir(parents=True)
        source_path.write_text(json.dumps(source, sort_keys=True), encoding="utf-8")

    persistence.close()
    reopened = _ok(RegistryPersistence.open(EvidenceStore(registry_root), World.REPLAY))

    baselines: dict[str, tuple[tuple[dict[str, object], ...], ...]] = {}
    snapshots: dict[str, BotStateSnapshot] = {}
    for name in worlds:
        source_path = tmp_path / "saved-source" / name / "manifest.json"
        source_obj = json.loads(source_path.read_text(encoding="utf-8"))
        source = cast("dict[str, str]", source_obj)
        loaded = _ok(reopened.load_record(refs[name]["bot"], for_world=World.REPLAY))
        family_loaded = _ok(reopened.load_record(refs[name]["family"], for_world=World.REPLAY))
        confluence_loaded = _ok(
            reopened.load_record(refs[name]["confluence"], for_world=World.REPLAY)
        )
        restored_family = _ok(mint_strategy_family(family_loaded.body["family_id"]))
        assert restored_family.family_id == worlds[name][2].family_id
        assert confluence_loaded.stable_id == refs[name]["confluence"]
        restored_confluence = _ok(mint_confluence(
            confluence_loaded.body["legs"],
            order_significance=confluence_loaded.body.get("order_significance"),
        ))
        restored_confluence_fp = _ok(restored_confluence.fingerprint_content())
        assert restored_confluence_fp == refs[name]["semantic_confluence"]
        declaration = _ok(mint_bot_definition(loaded.body))
        semantic = _ok(declaration.fingerprint_content())
        # CT-06 registration stable_id and CT-33 semantic content fp are separate
        # identities; the confluence cite in CT-33 is also semantic, not CT-06.
        assert semantic == refs[name]["semantic_bot"]
        assert semantic != loaded.stable_id
        assert refs[name]["semantic_confluence"] != confluence_loaded.stable_id
        assert declaration.confluence_set[0].fingerprint == restored_confluence_fp
        logic = worlds[name][1]
        assert _ok(fingerprint_source_manifest(source)) == logic.source_manifest
        factory = _ok(load_factory(
            FactorySpec(FACTORY_KIND_SOURCE, source["fixture_policy/factory.py"], _ENTRYPOINT),
            source_tree=source,
        ))
        golden = _ok(generate_golden_slice(declaration.footprint))
        surfaces = _ok(read_surfaces_for_slice(golden))
        hosted = _ok(construct_bot(
            factory, declaration=declaration, assignment=_ASSIGNMENT,
            read_surfaces=surfaces, state_scope=_scope(logic), state_bound=_STATE_BOUND,
        ))
        baseline = tuple(_trace(hosted, golden.evaluation_instants[i:i + 1])[0]
                         for i in range(len(golden.evaluation_instants)))
        assert [len(step) for step in baseline] == [1, 1, 0]
        baselines[name] = baseline

        factory2 = _ok(load_factory(
            FactorySpec(FACTORY_KIND_SOURCE, source["fixture_policy/factory.py"], _ENTRYPOINT),
            source_tree=source,
        ))
        prefix = _ok(construct_bot(
            factory2, declaration=declaration, assignment=_ASSIGNMENT,
            read_surfaces=surfaces, state_scope=_scope(logic), state_bound=_STATE_BOUND,
        ))
        _ok(prefix.on_instant(golden.evaluation_instants[0]))
        snapshot = _ok(prefix.snapshot())
        snapshot_path = tmp_path / f"{name}-snapshot.json"
        snapshot_path.write_text(
            json.dumps(snapshot.to_mapping(), sort_keys=True), encoding="utf-8"
        )
        snapshots[name] = _ok(BotStateSnapshot.from_mapping(
            json.loads(snapshot_path.read_text(encoding="utf-8"))
        ))

        restore_factory = _ok(load_factory(
            FactorySpec(FACTORY_KIND_SOURCE, source["fixture_policy/factory.py"], _ENTRYPOINT),
            source_tree=source,
        ))
        restored = _ok(restore_bot(
            snapshots[name], restore_factory, declaration=declaration,
            assignment=_ASSIGNMENT, read_surfaces=surfaces, current_scope=_scope(logic),
        ))
        tail = tuple(_trace(restored, golden.evaluation_instants[i:i + 1])[0]
                     for i in range(1, len(golden.evaluation_instants)))
        assert tail == baseline[1:]

    assert baselines["alpha"] != baselines["beta"]
    for source_name, target_name in (("alpha", "beta"), ("beta", "alpha")):
        declaration, logic = worlds[target_name][0], worlds[target_name][1]
        golden = _ok(generate_golden_slice(declaration.footprint))
        loaded_factory = _ok(load_factory(
            FactorySpec(
                FACTORY_KIND_SOURCE,
                worlds[target_name][4]["fixture_policy/factory.py"],
                _ENTRYPOINT,
            ),
            source_tree=worlds[target_name][4],
        ))

        class CountingFactory:
            def __init__(self, inner: _ConstructFactory) -> None:
                self.inner = inner
                self.construct_calls = 0

            def construct(self, **kwargs: object) -> Result[object]:
                self.construct_calls += 1
                return self.inner.construct(**kwargs)

        foreign_factory = CountingFactory(cast(_ConstructFactory, loaded_factory))
        mismatch = restore_bot(
            snapshots[source_name], foreign_factory, declaration=declaration,
            assignment=_ASSIGNMENT, read_surfaces=_ok(read_surfaces_for_slice(golden)),
            current_scope=_scope(logic),
        )
        assert is_refusal(mismatch)
        assert foreign_factory.construct_calls == 0
    reopened.close()


def test_failed_conformance_does_not_stamp_or_persist_bot(tmp_path: Path) -> None:
    declaration, _, family, confluence, source = _world("rejected")
    # A forbidden source capability fails Layer 2. The host receives no passing
    # candidate and its ticket gate must refuse before Registrar/persistence.
    bad_source = dict(source)
    bad_source["fixture_policy/factory.py"] = "import socket\n" + bad_source[
        "fixture_policy/factory.py"
    ]
    layer1 = lint_declaration(
        declaration, family_catalog=[family], confluence_catalog=[confluence],
        producer_catalog=declaration.footprint.producer_bindings,
        logic_catalog=[declaration.logic_reference],
    )
    assert is_ok(layer1)
    layer2 = run_sandbox(
        declaration=declaration, source_tree=bad_source, assignment=_ASSIGNMENT,
        state_scope=_scope(declaration.logic_reference), state_bound=_STATE_BOUND,
    )
    assert is_refusal(layer2), "foreign source bytes cannot produce a Layer-2 pass"

    kinds = KindRegistry()
    _ok(install_bot_domain_kinds(kinds))
    registrar = Registrar(kinds)
    persistence = _ok(
        RegistryPersistence.open(EvidenceStore(tmp_path / "empty-registry"), World.REPLAY)
    )
    before_export = _ok(persistence.backup_export())
    assert before_export.record_count == 0
    rejected = register_bot_definition(
        declaration, registrar=registrar, writer=_writer(), sequence=0,
        created_at=_ok(Instant.try_create(_CREATED_NS)), ticket=None,
    )
    assert is_refusal(rejected)
    assert registrar.stable_ids() == frozenset()
    after_export = _ok(persistence.backup_export())
    assert after_export.record_count == 0
    persistence.close()
