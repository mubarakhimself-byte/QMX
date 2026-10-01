"""Public two-Bot conformance and durable snapshot recovery journey."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import TypeVar, cast

from qmf.core.chrono import CalendarIdentity, Instant
from qmf.core.exact import ExactRational, PriceDelta, UnitKind
from qmf.core.fingerprint import fingerprint
from qmf.core.identity import Instrument, VenueId
from qmf.core.refusal import Ok, Result, is_ok, is_refusal
from qmf.risk.door import (
    Direction,
    EntryIntent,
    ExitIntent,
    ExitKind,
    ReasonCode,
)
from qmf.risk.paper import ExecutionTarget
from qml.conformance import (
    GoldenSlice,
    gate_registration,
    generate_golden_slice,
    lint_declaration,
    read_surfaces_for_slice,
    run_layer2_suite,
)
from qml.declaration import BotDefinition, mint_bot_definition, mint_confluence
from qml.families import mint_strategy_family
from qml.footprint import ProducerBinding, mint_footprint
from qml.logic import LogicIdentity, mint_logic_identity
from qml.protocol import (
    PROTOCOL_FORMAT_VERSION,
    BotStateSnapshot,
    FootprintEvidence,
    HostedBot,
    construct_bot,
    intent_identity,
    mint_state_scope,
    restore_bot,
)

T = TypeVar("T")
_OS = "linux-x86_64"
_ARITHMETIC = "none"
_STATE_BOUND = 512
_ASSIGNMENT: Mapping[str, object] = {"lookback": 3}
_FAMILY_ID = "recovery-journey"
_VENUE = "fixture-venue"
_SYMBOL = "EURUSD"
_ACCOUNT = "fixture-account"


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


class _CounterPolicy:
    def __init__(self, policy_id: str) -> None:
        self.policy_id = policy_id
        self.n = 0

    def export_state(self) -> dict[str, object]:
        return {"n": self.n}

    def import_state(self, payload: object) -> None:
        values = cast(Mapping[str, object], payload)
        counter = values.get("n")
        assert isinstance(counter, int) and not isinstance(counter, bool)
        self.n = counter

    def on_instant(self, evidence: FootprintEvidence) -> object:
        del evidence
        self.n += 1
        if self.n == 1:
            return (_entry(self.policy_id),)
        if self.n == 2:
            return (_exit(self.policy_id),)
        return ()


class _PolicyFactory:
    def __init__(self, policy_id: str) -> None:
        self.policy_id = policy_id
        self.construct_calls = 0

    def construct(
        self,
        *,
        declaration: object,
        assignment: object,
        read_surfaces: object,
    ) -> Result[object]:
        del declaration, assignment, read_surfaces
        self.construct_calls += 1
        return Ok(_CounterPolicy(self.policy_id))


def _entry(policy_id: str) -> EntryIntent:
    venue = _ok(VenueId.try_create(_VENUE))
    instrument = _ok(Instrument.try_create(venue, _SYMBOL))
    target = _ok(ExecutionTarget.try_create("live", venue, _ACCOUNT))
    reason = _ok(ReasonCode.try_create(f"{policy_id}-entry", _FAMILY_ID))
    stop = _ok(PriceDelta.try_create(500, instrument, 5))
    return _ok(
        EntryIntent.try_create(
            instrument,
            Direction.LONG,
            reason,
            target,
            proposed_r=_ok(ExactRational.try_create(1, 1, UnitKind.R_MULTIPLE)),
            advisory_stop_proposal=stop,
        )
    )


def _exit(policy_id: str) -> ExitIntent:
    reason = _ok(ReasonCode.try_create(f"{policy_id}-close", _FAMILY_ID))
    position = _ok(fingerprint({"class": "fixture-position", "policy": policy_id}))
    return _ok(ExitIntent.try_create(ExitKind.CLOSE_FULL, reason, position))


def _factory_sources(policy_id: str) -> dict[str, str]:
    return {
        "journey_bot/__init__.py": "",
        "journey_bot/policy.py": (
            f"POLICY_ID = {policy_id!r}\ndef on_instant(self, evidence):\n    return ()\n"
        ),
    }


def _world(policy_id: str) -> dict[str, object]:
    source = _factory_sources(policy_id)
    logic = _ok(mint_logic_identity("journey-bot", "1.0.0", source))
    family = _ok(mint_strategy_family(_FAMILY_ID))
    producer_fp = _ok(fingerprint({"class": "journey-producer", "role": "primary"}))
    producer = _ok(ProducerBinding.try_create(producer_fp))
    confluence = _ok(mint_confluence([{"role": "trigger", "producer_binding": producer}]))
    calendar = _ok(CalendarIdentity.try_create("fixture-calendar", "v1", "2026.1"))
    footprint = _ok(
        mint_footprint(
            [
                {
                    "instrument_role": "primary",
                    "bar_specs": [{"kind": "time-interval", "seconds": 60}],
                    "stream_role": "trading",
                }
            ],
            [calendar],
            [producer],
        )
    )
    declaration = _ok(
        mint_bot_definition(
            {
                "strategy_family_id": family.family_id.value,
                "confluence_set": [confluence],
                "parameter_space": [
                    {
                        "name": "lookback",
                        "type": "exact integer",
                        "bounds": {"min": 1, "max": 10},
                        "step": 1,
                        "default": 3,
                        "unit_kind": UnitKind.COUNT,
                        "ui": "ui-editable",
                    }
                ],
                "footprint": footprint,
                "permitted_exit_intents": ("close_full",),
                "logic_reference": logic,
            }
        )
    )
    return {
        "declaration": declaration,
        "logic": logic,
        "family": family,
        "confluence": confluence,
        "producer": producer,
        "source": source,
        "factory": _PolicyFactory(policy_id),
    }


def _declaration(world: Mapping[str, object]) -> BotDefinition:
    value = world["declaration"]
    assert isinstance(value, BotDefinition)
    return value


def _logic(world: Mapping[str, object]) -> LogicIdentity:
    value = world["logic"]
    assert isinstance(value, LogicIdentity)
    return value


def _scope(declaration: BotDefinition, *, os: str = _OS):
    return _ok(
        mint_state_scope(
            os=os,
            logic_identity=declaration.logic_reference,
            protocol_format_version=PROTOCOL_FORMAT_VERSION,
            arithmetic_reference_build=_ARITHMETIC,
        )
    )


def _admitted_candidate(world: Mapping[str, object]):
    declaration = _declaration(world)
    layer1 = _ok(
        lint_declaration(
            declaration,
            family_catalog=[world["family"]],
            confluence_catalog=[world["confluence"]],
            producer_catalog=[world["producer"]],
            logic_catalog=[world["logic"]],
        )
    )
    layer2 = _ok(
        run_layer2_suite(
            declaration=declaration,
            factory=world["factory"],
            source_tree=world["source"],
            assignment=_ASSIGNMENT,
            state_scope=_scope(declaration),
            state_bound=_STATE_BOUND,
        )
    )
    candidate = _ok(gate_registration(layer1=layer1, layer2=layer2))
    return candidate


def _drive(hosted: HostedBot, instants: tuple[Instant, ...]) -> tuple[tuple[object, ...], ...]:
    return tuple(
        tuple(intent_identity(intent) for intent in _ok(hosted.on_instant(instant)))
        for instant in instants
    )


def _construct(
    declaration: BotDefinition,
    factory: _PolicyFactory,
    slice_: GoldenSlice,
) -> HostedBot:
    surfaces = _ok(read_surfaces_for_slice(slice_))
    return _ok(
        construct_bot(
            factory,
            declaration=declaration,
            assignment=_ASSIGNMENT,
            read_surfaces=surfaces,
            state_scope=_scope(declaration),
            state_bound=_STATE_BOUND,
        )
    )


def _save_reopen(snapshot: BotStateSnapshot, path: Path) -> BotStateSnapshot:
    path.write_text(json.dumps(snapshot.to_mapping(), sort_keys=True), encoding="utf-8")
    saved = json.loads(path.read_text(encoding="utf-8"))
    return _ok(BotStateSnapshot.from_mapping(saved))


def test_two_admitted_bots_keep_separate_deterministic_recoverable_state(
    tmp_path: Path,
) -> None:
    alpha = _world("alpha")
    beta = _world("beta")
    alpha_candidate = _admitted_candidate(alpha)
    beta_candidate = _admitted_candidate(beta)
    alpha_definition = _declaration(alpha)
    beta_definition = _declaration(beta)

    assert alpha_candidate.ticket.layer1_passed and alpha_candidate.ticket.layer2_passed
    assert beta_candidate.ticket.layer1_passed and beta_candidate.ticket.layer2_passed
    assert alpha_candidate.fingerprint != beta_candidate.fingerprint
    assert _logic(alpha) != _logic(beta)
    assert alpha_definition.permitted_exit_intents == ("close_full",)
    assert beta_definition.permitted_exit_intents == ("close_full",)

    alpha_slice = _ok(generate_golden_slice(alpha_definition.footprint))
    beta_slice = _ok(generate_golden_slice(beta_definition.footprint))
    assert alpha_slice.fp1_identity() == beta_slice.fp1_identity()

    alpha_baseline = _drive(
        _construct(alpha_definition, _PolicyFactory("alpha"), alpha_slice),
        alpha_slice.evaluation_instants,
    )
    beta_baseline = _drive(
        _construct(beta_definition, _PolicyFactory("beta"), beta_slice),
        beta_slice.evaluation_instants,
    )
    assert alpha_baseline != beta_baseline
    assert [len(step) for step in alpha_baseline] == [1, 1, 0]
    assert [len(step) for step in beta_baseline] == [1, 1, 0]

    alpha_factory = _PolicyFactory("alpha")
    alpha_prefix = _construct(alpha_definition, alpha_factory, alpha_slice)
    _ok(alpha_prefix.on_instant(alpha_slice.evaluation_instants[0]))
    alpha_saved = _save_reopen(_ok(alpha_prefix.snapshot()), tmp_path / "alpha-state.json")
    alpha_restore_factory = _PolicyFactory("alpha")
    alpha_restored = _ok(
        restore_bot(
            alpha_saved,
            alpha_restore_factory,
            declaration=alpha_definition,
            assignment=_ASSIGNMENT,
            read_surfaces=_ok(read_surfaces_for_slice(alpha_slice)),
            current_scope=_scope(alpha_definition),
        )
    )
    alpha_continued = _drive(
        alpha_restored,
        alpha_slice.evaluation_instants[1:],
    )
    assert alpha_continued == alpha_baseline[1:]

    beta_factory = _PolicyFactory("beta")
    beta_prefix = _construct(beta_definition, beta_factory, beta_slice)
    _ok(beta_prefix.on_instant(beta_slice.evaluation_instants[0]))
    beta_saved = _save_reopen(_ok(beta_prefix.snapshot()), tmp_path / "beta-state.json")
    beta_restore_factory = _PolicyFactory("beta")
    beta_restored = _ok(
        restore_bot(
            beta_saved,
            beta_restore_factory,
            declaration=beta_definition,
            assignment=_ASSIGNMENT,
            read_surfaces=_ok(read_surfaces_for_slice(beta_slice)),
            current_scope=_scope(beta_definition),
        )
    )
    beta_continued = _drive(beta_restored, beta_slice.evaluation_instants[1:])
    assert beta_continued == beta_baseline[1:]

    cross_bot_factory = _PolicyFactory("beta")
    cross_bot = restore_bot(
        alpha_saved,
        cross_bot_factory,
        declaration=beta_definition,
        assignment=_ASSIGNMENT,
        read_surfaces=_ok(read_surfaces_for_slice(beta_slice)),
        current_scope=_scope(beta_definition),
    )
    assert is_refusal(cross_bot)
    assert cross_bot_factory.construct_calls == 0

    cross_os_factory = _PolicyFactory("alpha")
    cross_os = restore_bot(
        alpha_saved,
        cross_os_factory,
        declaration=alpha_definition,
        assignment=_ASSIGNMENT,
        read_surfaces=_ok(read_surfaces_for_slice(alpha_slice)),
        current_scope=_scope(alpha_definition, os="windows-11"),
    )
    assert is_refusal(cross_os)
    assert cross_os_factory.construct_calls == 0


def test_layer2_rejects_a_different_second_golden_run() -> None:
    world = _world("flip")
    declaration = _declaration(world)

    class AlternatingFactory:
        def __init__(self) -> None:
            self.construct_calls = 0

        def construct(
            self,
            *,
            declaration: object,
            assignment: object,
            read_surfaces: object,
        ) -> Result[object]:
            del declaration, assignment, read_surfaces
            self.construct_calls += 1
            emits = self.construct_calls % 2 == 1
            policy_id = "first-run" if emits else "second-run"

            class Callback:
                def on_instant(self, evidence: FootprintEvidence) -> object:
                    del evidence
                    return (_entry(policy_id),) if emits else ()

            return Ok(Callback())

    factory = AlternatingFactory()
    refused = run_layer2_suite(
        declaration=declaration,
        factory=factory,
        source_tree=world["source"],
        assignment=_ASSIGNMENT,
        state_scope=_scope(declaration),
        state_bound=_STATE_BOUND,
    )

    assert is_refusal(refused)
    assert factory.construct_calls >= 2
