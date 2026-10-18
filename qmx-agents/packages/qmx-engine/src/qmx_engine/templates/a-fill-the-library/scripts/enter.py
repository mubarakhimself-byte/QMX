"""Writes the graded Library entry as run files, one per card and one per source plus the
inventory, under `library/` in the run's write zone. The node lists `library/` as its artifacts,
so the run-end export stores each file in the Library port, linked `produced-by` to the run. No
`library` node is used. Prints the entry as the run's result."""

import json
import sys
from pathlib import Path


def flat(given):
    found = []
    for value in given if isinstance(given, list) else [given]:
        if isinstance(value, dict) and set(value) == {"input", "verdict", "feedback"}:
            found += flat(value["input"])
        else:
            found.append(value)
    return found


graded = json.load(sys.stdin)["in"]
entry = flat(graded["input"])[graded["feedback"]["output"]]
root = Path("library")
for folder, rows in (("cards", entry["cards"]), ("sources", entry["sources"])):
    (root / folder).mkdir(parents=True, exist_ok=True)
    for row in rows:
        (root / folder / f"{row['library_id']}.json").write_text(json.dumps(row, indent=1), "utf-8")
(root / "inventory.json").write_text(json.dumps(entry["inventory"], indent=1), "utf-8")
print(json.dumps(entry))
