"""Does a script agree with the agent on every replay?

The script is derived from the replays alone, with no model: a word that appears in titles of exactly
one label becomes a rule for that label, and a title is labelled by its longest matching word. A
title no rule matches has no label, and the workflow sends it to the agent, never guesses.

The equivalence check is the point: only when every one of the replays gets back the label the agent
gave is the step crystallised, and only then is the sampling rate set (one item in ten goes back to
the agent, so the script keeps being measured in production).
"""

import json
import re
import sys

SHORT = 3


def words(title):
    return [word for word in re.findall(r"[a-z]+", title.casefold()) if len(word) > SHORT]


def derive(replays):
    """`word -> label` for every word whose titles carry one label only."""
    seen: dict[str, set[str]] = {}
    for replay in replays:
        for word in words(replay["title"]):
            seen.setdefault(word, set()).add(replay["label"])
    return {word: next(iter(labels)) for word, labels in seen.items() if len(labels) == 1}


def classify(title, rules):
    """The label of the longest rule word in the title, or None when no rule matches."""
    found = sorted((word for word in words(title) if word in rules), key=len, reverse=True)
    return rules[found[0]] if found else None


given = json.load(sys.stdin)["in"]
state = given if isinstance(given, dict) else given[-1]
replays = state.get("replays") or []
rules = derive(replays)
wrong = [
    {"item_id": replay["item_id"], "agent": replay["label"], "script": classify(replay["title"], rules)}
    for replay in replays
    if classify(replay["title"], rules) != replay["label"]
]
equivalent = bool(replays) and not wrong
print(
    json.dumps(
        {
            "fixture": state.get("fixture"),
            "rules": rules,
            "equivalent": equivalent,
            "agreeing": len(replays) - len(wrong),
            "replays": len(replays),
            "wrong": wrong,
            "crystallised": equivalent,
            "sampling": {"one_in": 10} if equivalent else None,
            "labels": sorted(set(rules.values())),
        }
    )
)
