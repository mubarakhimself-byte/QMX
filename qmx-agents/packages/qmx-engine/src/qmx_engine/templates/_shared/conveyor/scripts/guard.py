"""The `conveyor` block's one step: the loop guard of a template an `event` trigger starts.

A conveyor is a template whose `event` trigger watches a landed result (its kind, output name and
producer) and whose first step calls this block with the run's inputs. The trigger hands the run
`event`, `{"object_id", "seq", "kind", "output", "producer"}`, and the engine already fires a
trigger once per object. This step adds the guard the trigger cannot hold (WF-05): a landing made
by a run of this same conveyor, at any depth of its subworkflows, never starts it again, so a
conveyor whose stage lands what its own trigger watches carries one landing and then stands down.

A run's producer is `run:<run_id>`. The step reads that run and its own from the run ledger, each
up its `parent_run_id` chain to the run a trigger started, and compares their workflows. It
prints `go`, the `event`, and either the `intent_key` the stage lands its output under
(`<output>|<object_id>`) or `why` it stood down. The calling template routes on `go`, which
its subworkflow node hands on as `outputs.guard.main.go`.
"""

import json
import os
import sys
from pathlib import Path

from qmx_engine.ledger.store import Reader
from qmx_engine.workers.zones import home_of

FAILURE = "[QMX_FAILURE]"
RUN = "run:"


def workflow_of(reader, run_id):
    """The workflow of the run a trigger started, read up `run_id`'s parents; None when this
    ledger holds no such run."""
    seen = set()
    while run_id not in seen:
        seen.add(run_id)
        events = reader.events(run_id)
        if not events or events[0].kind != "run_created":
            return None
        created = events[0].data
        parent = created.get("parent_run_id")
        if not parent:
            return created.get("workflow_item") or created.get("workflow_id")
        run_id = str(parent)
    return None


given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
event = next((r["event"] for r in rows if isinstance(r.get("event"), dict)), None)
if event is None or not event.get("object_id"):
    print(f"{FAILURE} the conveyor needs the event its trigger handed on")
    raise SystemExit(0)

producer = str(event.get("producer") or "")
own = None
if producer.startswith(RUN):
    with Reader.open(home_of(Path(os.environ["QMX_WORK_SHARED"]))) as reader:
        mine = workflow_of(reader, os.environ["QMX_RUN_ID"])
        theirs = workflow_of(reader, producer.removeprefix(RUN))
    own = mine is not None and mine == theirs

if own:
    why = (
        f"{event['object_id']} was landed by {producer}, a run of this conveyor; "
        "a conveyor never starts on its own landing"
    )
    print(json.dumps({"go": False, "event": event, "why": why}))
else:
    named = event.get("output") or event.get("kind")
    print(json.dumps({"go": True, "event": event, "intent_key": f"{named}|{event['object_id']}"}))
