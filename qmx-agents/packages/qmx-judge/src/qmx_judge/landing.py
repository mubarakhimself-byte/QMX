"""The core's one lander: every run's result reaches the Library here and nowhere else.

`Lander` is the lander port of Part B AD-207 and Level 0 AD-34: `open` mints the run id and lands
the `opened` try, `close` checks the tester's bundle and lands one `backtest-result` with its
edges and the closing try, and `fail` lands a `killed` result with no measures. All three are
idempotent by run id, so a retry finds what the first call wrote and writes nothing again.

`land` is PR 204's step, moved here from QMB so the referee stays home (Level 0 AD-25). It puts
QMB's ledger line and CT-32 artifact verbatim, with three edges:

- ``consumed`` to the dataset card version the backtest read;
- ``uses`` to the bot version it ran;
- ``tests`` to a hypothesis, when one is named.

The trade and equity tables travel inside the result's report blob, so a backtest of millions of
rows stays one object instead of a row per item. Everything else about the object's fields is the
kind's own schema: this step validates nothing twice, so a field the kind does not allow is
refused where kinds are enforced.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Protocol

from qmf.core import fingerprint_bytes

from qmx_judge.runs import (
    BundleRefused,
    Landing,
    RunId,
    RunStatus,
    Ticket,
    mint_run_id,
    new_ulid,
)
from qmx_judge.tries import TRY_KIND, Try, TryState, try_item

__all__ = [
    "BASE_PRINCIPAL",
    "REPORT_SLOT",
    "RESULT_KIND",
    "BacktestLanding",
    "BacktestResult",
    "Lander",
    "LanderPort",
    "LandingPort",
    "Stored",
    "land",
]

BASE_PRINCIPAL: Final[str] = "qmb:backtest"
"""Who puts a backtest result: QMB's own run, not the agent that asked for it."""

REPORT_SLOT: Final[str] = "report"
"""The one blob slot a `backtest-result` kind declares today."""


@dataclass(frozen=True, slots=True)
class Stored:
    """What the Library answered when the object landed."""

    object_id: str


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """One finished QMB backtest, as the landing step receives it.

    ``report`` is the ledger line and the CT-32 artifact verbatim, with the trade and equity
    tables inside it. ``outcome`` is the kind's own word (``supports | refutes | inconclusive``)
    when the run had one to claim.
    """

    run_id: str
    title: str
    summary: str
    world: str
    claim_class: str
    role: str
    fidelity: str
    provenance: Mapping[str, object]
    report: bytes
    outcome: str | None = None
    memo_key: str | None = None


class LandingPort(Protocol):
    """The Library, as this step needs it: one put, then one link per edge."""

    def put(
        self,
        kind: str,
        fields: Mapping[str, object],
        blobs: Mapping[str, bytes],
        *,
        item: str | None,
        title: str,
        summary: str,
        principal: str,
    ) -> Stored: ...

    def link(self, from_id: str, relation: str, to_id: str, *, principal: str) -> str: ...


@dataclass(frozen=True, slots=True)
class BacktestLanding:
    """The object that landed and the edges written from it, in order."""

    object_id: str
    edges: tuple[tuple[str, str], ...]


def land(
    result: BacktestResult,
    library: LandingPort,
    *,
    consumed: str,
    uses: str,
    tests: str | None = None,
    principal: str = BASE_PRINCIPAL,
) -> BacktestLanding:
    """Store one `backtest-result` and link it to its data, its bot and its hypothesis.

    ``consumed`` is the dataset card version the backtest read, ``uses`` the bot version it ran,
    and ``tests`` the hypothesis it was built to test. The result is stored under its QMB run id,
    so a rerun of the same run replaces nothing: QMB names a run by its own fingerprint.
    """
    fields: dict[str, object] = {
        "claim_class": result.claim_class,
        "fidelity": result.fidelity,
        "provenance": dict(result.provenance),
        "role": result.role,
        "world": result.world,
    }
    if result.outcome is not None:
        fields["outcome"] = result.outcome
    if result.memo_key is not None:
        fields["memo_key"] = result.memo_key
    stored = library.put(
        "backtest-result",
        fields,
        {REPORT_SLOT: result.report},
        item=result.run_id,
        title=result.title,
        summary=result.summary,
        principal=principal,
    )
    written: list[tuple[str, str]] = []
    for relation, target in (("consumed", consumed), ("uses", uses), ("tests", tests)):
        if target is None:
            continue
        library.link(stored.object_id, relation, target, principal=principal)
        written.append((relation, target))
    return BacktestLanding(stored.object_id, tuple(written))


