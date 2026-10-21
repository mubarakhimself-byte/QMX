"""Classify the new batch with the crystallised rule, and mark what falls back to the agent.

A title the rule matches is labelled by the script, for free. A title it does not match is marked
`fallback` and goes to the agent, which is the whole point of the pattern: the script handles what
it proved, the agent keeps what it never saw.

Every tenth item is also sent to the agent as a sample, so production keeps measuring the script
against the agent after the equivalence check passed (K-19)."""

import json
import re
import sys
from pathlib import Path

SHORT = 3


def words(title):
    return [word for word in re.findall(r"[a-z]+", title.casefold()) if len(word) > SHORT]


def classify(title, rules):
    found = sorted((word for word in words(title) if word in rules), key=len, reverse=True)
    return rules[found[0]] if found else None


given = json.load(sys.stdin)["in"]
items = given if isinstance(given, list) else [given]
agreed = next((v for v in items if isinstance(v, dict) and "rules" in v), {})
rules = agreed.get("rules") or {}
one_in = int(((agreed.get("sampling") or {}).get("one_in")) or 0)
batch = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "batch.json").read_text(encoding="utf-8")
)
classified = []
for index, item in enumerate(batch):
    label = classify(item["title"], rules)
    classified.append(
        {
            "item_id": item["item_id"],
            "title": item["title"],
            "label": label,
            "fallback": label is None,
            "sampled": bool(one_in) and index % one_in == 0,
        }
    )
sampled = [item for item in classified if item["sampled"]]
print(
    json.dumps(
        {
            "rules": rules,
            "crystallised": bool(agreed.get("crystallised")),
            "sampling": agreed.get("sampling"),
            "items": classified,
            "sampled": sampled,
            "any_sampled": bool(sampled),
            "fallbacks": sum(1 for item in classified if item["fallback"]),
        }
    )
)
