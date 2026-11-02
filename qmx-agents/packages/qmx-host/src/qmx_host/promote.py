"""`POST /api/units/promote`: his click moves a unit, and the same click deploys it (Part C
AD-324, `CONTRACTS.md` section 13, Level 0 AD-23, R1-C-01).

The route answers only to his principal `operator`, the principal of his UI bearer (caller kind
`user`, `qmx_engine/service/context.py`), as the seal move does. Every other principal, a
chat's agent, a workflow's run, the MCP client, an observer and a call no door named, is refused
before the body is read. It is a host route and never a catalog row, so no agent or workflow
has a tool that reaches it.

For a move into paper or live it builds the deployment document (`qmx.node.deployment/1`) from
the Library: the unit document, every pinned block file by fingerprint, the passing G
`test-report` of its compiled fingerprint, the starting numbers, the instrument, venue and
account records. It asks the node `deploy` through the node link, and only once the node took
it or queued it does it record the move through the host's one lifecycle writer. A move to
parked or retired is recorded first and then asks `withdraw` of every deployment his clicks put
on that market. The event id and the deployment id derive from the click's op id, so the same
click sent again lands nothing new and answers what the first answered.

Nothing here sends an order, binds an account or reads a secret: the node decides what trades.
"""

from __future__ import annotations

import dataclasses
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Final, Literal, Protocol, cast

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError
from qmf.core import fingerprint, is_refusal
from qml.compile import CompiledUnit, compile_unit
from qml.lifecycle import Actor, ActorKind, Event, MarketKey, State, fold
from qmx_control.models import Document
from qmx_engine.control_door import PRINCIPAL
from qmx_engine.service.context import OPERATOR
from qmx_judge.landing import GRecord
from qmx_library.port import JsonObject, LibraryRefused
from qmx_library.principal import MAIN, Principal, state_ref
from qmx_library.store import Store
from qmx_tools.gather import gather
from qmx_tools.journals import journal_query

from qmx_host.lifecycle import LifecycleWriter, MoveRefused
from qmx_host.node_link import NODE_APP, Change, NodeLink

__all__ = [
    "ROUTE",
    "SCHEMA",
    "Click",
    "Promoter",
    "harvested_calibrations",
    "promote_router",
]

ROUTE: Final = "/api/units/promote"
SCHEMA: Final = "qmx.units.promote/1"
DEPLOYMENT_SCHEMA: Final = "qmx.node.deployment/1"
TRADING: Final = frozenset({State.PAPER, State.LIVE})
LEAVING: Final = frozenset({State.PARKED, State.RETIRED})
READ: Final = Principal("operator")
SHOWN: Final[Mapping[str, str]] = {"applied": "accepted", "waiting": "queued"}
"""A node change's outbox state as his answer says it; a refused change is a refusal."""
GONE: Final = "unknown_deployment"
"""The node's answer to a withdraw of a deployment it does not hold: nothing is left to stop."""

type Lane = Literal["paper", "live"]
type Calibrations = Callable[[str, str], Sequence[Mapping[str, object]]]
"""The paper lane's harvested `calibration` row bodies of one unit version, oldest first."""


class GRecords(Protocol):
    def g_record(self, compiled_fp: str) -> GRecord | None: ...


