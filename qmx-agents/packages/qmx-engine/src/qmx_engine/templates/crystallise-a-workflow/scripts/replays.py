"""Read the recorded replays of the agent step this template is crystallising.

Each replay is one item the agent labelled: `item_id`, the `title` the agent saw and the `label` it
gave. Twenty or more replays are what an equivalence check needs before a script may replace the
agent (K-19)."""

import json
import sys
from pathlib import Path

given = json.load(sys.stdin)["in"]
state = given if isinstance(given, dict) else next((v for v in given if isinstance(v, dict)), {})
root = Path(__file__).parents[1]
replays = json.loads((root / "fixtures" / "replays.json").read_text("utf-8"))
print(
    json.dumps(
        {
            "fixture": state.get("fixture"),
            "replays": replays,
            "count": len(replays),
            "labels": sorted({replay["label"] for replay in replays}),
        }
    )
)
