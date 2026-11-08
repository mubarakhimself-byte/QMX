"""His promote click (Part C AD-324, slice C-23): only his principal moves a unit toward paper
or live, the move lands once through the host's lifecycle writer, and the deployment the node is
asked to take is built from the Library. The node is a recording conformance double behind the
real node link and the real staging folder; no order, account or secret is touched."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmf.core import is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.data.journal_writer import JournalWriter, WriterScope
from qml.compile import CompiledUnit, compile_unit
from qml.lifecycle import Actor, ActorKind, Event, State
from qmx_apps.errors import AppError
from qmx_control.catalog import rows as catalog_rows
from qmx_control.models import Document
from qmx_engine.control_door import PRINCIPAL, UNNAMED
from qmx_engine.service.context import Caller
from qmx_judge.landing import G_CHECK, TEST_REPORT
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import MAIN, Principal
from qmx_tools.gather import FIXTURE_RECORDS, gather
from starlette.types import ASGIApp, Receive, Scope, Send

from qmx_host.first_start import land_dummy
from qmx_host.host import HostStore, LanderLibrary, open_store, register_checkers
from qmx_host.lifecycle import LifecycleWriter, MoveRefused
from qmx_host.market_data import MarketDoor
from qmx_host.node_link import NodeLink
from qmx_host.promote import ROUTE, Promoter, harvested_calibrations, promote_router
from qmx_host.records import Cadence, Harvester, append_roots

OPERATOR = Principal("operator")
DUMMY = "dummy-trend-pullback"
TAG = "a4dqobyh"
DEFAULTS = {
    "ema_period": "100",
    "roc_lookback": "20",
    "min_trend_strength": "0",
    "rsi_period": "14",
    "rsi_low": "30",
    "rsi_high": "70",
    "stop_buffer": "0.0002",
    "target_r": "2",
    "time_out_bars": "48",
    "risk_fraction": "0.005",
}
CLICKED = datetime(2026, 11, 3, 9, 0, tzinfo=UTC)
HIM = Caller("user")
"""His UI bearer's caller, whose principal is `operator` (`qmx_engine/service/context.py`)."""


@dataclass
class ConformanceNode:
    """The trading node's `deploy` and `withdraw` as the node link reaches it on this machine:
    it refuses another node's tag, a compiled fingerprint its G record did not test, and a
    staged file missing or not matching its fingerprint, as the node's preflight does."""

    home: Path
    calls: list[tuple[str, Document]] = field(default_factory=list[tuple[str, Document]])
    held: dict[str, Document] = field(default_factory=dict[str, Document])
    refuse_deploy: str | None = None
    withdraw_times_out: bool = False

    def get(self, app: str) -> Document:
        return {"id": app}

    def call(
        self, app: str, operation: str, arguments: Document, *, pin: Document | None = None
    ) -> Document:
        del app, pin
        self.calls.append((operation, arguments))
        if operation == "deploy":
            return {"result": self._deploy(cast(Document, arguments["deployment"]))}
        if self.withdraw_times_out:
            raise AppError("tool_timeout", "The tool did not complete within its timeout.", 504)
        if str(arguments["deployment_id"]) not in self.held:
            return {"result": {"ok": False, "code": "unknown_deployment", "message": "none"}}
        self.held.pop(str(arguments["deployment_id"]))
        return {"result": {"ok": True, "value": {"state": "accepted"}}}

    def _deploy(self, document: Document) -> Document:
        if self.refuse_deploy is not None:
            return {"ok": False, "code": self.refuse_deploy, "message": "the node refuses it"}
        g = cast(Document, document["g_record"])
        if document["compiled_fingerprint"] != g["compiled_fingerprint"]:
            return {"ok": False, "code": "fingerprint_mismatch", "message": "not tested"}
        if cast(Document, document["node"])["tag"] != TAG:
            return {"ok": False, "code": "bad_argument", "message": "another node"}
        folder = (
            self.home / "apps" / "trading-node" / "data" / "deployments"
            / str(document["deployment_id"]) / "in"
        )  # fmt: skip
        for item in cast(list[Document], document["files"]):
            data = (folder / str(item["path"])).read_bytes()
            if f"sha256:{hashlib.sha256(data).hexdigest()}" != item["fingerprint"]:
                return {"ok": False, "code": "file_mismatch", "message": str(item["path"])}
        self.held[str(document["deployment_id"])] = document
        return {"ok": True, "value": {"deployment_id": document["deployment_id"]}}

    def deploys(self) -> list[Document]:
        return [cast(Document, a["deployment"]) for op, a in self.calls if op == "deploy"]

    def withdraws(self) -> list[str]:
        return [str(a["deployment_id"]) for op, a in self.calls if op == "withdraw"]


