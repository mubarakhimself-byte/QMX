"""The gates a model never decides (card D1 steps 4 to 6 and its kill rules, card D5 steps 4 and 5).

No-future: at every sampled bar t, the value computed on data cut at t equals the value computed on
the full data (to 1e-9); any difference is lookahead. Warm-up: the first `warm_up` values are
missing, not zero. Test first: every test file was first written before the code file. Round trip:
Graph to code to Graph gives the same graph. Green also needs every unit test passing, a clean
lint and type check. Publish needs all of it; otherwise the component stays a draft with each
failing check named.
"""

import json
import math
import sys

given = json.load(sys.stdin)["in"]
ran = next(v for v in given if "truncated" in v) if isinstance(given, list) else given
mismatched = [
    t
    for t, value in ran["truncated"].items()
    if not math.isclose(value, ran["full"][t], rel_tol=1e-9, abs_tol=1e-12)
]
warm = ran["first_values"][: ran["warm_up"]]
order = {f["path"]: f["order"] for f in ran["written"]}
tests = [o for path, o in order.items() if "/tests/" in path]
code = [o for path, o in order.items() if "/tests/" not in path and path.endswith(".py")]
checks = {
    "unit tests": all(t["passed"] for t in ran["tests"]) and bool(ran["tests"]),
    "no-future": not mismatched,
    "warm-up missing, not zero": all(v is None for v in warm),
    "tests written first": bool(tests) and bool(code) and max(tests) < min(code),
    "Graph and Code round trip": ran["graph_round_trip"]["graph"]
    == ran["graph_round_trip"]["rebuilt"],
    "lint": ran["lint"] == "clean",
    "types": ran["types"] == "clean",
}
print(
    json.dumps(
        {
            "checks": checks,
            "failing": [name for name, ok in checks.items() if not ok],
            "lookahead_at": mismatched,
            "bars_per_second": ran["bars_per_second"],
            "tests": ran["tests"],
        }
    )
)
