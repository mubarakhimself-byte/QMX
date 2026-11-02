"""Seals the experiment spec before any unit is built or any result is seen (card D2, steps 1 to
4 and 7; funnel stage 9). Zero tokens.

The holdout and the split are study settings, his choice per study, and both are off by default:
the whole `window` is then one in-sample window. Each setting the run's `study` input leaves out
takes its card default, the `default` of `inputs.study` in `definition.json`. With `split` on, the
first `in_sample_share` of the range is in-sample and the rest, up to the holdout, is cut into
`folds` walk-forward validation folds. With `holdout` on, the family's sealed holdout is reused, or
else the last `holdout_share` of the range becomes it; it is later than every other window, and
no window the family already used may overlap it. The shortest in-sample window, fold and holdout
are study settings too.

Costs, point-in-time fields and the session zone are no longer the spec's to check: QMB charges
each market's own costs, its bars are point in time, and the unit names its own zone. Refuses a
window shorter than its minimum and a window that overlaps the holdout. The memo key is the hash
of the sealed spec, settings included, so a finished run never reruns on resume.
"""

import hashlib
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

card = json.loads((Path(os.environ["QMX_CODE"]) / "definition.json").read_text("utf-8"))
defaults = {
    name: field["default"]
    for name, field in card["inputs"]["properties"]["study"]["properties"].items()
}
given = json.load(sys.stdin)["in"]
study = defaults | (given.get("study") or {})
window = given["window"]
family = given.get("family") or {}
start, end = date.fromisoformat(window["start"]), date.fromisoformat(window["end"])
span = (end - start).days
problems = []

holdout = None
if study["holdout"]:
    holdout = family.get("holdout") or {
        "start": str(start + timedelta(days=round(span * (1 - study["holdout_share"])))),
        "end": str(end),
    }
tested_end = date.fromisoformat(holdout["start"]) if holdout else end
in_sample_end = tested_end
folds = []
if study["split"]:
    in_sample_end = start + timedelta(days=round(span * study["in_sample_share"]))
    fold_days = max((tested_end - in_sample_end).days // study["folds"], 0)
    folds = [
        {
            "start": str(in_sample_end + timedelta(days=k * fold_days)),
            "end": str(in_sample_end + timedelta(days=(k + 1) * fold_days)),
        }
        for k in range(study["folds"])
    ]
    if fold_days < study["min_fold_days"]:
        problems.append(f"a validation fold is shorter than {study['min_fold_days']} days")
windows = {
    "in_sample": {"start": str(start), "end": str(in_sample_end)},
    "folds": folds,
    "holdout": holdout,
}

if (in_sample_end - start).days < study["min_in_sample_days"]:
    problems.append(f"in-sample is shorter than {study['min_in_sample_days']} days")
if holdout:
    holdout_start, holdout_end = (date.fromisoformat(holdout[k]) for k in ("start", "end"))
    if (holdout_end - holdout_start).days < study["min_holdout_days"]:
        problems.append(f"the holdout is shorter than {study['min_holdout_days']} days")
    if in_sample_end > holdout_start:
        problems.append("the holdout is not later than every other window")
    for used in family.get("used_windows", []):
        if (
            date.fromisoformat(used["start"]) < holdout_end
            and date.fromisoformat(used["end"]) > holdout_start
        ):
            problems.append(f"the window {used['start']} to {used['end']} overlaps the holdout")

spec = {
    "idea": given["idea"],
    "window": {"start": str(start), "end": str(end)},
    "seed": given.get("seed", 7),
    "study": study,
    "windows": windows,
}
memo_key = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
print(json.dumps({"spec": spec, "memo_key": memo_key, "problems": problems, "ok": not problems}))
