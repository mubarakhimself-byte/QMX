"""A deploy the node refused reads as a refused row on his deployments and units (C-29)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import JsonValue
from qmx_apps.errors import AppError
from qmx_control.models import Document

from qmx_host.node_link import NodeLink

DEPLOY: Document = {
    "deployment": {
        "deployment_id": "dep-1",
        "unit": {"id": "dummy-trend-pullback", "version": "fp-unit"},
        "files": [],
    }
}
REFUSED_ROW = {
    "deployment_id": "dep-1",
    "unit": {"id": "dummy-trend-pullback", "version": "fp-unit"},
    "state": "refused",
    "detail": "identity_unconfirmed: this node's volume was made on another machine",
    "accepted_at": None,
}


class Node:
    """The trading node as the supervisor reaches it: down, or answering as it is told."""

    def __init__(self, home: Path) -> None:
        self.home = home
        self.up = True
        self.deploy_answer: JsonValue = {
            "ok": False,
            "code": "identity_unconfirmed",
            "message": "this node's volume was made on another machine",
        }
        self.rows: list[JsonValue] = []

    def get(self, app: str) -> Document:
        return {"id": app}

    def call(
        self, app: str, operation: str, arguments: Document, *, pin: Document | None = None
    ) -> Document:
        del app, arguments, pin
        if not self.up:
            raise AppError("not_running", "the node is not running", 409)
        if operation == "deploy":
            return {"result": self.deploy_answer}
        return {"result": {"ok": True, "value": self.rows}}


@pytest.fixture
def node(tmp_path: Path) -> Node:
    return Node(tmp_path)


def link_of(node: Node) -> NodeLink:
    return NodeLink(
        node.home,
        here="pc",
        apps=cast(Any, node),
        settings=dict,
        pass_keys=dict,
    )


def rows(link: NodeLink, operation: str, **arguments: JsonValue) -> JsonValue:
    answer = link.read(operation, dict(arguments), principal="operator")
    return cast(Document, answer)["value"]


def test_a_queued_deploy_the_node_later_refuses_lands_a_refused_row(node: Node) -> None:
    node.up = False
    link = link_of(node)
    queued = link.change("trading-node", "deploy", DEPLOY, principal="operator", op_id="dep-1")
    node.up = True
    before = rows(link, "deployments")

    link.flush("pc")

    assert (queued.state, before) == ("waiting", [])
    assert rows(link, "deployments") == [REFUSED_ROW]


def test_the_refused_row_survives_a_restart_of_the_host(node: Node) -> None:
    link_of(node).change("trading-node", "deploy", DEPLOY, principal="operator", op_id="dep-1")

    assert rows(link_of(node), "deployments") == [REFUSED_ROW]


def test_the_copilots_units_read_shows_it_too_and_keeps_his_filter(node: Node) -> None:
    link = link_of(node)
    link.change("trading-node", "deploy", DEPLOY, principal="operator", op_id="dep-1")

    assert rows(link, "units") == [
        {
            "deployment_id": "dep-1",
            "unit_id": "dummy-trend-pullback",
            "state": "refused",
            "detail": REFUSED_ROW["detail"],
            "warm": None,
            "kill_level": "GREEN",
        }
    ]
    assert rows(link, "units", deployment_id="dep-2") == []


def test_a_deploy_the_node_took_is_never_shown_refused(node: Node) -> None:
    node.deploy_answer = {"ok": True, "value": {"deployment_id": "dep-1", "state": "accepted"}}
    node.rows = [{"deployment_id": "dep-1", "state": "trading"}]
    link = link_of(node)
    link.change("trading-node", "deploy", DEPLOY, principal="operator", op_id="dep-1")

    assert rows(link, "deployments") == [{"deployment_id": "dep-1", "state": "trading"}]


def test_a_deploy_filed_refused_that_the_node_holds_reads_as_the_node_has_it(node: Node) -> None:
    """A timed out ask settles as refused though the node may have kept the deployment."""
    link = link_of(node)
    node.deploy_answer = {"ok": False, "code": "tool_timeout", "message": "did not complete"}
    link.change("trading-node", "deploy", DEPLOY, principal="operator", op_id="dep-1")
    node.rows = [{"deployment_id": "dep-1", "state": "trading"}]

    assert rows(link, "deployments") == [{"deployment_id": "dep-1", "state": "trading"}]


def test_a_node_that_refuses_the_read_keeps_its_own_answer(node: Node) -> None:
    link = link_of(node)
    link.change("trading-node", "deploy", DEPLOY, principal="operator", op_id="dep-1")
    node.up = False

    with pytest.raises(AppError):
        link.read("deployments", {}, principal="operator")
