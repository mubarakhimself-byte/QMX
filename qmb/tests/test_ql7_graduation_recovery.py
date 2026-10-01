"""Host persistence/reopen for QML mill research and promoted-from lineage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from qmb.host.research_store import read_research_blob, save_research_hypothesis
from qmf.core import World
from qmf.core.chrono import CalendarIdentity, WriterId
from qmf.core.exact import UnitKind
from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import Result, is_ok
from qmf.data.store import EvidenceStore
from qmf.registry import EdgeType, RegistryPersistence
from qml.conformance import graduate_mill_to_governed, lint_declaration, run_layer2_suite
from qml.declaration import mint_bot_definition, mint_confluence
from qml.families import mint_strategy_family
from qml.footprint import ProducerBinding, mint_footprint
from qml.host import stamp_promoted_from_edge
from qml.logic import mint_logic_identity
from qml.protocol import PROTOCOL_FORMAT_VERSION, FunctionFactory, mint_state_scope
from qml.research import (
    DictionaryCite,
    fingerprint_hypothesis,
    mint_hypothesis,
    restore_hypothesis,
)

T = TypeVar("T")
_SOURCE = {
    "qmb_research_bot/__init__.py": "",
    "qmb_research_bot/bot.py": "def on_instant(self, evidence):\n    return ()\n",
}


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _candidate():
    producer = _ok(
        ProducerBinding.try_create(_ok(fingerprint({"class": "fixture-producer", "id": "sma"})))
    )
    confluence = _ok(mint_confluence([{"role": "level", "producer_binding": producer}]))
    footprint = _ok(
        mint_footprint(
            [
                {
                    "instrument_role": "primary",
                    "bar_specs": [{"kind": "time-interval", "seconds": 60}],
                    "stream_role": "trading",
                }
            ],
            [_ok(CalendarIdentity.try_create("fixture-ny", "v1", "2026a"))],
            [producer],
        )
    )
    family = _ok(mint_strategy_family("research-graduation-fixture"))
    logic = _ok(mint_logic_identity("research-graduation-fixture", "1.0.0", _SOURCE))
    declaration = _ok(
        mint_bot_definition(
            strategy_family_id=family.family_id.value,
            confluence_set=[confluence],
            parameter_space=[
                {
                    "name": "lookback",
                    "type": "exact integer",
                    "bounds": {"min": 1, "max": 20},
                    "step": 1,
                    "default": 5,
                    "unit_kind": UnitKind.COUNT,
                    "ui": "ui-editable",
                }
            ],
            footprint=footprint,
            permitted_exit_intents=(),
            logic_reference=logic,
        )
    )
    layer1 = lint_declaration(
        declaration,
        family_catalog=[family],
        confluence_catalog=[confluence],
        producer_catalog=[producer],
        logic_catalog=[logic],
    )
    assert is_ok(layer1), layer1
    state_scope = _ok(
        mint_state_scope(
            os="qmb-test-host",
            logic_identity=logic,
            protocol_format_version=PROTOCOL_FORMAT_VERSION,
            arithmetic_reference_build="fixture-arithmetic",
        )
    )
    layer2 = run_layer2_suite(
        declaration=declaration,
        factory=FunctionFactory(logic=lambda evidence: ()),
        source_tree=_SOURCE,
        state_scope=state_scope,
        state_bound=128,
    )
    assert is_ok(layer2), layer2
    return declaration, layer1.value, layer2.value


def test_host_reopens_saved_hypothesis_and_ct07_promoted_from_edge(tmp_path: Path) -> None:
    declaration, layer1, layer2 = _candidate()
    hypothesis = _ok(
        mint_hypothesis(
            hypothesis_class="entry_hypothesis",
            origin="idea",
            dictionary_cites=[DictionaryCite("dictionary/market-structure.md", "swing-high")],
            title="test candidate",
        )
    )

    saved = _ok(
        save_research_hypothesis(
            hypothesis,
            research_root=tmp_path / "research_root",
        )
    )
    research_bytes = _ok(
        read_research_blob(
            research_root=tmp_path / "research_root",
            research_ref=saved.research_ref,
        )
    )
    assert research_bytes == saved.canonical_bytes
    restored = _ok(restore_hypothesis(json.loads(research_bytes.decode("utf-8"))))
    assert _ok(fingerprint_hypothesis(restored)) == saved.research_ref

    graduation = _ok(
        graduate_mill_to_governed(
            layer1=layer1,
            layer2=layer2,
            hypothesis=restored,
            originating_research_ref=saved.research_ref,
        )
    )
    bot_fp = _ok(declaration.fingerprint_content())
    edge = _ok(
        stamp_promoted_from_edge(
            graduation=graduation,
            writer=_ok(WriterId.try_create("qmb-fixture", "authoring", "lineage", "boot-1")),
        )
    )
    assert edge.edge_type is EdgeType.PROMOTED_FROM
    assert edge.from_ref == bot_fp
    assert edge.to_ref == saved.research_ref

    registry_root = tmp_path / "registry-room"
    registry = _ok(RegistryPersistence.open(EvidenceStore(registry_root), World.REPLAY))
    receipt = registry.persist_edge(edge, edge_stream="qml-graduation")
    assert is_ok(receipt), receipt
    registry.close()

    reopened = _ok(RegistryPersistence.open(EvidenceStore(registry_root), World.REPLAY))
    edges = _ok(reopened.read_edges("qml-graduation", for_world=World.REPLAY))
    assert len(edges) == 1
    assert edges[0].edge_fingerprint == edge.edge_fingerprint
    assert edges[0].to_ref == saved.research_ref
    reopened.close()

    research_after_reopen = _ok(
        read_research_blob(
            research_root=tmp_path / "research_root",
            research_ref=saved.research_ref,
        )
    )
    restored_after_reopen = _ok(
        restore_hypothesis(json.loads(research_after_reopen.decode("utf-8")))
    )
    assert _ok(fingerprint_hypothesis(restored_after_reopen)) == edges[0].to_ref
