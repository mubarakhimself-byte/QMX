"""The digest's own check: every line names an object or a run the collect step really saw.

A writer that invents an item fails the run here, before the card is rendered, so the digest never
shows a line nothing backs."""

import json
import sys

given = json.load(sys.stdin)["in"]
doc = given if isinstance(given, dict) else given[-1]
problems = list(doc.get("problems") or [])
print(json.dumps({"verdict": "fail" if problems else "pass", "feedback": {"problems": problems}}))
