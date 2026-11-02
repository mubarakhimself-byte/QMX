"""A test run's stand-in for QMB: what it answered on a recorded run, read from
`fixtures/qmb.json` under the fixture's name. Zero tokens."""

import json
import os
import sys
from pathlib import Path

routed = json.load(sys.stdin)["in"]
recorded = json.loads((Path(os.environ["QMX_CODE"]) / "fixtures" / "qmb.json").read_text("utf-8"))
print(json.dumps(recorded[routed["recorded"]]))
