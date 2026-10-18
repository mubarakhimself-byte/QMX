"""The week's evidence, read from the engine's own service and ledger, never from the Library: every
run started in the last seven days (this review's own run left out) with its status, its tokens and
each failed step or failed check, and every open inbox item. A parked run is one whose status says
so. A run started with `{"fixture": true}` reads `fixtures/week.json`, a synthetic week, instead.

The run's write zone is `<home>/workspaces/wf-<id>/runs/<run_id>`, so the zone names this run and
the home is three folders above it."""

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from qmx_engine.ledger.inbox_table import InboxTable, inbox_path
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.clock import WallClock
from qmx_engine.service.inbox import Inbox
from qmx_engine.service.runs import status_of
from qmx_engine.trace_export import totals

DAYS = 7
MESSAGE_CHARS = 200

given = json.load(sys.stdin).get("in") or {}
if given.get("fixture"):
    found = json.loads((Path(__file__).parents[1] / "fixtures" / "week.json").read_text("utf-8"))
    print(json.dumps(found["week"] | {"source": "fixture"}))
    raise SystemExit(0)

home = Path.cwd().parents[3]
own = Path.cwd().name
now = datetime.now(UTC)
since = (now - timedelta(days=DAYS)).isoformat()
runs, parked, failures = [], [], []
with Reader.open(home) as reader:
    started = reader.connection.execute(
        "SELECT run_id, min(at) FROM events WHERE kind = 'run_created' GROUP BY run_id ORDER BY 2"
    ).fetchall()
    for run_id, at in started:
        if at < since or run_id == own:
            continue
        events = reader.events(run_id)
        state = status_of(events)
        workflow = str(events[0].data.get("workflow_id"))
        mode = str(events[0].data.get("mode"))
        for event in events:
            data = event.data
            if event.kind == "node_failed" or data.get("verdict") == "fail":
                failures.append(
                    {
                        "run_id": run_id,
                        "workflow": workflow,
                        "node_id": data.get("node_id"),
                        "signature": data.get("signature") or f"check {data.get('node_id')}",
                        "message": str(data.get("message") or json.dumps(data.get("outputs")))[
                            :MESSAGE_CHARS
                        ],
                    }
                )
        summed = totals(events, reader.spans(run_id))
        runs.append(
            {
                "run_id": run_id,
                "workflow": workflow,
                "mode": mode,
                "started": at,
                "status": state.status,
                "reason": state.reason,
                "tokens": summed["tokens"],
            }
        )
        if state.reason == "parked":
            why = (state.detail or "")[:MESSAGE_CHARS]
            parked.append({"run_id": run_id, "workflow": workflow, "why": why})
inbox = []
if inbox_path(home).exists():
    with InboxTable.open(home) as table:
        for item in Inbox(table, WallClock()).list(open_only=True):
            inbox.append(
                {
                    "run_id": item.run_id,
                    "category": item.category.value,
                    "title": item.title,
                    "cause": item.cause[:MESSAGE_CHARS],
                }
            )
print(
    json.dumps(
        {
            "from": since,
            "to": now.isoformat(),
            "runs": runs,
            "parked": parked,
            "failures": failures,
            "inbox": inbox,
            "source": "engine",
        }
    )
)
