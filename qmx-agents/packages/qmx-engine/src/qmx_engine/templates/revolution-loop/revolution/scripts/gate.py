"""The deterministic gates a revolution's candidate must pass before it may be kept.

No model decides this: the metric is one of the schema's closed list, the entry or the exit names an
operator word, the candidate has a stop, and its evidence names a source the brief was given. A
candidate that fails is kept as a negative result, never dropped.
"""

import json
import sys

OPERATORS = ("above", "below", "over", "under", "crosses", ">", "<")
given = json.load(sys.stdin)["in"]
items = given if isinstance(given, list) else [given]
candidate = next((found for found in items if isinstance(found, dict) and "entry" in found), None)
brief = next((found for found in items if isinstance(found, dict) and "sources" in found), {})
problems = []
if candidate is None:
    problems.append("the drafter wrote no candidate")
else:
    sides = f"{candidate.get('entry', '')} {candidate.get('exit', '')}".lower()
    if not any(word in sides for word in OPERATORS):
        problems.append("neither the entry nor the exit names an operator")
    if str(candidate.get("evidence", "")) not in list(brief.get("sources") or []):
        problems.append("the evidence names no source this run was given")
    if not str(candidate.get("stop", "")).strip():
        problems.append("the candidate has no stop")
print(
    json.dumps(
        {
            "candidate": candidate,
            "passed": not problems,
            "problems": problems,
            "chain": {
                key: brief.get(key)
                for key in ("idea", "score", "attempts", "rounds", "negatives", "fixture")
            },
        }
    )
)
