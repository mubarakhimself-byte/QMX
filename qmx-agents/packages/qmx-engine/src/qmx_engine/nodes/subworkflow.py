"""The `subworkflow` node (SOLUTION-DESIGN 3.5): one nested run with its own `run_id`, its
`parent_run_id` and `call_depth`.

`parameters.workflow` names the child's folder inside the parent's folder. With `wait` (the
default) the node ends with the child: its outputs on `main` when it passed, a failure otherwise.
With `wait: false` the node hands on `{"run_id": ...}` at once and the child runs beside the
parent. The child's `settings.caller_policy` is checked here, at dispatch: `none` refuses every
caller, and `any` and `workflows_only` both admit a parent workflow. A child deeper than the
`subworkflow.max_depth` setting is refused. The child's run id is the attempt's idempotency key,
so a rerun of one attempt can never start a second child.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from pydantic import JsonValue

from qmx_engine.definition.model import Workflow
from qmx_engine.definition.validate import checked
from qmx_engine.nodes.base import NodeJob, NodeResult, Ok
from qmx_engine.nodes.script import failed

if TYPE_CHECKING:
    from qmx_engine.runner import Outcome


class Launch(Protocol):
    def __call__(
        self, root: Path, workflow: Workflow, inputs: JsonValue, run_id: str
    ) -> Awaitable[Outcome]: ...


class Subworkflow:
    def __init__(
        self,
        folder: Path,
        *,
        depth: int,
        max_depth: int,
        launch: Launch,
        spawn: Callable[[Awaitable[Outcome]], None],
    ) -> None:
        """`depth` is the calling run's `call_depth`; `spawn` keeps a child the node does not wait
        for running until the root run ends."""
        self.folder = folder
        self.depth = depth
        self.max_depth = max_depth
        self.launch = launch
        self.spawn = spawn

    async def run(self, job: NodeJob) -> NodeResult:
        parameters = job.node_definition.get("parameters")
        parameters = parameters if isinstance(parameters, dict) else {}
        if self.depth + 1 > self.max_depth:
            return failed(
                "call_depth_exceeded",
                f"a child at depth {self.depth + 1} passes the ceiling {self.max_depth}",
                retryable=False,
            )
        ref = parameters.get("workflow")
        root = self.folder.resolve()
        child = (root / ref).resolve() if isinstance(ref, str) else root
        if child == root or not child.is_relative_to(root):
            return failed(
                "subworkflow_missing",
                "parameters.workflow names no folder inside this one",
                retryable=False,
            )
        found = checked(child)
        if isinstance(found, list):
            codes = " ".join(sorted({p.code for p in found}))
            return failed(
                "subworkflow_invalid", f"the child does not run: {codes}", retryable=False
            )
        _, workflow = found
        if workflow.settings.caller_policy == "none":
            return failed(
                "caller_refused", "the child's caller_policy admits no caller", retryable=False
            )
        inputs: JsonValue = job.inputs.get("in") if isinstance(job.inputs, dict) else None
        run_id = job.idempotency_key.replace(":", ".")
        outcome = self.launch(child, workflow, inputs, run_id)
        if parameters.get("wait") is False:
            self.spawn(outcome)
            return Ok({"main": {"run_id": run_id}})
        ended = await outcome
        if ended.status != "passed":
            return failed(
                "subworkflow_failed",
                f"child run {run_id} ended {ended.status}: {ended.reason}",
                retryable=False,
            )
        return Ok({"main": {"run_id": run_id, "outputs": ended.outputs}})
