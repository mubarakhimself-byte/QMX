"""E69: a run whose home died is adopted on another machine (AD-7, ruling 117).

Three lanes, each on a real `qmx_hub` over a real socket:

- `e69`, the proving lane. The PC runs a workflow to a hold, and its ledger is copied aside and
  deleted mid-run, which is the state a crashed home leaves. An adoption is refused while the PC's
  heartbeat is fresh. Aged past the window the same adoption succeeds on Contabo, the node that
  already finished is never started again, the run finishes there, and the PC restarted on its old
  ledger marks its copy moved and refuses to resume it.
- `race`. Two machines ask for the same run at once; exactly one wins the claim.
- `work`. A PC node commits files into its own `work/` zone. Zones do not travel, so that node runs
  again on Contabo and commits again.

Each lane writes its own `<evidence>/owner-<slug>.log` and exits 1 when a check failed.

    uv run --no-sync --project qmx-agents python scripts/live/server/e69_adopt.py --lane e69
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import statistics
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from collections.abc import Mapping
from typing import Final, cast

from pydantic import JsonValue

from qmx_engine.definition.validate import checked
from qmx_engine.heartbeat import Heartbeat
from qmx_engine.ledger import mirror, redact
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.mirror import HubJournals, MirrorRefused, post_json
from qmx_engine.ledger.store import Reader, ledger_path
from qmx_engine.runner import Outcome, Refused as EngineRefused
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.service.context import Refused as ServiceRefused
from qmx_engine.service.runs import RunView, status_of
from qmx_hub.server import Hub, serve
from qmx_library.store import Store

KEY = "pairing-key-of-this-lane"  # noqa: S105 (a lane-made key, never the ship's)
HOLD_S: Final = 1
PLAIN = "import json\nprint(json.dumps('done'))\n"
SAVE = (
    "import json\n"
    "from pathlib import Path\n"
    "Path('out').mkdir(exist_ok=True)\n"
    "Path('out', 'saved.txt').write_text('kept')\n"
    "print(json.dumps('saved'))\n"
)


class Lane:
    """One run of one lane: its own log, its pass lines, and the mirror times it measured."""

    def __init__(self, evidence: Path, lane: str) -> None:
        self.lane = lane
        self.path = evidence / f"owner-{lane}.log"
        self.log = self.path.open("w", encoding="utf-8", buffering=1)
        self.checked: list[tuple[bool, str]] = []
        self.times: list[float] = []

    def say(self, line: str) -> None:
        print(line)
        self.log.write(line + "\n")

    def check(self, ok: bool, line: str) -> None:
        self.checked.append((ok, line))
        self.say(f"{'PASS' if ok else 'FAIL'} {line}")

    def done(self) -> int:
        good = sum(1 for ok, _ in self.checked if ok)
        self.say(f"E69 {self.lane} {good}/{len(self.checked)} checks passed")
        self.log.close()
        return 0 if all(ok for ok, _ in self.checked) else 1


def beat(host: str, at: datetime) -> dict[str, JsonValue]:
    row = Heartbeat(
        subject="host",
        id=host,
        at=at.isoformat(),
        cpu_seconds=0.0,
        rss_bytes=0,
        machine_minutes=0.0,
        qmx_version="0.1.0",
        kinds_digest="lane",
        paused=False,
    )
    return row.model_dump(mode="json")


def hear(url: str, host: str, at: datetime) -> None:
    """One host heartbeat row on the Hub's own route, as the host's own loop sends it."""
    post_json(
        f"{url}/v1/heartbeat",
        {"heartbeat": cast("Mapping[str, JsonValue]", beat(host, at))},
        {"Authorization": f"Bearer {KEY}"},
    )


def held_at(url: str, run_id: str) -> JsonValue:
    """The journal the Hub holds for `run_id`, read over the wire."""
    return post_json(
        f"{url}/v1/op/journal_get",
        {"who": "hub", "args": {"run_id": run_id}},
        {"Authorization": f"Bearer {KEY}"},
    )


def node(name: str, kind: str, **parameters: JsonValue) -> dict[str, JsonValue]:
    return {"id": name, "name": name, "type": kind, "typeVersion": 1, "parameters": parameters}


def folder(
    root: Path, nodes: list[dict[str, JsonValue]], edges: dict[str, str], scripts: dict[str, str]
) -> Path:
    """A workflow folder; `edges` maps a source node to its one target on `main`."""
    root.mkdir(parents=True, exist_ok=True)
    document: dict[str, JsonValue] = {
        "schema": "qmx.workflow/1",
        "id": root.name,
        "name": root.name,
        "nodes": nodes,
        "connections": {
            source: {"main": [[{"node": target, "port": "in", "map": "one"}]]}
            for source, target in edges.items()
        },
    }
    (root / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    (root / "scripts").mkdir(exist_ok=True)
    for name, text in scripts.items():
        (root / "scripts" / f"{name}.py").write_text(text, encoding="utf-8")
    return root


def workflow(root: Path, middle: dict[str, JsonValue], script: str, text: str) -> Path:
    """`start -> middle -> hold`: the run is cut while the hold is still in front of it."""
    return folder(
        root,
        [node("start", "trigger"), middle, node("hold", "wait", seconds=HOLD_S)],
        {"start": str(middle["id"]), str(middle["id"]): "hold"},
        {script: text},
    )


def events_of(home: Path, run_id: str) -> list[Event]:
    with Reader.open(home) as reader:
        return reader.events(run_id)


def after(events: list[Event], kind: str) -> list[dict[str, JsonValue]]:
    """The events of `kind` written after the adoption's own `run_resumed` line."""
    line = next(
        i
        for i, event in enumerate(events)
        if event.kind == "run_resumed" and event.data.get("reason") == "adopted"
    )
    return [dict(e.data) for e in events[line + 1 :] if e.kind == kind]


