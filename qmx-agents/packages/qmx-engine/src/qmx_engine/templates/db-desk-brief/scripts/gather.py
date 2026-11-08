"""The zero-token gather (cards T1, T2 and T10, steps 1 and 2): everything the desk brief may say,
read by script, never by a model.

The edition follows the clock: `morning` before 07:00 London, `end of day` from 17:00 New York,
`pre-session` otherwise. The calendar rows for the watchlist come from the free weekly calendar at
nfs.faireconomy.media (today's, and tomorrow's for the end of day). The latest live result of the
research desk (T4), the calendar watch (T3) and the paper scout (RS1) from the last 36 hours, and
the open inbox items, come from the engine's own ledger and inbox in the home this run lives in;
test runs are never read. The units' result over the last day comes from the unit journal through
`journal_query`, and the session conditions are the MIS's last words for each watchlist market
from its reading history through `readings_query`, whose holdout refuses a held-out window by
name. Account, cushion, open risk, positions and unit states are node facts: they read
`could not check: trading node` until the node's read operations reach This PC. Every calendar row
is outside text, so it carries the `qmx.marked/1` mark: the writer reads it as data, never as an
instruction.

A run started with `{"fixture": "busy"}` or `{"fixture": "quiet"}` replays the matching synthetic
day in `fixtures/`; the journals and reading history are still read from the run's own home. The
home is found from the run's shared zone (`QMX_WORK_SHARED`), the one place a script learns where
its run lives.
"""

import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

WATCHLIST = {"EURUSD": ("EUR", "USD"), "USDJPY": ("USD", "JPY")}
MARKETS = {"EURUSD": "fx.eurusd", "USDJPY": "fx.usdjpy"}
READINGS = ("efficiency-ratio", "variance-ratio", "hurst-exponent", "spread_state")
MARK = "qmx.marked/1"
NODE = "could not check: trading node"
NODE_FACTS = (
    "account_equity",
    "kill_line_cushion_r",
    "open_risk_r",
    "open_positions",
    "unit_states",
)
NOTHING = "nothing recorded"
FEED = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
IMPACT = {"High": "high", "Medium": "medium", "Low": "low"}
FRESH_HOURS = 36
WANTED = ("t4-research-desk-overnight", "t3-news-calendar-watch", "rs1-paper-scout")


def edition(now):
    if now.astimezone(ZoneInfo("America/New_York")).hour >= 17:
        return "end of day"
    if now.astimezone(ZoneInfo("Europe/London")).hour < 7:
        return "morning"
    return "pre-session"


def calendar(days):
    request = Request(FEED, headers={"User-Agent": "QMX desk brief"})
    with urlopen(request, timeout=60) as reply:  # noqa: S310
        week = json.loads(reply.read())
    currencies = {c for legs in WATCHLIST.values() for c in legs}
    rows = []
    for row in week:
        when = datetime.fromisoformat(row["date"]).astimezone(UTC)
        if when.date().isoformat() not in days or row["country"] not in currencies:
            continue
        rows.append(
            {
                "title": row["title"],
                "currency": row["country"],
                "date": when.date().isoformat(),
                "time_utc": f"{when:%H:%M}",
                "impact": IMPACT.get(row.get("impact"), "low"),
                "forecast": row.get("forecast") or None,
                "previous": row.get("previous") or None,
                "source": FEED,
            }
        )
    return rows


def overnight(home, now):
    """The units' result over the last day, per unit and market, from the unit journal."""
    window = {"start": door.iso(now - timedelta(days=1)), "end": door.iso(now)}
    answer = door.journal(home, stream="unit", window=window, view="digest")
    units = [
        {"unit": r["unit_id"], "market": r["market_id"], "trades": r["trades"], "r": r["r"]}
        for r in answer["rows"]
        if r["trades"]
    ]
    if not units:
        return NOTHING
    return {"units": units, "r": str(sum((Decimal(u["r"]) for u in units), Decimal(0)))}


