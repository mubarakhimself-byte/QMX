"""Every order the node sends carries its stop at the venue, journalled first (AD-308, AD-39).

Also the kill switch's placeholder effects (lead's call LC-C-28) and the node's tags on a cTrader
order. Runs against the conformance venue only.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from google.protobuf import descriptor_pb2
from qmb.runloop import RestingIntent
from qmf.core import (
    Account,
    AccountRole,
    Instant,
    Instrument,
    Ok,
    PriceDelta,
    Quantity,
    Result,
    TypedRefusal,
    VenueId,
)
from qmf.venue.commands import (
    Command,
    CommandKind,
    OrderParameters,
    OrderType,
    TimeInForce,
)
from qmf.venue.encode import encode_place_order, order_tags
from qmf.venue.proto import SPOTWARE_PROTO_PACKAGE, compile_descriptor_set
from qmn.app.runtime import Blocked, Placed, Sent, Ticket
from qmn.app.store import Json
from qmn.protection.effect_matrix import PLACEHOLDER_KILL_EFFECTS
from qmn.protection.ksa import KsaLevel
from qmn.venue import SubmissionOutcome
from qmn.venue.conformance import InjectedFault
from qmn.venue.verify import ctrader_static_declaration
from test_app_runtime import (
    LIVE_FROM,
    Rig,
    deploy,
    deployment,
    play,
    rig,
    settle,
    unit_rows,
    value,
)

FIRST_SEND = 1_742_508_000_000_000_000
"""The bar the dummy's first entry is sent on in the recorded day (2025-03-20 22:00 UTC)."""


def node_rows(node: Rig, kind: str) -> list[dict[str, object]]:
    rows = value(node.node.call("journal_tail", {"streams": ["node"]}))["rows"]
    found = cast("list[dict[str, object]]", rows)
    return [cast("dict[str, object]", row["body"]) for row in found if row["kind"] == kind]


def trading(tmp_path: Path, *, holds_stops: bool = True) -> Rig:
    node = rig(tmp_path, holds_stops=holds_stops)
    deploy(node, deployment(node.data))
    assert settle(node) == "trading"
    return node