def start_on(home: Path, root: Path, name: str, client: HubJournals) -> Outcome:
    found = checked(root)
    assert not isinstance(found, list), found
    mirror.attach(client)
    try:
        with EngineService.open(home, name=name) as service:
            return asyncio.run(service.ctx.engine.start(root, found[1], mode="test", inputs=None))
    finally:
        mirror.attach(None)


def adopt_on(home: Path, name: str, url: str, run_id: str, lane: Lane) -> RunView:
    client = HubJournals(url, KEY, home=name)
    mirror.attach(client)
    try:
        with EngineService.open(home, name=name) as service:
            view = asyncio.run(service.runs.adopt(run_id, caller=OPERATOR))
            if view.status == "waiting":
                time.sleep(HOLD_S + 0.2)
                asyncio.run(wake(service, run_id))
                view = service.runs.get(run_id)
            return view
    finally:
        mirror.attach(None)
        lane.times += client.times


async def wake(service: EngineService, run_id: str) -> Outcome:
    """The ticker's own call for a held run whose `resume_at` has come (AD-10), made directly."""
    with Reader.open(service.ctx.home) as reader:
        events = reader.events(run_id)
    reset = next(
        (
            str(e.data["resume_at"])
            for e in reversed(events)
            if e.kind == "node_waiting" and e.data.get("resume_at") is not None
        ),
        "",
    )
    outcome = await service.ctx.engine.resume(run_id, reason="wake", woke=reset)
    await service.ctx.engine.settle()
    return outcome


def dead_home(home: Path) -> Path:
    """Copy the home's ledger aside and delete it: the state a crashed home leaves behind."""
    live = ledger_path(home)
    kept = live.with_name(live.name + ".crashed")
    shutil.copy2(live, kept)
    for suffix in ("", "-wal", "-shm"):
        Path(str(live) + suffix).unlink(missing_ok=True)
    return kept


def revive(home: Path, kept: Path) -> None:
    """Put the dead home's own ledger back, as a machine that survived the crash has it."""
    shutil.copy2(kept, ledger_path(home))
    kept.unlink(missing_ok=True)


