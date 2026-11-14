"""ship trace: the map a checkpoint review reads first (unit U09, FACTORY-DESIGN 2.7 step 2).

`trace(program, stop, settings)` writes `stop-review/<stop>/MAP.md` from `PROGRAM.yaml` (`chains`),
`state.json`, each brief's `Chain:` line and `git log --first-parent --reverse --name-only` over the
checkpoint (`from..tip`, from `notes/stop-<stop>.json`, or the fix program's for round 2):

- per ask: its plan lines, elements, interfaces and slices, each slice's state and landed commit;
- commits with no chain: a subject that starts with no slice id of this program or of its fix programs,
  and that is not a kit commit; each is a FAIL line. A kit commit is known by what it is, never by its
  subject (D-L22): a merge commit, or one whose files are all generator paths (`ci/baselines/`,
  `contracts/` and the profile's `[generators]` patterns);
- seams: every element, edge case or file that two or more slices of the stop touched;
- the scenario ledger: every `E` id in the stop's briefs (section 7a lines), the test named for it,
  and that test's result in `checks/` (a missing or failing test is a FAIL line);
- removed rows on the stop's files (the program's `REMOVED.md` and `_records/REMOVED.md` beside the
  program folder), and for each row a brief guards with a `CALLERS` or `GUARD*` fact, that fact's
  result at the tip (a mismatch is a FAIL line);
- every `DECISION` line of `evidence/*/*/report.md` and every line of `notes/CHAIN-ISSUES.md`.

It returns (no FAIL line, the printed lines). The review still runs on a FAIL; the verdict worker
must turn each one into an Important, and `ship review` refuses a CLEAN verdict while one stands.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ship import program as prog
from ship import state as st
from ship.dispatch import run_facts
from ship.gitx import GitError, git
from ship.layout import Program
from ship.plan import PlanError, parse_facts, parse_slices
from ship.settings import Settings
from ship.worktree import checkout_copy, drop_copy

GENERATOR_PATHS = ("ci/baselines/", "contracts/")  # what the kit's generator commits may touch
CHAIN_LINE = re.compile(r"^Chain:\s*(.*)$", re.M)
SCENARIO = re.compile(r"^\s*[-*]\s*`?(E[0-9][A-Za-z0-9.-]*)`?\b(.*)$")
TEST_NAME = re.compile(r"\(test:\s*`?([^`)]+?)`?\s*\)")
R_ID = re.compile(r"\bR-[A-Za-z0-9_.-]+-\d+\b")
DECISION = re.compile(r"^\s*[-*]?\s*DECISION\b.*$", re.M)
GUARD_FACT = re.compile(r"^(CALLERS|GUARD[A-Za-z0-9_-]*)$")


class TraceError(Exception):
    pass


def stop_range(program: Program, stop: str) -> tuple[str, str]:
    """(from, tip) of a stop from its note."""
    note = program.stop_note(stop)
    try:
        body = json.loads(note.read_text("utf-8"))
    except (OSError, ValueError) as exc:
        raise TraceError(f"no readable {note}: {exc}") from exc
    if not body.get("tip"):
        raise TraceError(f"{note} names no tip")
    return str(body.get("from") or ""), str(body["tip"])


def fix_programs(program: Program) -> list[Program]:
    return [Program(p) for p in sorted(program.dir.parent.glob(f"{program.dir.name}-fix-*")) if p.is_dir()]


def slice_ids(program: Program) -> set[str]:
    """Every slice id of this program and its fix programs."""
    ids: set[str] = set()
    for folder in [program, *fix_programs(program)]:
        try:
            ids |= {s.id for s in parse_slices(folder.slices_md.read_text("utf-8"))}
        except (OSError, PlanError):
            continue
    return ids


def commits(repo: Path, base: str, tip: str, settings: Settings) -> list[tuple[str, list[str], str, list[str]]]:
    """(sha, parents, subject, files) on the first-parent line from base to tip, oldest first. A merge
    commit lists no files (git shows none for a merge without -m)."""
    span = f"{base}..{tip}" if base else tip
    out = git(repo, "log", "--first-parent", "--reverse", "--name-only", "--format=%x00%H%x01%P%x01%s", span,
              timeout=settings.git_timeout_s)
    found = []
    for block in out.split("\x00")[1:]:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        sha, parents, subject = (lines[0].split("\x01") + ["", ""])[:3]
        found.append((sha, parents.split(), subject, lines[1:]))
    return found


def generator_patterns(profile: dict | None) -> list[str]:
    return [*GENERATOR_PATHS, *((profile or {}).get("generators") or {}).keys()]


def kit_commit(parents: list[str], files: list[str], patterns: list[str]) -> bool:
    """A commit the kit writes on a build branch: a merge of the target (two parents), or a generator
    commit whose every file is a generator path. Never judged by its subject (D-L22)."""
    from ship.plan import matches

    if len(parents) > 1:
        return True
    return bool(files) and all(any(matches(p, f) for p in patterns) for f in files)


def kit_line_problem(repo: Path, older: str, newer: str, patterns: list[str], settings: Settings) -> str | None:
    """None when `newer` follows `older` on its first-parent line through kit commits only (the rule for
    `ship merge`'s MERGE-BASE, D-L22), else why not."""
    from ship.gitx import is_ancestor

    if not is_ancestor(repo, older, newer, settings.git_timeout_s):
        return f"{newer[:10]} does not contain {older[:10]}"
    found = commits(repo, older, newer, settings)
    if not found:
        return None
    if found[0][1][:1] != [older]:
        return f"the first-parent line of {newer[:10]} does not run through {older[:10]}"
    for sha, parents, subject, files in found:
        if not kit_commit(parents, files, patterns):
            return f"{sha[:10]} {subject!r} is not a merge or generator commit"
    return None


def owner(subject: str, ids: set[str]) -> str | None:
    """The slice id a commit subject starts with (`<id>: ...`), or None."""
    head = subject.split(":", 1)[0].strip() if ":" in subject else ""
    return head if head in ids else None


def brief_text(program: Program, sid: str) -> str:
    for folder in [program, *fix_programs(program)]:
        path = folder.brief(sid)
        if path.exists():
            return path.read_text("utf-8", errors="replace")
    return ""


def scenarios(text: str) -> list[tuple[str, str, str]]:
    """(E id, the line, the test it names or "") from a brief's section 7a."""
    out = []
    in_7a = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_7a = line.startswith("## 7a")
            continue
        m = SCENARIO.match(line) if in_7a else None
        if m:
            test = TEST_NAME.search(line)
            out.append((m.group(1), line.strip(), test.group(1).strip() if test else ""))
    return out


def junit_outcomes(folder: Path) -> dict[str, str]:
    """`<file stem or class>::<name>` -> passed | failed, from every JUnit file under folder."""
    found: dict[str, str] = {}
    for xml in sorted(folder.rglob("*.xml")) if folder.is_dir() else []:
        try:
            cases = ET.parse(xml).getroot().iter("testcase")
            for case in cases:
                name = case.get("name", "")
                klass = case.get("classname", "")
                bad = case.find("failure") is not None or case.find("error") is not None
                skipped = case.find("skipped") is not None
                word = "failed" if bad else "skipped" if skipped else "passed"
                key = f"{klass}::{name}"
                if found.get(key) != "failed":
                    found[key] = word
        except (OSError, ET.ParseError):
            continue
    return found


def test_result(test: str, outcomes: dict[str, str]) -> str:
    """passed, failed, skipped or missing for a test named like `pkg/tests/test_x.py::test_y`."""
    name = test.split("::")[-1].strip()
    stem = Path(test.split("::")[0].strip()).stem if "::" in test else ""
    hits = [v for k, v in outcomes.items() if "::" in k and k.split("::")[-1] == name
            and (not stem or stem in k.split("::")[0].split("."))]
    if not hits:
        return "missing"
    if "failed" in hits:
        return "failed"
    return "passed" if "passed" in hits else "skipped"


def removed_rows(program: Program) -> list[str]:
    rows = []
    for path in (program.dir / "REMOVED.md", program.dir.parent / "_records" / "REMOVED.md"):
        if path.exists():
            rows += [ln.strip() for ln in path.read_text("utf-8", errors="replace").splitlines()
                     if R_ID.search(ln) and ln.lstrip().startswith(("-", "*"))]
    return rows


def trace(program: Program, stop: str, settings: Settings, base: str | None = None,
          tip: str | None = None) -> tuple[bool, list[str]]:
    state = st.load(program)
    repo = Path(state.repo)
    if tip is None:
        base, tip = stop_range(program, stop)
    base = base or ""
    try:
        git(repo, "fetch", "-q", state.remote, timeout=settings.git_timeout_s)
    except GitError:
        pass  # an unreachable remote: the objects of a landed tip are usually here already
    index = prog.load(program) if program.project_file.exists() else prog.Index()
    ids = slice_ids(program)
    stop_slices = [s for s in state.slices.values() if (s.checkpoint or stop) == stop]
    for fix in fix_programs(program):
        if fix.state.exists():
            stop_slices += [s for s in st.load(fix).slices.values() if (s.checkpoint or stop) == stop]
    mine = {s.id for s in stop_slices}
    fails: list[str] = []
    out = [f"# Map: {program.dir.name} stop {stop}", "", f"From `{base or '(start)'}` to `{tip}`.", ""]

    # per ask
    out += ["## Asks", ""]
    for chain in index.chains:
        if not isinstance(chain, dict):
            continue
        own = [s for s in chain.get("slices") or [] if s in mine]
        if not own:
            continue
        out.append(f"### {chain.get('ask')} ({chain.get('verdict') or 'no verdict'})")
        for key in ("plan", "arch", "interfaces", "edge_cases", "intent", "findings"):
            if chain.get(key):
                out.append(f"- {key}: {', '.join(map(str, chain[key]))}")
        for sid in own:
            sl = next(s for s in stop_slices if s.id == sid)
            found = CHAIN_LINE.search(brief_text(program, sid))
            out.append(f"- slice {sid}: {sl.status}, landed {sl.landed_sha or 'not landed'}; "
                       f"Chain: {found.group(1).strip() if found else '(no Chain line)'}")
        out.append("")
    unchained = sorted(mine - {s for c in index.chains if isinstance(c, dict) for s in c.get("slices") or []})
    if unchained:
        out += [f"Slices no chain row names: {', '.join(unchained)}", ""]

    # commits
    found_commits = commits(repo, base, tip, settings)
    out += ["## Commits", ""]
    by_slice: dict[str, list[str]] = {}
    from ship.project_profile import of_program

    patterns = generator_patterns(of_program(program.dir, settings))
    for sha, parents, subject, files in found_commits:
        sid = owner(subject, ids)
        if sid and len(parents) < 2:
            by_slice.setdefault(sid, []).extend(files)
            out.append(f"- `{sha[:10]}` {subject}")
        elif kit_commit(parents, files, patterns):
            out.append(f"- `{sha[:10]}` {subject} (kit)")
        else:
            line = f"FAIL unchained commit {sha} {subject!r}: its subject names no slice of {program.dir.name}"
            fails.append(line)
            out.append(f"- {line}")
    out.append("")

    # seams
    out += ["## Seams", ""]
    seams = []
    elements: dict[str, set[str]] = {}
    for chain in index.chains:
        if isinstance(chain, dict):
            for el in chain.get("arch") or []:
                elements.setdefault(str(el), set()).update(s for s in chain.get("slices") or [] if s in mine)
    seams += [f"- element {el}: {', '.join(sorted(sl))}" for el, sl in sorted(elements.items()) if len(sl) > 1]
    edge: dict[str, set[str]] = {}
    ledger: list[tuple[str, str, str, str]] = []
    for sid in sorted(mine):
        for eid, line, test in scenarios(brief_text(program, sid)):
            edge.setdefault(eid, set()).add(sid)
            ledger.append((sid, eid, line, test))
    seams += [f"- edge case {e}: {', '.join(sorted(s))}" for e, s in sorted(edge.items()) if len(s) > 1]
    files: dict[str, set[str]] = {}
    for sid, touched in by_slice.items():
        for f in touched:
            files.setdefault(f, set()).add(sid)
    seams += [f"- file {f}: {', '.join(sorted(s))}" for f, s in sorted(files.items()) if len(s) > 1]
    out += (seams or ["- none"]) + [""]

    # scenario ledger
    out += ["## Scenario ledger", ""]
    for sid, eid, line, test in ledger:
        sl = next(s for s in stop_slices if s.id == sid)
        folder = program.checks(sid, sl.head) if sl.head else program.checks_root / sid
        if not test:
            line_out = f"FAIL scenario {eid} of {sid} names no test"
        elif test.lower().startswith("covered by fact"):
            out.append(f"- {eid} ({sid}): {test}")
            continue
        else:
            result = test_result(test, junit_outcomes(folder))
            if result == "passed":
                out.append(f"- {eid} ({sid}): `{test}` passed")
                continue
            line_out = f"FAIL scenario {eid} of {sid}: its test `{test}` is {result} in {folder}"
        fails.append(line_out)
        out.append(f"- {line_out}")
    if not ledger:
        out.append("- no E ids in this stop's briefs")
    out.append("")

    # removed rows and their guards
    out += ["## Removed rows on this stop's files", ""]
    touched_files = set(files)
    rows = [r for r in removed_rows(program) if any(f in r for f in touched_files)
            or any(rid in brief_text(program, sid) for sid in mine for rid in R_ID.findall(r))]
    guards: list[tuple[str, str, object]] = []
    for row in rows:
        out.append(f"- {row}")
        for rid in R_ID.findall(row):
            for sid in sorted(mine):
                text = brief_text(program, sid)
                if rid in text:
                    guards += [(rid, sid, f) for f in parse_facts(text) if GUARD_FACT.match(f.id)]
    if guards:
        copy = checkout_copy(repo, Path(state.worktree_root) / f"stop-{program.dir.name}-{stop}-trace", tip, settings)
        try:
            for rid, sid, fact in guards:
                for result in run_facts([fact], copy, settings):
                    head = result.splitlines()[0]
                    if head.startswith("PASS"):
                        out.append(f"  - guard {rid} {sid} {fact.id}: PASS at {tip[:10]}")
                    else:
                        line = f"FAIL removal guard {rid} {sid} {fact.id} at {tip[:10]}: {result.splitlines()[-1].strip()}"
                        fails.append(line)
                        out.append(f"  - {line}")
        finally:
            drop_copy(repo, copy, settings)
    if not rows:
        out.append("- none")
    out.append("")

    # decisions and chain issues
    out += ["## Builder decisions", ""]
    decisions = []
    for report in sorted(program.evidence_root.glob("*/*/report.md")):
        sid = report.parent.parent.name
        if sid in mine:
            decisions += [f"- {sid}: {m.group(0).strip()}" for m in DECISION.finditer(report.read_text("utf-8"))]
    out += (decisions or ["- none"]) + ["", "## Chain issues", ""]
    issues = program.notes_dir / "CHAIN-ISSUES.md"
    lines = [ln for ln in issues.read_text("utf-8").splitlines() if ln.strip()] if issues.exists() else []
    out += (lines or ["- none"]) + [""]

    out += ["## Trace result", ""] + (fails or ["PASS every commit is chained, every scenario has a passing test"])
    path = program.stop_review(stop) / "MAP.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", "utf-8", newline="\n")
    return not fails, fails + [f"MAP {path}"]
