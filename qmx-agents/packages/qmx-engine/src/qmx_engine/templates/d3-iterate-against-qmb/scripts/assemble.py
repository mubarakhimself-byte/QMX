"""The generation tree and survivor scorecard with the writer's summary. Its inputs are told apart
by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
tree = next(v for v in given if "tree" in v)
prose = next((v for v in given if "summary" in v), {"summary": ""})
print(json.dumps(tree | {"summary": prose["summary"]}))
