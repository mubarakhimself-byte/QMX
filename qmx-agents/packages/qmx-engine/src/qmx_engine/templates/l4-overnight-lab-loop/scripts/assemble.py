"""The morning card: the end of the night with the writer's summary. Its inputs are told apart by
shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
night = next(v for v in given if "survivors" in v)
prose = next((v for v in given if "summary" in v), {"summary": ""})
print(json.dumps(night | {"summary": prose["summary"]}))
