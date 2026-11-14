"""Parse the planner's handoff: the SLICES.md table, the brief facts, and the files patterns."""

from __future__ import annotations

import dataclasses
import re
import shlex
from pathlib import Path

from ship.state import Slice

SLICE_COLUMNS = {"id": "id", "name": "name", "depends on": "depends_on", "files": "files", "size": "size"}
OPTIONAL_COLUMNS = {"ask": "ask", "stop": "checkpoint", "checkpoint": "checkpoint"}
NONE_WORDS = {"", "-", "none", "n/a"}


class PlanError(Exception):
    pass


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _items(cell: str) -> list[str]:
    if cell.strip().casefold() in NONE_WORDS:
        return []
    return [part.strip().strip("`").strip() for part in cell.split(",") if part.strip().strip("`").strip()]


def _optional(cell: str) -> str:
    cell = cell.strip().strip("`").strip()
    return "" if cell.casefold() in NONE_WORDS else cell


def parse_slices(text: str) -> list[Slice]:
    """The first markdown table whose header holds the columns id, name, depends on, files, size."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        header = [c.casefold() for c in _cells(line)]
        if not set(SLICE_COLUMNS) <= set(header):
            continue
        index = {SLICE_COLUMNS[name]: header.index(name) for name in SLICE_COLUMNS}
        extra = {field: header.index(name) for name, field in OPTIONAL_COLUMNS.items() if name in header}
        slices = []
        for row in lines[i + 2 :]:
            if not row.lstrip().startswith("|"):
                break
            cells = _cells(row)
            sid = cells[index["id"]].strip("`")
            slices.append(
                Slice(
                    id=sid,
                    name=cells[index["name"]],
                    depends_on=_items(cells[index["depends_on"]]),
                    files=[f.replace("\\", "/") for f in _items(cells[index["files"]])],
                    size=cells[index["size"]],
                    **{field: _optional(cells[i]) for field, i in extra.items()},
                )
            )
        ids = [s.id for s in slices]
        if len(ids) != len(set(ids)):
            raise PlanError("SLICES.md repeats a slice id")
        for s in slices:
            missing = [d for d in s.depends_on if d not in ids]
            if missing:
                raise PlanError(f"SLICES.md: {s.id} depends on unknown {missing}")
            if not s.files:
                raise PlanError(f"SLICES.md: {s.id} has no files")
        return slices
    raise PlanError("SLICES.md has no table with columns: id | name | depends on | files | size")


@dataclasses.dataclass(frozen=True)
class Fact:
    id: str
    argv: list[str]
    expect: str
    exit_code: int = 0


FACT_OPEN = re.compile(r"^```fact\s+(?P<id>\S+)(?:\s+exit=(?P<exit>\d+))?\s*$")


def parse_facts(text: str) -> list[Fact]:
    """Each fact is a fenced block: ```fact <ID> [exit=N], then `$ <command>`, then the expected output."""
    facts: list[Fact] = []
    lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        opened = FACT_OPEN.match(lines[i].strip())
        if not opened:
            i += 1
            continue
        body: list[str] = []
        i += 1
        while i < len(lines) and lines[i].strip() != "```":
            body.append(lines[i])
            i += 1
        if i == len(lines):
            raise PlanError(f"fact {opened['id']} has no closing fence")
        if not body or not body[0].startswith("$ "):
            raise PlanError(f"fact {opened['id']} must start with a line `$ <command>`")
        facts.append(
            Fact(
                id=opened["id"],
                argv=shlex.split(body[0][2:], posix=True),
                expect=normalize_output("\n".join(body[1:])),
                exit_code=int(opened["exit"] or 0),
            )
        )
        i += 1
    ids = [f.id for f in facts]
    if len(ids) != len(set(ids)):
        raise PlanError("a brief repeats a fact id")
    return facts


def normalize_output(text: str) -> str:
    """CRLF to LF, trailing spaces off each line, trailing blank lines off the end."""
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).rstrip("\n")


GLOB_CHARS = re.compile(r"[*?\[]")


