"""The `trigger` node marks the entry: it passes the run's inputs out on `main`. Which trigger kinds
may bind it is the scheduler's business (EP12)."""

from __future__ import annotations

from qmx_engine.nodes.base import NodeJob, NodeResult, Ok


class Trigger:
    def run(self, job: NodeJob) -> NodeResult:
        return Ok({"main": job.inputs})
