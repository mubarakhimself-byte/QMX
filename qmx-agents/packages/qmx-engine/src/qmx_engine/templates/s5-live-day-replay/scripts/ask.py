"""The replay QMB runs, unwrapped for the `app_op` node, which merges nothing over it."""

import json
import sys

print(json.dumps(json.load(sys.stdin)["in"]["replay_check"]))
