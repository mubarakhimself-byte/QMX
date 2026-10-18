"""The component page and the publish rule (card D1 step 9). All green, a review that finds the
code matches the card with nothing invented, and no failing test after the repair: the page offers
publishing a version. Otherwise it stays a draft with each failing check named; a test still
failing after one repair saves the card as a `fragment` with the failure note. An incomplete card
ends here with its problems. Its inputs are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
card = next(v for v in given if "formula_hash" in v)
verdict = next((v for v in given if "failing" in v), None)
review = next((v for v in given if "matches_card" in v), None)
build = next((v for v in given if "fragment" in v), {"fragment": None})
failing = list(verdict["failing"]) if verdict else []
if review is not None and not review["matches_card"]:
    failing.append("the code does not match the card")
if review is not None and review["invented_values"]:
    failing.append("the code invents values the card does not give")
if not card["ok"]:
    state = "card incomplete"
elif build["fragment"]:
    state = "fragment"
    failing.append(f"test {build['fragment']} still fails after one repair")
else:
    state = "ready to publish a version" if not failing else "draft"
print(
    json.dumps(
        {
            "name": card["card"]["name"],
            "kind": card["card"]["kind"],
            "formula_hash": card["formula_hash"],
            "label": card["label"],
            "state": state,
            "problems": card["problems"],
            "checks": verdict["checks"] if verdict else {},
            "failing": failing,
            "tests": verdict["tests"] if verdict else [],
            "bars_per_second": verdict["bars_per_second"] if verdict else None,
            "review": review["notes"] if review else "",
            "invented_values": review["invented_values"] if review else [],
        }
    )
)
