"""Passes when every fetched word got exactly one true-or-false answer across the chunks."""

import json
import sys

parts = json.load(sys.stdin)["in"]
answers = [a for part in parts for a in part.get("results", [])]
ids = sorted(a.get("id") for a in answers)
typed = all(isinstance(a.get("animal"), bool) for a in answers)
ok = ids == list(range(12)) and typed
print(json.dumps({"verdict": "pass" if ok else "fail", "feedback": f"{len(answers)} answers"}))