def test_every_entry_reaches_the_venue_with_its_stop_after_its_journal_row(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    journalled: list[bool] = []
    sending = node.account.send

    def watched(ticket: Ticket) -> Result[Sent]:
        if ticket.tags is not None:
            send = f"{ticket.tags.client_order_id}/send"
            journalled.append(any(r["event_id"] == send for r in node_rows(node, "order")))
        return sending(ticket)

    node.account.send = watched  # type: ignore[method-assign]
    play(node, LIVE_FROM + 2 * 86_400_000_000_000)
    entries = [t for t in node.account.received if t.command.kind is CommandKind.PLACE_ORDER]
    sends = [r for r in node_rows(node, "order") if r["step"] == "send"]

    assert journalled == [True, True, True]
    assert [(r["stop_form"], r["quantity"], r["receipt_quantity"]) for r in sends] == [
        ("entry-relative", "1.72", "1.72"),
        ("entry-relative", "1.08", "1.08"),
        ("entry-relative", "0.75", "0.75"),
    ]
    assert all(
        t.command.order_parameters is not None
        and t.command.order_parameters.protective_stop_distance is not None
        for t in entries
    )
    stopped = [t for t in unit_rows(node, "trade") if t["exit_kind"] == "stop"]
    assert [t["stop"] for t in stopped] == [s["stop"] for s in sends[:2]]


def test_an_entry_whose_stop_the_gate_cannot_prove_never_reaches_the_venue(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    node.account.double.inject(InjectedFault.PROTECTIVE_STOP_CAPABILITY)
    play(node, LIVE_FROM + 2 * 86_400_000_000_000)
    guards = unit_rows(node, "guard")

    assert node.account.received == []
    assert [(g["reason"], g["detail"]) for g in guards] == [
        ("health_stop", "the node cannot prove the venue holds this order's stop")
    ] * 10


def test_a_stop_the_venue_does_not_hold_after_three_tries_is_closed_and_alarmed(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path, holds_stops=False)
    play(node, FIRST_SEND + 1)
    status = value(node.node.call("status", {}))

    assert [t.command.kind for t in node.account.received] == [
        CommandKind.PLACE_ORDER,
        CommandKind.AMEND_PROTECTION,
        CommandKind.AMEND_PROTECTION,
        CommandKind.CLOSE_POSITION,
    ]
    position = node.account.received[0].tags
    assert position is not None
    alarm = {
        "alarm": "protection_escalation",
        "position": position.client_order_id,
        "market_id": "fx.eurusd",
        "tries": 3,
        "action": "closed_reduce_only",
        "origin": "placeholder",
    }
    assert node_rows(node, "protection") == [alarm]
    assert status["alarms"] == [alarm]
    assert node.account.positions() == {}


def test_an_unprotected_position_whose_close_is_refused_is_alarmed_and_closed_once_it_can_be(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path, holds_stops=False)
    refusing(node, [3])
    play(node, FIRST_SEND + 1)
    held = dict(node.account.positions())
    node.runtime.tick()
    node.runtime.tick()
    node.runtime.tick()
    position = node.account.received[0].tags
    assert position is not None
    name = position.client_order_id
    closes = [t for t in node.account.received if t.command.kind is CommandKind.CLOSE_POSITION]

    assert held == {name: ("fx.eurusd", "short", Decimal("1.72"), None)}
    assert node_rows(node, "protection") == [
        {
            "alarm": "protection_escalation",
            "position": name,
            "market_id": "fx.eurusd",
            "tries": 3,
            "action": "close_refused",
            "origin": "placeholder",
        },
        {
            "alarm": "close_refused",
            "position": name,
            "market_id": "fx.eurusd",
            "why": "protection",
            "refusals": 3,
            "origin": "placeholder",
        },
    ]
    assert [t.position for t in closes] == [name] * 4
    assert node.account.positions() == {}
    assert unit_rows(node, "trade") == []


def test_a_journal_that_cannot_be_written_blocks_the_entry_before_the_venue(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    node.runtime.journal.close()
    play(node, FIRST_SEND + 1)

    assert node.account.received == []


KILL_SCOPES = [
    pytest.param("all", "all", "Paused", id="all"),
    pytest.param({"instrument": "fx.eurusd"}, "instrument:fx.eurusd", "Paused", id="market-id"),
]
"""Each scope a kill is asked at, its key, and the status word."""


@pytest.mark.parametrize(("scope", "key", "word"), KILL_SCOPES)
@pytest.mark.parametrize(
    ("level", "sent", "closed"),
    [
        ("YELLOW", [CommandKind.PLACE_ORDER], 0),
        ("ORANGE", [CommandKind.PLACE_ORDER], 0),
        ("RED", [CommandKind.PLACE_ORDER, CommandKind.CLOSE_POSITION], 1),
        ("BLACK", [CommandKind.PLACE_ORDER, CommandKind.CLOSE_POSITION], 1),
    ],
)
def test_each_kill_level_applies_its_placeholder_effect_and_only_his_resume_lifts_it(
    tmp_path: Path,
    level: str,
    sent: list[CommandKind],
    closed: int,
    scope: Json,
    key: str,
    word: str,
) -> None:
    node = trading(tmp_path)
    play(node, FIRST_SEND + 1)
    killed = node.node.call("kill", {"op_id": "op-kill", "level": level, "scope": scope})
    lower = node.node.call("kill", {"op_id": "op-lower", "level": "YELLOW", "scope": scope})
    node.runtime.tick()
    play(node, LIVE_FROM + 86_400_000_000_000, start=FIRST_SEND + 1)
    during = value(node.node.call("status", {}))
    effect = PLACEHOLDER_KILL_EFFECTS[KsaLevel(level)].document()
    resumed = node.node.call("resume", {"op_id": "op-resume", "scope": "all"})
    node.runtime.tick()
    after = value(node.node.call("status", {}))

    assert killed == {"ok": True, "value": {"level_in_force": level}, "op_id": "op-kill"}
    assert value(lower) == {"level_in_force": level}
    assert [t.command.kind for t in node.account.received] == sent
    assert (during["word"], during["kill_level"]) == (word, level)
    assert during["kill_effects"] == {key: effect}
    assert effect["origin"] == "placeholder"
    kills = node_rows(node, "kill_level")
    assert [(k["scope"], k["level"], k["origin"], k["positions_closed"]) for k in kills] == [
        (key, level, "placeholder", closed),
        ("all", "GREEN", "placeholder", 0),
    ]
    assert value(resumed) == {"state": "accepted", "open_causes": []}
    assert (after["kill_level"], after["kill_effects"]) == ("GREEN", {})


def test_a_kill_at_an_instrument_no_deployment_trades_is_refused_by_name(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    killed = node.node.call(
        "kill", {"op_id": "op-kill", "level": "RED", "scope": {"instrument": "fx.gbpusd"}}
    )
    paused = node.node.call("pause", {"op_id": "op-pause", "scope": {"instrument": "XAUUSD"}})

    assert (killed["ok"], killed["code"]) == (False, "unknown_scope")
    assert str(killed["message"]).startswith("kill: this node holds no instrument fx.gbpusd; ")
    assert value(paused) == {"state": "accepted"}
    assert value(node.node.call("status", {}))["kill_effects"] == {}


def refusing(node: Rig, refusals: list[int]) -> None:
    """The venue refuses the next ``refusals[0]`` closes it is sent, then answers again."""
    sending = node.account.send

    def send(ticket: Ticket) -> Result[Sent]:
        if ticket.command.kind is CommandKind.CLOSE_POSITION and refusals[0] > 0:
            refusals[0] -= 1
            node.account.received.append(ticket)
            return Ok(Sent(SubmissionOutcome.REJECTED_BY_VENUE, None, "busy"))
        return sending(ticket)

    node.account.send = send  # type: ignore[method-assign]


def test_a_red_close_the_venue_refuses_is_sent_again_on_the_next_tick(tmp_path: Path) -> None:
    node = trading(tmp_path)
    play(node, FIRST_SEND + 1)
    refusing(node, [1])
    node.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    node.runtime.tick()
    open_after_first = len(node.account.positions())
    node.runtime.tick()
    node.runtime.tick()
    closes = [t for t in node.account.received if t.command.kind is CommandKind.CLOSE_POSITION]

    assert open_after_first == 1
    assert node.account.positions() == {}
    assert len(closes) == 2
    assert [k["positions_closed"] for k in node_rows(node, "kill_level")] == [0]
    assert [r["step"] for r in node_rows(node, "order") if r["step"] in {"close", "closed"}] == [
        "close",
        "closed",
    ]


def _compiled() -> object:
    files = descriptor_pb2.FileDescriptorSet()
    proto = files.file.add()
    proto.name, proto.package, proto.syntax = "protooa.proto", "protooa", "proto2"
    string, int64, int32, uint32, raw = (
        descriptor_pb2.FieldDescriptorProto.TYPE_STRING,
        descriptor_pb2.FieldDescriptorProto.TYPE_INT64,
        descriptor_pb2.FieldDescriptorProto.TYPE_INT32,
        descriptor_pb2.FieldDescriptorProto.TYPE_UINT32,
        descriptor_pb2.FieldDescriptorProto.TYPE_BYTES,
    )
    shapes: Mapping[str, tuple[tuple[str, int, int], ...]] = {
        "ProtoMessage": (
            ("payloadType", 1, uint32),
            ("payload", 2, raw),
            ("clientMsgId", 3, string),
        ),
        "ProtoOANewOrderReq": (
            ("ctidTraderAccountId", 2, int64),
            ("symbolId", 3, int64),
            ("orderType", 4, int32),
            ("tradeSide", 5, int32),
            ("volume", 6, int64),
            ("timeInForce", 9, int32),
            ("label", 16, string),
            ("clientOrderId", 18, string),
            ("relativeStopLoss", 19, int64),
        ),
    }
    for name, fields in shapes.items():
        message = proto.message_type.add()
        message.name = name
        for field_name, number, kind in fields:
            added = message.field.add()
            added.name, added.number, added.type = field_name, number, kind
            added.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    compiled = compile_descriptor_set(
        files.SerializeToString(), package_name=SPOTWARE_PROTO_PACKAGE, release_tag=91
    )
    assert not isinstance(compiled, TypedRefusal), compiled
    return compiled.value


def test_the_node_tags_fit_ctrader_and_ride_the_encoded_order() -> None:
    venue = VenueId("icmarkets-ctrader")
    instrument = Instrument(venue, "EURUSD")
    params = OrderParameters.try_create(
        OrderType.MARKET,
        TimeInForce.IMMEDIATE_OR_CANCEL,
        Quantity(172, "lot", 2),
        protective_stop_distance=PriceDelta(29, instrument, 5),
        instrument=instrument,
        trade_side="sell",
    )
    assert not isinstance(params, TypedRefusal), params
    command = Command.place_order(
        venue, Account("demo-1", venue, AccountRole.DEMO), "s1", 1, params.value
    )
    assert not isinstance(command, TypedRefusal), command
    tags = order_tags("qa4dqobyh-01JPTS40R0AAXPDJ2WRTPTTH2Q", "qmx:a4dqobyh:dummy-trend-pullback")
    assert not isinstance(tags, TypedRefusal), tags
    declaration = ctrader_static_declaration()
    assert not isinstance(declaration, TypedRefusal), declaration
    encoded = encode_place_order(
        command.value,
        compiled=_compiled(),
        declaration=declaration.value,
        ctid_trader_account_id=7,
        symbol_id=1,
        trade_side="sell",
        tags=tags.value,
    )
    assert not isinstance(encoded, TypedRefusal), encoded
    payload = encoded.value.payload

    too_long = order_tags("q" + "x" * 50, "qmx:a4dqobyh:u")
    label_long = order_tags("qa4dqobyh-1", "qmx:" + "u" * 97)
    assert isinstance(too_long, TypedRefusal) and isinstance(label_long, TypedRefusal)
    assert too_long.context["reason"] == "cTrader keeps at most 50 characters in client_order_id"
    assert label_long.context["reason"] == "cTrader keeps at most 100 characters in label"
    assert b"qa4dqobyh-01JPTS40R0AAXPDJ2WRTPTTH2Q" in payload
    assert b"qmx:a4dqobyh:dummy-trend-pullback" in payload


def test_a_stop_amendment_that_widens_is_refused_and_one_that_tightens_moves_the_venue_stop(
    tmp_path: Path,
) -> None:
    node = trading(tmp_path)
    play(node, FIRST_SEND + 900_000_000_001)
    unit = node.runtime.hosted["dep-1"].unit
    assert unit is not None and unit.handler is not None
    held = unit.handler.open_positions["fx.eurusd"]
    named = unit.venue_name(held.position_id)
    stop = node.account.stop_of(named)
    assert stop is not None

    def amend(level: Decimal, row: str) -> Placed | Blocked:
        wire: dict[str, object] = {
            "contract_format_version": 3,
            "intent_family": "exit",
            "kind": "amend_protection",
            "position_ref": {
                "position_id": held.position_id,
                "instrument": {"venue": "icmarkets-ctrader", "symbol": "EURUSD"},
                "opened_by": held.opened_by.value,
            },
            "reason_code": {"code": "trail", "book_family": "unit"},
            "decision_row_id": row,
            "stop": str(level),
            "targets": [],
        }
        intent = RestingIntent.try_create(f"exit:{row}", "fx.eurusd", order=wire)
        assert not isinstance(intent, TypedRefusal), intent
        return unit.place(intent.value, Instant(FIRST_SEND))

    widened = amend(stop + Decimal("0.00050"), "row-widen")
    widened_sent = [t.command.kind for t in node.account.received]
    tightened = amend(stop - Decimal("0.00010"), "row-tighten")

    assert (held.side.value, widened) == (
        "short",
        Blocked("the amendment widens the stop, so the node refused it"),
    )
    assert CommandKind.AMEND_PROTECTION not in widened_sent
    assert tightened == Placed(stop - Decimal("0.00010"))
    assert node.account.stop_of(named) == stop - Decimal("0.00010")
    assert node.account.received[-1].command.kind is CommandKind.AMEND_PROTECTION
