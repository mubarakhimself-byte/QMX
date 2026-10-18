"""The desk brief card: the writer's headline, summary, decisions and watch lines beside the tiles,
which come from the gather and never from the model, so a node fact the writer cannot see stays
`could not check`. The input is the links check's pass, holding the ranked day and the brief."""

import json
import sys


def flat(given):
    found = []
    for value in given if isinstance(given, list) else [given]:
        if isinstance(value, dict) and set(value) == {"input", "verdict", "feedback"}:
            found += flat(value["input"])
        else:
            found.append(value)
    return found


given = flat(json.load(sys.stdin)["in"])
day = next(v for v in given if "ranked" in v)
brief = next(v for v in given if "headline" in v)
print(
    json.dumps(
        {
            "date": day["date"],
            "edition": day["edition"],
            "headline": brief["headline"],
            "summary": brief["summary"],
            "node_facts": day["node_facts"],
            "tiles": {
                "events": [e for e in day["events"] if e["impact"] != "low"],
                "alerts": day["alerts"],
                "desk": day["desk"],
                "research": day["research"],
            },
            "decisions": brief["decisions"],
            "watch_today": brief["watch_today"],
            "could_not_check": day["could_not_check"],
            "quiet": False,
        }
    )
)
