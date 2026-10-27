"""Read the replays of the agent step this template is crystallising.

Each replay is one item the agent labelled: `item_id`, the `title` the agent saw and the `label` it
gave. Twenty or more replays are what an equivalence check needs before a script may replace the
agent (K-19).

The replays are the step's own outputs in real runs of the workflow: every `node_finished` of the
`node` input in the runs of the `workflow` item's published version (the runner serves that
version as `library.version`), read from the run ledger. A run counts only when it was `live`, on
real models and `passed`; a fake or test run's canned answers are left out and counted. With no
replay the step refuses rather than learning from samples. Only a run whose `fixture` input is set
reads the shipped fixture replays.
"""

import json
import os
import sys
from pathlib import Path

from qmx_engine.ledger.store import Reader
from qmx_engine.workers.zones import home_of

FAILURE = "[QMX_FAILURE]"
SHAPE = ("item_id", "title", "label")


def refuse(why):
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


def labelled(value):
    """The `{item_id, title, label}` rows one output holds, or None when it holds anything else."""
    rows = value if isinstance(value, list) else [value]
    if rows and all(isinstance(row, dict) and all(key in row for key in SHAPE) for row in rows):
        return [{key: row[key] for key in SHAPE} for row in rows]
    return None


def real_replays(workflow, node, content_hash):
    """The step's labelled outputs in the version's live passed runs on real models, and how many
    fake or test runs of the version were left out."""
    replays, left_out = [], 0
    with Reader.open(home_of(Path(os.environ["QMX_WORK_SHARED"]))) as reader:
        made = reader.connection.execute(
            "SELECT run_id, data FROM events WHERE kind = 'run_created'"
        ).fetchall()
        for run_id, data in made:
            created = json.loads(data)
            if created.get("content_hash") != content_hash:
                continue
            if created.get("workflow_item") not in (None, workflow):
                continue
            if created.get("fake") is True or created.get("mode") != "live":
                left_out += 1
                continue
            events = reader.events(str(run_id))
            ended = [e for e in events if e.kind == "run_finished"]
            if not ended or ended[-1].data.get("status") != "passed":
                continue
            for event in events:
                if event.kind != "node_finished" or event.data.get("node_id") != node:
                    continue
                rows = labelled((event.data.get("outputs") or {}).get("main"))
                if rows is None:
                    refuse(f"step {node} outputs are not {{item_id, title, label}}")
                replays += rows
    return replays, left_out


payload = json.load(sys.stdin)
given = payload["in"]
state = given if isinstance(given, dict) else next((v for v in given if isinstance(v, dict)), {})
if state.get("fixture"):
    root = Path(__file__).parents[1]
    replays = json.loads((root / "fixtures" / "replays.json").read_text("utf-8"))
else:
    workflow, node = state.get("workflow"), state.get("node")
    if not workflow or not node:
        refuse("name the workflow and the agent step to crystallise")
    version = (payload.get("library") or {}).get("version")
    if not version:
        refuse(f"{workflow} has no published version")
    replays, left_out = real_replays(workflow, node, version.get("content_hash"))
    if not replays:
        refuse(f"no replays yet ({left_out} fake or test runs left out)")
print(
    json.dumps(
        {
            "fixture": state.get("fixture"),
            "replays": replays,
            "count": len(replays),
            "labels": sorted({replay["label"] for replay in replays}),
        }
    )
)
