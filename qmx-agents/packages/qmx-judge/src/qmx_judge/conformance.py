"""The conformance pack: the core proves a tester before it may become the default (AD-206).

The pack is golden runs of Part A's dummy unit over a fixture dataset shipped beside this
module (`conformance_pack/`). A tester's `conformance` job only replays the pack's cases and
leaves their raw rows: trades, fills, cash events and holes. The core reads those rows from the
result it landed, puts each in one canonical form, fingerprints the lists itself and compares
them with the golden fingerprints. Nothing a tester says about itself counts: its measures, its
labels and any hash it computed are never read (QB-13, QB-24). The verdict lands as the core's
`test-report`, `check = "qmb-conformance/1"`, stamped with the tester's exact app and version.

`[qmb] default_tester` may name only a tester whose newest report on the current pack passed
(`unproven`). The goldens are made by the shipped tester and written only by `write_golden`,
which the pack's regeneration script calls in the PR that changes QML, the checker or QMB.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Final, Protocol, cast

from qmf.core import fingerprint_bytes

from qmx_judge.landing import TEST_REPORT, LandingPort, RunJob

__all__ = [
    "CHECK",
    "JOB",
    "LISTS",
    "PACK",
    "Case",
    "CaseVerdict",
    "ConformanceLibrary",
    "Diff",
    "Pack",
    "Verdict",
    "canonical",
    "judge_output",
    "list_fp",
    "load_pack",
    "pack_inputs",
    "run_conformance",
    "unproven",
    "write_golden",
]

CHECK: Final = "qmb-conformance/1"
"""The `check` of a tester's conformance `test-report`."""
JOB: Final = "jobs/conformance.py"
"""The run kind every tester implements (CONTRACTS §1)."""
OUTPUT: Final = "qmx.conformance.output/1"
"""The schema of the one report file a tester's conformance job leaves."""
PACK_SCHEMA: Final = "qmx.conformance.pack/1"
"""The schema of the pack as a conformance job's inputs carry it."""
PACK: Final[Traversable] = files("qmx_judge") / "conformance_pack"
PACK_KIND: Final = "dataset"
"""The pack lands once as a `dataset` record: the object a conformance run `uses`."""


@dataclass(frozen=True, slots=True)
class Spec:
    """One raw list a tester leaves per case: the fields the core compares and the row order."""

    fields: tuple[str, ...]
    optional: tuple[str, ...]
    order: tuple[str, ...]


LISTS: Final[Mapping[str, Spec]] = {
    "trades": Spec(
        fields=(
            "market_id",
            "side",
            "opened_at",
            "closed_at",
            "entry_price",
            "exit_price",
            "stop",
            "quantity",
            "exit_kind",
            "money",
            "r",
        ),
        optional=("gap_through_stop",),
        order=("opened_at", "market_id"),
    ),
    "fills": Spec(
        fields=(
            "instant",
            "market_id",
            "kind",
            "side",
            "price",
            "quantity",
            "receipt_quantity",
            "residue_r",
        ),
        optional=(),
        order=("instant", "market_id", "kind"),
    ),
    "cash_events": Spec(
        fields=("instant", "market_id", "kind", "money", "detail"),
        optional=(),
        order=("instant", "market_id", "kind"),
    ),
    "holes": Spec(
        fields=("market_id", "after", "before", "bars_missing"),
        optional=(),
        order=("after", "market_id"),
    ),
}
"""What a case's output holds. Trade and position ids are left out: they are a tester's names,
not what a unit earned, so two testers that trade alike compare alike."""

type Row = dict[str, str]


def _text(value: object) -> str | None:
    """A raw value as the one text the core compares; a float or a structure has none, because
    no binary float reaches a price, a quantity or money."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | str):
        return str(value)
    return None


def _sort_key(row: Row, order: Sequence[str]) -> tuple[tuple[int, int, str], ...]:
    def part(text: str) -> tuple[int, int, str]:
        digits = text.removeprefix("-")
        return (0, int(text), "") if digits.isdigit() else (1, 0, text)

    return tuple(part(row[name]) for name in order)


def canonical(name: str, raw: object) -> tuple[Row, ...] | str:
    """A tester's raw list in the core's form, in the list's order, or why it has none."""
    spec = LISTS[name]
    if not isinstance(raw, list):
        return f"{name} is a list of rows"
    rows: list[Row] = []
    for index, entry in enumerate(cast("list[object]", raw)):
        if not isinstance(entry, Mapping):
            return f"{name}[{index}] is an object"
        found = cast("Mapping[str, object]", entry)
        row: Row = {}
        for field in (*spec.fields, *spec.optional):
            if field not in found:
                if field in spec.fields:
                    return f"{name}[{index}] has no {field}"
                continue
            text = _text(found[field])
            if text is None:
                return f"{name}[{index}].{field} is text or a whole number, never {found[field]!r}"
            row[field] = text
        rows.append(row)
    return tuple(sorted(rows, key=lambda row: _sort_key(row, spec.order)))


