"""Where the operator's last look ended: one row in control, a Library log position, never a clock.

The digest read starts at that position, so a second digest shows only what landed after the first
one (46 K-32). Before he has looked once the position is zero and the digest reads the whole log.
"""

import json
import os
import sys
from pathlib import Path

from qmx_control.service import ControlService

from qmx_engine.workers.zones import home_of

given = json.load(sys.stdin)["in"]
state = given if isinstance(given, dict) else next((v for v in given if isinstance(v, dict)), {})
home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
service = ControlService(home)
try:
    row = service.last_look()
finally:
    service.close()
print(
    json.dumps({"position": int(row["position"]), "at": row["at"], "fixture": state.get("fixture")})
)
