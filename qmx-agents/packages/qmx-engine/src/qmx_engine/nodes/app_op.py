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

`inputs` tells the job what to do (Level 0 AD-33 change 1): a table merged over the node's `in`
port value when that is a table. The job's `result` comes back on `main`, and the run is the
principal the app's log records. A node without `inputs` calls the two-argument runner exactly as
before, so a job asked by name alone sees nothing new.

Where the operation runs is `Placements` (AD-64). An operation declaring `state: none` starts the
app lazily on the caller's machine from its pinned bundle. One declaring `state: instance` belongs
to the app instance's home: when the home is this machine it runs here, and when the home is
another machine the node asks that home through `remote`. An unreachable home is never a failure;
the node waits `placement` and the core resumes it, because the home can come back.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import cast

from pydantic import JsonValue
from qmx_apps.errors import AppError
from qmx_control.models import ControlError, Document

from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok, Waiting

type RunJob = Callable[[str, str], Document]
"""`(app_id, job) -> what ran`: `ControlService.app_job`, which raises `ControlError`."""
type RunPinned = Callable[..., Document]
"""`(app_id, job, pin=, profile=) -> what ran`: the supervisor's `run_job`, which revalidates the
pin and refuses a run aimed at another profile. A node with inputs adds `inputs=` and
`principal=`."""

PLACEMENT_RETRY_SECONDS = 60
"""How long a node waits before it asks an unreachable home again (Claude's default). The home's
return is what resumes it, and nothing on the calling machine watches for that yet."""


@dataclass(frozen=True, slots=True)
class Placements:
    """Where the app instances this node may call live, as the calling machine sees them (AD-64).

    `state_of(app, op)` is the operation's declared `state`; `home_of(app)` is the one placement
    that owns its volume; `here` is this machine; `reachable(placement)` says whether this machine
    can reach it now. `lazy` starts an app on this machine from its pinned bundle for a `state:
    none` operation, and `remote` sends an ask to another placement's home."""

    state_of: Callable[[str, str], str]
    home_of: Callable[[str], str]
    here: str
    reachable: Callable[[str], bool]
    lazy: Callable[[str, Document | None], Document] | None = None
    remote: Callable[..., Document] | None = None
    """`(placement, app, job, pin, profile) -> what ran`, with the inputs as a sixth argument
    only when the node carries some."""


def _failed(code: str, message: str) -> Failed:
    return Failed(code, message, signature(code, message), retryable=False)


def _waiting(seconds: int = PLACEMENT_RETRY_SECONDS) -> Waiting:
    resume = datetime.now(UTC) + timedelta(seconds=seconds)
    return Waiting("placement", resume_at=resume.isoformat(), span={"reason": "placement"})


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


def _inputs(declared: object, ports: JsonValue) -> Document | None:
    """`parameters.inputs` merged over the `in` port's table; None when the node declares none."""
    if declared is None:
        return None
    if not isinstance(declared, dict):
        raise ValueError("parameters.inputs is a table")
    given = ports.get("in") if isinstance(ports, dict) else None
    if given is not None and not isinstance(given, dict):
        raise ValueError("the in port carries a table for parameters.inputs to merge over")
    upstream = cast(Document, given or {})
    return {**upstream, **cast(Document, declared)}


@dataclass(frozen=True, slots=True)
class Ask:
    """One `app_op` attempt: which job of which app, pinned how, told what, by which run."""

    app: str
    job: str
    pin: Document | None
    profile: str | None
    inputs: Document | None
    run_id: str


class AppOp:
    def __init__(
        self,
        run_job: RunJob,
        dispatch: RunPinned | None = None,
        placements: Placements | None = None,
    ) -> None:
        self.run_job = run_job
        self.dispatch = dispatch
        self.placements = placements

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
            ask = Ask(app, name, pin, profile, _inputs(found.get("inputs"), job.inputs), job.run_id)
            routed = await asyncio.to_thread(self._route, ask)
        except ValueError as error:
            return _failed("app_op_refused", str(error))
        except (ControlError, AppError) as error:
            return _failed(error.code, str(error))
        if isinstance(routed, Waiting):
            return routed
        return Ok({"main": routed})

    def _route(self, ask: Ask) -> Document | Waiting:
        """Run the operation where its declared `state` says it belongs (AD-64)."""
        if self.placements is None:
            return self._run(ask)
        here = self.placements.here
        home = self.placements.home_of(ask.app)
        state = self.placements.state_of(ask.app, ask.job)
        if state == "instance":
            if home == here:
                return self._run(ask)
            if not self.placements.reachable(home):
                return _waiting()
            if self.placements.remote is None:
                raise AppError(
                    "placement_unreachable",
                    f"{ask.app} is homed on {home} and this engine holds no door to it",
                    409,
                )
            sent = (home, ask.app, ask.job, ask.pin, ask.profile)
            return self.placements.remote(*sent, *(() if ask.inputs is None else (ask.inputs,)))
        if self.placements.lazy is not None:
            self.placements.lazy(ask.app, ask.pin)
        return self._run(ask)

    def _run(self, ask: Ask) -> Document:
        if ask.pin is None and ask.profile is None and ask.inputs is None:
            return self.run_job(ask.app, ask.job)
        if self.dispatch is None:
            raise ControlError(
                "pin_unsupported",
                f"{ask.app} is asked with a pin, a profile or inputs and the door binds no "
                "pinned dispatcher",
            )
        if ask.inputs is None:
            return self.dispatch(ask.app, ask.job, pin=ask.pin, profile=ask.profile)
        return self.dispatch(
            ask.app,
            ask.job,
            pin=ask.pin,
            profile=ask.profile,
            inputs=ask.inputs,
            principal=f"run:{ask.run_id}",
        )
