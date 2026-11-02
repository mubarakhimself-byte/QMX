"""The week's evidence, read from the engine's own service and ledger, never from the Library: every
run started in the last seven days (this review's own run left out) with its status, its tokens and
each failed step or failed check, and every open inbox item. A parked run is one whose status says
so. A run started with `{"fixture": true}` reads `fixtures/week.json`, a synthetic week, instead.

Beside the runs it reads the week's market almanac from the journals, through the same doors the
slow lane reads (`scripts/door.py`), in the fixture week too: per market, the units' trades and
R by UTC weekday from the unit journal's `digest` view, and how often each MIS reading said each
word, from its reading history through `readings_query`, whose holdout refuses a held-out window
by name. Every number in it is made here, so it needs no model.

The run context names this run (`QMX_RUN_ID`), and the home is found from the run's shared zone
(`QMX_WORK_SHARED`)."""

import importlib.util
import json
import os
import sys
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from qmx_engine.ledger.inbox_table import InboxTable, inbox_path
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.clock import WallClock
from qmx_engine.service.inbox import Inbox
from qmx_engine.service.runs import status_of
from qmx_engine.trace_export import totals
from qmx_engine.workers.zones import home_of

DAYS = 7
MESSAGE_CHARS = 200
READINGS = ("efficiency-ratio", "variance-ratio", "hurst-exponent", "cusum-change-point")

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)


def almanac(qmx_home, now):
    """The week per market: the units' trades and R by UTC weekday, and the MIS's words."""
    window = {"start": door.iso(now - timedelta(days=DAYS)), "end": door.iso(now)}
    markets = {}
    for row in door.journal(qmx_home, stream="unit", window=window, view="digest")["rows"]:
        found = markets.setdefault(row["market_id"], {"trades": 0, "r": Decimal(0), "days": {}})
        weekday = date.fromisoformat(row["day"]).strftime("%A")
        day = found["days"].setdefault(weekday, {"trades": 0, "r": Decimal(0)})
        for into in (found, day):
            into["trades"] += row["trades"]
            into["r"] += Decimal(row["r"])
    words, refused = {}, {}
    for reading in READINGS:
        read = door.readings(qmx_home, reading, window, source="mis")
        if "refused" in read:
            refused[reading] = read["refused"]
            continue
        for row in read["rows"]:
            said = words.setdefault(row["market_id"], {}).setdefault(reading, Counter())
            said[str(row.get("word", row.get("value")))] += 1
    book = {}
    for market in sorted(set(markets) | set(words)):
        found = markets.get(market, {"trades": 0, "r": Decimal(0), "days": {}})
        book[market] = {
            "trades": found["trades"],
            "r": str(found["r"]),
            "days": {
                d: {"trades": v["trades"], "r": str(v["r"])} for d, v in found["days"].items()
            },
            "words": {r: dict(c) for r, c in sorted(words.get(market, {}).items())},
        }
    return {"window": window, "markets": book, "readings_refused": refused}


given = json.load(sys.stdin).get("in") or {}
home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
now = door.now()
if given.get("fixture"):
    found = json.loads((Path(__file__).parents[1] / "fixtures" / "week.json").read_text("utf-8"))
    book = almanac(home, now)
    print(json.dumps(found["week"] | {"source": "fixture", "almanac": book}))
    raise SystemExit(0)

own = os.environ["QMX_RUN_ID"]
since = (now - timedelta(days=DAYS)).isoformat()
runs, parked, failures = [], [], []
with Reader.open(home) as reader:
    started = reader.connection.execute(
        "SELECT run_id, min(at) FROM events WHERE kind = 'run_created' GROUP BY run_id ORDER BY 2"
    ).fetchall()
    for run_id, at in started:
        if at < since or run_id == own:
            continue
        events = reader.events(run_id)
        state = status_of(events)
        workflow = str(events[0].data.get("workflow_id"))
        mode = str(events[0].data.get("mode"))
        for event in events:
            data = event.data
            if event.kind == "node_failed" or data.get("verdict") == "fail":
                failures.append(
                    {
                        "run_id": run_id,
                        "workflow": workflow,
                        "node_id": data.get("node_id"),
                        "signature": data.get("signature") or f"check {data.get('node_id')}",
                        "message": str(data.get("message") or json.dumps(data.get("outputs")))[
                            :MESSAGE_CHARS
                        ],
                    }
                )
        summed = totals(events, reader.spans(run_id))
        runs.append(
            {
                "run_id": run_id,
                "workflow": workflow,
                "mode": mode,
                "started": at,
                "status": state.status,
                "reason": state.reason,
                "tokens": summed["tokens"],
            }
        )
        if state.reason == "parked":
            why = (state.detail or "")[:MESSAGE_CHARS]
            parked.append({"run_id": run_id, "workflow": workflow, "why": why})
inbox = []
if inbox_path(home).exists():
    with InboxTable.open(home) as table:
        for item in Inbox(table, WallClock()).list(open_only=True):
            inbox.append(
                {
                    "run_id": item.run_id,
                    "category": item.category.value,
                    "title": item.title,
                    "cause": item.cause[:MESSAGE_CHARS],
                }
            )
print(
    json.dumps(
        {
            "from": since,
            "to": now.isoformat(),
            "runs": runs,
            "parked": parked,
            "failures": failures,
            "inbox": inbox,
            "source": "engine",
            "almanac": almanac(home, now),
        }
    )
)
