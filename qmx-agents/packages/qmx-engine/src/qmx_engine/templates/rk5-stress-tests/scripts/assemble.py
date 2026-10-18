"""The stress report: the units x scenarios heatmap rows, the worst three with their explanation,
and the tighten-only proposals for his signature. Its inputs, the scenario results and the
analyst's read of the worst three, are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
stress = next(v for v in given if "results" in v)
read = next(v for v in given if "explanations" in v)
print(json.dumps(stress | {"explanations": read["explanations"], "proposals": read["proposals"]}))
