"""The `monitor` node: a cheap source script prints what it sees as JSON, and the node compares
its hash with the one the previous run of this workflow saw. A new hash fires `changed` with the
value and the diff; the same hash ends `silent`, so nothing on `changed` starts.

The last hash is kept per workflow, node and mode in the workflow's workspace, outside any run's
write zone, so a test run never moves a live run's monitor.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import JsonValue
from qmx_ledger.journal import fingerprint

from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok
from qmx_engine.nodes.script import HostScript

type JsonObject = dict[str, JsonValue]


def diff(before: JsonValue, after: JsonValue) -> JsonObject:
    """Changed top-level keys of two objects; a list under a key also says what it gained and
    lost. Anything else is a plain before and after."""
    if not isinstance(before, dict) or not isinstance(after, dict):
        return {"before": before, "after": after}
    changed: JsonObject = {}
    for key in sorted(before.keys() | after.keys()):
        old, new = before.get(key), after.get(key)
        if old == new:
            continue
        entry: JsonObject = {"before": old, "after": new}
        if isinstance(old, list) and isinstance(new, list):
            entry["added"] = [item for item in new if item not in old]
            entry["removed"] = [item for item in old if item not in new]
        changed[key] = entry
    return changed


class Monitor:
    def __init__(self, host: HostScript, state: Path) -> None:
        """`state` is the folder holding one `<node_id>.<mode>.json` per monitor."""
        self.host = host
        self.state = state

    async def run(self, job: NodeJob) -> NodeResult:
        seen = await self.host.run(job, "source")
        if isinstance(seen, Failed):
            return seen
        digest = fingerprint(seen)
        path = self.state / f"{job.node_id}.{job.mode}.json"
        last: JsonObject = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        if last.get("hash") == digest:
            return Ok({"silent": {"hash": digest}})
        self.state.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"hash": digest, "value": seen}), encoding="utf-8")
        return Ok({"changed": {"value": seen, "diff": diff(last.get("value"), seen)}})