def lane_e69(lane: Lane, root: Path, url: str) -> None:
    pc, contabo = root / "pc", root / "contabo"
    workflow(root / "wf", node("work", "script", script="scripts/work.py"), "work", PLAIN)
    lane.say("the PC's engine home and the Hub are processes on this machine")
    pc_client = HubJournals(url, KEY, home="pc")
    mirror.attach(pc_client)
    found = checked(root / "wf")
    assert not isinstance(found, list), found
    with EngineService.open(pc, name="pc") as service:
        run_id = asyncio.run(
            service.ctx.engine.start(root / "wf", found[1], mode="test", inputs=None)
        ).run_id
    mirror.attach(None)
    lane.times += pc_client.times
    outcome = status_of(events_of(pc, run_id))
    lane.check(outcome.status == "waiting", f"the run is cut while its last node holds it ({outcome.status})")
    ends = len([e for e in events_of(pc, run_id) if e.kind == "node_finished"])
    lane.check(ends == 2, f"two node ends are in the PC's ledger ({ends})")
    lane.check(
        len(pc_client.times) == 2 and held_at(url, run_id) is not None,
        f"the Hub holds the journal the mirror pushed ({len(pc_client.times)} pushes)",
    )

    kept = dead_home(pc)
    lane.check(
        not ledger_path(pc).exists(), "the PC's ledger file is gone, as a dead home's would be"
    )
    hear(url, "pc", datetime.now(UTC))
    mirror.attach(HubJournals(url, KEY, home="contabo"))
    try:
        with EngineService.open(contabo, name="contabo") as probe:
            asyncio.run(probe.runs.adopt(run_id, caller=OPERATOR))
    except ServiceRefused as refused:
        lane.check(
            refused.code == "home_fresh",
            f"the adoption is refused while the home's heartbeat is fresh ({refused.code})",
        )
    finally:
        mirror.attach(None)

    hear(url, "pc", datetime.now(UTC) - timedelta(minutes=10))

    view = adopt_on(contabo, "contabo", url, run_id, lane)
    events = events_of(contabo, run_id)
    lane.check(view.status == "passed", f"the run finishes on Contabo ({view.status})")
    started = [line.get("node_id") for line in after(events, "node_started")]
    lane.check(
        "work" not in started,
        f"the node that already finished is never started again ({started})",
    )
    adopted = [e.data for e in events if e.kind == "run_resumed" and e.data.get("reason") == "adopted"]
    lane.check(
        bool(adopted) and (adopted[0].get("from"), adopted[0].get("to")) == ("pc", "contabo"),
        f"Contabo's ledger records where the run came from and went ({adopted[:1]})",
    )

    revive(pc, kept)
    mirror.attach(HubJournals(url, KEY, home="pc"))
    try:
        with EngineService.open(pc, name="pc") as service:
            try:
                asyncio.run(service.ctx.engine.resume(run_id))
            except EngineRefused:
                lane.check(True, "the old home refuses to resume its copy")
            else:
                lane.check(False, "the old home refuses to resume its copy")
    finally:
        mirror.attach(None)
    here = events_of(pc, run_id)
    moved = [e.data for e in here if e.kind == "run_cancelled"]
    state = status_of(here)
    lane.check(
        moved == [{"reason": "moved", "to": "contabo"}],
        f"the old home marks its copy moved ({moved})",
    )
    lane.check(
        (state.status, state.reason) == ("stopped", "moved"),
        f"the old home's copy reads stopped, moved ({state.status}, {state.reason})",
    )
    perf(lane)


def lane_race(lane: Lane, root: Path, url: str) -> None:
    pc, contabo, qmb = root / "pc", root / "contabo", root / "qmb"
    workflow(root / "wf", node("work", "script", script="scripts/work.py"), "work", PLAIN)
    outcome = start_on(pc, root / "wf", "pc", HubJournals(url, KEY, home="pc"))
    run_id = outcome.run_id
    hear(url, "pc", datetime.now(UTC) - timedelta(minutes=10))

    lane.say("two machines ask the Hub for the same run at once")

    clients = {name: HubJournals(url, KEY, home=name) for name in ("contabo", "qmb")}
    winners: list[str] = []
    for name, client in clients.items():
        try:
            client.adopt(run_id)
        except MirrorRefused as refused:
            lane.check(
                refused.code == "claim_held",
                f"{name} loses the claim while another home holds it ({refused.code})",
            )
        else:
            winners.append(name)
    lane.check(winners == ["contabo"], f"exactly one machine wins the claim ({winners})")

    view = adopt_on(contabo, "contabo", url, run_id, lane)
    lane.check(view.status == "passed", f"the winner finishes the run ({view.status})")

    mirror.attach(clients["qmb"])
    try:
        with EngineService.open(qmb, name="qmb") as service:
            try:
                asyncio.run(service.runs.adopt(run_id, caller=OPERATOR))
            except ServiceRefused as refused:
                lane.check(
                    refused.code == "claim_held",
                    f"the loser's own adopt is refused by the Hub ({refused.code})",
                )
            else:
                lane.check(False, "the loser's own adopt is refused by the Hub")
    finally:
        mirror.attach(None)


