"""A deployment names both halves of a unit version, and its G record covers the logic half
(AD-3).

A document whose G record names another logic fingerprint is refused at the door as
`g_record_missing`, before the node keeps it. A risk-only recompile is the other side: the
compiled fingerprint moved, the logic half did not, so the deployment names the new risk half
beside the same G record and the node hosts it.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from pathlib import Path
from typing import cast

from qml.compile import CompiledUnit
from qmn.app.runtime import compile_staged, parse_deployment, staging_folder
from qmn.app.store import Json
from test_app_runtime import (
    Rig,
    deploy,
    deployment,
    dummy_document,
    listed,
    month,
    play,
    rig,
    settle,
)

_STALE = "fp1:sha256:" + "0" * 64
"""A logic fingerprint no G record covers."""
_OPEN_AT = 1_742_508_000_000_000_000 + 900_000_000_001
"""A bar the dummy holds a position after, so the node's own stamp can be read."""


def _compiled(node: Rig, document: dict[str, Json]) -> CompiledUnit:
    """The document's own compile, through the node's staging folder, as the runtime does it."""
    deployment_id = str(document["deployment_id"])
    parsed = parse_deployment(cast("dict[str, object]", document))
    compiled = compile_staged(parsed, staging_folder(node.data, deployment_id))
    assert isinstance(compiled, CompiledUnit), compiled
    return compiled


def _named(node: Rig, document: dict[str, Json]) -> CompiledUnit:
    """Name both halves and the compile on the document, as the host writes them."""
    compiled = _compiled(node, document)
    document["compiled_fingerprint"] = compiled.compiled_fingerprint.value
    document["logic_fingerprint"] = compiled.logic_fingerprint.value
    document["risk_fingerprint"] = compiled.risk_fingerprint.value
    return compiled


def _g_record(document: dict[str, Json], logic: str) -> dict[str, Json]:
    return {**cast("dict[str, Json]", document["g_record"]), "logic_fingerprint": logic}


def _raised() -> dict[str, Json]:
    """The dummy with its one sizer number raised, so the risk half moves and the logic does not."""
    document = cast("dict[str, Json]", dummy_document())
    numbers = cast("dict[str, dict[str, Json]]", document["numbers"])
    numbers["risk_fraction"]["default"] = "0.01"
    return document


def test_a_logic_edit_needs_a_new_g_record(tmp_path: Path) -> None:
    node = rig(tmp_path)
    document = deployment(node.data)
    logic = _named(node, document).logic_fingerprint.value
    document["g_record"] = _g_record(document, _STALE)

    refused = deploy(node, document)

    assert (refused["ok"], refused["code"]) == (False, "g_record_missing")
    assert _STALE in str(refused["message"]) and logic in str(refused["message"])
    assert listed(node) == []
    assert node.account.received == []


def test_a_risk_only_recompile_is_taken_on_the_same_g_record(tmp_path: Path) -> None:
    node = rig(tmp_path)
    old = _named(node, deployment(node.data, "dep-1"))
    raised = deployment(node.data, "dep-2")
    raised["unit_document"] = _raised()
    compiled = _named(node, raised)
    assert compiled.logic_fingerprint.value == old.logic_fingerprint.value
    assert compiled.risk_fingerprint.value != old.risk_fingerprint.value
    raised["g_record"] = _g_record(raised, compiled.logic_fingerprint.value)
    assert raised["g_record"]["compiled_fingerprint"] == month().fingerprint

    accepted = deploy(node, raised, "op-deploy-2")

    assert accepted["ok"] is True, accepted
    assert settle(node, "dep-2") == "trading"

    play(node, _OPEN_AT)
    unit = node.runtime.hosted["dep-2"].unit
    assert unit is not None and unit.handler is not None
    held = unit.handler.open_positions["fx.eurusd"]
    assert held.opened_by == compiled.logic_fingerprint
    node.runtime.stop()