@dataclass
class Rig:
    home: Path
    store: HostStore
    lifecycle: LifecycleWriter
    node: ConformanceNode
    app: FastAPI
    unit: str
    compiled: CompiledUnit
    promoter: Promoter

    def click(self, caller: Caller = HIM, **body: Any) -> tuple[int, dict[str, Any]]:
        sent: dict[str, Any] = {
            "schema_version": "qmx.units.promote/1",
            "unit": {"id": DUMMY, "version": self.unit},
            "market_id": "fx.eurusd",
            "node": {"tag": TAG},
            "account": {"id": "demo-1"},
            **body,
        }
        answer = TestClient(as_caller(self.app, caller)).post(ROUTE, json=sent)
        return answer.status_code, answer.json()

    def moves(self) -> list[tuple[str, str, str, dict[str, object]]]:
        found: list[tuple[str, str, str, dict[str, object]]] = []
        for folder in stream_folders(self.home / "journals"):
            lines = read_committed(folder)
            assert not is_refusal(lines)
            for line in lines.value:
                if isinstance(line, JournalLine):
                    body = cast(dict[str, object], line.record["body"])
                    found.append(
                        (
                            str(body["market_id"]),
                            str(body["from"]),
                            str(body["to"]),
                            cast(dict[str, object], body["by"]),
                        )
                    )
        return found


def as_caller(app: ASGIApp, caller: Caller) -> ASGIApp:
    async def served(scope: Scope, receive: Receive, send: Send) -> None:
        token = PRINCIPAL.set(caller)
        try:
            await app(scope, receive, send)
        finally:
            PRINCIPAL.reset(token)

    return served


def put(store: HostStore, kind: str, item: str, fields: JsonObject) -> str:
    draft = Draft(kind, item, item, fields=fields)
    return store.put(OPERATOR, draft, on=MAIN, expected_head=None).object_id


def judged(writer: LifecycleWriter, unit: str, compiled: str, market: str) -> None:
    writer.record_move(
        Event(
            event_id=f"judge-{market}",
            unit_id=DUMMY,
            version_ref=unit,
            compiled_fingerprint=compiled,
            market_id=market,
            from_state=State.DRAFT,
            to_state=State.TESTED,
            by=Actor(ActorKind.JUDGE, "agent:chat"),
            reason="the judge's verdict: pass",
            evidence_ref="verdict-1",
            at=datetime(2026, 11, 2, 9, 0, tzinfo=UTC),
            writer="",
            sequence=0,
        )
    )


def g_report(store: HostStore, compiled: str, verdict: str = "pass") -> str:
    fields: JsonObject = {
        "check": G_CHECK,
        "run_id": f"qmbr-g-{verdict}",
        "status": "finished",
        "compiled_fingerprint": compiled,
        "behaviour": {},
        "safety": {"verdict": verdict},
    }
    return put(store, TEST_REPORT, f"qmbr-g-{verdict}", fields)


