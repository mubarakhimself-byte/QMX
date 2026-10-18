"""Keeps only the findings a script reproduced (card R8 steps 3 and 5 and its gate). Its inputs,
the kernel's run and the re-run, are told apart by shape.

A finding is reported only when the re-run from the snapshot gives the same number (to 1e-9
relative); any other is listed as "not reproduced" and is never reported as a finding. The
evidence pack is complete when it holds the cells, the sub-call log and the cost.
"""

import json
import math
import sys

given = json.load(sys.stdin)["in"]
run = next(v for v in given if "findings" in v)
rerun = {r["id"]: r for r in next(v for v in given if "reproduced" in v)["reproduced"]}
kept, not_reproduced = [], []
for finding in run["findings"]:
    again = rerun.get(finding["id"], {})
    value = again.get("value")
    if value is not None and math.isclose(value, finding["value"], rel_tol=1e-9, abs_tol=1e-12):
        kept.append(finding | {"reproduced": True})
    else:
        why = again.get("error") or ("no re-run" if not again else f"re-run gave {value}")
        not_reproduced.append({"id": finding["id"], "why": why})
missing = [k for k in ("cells", "sub_call_log", "cost_usd") if not run.get(k) and run.get(k) != 0]
print(
    json.dumps(
        {
            "findings": kept,
            "not_reproduced": not_reproduced,
            "evidence_complete": not missing,
            "evidence_missing": missing,
            "snapshot": run.get("snapshot"),
            "cost_usd": run.get("cost_usd"),
        }
    )
)
