"""Records come home from the nodes by pull (Part B B16, AD-210; Level 0 AD-28).

A far host `ldn-1` answers the real host route over a real market-data door off This PC, holding
three closed months of recorded bars and the open one, each committed `node`-born as its
harvester commits them. This PC's real pull asks it through the route in process and commits
through its own real door. A second node `fra-2` never answers. The pairing key is a fake made at
runtime.
"""

from __future__ import annotations

import json
import secrets
import shutil
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import JsonValue
from qmb.execution.fill import FillKind
from qmb.host.unit_handler import UnitTrade
from qmb.results.journal import RunJournal
from qmf.core import Instant, is_refusal
from qmf.data import journal_writer
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.series import SeriesKey
from qmf.data.store.engines.jsonl import jsonl_opener
from qmf.data.store.engines.typed import TypedWriter
from qml.unit.model import Side
from qmx_apps.supervisor import Supervisor
from qmx_engine.ledger import redact
from qmx_engine.service.forward import PASS_HEADER, mint_host_pass
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import MAIN, Principal
from qmx_library.store import Store
from test_backups_service import Clock as BackupClock
from test_backups_service import folder, service
from test_harvest import CLOSED_MONTH, COMPILED, OPEN_MONTH, Volume, harvester, volume, writer

from qmx_host.host_route import ANSWERS, Answering, Answers, host_router
from qmx_host.maintenance import maintenance_router
from qmx_host.market_data import MarketDoor, Placement
from qmx_host.node_link import SCHEMA, NodeLink, Place, Post, Unreachable
from qmx_host.records import Cadence, Fetch, Harvester, Projection, Pull, Records

__all__ = ["volume"]

FAR, DOWN = "ldn-1", "fra-2"
SERIES = f"recorder/EURUSD/bar-m1/{FAR}"
_REAL = datetime.now(UTC)  # ambient-scan: allow (the stores freeze by the real month)
OPEN = datetime(_REAL.year, _REAL.month, 1, tzinfo=UTC)


def months_before(moment: datetime, count: int) -> datetime:
    year, month = moment.year, moment.month - count
    while month < 1:
        year, month = year - 1, month + 12
    return datetime(year, month, 1, tzinfo=UTC)


CLOSED = tuple(months_before(OPEN, n) for n in (3, 2, 1))
NOW = OPEN + timedelta(days=1)
OPERATOR = Principal("operator")


def month(moment: datetime) -> str:
    return f"{moment.year:04d}-{moment.month:02d}"


def key(moment: datetime) -> SeriesKey:
    source, subject, kind, variant = SERIES.split("/")
    made = SeriesKey.try_create(source, subject, kind, moment.year, moment.month, variant)
    assert not is_refusal(made)
    return made.value


def commit(
    door: MarketDoor,
    root: Path,
    moment: datetime,
    rows: int,
    *,
    times: int = 1,
    born_on: Placement = Placement.NODE,
) -> None:
    """Commit ``rows`` one-minute bars of a month `node`-born, as a node's harvester does; a
    closed bar month freezes on its second commit of the same rows."""
    made = key(moment)
    staging = root / "staging"
    target = staging.joinpath(*SERIES.split("/"), f"{month(moment)}.parquet")
    target.parent.mkdir(parents=True, exist_ok=True)
    start = int(moment.timestamp()) * 1_000
    bars = [(start + n * 60_000, 108_000, 108_010, 107_990, 108_005, 12.5) for n in range(rows)]
    for _ in range(times):
        TypedWriter(target, made.text, made.rule.columns).add(bars).finish()
        receipts = door.commit([target], staging=staging, born_on=born_on)
        assert not is_refusal(receipts)
        target.unlink()


def state(door: MarketDoor, moment: datetime) -> Mapping[str, object]:
    path = door.store_root.joinpath(*SERIES.split("/"), month(moment), "state.json")
    return cast("Mapping[str, object]", json.loads(path.read_text(encoding="utf-8")))


