"""The checked spec's readings as a list, one builder each."""

import json
import sys

print(json.dumps(json.load(sys.stdin)["in"]["readings"]))
