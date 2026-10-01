"""CT-33/CT-34 receipt stamping belongs to the QMB composition root."""

from __future__ import annotations

from typing import TypeVar

from qmb.host.bot_registration import (
    install_bot_domain_kinds,
    mint_generation_envelope,
    register_bot_definition,
)
from qmf.core.chrono import CalendarIdentity, Instant, WriterId
from qmf.core.exact import UnitKind
from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import Result, is_ok, is_refusal
from qmf.registry import KindRegistry, Registrar, RegistrationReceipt
from qml.conformance import evaluate_ticket
from qml.declaration import KIND_BOT_DEFINITION
from qml.footprint import ProducerBinding, mint_footprint
from qml.generation import author_new_structure

T = TypeVar("T")
_CREATED_NS = 1_700_000_000_000_000_000
_SOURCE = {
    "research_bot/__init__.py": "",
    "research_bot/bot.py": "def on_instant(self, instant):\n    return ()\n",
}


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _writer(kind: str, machine: str = "qmb-test") -> WriterId:
    return _ok(WriterId.try_create(machine, "authoring", kind, "boot-qmb-test"))


def _authored():
    producer_fp = _ok(fingerprint({"class": "test-producer", "tag": "sma"}))
    producer = _ok(ProducerBinding.try_create(producer_fp))
    calendar = _ok(CalendarIdentity.try_create("forex-test", "v1", "2026.1"))
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
    return _ok(
        author_new_structure(
            strategy_family_id="trend-follow",
            confluence_legs=[{"role": "level", "producer_binding": producer}],
            parameter_space=[
                {
                    "name": "lookback",
                    "type": "exact integer",
                    "bounds": {"min": 1, "max": 200},
                    "step": 1,
                    "default": 20,
                    "unit_kind": UnitKind.COUNT,
                    "ui": "ui-editable",
                }
            ],
            footprint=footprint,
            logic_source=_SOURCE,
        )
    )


class _RecordingRegistrar(Registrar):
    def __init__(self, kinds: KindRegistry) -> None:
        super().__init__(kinds)
        self.calls: list[dict[str, object]] = []

    def register(self, **kwargs: object) -> Result[RegistrationReceipt]:
        self.calls.append(dict(kwargs))
        return super().register(**kwargs)


def test_qmb_composition_root_stamps_only_ticketed_qml_content() -> None:
    import qml.host

    import qml

    authored = _authored()
    registry = KindRegistry()
    assert is_ok(install_bot_domain_kinds(registry))
    registrar = _RecordingRegistrar(registry)
    no_ticket = mint_generation_envelope(
        authored,
        registrar=registrar,
        created_at=_ok(Instant.try_create(_CREATED_NS)),
        bot_writer=_writer("bot-definition"),
        confluence_writer=_writer("confluence"),
    )
    assert is_refusal(no_ticket)
    assert registrar.calls == [], "QMB must not stamp a Bot without both conformance layers"

    ticket = _ok(evaluate_ticket(layer1_passed=True, layer2_passed=True))
    stamped = _ok(
        mint_generation_envelope(
            authored,
            registrar=registrar,
            created_at=_ok(Instant.try_create(_CREATED_NS)),
            ticket=ticket,
            bot_writer=_writer("bot-definition"),
            confluence_writer=_writer("confluence"),
        )
    )
    assert stamped.bot is not None and stamped.bot.record.kind == KIND_BOT_DEFINITION
    assert stamped.confluence is not None
    assert len(registrar.calls) == 2
    assert not hasattr(qml, "mint_generation_envelope")
    assert not hasattr(qml.host, "register_bot_definition")


def test_qmb_composition_returns_record_sink_refusal() -> None:
    authored = _authored()
    assert authored.bot is not None
    registry = KindRegistry()
    assert is_ok(install_bot_domain_kinds(registry))
    registrar = _RecordingRegistrar(registry)
    result = register_bot_definition(
        authored.bot,
        registrar=registrar,
        created_at=_ok(Instant.try_create(_CREATED_NS)),
        ticket=_ok(evaluate_ticket(layer1_passed=True, layer2_passed=True)),
        writer="not-a-writer-id",
        sequence=0,
    )
    assert is_refusal(result)
    assert registrar.calls
