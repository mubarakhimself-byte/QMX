"""The install card (card D7 steps 8 and 9 and its gates). Its inputs, the scaffold and the check
report, are told apart by shape.

No install card until every check line reads pass or needs-human; a failing render check always
blocks. A scaffold refused for a money tool ends here, unbuilt. The card says what the app does,
shows the check report and the box (budget, network allow-list, breaker), and installs disabled:
install always asks, and enabling is his act.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
scaffold = next(v for v in given if "app_toml" in v)
check = next((v for v in given if "lines" in v), {"lines": []})
failing = [line for line in check["lines"] if line["status"] == "fail"]
blocked = scaffold["problems"] + [line["name"] for line in failing]
needs_human = [line for line in check["lines"] if line["status"] == "needs-human"]
card = None
if not blocked:
    card = {
        "kind": "install",
        "app": scaffold["app"],
        "version": scaffold["version"],
        "installs": "disabled",
        "box": {"tools": scaffold["tools"], "network": "allow-list only", "breaker": "on"},
        "needs_human": [line["name"] for line in needs_human],
        "screenshots": check.get("screenshots", []),
    }
print(
    json.dumps(
        {
            "app": scaffold["app"],
            "version": scaffold["version"],
            "lines": check["lines"],
            "blocked_by": blocked,
            "card": card,
        }
    )
)
