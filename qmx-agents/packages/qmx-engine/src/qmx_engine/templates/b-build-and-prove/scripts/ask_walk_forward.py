"""QMB's walk-forward ask, unwrapped for the `app_op` node, which merges nothing over it."""

import json
import sys

print(json.dumps(json.load(sys.stdin)["in"]["walk_forward"]))