@dataclass
class Far:
    """The far host's door and route, and every ask This PC sent it."""

    door: MarketDoor
    client: TestClient
    root: Path
    key: str
    asked: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    fetched: list[str] = field(default_factory=list[str])

    def commit(self, moment: datetime, rows: int, *, times: int = 1) -> None:
        commit(self.door, self.root, moment, rows, times=times)

    def state(self, moment: datetime) -> Mapping[str, object]:
        return state(self.door, moment)

    def post(
        self, url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str], _: float | None
    ) -> JsonValue:
        if url.startswith(f"http://{DOWN}"):
            raise Unreachable("ConnectError: the far host is off")
        self.asked.append(dict(body))
        return cast(
            "JsonValue", self.client.post("/api/host/forward", json=body, headers=headers).json()
        )

    def fetch(
        self, url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str], into: Path
    ) -> int:
        answer = self.client.post("/api/host/forward", json=dict(body), headers=dict(headers))
        self.fetched.append(str(cast("Mapping[str, object]", body["args"])["fingerprint"]))
        into.write_bytes(answer.content)
        return answer.status_code

    def confirmed(self) -> list[list[str]]:
        return [
            sorted(cast("list[str]", ask["args"]["confirmed"]))
            for ask in self.asked
            if ask["verb"] == "data.list"
        ]


@pytest.fixture
def far(tmp_path: Path) -> Iterator[Far]:
    pairing = secrets.token_hex(16)
    root = tmp_path / FAR
    root.mkdir()
    door = MarketDoor(root=root / "market", placement=Placement.SERVER)
    link = NodeLink(
        root,
        here=FAR,
        apps=cast("Supervisor", None),
        settings=dict,
        pass_keys=lambda: {"pc": pairing},
    )

    async def beats() -> Mapping[str, object]:
        return {}

    answering = Answering(
        link,
        pass_keys=lambda: {"pc": pairing},
        heartbeats=beats,
        store_root=lambda: door.store_root,
        answers=Answers(root / ANSWERS),
        door=lambda: door,
    )
    app = FastAPI()
    app.include_router(host_router(answering))
    with TestClient(app) as client:
        made = Far(door, client, root, pairing)
        for closed in CLOSED:
            made.commit(closed, 30, times=2)
        made.commit(OPEN, 60)
        yield made


def pc_door(tmp_path: Path) -> MarketDoor:
    return MarketDoor(root=tmp_path / "pc" / "market")


def pull(
    tmp_path: Path,
    far: Far,
    *,
    down: bool = False,
    fetch: Fetch | None = None,
    post: Post | None = None,
) -> Pull:
    places = {FAR: Place(FAR, f"http://{FAR}", ())}
    if down:
        places[DOWN] = Place(DOWN, f"http://{DOWN}", ())
    return Pull(
        pc_door(tmp_path),
        tmp_path / "pc" / "records",
        here="pc",
        places=lambda: places,
        pass_keys=lambda: {FAR: far.key, DOWN: far.key},
        post=far.post if post is None else post,
        fetch=far.fetch if fetch is None else fetch,
    )


def watermark(tmp_path: Path) -> str:
    found = json.loads((tmp_path / "pc" / "records" / "pull.json").read_text(encoding="utf-8"))
    return str(found["nodes"][FAR]["watermark"])


def home_rows(tmp_path: Path, moment: datetime) -> tuple[int, bool, str] | None:
    held = pc_door(tmp_path).series_store().state(key(moment))
    return None if held is None else (held.rows, held.frozen, held.fingerprint)


def test_a_node_door_pins_what_it_harvests_and_this_pcs_door_does_not(tmp_path: Path) -> None:
    server = MarketDoor(root=tmp_path / "server", placement=Placement.SERVER)
    pc = MarketDoor(root=tmp_path / "pc")
    commit(server, tmp_path / "server", CLOSED[0], 30, times=2)
    commit(pc, tmp_path / "pc", CLOSED[0], 30, times=2)
    printed = str(state(server, CLOSED[0])["fingerprint"])

    before = (server.pinned(), pc.pinned())
    cleared = server.verify([printed])
    commit(server, tmp_path / "server", CLOSED[0], 30)

    assert before == ((f"{FAR}/{month(CLOSED[0])}",), ())
    assert not is_refusal(cleared)
    assert cleared.value == (f"{FAR}/{month(CLOSED[0])}",)
    assert server.pinned() == ()
    kept = server.store_root.joinpath(*SERIES.split("/"), month(CLOSED[0]))
    assert sorted(path.name for path in kept.iterdir()) == [f"{printed}.parquet", "state.json"]