@pytest.fixture
def rig(tmp_path: Path) -> Iterator[Rig]:
    home = tmp_path / "QMX"
    with open_store(home, home / "library", serving=False, floor=0) as store:
        register_checkers(store)
        writer = LifecycleWriter(home / "journals", "pc", "test")
        store.lifecycle = writer
        for name in ("eurusd", "xauusd"):
            record = json.loads((FIXTURE_RECORDS / f"{name}.json").read_text("utf-8"))
            record.pop("record_version")
            put(store, "instrument", f"instrument-{name}", record)
        for account_id, world in (("demo-1", "demo"), ("live-1", "live")):
            account: JsonObject = {
                "venue": "icmarkets-ctrader",
                "account_id": account_id,
                "world": world,
            }
            put(store, "account", f"account-{account_id}", account)
        unit = cast(str, land_dummy(store))
        document = store.get(OPERATOR, unit).fields
        compiled = compile_unit(document, gather(store, document).context)
        assert isinstance(compiled, CompiledUnit), compiled
        judged(writer, unit, compiled.compiled_fingerprint.value, "fx.eurusd")
        node = ConformanceNode(home)
        link = NodeLink(
            home,
            here="pc",
            apps=cast(Any, node),
            settings=dict,
            pass_keys=dict,
            blobs=lambda fingerprint: [store.read_blob(fingerprint)],
        )
        promoter = Promoter(
            store,
            writer,
            link,
            LanderLibrary(store),
            calibrations=harvested_calibrations(home, lambda: time.time_ns() + 10**12),
            trading_profile=lambda _place: False,
            now=lambda: CLICKED,
        )
        app = FastAPI()
        app.include_router(promote_router(promoter))
        yield Rig(home, store, writer, node, app, unit, compiled, promoter)
        writer.close()


def test_his_click_promotes_the_dummy_to_paper_and_the_node_takes_one_deployment(
    rig: Rig,
) -> None:
    fp = rig.compiled.compiled_fingerprint.value
    report = g_report(rig.store, fp)

    status, answer = rig.click(op_id="click-1", to="paper")

    deployment_id = answer["value"]["deployment_id"]
    (sent,) = rig.node.deploys()
    assert (status, answer["ok"], answer["value"]["node_answer"]) == (200, True, "accepted")
    assert rig.moves()[1:] == [
        ("fx.eurusd", "tested", "paper", {"kind": "his_click", "principal": "operator"})
    ]
    assert (sent["deployment_id"], sent["lane"], sent["node"]) == (
        deployment_id,
        "paper",
        {"tag": TAG, "install_id": None},
    )
    assert sent["g_record"] == {"id": "qmbr-g-pass", "version": 1, "compiled_fingerprint": fp}
    assert sent["compiled_fingerprint"] == fp
    assert sent["starting"] == {"source": "defaults", "values": DEFAULTS}
    assert sent["unit"] == {"id": DUMMY, "version": rig.unit}
    assert sent["lifecycle_event"] == answer["value"]["lifecycle_event_id"]
    markets = cast(list[Document], sent["markets"])
    assert [m["market_id"] for m in markets] == ["fx.eurusd"]
    assert cast(Document, markets[0]["instrument"])["id"] == "instrument-eurusd"
    assert cast(Document, sent["account"])["id"] == "demo-1"
    files = cast(list[Document], sent["files"])
    assert len(files) == 2 * len(
        gather(rig.store, rig.store.get(OPERATOR, rig.unit).fields).context.sources
    )
    assert {str(f["kind"]) for f in files} == {"block", "entry"}
    assert all(rig.store.has_blob(str(f["fingerprint"])) for f in files)
    assert report in rig.store.with_field(TEST_REPORT, "compiled_fingerprint", fp)
    symbols = [s.get("symbol") for s in cast(list[Document], sent["snapshots"])]
    assert symbols == ["EURUSD", "XAUUSD", None]


@pytest.mark.parametrize(
    "caller",
    [
        Caller("agent", "x"),
        Caller("workflow", "y"),
        Caller("agent", "mcp"),
        Caller("agent", "observer:o"),
        UNNAMED,
    ],
    ids=["agent", "run", "mcp", "observer", "unnamed"],
)
def test_every_principal_but_his_is_refused_and_nothing_moves(rig: Rig, caller: Caller) -> None:
    g_report(rig.store, rig.compiled.compiled_fingerprint.value)
    forged = {"principal": "operator", "created_by": "operator"}

    status, answer = rig.click(caller, op_id="click-1", to="paper", **forged)

    assert (status, answer["code"]) == (403, "refused_principal")
    assert answer["message"] == (
        f"a unit moves toward paper or live only by his click, not by {caller.principal}"
    )
    assert (len(rig.moves()), rig.node.calls) == (1, [])


