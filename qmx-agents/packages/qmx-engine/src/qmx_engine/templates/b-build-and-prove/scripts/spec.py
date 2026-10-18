"""Seals the experiment spec before any result is seen (card D2, steps 1 to 4 and 7; funnel stage
9). Zero tokens.

Splits the data range into in-sample (the first 60%), three walk-forward validation folds (the next
20%) and the family's holdout. The holdout is sealed once per family and is later than every other
window: an existing one is reused, otherwise the last 20% becomes it. Refuses a spec without the
four costs, a field that is not point-in-time, a strategy with no session timezone, a split shorter
than its minimum, and a window that overlaps the family's holdout or a window the family already
used for the holdout's purpose. The memo key is the hash of the sealed spec, so a finished backtest
never reruns on resume.
"""

import hashlib
import json
import sys
from datetime import date, timedelta

COSTS = ("spread", "commission", "slippage", "swap")
MIN_DAYS = {"in_sample": 180, "fold": 30, "holdout": 60}
FOLDS = 3

given = json.load(sys.stdin)["in"]
strategy, data, costs = given["strategy"], given["data"], given.get("costs") or {}
family = given.get("family") or {}
start, end = date.fromisoformat(data["start"]), date.fromisoformat(data["end"])
span = (end - start).days
problems = []

missing = [name for name in COSTS if name not in costs]
if missing:
    problems.append(f"no spec without costs: {', '.join(missing)} missing")
problems += [f"field {f['name']} is not point-in-time" for f in data["fields"] if not f.get("pit")]
if not strategy.get("session_timezone"):
    problems.append("the strategy names no session timezone")

if family.get("holdout"):
    holdout = family["holdout"]
else:
    holdout = {"start": str(start + timedelta(days=round(span * 0.8))), "end": str(end)}
holdout_start = date.fromisoformat(holdout["start"])
in_sample_end = start + timedelta(days=round(span * 0.6))
fold_days = max((holdout_start - in_sample_end).days // FOLDS, 0)
folds = [
    {
        "start": str(in_sample_end + timedelta(days=k * fold_days)),
        "end": str(in_sample_end + timedelta(days=(k + 1) * fold_days)),
    }
    for k in range(FOLDS)
]
windows = {
    "in_sample": {"start": str(start), "end": str(in_sample_end)},
    "folds": folds,
    "holdout": holdout,
}

if (in_sample_end - start).days < MIN_DAYS["in_sample"]:
    problems.append(f"in-sample is shorter than {MIN_DAYS['in_sample']} days")
if fold_days < MIN_DAYS["fold"]:
    problems.append(f"a validation fold is shorter than {MIN_DAYS['fold']} days")
if (date.fromisoformat(holdout["end"]) - holdout_start).days < MIN_DAYS["holdout"]:
    problems.append(f"the holdout is shorter than {MIN_DAYS['holdout']} days")
if in_sample_end > holdout_start:
    problems.append("the holdout is not later than every other window")
for used in family.get("used_windows", []):
    if (
        date.fromisoformat(used["start"]) < date.fromisoformat(holdout["end"])
        and date.fromisoformat(used["end"]) > holdout_start
    ):
        problems.append(f"the window {used['start']} to {used['end']} overlaps the holdout")

spec = {
    "strategy": strategy["id"],
    "code_hash": strategy["code_hash"],
    "data_snapshot": data.get("snapshot"),
    "costs": costs,
    "seed": given.get("seed", 7),
    "windows": windows,
}
memo_key = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
print(json.dumps({"spec": spec, "memo_key": memo_key, "problems": problems, "ok": not problems}))