def test_three_closed_months_come_home_and_the_far_door_unpins_them_after_the_next_list(
    tmp_path: Path, far: Far
) -> None:
    pulling = pull(tmp_path, far)
    printed = {moment: str(far.state(moment)["fingerprint"]) for moment in (*CLOSED, OPEN)}
    pinned_before = far.door.pinned()

    (first,) = pulling.round(NOW, Cadence())
    pinned_between = far.door.pinned()
    (second,) = pulling.round(NOW + timedelta(seconds=300), Cadence())

    every = tuple(f"{FAR}/{month(moment)}" for moment in (*CLOSED, OPEN))
    assert pinned_before == pinned_between == every
    assert (first.reached, first.partitions, first.open_fetched, first.confirmed) == (True, 4, 1, 0)
    assert [home_rows(tmp_path, moment) for moment in (*CLOSED, OPEN)] == [
        (30, True, printed[CLOSED[0]]),
        (30, True, printed[CLOSED[1]]),
        (30, True, printed[CLOSED[2]]),
        (60, False, printed[OPEN]),
    ]
    assert watermark(tmp_path) == max(str(far.state(moment)["at"]) for moment in (*CLOSED, OPEN))
    assert far.confirmed() == [[], sorted(printed[moment] for moment in CLOSED)]
    assert (second.partitions, second.confirmed, second.refusals) == (0, 3, ())
    assert far.door.pinned() == second.still_pinned == (f"{FAR}/{month(OPEN)}",)
    assert [far.state(moment)["frozen"] for moment in CLOSED] == [True, True, True]


def test_the_open_month_is_fetched_again_only_when_it_changed_and_its_pull_is_due(
    tmp_path: Path, far: Far
) -> None:
    pulling = pull(tmp_path, far)
    pulling.round(NOW, Cadence())
    sixty = home_rows(tmp_path, OPEN)
    far.commit(OPEN, 120)
    (early,) = pulling.round(NOW + timedelta(seconds=300), Cadence())
    rows_early = home_rows(tmp_path, OPEN)
    far.commit(OPEN, 180)
    (due,) = pulling.round(NOW + timedelta(seconds=3_600), Cadence())
    rows_due = home_rows(tmp_path, OPEN)
    far.commit(OPEN, 180)
    (unchanged,) = pulling.round(NOW + timedelta(seconds=7_500), Cadence())

    assert (early.waiting, early.open_fetched, early.oldest_unshipped) == (1, 0, month(OPEN))
    assert sixty is not None
    assert rows_early == sixty == (60, False, sixty[2])
    assert (due.open_fetched, rows_due) == (1, (180, False, str(far.state(OPEN)["fingerprint"])))
    assert (unchanged.already_home, unchanged.open_fetched) == (1, 0)
    assert far.fetched.count(str(far.state(OPEN)["fingerprint"])) == 1
    assert len(far.fetched) == 5


def test_a_resend_of_months_already_home_changes_nothing(tmp_path: Path, far: Far) -> None:
    pulling = pull(tmp_path, far)
    pulling.round(NOW, Cadence())
    store = tmp_path / "pc" / "market" / "series"
    before = {path: path.read_bytes() for path in sorted(store.rglob("*")) if path.is_file()}
    (tmp_path / "pc" / "records" / "pull.json").unlink()

    (resent,) = pulling.round(NOW + timedelta(seconds=300), Cadence())

    after = {path: path.read_bytes() for path in sorted(store.rglob("*")) if path.is_file()}
    assert (resent.partitions, resent.already_home, resent.open_fetched) == (0, 4, 0)
    assert len(far.fetched) == 4
    assert after == before


