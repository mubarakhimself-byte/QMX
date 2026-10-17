"""The `loop` node. The core decides each iteration's stop from the ledger
(`qmx_engine.core.loops`) and passes it in as `stop`; the node sends the value on `body` to run
the body once more, or on `done` once a stop fired."""

from __future__ import annotations

from qmx_engine.nodes.base import NodeJob, NodeResult, Ok


class Loop:
    def run(self, job: NodeJob) -> NodeResult:
        ports = job.inputs if isinstance(job.inputs, dict) else {}
        return Ok({"done" if ports.get("stop") else "body": ports.get("in")})
