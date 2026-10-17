"""The `join` node. The core decides when it fires and which partitions it merges
(`qmx_engine.core.joins`); the node passes the merged list on `main`, in partition order."""

from __future__ import annotations

from qmx_engine.nodes.base import NodeJob, NodeResult, Ok


class Join:
    def run(self, job: NodeJob) -> NodeResult:
        ports = job.inputs if isinstance(job.inputs, dict) else {}
        return Ok({"main": ports.get("in")})