def _glob_regex(pattern: str) -> re.Pattern[str]:
    out = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def matches(pattern: str, path: str) -> bool:
    """A plain path names a file or a folder; `dir/` and `dir/**` name a folder; `*`, `?`, `**` glob."""
    pattern = pattern.replace("\\", "/")
    path = path.replace("\\", "/")
    if not GLOB_CHARS.search(pattern):
        bare = pattern.rstrip("/")
        return path == bare or path.startswith(bare + "/")
    return bool(_glob_regex(pattern).match(path))


def _literal_prefix(pattern: str) -> str:
    found = GLOB_CHARS.search(pattern)
    return pattern[: found.start()] if found else pattern.rstrip("/")


def _related(a: str, b: str) -> bool:
    """One path is the other, or sits inside it."""
    a, b = a.rstrip("/"), b.rstrip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/") or not a or not b


def _pair_overlaps(x: str, y: str) -> bool:
    gx, gy = bool(GLOB_CHARS.search(x)), bool(GLOB_CHARS.search(y))
    if not gx and not gy:
        return _related(x, y)
    if gx and gy:
        return _related(_literal_prefix(x), _literal_prefix(y))
    glob, plain = (x, y) if gx else (y, x)
    plain = plain.rstrip("/")
    if "." in plain.rsplit("/", 1)[-1]:  # a plain path with an extension is a file
        return matches(glob, plain)
    return matches(glob, plain) or _related(_literal_prefix(glob), plain)


def overlaps(a: list[str], b: list[str]) -> list[tuple[str, str]]:
    """Pairs of patterns that can name one file. Case-insensitive, because Windows is.

    Globs compare by their literal prefix, which over-reports. That is the safe side: a false
    overlap only delays a dispatch.
    """
    found = []
    for pa in a:
        for pb in b:
            x, y = pa.replace("\\", "/").casefold(), pb.replace("\\", "/").casefold()
            if _pair_overlaps(x, y):
                found.append((pa, pb))
    return found


def outside(patterns: list[str], paths: list[str]) -> list[str]:
    return [p for p in paths if not any(matches(pat, p) for pat in patterns)]


def read_brief_facts(brief: Path) -> list[Fact]:
    if not brief.exists():
        raise PlanError(f"no brief at {brief}")
    return parse_facts(brief.read_text("utf-8"))


def init_state(program_dir: Path, repo: Path, build_branch: str, worktree_root: Path, remote: str) -> str:
    """Create state.json from SLICES.md. Run twice, it changes nothing. A changed SLICES.md is refused, because
    slices never change mid-run, with one exception (D-L26 F1): rows added, after the core merged, for a stop
    PROGRAM.yaml marks `handoff: deferred` (the later-handoff's slices) are appended; every existing row must be
    unchanged."""
    from ship import state as st
    from ship.layout import Program

    program = Program(program_dir)
    slices = parse_slices(program.slices_md.read_text("utf-8"))
    if program.state.exists():
        current = st.load(program)
        planned = {s.id: (s.depends_on, s.files) for s in slices}
        held = {s.id: (s.depends_on, s.files) for s in current.slices.values()}
        if planned == held:
            return "state.json already matches SLICES.md"
        added = [s for s in slices if s.id not in held]
        changed = sorted(sid for sid, row in held.items() if planned.get(sid) != row)
        deferred = deferred_stops(program)
        late = sorted({s.checkpoint for s in added if s.checkpoint not in deferred})
        if changed or late or not added:
            raise PlanError("state.json exists and SLICES.md no longer matches it; slices never change mid-run "
                            f"(changed or removed: {changed}; added outside a deferred stop: {late})")
        with st.locked(program) as state:
            for s in added:
                state.slices[s.id] = s
            state.log("init", None, added=[s.id for s in added])
        return f"state.json gained {len(added)} slices of deferred stops: {', '.join(s.id for s in added)}"
    fresh = st.State(repo=str(repo.resolve()), build_branch=build_branch, remote=remote,
                     worktree_root=str(worktree_root.resolve()), slices={s.id: s for s in slices})
    fresh.log("init", None, slices=len(slices))
    st.save(program, fresh)
    return f"state.json created with {len(slices)} slices"


def deferred_stops(program) -> set[str]:
    """The stops PROGRAM.yaml marks `handoff: deferred` (LATER stops whose briefs come after the core merged)."""
    from ship import program as prog

    try:
        return {s.id for s in prog.load(program).stops if s.handoff == "deferred"}
    except (prog.ProgramError, OSError):
        return set()