RESULT_KIND: Final = "backtest-result"
"""The provides name the lander lands; an app that provides no such output gets no ticket."""

CHECK_JOB: Final = "behaviour_check"

REQUEST_FIELDS: Final = (
    "compiled_fp",
    "markets",
    "window",
    "seed",
    "motion",
    "place",
    "model_cutoff",
)
"""Run request fields a result carries as the core received them."""


class LanderPort(LandingPort, Protocol):
    """The Library as the lander needs it: `find` answers the main object of an item, if any."""

    def find(self, item: str) -> str | None: ...


@dataclass(frozen=True, slots=True)
class Lander:
    """The one lander on the supervisor's job path (Part B CONTRACTS §3, the lander port).

    ``writer`` is the principal the host lands records as. ``provides_of`` answers the provides
    names of an installed app version.
    """

    library: LanderPort
    writer: str
    machine: str
    provides_of: Callable[[str, str], Collection[str]]
    clock: Callable[[], datetime]
    mint: Callable[[], str] = new_ulid

    def open(
        self, app_id: str, version: str, job: str, inputs: Mapping[str, object], principal: str
    ) -> Ticket | None:
        """Mint the run id and land the `opened` try; None for an app that lands no result."""
        if RESULT_KIND not in self.provides_of(app_id, version):
            return None
        unit, study = inputs.get("unit"), inputs.get("study")
        family, given = inputs.get("family", unit), inputs.get("run_id")
        checks = (
            (isinstance(unit, str) and bool(unit), "unit is the pin of the unit version"),
            (study is None or isinstance(study, str), "study is the pin of a study spec"),
            (isinstance(family, str), "family is the root item of the unit's lineage"),
            (given is None or isinstance(given, str), "run_id is one the core minted"),
        )
        problems = [message for ok, message in checks if not ok]
        if problems:
            raise BundleRefused(problems)
        run_id = RunId(str(given)) if given is not None else mint_run_id(self.machine, self.mint())
        place = inputs.get("place")
        opened = Try(
            kind="check" if job == CHECK_JOB else "run",
            state="opened",
            run_id=run_id,
            family=str(family),
            unit=str(unit),
            principal=principal,
            at=self.clock().isoformat(),
            study=None if study is None else str(study),
            tester={"app": app_id, "version": version},
            place=place if isinstance(place, str) else None,
        )
        opened_id = self._once(
            TRY_KIND, try_item(run_id, "opened"), opened.fields(), {}, f"{job} {run_id} opened"
        )
        return Ticket(
            run_id=run_id,
            app_id=app_id,
            version=version,
            job=job,
            principal=principal,
            unit=opened.unit,
            study=opened.study,
            family=opened.family,
            opened=opened_id,
            request=dict(inputs),
        )

    def close(self, landing: Landing) -> str:
        """Land the bundle's `backtest-result`, its edges and the closing try."""
        ticket, bundle = landing.ticket, landing.bundle
        if bundle.run_id != ticket.run_id:
            raise BundleRefused([f"the bundle answers {bundle.run_id}, not {ticket.run_id}"])
        result_id = self.library.find(ticket.run_id)
        if result_id is None:
            fields = _result_fields(ticket, bundle.status, bundle.reason)
            labels = dict(bundle.labels or {})
            if labels:
                fields["labels"] = labels
            if isinstance(labels.get("fidelity"), str):
                fields["fidelity"] = labels["fidelity"]
            if bundle.status == "finished" and bundle.measures:
                fields["measures"] = dict(bundle.measures)
            if bundle.request_fp is not None:
                fields["request_fp"] = bundle.request_fp
            if bundle.versions is not None:
                fields["versions"] = dict(bundle.versions)
            result_id = self._once(
                RESULT_KIND, ticket.run_id, fields, _blobs(landing), _title(ticket, bundle.status)
            )
        self._link(result_id, ticket, [("consumed", card) for card in bundle.consumed])
        state: TryState = "landed" if bundle.status == "finished" else "failed"
        self._closing_try(ticket, state, result_id)
        return result_id

    def fail(self, ticket: Ticket, reason: str, *, status: RunStatus = "killed") -> str:
        """Land a result the tester never finished: its status and reason, no measures."""
        result_id = self.library.find(ticket.run_id)
        if result_id is None:
            fields = _result_fields(ticket, status, reason)
            result_id = self._once(RESULT_KIND, ticket.run_id, fields, {}, _title(ticket, status))
        self._link(result_id, ticket, [])
        self._closing_try(ticket, "failed", result_id)
        return result_id

    def _closing_try(self, ticket: Ticket, state: TryState, result_id: str) -> None:
        closing = Try(
            kind="check" if ticket.job == CHECK_JOB else "run",
            state=state,
            run_id=ticket.run_id,
            family=ticket.family,
            unit=ticket.unit,
            principal=ticket.principal,
            at=self.clock().isoformat(),
            study=ticket.study,
            tester={"app": ticket.app_id, "version": ticket.version},
            links=(ticket.opened, result_id),
        )
        title = f"{ticket.job} {ticket.run_id} {state}"
        self._once(TRY_KIND, try_item(ticket.run_id, state), closing.fields(), {}, title)

    def _link(self, result_id: str, ticket: Ticket, edges: list[tuple[str, str]]) -> None:
        """Write the result's edges; the Library keeps one of each, so a retry adds none."""
        edges.append(("uses", ticket.unit))
        if ticket.study is not None:
            edges.append(("tests", ticket.study))
        for relation, target in edges:
            self.library.link(result_id, relation, target, principal=self.writer)

    def _once(
        self,
        kind: str,
        item: str,
        fields: Mapping[str, object],
        blobs: Mapping[str, bytes],
        title: str,
    ) -> str:
        found = self.library.find(item)
        if found is not None:
            return found
        stored = self.library.put(
            kind, fields, blobs, item=item, title=title, summary=title, principal=self.writer
        )
        return stored.object_id


