"""How much of the live day QMB's replay decided alike, and a proposal when too little did. Zero
tokens.

Its inputs are the route step's output and, when QMB was asked, what its `replay_check` job
answered: the result's `measures`, `matched` (decisions live and replay took alike) and `differs`
(decisions only one of them took, or took differently). The match is `matched` over both, to two
places. Under `warn_below` (a card setting the route step hands on, 0.80 by default) the unit
gets one `bench` card for his click, since a live unit that its own replay cannot reproduce is
trading on something the test never saw. A replay that did not finish is reported with its reason
and proposes nothing.

The script writes the note itself; no model is asked. It lands the diff as one `replay-diff`
artifact and prints what the land step lands.
"""

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

CENT = Decimal("0.01")

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
route = next(r for r in rows if "replay_check" in r)
replayed = next((r for r in rows if isinstance(r.get("result"), dict)), None)
warn = Decimal(str(route["warn_below"]))
unit, day = route["unit"], route["day"]
diff = {"unit": unit, "day": day, "live_rows": route["live_rows"], "warn_below": str(warn)}
note, cards = route["note"], []
if replayed is not None:
    data = replayed["result"].get("data", {})
    measures = data.get("measures", {})
    diff |= {"qmb_run": data.get("run_id"), "status": data.get("status")}
    if data.get("status") != "finished":
        why = data.get("reason") or "no reason given"
        note = {
            "title": f"The replay of {unit} on {day} did not finish",
            "text": f"QMB's replay of {unit}'s live day {day} ended {data.get('status')}: {why}. "
            "Nothing is proposed.",
            "receipts": ["diff"],
        }
    else:
        matched, differs = int(measures["matched"]), int(measures["differs"])
        rate = (
            (Decimal(matched) / (matched + differs)).quantize(CENT) if matched + differs else None
        )
        diff |= {
            "matched": matched,
            "differs": differs,
            "match": None if rate is None else str(rate),
        }
        said = "had no decisions to compare" if rate is None else f"matched {rate}"
        note = {
            "title": f"Live-day replay of {unit} on {day}",
            "text": f"QMB replayed {unit}'s live day {day} from the bars the node recorded: "
            f"{matched} decisions alike and {differs} not, so the replay {said}.",
            "receipts": ["diff"],
        }
        if rate is not None and rate < warn:
            why = f"its replay of {day} matched {rate}, under {warn}"
            cards.append({"subject": unit, "ask": "bench", "why": why})
            note["text"] += f" That is under {warn}, so one bench card waits for his click."
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "diff.json").write_text(json.dumps(diff, sort_keys=True), encoding="utf-8")
print(
    json.dumps(
        {
            "diff": diff,
            "note": note,
            "note_kind": "analysis",
            "about": route["about"],
            "window": route["window"],
            "cards": cards,
            "library": [
                {
                    "op": "put_artifact",
                    "type": "replay-diff",
                    "body": "library/diff.json",
                    "metadata": diff,
                    "intent_key": f"replay-diff|{unit}|{day}",
                }
            ],
        }
    )
)