def test_rows_that_do_not_match_the_listed_fingerprint_never_land(tmp_path: Path, far: Far) -> None:
    oldest = str(far.state(CLOSED[0])["fingerprint"])
    newer = str(far.state(CLOSED[1])["fingerprint"])

    def swapped(
        url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str], into: Path
    ) -> int:
        status = far.fetch(url, body, headers, into)
        if far.fetched[-1] == oldest:
            asked: dict[str, JsonValue] = {**body, "args": {"fingerprint": newer}}
            status = far.fetch(url, asked, headers, into)
        return status

    pulling = pull(tmp_path, far, fetch=swapped)

    (first,) = pulling.round(NOW, Cadence())

    assert home_rows(tmp_path, CLOSED[0]) is None
    assert [item["key"] for item in first.refusals] == [key(CLOSED[0]).text]
    assert str(first.refusals[0]["reason"]).endswith(f"not the listed {oldest}")
    assert (first.partitions, first.oldest_unshipped) == (3, month(CLOSED[0]))
    assert watermark(tmp_path) == ""


def test_an_unreachable_node_is_skipped_and_named_and_each_round_lands_one_result(
    tmp_path: Path, far: Far
) -> None:
    pc = pc_door(tmp_path)
    now = [NOW]
    with Store.open(tmp_path / "library", redactor=redact) as store:
        job = Records(
            Harvester(lambda: (), pc, tmp_path / "pc" / "records", journals_open=True),
            Cadence,
            clock=lambda: now[0],
            store=store,
            pull=pull(tmp_path, far, down=True),
        )
        job.round()
        now[0] = NOW + timedelta(seconds=60)
        job.round()
        now[0] = NOW + timedelta(seconds=300)
        job.round()
        views = [store.get(OPERATOR, object_id) for _item, object_id in store.heads_on(MAIN)]

    results = [
        cast("Mapping[str, Any]", view.fields["metadata"])
        for view in views
        if view.kind == "artifact" and view.fields.get("type") == "maintenance-result"
    ]
    firsts = [r for r in results if r["at"] == NOW.isoformat()]
    assert len(results) == 2
    assert firsts[0]["state"] == "refused"
    assert firsts[0]["line"] == (
        "0 partitions filed from 0 streams, 0 trades projected, 0 refusals; "
        "1 of 2 nodes reached, 4 partitions brought home, fra-2 skipped"
    )
    nodes = {node["node"]: node for node in firsts[0]["nodes"]}
    assert (nodes[DOWN]["reached"], nodes[FAR]["reached"], nodes[FAR]["partitions"]) == (
        False,
        True,
        4,
    )
    assert nodes[DOWN]["refusals"] == [
        {"node": DOWN, "reason": "fra-2 did not answer: ConnectError: the far host is off"}
    ]


def test_the_maintenance_list_shows_node_records_home_with_its_pins_and_switch(
    tmp_path: Path, far: Far
) -> None:
    layout = folder(tmp_path / "QMX")
    backups = service(layout, BackupClock())
    pc = pc_door(tmp_path)
    pulling = pull(tmp_path, far, down=True)
    pulling.round(NOW, Cadence())
    pulling.round(NOW + timedelta(seconds=300), Cadence())
    job = Records(
        Harvester(lambda: (), pc, tmp_path / "pc" / "records", journals_open=True),
        Cadence,
        clock=lambda: NOW,
        pull=pulling,
    )
    app = FastAPI()
    app.include_router(maintenance_router(backups, lambda _workflow: [], job))

    listed = TestClient(app).get("/api/maintenance").json()

    row = next(item for item in listed["host"] if item["id"] == "records-home")
    shown = {node["node"]: (node["reached"], node["still_pinned"]) for node in row["nodes"]}
    assert (row["name"], row["on"], row["switch"]) == (
        "Bring node records home",
        True,
        {"section": "records", "key": "on"},
    )
    assert shown == {DOWN: (False, []), FAR: (True, [f"{FAR}/{month(OPEN)}"])}
    assert next(n for n in row["nodes"] if n["node"] == FAR)["confirmed"] == 3


