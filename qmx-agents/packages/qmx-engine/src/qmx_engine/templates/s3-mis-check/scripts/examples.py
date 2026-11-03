"""Keeps each disagreement the agent named that points at a change point the read step printed.
Zero tokens.

Its inputs are the read step's output and, when the agent wrote, the `receipts-grader` child's
output, whose note carries the agent's `disagreements`. A disagreement names its `market`,
`reading` and `at` (the change point's time, copied exactly), what the MIS said, what the agent
reads and why. One that names no change point the read step printed is dropped and listed under
`dropped`, so no example points at a row the MIS never published. One whose `agent_reads` or `why`
holds a digit fails the step: the agent read bars through its tools, which leave no receipt, so it
says what it sees in words and every number in what lands comes from a script.

It prints the read step's output with `about` set to one link per kept example
(`rel: reading`, `ref: <reading>|<market>|<at>`), the kept examples under `examples`, and
`note_title`, which names the day and counts the kept examples, for the land step. The count is
this step's, so no model wrote it. On a quiet day it hands the read step's output on unchanged.
"""

import json
import sys

FAILURE = "[QMX_FAILURE]"

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
read = next(r for r in rows if "note_kind" in r)
graded = next(
    (
        r["outputs"]["deliver"]["main"]["note"]
        for r in rows
        if isinstance(r.get("outputs"), dict) and "deliver" in r["outputs"]
    ),
    None,
)
points = {
    (c["market"], c["reading"], change["at"]): change["said"]
    for c in read["findings"]["checked"]
    for change in c["changes"]
}
kept, dropped = [], []
for place, example in enumerate((graded or {}).get("disagreements", []), start=1):
    key = (example.get("market"), example.get("reading"), example.get("at"))
    words = f"{example.get('agent_reads', '')} {example.get('why', '')}"
    if any(ch.isdigit() for ch in words):
        print(f"{FAILURE} disagreement {place} states a number no step printed: say it in words")
        raise SystemExit(0)
    if key not in points:
        dropped.append({**example, "dropped": "no change point the read step printed"})
        continue
    kept.append({**example, "mis_said": points[key]})
about = [{"rel": "reading", "ref": f"{e['reading']}|{e['market']}|{e['at']}"} for e in kept]
points_word = "change point" if len(kept) == 1 else "change points"
title = f"MIS check for {read['findings']['day']}: {len(kept)} {points_word} read differently"
print(
    json.dumps(read | {"about": about, "examples": kept, "dropped": dropped, "note_title": title})
)