def test_a_forged_principal_in_his_own_body_is_a_bad_request(rig: Rig) -> None:
    status, answer = rig.click(op_id="click-1", to="paper", principal="operator")

    assert (status, answer["code"], answer["message"]) == (
        400,
        "bad_request",
        "principal: Extra inputs are not permitted",
    )
    assert rig.node.calls == []


def test_draft_to_live_is_an_illegal_move_and_reaches_no_node(rig: Rig) -> None:
    g_report(rig.store, rig.compiled.compiled_fingerprint.value)

    status, answer = rig.click(
        op_id="click-1", to="live", market_id="metal.xauusd", placeholders_acknowledged=True
    )

    assert (status, answer["code"], answer["message"]) == (
        409,
        "illegal_move",
        "not_in_table: his_click cannot move draft to live",
    )
    assert (len(rig.moves()), rig.node.calls) == (1, [])


def test_the_same_click_sent_twice_lands_nothing_new(rig: Rig) -> None:
    g_report(rig.store, rig.compiled.compiled_fingerprint.value)

    first = rig.click(op_id="click-1", to="paper")
    second = rig.click(op_id="click-1", to="paper")

    assert first == second
    assert (len(rig.moves()), len(rig.node.deploys())) == (2, 1)


def test_a_unit_with_no_passing_g_report_is_refused(rig: Rig) -> None:
    fp = rig.compiled.compiled_fingerprint.value
    none = rig.click(op_id="click-1", to="paper")
    g_report(rig.store, fp, verdict="fail")
    failed = rig.click(op_id="click-2", to="paper")

    assert (none[0], none[1]["code"], none[1]["message"]) == (
        409,
        "no_g_record",
        f"no G test-report for compiled fingerprint {fp}",
    )
    assert failed[1]["code"] == "no_g_record"
    assert failed[1]["message"].endswith(f"failed for compiled fingerprint {fp}")
    assert (len(rig.moves()), rig.node.calls) == (1, [])


def test_a_node_that_refuses_deploy_moves_nothing(rig: Rig) -> None:
    g_report(rig.store, rig.compiled.compiled_fingerprint.value)
    rig.node.refuse_deploy = "identity_unconfirmed"

    status, answer = rig.click(op_id="click-1", to="paper")

    assert (status, answer["code"]) == (409, "node_not_ready")
    assert answer["message"] == (
        "the node refused the deployment: identity_unconfirmed: the node refuses it"
    )
    assert len(rig.moves()) == 1


def paper(rig: Rig) -> str:
    g_report(rig.store, rig.compiled.compiled_fingerprint.value)
    status, answer = rig.click(op_id="click-paper", to="paper")
    assert status == 200, answer
    return str(answer["value"]["deployment_id"])


def calibrated(rig: Rig, rows: list[tuple[str, str, int]]) -> None:
    """The paper lane's calibration rows, written by the node's unit writer into its volume and
    filed by one round of this machine's real harvester."""
    root = rig.home / "apps" / "trading-node" / "data" / "journal"
    now = time.time_ns()
    scope = WriterScope(JournalStream.UNIT, DUMMY, JournalWorld.PAPER, "pc", "node", "test")
    opened = JournalWriter.open(root, scope, clock=lambda: now, boot_epoch_id="boot1")
    assert not is_refusal(opened)
    for index, (number, new, watermark) in enumerate(rows):
        body = {
            "row_id": f"cal-{index}",
            "number": number,
            "old": "0",
            "new": new,
            "rule": "trend-floor-from-record@1",
            "read_trades": {"from_trade_id": "t0", "to_trade_id": "t19", "count": 20},
            "statistic": {"floor": new},
            "watermark": watermark,
        }
        facts = RowFacts(
            ts_recv=now + index,
            clock_ok=True,
            unit_id=DUMMY,
            unit_version=rig.compiled.document_fingerprint.value,
        )
        assert not is_refusal(opened.value.append("calibration", body, facts))
    opened.value.close()
    door = MarketDoor(root=rig.home / "market")
    harvester = Harvester(
        lambda: append_roots(rig.home), door, rig.home / "records", journals_open=True
    )
    harvester.round(datetime.now(UTC), Cadence.of({}, {}))


