"""Move the operator's cursor forward to the position this digest read, and hand the card on.

It runs only after the digest passed its check and was delivered, so a failed digest shows the same
items again rather than hiding them. The cursor never moves back."""

import json
import os
import sys
from pathlib import Path

from qmx_control.service import ControlService

from qmx_engine.workers.zones import home_of

given = json.load(sys.stdin)["in"]
card = given if isinstance(given, dict) else given[-1]
home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
service = ControlService(home)
try:
    row = service.mark_looked(int(card.get("cursor_to") or 0))
finally:
    service.close()
print(json.dumps(card | {"cursor": row}))
