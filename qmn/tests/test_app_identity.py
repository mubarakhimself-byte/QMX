"""C-10: a node is its machine id plus an install id; a copied volume refuses trading."""

from __future__ import annotations

import itertools
import re
import shutil
from pathlib import Path

from qmn.app.server import Node, open_node
from qmn.app.store import Json

START_NS = 1_793_000_000_000_000_000


def node_on(data: Path, machine: str | None) -> Node:
    ticks = itertools.count(START_NS, 1_000_000)
    return open_node(data, here=machine, machine="pc", clock_ns=lambda: next(ticks))


def status(node: Node) -> dict[str, Json]:
    answer = node.call("status", {})
    found = answer["value"]
    assert answer["ok"] is True and isinstance(found, dict)
    return found


def identity(node: Node) -> dict[str, Json]:
    found = status(node)["identity"]
    assert isinstance(found, dict)
    return found


def deployment(tag: Json, deployment_id: str) -> dict[str, Json]:
    return {
        "op_id": f"deploy-{deployment_id}",
        "deployment": {
            "schema_version": "qmx.node.deployment/1",
            "deployment_id": deployment_id,
            "node": {"tag": tag},
            "unit": {"id": "dummy", "version": "1.0.0"},
            "unit_document": {"markets": [{"market_id": "fx.eurusd"}]},
            "markets": [{"market_id": "fx.eurusd"}],
            "starting": {"source": "defaults", "values": {}},
            "compiled_fingerprint": "fp1:sha256:" + "a" * 64,
            "g_record": {"compiled_fingerprint": "fp1:sha256:" + "a" * 64},
            "files": [],
            "account": {"id": "demo-1"},
            "snapshots": [],
            "lane": "paper",
        },
    }


def test_first_start_mints_an_install_id_and_a_restart_keeps_it(tmp_path: Path) -> None:
    first = identity(node_on(tmp_path, "fp-pc-1"))
    again = identity(node_on(tmp_path, "fp-pc-1"))

    install_id = first["install_id"]
    assert isinstance(install_id, str) and re.fullmatch(r"[a-z2-7]{26}", install_id)
    assert first["tag"] == install_id[:8]
    assert (first["machine_fingerprint"], first["mismatch"]) == ("fp-pc-1", False)
    assert again == first


def test_a_copied_volume_on_another_machine_refuses_trading_until_confirm_same_node(
    tmp_path: Path,
) -> None:
    original = tmp_path / "pc"
    tag = identity(node_on(original, "fp-pc-1"))["tag"]
    copy = tmp_path / "server"
    shutil.copytree(original, copy)
    moved = node_on(copy, "fp-server-1")

    refused = moved.call("deploy", deployment(tag, "dep-1"))
    word = status(moved)["word"]
    confirmed = moved.call("confirm_same_node", {"op_id": "confirm-1"})
    accepted = moved.call("deploy", deployment(tag, "dep-2"))

    assert (refused["ok"], refused["code"]) == (False, "identity_unconfirmed")
    assert word == "Stopped by a health check"
    assert confirmed["ok"] is True
    after = identity(moved)
    assert (after["tag"], after["machine_fingerprint"], after["mismatch"]) == (
        tag,
        "fp-server-1",
        False,
    )
    assert accepted == {
        "ok": True,
        "value": {"deployment_id": "dep-2", "state": "accepted"},
        "op_id": "deploy-dep-2",
    }
    assert status(moved)["headline"] == "Ready, no units yet"
    assert identity(node_on(original, "fp-pc-1"))["mismatch"] is False


def test_a_machine_whose_id_cannot_be_read_refuses_trading_and_cannot_be_confirmed(
    tmp_path: Path,
) -> None:
    node = node_on(tmp_path, None)
    tag = identity(node)["tag"]

    refused = node.call("deploy", deployment(tag, "dep-1"))
    confirmed = node.call("confirm_same_node", {"op_id": "confirm-1"})

    assert (refused["ok"], refused["code"]) == (False, "identity_unconfirmed")
    assert (confirmed["ok"], confirmed["code"]) == (False, "machine_unknown")
    assert identity(node)["mismatch"] is True
