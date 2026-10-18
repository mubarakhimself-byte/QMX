"""Puts the surprise notes into the calendar strip. Its two inputs are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
strip = next(v for v in given if "strip" in v)
notes = next(v for v in given if "strip" not in v)
print(json.dumps(strip | {"notes": notes["notes"]}))
