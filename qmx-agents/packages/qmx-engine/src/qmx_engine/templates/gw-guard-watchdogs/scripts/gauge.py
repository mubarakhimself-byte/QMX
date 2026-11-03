"""Lands the gauge the monitor found changed, as one `node-watch` artifact on the run's own ref,
and hands it on to the land step with what changed since the last gauge.

Its input is the monitor's `changed` port: the read step's output as `value` and the change as
`diff`. The window is the lookback the read step used, ending at the run's own clock.
"""

import importlib.util
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

given = json.load(sys.stdin)["in"]
read = given["value"]
findings = read["findings"]
end = door.now()
start = end - timedelta(hours=float(findings["lookback_h"]))
window = {"start": door.iso(start), "end": door.iso(end)}
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "findings.json").write_text(json.dumps(findings, sort_keys=True), encoding="utf-8")
print(
    json.dumps(
        read
        | {
            "window": window,
            "changes": given.get("diff"),
            "library": [
                {
                    "op": "put_artifact",
                    "type": "node-watch",
                    "body": "library/findings.json",
                    "metadata": findings | {"window": window},
                    "intent_key": f"node-watch|{window['end']}",
                }
            ],
        }
    )
)
