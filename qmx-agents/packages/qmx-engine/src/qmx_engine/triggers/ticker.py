"""The in-process ticker (AD-10, SOLUTION-DESIGN 4.2): every `scheduler.tick` seconds it renews its
leases, resumes the paused runs whose wake has come (AD-9), and claims what is due.

Each claimed fire runs as its own task, so a tick never waits on a run. A fire's path is: the
pinned version must be enabled; preflight (`triggers.preflight`); a closed usage window holds it
(`triggers.quota`); the trigger's `monitor` precheck ends it `silent` when its source hash is
unchanged; otherwise one live run starts with the trigger's inputs, the trigger's last successful
outputs when `continuity` is on, and an `after` trigger's upstream outputs, on the trigger's role
and effort pins (B-60). A run that finishes passed fires every `after` trigger on its workflow
(`service.runs.fire_after`). A wake resumes any run held with a `resume_at`: a usage limit, a time
`wait` or a retry backoff (AD-10). A fire whose run is cancelled ends `cancelled` at once (L-69),
and `run_now` answers what became of the fire it asked for (B-72).
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import secrets
from collections.abc import Collection, Coroutine
from dataclasses import dataclass
from datetime import timedelta
from typing import Final

from pydantic import ValidationError

from qmx_engine.definition.model import Workflow
from qmx_engine.ledger.store import Reader
from qmx_engine.nodes.base import Failed, NodeJob, Ok
from qmx_engine.nodes.monitor import Monitor
from qmx_engine.nodes.script import HostScript
from qmx_engine.ports.inbox import Category, Raise
from qmx_engine.ports.library import Bundle, LibraryRefused, Stored
from qmx_engine.runner import Engine, Outcome, new_run_id, workspace
from qmx_engine.runner import Refused as EngineRefused
from qmx_engine.service.context import Caller, Context
from qmx_engine.service.runs import Runs, fire_after, run_bundle, summarize_again
from qmx_engine.triggers.claims import (
    Claimed,
    Lease,
    claim_due,
    claim_wakes,
    end_wake,
    heartbeat,
    hold,
    settle,
    settle_run,
    start,
)
from qmx_engine.triggers.preflight import Blocked, preflight
from qmx_engine.triggers.quota import closed_until
from qmx_engine.triggers.rows import (
    HERE,
    Fire,
    FireStatus,
    HomeEngine,
    JsonObject,
    Trigger,
    fire_now,
    fires,
    triggers,
)

ENDING: Final[dict[str, FireStatus]] = {
    "passed": "ok",
    "failed": "failed",
    "waiting": "waiting",
    "interrupted": "unknown",
    "stopped": "cancelled",
}


def pins(trigger: Trigger) -> JsonObject:
    found: JsonObject = {}
    if trigger.role_pins:
        found["roles"] = trigger.role_pins
    if trigger.effort_pin is not None:
        found["effort"] = trigger.effort_pin
    return found


def unclaimed(trigger: Trigger, live: int, home: HomeEngine, *, claiming: bool) -> str:
    """Why a pending fire was not claimed on this tick."""
    if not claiming:
        return "the engine stopped claiming work after a ledger write error"
    if not trigger.enabled:
        return "the trigger is disabled"
    if trigger.home_engine != home:
        return f"the trigger runs on {trigger.home_engine}, not on this engine ({home})"
    if live >= trigger.max_concurrent:
        return f"the trigger already runs {live} of max_concurrent {trigger.max_concurrent} fires"
    return "the fire waits for the next tick"


def caller_of(principal: str) -> Caller:
    kind, _, own = principal.partition(":")
    return Caller("agent", own) if kind == "agent" else Caller("user")


@dataclass(frozen=True, slots=True)
class Tick:
    claimed: tuple[Claimed, ...]
    woken: tuple[str, ...]


class Scheduler:
    def __init__(
        self,
        ctx: Context,
        *,
        claimant: str | None = None,
        home: HomeEngine = HERE,
        credentials: Collection[str] | None = None,
        skills: Collection[str] | None = None,
    ) -> None:
        """`credentials` and `skills` are the inventories preflight checks against, by name;
        None leaves that check out."""
        self.ctx = ctx
        self.claimant = claimant or f"{home}:{os.getpid()}:{secrets.token_hex(3)}"
        self.home: HomeEngine = home
        self.credentials = credentials
        self.skills = skills
        self.fires: dict[str, asyncio.Task[None]] = {}
        self.waking: dict[str, asyncio.Task[None]] = {}
        self.workflows: dict[str, Workflow | None] = {}
        """Parsed workflows by object id; a published object never changes."""

    @property
    def engine(self) -> Engine:
        return self.ctx.engine

    def setting(self, key: str, default: float) -> float:
        found = self.engine.settings.get(key)
        return float(found) if isinstance(found, int | float) else default

    def lease(self) -> Lease:
        return Lease(
            self.claimant, self.ctx.clock.now(), self.setting("scheduler.lease_seconds", 300)
        )

    async def tick(self) -> Tick:
        if not self.engine.claiming:
            return Tick((), ())
        ledger = self.engine.ledger
        lease = self.lease()
        ledger.write(heartbeat(lease, list(self.fires), list(self.waking)))
        woken = ledger.write(claim_wakes(lease, set(self.waking)))
        for run_id, reset in woken:
            self._spawn(self.waking, run_id, self._wake(run_id, reset))
        grace = timedelta(seconds=self.setting("scheduler.grace", 900))
        claimed = ledger.write(claim_due(lease, grace=grace, home=self.home, busy=set(self.fires)))
        for found in claimed:
            self._spawn(self.fires, found.fire.id, self._fire(found))
        return Tick(tuple(claimed), tuple(run_id for run_id, _ in woken))

    async def serve(self, stop: asyncio.Event) -> None:
        """Tick until `stop` is set, then wait for the fires and wakes in flight."""
        every = self.setting("scheduler.tick", 60)
        while not stop.is_set():
            await self.tick()
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=every)
        await self.settle()

    async def settle(self) -> None:
        while self.fires or self.waking:
            await asyncio.gather(*self.fires.values(), *self.waking.values())

    def _spawn(
        self, tasks: dict[str, asyncio.Task[None]], key: str, work: Coroutine[None, None, None]
    ) -> None:
        task = asyncio.create_task(work)
        tasks[key] = task
        task.add_done_callback(lambda _: tasks.pop(key, None))

    async def _wake(self, run_id: str, reset: str) -> None:
        ledger = self.engine.ledger
        try:
            outcome = await self.engine.resume(run_id, reason="wake", woke=reset)
        except EngineRefused:
            outcome = None
        ledger.write(end_wake(run_id, self.claimant))
        if outcome is None:
            return
        summarize_again(self.ctx, outcome)
        outputs = outcome.outputs if outcome.status == "passed" else None
        ledger.write(settle_run(run_id, ENDING[outcome.status], self.ctx.at(), outputs))
        fire_after(self.ctx, outcome)

    async def _fire(self, claimed: Claimed) -> None:
        fire, trigger = claimed.fire, claimed.trigger
        ledger = self.engine.ledger
        try:
            if fire.status == "running" and fire.run_id is not None and self._exists(fire.run_id):
                outcome = await self.engine.resume(fire.run_id)
                self._ended(fire, trigger, outcome)
                fire_after(self.ctx, outcome, trigger.workflow_item)
                return
            version = self._version(trigger)
            if isinstance(version, str):
                ledger.write(settle(fire, "skipped", self.ctx.at(), detail=version))
                return
            bundle = self.ctx.library.get_object(version.object_id)
            workflow = self._workflow(version.object_id, bundle)
            if workflow is None:
                why = f"{version.object_id} does not parse"
                self._blocked(fire, trigger, Blocked("config", "not_runnable", why))
                return
            harness = self.engine.harness
            blocked = preflight(
                workflow,
                self.engine.settings,
                profiles=None if harness is None else harness.profiles(),
                credentials=self.credentials,
                skills=self.skills,
            )
            if blocked is not None:
                self._blocked(fire, trigger, blocked)
                return
            until = await closed_until(
                workflow, self.engine.settings, self.engine.harness, self.engine.admission
            )
            if until is not None:
                ledger.write(hold(fire, until))
                return
            inputs = self._inputs(fire, trigger)
            if trigger.precheck_ref is not None:
                seen = await self._precheck(trigger, workflow, bundle, fire)
                if isinstance(seen, Failed):
                    ledger.write(settle(fire, "failed", self.ctx.at(), detail=seen.message))
                    return
                if "silent" in seen.outputs:
                    ledger.write(settle(fire, "silent", self.ctx.at(), detail="unchanged"))
                    return
                inputs["precheck"] = seen.outputs.get("changed")
            run_id = fire.run_id or new_run_id(self.ctx.clock.now())
            ledger.write(start(fire.id, run_id))
            outcome, _ = await run_bundle(
                self.ctx,
                bundle,
                object_id=version.object_id,
                item=version.item,
                mode="live",
                inputs=inputs,
                subgraph=None,
                caller=caller_of(trigger.created_by),
                run_id=run_id,
                pins=pins(trigger),
            )
            self._ended(fire, trigger, outcome)
        except asyncio.CancelledError:
            task = asyncio.current_task()
            if task is not None and task.cancelling():
                raise
            ledger.write(settle(fire, "cancelled", self.ctx.at(), detail="the run was cancelled"))
        except LibraryRefused as refused:
            ledger.write(settle(fire, "blocked_config", self.ctx.at(), detail=str(refused)))
        except Exception as error:  # one broken fire must not stop the ticker
            detail = f"{type(error).__name__}: {error}"
            with contextlib.suppress(Exception):
                ledger.write(settle(fire, "failed", self.ctx.at(), detail=detail))

    def _exists(self, run_id: str) -> bool:
        with Reader.open(self.ctx.home) as reader:
            return bool(reader.events(run_id))

    def _version(self, trigger: Trigger) -> Stored | str:
        """The object a fire runs, or why it does not run: only an enabled version fires."""
        runs = Runs(self.ctx)
        state = runs.version_state(self.ctx.library.get(trigger.pinned_object))
        if state != "enabled":
            return f"the pinned version is {state}"
        return runs.pinned(trigger.pinned_object, trigger.follow_champion)

    def _workflow(self, object_id: str, bundle: Bundle) -> Workflow | None:
        if object_id not in self.workflows:
            try:
                self.workflows[object_id] = Workflow.model_validate(bundle.definition)
            except ValidationError:
                self.workflows[object_id] = None
        return self.workflows[object_id]

    def _blocked(self, fire: Fire, trigger: Trigger, blocked: Blocked) -> None:
        at = self.ctx.at()
        line = f"trigger {trigger.id} blocked_config: {blocked.message}"
        if blocked.cause == "provider":
            self.ctx.inbox.raise_item(
                Raise(
                    trigger.id,
                    blocked.signature,
                    Category.PROVIDER_FAILURE,
                    f"trigger {trigger.id} cannot fire: {blocked.code}",
                    blocked.message,
                ),
                at=at,
            )
            self.engine.ledger.write(settle(fire, "blocked_config", at, detail=blocked.code))
            return
        self.engine.ledger.write(
            settle(fire, "blocked_config", at, detail=blocked.code, digest=line)
        )

    def _inputs(self, fire: Fire, trigger: Trigger) -> JsonObject:
        found: JsonObject = {
            "trigger": {
                "id": trigger.id,
                "kind": trigger.kind,
                "fire_id": fire.id,
                "occurrence_at": fire.occurrence_at,
                "merged": fire.merged,
            }
        }
        if fire.payload:
            found |= fire.payload
        if trigger.continuity and trigger.last_outputs is not None:
            found["continuity"] = trigger.last_outputs
        return found

    async def _precheck(
        self, trigger: Trigger, workflow: Workflow, bundle: Bundle, fire: Fire
    ) -> Ok | Failed:
        root = bundle.write(self.ctx.home / "engine" / "prechecks" / trigger.pinned_object)
        zone = self.ctx.home / "engine" / "prechecks" / "zones" / fire.id
        zone.mkdir(parents=True, exist_ok=True)
        host = HostScript(
            root, self.setting("timeout.script.run", 600), self.engine.banned_values()
        )
        monitors = workspace(self.ctx.home, workflow.id) / "monitors"
        node_id = f"precheck-{trigger.id}"
        definition: JsonObject = {
            "type": "monitor",
            "parameters": {"source": trigger.precheck_ref},
        }
        job = NodeJob(
            run_id=fire.id,
            node_id=node_id,
            iteration=0,
            partition=None,
            attempt=1,
            memo_key=fire.id,
            idempotency_key=f"{fire.id}:{node_id}",
            node_definition=definition,
            inputs=None,
            now=self.ctx.at(),
            mode="live",
            workspace=str(zone),
        )
        found = await Monitor(host, monitors).run(job)
        return found if isinstance(found, Ok | Failed) else Failed("precheck", "", "", False)

    def _ended(self, fire: Fire, trigger: Trigger, outcome: Outcome) -> None:
        status = ENDING[outcome.status]
        outputs = outcome.outputs if outcome.status == "passed" else None
        detail = None if outcome.status == "passed" else outcome.reason
        self.engine.ledger.write(
            settle(fire, status, self.ctx.at(), detail=detail, outputs=outputs)
        )

    async def run_now(self, trigger_id: str) -> JsonObject:
        """Fire a trigger now and say what became of the fire: started, settled with its reason,
        or still pending and why it was not claimed (B-72)."""
        fire_id = fire_now(self.engine.ledger, trigger_id, self.ctx.clock.now(), {})
        await self.tick()
        await asyncio.sleep(0)
        with Reader.open(self.ctx.home) as reader:
            found = next(f for f in fires(reader.connection, trigger_id) if f.id == fire_id)
            trigger = triggers(reader.connection, "WHERE id = ?", trigger_id)[0]
            (live,) = reader.connection.execute(
                "SELECT count(*) FROM fires WHERE trigger_id = ? AND id != ?"
                " AND status IN ('claimed', 'running')",
                (trigger_id, fire_id),
            ).fetchone()
        detail = found.detail
        if found.status == "pending":
            detail = unclaimed(trigger, int(live), self.home, claiming=self.engine.claiming)
        return {
            "trigger_id": trigger_id,
            "fire_id": fire_id,
            "status": found.status,
            "detail": detail,
            "run_id": found.run_id,
        }
