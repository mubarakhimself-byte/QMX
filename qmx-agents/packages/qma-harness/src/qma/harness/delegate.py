"""`delegate` v2: a helper is a full chat that returns a handle at once (AD-41, H26).

The parent is never blocked on a helper. `start` resolves one child bundle (profile, model,
wire, effort), starts the helper and returns its handle in milliseconds; the helper runs as its
own chat, so the parent keeps talking to the operator while it works. What the parent gets back
is a report between its turns, never a tool result it waited for:

- the answer is stored in `control.db` first, then announced on the parent's session, then
  handed to the parent once, in front of its next turn, and marked delivered in that same
  write. A host restart between two turns delivers each completion exactly once.
- `list` reads the live helpers and the stored completions, so a helper whose owner died reads
  `unknown` instead of vanishing.
- `steer` leaves a note the helper reads at its next checkpoint, and `stop` ends it.

A helper never outgrows its parent. Its tools are the parent's Surface cut to the Child rules
and to its role's preset (AD-62); it has no `delegate` of its own; and it is judged by the same
stuck rules as any unfinished chat (`qma.harness.stuck` through `watch_turn`).

A `cli` helper is an ordinary local process owned by its handle: its cwd is the helper's own
folder, its model traffic goes to the relay on a grant minted for the handle, and it dies with
the handle. Day one it runs an agent CLI that takes an Anthropic base URL and token from its
environment, which is what `[agents] cli_helper` names; the pinned Claude Code CLI is the
default.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import json
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, Protocol, cast

from qmx_control.models import (
    DELEGATE_SUMMARY_CHARS,
    DelegateCompletion,
    Document,
    LibraryInput,
)
from qmx_control.service import ControlService, SessionBlock
from qmx_router.agents import ROLE_TIERS
from qmx_router.complete import Refused as SchemaRefused
from qmx_router.complete import check as check_schema
from qmx_router.profiles import GptPlan, Profile, Profiles, resolve_model
from qmx_router.registry import ModelRow, Registry, UnknownModel, bundled

from qma.harness.launch import PermissionMode
from qma.harness.stuck import Pulse, Quiet, StuckTimeouts, watch_progress
from qma.harness.surface import Declaration, Surface, helper_scope
from qma.harness.turns import DEFAULT_TIMEOUTS, TurnHandle, watch_turn

if TYPE_CHECKING:
    from qma.harness.home import SessionId

type HelperState = Literal["queued", "running", "done", "failed", "stalled", "stopped", "unknown"]
type Target = Literal["chat", "cli"]
type Ending = Literal["done", "failed", "stalled", "stopped"]

BATCH: Final = 10
"""Helpers of one harness that run at once (Claude's default). There is no ceiling: the rest wait
as `queued` until a batch slot frees, and host chat capacity queues behind that (AD-58)."""
HANDLE: Final = 8
SUMMARY_HEAD: Final = 400
"""Characters of an answer a report line carries before it points at the artifact instead."""
CLI_POLL_S: Final = 2.0
"""How often a `cli` helper's silence is read against the no-progress rule."""
OUTPUT_LIMIT: Final = 1_000_000
"""Bytes of a `cli` helper's output kept. Past it the process stops as stalled, because a helper
that prints a million bytes and no answer has not answered."""
EFFORTS: Final = frozenset({"low", "medium", "high", "xhigh", "max"})
TARGETS: Final = frozenset({"chat", "cli"})


class DelegateRefused(RuntimeError):
    """The helper was not started, or the handle is not this chat's. The tool returns the reason
    as an error result, and nothing was spent."""


@dataclass(frozen=True)
class Start:
    """One `delegate` call's request, parsed at the tool boundary."""

    task: str
    profile: str | None = None
    model: str | None = None
    role: str | None = None
    effort: str | None = None
    output_schema: Mapping[str, object] | None = None
    worktree: bool = False
    group: str = ""
    target: Target = "chat"
    allow_cli: bool = False

    @classmethod
    def parse(cls, arguments: Mapping[str, object]) -> Start:
        """The tool call's arguments as a request, or a refusal naming what to fix."""
        task = arguments.get("task")
        if not isinstance(task, str) or not task.strip():
            raise DelegateRefused("delegate needs a task: the whole job, in your own words")
        found: dict[str, Any] = {}
        for name in ("profile", "model", "role", "effort", "group"):
            value = arguments.get(name)
            if value is None:
                continue
            if not isinstance(value, str):
                raise DelegateRefused(f"{name} is a string, not {type(value).__name__}")
            found[name] = value.strip() or None
        schema = arguments.get("output_schema")
        if schema is not None and not isinstance(schema, dict):
            raise DelegateRefused("output_schema is a JSON Schema object")
        target = arguments.get("target", "chat")
        if target not in TARGETS:
            raise DelegateRefused(f"target is one of {', '.join(sorted(TARGETS))}, not {target!r}")
        effort = found.get("effort")
        if effort is not None and effort not in EFFORTS:
            raise DelegateRefused(f"effort is one of {', '.join(sorted(EFFORTS))}, not {effort!r}")
        role = found.get("role")
        if role is not None and role not in ROLE_TIERS:
            raise DelegateRefused(
                f"role is one of {', '.join(sorted(ROLE_TIERS))}, or leave it out and name a "
                "profile or a model"
            )
        return cls(
            task=task,
            profile=found.get("profile"),
            model=found.get("model"),
            role=role,
            effort=effort,
            output_schema=cast("Mapping[str, object] | None", schema),
            worktree=arguments.get("worktree") is True,
            group=found.get("group") or "",
            target=cast("Target", target),
            allow_cli=arguments.get("allow_cli") is True,
        )


@dataclass(frozen=True)
class Resolved:
    """One child's runtime bundle, resolved in one function and never mixed field by field."""

    profile: str
    model: str
    wire: str
    effort: str | None
    role: str | None
    account: str
    """The lease's account is minted by the relay at launch; this names the provider it leases."""

    def document(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "model": self.model,
            "wire": self.wire,
            "effort": self.effort,
            "role": self.role,
            "account": self.account,
        }


@dataclass(frozen=True)
class ParentBundle:
    """What a helper copies from its parent: the chat's own profile and model, where it works,
    the declaration it had at birth (a parent that never launched has no Surface yet), its
    permission mode, and whether it is unattended."""

    profile: str
    model: str
    workspace: Path
    declared: Declaration
    mode: PermissionMode = "default"
    unattended: bool = False


def wire_of(profile: Profile) -> str:
    """The wire a profile's model calls speak, for the report the parent reads."""
    return "responses" if isinstance(profile, GptPlan) else "anthropic"


def tier_default(profile: Profile) -> str:
    """The model a profile runs when the caller names none: its own `opus` tier if it maps one,
    else the plan alias, which the profile refuses if it cannot run it."""
    tiers = getattr(profile, "tiers", None)
    return str(getattr(tiers, "opus", None) or "opus")


def row_for(registry: Registry, model: str) -> ModelRow | None:
    """The registry row a model id names, by its QMX id or its provider's native id."""
    wanted = model.strip().lower()
    for row in registry.rows():
        if wanted in (str(row.qmx_id).lower(), str(row.native).lower()):
            return row
    return None


def resolve(
    start: Start,
    *,
    profiles: Profiles,
    registry: Registry,
    parent: ParentBundle,
) -> Resolved:
    """One child bundle from the caller's one target word. Precedence: `profile`, then `model`,
    then `role`, then the parent's own profile and model. Every path ends in one profile, one
    model that profile runs, one wire and one effort, so a helper is launched from one value and
    never inherits half of another (AD-41)."""
    effort = start.effort
    if start.profile is not None:
        profile = profiles.get(start.profile)
        requested = start.model or parent.model
        model = resolve_model(profile, requested) or resolve_model(profile, tier_default(profile))
        if model is None:
            raise DelegateRefused(
                f"{start.profile} cannot run {requested!r}: name a model its [providers] row "
                "tiers, or a model id it lists"
            )
        return Resolved(
            start.profile, str(model), wire_of(profile), effort, start.role, start.profile
        )
    if start.model is not None:
        row = row_for(registry, start.model)
        if row is None:
            profile = profiles.get(parent.profile)
            model = resolve_model(profile, start.model)
            if model is None:
                raise DelegateRefused(
                    f"no registry row or [providers] tier names {start.model!r}; name the "
                    "profile it runs on"
                )
            return Resolved(
                parent.profile, str(model), wire_of(profile), effort, start.role, parent.profile
            )
        profile = profiles.get(str(row.provider))
        model = resolve_model(profile, str(row.qmx_id))
        if model is None:
            raise DelegateRefused(
                f"the {row.provider} profile does not run {row.qmx_id}: add that model id to "
                "its [providers] tiers"
            )
        return Resolved(
            str(row.provider), str(model), row.wire, effort, start.role, str(row.provider)
        )
    if start.role is not None:
        tier = ROLE_TIERS[start.role]
        chosen = _role_row(registry, profiles, tier)
        if chosen is None:
            raise DelegateRefused(
                f"no provider this QMX can lease runs the {tier} tier for the {start.role} "
                "role; name a profile and a model instead"
            )
        row, model = chosen
        return Resolved(str(row.provider), model, row.wire, effort, start.role, str(row.provider))
    profile = profiles.get(parent.profile)
    model = resolve_model(profile, parent.model) or resolve_model(profile, tier_default(profile))
    if model is None:
        raise DelegateRefused(f"{parent.profile} cannot run {parent.model!r}")
    return Resolved(parent.profile, str(model), wire_of(profile), effort, None, parent.profile)


def _role_row(registry: Registry, profiles: Profiles, tier: str) -> tuple[ModelRow, str] | None:
    """The first registry row of `tier` that a configured profile runs, and the model id that
    profile resolves it to. Chinese rows lead every tier (ruling 107)."""
    rows = sorted(
        (row for row in registry.rows() if row.class_ == tier),
        key=lambda row: (str(row.provider) not in profiles.by_name, str(row.qmx_id)),
    )
    for row in rows:
        if str(row.provider) not in profiles.by_name:
            continue
        with contextlib.suppress(UnknownModel, ValueError):
            model = resolve_model(profiles.get(str(row.provider)), str(row.qmx_id))
            if model is not None:
                return row, str(model)
    return None


@dataclass(frozen=True)
class ChildSpec:
    """What the host needs to start one helper chat and nothing more."""

    parent: SessionId
    handle: str
    title: str
    profile: str
    model: str
    effort: str | None
    scope: Declaration
    workspace: Path


@dataclass(frozen=True)
class CliSpawn:
    """One `cli` helper's process: the command, its environment and its folder."""

    argv: tuple[str, ...]
    env: Mapping[str, str]
    cwd: Path
    version: str
    """`<binary> <digest>`: one version tag per binary build, so the first spawn of each asks."""


class HelperHost(Protocol):
    """The harness, as `Helpers` needs it. Everything a helper does to the host goes through one
    of these calls, so the manager is testable without a CLI and reads no chat internals."""

    @property
    def control(self) -> ControlService: ...

    @property
    def state_dir(self) -> Path: ...

    def parent_bundle(self, parent: SessionId) -> ParentBundle: ...

    def surface(self, chat: SessionId) -> Surface | None: ...

    async def provider_profiles(self) -> Profiles: ...

    async def start_helper(self, spec: ChildSpec) -> SessionId: ...

    async def helper_turn(self, child: SessionId, text: str) -> TurnHandle: ...

    async def interrupt(self, chat: SessionId) -> None: ...

    async def close_chat(self, chat: SessionId) -> None: ...

    async def cli_spawn(self, spec: ChildSpec, child: SessionId) -> CliSpawn: ...


@dataclass
class Helper:
    """One helper this harness started, live in this process."""

    handle: str
    parent: SessionId
    resolved: Resolved
    group: str
    target: Target
    task: str
    started: float
    last_activity: float
    child: SessionId | None = None
    state: HelperState = "queued"
    steer: str = ""
    """A note waiting for the helper's next checkpoint."""
    steers_read: int = 0
    steers_late: int = 0
    stopping: str | None = None
    """The reason `stop` gave, so the helper's own end reads stopped rather than failed."""
    spawn: CliSpawn | None = None
    process: asyncio.subprocess.Process | None = None
    running: asyncio.Task[None] | None = None

    @property
    def chat(self) -> SessionId:
        if self.child is None:
            raise DelegateRefused(f"the helper {self.handle} has no chat yet")
        return self.child

    def document(self) -> dict[str, object]:
        return {
            "handle": self.handle,
            "state": self.state,
            "elapsed": round(time.monotonic() - self.started, 1),
            "last_activity": round(time.monotonic() - self.last_activity, 1),
            "profile": self.resolved.profile,
            "model": self.resolved.model,
            "group": self.group,
            "target": self.target,
        }


def new_handle() -> str:
    return f"h-{uuid.uuid4().hex[:HANDLE]}"


class Helpers:
    """Every helper this harness started, and every completion it owes a parent."""

    def __init__(
        self,
        host: HelperHost,
        *,
        batch: int = BATCH,
        timeouts: StuckTimeouts = DEFAULT_TIMEOUTS,
    ) -> None:
        self._host = host
        self._batch = asyncio.Semaphore(batch)
        self._timeouts = timeouts
        self._by_handle: dict[str, Helper] = {}
        self._tasks: set[asyncio.Task[None]] = set()

    async def start(self, parent: SessionId, start: Start) -> dict[str, object]:
        """Resolve, start and return the handle. The helper's turns are a task, so the caller
        gets its handle in milliseconds whatever the model or the provider does."""
        host, profiles = self._host, await self._host.provider_profiles()
        bundle = host.parent_bundle(parent)
        resolved = resolve(start, profiles=profiles, registry=bundled(), parent=bundle)
        for name in (start.profile, resolved.profile):
            refusal = None if name is None else profiles.delegate_refusal(name)
            if refusal is not None:
                raise DelegateRefused(refusal)
        if resolved.profile not in profiles.by_name:
            raise DelegateRefused(f"no provider is named {resolved.profile!r}")
        handle = new_handle()
        workspace = _helper_folder(bundle.workspace, handle, start.worktree)
        spec = ChildSpec(
            parent=parent,
            handle=handle,
            title=f"Helper {handle} on {resolved.profile}",
            profile=resolved.profile,
            model=resolved.model,
            effort=resolved.effort,
            scope=helper_scope(host.surface(parent), start.role, declared=bundle.declared),
            workspace=workspace,
        )
        spawn = None
        now = time.monotonic()
        helper = Helper(handle, parent, resolved, start.group, start.target, start.task, now, now)
        helper.child = child = await host.start_helper(spec)
        if start.target == "cli":
            try:
                spawn = await host.cli_spawn(spec, child)
                _consent(host, spawn, allow=start.allow_cli)
            except BaseException:
                with contextlib.suppress(Exception):
                    await host.close_chat(child)
                raise
        helper.spawn = spawn
        self._by_handle[handle] = helper
        task = asyncio.create_task(self._run(helper, start, spec))
        helper.running = task
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        await _note(host, parent, "agents", {"handle": handle, "state": helper.state})
        return {"handle": handle, "resolved": resolved.document(), "state": helper.state}

    async def listing(self, parent: SessionId, group: str = "") -> list[dict[str, object]]:
        """This chat's helpers: the live ones, then the stored completions of earlier ones, then
        a child session with no completion, which reads `unknown` because the process that owned
        it is gone (AD-41)."""
        found: list[dict[str, object]] = [
            helper.document()
            for helper in self._by_handle.values()
            if helper.parent == parent and (not group or helper.group == group)
        ]
        known = {str(row["handle"]) for row in found}
        children = {
            helper.child
            for helper in self._by_handle.values()
            if helper.parent == parent and helper.child is not None
        }
        for row in await asyncio.to_thread(
            self._host.control.delegate_completions_all, str(parent)
        ):
            if str(row["handle"]) in known:
                continue
            found.append(
                {
                    "handle": row["handle"],
                    "state": row["state"],
                    "group": group,
                    "target": "chat",
                    "delivered": bool(row.get("delivered_at")),
                }
            )
            known.add(str(row["handle"]))
        for child in await asyncio.to_thread(self._host.control.sessions_list, 0, 1000):
            if child.get("parent_id") != parent:
                continue
            unknown = f"h-{str(child['id'])[:HANDLE]}"
            if str(child["id"]) in children or unknown in known:
                continue
            found.append({"handle": unknown, "state": "unknown", "group": group, "target": "chat"})
            known.add(unknown)
        return found

    async def steer(self, parent: SessionId, handle: str, text: str) -> dict[str, object]:
        """Leave one note for a running helper's next checkpoint. A helper that already ended
        says so, and the note is not read."""
        helper = self._owned(parent, handle)
        if not text.strip():
            raise DelegateRefused("a steer needs text")
        if helper.state in ("done", "failed", "stalled", "stopped", "unknown"):
            return {"handle": handle, "steer": "missed_steer", "state": helper.state}
        helper.steer = text
        helper.last_activity = time.monotonic()
        return {"handle": handle, "steer": "queued_for_checkpoint", "state": helper.state}

    async def stop(self, parent: SessionId, handle: str, reason: str) -> dict[str, object]:
        """End one helper now, and say why."""
        helper = self._owned(parent, handle)
        if helper.state in ("done", "failed", "stalled", "stopped"):
            return {"handle": handle, "state": helper.state}
        helper.stopping = reason.strip() or "stopped by the parent"
        _kill(helper)
        if helper.child is not None:
            with contextlib.suppress(Exception):
                await self._host.interrupt(helper.child)
        return {"handle": handle, "state": "stopped", "reason": helper.stopping}

    async def pending(self, parent: SessionId) -> list[Document]:
        """The completions this chat has not been handed, oldest first. The caller claims them in
        the same write that carries them into a turn."""
        return await asyncio.to_thread(self._host.control.delegate_completions_pending, str(parent))

    async def claim(self, rows: Sequence[Mapping[str, object]]) -> int:
        handles = [str(row["handle"]) for row in rows]
        return await asyncio.to_thread(self._host.control.delegate_completions_claim, handles)

    async def shutdown(self) -> None:
        """End every helper of this harness. Each child chat closes and each process dies, and
        each helper stores what it had, so a restart loses nothing worth keeping."""
        for helper in list(self._by_handle.values()):
            helper.stopping = helper.stopping or "the host stopped"
            _kill(helper)
        for task in list(self._tasks):
            task.cancel()
        for task in list(self._tasks):
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task

    async def _run(self, helper: Helper, start: Start, spec: ChildSpec) -> None:
        """One helper from its start to its stored completion."""
        try:
            async with self._batch:
                if helper.stopping is not None:
                    await self._finish(helper, "stopped", helper.stopping)
                    return
                helper.state = "running"
                helper.last_activity = time.monotonic()
                if helper.target == "cli":
                    await self._run_cli(helper, start)
                else:
                    await self._run_chat(helper, start)
        except asyncio.CancelledError:
            if helper.state not in _ENDED:
                await self._finish(helper, "stopped", helper.stopping or "the host stopped")
            raise
        except DelegateRefused as refused:
            await self._finish(helper, "failed", str(refused))
        except Exception as error:  # a host refusal, a launch failure, a dead CLI
            await self._finish(helper, "failed", f"the helper did not finish: {error}")
        finally:
            helper.process = None
            if helper.child is not None:
                with contextlib.suppress(Exception):
                    await self._host.close_chat(helper.child)

    async def _run_chat(self, helper: Helper, start: Start) -> None:
        text, verdict = await self._chat_turns(helper, start.task)
        if verdict is not None:
            await self._finish(helper, "stalled", f"the stuck rules stopped it: {verdict}")
            return
        if helper.stopping is not None:
            await self._finish(helper, "stopped", helper.stopping)
            return
        if helper.steer:
            helper.steers_late += 1
            helper.steer = ""
        summary, valid = await self._schema(helper, start, text)
        await self._finish(helper, "done", summary, schema_valid=valid)

    async def _chat_turns(self, helper: Helper, task: str) -> tuple[str, str | None]:
        """The helper's first turn, then one more per note it picked up. Returns its final text
        and the stuck verdict that stopped it, if one did. This loop is the only reader of the
        helper's turns, so a note never opens a turn nobody collects."""
        text, verdict = await self._one_turn(helper, task)
        while verdict is None and helper.steer and helper.stopping is None:
            note = helper.steer
            helper.steer = ""
            helper.steers_read += 1
            text, verdict = await self._one_turn(helper, f"A note from your parent: {note}")
        return text, verdict

    async def _one_turn(self, helper: Helper, text: str) -> tuple[str, str | None]:
        child = helper.chat
        handle = await self._host.helper_turn(child, text)
        verdict = await watch_turn(handle, functools.partial(self._host.interrupt, child))
        ended = await handle.result()
        helper.last_activity = time.monotonic()
        if verdict is not None:
            return "", str(verdict)
        if ended.status == "unknown" and helper.stopping is None:
            raise DelegateRefused("the helper's process ended before it answered")
        if helper.stopping is not None:
            return ended.text or "", None
        if ended.status != "ok":
            reason = ended.text or ended.terminal_reason
            raise DelegateRefused(f"the helper's turn failed: {reason}")
        return ended.text or "", None

    async def _run_cli(self, helper: Helper, start: Start) -> None:
        """A `cli` helper: a local process owned by the handle, read against the no-progress
        rule and killed when it ends, stalls or is stopped."""
        spawn = helper.spawn
        if spawn is None:
            raise DelegateRefused("the cli helper has no command to run")
        solution = await asyncio.create_subprocess_exec(
            *spawn.argv,
            env=dict(spawn.env),
            cwd=spawn.cwd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        helper.process = solution
        if solution.stdin is None or solution.stdout is None:
            raise DelegateRefused("the cli helper's pipes did not open")
        solution.stdin.write(start.task.encode())
        with contextlib.suppress(BrokenPipeError, ConnectionResetError):
            await solution.stdin.drain()
        solution.stdin.close()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(solution.stdin.wait_closed(), 5)
        quiet, progress, clock, kept = Quiet(), 0, time.monotonic(), 0
        chunks: list[str] = []
        while True:
            try:
                line = await asyncio.wait_for(solution.stdout.readline(), CLI_POLL_S)
            except TimeoutError:
                line = None
            if line:
                progress += 1
                kept += len(line)
                chunks.append(line.decode("utf-8", "replace"))
                helper.last_activity = time.monotonic()
                if kept > OUTPUT_LIMIT:
                    solution.kill()
                    await self._finish(helper, "stalled", "it printed more than the output bound")
                    return
            elif line is not None:
                await self._settle_cli(helper, solution)
                if helper.state in _ENDED:
                    return
                break
            if solution.returncode is not None:
                break
            now = time.monotonic()
            quiet, alarm = watch_progress(quiet, Pulse(progress), now - clock, self._timeouts)
            clock = now
            if alarm in ("interrupt", "stalled"):
                solution.kill()
                await self._finish(helper, "stalled", "the stuck rules stopped it: no progress")
                return
        text = "".join(chunks).strip()
        if helper.stopping is not None:
            await self._finish(helper, "stopped", helper.stopping)
            return
        if solution.returncode != 0:
            await self._finish(
                helper,
                "failed",
                f"the cli helper ended {solution.returncode}: {text[-SUMMARY_HEAD:]}",
            )
            return
        summary, valid = await self._schema(helper, start, text)
        await self._finish(helper, "done", summary, schema_valid=valid)

    async def _settle_cli(self, helper: Helper, solution: asyncio.subprocess.Process) -> None:
        """Wait for a `cli` helper whose output has closed. A process that keeps running with its
        output closed is killed and reads stalled, so a stuck binary cannot hold a helper slot."""
        try:
            await asyncio.wait_for(solution.wait(), self._timeouts.idle)
        except TimeoutError:
            solution.kill()
            await self._finish(
                helper, "stalled", "its output closed and it did not exit; the handle killed it"
            )

    async def _schema(self, helper: Helper, start: Start, text: str) -> tuple[str, bool]:
        """The answer to keep, and whether it holds to the schema the caller asked for. One
        correction turn carries the errors verbatim; after it the raw answer is kept with
        `schema_valid: false` (AD-41)."""
        schema = start.output_schema
        if schema is None:
            return text, True
        try:
            _check(schema, text)
            return text, True
        except SchemaRefused as refused:
            if helper.target == "cli":
                return text, False
            child = helper.chat
            handle = await self._host.helper_turn(
                child,
                "Your answer did not hold to the schema you were given. The errors, verbatim:\n"
                f"{refused}\n\nAnswer again with one JSON document that holds to it, and "
                "nothing else.",
            )
            verdict = await watch_turn(handle, functools.partial(self._host.interrupt, child))
            ended = await handle.result()
            helper.last_activity = time.monotonic()
            if verdict is not None or ended.status != "ok":
                return text, False
            corrected = ended.text or text
            try:
                _check(schema, corrected)
                return corrected, True
            except SchemaRefused:
                return corrected, False

    async def _finish(
        self,
        helper: Helper,
        state: Ending,
        summary: str,
        *,
        schema_valid: bool = True,
    ) -> None:
        """Store the answer, then announce it on the parent's session. Delivery into the parent's
        next turn is separate, so a restart here loses nothing (AD-41)."""
        if helper.state in _ENDED:
            return
        helper.state = state
        helper.last_activity = time.monotonic()
        kept = await asyncio.to_thread(self._record, helper, state, summary, schema_valid)
        await _note(
            self._host,
            helper.parent,
            "text",
            {"text": report_text([kept]), "helper": helper.handle},
        )

    def _record(self, helper: Helper, state: Ending, summary: str, schema_valid: bool) -> Document:
        """The completion row, saved before anything announces it."""
        body = summary.strip()
        head = f"{helper.handle} on {helper.resolved.profile}/{helper.resolved.model}"
        notes: list[str] = []
        if helper.steers_read:
            notes.append(f"{helper.steers_read} steer read")
        if helper.steers_late:
            notes.append("a steer arrived after its last turn and was not read")
        if notes:
            head = f"{head} ({'; '.join(notes)})"
        artifact = ""
        if len(body) > DELEGATE_SUMMARY_CHARS:
            artifact = self._save_artifact(helper, body)
            body = f"{body[:SUMMARY_HEAD]}… the whole answer is Library artifact {artifact}"
        completion = DelegateCompletion(
            handle=helper.handle,
            parent_session=str(helper.parent),
            state=state,
            summary=f"{head}: {body}"[:DELEGATE_SUMMARY_CHARS],
            artifact_id=artifact,
            schema_valid=schema_valid,
        )
        data = self._host.control.delegate_completion_save(completion)
        return data

    def _save_artifact(self, helper: Helper, body: str) -> str:
        saved = self._host.control.library_save(
            LibraryInput(
                title=f"Helper {helper.handle} on {helper.resolved.profile}",
                kind="delegate-report",
                content=body,
                tags=["delegate", str(helper.parent)],
                source=f"{helper.resolved.profile}/{helper.resolved.model}",
            )
        )
        return str(saved["id"])

    def _owned(self, parent: SessionId, handle: str) -> Helper:
        helper = self._by_handle.get(handle)
        if helper is None or helper.parent != parent:
            raise DelegateRefused(f"no helper of this chat has the handle {handle!r}")
        return helper


_ENDED: Final = frozenset({"done", "failed", "stalled", "stopped"})


def _check(schema: Mapping[str, object], text: str) -> None:
    """One answer against its schema: JSON, one document, and the fields the schema names."""
    try:
        parsed: object = json.loads(text)
    except ValueError:
        raise SchemaRefused(f"the answer is not JSON: {text[:200]!r}") from None
    check_schema(schema, parsed)


def report_text(rows: Sequence[Mapping[str, object]]) -> str:
    """The one block a parent reads for its finished helpers. It never starts with a slash or an
    `@`, because a copilot chat carries it into a turn of its own, where those would be
    commands."""
    lines = ["Helper reports, which arrived between your turns:"]
    for row in rows:
        summary = str(row.get("summary", "")).strip()
        lines.append(f"- {summary}")
        if row.get("artifact_id"):
            lines.append(f"  the whole answer is Library artifact {row['artifact_id']}")
        if row.get("schema_valid") is False:
            lines.append("  its answer never held to the output schema you asked for")
    return "\n".join(lines)


def _kill(helper: Helper) -> None:
    """Kill the helper's own process if it still runs. A process that already ended, or whose
    pipe the host has closed, is not an error: the handle is dead either way."""
    process = helper.process
    if process is not None and process.returncode is None:
        with contextlib.suppress(ProcessLookupError, OSError):
            process.kill()


def _helper_folder(parent_workspace: Path, handle: str, worktree: bool) -> Path:
    """Where the helper works: the parent's folder, or its own folder beside it when the caller
    asked for one. A git worktree is AD-49 and arrives with the Library."""
    if not worktree:
        return parent_workspace
    folder = parent_workspace / ".qmx" / "helpers" / handle
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _consent(host: HelperHost, spawn: CliSpawn, *, allow: bool) -> None:
    """The first spawn of one binary version asks in the chat. The tool refuses with the version
    and the exact argument that allows it, and records nothing until the caller passes it."""
    state = _read_versions(_versions_path(host))
    allowed = set(state.get("allowed", []))
    if spawn.version in allowed:
        return
    seen: list[str] = list(state.get("seen", []))
    if not allow:
        if spawn.version not in seen:
            seen.append(spawn.version)
            state["seen"] = seen
            _write_versions(host, state)
        raise DelegateRefused(
            f"a cli helper would run {spawn.version}, which has not been allowed here yet. Ask "
            "the operator, then call delegate again with allow_cli=true to run it"
        )
    allowed.add(spawn.version)
    state["allowed"] = sorted(allowed)
    _write_versions(host, state)


def _versions_path(host: HelperHost) -> Path:
    return host.state_dir / "delegate-cli.json"


def _read_versions(path: Path) -> dict[str, list[str]]:
    if not path.is_file():
        return {}
    try:
        found: object = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    return cast("dict[str, list[str]]", found) if isinstance(found, dict) else {}


def _write_versions(host: HelperHost, state: Mapping[str, list[str]]) -> None:
    path = _versions_path(host)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(state), indent=2), encoding="utf-8")


async def _note(
    host: HelperHost, chat: SessionId, kind: str, content: Mapping[str, object]
) -> None:
    """One block on a chat's session, written off the event loop. A session that cannot take the
    block never fails the helper."""
    block = SessionBlock(type=cast("Any", kind), content=cast("Document", dict(content)))
    with contextlib.suppress(Exception):
        await asyncio.to_thread(host.control.sessions_append, str(chat), block)
