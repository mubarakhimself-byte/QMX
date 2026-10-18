"""Tighten-only cards (card R3 step 6, card P3 step 6): every red unit gets a card whose options are
keep watching, shrink within the declared range, back to demo, or bench, with "keep watching" as the
default if he does not answer. A loosening is never an option. A red unit with no explanation still
gets its card. Nothing changes without his click. Its inputs, the decay results and the
explanations when some unit was flagged, are told apart by shape."""

import json
import sys

OPTIONS = ["keep watching", "shrink within the declared range", "back to demo", "bench"]

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
decay = next(v for v in given if "flagged" in v)
explained = {
    e["unit"]: e for e in next((v["explanations"] for v in given if "explanations" in v), [])
}
cards = [
    {
        "unit": u["unit"],
        "options": OPTIONS,
        "default": "keep watching",
        "explanation": explained.get(u["unit"], {}).get("what_changed", "no explanation"),
    }
    for u in decay["units"]
    if u["level"] == "red"
]
print(json.dumps(decay | {"explanations": list(explained.values()), "cards": cards}))
