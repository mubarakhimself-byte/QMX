"""The schema compatibility check (card D9 pre-check and step 2), a JSON Schema subset check. Zero
tokens.

Both apps must exist and be enabled. The producer's output is compatible when every field the
consumer requires is a field the producer requires, with the same type, recursively through
objects. Each mismatch is named. An incompatible pair goes to a transform step.
"""

import json
import sys


def mismatches(provides, feeds, path="$"):
    found = []
    if feeds.get("type") and provides.get("type") != feeds.get("type"):
        return [
            f"{path}: the producer gives {provides.get('type')}, the consumer needs {feeds['type']}"
        ]
    if feeds.get("type") == "object":
        given = provides.get("properties", {})
        sure = set(provides.get("required", []))
        for name in feeds.get("required", []):
            if name not in given or name not in sure:
                found.append(
                    f"{path}.{name}: the consumer requires it, the producer may not give it"
                )
            else:
                found += mismatches(
                    given[name], feeds.get("properties", {}).get(name, {}), f"{path}.{name}"
                )
    return found


apps = json.load(sys.stdin)["in"]
problems = [
    f"{a['id']} is not enabled" for a in (apps["producer"], apps["consumer"]) if not a["enabled"]
]
gaps = mismatches(apps["provides"], apps["feeds"])
print(json.dumps({"compatible": not problems and not gaps, "problems": problems, "gaps": gaps}))