def list_fp(rows: Sequence[Row]) -> str:
    """The fingerprint of one canonical list: its rows as sorted-key JSON, in order."""
    data = json.dumps(list(rows), sort_keys=True, separators=(",", ":")).encode()
    return fingerprint_bytes(data).value


@dataclass(frozen=True, slots=True)
class Case:
    """One golden run: the request fields the core writes for it and each list's golden rows."""

    case: str
    request: Mapping[str, object]
    golden: Mapping[str, tuple[Row, ...]]
    golden_fp: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class Pack:
    """The pack as the core reads it: its id, its fingerprint, how its goldens were made, its
    cases, and the fixture dataset's files as text by their path under a run's `in/`."""

    id: str
    fp: str
    made: Mapping[str, object]
    cases: tuple[Case, ...]
    fixture: Mapping[str, str]


def _json(root: Traversable, name: str, default: object) -> object:
    found = root / name
    return json.loads(found.read_text("utf-8")) if found.is_file() else default


def load_pack(root: Traversable = PACK) -> Pack:
    """Read the pack. Its fingerprint covers the cases, the goldens and every fixture file's
    text as parsed JSON, so a checkout that changes line endings changes neither."""
    manifest = cast("dict[str, object]", _json(root, "pack.json", None))
    golden = cast("dict[str, object]", _json(root, "golden.json", {"cases": {}}))
    fixture = cast("dict[str, str]", _json(root, "fixture.json", {}))
    made = cast("dict[str, dict[str, object]]", golden["cases"])
    cases: list[Case] = []
    for asked in cast("list[dict[str, object]]", manifest["cases"]):
        name = str(asked["case"])
        lists = made.get(name, {})
        rows = {
            key: tuple(cast("list[Row]", cast("dict[str, object]", body)["rows"]))
            for key, body in lists.items()
        }
        fps = {key: str(cast("dict[str, object]", body)["fp"]) for key, body in lists.items()}
        cases.append(Case(name, cast("dict[str, object]", asked["request"]), rows, fps))
    every = {"pack": manifest, "golden": golden, "fixture": fixture}
    data = json.dumps(every, sort_keys=True, separators=(",", ":")).encode()
    return Pack(
        id=str(manifest["id"]),
        fp=fingerprint_bytes(data).value,
        made={key: value for key, value in golden.items() if key != "cases"},
        cases=tuple(cases),
        fixture=fixture,
    )


def pack_inputs(pack: Pack, dataset: str) -> dict[str, object]:
    """The conformance job's inputs: the pack's dataset pin, each case's request and the fixture
    files as text, which the tester lays out under its run folder before it replays them."""
    return {
        "unit": dataset,
        "purpose": "conformance",
        "pack": {
            "schema_version": PACK_SCHEMA,
            "id": pack.id,
            "fp": pack.fp,
            "cases": [{"case": case.case, "request": dict(case.request)} for case in pack.cases],
            "files": dict(sorted(pack.fixture.items())),
        },
    }


@dataclass(frozen=True, slots=True)
class Diff:
    """The first row where a tester's list departs from the golden one."""

    list: str
    index: int
    field: str | None
    expected: str | None
    got: str | None
    expected_row: Row | None
    got_row: Row | None

    def says(self) -> str:
        if self.expected_row is None:
            return f"{self.list}[{self.index}] is a row the golden run never made"
        if self.got_row is None:
            return f"{self.list}[{self.index}] is missing"
        return f"{self.list}[{self.index}].{self.field} is {self.got}, golden {self.expected}"

    def fields(self) -> dict[str, object]:
        return {
            "list": self.list,
            "index": self.index,
            "field": self.field,
            "expected": self.expected,
            "got": self.got,
            "expected_row": self.expected_row,
            "got_row": self.got_row,
            "says": self.says(),
        }