def lane_work(lane: Lane, root: Path, url: str) -> None:
    pc, contabo = root / "pc", root / "contabo"
    saving = node("save", "script", script="scripts/save.py")
    saving["outputs"] = {"files": [{"path": "out/saved.txt"}]}
    workflow(root / "wf", saving, "save", SAVE)
    outcome = start_on(pc, root / "wf", "pc", HubJournals(url, KEY, home="pc"))
    run_id = outcome.run_id
    committed = [e.data for e in events_of(pc, run_id) if e.kind == "zone_committed"]
    lane.check(
        [line.get("paths") for line in committed] == [["out/saved.txt"]],
        f"the PC's node committed a file into its own zone ({committed})",
    )
    hear(url, "pc", datetime.now(UTC) - timedelta(minutes=10))


    view = adopt_on(contabo, "contabo", url, run_id, lane)
    events = events_of(contabo, run_id)
    lane.check(view.status == "passed", f"the adopted run finishes on Contabo ({view.status})")
    started = [line.get("node_id") for line in after(events, "node_started")]
    lane.check(
        started == ["save", "hold"],
        f"the node that committed files runs again on the new home ({started})",
    )
    lane.check(
        [line.get("paths") for line in after(events, "zone_committed")] == [["out/saved.txt"]],
        "it commits again into the new home's own zone",
    )
    saved = contabo.with_name(contabo.name + ".zones") / run_id / "work" / "out" / "saved.txt"
    lane.check(saved.read_text() == "kept", f"the committed file is here, made here ({saved})")


LANES = {"e69": lane_e69, "race": lane_race, "work": lane_work}


def perf(lane: Lane) -> None:
    if not lane.times:
        return
    ordered = sorted(lane.times)
    lane.say(
        "METRIC mirror time per node end, ms: "
        + json.dumps(
            {
                "node_ends": len(ordered),
                "mean": round(statistics.fmean(ordered), 2),
                "p95": round(ordered[int(0.95 * (len(ordered) - 1))], 2),
                "max": round(max(ordered), 2),
            },
            sort_keys=True,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="e69_adopt")
    parser.add_argument("--lane", choices=("e69", "race", "work"), default="e69")
    parser.add_argument("--root", type=Path, default=Path("D:/Temp/adopt-e69"))
    parser.add_argument("--evidence", type=Path, default=None)
    parser.add_argument("--hub-url", default=None, help="a Hub already running, instead of one here")
    parser.add_argument("--key-file", type=Path, default=None, help="that Hub's pairing key")
    args = parser.parse_args()
    evidence = args.evidence or Path(
        os.environ.get("QMA_EVIDENCE_DIR", "D:/QMX-worktrees/qma-ship/build/evidence/adopt")
    )
    evidence.mkdir(parents=True, exist_ok=True)
    root: Path = args.root / args.lane
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    lane = Lane(evidence, args.lane)
    try:
        if args.hub_url is not None:
            global KEY  # noqa: PLW0603 (the lane's own key, from the file it is told to read)
            KEY = (args.key_file or root / "pairing-key").read_text(encoding="utf-8").strip()
            lane.say(f"the Hub is a separate machine's process at {args.hub_url}")
            LANES[args.lane](lane, root, args.hub_url.rstrip("/"))
        else:
            store_root = root / "hub-store"
            store_root.mkdir(parents=True, exist_ok=True)
            home = root / "hub-home"
            home.mkdir(parents=True, exist_ok=True)
            with Store.open(store_root, redactor=redact, name="server") as store:
                hub = Hub(store, home=home)
                server = serve(hub, host="127.0.0.1", port=0, key=KEY)
                threading.Thread(target=server.serve_forever, daemon=True).start()
                url = f"http://127.0.0.1:{server.server_address[1]}"
                lane.say(f"the Hub serves {url} on this machine")
                try:
                    LANES[args.lane](lane, root, url)
                finally:
                    server.shutdown()
    finally:
        code = lane.done()
    return code


if __name__ == "__main__":
    raise SystemExit(main())



