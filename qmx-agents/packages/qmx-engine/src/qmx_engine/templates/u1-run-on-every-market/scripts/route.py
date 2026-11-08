"""Where the run goes: QMB, or a recorded run on a test run. Zero tokens.

It prints `recorded`, the fixture a test run replays (null otherwise), and `ask`, the sweep QMB
runs: the unit's pin, the window, and a grid of his markets alone, so each market trades alone
as its own counted try.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
ask = {"unit": given["unit"], "window": given["window"], "grid": {"markets": given["markets"]}}
print(json.dumps({"recorded": given.get("fixture"), "ask": ask}))