def test_a_month_this_pc_lost_stays_pinned_on_the_node_and_comes_home_again(
    tmp_path: Path, far: Far
) -> None:
    pulling = pull(tmp_path, far)
    printed = [str(far.state(moment)["fingerprint"]) for moment in CLOSED]
    pulling.round(NOW, Cadence())
    lost = pc_door(tmp_path).store_root.joinpath(*SERIES.split("/"), month(CLOSED[0]))
    shutil.rmtree(lost)

    (healed,) = pulling.round(NOW + timedelta(seconds=300), Cadence())
    pinned_between = far.door.pinned()
    (after,) = pulling.round(NOW + timedelta(seconds=600), Cadence())

    assert (healed.partitions, healed.already_home, healed.confirmed) == (1, 3, 2)
    assert far.confirmed() == [[], sorted(printed[1:]), sorted(printed)]
    assert pinned_between == (f"{FAR}/{month(CLOSED[0])}", f"{FAR}/{month(OPEN)}")
    assert home_rows(tmp_path, CLOSED[0]) == (30, True, printed[0])
    assert (after.confirmed, far.door.pinned()) == (3, (f"{FAR}/{month(OPEN)}",))


def test_an_open_month_that_grew_while_it_waited_is_fetched_once_its_pull_is_due(
    tmp_path: Path, far: Far
) -> None:
    pulling = pull(tmp_path, far)
    pulling.round(NOW, Cadence())
    far.commit(OPEN, 120)

    (early,) = pulling.round(NOW + timedelta(seconds=300), Cadence())
    rows_early = home_rows(tmp_path, OPEN)
    (due,) = pulling.round(NOW + timedelta(seconds=3_700), Cadence())

    assert (early.waiting, early.open_fetched) == (1, 0)
    assert rows_early is not None and rows_early[0] == 60
    assert (due.waiting, due.open_fetched) == (0, 1)
    assert home_rows(tmp_path, OPEN) == (120, False, str(far.state(OPEN)["fingerprint"]))


def asked(
    client: TestClient,
    pairing: str,
    *,
    source: str,
    target: str,
    principal: str,
    confirmed: list[str],
) -> dict[str, Any]:
    held = mint_host_pass(pairing, source=source, target=target, principal=principal)
    body = {"schema_version": SCHEMA, "verb": "data.list", "args": {"confirmed": confirmed}}
    return cast(
        "dict[str, Any]",
        client.post("/api/host/forward", json=body, headers={PASS_HEADER: held}).json(),
    )


def listing(
    client: TestClient,
    pairing: str,
    *,
    source: str = "pc",
    target: str,
    principal: str,
    confirmed: list[str],
) -> dict[str, Any]:
    answer = asked(
        client, pairing, source=source, target=target, principal=principal, confirmed=confirmed
    )
    assert answer["ok"] is True
    return cast("dict[str, Any]", answer["value"])


def test_a_confirmed_list_from_any_principal_but_this_pcs_pull_unpins_nothing(far: Far) -> None:
    oldest = str(far.state(CLOSED[0])["fingerprint"])
    every = tuple(f"{FAR}/{month(moment)}" for moment in (*CLOSED, OPEN))

    other = [
        listing(far.client, far.key, target=FAR, principal=principal, confirmed=[oldest])
        for principal in ("operator", "run:r1")
    ]
    forged = asked(
        far.client, far.key, source="fra-2", target=FAR, principal="host:fra-2", confirmed=[oldest]
    )
    pinned_after_forged = far.door.pinned()
    real = listing(far.client, far.key, target=FAR, principal="host:pc", confirmed=[oldest])

    assert [("unpinned" in value, tuple(value["pinned"])) for value in other] == [
        (False, every),
        (False, every),
    ]
    assert (forged["code"], forged["message"]) == (
        "bad_pass",
        "this host holds no pass key for 'fra-2'",
    )
    assert pinned_after_forged == every
    assert real["unpinned"] == [f"{FAR}/{month(CLOSED[0])}"]
    assert far.door.pinned() == every[1:]


