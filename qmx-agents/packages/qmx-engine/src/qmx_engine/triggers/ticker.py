"""The in-process ticker (AD-10, SOLUTION-DESIGN 4.2): every `scheduler.tick` seconds it renews its
leases, resumes the paused runs whose wake has come (AD-9), and claims what is due.

A tick first reads the Library ref log once and queues the fires the enabled `event` triggers owe
(`triggers.event`, AD-64), then claims, so a landing fires within the same tick and a burst inside
one tick collapses without a queue at all.

Each claimed fire runs as its own task, so a tick never waits on a run. A tick starts its fires in
priority order, then oldest first, and each run carries its fire's priority into the capacity
queue (AD-58); `ready_by` raises it as the deadline nears (`rows.priority_at`). A fire's path is:
the pinned version must be enabled; preflight (`triggers.preflight`); a closed usage window holds
it (`triggers.quota`); the `market_open` precheck holds it while the market is shut; the trigger's
`monitor` precheck ends it `silent` when its source hash is unchanged; otherwise one live run
starts with the trigger's inputs, the trigger's last successful outputs when `continuity` is on,
and an `after` trigger's upstream outputs, on the trigger's role and effort pins (B-60). A run that
finishes passed fires every `after` trigger on its workflow (`service.runs.fire_after`). A wake
resumes any run held with a `resume_at`: a usage limit, a time `wait`, a retry backoff or the
pause flag (AD-10). A fire whose run is cancelled ends `cancelled` at once (L-69), and `run_now`
answers what became of the fire it asked for (B-72).

While `autonomy.paused` is set the ticker only renews its leases and its heartbeat: it claims no
fire and no wake, so clearing the flag gives each clocked trigger at most one catch-up fire
(`triggers.catchup`) and resumes every run the flag held (AD-65).

A failed fire always delivers: it ends with a `[QMX_FAILURE]` digest line and counts on the
trigger's incident for its masked signature (`InboxTable.incident`); a passing fire resolves the
incident. A failure that spent nothing, no model tokens and no finished node with an effect, is
re-run as a held fire at each `triggers.rerun_delays` after the first failure. A passed run with an
empty payload fails its delivery closed. The ticker writes its heartbeat to the ledger's `meta` row
`ticker_heartbeat` every tick, which `explain_trigger` reads.

A trigger's own check script runs in a zone outside the home, as a run's scripts do (AD-24), and
the zone is removed when the check ends.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import secrets
from collections.abc import Collection, Coroutine
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final, cast

from pydantic import ValidationError

from qmx_engine.definition.model import Workflow
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.heartbeat import INTERVAL_S, host_kinds
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Operation, Reader, Transaction
from qmx_engine.nodes.base import Failed, NodeJob, Ok
from qmx_engine.nodes.monitor import Monitor
from qmx_engine.nodes.script import FAILURE, HostScript
from qmx_engine.ports.inbox import Category, Raise
from qmx_engine.ports.library import Bundle, LibraryRefused, Stored
from qmx_engine.runner import Engine, Outcome, new_run_id, workspace
from qmx_engine.runner import Refused as EngineRefused
from qmx_engine.service.context import Caller, Context, Refused
from qmx_engine.service.explain import TriggerFacts, explain_trigger
from qmx_engine.service.runs import Runs, fire_after, run_bundle, summarize_again
from qmx_engine.triggers.claims import (
    Claimed,
    Lease,
    claim_due,
    claim_wakes,
    end_wake,
    heartbeat,
    hold,
    rerun,
    settle,
    start,
)
from qmx_engine.triggers.cron import instant, stamp
from qmx_engine.triggers.event import drain
from qmx_engine.triggers.preflight import (
    MARKET_OPEN,
    Blocked,
    market_shut_until,
    placement_wait,
    preflight,
    quarantined_input,
)
from qmx_engine.triggers.quota import closed_until
from qmx_engine.triggers.rows import (
    FIRE_COLUMNS,
    HERE,
    Delivered,
    Fire,
    FireStatus,
    HomeEngine,
    JsonObject,
    Trigger,
    deliver,
    fire_now,
    fire_of,
    fires,
    priority_at,
    triggers,
)
from qmx_engine.workers.zones import RunZone, remove

ENDING: Final[dict[str, FireStatus]] = {
    "passed": "ok",
    "failed": "failed",
    "waiting": "waiting",
    "interrupted": "unknown",
    "stopped": "cancelled",
}
HEARTBEAT: Final = "ticker_heartbeat"


def pins(trigger: Trigger) -> JsonObject:
    found: JsonObject = {}
    if trigger.role_pins:
        found["roles"] = trigger.role_pins
    if trigger.effort_pin is not None:
        found["effort"] = trigger.effort_pin
    return found


def unclaimed(
    trigger: Trigger, live: int, home: HomeEngine, *, claiming: bool, paused: bool
) -> str:
    """Why a pending fire was not claimed on this tick."""
    if not claiming:
        return "the engine stopped claiming work after a ledger write error"
    if paused:
        return "autonomy.paused is set: no fire is claimed on this host until it is cleared"
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


def beat(lease: Lease, fire_ids: list[str], run_ids: list[str]) -> Operation[None]:
    """Renew this claimant's leases and record the ticker's heartbeat, in one write."""
    renew = heartbeat(lease, fire_ids, run_ids)

    def operation(txn: Transaction) -> None:
        renew(txn)
        txn.connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)"
            " ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (HEARTBEAT, lease.at),
        )

    return operation


def mark_incident(trigger_id: str, incident_id: str | None) -> Operation[None]:
    def operation(txn: Transaction) -> None:
        txn.connection.execute(
            "UPDATE triggers SET incident_id = ? WHERE id = ?", (incident_id, trigger_id)
        )

    return operation


def delivered(trigger: Trigger, status: FireStatus, outputs: JsonObject | None) -> Delivered | None:
    """A fire's delivery from how it ended: an empty payload fails closed."""
    if status == "silent" or (status == "ok" and trigger.delivery == "silent"):
        return "none"
    if status == "ok":
        return "delivered" if outputs else "failed"
    return None


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

    @property
    def incidents(self) -> InboxTable:
        inbox = self.engine.inbox
        return inbox if isinstance(inbox, InboxTable) else InboxTable.open(self.ctx.home)

    def setting(self, key: str, default: float) -> float:
        found = self.engine.settings.get(key)
        return float(found) if isinstance(found, int | float) else default

    def lease(self) -> Lease:
        return Lease(
            self.claimant, self.ctx.clock.now(), self.setting("scheduler.lease_seconds", 300)
        )

    def priority(self, fire: Fire, trigger: Trigger, now: datetime) -> int:
        window = self.setting("triggers.ready_by_window", 3600)
        return priority_at(trigger, instant(fire.occurrence_at), now, window)

    async def tick(self) -> Tick:
        if not self.engine.claiming:
            return Tick((), ())
        ledger = self.engine.ledger
        lease = self.lease()
        ledger.write(beat(lease, list(self.fires), list(self.waking)))
        drain(
            ledger,
            self.ctx.library,
            home=self.ctx.home,
            engine=self.home,
            now=self.ctx.clock.now(),
            paused=self.engine.paused,
        )
        if self.engine.paused:
            return Tick((), ())
        woken = ledger.write(claim_wakes(lease, set(self.waking)))
        for run_id, reset in woken:
            self._spawn(self.waking, run_id, self._wake(run_id, reset))
        grace = timedelta(seconds=self.setting("scheduler.grace", 900))
        claimed = ledger.write(claim_due(lease, grace=grace, home=self.home, busy=set(self.fires)))
        claimed.sort(
            key=lambda c: (-self.priority(c.fire, c.trigger, lease.now), c.fire.occurrence_at)
        )
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
        held = self._fire_of_run(run_id)
        if held is not None:
            self._ended(*held, outcome)
        fire_after(self.ctx, outcome)

    def _fire_of_run(self, run_id: str) -> tuple[Fire, Trigger] | None:
        with Reader.open(self.ctx.home) as reader:
            row = reader.connection.execute(
                f"SELECT {FIRE_COLUMNS} FROM fires WHERE run_id = ?"  # noqa: S608
                " AND status IN ('waiting', 'claimed', 'running')",
                (run_id,),
            ).fetchone()
            if row is None:
                return None
            fire = fire_of(row)
            return fire, triggers(reader.connection, "WHERE id = ?", fire.trigger_id)[0]

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
            ) or quarantined_input(version.object_id, self.ctx.library)
            if blocked is not None:
                self._blocked(fire, trigger, blocked)
                return
            waits = placement_wait(workflow, host_kinds(self.ctx.home))
            if waits is not None:
                beat = timedelta(seconds=self.setting("heartbeat.interval", INTERVAL_S))
                ledger.write(hold(fire, stamp(self.ctx.clock.now() + beat), waits))
                return
            until = await closed_until(
                workflow, self.engine.settings, self.engine.harness, self.engine.admission
            )
            if until is not None:
                ledger.write(hold(fire, until))
                return
            inputs = self._inputs(fire, trigger)
            if trigger.precheck_ref == MARKET_OPEN:
                shut = market_shut_until(self.ctx.clock.now(), trigger.zone, self._holidays())
                if shut is not None:
                    ledger.write(hold(fire, stamp(shut), f"the market is shut in {trigger.zone}"))
                    return
            elif trigger.precheck_ref is not None:
                seen = await self._precheck(trigger, workflow, bundle, fire)
                if isinstance(seen, Failed):
                    self._failed(fire, trigger, seen.code, seen.message, None)
                    return
                if "silent" in seen.outputs:
                    ledger.write(
                        settle(fire, "silent", self.ctx.at(), detail="unchanged", delivery="none")
                    )
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
                priority=self.priority(fire, trigger, self.ctx.clock.now()),
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
            with contextlib.suppress(Exception):
                self._failed(fire, trigger, type(error).__name__, str(error), fire.run_id)

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

    def _holidays(self) -> tuple[str, ...]:
        found = self.engine.settings.get("market.holidays")
        days = cast(tuple[object, ...], found) if isinstance(found, tuple) else ()
        return tuple(str(day) for day in days)

    def _blocked(self, fire: Fire, trigger: Trigger, blocked: Blocked) -> None:
        at = self.ctx.at()
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
        self._failed(fire, trigger, blocked.code, blocked.message, None, "blocked_config")

    def _failed(
        self,
        fire: Fire,
        trigger: Trigger,
        code: str,
        message: str,
        run_id: str | None,
        status: FireStatus = "failed",
    ) -> None:
        """End the fire with its `[QMX_FAILURE]` line, count it on the trigger's incident, and
        hold a re-run when the failure spent nothing."""
        at = self.ctx.at()
        line = f"{FAILURE} trigger {trigger.id} {code}: {message}"
        ledger = self.engine.ledger
        ledger.write(settle(fire, status, at, detail=message, digest=line, delivery="delivered"))
        incident = self.incidents.incident(
            trigger.id,
            signature(code, message),
            f"trigger {trigger.id} failed: {code}",
            message,
            at=at,
        )
        ledger.write(mark_incident(trigger.id, incident))
        found = self.engine.settings.get("triggers.rerun_delays")
        listed = cast(tuple[object, ...], found) if isinstance(found, tuple) else ()
        delays = [float(d) for d in listed if isinstance(d, int | float)]
        if fire.rerun >= len(delays) or not self._neutral(run_id):
            return
        first = self._first_failure(fire) or self.ctx.clock.now()
        until = first + timedelta(seconds=delays[fire.rerun])
        ledger.write(rerun(fire, stamp(until)))

    def _neutral(self, run_id: str | None) -> bool:
        """Whether a failed fire's run spent nothing: no model tokens, and no node with an effect
        finished, so a re-run repeats no outside act (41 M5)."""
        if run_id is None:
            return True
        try:
            events, _, workflow = self.engine.load(run_id)
        except EngineRefused:
            return False
        with Reader.open(self.ctx.home) as reader:
            spans = reader.spans(run_id)
        kinds = {n.id: REGISTRY.kind(n.type) for n in workflow.nodes}
        acted = {
            str(e.data.get("node_id"))
            for e in events
            if e.kind == "node_finished" and e.data.get("memo") is not True
        }
        effects = [kind.effect for n in acted if (kind := kinds.get(n)) is not None]
        spent = any(sum(s.tokens.values()) for s in spans)
        return not spent and all(effect == "none" for effect in effects)

    def _first_failure(self, fire: Fire) -> datetime | None:
        with Reader.open(self.ctx.home) as reader:
            row = reader.connection.execute(
                "SELECT ended_at FROM fires WHERE id = ?", (fire.rerun_of or fire.id,)
            ).fetchone()
        return None if row is None or row[0] is None else instant(str(row[0]))

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
        zone = RunZone.of(self.ctx.home, f"precheck-{fire.id}")
        root = bundle.write(zone.code)
        host = HostScript(
            root,
            self.setting("triggers.precheck_timeout", 600),
            self.engine.banned_values(),
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
            workspace=str(zone.root),
        )
        try:
            found = await Monitor(host, monitors).run(job)
        finally:
            remove(zone.root)
        return found if isinstance(found, Ok | Failed) else Failed("precheck", "", "", False)

    def _ended(self, fire: Fire, trigger: Trigger, outcome: Outcome) -> None:
        status = ENDING[outcome.status]
        if status == "failed":
            why = outcome.reason or "the run failed"
            self._failed(fire, trigger, "run_failed", why, outcome.run_id)
            return
        outputs = outcome.outputs if outcome.status == "passed" else None
        detail = None if outcome.status == "passed" else outcome.reason
        delivery = delivered(trigger, status, outputs)
        at = self.ctx.at()
        self.engine.ledger.write(
            settle(fire, status, at, detail=detail, outputs=outputs, delivery=delivery)
        )
        if status == "ok":
            self.incidents.resolve_incident(trigger.id, at=at)
            self.engine.ledger.write(mark_incident(trigger.id, None))

    async def run_now(self, trigger_id: str) -> JsonObject:
        """Fire a trigger now and say what became of the fire: started, settled with its reason,
        or still pending and why it was not claimed (B-72)."""
        fire_id = fire_now(self.engine.ledger, trigger_id, self.ctx.clock.now(), {})
        return await self.answer(trigger_id, fire_id)

    async def deliver(self, trigger_id: str, delivery_id: str, payload: JsonObject) -> JsonObject:
        """One webhook delivery: a new delivery id fires the trigger once; a repeat answers with
        the fire it made and fires nothing."""
        with Reader.open(self.ctx.home) as reader:
            found = triggers(reader.connection, "WHERE id = ?", trigger_id)
        if not found or found[0].kind != "webhook":
            raise Refused("not_webhook", f"{trigger_id} is not a webhook trigger")
        body: JsonObject = {"webhook": {"delivery_id": delivery_id, "body": payload}}
        now = self.ctx.clock.now()
        fire_id, fresh = deliver(self.engine.ledger, trigger_id, delivery_id, body, now)
        answered = await self.answer(trigger_id, fire_id)
        return answered | {"delivery_id": delivery_id, "duplicate": not fresh}

    def explain(self, trigger_id: str) -> JsonObject:
        with Reader.open(self.ctx.home) as reader:
            found = triggers(reader.connection, "WHERE id = ?", trigger_id)
            if not found:
                raise Refused("unknown_trigger", f"no trigger {trigger_id}")
            state = Runs(self.ctx).version_state(self.ctx.library.get(found[0].pinned_object))
            facts = TriggerFacts(
                now=self.ctx.clock.now(),
                home=self.home,
                paused=self.engine.paused,
                version_state=state,
                incident=self.incidents.open_incident(trigger_id),
                tick_seconds=self.setting("scheduler.tick", 60),
                holidays=self._holidays(),
            )
            return explain_trigger(reader.connection, trigger_id, facts)

    async def answer(self, trigger_id: str, fire_id: str) -> JsonObject:
        """Tick once, then say what became of `fire_id`."""
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
            detail = unclaimed(
                trigger,
                int(live),
                self.home,
                claiming=self.engine.claiming,
                paused=self.engine.paused,
            )
        return {
            "trigger_id": trigger_id,
            "fire_id": fire_id,
            "status": found.status,
            "detail": detail,
            "run_id": found.run_id,
        }