class Refused(Exception):
    """A click this route does not carry out, with the code his answer names."""

    def __init__(self, code: str, message: str, next_step: str, *, status: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.next_step = next_step
        self.status = status
        self.value: Document = {}


class UnitRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(min_length=1)
    """The document's `unit_id`."""
    version: str = Field(min_length=1)
    """The unit version's Library object id, the `version_ref` every lifecycle move names."""


class NodeRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    tag: str = Field(min_length=1)


class AccountRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(min_length=1)
    """The venue's account id, the one the node binds; its `account` record names it."""


class Click(BaseModel):
    """His click, `qmx.units.promote/1`."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["qmx.units.promote/1"]
    op_id: str = Field(min_length=1, max_length=200)
    unit: UnitRef
    market_id: str = Field(min_length=1)
    to: Literal["paper", "live", "parked", "retired"]
    clears: str | None = None
    node: NodeRef | None = None
    account: AccountRef | None = None
    placeholders_acknowledged: bool = False

    @property
    def target(self) -> State:
        return State(self.to)

    @property
    def key(self) -> MarketKey:
        return MarketKey(self.unit.id, self.unit.version, self.market_id)

    def digest(self) -> str:
        named = fingerprint(
            {
                "op_id": self.op_id,
                "unit": self.unit.id,
                "version": self.unit.version,
                "market": self.market_id,
                "to": self.to,
            }
        )
        if is_refusal(named):
            raise Refused("bad_request", "the click's names do not fingerprint", "", status=400)
        return named.value.digest[:24]


def event_id(digest: str) -> str:
    return f"click-{digest}"


def deployment_id(digest: str) -> str:
    return f"dep-{digest}"


def deployment_of(event: Event) -> str | None:
    """The deployment his click into paper or live put on the node, named by its event."""
    if event.to_state not in TRADING or not event.event_id.startswith("click-"):
        return None
    return deployment_id(event.event_id.removeprefix("click-"))


@dataclass(frozen=True, slots=True)
class Held:
    """A Library record as a deployment names it: the item, its version on its ref and the
    object, which is the content address of that version."""

    item: str
    version: int
    object_id: str
    fields: JsonObject

    def ref(self) -> Document:
        return {"id": self.item, "version": self.version, "fingerprint": self.object_id}


def _version(store: Store, item: str, kind: str, object_id: str) -> int:
    placed = [found for found, _ in store.placed(item, kind, None)]
    return placed.index(object_id) + 1 if object_id in placed else 1


def _main(store: Store, kind: str, key: str, value: str) -> list[Held]:
    """Each live item of `kind` whose head on `main` holds `key = value`. An archived item is
    withdrawn and names nothing (Library AD-6)."""
    items = {store.get(READ, found).item for found in store.with_field(kind, key, value)}
    held: list[Held] = []
    for item in sorted(items):
        head, state = store.head(item, MAIN), store.head(item, state_ref(item))
        if head is None or (state is not None and state[0] == "archived"):
            continue
        fields = store.get(READ, head[0]).fields
        if fields.get(key) == value:
            held.append(Held(item, head[1], head[0], fields))
    return held


def _one(found: list[Held], what: str) -> Held:
    if len(found) != 1:
        many = f"{len(found)} records" if found else "no record"
        raise Refused(
            "no_record",
            f"the Library holds {many} for {what}",
            "Add or fix that record in the Library, then click again.",
        )
    return found[0]


def harvested_calibrations(home: Path, clock: Callable[[], int]) -> Calibrations:
    """The paper lane's `calibration` rows of a unit version as this machine's harvester filed
    them (`qmx_tools.journals.journal_query`, Part B AD-209)."""

    def read(unit_id: str, unit_version: str) -> list[Mapping[str, object]]:
        answer = journal_query(
            home,
            stream="unit",
            window={"start": 0, "end": clock()},
            filters={
                "kind": "calibration",
                "unit_id": unit_id,
                "unit_version": unit_version,
                "world": "paper",
            },
        )
        rows = cast("list[Mapping[str, object]]", answer["rows"])
        return [cast("Mapping[str, object]", row["body"]) for row in rows]

    return read


def starting(
    document: Mapping[str, object], lane: Lane, rows: Sequence[Mapping[str, object]]
) -> Document:
    """The numbers a lane starts from: paper from the unit's defaults, as QMB tested it; live
    from the paper lane's last calibrated value of each number and the newest watermark of the
    rows they came from (AD-324, LC-C-39). A number no row moved keeps its default."""
    numbers = cast("Mapping[str, Mapping[str, object]]", document.get("numbers") or {})
    values: dict[str, JsonValue] = {name: str(n.get("default")) for name, n in numbers.items()}
    if lane == "paper":
        return {"source": "defaults", "values": values}
    found: Document = {"source": "paper_lane", "values": values}
    for row in rows:
        values[str(row["number"])] = str(row["new"])
    marks = [int(cast("int", row["watermark"])) for row in rows]
    if marks:
        found["watermark"] = max(marks)
    return found


class Promoter:
    """His promote click over the Library, the lifecycle writer and the node link."""

    def __init__(
        self,
        store: Store,
        lifecycle: LifecycleWriter,
        nodes: NodeLink,
        records: GRecords,
        *,
        calibrations: Calibrations,
        trading_profile: Callable[[str], bool],
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        """`trading_profile(place)` says whether the host at that place runs in the trading
        profile (AD-307); a place it cannot read answers False."""
        self.store = store
        self.lifecycle = lifecycle
        self.nodes = nodes
        self.records = records
        self.calibrations = calibrations
        self.trading_profile = trading_profile
        self.now = now
        self._lock = threading.Lock()

    def promote(self, click: Click) -> Document:
        with self._lock:
            digest = click.digest()
            known = self.lifecycle.events(click.unit.id)
            if click.target in TRADING:
                return self._admit(click, digest, known)
            return self._leave(click, digest, known)

    def _event(
        self, click: Click, digest: str, current: State, compiled: str, evidence: str | None
    ) -> Event:
        return Event(
            event_id=event_id(digest),
            unit_id=click.unit.id,
            version_ref=click.unit.version,
            compiled_fingerprint=compiled,
            market_id=click.market_id,
            from_state=current,
            to_state=click.target,
            by=Actor(ActorKind.HIS_CLICK, OPERATOR.principal),
            reason=f"his click: {current} to {click.to}",
            evidence_ref=evidence,
            at=self.now(),
            writer=self.lifecycle.writer_id,
            sequence=0,
            clears=click.clears,
        )

    def _allowed(self, event: Event, known: Sequence[Event]) -> None:
        """Refuse a move Part A's `fold` refuses, before anything reaches the node."""
        mine = [seen.sequence for seen in known if seen.writer == self.lifecycle.writer_id]
        stamped = dataclasses.replace(event, sequence=max(mine, default=-1) + 1)
        folded = fold([*known, stamped], auto_paper=self.lifecycle.auto_paper())
        for rejected in folded.rejected:
            if rejected.event.event_id == event.event_id:
                raise Refused(
                    "illegal_move",
                    f"{rejected.refusal}: {rejected.message}",
                    "Only the moves the lifecycle table allows go through.",
                )

    def _admit(self, click: Click, digest: str, known: Sequence[Event]) -> Document:
        made, ask = event_id(digest), deployment_id(digest)
        if any(seen.event_id == made for seen in known):
            change = self.nodes.outbox.get(ask)
            if change is not None:
                self.nodes.flush(change.place)
                change = self.nodes.outbox.get(ask) or change
                return _done(made, _shown(change), ask)
        if click.node is None or click.account is None:
            raise Refused(
                "bad_request",
                f"a move to {click.to} names the node and the account it trades on",
                "Name the node's tag and the account id.",
                status=400,
            )
        current = fold(known, auto_paper=self.lifecycle.auto_paper()).state(click.key)
        if current is State.STOPPED:
            raise Refused(
                "illegal_move",
                f"{click.market_id} is stopped by a risk rule; his resume on the node clears it",
                "Resume the unit on the node's card.",
            )
        document, compiled = self._unit(click)
        probe = self._event(click, digest, current, compiled.compiled_fingerprint.value, None)
        self._allowed(probe, known)
        lane: Lane = "paper" if click.target is State.PAPER else "live"
        report = self._g_record(compiled.compiled_fingerprint.value)
        account = _one(
            _main(self.store, "account", "account_id", click.account.id),
            f"account {click.account.id}",
        )
        place = self.nodes.home_of(NODE_APP)
        if lane == "live":
            if account.fields.get("world") == "live" and not self.trading_profile(place):
                raise Refused(
                    "trading_profile_off",
                    f"account {click.account.id} is a live-world account and the host at {place}"
                    " is not in the trading profile",
                    "Bind live money through the deliberate live path first.",
                )
            if compiled.placeholders and not click.placeholders_acknowledged:
                raise Refused(
                    "placeholders_unacknowledged",
                    f"the unit still uses placeholder blocks: {', '.join(compiled.placeholders)}",
                    "Tick that you accept the placeholders, then click again.",
                )
        event = self._event(click, digest, current, compiled.compiled_fingerprint.value, report)
        deployment = self._deployment(
            click, click.node, ask, document, compiled, lane, report, account, event.event_id
        )
        change = self.nodes.change(
            NODE_APP,
            "deploy",
            {"deployment": deployment},
            principal=OPERATOR.principal,
            op_id=ask,
        )
        answer = _shown(change)
        try:
            self.lifecycle.record_move(event)
        except MoveRefused as refused:
            self._withdraw(f"{digest}-undo", [ask])
            raise Refused(
                "illegal_move",
                f"{refused.refusal}: {refused}",
                "The node was asked to withdraw the deployment; nothing moved.",
            ) from None
        return _done(made, answer, ask)

    def _leave(self, click: Click, digest: str, known: Sequence[Event]) -> Document:
        """Park or retire: record the move, then ask the node to withdraw each deployment his
        clicks put on this market. A market already parked or retired records nothing and asks
        the withdraw again, so a second click finishes a withdraw the node did not answer."""
        folded = fold(known, auto_paper=self.lifecycle.auto_paper())
        current = folded.state(click.key)
        moves = [applied for applied in folded.applied if applied.key == click.key]
        made = event_id(digest)
        if current is click.target and not any(seen.event_id == made for seen in known):
            made = moves[-1].event_id
        else:
            compiled = moves[-1].compiled_fingerprint if moves else ""
            try:
                made = self.lifecycle.record_move(
                    self._event(click, digest, current, compiled, None)
                )
            except MoveRefused as refused:
                raise Refused(
                    "illegal_move",
                    f"{refused.refusal}: {refused}",
                    "Only the moves the lifecycle table allows go through.",
                ) from None
        placed = [found for move in moves if (found := deployment_of(move)) is not None]
        answer = self._withdraw(digest, list(dict.fromkeys(placed)))
        if answer.code is not None:
            refused = Refused(
                "node_not_ready",
                f"the move is recorded, and the node did not withdraw: {answer.message}",
                "Withdraw again with a new click, or kill the unit on the node's card.",
            )
            refused.value = {"lifecycle_event_id": made}
            raise refused
        return _done(made, answer.word, None)

    def _withdraw(self, digest: str, placed: Sequence[str]) -> Withdrawn:
        worst = Withdrawn("accepted")
        for deployment in placed:
            change = self.nodes.change(
                NODE_APP,
                "withdraw",
                {"deployment_id": deployment, "when": "flat"},
                principal=OPERATOR.principal,
                op_id=f"withdraw-{digest}-{deployment}",
            )
            answer = cast("Mapping[str, object]", change.answer or {})
            if change.state == "refused" and answer.get("code") != GONE:
                return Withdrawn("refused", str(answer.get("code")), str(answer.get("message")))
            if change.state == "waiting":
                worst = Withdrawn("queued")
        return worst

    def _unit(self, click: Click) -> tuple[Mapping[str, object], CompiledUnit]:
        try:
            view = self.store.get(READ, click.unit.version)
        except LibraryRefused:
            view = None
        if view is None or view.kind != "unit" or view.fields.get("unit_id") != click.unit.id:
            raise Refused(
                "no_record",
                f"the Library holds no unit {click.unit.id} at {click.unit.version}",
                "Name the unit version his Library holds.",
            )
        document = cast("Mapping[str, object]", view.fields)
        markets = cast("list[Mapping[str, object]]", document.get("markets") or [])
        if click.market_id not in {str(m.get("market_id")) for m in markets}:
            raise Refused(
                "no_record",
                f"the unit trades no market {click.market_id}",
                "Promote it on one of its own markets.",
            )
        compiled = compile_unit(document, gather(self.store, document).context)
        if not isinstance(compiled, CompiledUnit):
            first = compiled[0].message if compiled else "the unit does not compile"
            raise Refused("no_g_record", f"the unit does not compile: {first}", "Fix the unit.")
        return document, compiled

    def _g_record(self, compiled: str) -> str:
        found = self.records.g_record(compiled)
        if found is None or not found.safety_passed:
            why = "no G test-report" if found is None else f"G test-report {found.object_id} failed"
            raise Refused(
                "no_g_record",
                f"{why} for compiled fingerprint {compiled}",
                "Run the behaviour check on this version; a passing check lets it trade.",
            )
        return found.object_id

    def _deployment(
        self,
        click: Click,
        node: NodeRef,
        ask: str,
        document: Mapping[str, object],
        compiled: CompiledUnit,
        lane: Lane,
        report: str,
        account: Held,
        lifecycle_event: str,
    ) -> Document:
        markets = cast("list[Mapping[str, object]]", document.get("markets") or [])
        records = [self._instrument(market) for market in markets]
        admitted = next(
            held
            for market, held in zip(markets, records, strict=True)
            if market.get("market_id") == click.market_id
        )
        venues = {str(held.fields.get("venue")) for held in records}
        venue_records = [
            held for venue in sorted(venues) for held in _main(self.store, "venue", "venue", venue)
        ]
        rows: Sequence[Mapping[str, object]] = (
            ()
            if lane == "paper"
            else self.calibrations(click.unit.id, compiled.document_fingerprint.value)
        )
        report_view = self.store.get(READ, report)
        report_held = Held(
            report_view.item,
            _version(self.store, report_view.item, report_view.kind, report),
            report,
            report_view.fields,
        )
        return {
            "schema_version": DEPLOYMENT_SCHEMA,
            "deployment_id": ask,
            "node": {"tag": node.tag, "install_id": None},
            "unit": {"id": click.unit.id, "version": click.unit.version},
            "unit_document": cast("JsonValue", dict(document)),
            "compiled_fingerprint": compiled.compiled_fingerprint.value,
            "g_record": {
                "id": report_held.item,
                "version": report_held.version,
                "compiled_fingerprint": compiled.compiled_fingerprint.value,
            },
            "files": self._files(document),
            "starting": cast("JsonValue", starting(document, lane, rows)),
            "markets": [{"market_id": click.market_id, "instrument": admitted.ref()}],
            "account": {
                "id": account.fields["account_id"],
                "version": account.version,
                "fingerprint": account.object_id,
            },
            "snapshots": [
                *({**held.fields, "record_version": held.version} for held in records),
                *(dict(held.fields) for held in venue_records),
                dict(account.fields),
            ],
            "lane": lane,
            "lifecycle_event": lifecycle_event,
            "placeholders_acknowledged": click.placeholders_acknowledged,
            "created_by": OPERATOR.principal,
            "created_at": self.now().isoformat(),
        }

    def _instrument(self, market: Mapping[str, object]) -> Held:
        ref = cast("Mapping[str, object]", market.get("instrument_ref") or {})
        venue, symbol = str(ref.get("venue")), str(ref.get("symbol"))
        found = _main(self.store, "instrument", "symbol", symbol)
        return _one(
            [held for held in found if held.fields.get("venue") == venue],
            f"{market.get('market_id')} ({venue}:{symbol})",
        )

    def _files(self, document: Mapping[str, object]) -> list[JsonValue]:
        """Every pinned block file, the bytes the unit compiled from, kept in the Library's
        blob store by their fingerprint so the node link stages them from there."""
        context = gather(self.store, document).context
        files: list[JsonValue] = []
        for pin in sorted(context.sources):
            entry_id, version = pin.split("@")
            for name, kind, data in (
                ("block.py", "block", context.sources[pin]),
                ("entry.json", "entry", context.entries[pin]),
            ):
                files.append(
                    {
                        "entry_id": entry_id,
                        "version": int(version),
                        "fingerprint": self.store.store_blob(data),
                        "path": f"blocks/{pin}/{name}",
                        "kind": kind,
                        "bytes": len(data),
                    }
                )
        return files


@dataclass(frozen=True, slots=True)
class Withdrawn:
    word: str
    code: str | None = None
    message: str = ""


def _shown(change: Change) -> str:
    if change.state == "refused":
        answer = cast("Mapping[str, object]", change.answer or {})
        refused = Refused(
            "node_not_ready",
            f"the node refused the deployment: {answer.get('code')}: {answer.get('message')}",
            str(answer.get("next_step") or "Check the node's card, then click again."),
        )
        refused.value = {"node_answer": change.answer}
        raise refused
    return SHOWN[change.state]


def _done(made: str, answer: str, deployment: str | None) -> Document:
    value: Document = {"lifecycle_event_id": made, "node_answer": answer}
    if deployment is not None:
        value["deployment_id"] = deployment
    return {"ok": True, "value": value}


def _refusal(refused: Refused) -> JSONResponse:
    body: Document = {
        "ok": False,
        "code": refused.code,
        "message": str(refused),
        "next_step": refused.next_step,
    }
    if refused.value:
        body["value"] = refused.value
    return JSONResponse(body, status_code=refused.status)


def promote_router(promoter: Promoter) -> APIRouter:
    router = APIRouter()

    @router.post(ROUTE)
    def promote(body: Annotated[JsonValue, Body()]) -> JSONResponse:
        caller = PRINCIPAL.get().principal
        if caller != OPERATOR.principal:
            return _refusal(
                Refused(
                    "refused_principal",
                    f"a unit moves toward paper or live only by his click, not by {caller}",
                    "He clicks it on the unit's page.",
                    status=403,
                )
            )
        try:
            click = Click.model_validate(body)
        except ValidationError as error:
            first = error.errors()[0]
            where = ".".join(str(part) for part in first["loc"]) or "body"
            return _refusal(Refused("bad_request", f"{where}: {first['msg']}", "", status=400))
        try:
            return JSONResponse(promoter.promote(click))
        except Refused as refused:
            return _refusal(refused)

    _ = promote
    return router
