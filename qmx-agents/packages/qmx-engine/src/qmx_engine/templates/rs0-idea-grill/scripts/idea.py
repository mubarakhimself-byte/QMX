"""The idea and what is already known about it, before the first question, so known facts are shown
and never asked. Known dead ends come with the run input (`dead_ends`); searching the Library for
them needs the real Library, so without them the step says the Library was not searched. A run
started with `{"fixture": true}` reads `fixtures/idea.json` instead."""

import json
import sys
from pathlib import Path

given = json.load(sys.stdin).get("in") or {}
if given.get("fixture"):
    given = json.loads((Path(__file__).parents[1] / "fixtures" / "idea.json").read_text("utf-8"))
idea = str(given.get("idea") or "").strip()
if not idea:
    sys.stderr.write("the run input names no idea")
    raise SystemExit(2)
dead_ends = given.get("dead_ends")
searched = (
    "dead ends given with the run"
    if dead_ends is not None
    else "could not check: searching the Library needs the real Library"
)
print(json.dumps({"idea": idea, "known": {"dead_ends": dead_ends or [], "searched": searched}}))