def first_diff(name: str, golden: Sequence[Row], got: Sequence[Row]) -> Diff | None:
    """Walk both lists in order; the first differing field is named in the list's field order."""
    spec = LISTS[name]
    for index in range(max(len(golden), len(got))):
        want = golden[index] if index < len(golden) else None
        have = got[index] if index < len(got) else None
        if want == have:
            continue
        if want is None or have is None:
            return Diff(name, index, None, None, None, want, have)
        field = next(f for f in (*spec.fields, *spec.optional) if want.get(f) != have.get(f))
        return Diff(name, index, field, want.get(field), have.get(field), want, have)
    return None


@dataclass(frozen=True, slots=True)
class CaseVerdict:
    case: str
    passed: bool
    fps: Mapping[str, str]
    diff: Diff | None = None
    reason: str | None = None

    def fields(self) -> dict[str, object]:
        body: dict[str, object] = {
            "case": self.case,
            "verdict": "pass" if self.passed else "fail",
            "fps": dict(self.fps),
        }
        if self.diff is not None:
            body["diff"] = self.diff.fields()
        if self.reason is not None:
            body["reason"] = self.reason
        return body


@dataclass(frozen=True, slots=True)
class Verdict:
    cases: tuple[CaseVerdict, ...]

    @property
    def passed(self) -> bool:
        return bool(self.cases) and all(case.passed for case in self.cases)

    def says(self) -> str:
        if self.passed:
            return f"passed all {len(self.cases)} cases"
        failed = next(case for case in self.cases if not case.passed)
        why = failed.diff.says() if failed.diff is not None else failed.reason
        return f"failed {failed.case}: {why}"


def _case_output(output: object, case: str) -> Mapping[str, object] | str:
    if not isinstance(output, Mapping):
        return f"the tester's report is no {OUTPUT} object"
    found = cast("Mapping[str, object]", output)
    if found.get("schema_version") != OUTPUT:
        return f"the tester's report is no {OUTPUT} object"
    cases = found.get("cases")
    entry = cast("Mapping[str, object]", cases).get(case) if isinstance(cases, Mapping) else None
    if not isinstance(entry, Mapping):
        return f"the tester left no output for {case}"
    body = cast("Mapping[str, object]", entry)
    if body.get("status") != "finished":
        return f"the tester did not finish {case}: {body.get('reason', 'no reason given')}"
    return body


def judge_output(pack: Pack, output: object) -> Verdict:
    """The core's verdict over a tester's raw report: every list fingerprinted here and compared
    with the golden one. A case passes only when every list matches."""
    verdicts: list[CaseVerdict] = []
    for case in pack.cases:
        body = _case_output(output, case.case)
        if isinstance(body, str):
            verdicts.append(CaseVerdict(case.case, False, {}, reason=body))
            continue
        fps: dict[str, str] = {}
        diff: Diff | None = None
        reason: str | None = None
        for name in LISTS:
            rows = canonical(name, body.get(name))
            if isinstance(rows, str):
                reason = reason or rows
                continue
            fps[name] = list_fp(rows)
            if diff is None and fps[name] != case.golden_fp.get(name):
                diff = first_diff(name, case.golden.get(name, ()), rows)
        if not case.golden_fp:
            reason = reason or f"the pack holds no golden run for {case.case}"
        passed = reason is None and diff is None
        verdicts.append(CaseVerdict(case.case, passed, fps, diff, reason))
    return Verdict(tuple(verdicts))


class ConformanceLibrary(LandingPort, Protocol):
    """The Library as a conformance run needs it: the lander's put and link, `find` by item, and
    the fields and report blob of an object the core landed."""

    def find(self, item: str) -> str | None: ...

    def read(self, object_id: str) -> tuple[Mapping[str, object], bytes | None]: ...


@dataclass(frozen=True, slots=True)
class ConformanceRun:
    run_id: str
    result_id: str
    report_id: str
    verdict: Verdict


def _dataset(library: ConformanceLibrary, pack: Pack, writer: str) -> str:
    """The pack as a `dataset` record, landed once per pack fingerprint."""
    item = f"conformance-pack/{pack.id}/{pack.fp.removeprefix('fp1:')[:16]}"
    found = library.find(item)
    if found is not None:
        return found
    fields: dict[str, object] = {
        "source": "qmx-judge conformance pack",
        "subject": pack.id,
        "kind": "conformance-pack",
        "partition_digests": [pack.fp],
    }
    title = f"Conformance pack {pack.id}"
    return library.put(
        PACK_KIND, fields, {}, item=item, title=title, summary=title, principal=writer
    ).object_id


