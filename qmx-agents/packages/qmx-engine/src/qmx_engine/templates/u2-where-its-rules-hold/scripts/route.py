"""Where the run goes, and the contexts QMB tries. Zero tokens.

It prints `recorded`, the fixture a test run replays (null otherwise); `sweep`, the unit's pin and
window with a grid of the markets he names, each traded alone; and `whatif`, one `session_hours`
scenario per session he names (UTC hours), or null when he names none. QMB counts every market
cell and every `session_hours` scenario as a try in the unit's family, so the best context is
judged against every context that was looked at. Session hours come from him, never from a
clock written here.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
base = {"unit": given["unit"], "window": given["window"]}
sessions = given.get("sessions") or []
whatif = None
if sessions:
    scenarios = [{"name": "session_hours", "params": {"from": s["from"], "to": s["to"]}} for s in sessions]
    whatif = base | {"scenarios": scenarios}
print(
    json.dumps(
        {
            "recorded": given.get("fixture"),
            "sweep": base | {"grid": {"markets": given["markets"]}},
            "whatif": whatif,
        }
    )
)
