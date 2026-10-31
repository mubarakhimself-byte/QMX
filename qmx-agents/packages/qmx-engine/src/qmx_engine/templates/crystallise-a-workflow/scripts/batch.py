"""Classify the new batch with the crystallised rule, and mark what falls back to the agent.

A title the rule matches is labelled by the script, for free. A title it does not match is marked
`fallback` and goes to the agent, which is the whole point of the pattern: the script handles what
it proved, the agent keeps what it never saw.

Every tenth item is also sent to the agent as a sample, so production keeps measuring the script
against the agent after the equivalence check passed (K-19).

The batch is the run's own `batch` input, each item `{item_id, title}`; a run with none is refused.
Only a run whose `fixture` input is set classifies the shipped fixture batch."""

import json
import re
import sys
from pathlib import Path

FAILURE = "[QMX_FAILURE]"
SHORT = 3


def words(title):
    return [word for word in re.findall(r"[a-z]+", title.casefold()) if len(word) > SHORT]


def classify(title, rules):
    found = sorted((word for word in words(title) if word in rules), key=len, reverse=True)
    return rules[found[0]] if found else None


given = json.load(sys.stdin)["in"]
items = given if isinstance(given, list) else [given]
agreed = next((v for v in items if isinstance(v, dict) and "rules" in v), {})
asked = next((v for v in items if isinstance(v, dict) and "rules" not in v), {})
rules = agreed.get("rules") or {}
one_in = int(((agreed.get("sampling") or {}).get("one_in")) or 0)
if asked.get("fixture") or agreed.get("fixture"):
    batch = json.loads(
        (Path(__file__).parents[1] / "fixtures" / "batch.json").read_text(encoding="utf-8")
    )
else:
    batch = [
        item
        for item in asked.get("batch") or []
        if isinstance(item, dict) and "item_id" in item and "title" in item
    ]
    if not batch:
        print(f"{FAILURE} no batch given: name the new items as batch, each {{item_id, title}}")
        raise SystemExit(0)
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
