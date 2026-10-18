"""Applies one search-space move from the fixed list (card L4 step 11 and its gates). Its inputs,
tonight's state after the plateau and the proposed move, are told apart by shape.

A move outside the list, one that names the fitness function or a threshold, a range whose new low
is not below its high, a widen that narrows (or a narrow that widens), or a timeframe outside the
markets in scope is refused: the space stays as it was and the refusal is written into the history.
An applied move keeps the old space in the history as a dead-end region, resets the plateau count,
and the loop restarts from the generator.
"""

import copy
import json
import sys

LISTS = ("signal_classes", "filters", "exits")

given = json.load(sys.stdin)["in"]
state = next(v for v in given if "tried" in v)
move = next(v for v in given if "move" in v and "reason" in v)
space = copy.deepcopy(state["space"])
refused = None
name, target, value = move["move"], move["target"], move["value"]
if name not in state["moves"] or target in ("fitness", "thresholds"):
    refused = f"{name} on {target} is not a move the loop may make"
elif name in ("add_class", "drop_class"):
    if target not in LISTS:
        refused = f"{target} is not a class list"
    elif name == "add_class" and value not in space[target]:
        space[target].append(value)
    elif name == "drop_class" and value in space[target] and len(space[target]) > 1:
        space[target].remove(value)
    else:
        refused = f"cannot {name} {value} in {target}"
elif name in ("widen_range", "narrow_range"):
    low, high = value
    old_low, old_high = space["ranges"].get(target, (None, None))
    wider = old_low is not None and low <= old_low and high >= old_high
    narrower = old_low is not None and low >= old_low and high <= old_high
    if old_low is None or not low < high or (wider if name == "narrow_range" else narrower):
        refused = f"{name} {target} to {low}-{high} is not a {name.split('_')[0]}"
    else:
        space["ranges"][target] = [low, high]
elif value in space["timeframes"]:
    space["timeframes"] = [value]
else:
    refused = f"timeframe {value} is outside the space"
entry = {
    "move": name,
    "target": target,
    "value": value,
    "reason": move["reason"],
    "refused": refused,
}
dead = [*state["dead_regions"], state["space"]] if refused is None else state["dead_regions"]
print(
    json.dumps(
        state
        | {
            "space": space,
            "dead_regions": dead,
            "history": [*state["history"], entry],
            "trials_since_gain": 0 if refused is None else state["trials_since_gain"],
            "plateau": False,
        }
    )
)