def conditions(home, now, missing):
    """The MIS's last word of each reading for each watchlist market over the last day."""
    window = {"start": door.iso(now - timedelta(days=1)), "end": door.iso(now)}
    found = {}
    for reading in READINGS:
        read = door.readings(home, reading, window, markets=sorted(MARKETS.values()), source="mis")
        if "refused" in read:
            missing.append(f"reading history: {reading}: {read['refused']}")
            continue
        for row in read["rows"]:
            found.setdefault(row["market_id"], {})[reading] = row.get("word", row.get("value"))
    return dict(sorted(found.items())) or NOTHING


def latest_results(home, since):
    from qmx_engine.ledger.store import Reader  # noqa: PLC0415

    found = {}
    with Reader.open(home) as reader:
        started = reader.connection.execute(
            "SELECT run_id, min(at) FROM events WHERE kind = 'run_created' "
            "GROUP BY run_id ORDER BY 2 DESC"
        ).fetchall()
        for run_id, at in started:
            if at < since or len(found) == len(WANTED):
                break
            events = reader.events(run_id)
            workflow = events[0].data.get("workflow_id")
            if workflow not in WANTED or workflow in found or events[0].data.get("mode") == "test":
                continue
            for event in events:
                if event.kind == "node_finished" and event.data.get("node_id") == "deliver":
                    found[workflow] = (run_id, event.data["outputs"]["main"])
    return found


def open_decisions(home):
    from qmx_engine.ledger.inbox_table import InboxTable, inbox_path  # noqa: PLC0415
    from qmx_engine.ports.clock import WallClock  # noqa: PLC0415
    from qmx_engine.service.inbox import Inbox  # noqa: PLC0415

    if not inbox_path(home).exists():
        return []
    with InboxTable.open(home) as table:
        return [
            {
                "title": item.title,
                "cause": item.cause[:200],
                "run_id": item.run_id,
                "category": item.category.value,
            }
            for item in Inbox(table, WallClock()).list(open_only=True)
        ]


given = json.load(sys.stdin).get("in") or {}
fixture = given.get("fixture") if isinstance(given, dict) else None
missing = []
now = door.now()
home = door.home()
if fixture in ("busy", "quiet"):
    day = json.loads(
        (Path(__file__).parents[1] / "fixtures" / f"day-{fixture}.json").read_text("utf-8")
    )
    day.pop("note")
    source = "fixture"
else:
    day = {"date": now.date().isoformat(), "edition": edition(now)}
    days = {day["date"]}
    if day["edition"] == "end of day":
        days.add((now + timedelta(days=1)).date().isoformat())
    try:
        day["events"] = calendar(days)
    except Exception as error:
        day["events"] = []
        missing.append(f"calendar: {type(error).__name__}")
    results = latest_results(home, (now - timedelta(hours=FRESH_HOURS)).isoformat())
    desk_run, desk = results.get("t4-research-desk-overnight", (None, {}))
    day["desk"] = [
        {"section": name, "text": line["text"], "links": line["links"], "run_id": desk_run}
        for name in ("HIGH", "MEDIUM", "CALENDAR")
        for line in desk.get("sections", {}).get(name, [])
    ]
    day["alerts"] = results.get("t3-news-calendar-watch", (None, {}))[1].get("alerts", [])
    scout_run, note = results.get("rs1-paper-scout", (None, {}))
    day["research"] = [
        {"title": p["title"], "link": f"https://arxiv.org/abs/{p['paper_id']}", "run_id": scout_run}
        for p in note.get("papers", [])
    ]
    day["decisions"] = open_decisions(home)
    for workflow in WANTED:
        if workflow not in results:
            missing.append(f"{workflow}: no live result in the last {FRESH_HOURS} hours")
    source = "engine"

facts = dict.fromkeys(NODE_FACTS, NODE)
facts["overnight_pnl_r"] = overnight(home, now)
facts["session_conditions"] = conditions(home, now, missing)
day["events"] = [e | {"marked": MARK} for e in day["events"]]
notable = [e for e in day["events"] if e["impact"] != "low"]
quiet = not (notable or day["desk"] or day["alerts"] or day["research"] or day["decisions"])
print(
    json.dumps(
        day
        | {
            "watchlist": sorted(WATCHLIST),
            "node_facts": facts,
            "quiet": quiet,
            "could_not_check": missing,
            "source": source,
        }
    )
)