def test_this_pcs_route_never_clears_a_pc_born_pin_by_data_list(tmp_path: Path) -> None:
    pairing = secrets.token_hex(16)
    door = pc_door(tmp_path)
    commit(door, tmp_path / "pc", CLOSED[0], 30, times=2, born_on=Placement.PC)
    printed = str(state(door, CLOSED[0])["fingerprint"])
    link = NodeLink(
        tmp_path,
        here="pc",
        apps=cast("Supervisor", None),
        settings=dict,
        pass_keys=lambda: {"ldn-1": pairing},
    )

    async def beats() -> Mapping[str, object]:
        return {}

    app = FastAPI()
    app.include_router(
        host_router(
            Answering(
                link,
                pass_keys=lambda: {"ldn-1": pairing},
                heartbeats=beats,
                store_root=lambda: door.store_root,
                answers=Answers(tmp_path / ANSWERS),
                door=lambda: door,
            )
        )
    )
    with TestClient(app) as client:
        answers = [
            listing(
                client,
                pairing,
                source="ldn-1",
                target="pc",
                principal=principal,
                confirmed=[printed],
            )
            for principal in ("host:ldn-1", "run:r1")
        ]

    pin = f"{FAR}/{month(CLOSED[0])}"
    assert [("unpinned" in value, value["pinned"]) for value in answers] == [
        (False, [pin]),
        (False, [pin]),
    ]
    assert door.pinned() == (pin,)


def results(store: Store) -> list[Mapping[str, Any]]:
    views = [store.get(OPERATOR, object_id) for _item, object_id in store.heads_on(MAIN)]
    found = [
        cast("Mapping[str, Any]", view.fields["metadata"])
        for view in views
        if view.kind == "artifact" and view.fields.get("type") == "maintenance-result"
    ]
    return sorted(found, key=lambda result: str(result["at"]))


def test_an_unreadable_pull_state_fails_one_round_by_name_and_the_next_brings_records_home(
    tmp_path: Path, far: Far
) -> None:
    records = tmp_path / "pc" / "records"
    records.mkdir(parents=True)
    garbled = '{"nodes": {"ldn-1": {"opened": {"k": "soon"}}}}'
    (records / "pull.json").write_text(garbled, encoding="utf-8")
    pulling = pull(tmp_path, far)
    shown = pulling.entry(True)
    now = [NOW]
    with Store.open(tmp_path / "library", redactor=redact) as store:
        job = Records(
            Harvester(lambda: (), pc_door(tmp_path), records, journals_open=True),
            Cadence,
            clock=lambda: now[0],
            store=store,
            pull=pulling,
        )
        job.round()
        now[0] = NOW + timedelta(seconds=300)
        job.round()
        failed, next_round = results(store)

    reason = (
        "the pull round failed: ValueError: records/pull.json could not be read (a node's state"
        " is not readable: invalid literal for int() with base 10: 'soon'); it was set aside as"
        " pull.json.corrupt, so the next round lists every node from the start"
    )
    assert (shown["problem"], shown["nodes"]) == (
        "records/pull.json could not be read: a node's state is not readable: invalid literal"
        " for int() with base 10: 'soon'",
        [],
    )
    assert (failed["state"], failed["pull_failed"]) == ("refused", reason)
    assert failed["line"] == (
        f"0 partitions filed from 0 streams, 0 trades projected, 0 refusals; {reason}"
    )
    assert (records / "pull.json.corrupt").read_text(encoding="utf-8") == garbled
    assert (next_round["state"], next_round["nodes"][0]["partitions"]) == ("ok", 4)


