"""Setup, once (card L4 step 1 and its gates). Zero tokens.

Loads the search space as data and refuses one the loop may not run: every class list and range
must be non-empty, every range low below high, and the fitness function one of his approved list.
The moves the loop may make come from a fixed list, and changing the fitness function is not one of
them. Gate thresholds are not here: the family step reads them from Settings, read-only.

The night's counts are on the card: `revolutions`, `revolutions_without_gain`, `trials` and
`plateau_trials` from the run's inputs, each one left out taking its `default` in
`definition.json`. They are starting defaults, never caps, and travel in `counts`.
"""

import json
import os
import sys
from pathlib import Path

APPROVED_FITNESS = ("validated_sharpe", "validated_expectancy_r", "profit_factor_after_costs")
MOVES = ("add_class", "drop_class", "widen_range", "narrow_range", "switch_timeframe")
LISTS = ("signal_classes", "filters", "exits", "timeframes", "markets")
COUNTS = ("revolutions", "revolutions_without_gain", "trials", "plateau_trials")

card = json.loads((Path(os.environ["QMX_CODE"]) / "definition.json").read_text("utf-8"))
given = json.load(sys.stdin)["in"]
space = given["search_space"]
problems = [f"{name} is empty" for name in LISTS if not space.get(name)]
problems += [
    f"range {name} has low {low} not below high {high}"
    for name, (low, high) in space.get("ranges", {}).items()
    if not low < high
]
if space.get("fitness") not in APPROVED_FITNESS:
    problems.append(f"fitness {space.get('fitness')!r} is not on the approved list")
if problems:
    sys.stderr.write("the search space cannot run: " + "; ".join(problems))
    raise SystemExit(1)
counts = {name: given.get(name, card["inputs"]["properties"][name]["default"]) for name in COUNTS}
print(
    json.dumps({"family": given["family"], "space": space, "moves": list(MOVES), "counts": counts})
)
