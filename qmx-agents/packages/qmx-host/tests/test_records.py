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
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import JsonValue
from qmf.core import is_refusal
from qmf.data.series import SeriesKey
from qmf.data.store.engines.typed import TypedWriter
from qmx_apps.supervisor import Supervisor
from qmx_engine.ledger import redact
from qmx_library.principal import MAIN, Principal
from qmx_library.store import Store
from test_backups_service import Clock as BackupClock
from test_backups_service import folder, service

from qmx_host.host_route import ANSWERS, Answering, Answers, host_router
from qmx_host.maintenance import maintenance_router
from qmx_host.market_data import MarketDoor, Placement
from qmx_host.node_link import NodeLink, Place, Unreachable
from qmx_host.records import Cadence, Fetch, Harvester, Pull, Records

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


def commit(door: MarketDoor, root: Path, moment: datetime, rows: int, *, times: int = 1) -> None:
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
        receipts = door.commit([target], staging=staging, born_on=Placement.NODE)
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
        root, here=FAR, apps=cast("Supervisor", None), settings=dict, key=lambda: pairing
    )

    async def beats() -> Mapping[str, object]:
        return {}

    answering = Answering(
        link,
        key=lambda: pairing,
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


def pull(tmp_path: Path, far: Far, *, down: bool = False, fetch: Fetch | None = None) -> Pull:
    places = {FAR: Place(FAR, f"http://{FAR}", ())}
    if down:
        places[DOWN] = Place(DOWN, f"http://{DOWN}", ())
    return Pull(
        pc_door(tmp_path),
        tmp_path / "pc" / "records",
        here="pc",
        places=lambda: places,
        key=lambda: far.key,
        post=far.post,
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