def run_conformance(
    app_id: str,
    version: str,
    *,
    run_job: RunJob,
    library: ConformanceLibrary,
    principal: str,
    writer: str = "operator",
    pack: Pack | None = None,
) -> ConformanceRun:
    """Run the pack on one tester through the supervisor's job path, then judge what it left.

    The tester's result lands through the core's lander like any run. The core reads that
    result's report blob back from the Library, judges it with `judge_output` and lands the
    verdict as a `test-report` linked `uses` to the result. Running it again lands a new run and
    a new report; `unproven` reads the newest."""
    pack = pack or load_pack()
    dataset = _dataset(library, pack, writer)
    ran = run_job(app_id, JOB, pack_inputs(pack, dataset), principal)
    run_id = str(ran.get("run_id", ""))
    result_id = library.find(run_id)
    if result_id is None:
        raise ValueError(f"the conformance run {run_id or '(none)'} landed no result")
    fields, report = library.read(result_id)
    if fields.get("status") != "finished" or report is None:
        why = fields.get("reason", "it left no report")
        output: object = {"schema_version": OUTPUT, "cases": {}, "reason": why}
        verdict = Verdict(
            tuple(
                CaseVerdict(case.case, False, {}, reason=f"the run {fields.get('status')}: {why}")
                for case in pack.cases
            )
        )
    else:
        output = json.loads(report)
        verdict = judge_output(pack, output)
    tester = {"app": app_id, "version": version}
    body: dict[str, object] = {
        "check": CHECK,
        "run_id": run_id,
        "status": "finished",
        "tester": tester,
        "tester_pin": f"{app_id}@{version}",
        "pack": {"id": pack.id, "fp": pack.fp},
        "verdict": "pass" if verdict.passed else "fail",
        "says": verdict.says(),
        "cases": [case.fields() for case in verdict.cases],
        "result": result_id,
    }
    title = f"Conformance of {app_id}@{version}: {body['verdict']}"
    report_id = library.find(f"conformance/{run_id}")
    if report_id is None:
        report_id = library.put(
            TEST_REPORT,
            body,
            {},
            item=f"conformance/{run_id}",
            title=title,
            summary=verdict.says(),
            principal=writer,
        ).object_id
    library.link(report_id, "uses", result_id, principal=writer)
    return ConformanceRun(run_id, result_id, report_id, verdict)


def unproven(
    pin: str, reports: Iterable[Mapping[str, object]], pack: Pack | None = None
) -> str | None:
    """Why `pin` (`app@version`) may not be the default tester, or None when its newest report
    on the current pack passed. `reports` are conformance `test-report` fields, oldest first."""
    pack = pack or load_pack()
    mine = [
        report
        for report in reports
        if report.get("check") == CHECK
        and report.get("tester_pin") == pin
        and cast("Mapping[str, object]", report.get("pack") or {}).get("fp") == pack.fp
    ]
    if not mine:
        return f"{pin} has no conformance report on the pack {pack.id}; run the pack on it first"
    newest = mine[-1]
    if newest.get("verdict") == "pass":
        return None
    return f"{pin} failed its conformance check: {newest.get('says')}"


def write_golden(
    root: Path, output: Mapping[str, object], made: Mapping[str, object]
) -> dict[str, object]:
    """Write `golden.json` from the shipped tester's raw report. Only the pack's regeneration
    script calls this, in the PR that changes QML, the checker or QMB; a tester never does."""
    manifest = cast("dict[str, object]", json.loads((root / "pack.json").read_text("utf-8")))
    cases: dict[str, object] = {}
    for asked in cast("list[dict[str, object]]", manifest["cases"]):
        name = str(asked["case"])
        body = _case_output(output, name)
        if isinstance(body, str):
            raise ValueError(body)
        lists: dict[str, object] = {}
        for key in LISTS:
            rows = canonical(key, body.get(key))
            if isinstance(rows, str):
                raise ValueError(rows)
            lists[key] = {"fp": list_fp(rows), "rows": list(rows)}
        cases[name] = lists
    golden: dict[str, object] = {**made, "cases": cases}
    (root / "golden.json").write_text(json.dumps(golden, indent=1, sort_keys=True) + "\n", "utf-8")
    return golden
