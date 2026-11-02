"""The markets whose session opens soon, with today's reading words and each unit's record under
them. Zero tokens.

Inputs are the card's settings, each left out taking its `default` in `definition.json`:
`lead_minutes`, `calendars` (a market id's class, its first part such as `fx`, to the shipped
calendar it trades on), `day_start_utc`, `session_hours`, `record_days`, `readings`, and
optionally `markets` (read beside every market a unit traded over the record).

A market's next session starts at its calendar's next open while the calendar is shut, and at the
next `day_start_utc` while it is open (WF-04's named hour for markets that never close). The clock
is the run's own. The calendars are the shipped ones the `calendar-open` block reads, so no market's
hours are written here. Each market whose session starts within `lead_minutes` is read:

- today's words: the last word each reading said over the record, through `readings_query`, whose
  holdout refuses a held-out window by name;
- each unit's record on that market under those words: its closed trades over `record_days`
  through `journal_query`, each set beside the word each reading said last before it opened, and
  the trades and R earned under today's word, per reading.

A unit fits when its R under today's words, summed over the readings, is above zero. The
shortlist is every opening market with a fitting unit, the most fitting units first, then the
most R. Units trade their admitted markets on their own conditions whatever the shortlist says
(MIS-09): it is a read for him. A run with nothing on the shortlist is quiet and asks no model.
"""

import importlib.util
import json
import os
import sys
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from qmx_engine.triggers.preflight import shipped_calendars

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def ns_of(text):
    moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return (moment - EPOCH) // timedelta(microseconds=1) * 1_000


def session_start(calendar, at, day_start):
    if not calendar.open_at(at):
        return calendar.next_open(at)
    start = datetime.combine(at.date(), day_start, tzinfo=UTC)
    return start if start > at else start + timedelta(days=1)


asked = door.settings(json.load(sys.stdin).get("in"))
now = door.now()
record = {
    "start": door.iso(now - timedelta(days=int(asked["record_days"]))),
    "end": door.iso(now),
}
qmx_home = door.home()
try:
    trades = door.journal(qmx_home, stream="unit", window=record, filters={"kind": "trade"})
except ValueError as refusal:
    print(f"[QMX_FAILURE] {refusal}")
    raise SystemExit(0) from None

calendars = shipped_calendars()
day_start = time.fromisoformat(str(asked["day_start_utc"]))
lead = timedelta(minutes=int(asked["lead_minutes"]))
opening, unscheduled = [], []
for market in sorted(
    {row["market_id"] for row in trades["rows"]} | set(asked.get("markets") or [])
):
    ref = asked["calendars"].get(market.split(".")[0])
    calendar = calendars.get(ref) if ref else None
    if calendar is None:
        unscheduled.append({"market": market, "why": f"no shipped calendar is named for {market}"})
        continue
    start = session_start(calendar, now, day_start)
    if start is not None and now < start <= now + lead:
        opening.append((market, ref, start))

latest, history, refused = {}, {}, {}
for reading in asked["readings"] if opening else []:
    found = door.readings(
        qmx_home, reading, record, markets=[m for m, _, _ in opening], source="mis"
    )
    if "refused" in found:
        refused[reading] = found["refused"]
        continue
    for row in found["rows"]:
        word = str(row.get("word", row.get("value")))
        latest[(row["market_id"], reading)] = word
        history.setdefault((row["market_id"], reading), []).append((ns_of(row["at"]), word))

rows = []
for market, ref, start in opening:
    words = {r: latest[(market, r)] for r in asked["readings"] if (market, r) in latest}
    units = {}
    for row in trades["rows"]:
        if row["market_id"] != market:
            continue
        opened = row["body"].get("opened_at")
        at = opened if isinstance(opened, int) else ns_of(row["at"])
        r = Decimal(str(row["body"].get("r", "0")))
        unit = units.setdefault(row["unit_id"], {})
        for reading, today in words.items():
            said = [w for t, w in history.get((market, reading), []) if t <= at]
            if said and said[-1] == today:
                earned = unit.setdefault(reading, [0, Decimal(0)])
                earned[0] += 1
                earned[1] += r
    fitting = []
    for unit, earned in sorted(units.items()):
        total = sum((r for _, r in earned.values()), Decimal(0))
        if total > 0:
            fitting.append(
                {
                    "unit": unit,
                    "under_todays_words": {
                        reading: {"trades": n, "r": str(r)} for reading, (n, r) in earned.items()
                    },
                    "r": str(total),
                }
            )
    if fitting:
        horizon = start + timedelta(hours=int(asked["session_hours"]))
        rows.append(
            {
                "market": market,
                "calendar": ref,
                "session_starts": door.iso(start),
                "horizon": door.iso(horizon),
                "words": words,
                "fitting_units": fitting,
                "fits": len(fitting),
                "r": str(sum((Decimal(u["r"]) for u in fitting), Decimal(0))),
            }
        )
rows.sort(key=lambda row: (-row["fits"], -Decimal(row["r"]), row["market"]))

findings = {
    "at": door.iso(now),
    "settings": {
        name: asked[name]
        for name in ("lead_minutes", "day_start_utc", "session_hours", "record_days")
    },
    "opening": [m for m, _, _ in opening],
    "shortlist": rows,
    "unscheduled": unscheduled,
    "readings_refused": refused,
}
note = None
if not rows:
    opens = ", ".join(findings["opening"]) or "no market"
    note = {
        "title": f"No shortlist at {door.iso(now)}",
        "text": f"Opening within the lead: {opens}. No unit's record fits today's words on an "
        "opening market, so nothing is shortlisted.",
        "receipts": ["read"],
    }
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "findings.json").write_text(json.dumps(findings, sort_keys=True), encoding="utf-8")
print(
    json.dumps(
        {
            "findings": findings,
            "quiet": not rows,
            "note": note,
            "note_kind": "proposal",
            "about": [{"rel": "market", "ref": row["market"]} for row in rows],
            "window": record,
            "cards": [],
            "library": [
                {
                    "op": "put_artifact",
                    "type": "shortlist",
                    "body": "library/findings.json",
                    "metadata": findings,
                    "intent_key": f"shortlist|{door.iso(now)}",
                }
            ],
        }
    )
)
