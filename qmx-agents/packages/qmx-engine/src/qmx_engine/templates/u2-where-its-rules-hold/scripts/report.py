"""The run's answer: where the rules hold, and the proposal card it landed, if any. Zero tokens.

Its inputs are the `holds` step's answer and, when a market held, the `proposal-card` child's
output, nested as `outputs.card.main`."""

import json
import sys

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
found = next(r for r in rows if "holds" in r)
card = next(
    (r["outputs"]["card"]["main"]["card"] for r in rows if isinstance(r.get("outputs"), dict)),
    None,
)
print(json.dumps({k: v for k, v in found.items() if k != "proposal"} | {"card": card}))
