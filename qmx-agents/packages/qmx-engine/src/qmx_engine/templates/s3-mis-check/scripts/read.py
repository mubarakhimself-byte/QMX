"""What the MIS said about each market over the day, read by script before any agent looks. Zero
tokens.

Inputs, all optional: `day` (YYYY-MM-DD, UTC; the day before the run's clock by default), `days`
(how many days up to and including `day` to check; the card's default is 1), `readings` (the
reading ids to check; the card's default is the MIS's default packs) and `markets` (market ids;
every market the MIS read by default).

It reads the MIS's reading history through `readings_query`, the one door to it, whose holdout
refuses a held-out window by name: a refused reading is listed under `refused`, never read around.
Per market and reading it prints how many rows were published, the words by count, the healths by
count, and every change point: the first row and each row whose word differs from the one before,
with its time. The agent reads the market its own way beside these change points. It lands the
summary as one `mis-check` artifact. A day with no reading history is quiet and asks no agent.
"""

import importlib.util
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

asked = door.settings(json.load(sys.stdin).get("in"))
day, last = door.day_window(asked.get("day"))
first = datetime.fromisoformat(last["start"].replace("Z", "+00:00"))
window = {"start": door.iso(first - timedelta(days=int(asked["days"]) - 1)), "end": last["end"]}
qmx_home = door.home()
markets = asked.get("markets") or None
said, refused = {}, {}
for reading in asked["readings"]:
    found = door.readings(qmx_home, reading, window, markets=markets, source="mis")
    if "refused" in found:
        refused[reading] = found["refused"]
        continue
    for row in found["rows"]:
        said.setdefault((row["market_id"], reading), []).append(row)

checked = []
for (market, reading), rows in sorted(said.items()):
    changes, last = [], object()
    for row in rows:
        word = row.get("word", row.get("value"))
        if word != last:
            changes.append({"at": row["at"], "said": word, "health": row.get("health")})
            last = word
    checked.append(
        {
            "market": market,
            "reading": reading,
            "rows": len(rows),
            "words": dict(Counter(str(r.get("word", r.get("value"))) for r in rows)),
            "healths": dict(Counter(str(r.get("health")) for r in rows)),
            "changes": changes,
        }
    )

findings = {"day": day, "window": window, "checked": checked, "refused": refused}
note = None
if not checked:
    why = "; ".join(f"{r}: {w}" for r, w in sorted(refused.items())) or "nothing is recorded"
    note = {
        "title": f"MIS check for {day}: no reading history to check",
        "text": f"No MIS reading history was read for {day} (UTC). {why}.",
        "receipts": ["read"],
    }
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "findings.json").write_text(json.dumps(findings, sort_keys=True), encoding="utf-8")
print(
    json.dumps(
        {
            "findings": findings,
            "quiet": not checked,
            "note": note,
            "note_kind": "disagreement",
            "about": [],
            "window": window,
            "cards": [],
            "library": [
                {
                    "op": "put_artifact",
                    "type": "mis-check",
                    "body": "library/findings.json",
                    "metadata": findings,
                    "intent_key": f"mis-check|{day}",
                }
            ],
        }
    )
)