def test_paper_to_live_onto_a_demo_account_carries_the_last_calibrated_values(rig: Rig) -> None:
    paper(rig)
    calibrated(
        rig,
        [
            ("min_trend_strength", "0.0012", 1_762_000_000_000_000_000),
            ("min_trend_strength", "0.0015", 1_762_100_000_000_000_000),
        ],
    )

    status, answer = rig.click(op_id="click-live", to="live", placeholders_acknowledged=True)

    live = rig.node.deploys()[-1]
    assert (status, answer["value"]["node_answer"], live["lane"]) == (200, "accepted", "live")
    assert live["starting"] == {
        "source": "paper_lane",
        "values": {**DEFAULTS, "min_trend_strength": "0.0015"},
        "watermark": 1_762_100_000_000_000_000,
    }
    assert rig.moves()[-1] == (
        "fx.eurusd",
        "paper",
        "live",
        {"kind": "his_click", "principal": "operator"},
    )


def test_a_live_move_needs_the_trading_profile_on_a_live_world_account_and_his_tick(
    rig: Rig,
) -> None:
    paper(rig)
    live_world = rig.click(
        op_id="click-live", to="live", account={"id": "live-1"}, placeholders_acknowledged=True
    )
    unticked = rig.click(op_id="click-live-2", to="live")

    assert (live_world[1]["code"], live_world[1]["message"]) == (
        "trading_profile_off",
        "account live-1 is a live-world account and the host at pc is not in the trading profile",
    )
    assert unticked[1]["code"] == "placeholders_unacknowledged"
    assert (len(rig.moves()), len(rig.node.deploys())) == (2, 1)


def test_a_park_asks_the_node_to_withdraw_the_paper_deployment(rig: Rig) -> None:
    deployment = paper(rig)

    status, answer = rig.click(op_id="click-park", to="parked", node=None, account=None)

    assert (status, answer["value"]["node_answer"]) == (200, "accepted")
    assert rig.node.withdraws() == [deployment]
    assert rig.node.held == {}
    assert rig.moves()[-1][1:3] == ("paper", "parked")


def test_a_withdraw_that_times_out_keeps_the_park_and_a_second_click_finishes_it(
    rig: Rig,
) -> None:
    deployment = paper(rig)
    rig.node.withdraw_times_out = True

    timed_out = rig.click(op_id="click-park", to="parked", node=None, account=None)
    rig.node.withdraw_times_out = False
    again = rig.click(op_id="click-park-2", to="parked", node=None, account=None)

    assert (timed_out[0], timed_out[1]["code"]) == (409, "node_not_ready")
    assert timed_out[1]["value"]["lifecycle_event_id"] == again[1]["value"]["lifecycle_event_id"]
    assert (again[0], again[1]["value"]["node_answer"]) == (200, "accepted")
    assert rig.node.withdraws() == [deployment, deployment]
    assert [move[1:3] for move in rig.moves()] == [
        ("draft", "tested"),
        ("tested", "paper"),
        ("paper", "parked"),
    ]


def test_a_live_world_account_refuses_a_two_market_unit_before_the_node(rig: Rig) -> None:
    def trading(place: str) -> bool:
        return place == "pc"

    rig.promoter.trading_profile = trading
    paper(rig)

    status, answer = rig.click(
        op_id="click-live", to="live", account={"id": "live-1"}, placeholders_acknowledged=True
    )

    assert (status, answer["code"], answer["message"], answer["next_step"]) == (
        409,
        "multi_market_live",
        "the node runs every market of a unit, and dummy-trend-pullback trades 2 markets;"
        " a live-world account takes a one-market unit until the node reads deployment.markets",
        "Make a one-market version of the unit for live money, or promote it onto a demo account.",
    )
    assert (len(rig.moves()), len(rig.node.deploys())) == (2, 1)


