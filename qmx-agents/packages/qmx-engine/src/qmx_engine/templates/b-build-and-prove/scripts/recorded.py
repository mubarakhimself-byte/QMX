"""A test run's stand-in for the two QMB runs: what QMB answered on a recorded run, read from
`fixtures/qmb.json` under the fixture's name. Only a run whose inputs name a `fixture` comes here; any
other run asks QMB itself. Zero tokens.
"""

import json
import os
import sys
from pathlib import Path

ready = json.load(sys.stdin)["in"]
recorded = json.loads((Path(os.environ["QMX_CODE"]) / "fixtures" / "qmb.json").read_text("utf-8"))
print(json.dumps(recorded[ready["recorded"]]))
