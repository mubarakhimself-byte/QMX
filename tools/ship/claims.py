"""Claims: which program builds which files right now (FACTORY-DESIGN 3.7, 11.5; unit U38).

Rows live in `<plans>/_records/CLAIMS.tsv` (`program kind pattern since released`), where `<plans>` is
the folder that holds the program folders. Every change is made under `records.lock` and committed. A
program folder outside a plans worktree (no `_records/CLAIMS.tsv` beside it) claims nothing.

- `claim(program, patterns)`: `claim` rows for the patterns this program has not claimed yet; returns
  the overlaps with other programs' live claims as (pattern, other program, other pattern). A pattern a
  `shared_generated` glob names is never claimed: the merge rebuilds those files.
- `notice(program, patterns)`: `notice` rows (an audit's or a plan's area); notices never block.
- `release(program, patterns=None)`: stamps `released` on this program's live rows (all, or those).
- `live(exclude=None)`: live claim and notice rows.
- `sweep(settings)`: releases the rows of programs whose folder is gone, that are abandoned, or whose
  every stop is merged while no conveyor runs them.
- `blocked_slices(slices, overlaps)`: slice id -> the program holding a file it names.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from ship import clock
from ship import records
from ship.layout import Program, Records, records_of
from ship.plan import matches, overlaps
from ship.settings import Settings

COLUMNS = ("program", "kind", "pattern", "since", "released")


def family(a: str, b: str) -> bool:
    """One program, or a program and its own fix program: they build on one branch, never against each other."""
    return a == b or a.startswith(b + "-fix-") or b.startswith(a + "-fix-")


@dataclasses.dataclass
class Row:
    program: str
    kind: str
    pattern: str
    since: str
    released: str = ""

    def line(self) -> str:
        return "\t".join((self.program, self.kind, self.pattern, self.since, self.released)) + "\n"


class Claims:
    def __init__(self, plans: Path, settings: Settings, shared: list[str] | None = None):
        self.plans = plans
        self.records: Records = records_of(plans)
        self.settings = settings
        self.shared = list(shared or [])
        self.lines: list[str] = []

    @property
    def active(self) -> bool:
        return self.records.claims.exists()

    def read(self) -> list[Row]:
        if not self.active:
            return []
        rows = []
        for line in self.records.claims.read_text("utf-8").splitlines()[1:]:
            cells = line.split("\t")
            if len(cells) >= 4 and cells[0]:
                rows.append(Row(*(cells + [""] * (5 - len(cells)))[:5]))
        return rows

    def _write(self, rows: list[Row], message: str) -> None:
        text = "\t".join(COLUMNS) + "\n" + "".join(r.line() for r in rows)
        self.records.claims.write_text(text, "utf-8", newline="\n")
        records.commit(self.plans, message, self.settings, lines=self.lines)

    def live(self, exclude: str | None = None) -> list[Row]:
        return [r for r in self.read() if not r.released and r.program != exclude]

    def shared_file(self, pattern: str) -> bool:
        return any(matches(glob, pattern) or glob == pattern for glob in self.shared)

    def claim(self, program: str, patterns: list[str], kind: str = "claim") -> list[tuple[str, str, str]]:
        if not self.active:
            return []
        wanted = list(dict.fromkeys(p for p in patterns if not self.shared_file(p)))
        with records.locked(self.records):
            rows = self.read()
            mine = {r.pattern for r in rows if r.program == program and r.kind == kind and not r.released}
            stamp = clock.now().isoformat(timespec="seconds")
            new = [Row(program, kind, p, stamp) for p in wanted if p not in mine]
            if new:
                self._write(rows + new, f"claims: {program} {kind}s {len(new)} patterns")
            others = [r for r in rows if not r.released and not family(r.program, program) and r.kind == "claim"]
        if kind != "claim":
            return []
        found = []
        for pattern in wanted:
            for other in others:
                if overlaps([pattern], [other.pattern]):
                    found.append((pattern, other.program, other.pattern))
        return found

    def notice(self, program: str, patterns: list[str]) -> None:
        self.claim(program, patterns, kind="notice")

    def overlaps_now(self, program: str, patterns: list[str]) -> list[tuple[str, str, str]]:
        """The overlaps of `patterns` with other programs' live claims, without writing anything."""
        found = []
        for other in self.live(exclude=program):
            if other.kind != "claim" or family(other.program, program):
                continue
            for pattern in patterns:
                if not self.shared_file(pattern) and overlaps([pattern], [other.pattern]):
                    found.append((pattern, other.program, other.pattern))
        return found

    def release(self, program: str, patterns: list[str] | None = None) -> int:
        if not self.active:
            return 0
        with records.locked(self.records):
            rows = self.read()
            stamp = clock.now().isoformat(timespec="seconds")
            n = 0
            for r in rows:
                if r.program == program and not r.released and (patterns is None or r.pattern in patterns):
                    r.released = stamp
                    n += 1
            if n:
                self._write(rows, f"claims: {program} releases {n} patterns")
        return n

    def sweep(self) -> list[str]:
        """Release the rows of programs that are gone, abandoned, or merged with no conveyor."""
        if not self.active:
            return []
        out = []
        for name in sorted({r.program for r in self.live()}):
            why = finished(Program(self.plans / name), self.settings)
            if why:
                n = self.release(name)
                out.append(f"SWEPT {name}: {n} rows ({why})")
        return out


def finished(program: Program, settings: Settings) -> str:
    """Why a program's claims may go: "gone", "abandoned", "merged", or "" while it may still build."""
    from ship import phase
    from ship import program as prog
    from ship import state as st

    if not program.dir.is_dir():
        return "gone"
    if not program.project_file.exists():
        return ""
    try:
        index = prog.load(program)
    except prog.ProgramError:
        return ""
    if index.abandoned:
        return "abandoned"
    alive, _ = phase.conveyor(program)
    if alive or not program.state.exists() or not index.stops:
        return ""
    merged = set(st.load(program).merged)
    return "merged" if all(s.id in merged or s.merged for s in index.stops) else ""


def for_program(program: Program, settings: Settings) -> Claims:
    """The claims list beside a program folder, with its project's shared-generated globs."""
    from ship import profile

    shared = profile.of_program(program.dir, settings)["project"].get("shared_generated") or []
    return Claims(program.dir.parent, settings, shared)


def blocked_slices(slices, found: list[tuple[str, str, str]]) -> dict[str, str]:
    """slice id -> the other program whose live claim names one of its files."""
    out: dict[str, str] = {}
    for sl in slices:
        for _, other, other_pattern in found:
            if overlaps(sl.files, [other_pattern]):
                out[sl.id] = other
                break
    return out


def slice_files(program: Program) -> list[str]:
    from ship.plan import PlanError, parse_slices

    try:
        return [f for s in parse_slices(program.slices_md.read_text("utf-8")) for f in s.files]
    except (OSError, PlanError):
        return []
