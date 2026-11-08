"""Hands the writer's dated calls to the `forecast` block. Zero tokens.

Its inputs are the read step's output and the `receipts-grader` child's output, whose note
carries the writer's `forecasts`. A call is kept only for a shortlisted market, and its `horizon`
is that market's own from the read step, never the writer's, so every call is for the session the
shortlist read. The block then lands each one dated by the run's clock, keeps only the `forecast`
kind's fields, and refuses a call that could not be scored (WF-11). The author is this template.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
read = next(r for r in rows if "findings" in r)
note = next(
    r["outputs"]["deliver"]["main"]["note"]
    for r in rows
    if isinstance(r.get("outputs"), dict) and "deliver" in r["outputs"]
)
horizons = {row["market"]: row["horizon"] for row in read["findings"]["shortlist"]}
calls = [
    {**call, "horizon": horizons[call.get("market")]}
    for call in note.get("forecasts", [])
    if call.get("market") in horizons
]
print(json.dumps({"forecasts": calls, "author": "agent:s1-pre-session-shortlist"}))
