"""Is the unit the builder saved the one that passed its check? Zero tokens.

Its inputs are told apart by shape: the run's inputs (`idea`, `window`, `fixture` on a test run),
the sealed spec (`memo_key`), the builder's answer (`item`, `object_id`, `unit`) and the
`unit-check` child's report, which the subworkflow node hands on as `outputs.report.main`.

QMB backtests a Library pin, so the document the check passed must be the draft the builder
saved. A unit that passed with no fix round is ready. A unit the check step had to fix is not the
saved draft, and a unit that still fails is not a unit, so neither is tested; `why` says which.
It prints `ok`, `why`, the `unit` pin, the in-sample `window` QMB runs, the check's summary, and
`recorded`, the fixture a test run replays in place of QMB.
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
print(
    json.dumps(
        {
            "ok": why is None,
            "why": why,
            "unit": None if built is None else {"item": built["item"], "pin": built["object_id"]},
            "window": sealed["spec"]["windows"]["in_sample"],
            "check": None
            if report is None
            else {k: report[k] for k in ("verdict", "rounds", "stopped", "problem_set")},
            "recorded": inputs.get("fixture"),
        }
    )
)