def test_a_node_whose_round_raises_is_named_and_the_other_node_still_comes_home(
    tmp_path: Path, far: Far
) -> None:
    def post(
        url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str], wait: float | None
    ) -> JsonValue:
        if url.startswith(f"http://{DOWN}"):
            raise RuntimeError("the answer was not one JSON table")
        return far.post(url, body, headers, wait)

    pulling = pull(tmp_path, far, down=True, post=post)

    down, reached = pulling.round(NOW, Cadence())

    assert (down.node, down.reached, down.refusals) == (
        DOWN,
        False,
        (
            {
                "node": DOWN,
                "reason": "its round failed: RuntimeError: the answer was not one JSON table",
            },
        ),
    )
    assert (reached.node, reached.reached, reached.partitions) == (FAR, True, 4)


@pytest.fixture
def one_row_files(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every journal line opens a new rotation file, so a test reads which rows a round opened."""
    monkeypatch.setattr(journal_writer, "jsonl_opener", lambda: jsonl_opener(1))


def into_paper(home: Path, volume: Volume, at: datetime) -> None:
    """This PC's real lifecycle row, so a lane's start does not depend on the rows it is handed."""
    host = writer(home / "journals", JournalStream.UNIT, "dummy", volume.clock)
    volume.clock.at(at)
    body = {
        "schema": "qmx.lifecycle/1",
        "event_id": "move-paper",
        "unit_id": "dummy",
        "version_ref": "v1",
        "compiled_fingerprint": "fp1-dummy",
        "market_id": "fx.eurusd",
        "from": "tested",
        "to": "paper",
        "by": {"kind": "his_click", "principal": "operator"},
        "reason": "his click",
        "at": at.isoformat(),
    }
    facts = RowFacts(ts_recv=volume.clock.ns, clock_ok=True, unit_id="dummy", market_id="fx.eurusd")
    assert not is_refusal(host.append("lifecycle", body, facts))
    host.close()


def paper_scores(store: Store) -> list[tuple[object, object, object]]:
    views = [store.get(OPERATOR, object_id) for _item, object_id in store.heads_on(MAIN)]
    return [
        (view.fields["trades"], view.fields["record_r"], view.fields["sequential_score"])
        for view in views
        if view.kind == "paper-run"
    ]


def test_a_second_and_third_round_score_the_same_paper_run(
    one_row_files: None,
    volume: Volume,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    into_paper(volume.home, volume, CLOSED_MONTH)
    span = CLOSED_MONTH + timedelta(days=20)
    volume.trade("old1", CLOSED_MONTH, CLOSED_MONTH + timedelta(hours=1), r="1.0")
    volume.trade("old2", CLOSED_MONTH, CLOSED_MONTH + timedelta(hours=2), r="1.0")
    volume.trade("span", span, OPEN_MONTH + timedelta(hours=1), r="1.0")
    opened: list[str] = []
    read_bytes = Path.read_bytes

    def counted(path: Path) -> bytes:
        if path.parent.name.startswith("journal-unit.trade."):
            opened.append(path.name)
        return read_bytes(path)

    with Store.open(tmp_path / "library", redactor=redact) as store:
        now = [OPEN_MONTH + timedelta(days=10)]
        job = Records(
            harvester(volume.home),
            Cadence,
            clock=lambda: now[0],
            projection=Projection(store, volume.home / "records"),
            store=store,
        )
        first = job.round()
        after_first = paper_scores(store)
        volume.trade("new", OPEN_MONTH + timedelta(hours=2), OPEN_MONTH + timedelta(hours=3), r="1.0")
        now[0] += timedelta(hours=1)
        monkeypatch.setattr(Path, "read_bytes", counted)
        second = job.round()
        monkeypatch.undo()
        after_second = paper_scores(store)
        volume.signal(OPEN_MONTH + timedelta(hours=4), "later")
        now[0] += timedelta(hours=1)
        third = job.round()
        after_third = paper_scores(store)

    open_key = f"journal-unit/dummy/trade/paper.this-pc/{month(OPEN_MONTH)}"
    assert (first.trades, first.paper_runs, first.refusals) == (3, 1, ())
    assert after_first == [(3, "3.0", "1.323379")]
    assert [text for text in second.committed if "/trade/" in text] == [open_key]
    assert (second.trades, second.paper_runs, second.refusals) == (1, 1, ())
    assert after_second == [(4, "4.0", "1.464255")]
    assert (third.trades, third.paper_runs, third.refusals) == (0, 0, ())
    assert after_third == [(4, "4.0", "1.464255")]
    assert opened == ["000002.jsonl", "000003.jsonl"]


def test_a_pulled_trade_lands_a_library_item(tmp_path: Path, far: Far) -> None:
    closed = CLOSED[-1] + timedelta(hours=9)
    written = RunJournal.open_live(
        far.root / "apps" / "trading-node" / "data" / "journal",
        COMPILED,
        scope_id="dep-1",
        world=JournalWorld.PAPER,
        machine=FAR,
        role="node",
        build="b",
        boot_epoch_id="b1",
        account="demo-1",
    )
    assert not is_refusal(written)
    written.value.at(Instant(int(closed.timestamp()) * 1_000_000_000))
    written.value.append(
        UnitTrade(
            "t1",
            "fx.eurusd",
            Side.LONG,
            Instant(int(CLOSED[-1].timestamp()) * 1_000_000_000),
            Instant(int(closed.timestamp()) * 1_000_000_000),
            Decimal("1.08000"),
            Decimal("1.08300"),
            Decimal("1.07900"),
            Decimal("0.10"),
            FillKind.CLOSE,
            Decimal("30.00"),
            Decimal("1.5"),
        )
    )
    written.value.close()
    Harvester(
        lambda: (far.root / "apps" / "trading-node" / "data" / "journal",),
        far.door,
        far.root / "records",
        journals_open=False,
    ).round(NOW, Cadence())
    records = tmp_path / "pc" / "records"
    now = [NOW]
    with Store.open(tmp_path / "library", redactor=redact) as store:
        job = Records(
            Harvester(lambda: (), pc_door(tmp_path), records, journals_open=True),
            Cadence,
            clock=lambda: now[0],
            projection=Projection(store, records),
            store=store,
            pull=pull(tmp_path, far),
        )
        first = job.round()
        now[0] = NOW + timedelta(seconds=300)
        again = job.round()
        views = [store.get(OPERATOR, object_id) for _item, object_id in store.heads_on(MAIN)]

    trades = [view.fields for view in views if view.kind == "trade"]
    papers = [view.fields for view in views if view.kind == "paper-run"]
    assert (first.trades, first.paper_runs, again.trades, again.paper_runs) == (1, 1, 0, 0)
    assert [(t["account"], t["machine"], t["net_result"], t["world"]) for t in trades] == [
        ("demo-1", FAR, 3000, "paper")
    ]
    assert [(p["node"], p["trades"], p["record_r"]) for p in papers] == [(FAR, 1, "1.5")]


def test_a_key_whose_projection_failed_is_told_again(
    volume: Volume, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    volume.trade("t1", CLOSED_MONTH, CLOSED_MONTH + timedelta(hours=1), r="1.0")
    with Store.open(tmp_path / "library", redactor=redact) as store:
        now = [OPEN_MONTH + timedelta(days=10)]
        job = Records(
            harvester(volume.home),
            Cadence,
            clock=lambda: now[0],
            projection=Projection(store, volume.home / "records"),
            store=store,
        )
        real_put = store.put

        def refused(who: Principal, draft: Draft, **kwargs: Any) -> object:
            if draft.kind in ("trade", "paper-run"):
                raise LibraryRefused("busy", "the Library refused this write")
            return real_put(who, draft, **kwargs)

        monkeypatch.setattr(store, "put", refused)
        cut = job.round()
        monkeypatch.setattr(store, "put", real_put)
        now[0] += timedelta(hours=1)
        told_again = job.round()
        now[0] += timedelta(hours=1)
        after = job.round()
        scores = paper_scores(store)

    assert (cut.trades, cut.paper_runs) == (0, 0)
    assert (told_again.partitions, told_again.trades, told_again.paper_runs) == (0, 1, 1)
    assert (after.trades, after.paper_runs) == (0, 0)
    assert scores == [(1, "1.0", "1.093750")]
