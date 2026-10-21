"""The `app_op` node (AD-5, AD-19, AD-64): runs one of a mini app's operations in the app's
supervised process.

An app's scheduled job is an engine trigger on a workflow holding this node, never a schedule in
the apps supervisor (AD-57). `parameters` name the app and the job entrypoint. The attempt takes no
engine slot: the app's own job queue orders it (AD-58), and it waits there for as long as the job
runs. When the app is not running, or the job raises, the node fails with the supervisor's reason.

Two optional parameters carry the ask's pin and its profile:

- `pin = {pack, version}` is the `(pack, version)` the caller meant. A node that declares one
  dispatches through the pinned path, which revalidates the pin in the supervisor before the app
  runs, so a version that moved under a queued ask fails instead of answering as the new one.
- `profile` names the partition of the app's `data/` the run writes. One instance serves one
  profile, so a run aimed at another profile is refused rather than silently writing here.

A pinned node needs a pinned dispatcher. The control door still binds the two-argument
`app_job`, so a node that declares a pin or a profile fails with `pin_unsupported` until it binds
the supervisor's `run_job` (B-APP2A-3).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import cast

from qmx_apps.errors import AppError
from qmx_control.models import ControlError, Document

from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok

type RunJob = Callable[[str, str], Document]
"""`(app_id, job) -> what ran`: `ControlService.app_job`, which raises `ControlError`."""
type RunPinned = Callable[..., Document]
"""`(app_id, job, pin=, profile=) -> what ran`: the supervisor's `run_job`, which revalidates the
pin and refuses a run aimed at another profile."""


def _failed(code: str, message: str) -> Failed:
    return Failed(code, message, signature(code, message), retryable=False)


def _pin(value: object) -> Document | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("parameters.pin is a table of pack and version")
    declared = cast("dict[str, object]", value)
    table: Document = {}
    for key in ("pack", "version"):
        found = declared.get(key)
        if not isinstance(found, str):
            raise ValueError(f"parameters.pin.{key} is a string")
        table[key] = found
    return table


class AppOp:
    def __init__(self, run_job: RunJob, dispatch: RunPinned | None = None) -> None:
        self.run_job = run_job
        self.dispatch = dispatch

    async def run(self, job: NodeJob) -> NodeResult:
        parameters = job.node_definition.get("parameters")
        found = parameters if isinstance(parameters, dict) else {}
        app, name = found.get("app"), found.get("job")
        if not isinstance(app, str) or not isinstance(name, str):
            return _failed("app_op_refused", "parameters.app and parameters.job are strings")
        try:
            pin = _pin(found.get("pin"))
            profile = found.get("profile")
            if profile is not None and not isinstance(profile, str):
                raise ValueError("parameters.profile is a string")
            ran = await asyncio.to_thread(self._run, app, name, pin, profile)
        except ValueError as error:
            return _failed("app_op_refused", str(error))
        except (ControlError, AppError) as error:
            return _failed(error.code, str(error))
        return Ok({"main": ran})

    def _run(self, app: str, name: str, pin: Document | None, profile: str | None) -> Document:
        if pin is None and profile is None:
            return self.run_job(app, name)
        if self.dispatch is None:
            raise ControlError(
                "pin_unsupported",
                f"{app} is asked with a pin or a profile and the door binds no pinned dispatcher",
            )
        return self.dispatch(app, name, pin=pin, profile=profile)