def test_a_second_market_of_a_running_version_answers_the_deployment_that_runs_it(
    rig: Rig,
) -> None:
    judged(rig.lifecycle, rig.unit, rig.compiled.compiled_fingerprint.value, "metal.xauusd")
    running = paper(rig)

    second = rig.click(op_id="click-gold", to="paper", market_id="metal.xauusd")
    rig.click(op_id="click-park", to="parked", node=None, account=None)
    after_park = rig.click(op_id="click-gold-2", to="paper", market_id="metal.xauusd")

    assert (second[0], second[1]["code"], second[1]["value"]) == (
        409,
        "already_deployed",
        {"deployment_id": running},
    )
    assert second[1]["message"] == (
        f"deployment {running} already runs dummy-trend-pullback on fx.eurusd, and the node runs"
        " every market of a unit, metal.xauusd among them"
    )
    assert (after_park[0], after_park[1]["value"]["node_answer"]) == (200, "accepted")
    assert [move[:3] for move in rig.moves()] == [
        ("fx.eurusd", "draft", "tested"),
        ("metal.xauusd", "draft", "tested"),
        ("fx.eurusd", "tested", "paper"),
        ("fx.eurusd", "paper", "parked"),
        ("metal.xauusd", "tested", "paper"),
    ]
    assert len(rig.node.deploys()) == 2


def test_a_record_that_fails_after_the_deploy_names_what_a_timed_out_withdraw_left(
    rig: Rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    g_report(rig.store, rig.compiled.compiled_fingerprint.value)

    def full(event: Event) -> str:
        raise MoveRefused("storage", "the lifecycle row was not written: disk full")

    monkeypatch.setattr(rig.lifecycle, "record_move", full)
    rig.node.withdraw_times_out = True

    status, answer = rig.click(op_id="click-1", to="paper")

    (held,) = rig.node.held
    assert (status, answer["code"], answer["value"]) == (
        409,
        "node_not_ready",
        {"deployment_id": held},
    )
    assert answer["message"] == (
        "storage: the lifecycle row was not written: disk full, and the node did not withdraw"
        f" deployment {held}: tool_timeout"
    )
    assert answer["next_step"] == f"Kill deployment {held} on the node's card."
    assert (len(rig.moves()), rig.node.withdraws()) == (1, [held])


def test_an_os_error_from_the_record_withdraws_and_the_same_click_again_moves_nothing(
    rig: Rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    g_report(rig.store, rig.compiled.compiled_fingerprint.value)

    def full(event: Event) -> str:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(rig.lifecycle, "record_move", full)
    first = rig.click(op_id="click-1", to="paper")
    monkeypatch.undo()
    again = rig.click(op_id="click-1", to="paper")

    assert (first[0], first[1]["code"], first[1]["message"], first[1]["next_step"]) == (
        409,
        "illegal_move",
        "storage: [Errno 28] No space left on device",
        "The node withdrew the deployment and nothing moved; click again.",
    )
    assert (again[0], again[1]["code"], again[1]["message"]) == (
        409,
        "illegal_move",
        "click-1 was sent before and its move was not recorded",
    )
    assert (len(rig.moves()), len(rig.node.deploys()), rig.node.held) == (1, 1, {})


def test_no_agent_tool_reaches_the_promote_route() -> None:
    surface = [
        (row.toolset, row.op, row.target, row.rest)
        for row in catalog_rows()
        if "promote" in f"{row.op} {row.target} {row.rest}".lower()
    ]
    agents = Path(__file__).resolve().parents[3]
    named = [
        path.relative_to(agents).as_posix()
        for folder in ("packages", "plugin", "apps")
        for path in (agents / folder).rglob("*")
        if path.suffix in {".py", ".json", ".toml", ".md"}
        and "/tests/" not in path.as_posix()
        and ROUTE in path.read_text("utf-8", errors="ignore")
    ]

    assert surface == []
    assert named == ["packages/qmx-host/src/qmx_host/promote.py"]
