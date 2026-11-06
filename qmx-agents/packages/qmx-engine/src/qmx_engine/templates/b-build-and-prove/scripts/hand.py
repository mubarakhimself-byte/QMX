"""Hands the referee's verdict on by reference, so what routes is what the Library holds, never a
model's copy. Zero tokens. The same file in every template that asks the referee.

Its inputs are told apart by shape: the referee step's `verdict` on a real run, or the replay's
`library_written` receipts on a recorded one; what QMB answered for each run (`run_id`); and the
step that names the run's pin, `Unit ready?`'s `unit.pin` or the route's `ask` or `sweep`.

It prints `verdict`, the reference the `library` node reads; `refs`, that reference and those of the
verdict's cards and results as the copy names them; `unit`, this run's pin; `runs`, this run's QMB
runs; and `recorded`. The next script holds the copy to all of it, so nothing here is trusted.
"""

import json
import sys


def pin_of(rows):
    for row in rows:
        if isinstance(row.get("unit"), dict):
            return row["unit"]["pin"]
        for ask in ("ask", "sweep"):
            if isinstance(row.get(ask), dict):
                return row[ask]["unit"]
    return None


given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
planted = next((r["library_written"] for r in rows if "library_written" in r), None)
if planted is not None:
    ids = [written["object_id"] for written in planted]
else:
    copy = next(r["verdict"] for r in rows if isinstance(r.get("verdict"), dict))
    ids = [copy["verdict_id"], *copy.get("cards", {}).values(), *copy["result_ids"]]
print(
    json.dumps(
        {
            "verdict": f"@library:{ids[0]}",
            "refs": [f"@library:{found}" for found in ids],
            "unit": pin_of(rows),
            "runs": [r["run_id"] for r in rows if "run_id" in r],
            "recorded": planted is not None,
        }
    )
)
