"""Dedupe against everything tried (card L4 step 4), and drop a candidate outside the space. Its
inputs, tonight's state and the generator's batch, are told apart by shape. A candidate's spec
hash is the hash of its spec with sorted keys, so the same candidate always has the same hash.
"""

import hashlib
import json
import sys

given = json.load(sys.stdin)["in"]
state = next(v for v in given if "tried" in v)
batch = next(v for v in given if "candidates" in v)["candidates"]
space, tried = state["space"], set(state["tried"])


def inside(spec):
    ranges = space["ranges"]
    return (
        spec["signal_class"] in space["signal_classes"]
        and spec["timeframe"] in space["timeframes"]
        and spec["market"] in space["markets"]
        and spec["exit"] in space["exits"]
        and set(spec["filters"]) <= set(space["filters"])
        and all(
            name in ranges and ranges[name][0] <= v <= ranges[name][1]
            for name, v in spec["params"].items()
        )
    )


fresh, dropped = [], []
for candidate in batch:
    spec_hash = hashlib.sha256(json.dumps(candidate["spec"], sort_keys=True).encode()).hexdigest()
    if spec_hash in tried:
        dropped.append({"spec_hash": spec_hash, "why": "already tried"})
    elif not inside(candidate["spec"]):
        dropped.append({"spec_hash": spec_hash, "why": "outside the search space"})
    else:
        tried.add(spec_hash)
        fresh.append(candidate | {"spec_hash": spec_hash})
print(json.dumps({"fresh": fresh, "dropped": dropped}))
