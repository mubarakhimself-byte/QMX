"""The diagnoser may not see holdout numbers (card D3's gates). Drops the holdout and every report
section or field whose name mentions it, and refuses a parent whose report is missing a section
the diagnosis needs."""

import json
import sys

SECTIONS = ("backtest", "walk_forward", "monte_carlo", "regimes", "sessions")


def blind(value):
    if isinstance(value, dict):
        return {k: blind(v) for k, v in value.items() if "holdout" not in k.casefold()}
    if isinstance(value, list):
        return [blind(v) for v in value]
    return value


read = json.load(sys.stdin)["in"]
missing = [s for s in SECTIONS if s not in read["report"]]
if missing:
    sys.stderr.write(f"the parent has no full report: {', '.join(missing)} missing")
    raise SystemExit(1)
print(
    json.dumps(
        {"parent": blind(read["parent"]), "report": blind(read["report"]), "family": read["family"]}
    )
)
