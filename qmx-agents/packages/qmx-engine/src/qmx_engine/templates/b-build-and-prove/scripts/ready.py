"""Is the unit the builder saved the one that passed its check? Zero tokens.

Its inputs are told apart by shape: the run's inputs (`idea`, `window`, `fixture` on a test run),
the sealed spec (`memo_key`), the builder's answer (`item`, `object_id`, `unit`) and the
`unit-check` child's report, which the subworkflow node hands on as `outputs.report.main`.

QMB backtests a Library pin, so the document the check passed must be the draft the builder
saved. A unit that passed with no fix round is ready. A unit the check step had to fix is not the
saved draft, and a unit that still fails is not a unit, so neither is tested; `why` says which.
It prints `ok`, `why`, the `unit` pin, the in-sample `window` QMB runs, the check's summary,
`recorded`, the fixture a test run replays in place of QMB, and `walk_forward`, QMB's
walk-forward ask when the run names `ranges` (null otherwise): the unit's numbers to pick from in
each fold, over in-sample and the validation folds, never the holdout.
"""

import json
import sys


def report_of(value):
    if isinstance(value, dict):
        if "stopped" in value and "verdict" in value:
            return value
        value = list(value.values())
    if isinstance(value, list):
        return next((found for v in value if (found := report_of(v)) is not None), None)
    return None


given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
inputs = next(r for r in rows if "idea" in r and "window" in r)
sealed = next(r for r in rows if "memo_key" in r)
built = next((r for r in rows if "object_id" in r and "unit" in r), None)
report = report_of([r for r in rows if r is not built])

why = None
if built is None or not built.get("object_id"):
    why = "the builder saved no unit draft, so there is nothing to test"
elif report is None:
    why = "the unit-check step reported nothing"
elif report["verdict"] != "pass":
    why = f"the unit does not pass its check: {report['why']}"
elif report["rounds"] > 0:
    why = (
        f"the unit-check step fixed the builder's unit in {report['rounds']} round(s), so the "
        f"saved draft {built['item']} is not the checked document; it is not tested"
    )
windows = sealed["spec"]["windows"]
walk_forward = None
if inputs.get("ranges") and built is not None:
    end = windows["folds"][-1]["end"] if windows["folds"] else windows["in_sample"]["end"]
    walk_forward = {
        "unit": built["object_id"],
        "window": {"start": windows["in_sample"]["start"], "end": end},
        "split": {"folds": sealed["spec"]["study"]["folds"]},
        "ranges": inputs["ranges"],
    }
print(
    json.dumps(
        {
            "ok": why is None,
            "why": why,
            "unit": None if built is None else {"item": built["item"], "pin": built["object_id"]},
            "window": windows["in_sample"],
            "check": None
            if report is None
            else {k: report[k] for k in ("verdict", "rounds", "stopped", "problem_set")},
            "recorded": inputs.get("fixture"),
            "walk_forward": walk_forward,
        }
    )
)
