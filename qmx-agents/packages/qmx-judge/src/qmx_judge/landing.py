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

import json
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import Final, Protocol, cast

from qmf.core import fingerprint_bytes

from qmx_judge.runs import (
    BundleRefused,
    Landing,
    RunStatus,
    Ticket,
    mint_run_id,
    new_ulid,
)
from qmx_judge.tries import TRY_KIND, Try, TryState, try_item

__all__ = [
    "BASE_PRINCIPAL",
    "CHECK_KIND",
    "G_CHECK",
    "REPORT_SLOT",
    "RESULT_KIND",
    "TEST_REPORT",
    "BacktestLanding",
    "BacktestResult",
    "CheckFirst",
    "GRecord",
    "GRecords",
    "Lander",
    "LanderPort",
    "LandingPort",
    "RunJob",
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

CHECK_KIND: Final = "behaviour_check"
"""The run kind of checker layer G, whose result is the unit's `test-report`, not a backtest."""
G_CHECK: Final = "qml-g/1"
"""The `check` a `test-report` names when it is a unit's layer G record (Part A CONTRACTS §3.3)."""
TEST_REPORT: Final = "test-report"


def run_kind(job: str) -> str:
    """A job's run kind: its entrypoint's stem, `jobs/<kind>.py` in a tester (CONTRACTS §1)."""
    return PurePosixPath(job).stem


def check_job(job: str) -> str:
    """The behaviour check's entrypoint beside `job`, laid out the same way."""
    path = PurePosixPath(job)
    return str(path.with_name(f"{CHECK_KIND}{path.suffix}"))


@dataclass(frozen=True, slots=True)
class GRecord:
    """A unit's recorded layer G verdict for one compiled fingerprint."""

    object_id: str
    safety_passed: bool


class GRecords(Protocol):
    """What the host answers about a unit's compile and its G verdicts."""

    def compiled_fingerprint(self, unit: str) -> str | None:
        """The fingerprint `unit` compiles to, or None when the pin names no unit document."""
        ...

    def g_record(self, compiled_fp: str) -> GRecord | None:
        """The finished layer G `test-report` of that fingerprint, if one landed."""
        ...


type RunJob = Callable[[str, str, Mapping[str, object], str], Mapping[str, object]]
"""`(app_id, job, inputs, principal) -> what ran`: the supervisor's own `run_job`."""


@dataclass(frozen=True, slots=True)
class CheckFirst:
    """What `open` needs to run the behaviour check before a run whose unit has no G record
    (Part B AD-202 step 1): the supervisor's `run_job`, which the host injects, and the host's
    answers about the unit's compile and its G records."""

    run_job: RunJob
    records: GRecords


def _text(value: object) -> bool:
    return isinstance(value, str)


def _texts(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(entry, str) for entry in value)  # pyright: ignore[reportUnknownVariableType]


def _text_map(*keys: str) -> Callable[[object], bool]:
    def check(value: object) -> bool:
        if not isinstance(value, Mapping):
            return False
        entries: Mapping[object, object] = value  # pyright: ignore[reportUnknownVariableType]
        return all(isinstance(entries.get(key, ""), str) for key in keys)

    return check


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _motion(value: object) -> bool:
    return value in ("on", "off", "both")


REQUEST_FIELDS: Final[Mapping[str, tuple[Callable[[object], bool], str]]] = {
    "compiled_fp": (_text, "compiled_fp is text"),
    "markets": (_texts, "markets is a list of text"),
    "window": (_text_map("start", "end"), "window is an object of text start and end"),
    "seed": (_integer, "seed is an integer"),
    "motion": (_motion, "motion is one of on, off, both"),
    "place": (_text, "place is text"),
    "model_cutoff": (_text_map("model", "cutoff"), "model_cutoff is an object of text"),
}
"""Run request fields a result carries as the core received them, each with the check `open`
makes before any try lands, so `close` and `fail` always build a result the kind accepts."""


class LanderPort(LandingPort, Protocol):
    """The Library as the lander needs it: `find` answers the main object of an item, if any."""

    def find(self, item: str) -> str | None: ...


@dataclass(frozen=True, slots=True)
class Lander:
    """The one lander on the supervisor's job path (Part B CONTRACTS §3, the lander port).

    ``writer`` is the principal the host lands records as. ``provides_of`` answers the provides
    names of an installed app version. With ``check_first``, a run of a unit document pins the
    fingerprint the unit compiles to, and runs only after a passing layer G verdict for it.
    """

    library: LanderPort
    writer: str
    machine: str
    provides_of: Callable[[str, str], Collection[str]]
    clock: Callable[[], datetime]
    mint: Callable[[], str] = new_ulid
    check_first: CheckFirst | None = None

    def open(
        self, app_id: str, version: str, job: str, inputs: Mapping[str, object], principal: str
    ) -> Ticket | None:
        """Mint the run id and land the `opened` try; None for an app that lands no result.

        A request's `compiled_fp` defaults to what its unit compiles to; a check always runs on
        that one, so a caller's pin can make a run fail but never a G record lie."""
        if RESULT_KIND not in self.provides_of(app_id, version):
            return None
        unit, study = inputs.get("unit"), inputs.get("study")
        family = inputs.get("family", unit)
        checks = [
            (isinstance(unit, str) and bool(unit), "unit is the pin of the unit version"),
            (study is None or isinstance(study, str), "study is the pin of a study spec"),
            (isinstance(family, str), "family is the root item of the unit's lineage"),
            ("run_id" not in inputs, "run_id is minted by the lander, never by the request"),
        ]
        checks += [
            (check(inputs[name]), message)
            for name, (check, message) in REQUEST_FIELDS.items()
            if name in inputs
        ]
        problems = [message for ok, message in checks if not ok]
        if problems:
            raise BundleRefused(problems)
        request = dict(inputs)
        checking = run_kind(job) == CHECK_KIND
        compiled = (
            None
            if self.check_first is None
            else self.check_first.records.compiled_fingerprint(str(unit))
        )
        if compiled is not None:
            request["compiled_fp"] = compiled if checking else request.get("compiled_fp", compiled)
            if not checking:
                self._behaviour_first(app_id, job, request, compiled, principal)
        run_id = mint_run_id(self.machine, self.mint())
        place = inputs.get("place")
        opened = Try(
            kind="check" if checking else "run",
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
            request=request,
        )

    def _behaviour_first(
        self, app_id: str, job: str, request: Mapping[str, object], compiled: str, principal: str
    ) -> None:
        """Run the unit's behaviour check on the same tester when no G verdict is recorded for
        `compiled`, then refuse the run unless that verdict's safety half passed."""
        first = cast(CheckFirst, self.check_first)
        found = first.records.g_record(compiled)
        if found is None:
            ran = first.run_job(
                app_id, check_job(job), {**request, "compiled_fp": compiled}, principal
            )
            found = first.records.g_record(compiled)
            if found is None:
                report = self.library.find(str(ran.get("run_id", "")))
                raise BundleRefused(
                    [f"the behaviour check of {compiled} gave no verdict; its report is {report}"]
                )
        if not found.safety_passed:
            raise BundleRefused(
                [
                    f"the unit failed the safety half of its behaviour check; its report is "
                    f"{found.object_id}"
                ]
            )

    def close(self, landing: Landing) -> str:
        """Land the bundle's `backtest-result` (a check's `test-report`), its edges and the
        closing try."""
        ticket, bundle = landing.ticket, landing.bundle
        if bundle.run_id != ticket.run_id:
            raise BundleRefused([f"the bundle answers {bundle.run_id}, not {ticket.run_id}"])
        if run_kind(ticket.job) == CHECK_KIND:
            return self._close_check(landing)
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
        if run_kind(ticket.job) == CHECK_KIND:
            return self._check_report(ticket, status, {"reason": reason}, None)
        result_id = self.library.find(ticket.run_id)
        if result_id is None:
            fields = _result_fields(ticket, status, reason)
            result_id = self._once(RESULT_KIND, ticket.run_id, fields, {}, _title(ticket, status))
        self._link(result_id, ticket, [])
        self._closing_try(ticket, "failed", result_id)
        return result_id

    def _close_check(self, landing: Landing) -> str:
        """A check's leave is its behaviour report, landed as the unit's `test-report`."""
        bundle = landing.bundle
        if bundle.status != "finished":
            return self._check_report(
                landing.ticket, bundle.status, {"reason": bundle.reason or "failed"}, None
            )
        report = cast(dict[str, object], json.loads(_blobs(landing)[REPORT_SLOT]))
        safety = cast(dict[str, object], report.pop("safety", {}))
        return self._check_report(landing.ticket, "finished", report, safety)

    def _check_report(
        self,
        ticket: Ticket,
        status: RunStatus,
        behaviour: Mapping[str, object],
        safety: Mapping[str, object] | None,
    ) -> str:
        """Land the check's `test-report` once, link it `tests` to the unit, close its try. Only
        a finished check carries a `safety` half, so only it is a G verdict."""
        report_id = self.library.find(ticket.run_id)
        if report_id is None:
            fields: dict[str, object] = {
                "check": G_CHECK,
                "run_id": ticket.run_id,
                "status": status,
                "compiled_fingerprint": str(ticket.request.get("compiled_fp", "")),
                "behaviour": dict(behaviour),
            }
            if safety is not None:
                fields["safety"] = dict(safety)
            report_id = self._once(TEST_REPORT, ticket.run_id, fields, {}, _title(ticket, status))
        self.library.link(report_id, "tests", ticket.unit, principal=self.writer)
        self._closing_try(ticket, "landed" if status == "finished" else "failed", report_id)
        return report_id

    def _closing_try(self, ticket: Ticket, state: TryState, result_id: str) -> None:
        closing = Try(
            kind="check" if run_kind(ticket.job) == CHECK_KIND else "run",
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
        "kind": run_kind(ticket.job),
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
