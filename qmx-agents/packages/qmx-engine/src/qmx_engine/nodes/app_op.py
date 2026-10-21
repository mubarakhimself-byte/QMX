"""The `app_op` node (AD-5, AD-19): runs one of a mini app's jobs in the app's supervised process.

An app's scheduled job is an engine trigger on a workflow holding this node, never a schedule in
the apps supervisor (AD-57). `parameters` name the app and the job entrypoint. The attempt takes no
engine slot: the app's own job queue orders it (AD-58), and it waits there for as long as the job
runs. When the app is not running, or the job raises, the node fails with the supervisor's reason.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from qmx_control.models import ControlError, Document

from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok

type RunJob = Callable[[str, str], Document]
"""`(app_id, job) -> what ran`: `ControlService.app_job`, which raises `ControlError`."""


def _failed(code: str, message: str) -> Failed:
    return Failed(code, message, signature(code, message), retryable=False)


class AppOp:
    def __init__(self, run_job: RunJob) -> None:
        self.run_job = run_job

    async def run(self, job: NodeJob) -> NodeResult:
        parameters = job.node_definition.get("parameters")
        found = parameters if isinstance(parameters, dict) else {}
        app, name = found.get("app"), found.get("job")
        if not isinstance(app, str) or not isinstance(name, str):
            return _failed("app_op_refused", "parameters.app and parameters.job are strings")
        try:
            ran = await asyncio.to_thread(self.run_job, app, name)
        except ControlError as error:
            return _failed(error.code, str(error))
        return Ok({"main": ran})