def _title(ticket: Ticket, status: RunStatus) -> str:
    return f"{ticket.job} {ticket.run_id} {status}"


def _result_fields(ticket: Ticket, status: RunStatus, reason: str | None) -> dict[str, object]:
    request = ticket.request
    fields: dict[str, object] = {
        "run_id": ticket.run_id,
        "status": status,
        "kind": ticket.job,
        "tester": {"app": ticket.app_id, "version": ticket.version},
        "unit": ticket.unit,
        "principal": ticket.principal,
        "world": "stress" if request.get("purpose") == "stress" else "backtest",
    }
    if ticket.study is not None:
        fields["study"] = ticket.study
    if reason is not None:
        fields["reason"] = reason
    fields.update({name: request[name] for name in REQUEST_FIELDS if name in request})
    return fields


def _blobs(landing: Landing) -> dict[str, bytes]:
    """Every bundle file, read from the run's output folder and checked against its fp."""
    root = landing.output_dir.resolve()
    problems: list[str] = []
    blobs: dict[str, bytes] = {}
    for file in landing.bundle.files:
        path = (root / file.path).resolve()
        if not path.is_relative_to(root):
            problems.append(f"{file.slot}: {file.path} is outside the run's output folder")
            continue
        try:
            data = path.read_bytes()
        except OSError:
            problems.append(f"{file.slot}: {file.path} is missing")
            continue
        if fingerprint_bytes(data).value != file.fp:
            problems.append(f"{file.slot}: {file.path} does not match its fingerprint")
            continue
        blobs[file.slot] = data
    if problems:
        raise BundleRefused(problems)
    return blobs
