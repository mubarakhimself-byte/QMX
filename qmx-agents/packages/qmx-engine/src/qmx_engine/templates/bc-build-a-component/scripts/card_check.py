"""The pre-check and the scaffold (card D1 pre-check and step 1, card D5 steps 1 and 2). Zero
tokens.

The card passes when every parameter has a value or reads `unresolved`, and it names a formula, a
warm-up and an output type. A Pine source with `lookahead_on` or a repaint flag is rebuilt without
it, and the rebuild is labelled a child. The formula hash is what the Library dedupe matches on.
The scaffold is the component folder the builder fills: the interface, the parameter schema, the
tests and their fixtures.
"""

import hashlib
import json
import re
import sys

REQUIRED = ("name", "kind", "formula", "warm_up", "output_type")

card = json.load(sys.stdin)["in"]["card"]
problems = [f"the card has no {field}" for field in REQUIRED if not card.get(field)]
problems += [
    f"parameter {p['name']} has neither a value nor unresolved"
    for p in card.get("parameters", [])
    if p.get("value") in (None, "")
]
unresolved = [p["name"] for p in card.get("parameters", []) if p.get("value") == "unresolved"]
pine = card.get("pine") or ""
repaint = bool(re.search(r"lookahead\s*=\s*barmerge\.lookahead_on", pine)) or card.get("repaint")
formula = re.sub(r"\s+", "", str(card.get("formula", ""))).casefold()
name = re.sub(r"[^a-z0-9]+", "_", str(card.get("name", "component")).casefold()).strip("_")
scaffold = [
    f"{name}/interface.py",
    f"{name}/parameters.json",
    f"{name}/tests/test_worked_example.py",
    f"{name}/tests/test_edges.py",
    f"{name}/tests/test_no_future.py",
    f"{name}/fixtures/week.csv",
]
print(
    json.dumps(
        {
            "ok": not problems,
            "problems": problems,
            "card": card,
            "unresolved": unresolved,
            "formula_hash": hashlib.sha256(formula.encode()).hexdigest()[:16],
            "rebuild_without_lookahead": repaint,
            "label": "child: rebuilt without lookahead" if repaint else None,
            "scaffold": scaffold,
        }
    )
)
