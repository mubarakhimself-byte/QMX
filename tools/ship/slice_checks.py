"""slice_checks: every check a ready slice must pass at its head, on this machine.

Writes checks/<id>/<head8>/: one log per check, each ending in its PASS, FAIL or NOTRUN line, and
summary.txt with the same lines. One FAIL anywhere moves the slice to `red`; otherwise `checked`.

Checks: `git diff --check`, case-only path collisions, then per touched package its setup, lint,
types and tests at the head; the parent rule of the slice's kind (below); Vulture, failing
only on a finding in the slice's files that the repo's `ci/baselines/vulture.txt` (read at the parent) does
not hold, as qmx-ci's slice level judges it; Skylos the same, by CI's own blocking rule (a finding CI keeps
as a note is a NOTE here), with what the parent already shows known too (CI scans a slice with
`--diff-base`). A failed `types` run is ratcheted against `ci/baselines/pyright.txt` alone (no parent run,
as CI). Last, the brief's SAFETY fact at the head. A touched package's reds run once more, as in qmx-ci,
and the test check fails only on what CI blocks (suite.Baseline.judge): a red known-reds.txt does not
name, or a flaky red (it passed on the rerun, in a module the slice did not touch) flaky.txt does not name;
both lists are read at the parent, so a slice cannot excuse its own red.

U29, the parent rule by the slice's kind (SLICES.md `kind`, default feature), `parent_rule(kind, ...)`:
- `feature` (`fail-at-parent-<package>`): each new test case fails at the parent on an assertion (an import,
  collection or other error does not count) and passes at the head.
- `pin` (`pin-<package>`): each new test passes at the parent and at the head (a pin describes today's
  behaviour), then the probe (`probe.py`: its subjects swapped for None and for a sentinel, D-L18) shows each
  one can fail; the probe's rows are `probe-<package>.tsv` beside the logs. A pin slice that adds no test is red.
- `refactor` (`pins`, `deleted-tests`): no new test is needed; every test file the pin slices it depends on
  (directly or not) changed is run at the head and must pass; no test file may be deleted.
- `remove` (`callers`, `deleted-tests`, `replaced-by`): the brief's CALLERS fact holds at the head; a deleted
  test file has a module it imported deleted in the same slice, or a `probe <path> cannot-fail` line in the
  slice's `evidence/<id>/<attempt>/report.md`; the brief's `Replaced by:` is not empty.
- `docs` (`docs-only`): only `docs/**`, `contracts/CHANGELOG.md` and `*.md` change.
A slice that deletes a package root: the packages that remain are checked; the deleted one's commands are
`NOTRUN ... removed-package`, and `removed-package-<package>` fails while `checks.toml`, `tools/test_all.py` or
`tools/ci.py` at the head still names the root.

With `ci = "github"`, the Linux line is qmx-ci's slice run on the pushed head: PASS, FAIL (red), or
PENDING while it queues or runs; land reads it again before landing (ci.linux_gate). For a `pin` or
`refactor` slice CI's slice-level `fail-at-parent` job, which knows no kinds yet, is never a block when it is
the only red job: it is a `NOTE ci-fail-at-parent` line, and the kit's own parent rule judges the slice
(D-L27). Every other CI job still counts.
"""

from __future__ import annotations

import ast
import dataclasses
import re
import shutil
import sys
from collections import Counter
from pathlib import Path, PurePosixPath

from ship import ci
from ship import state as st
from ship.dispatch import run_facts
from ship.gitx import GitError, changed_files, git, git_rc
from ship.layout import Program
from ship.plan import PlanError, matches, read_brief_facts
from ship.quality import RepoRatchet, check_package, types_ratchet
from ship.settings import Settings
from ship.state import Status
from ship.suite import (Outcome, Package, TestRun, baseline_for, load_packages, package_of, rerun_reds, run_tests,
                        touched)
from ship.wrapper import run_timed
from ship.worktree import checkout_copy

CHECKABLE = frozenset({Status.READY, Status.CHECKED, Status.RED})


def is_test_module(path: str) -> bool:
    name = PurePosixPath(path).name
    return name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def is_test_support(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return path.endswith(".py") and (is_test_module(path) or parts[-1] == "conftest.py"
                                     or any(p in ("tests", "test") for p in parts[:-1]))


class Recorder:
    def __init__(self, out: Path, slice_id: str, head: str):
        self.out, self.slice_id, self.head8 = out, slice_id, head[:8]
        self.lines: list[str] = []

    def record(self, verdict: str, check: str, detail: str = "", log: Path | None = None) -> None:
        line = f"{verdict} {check} {self.slice_id} {self.head8}" + (f" {detail}" if detail else "")
        self.lines.append(line)
        target = log or self.out / f"{check}.log"
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line + "\n")

    @property
    def red(self) -> bool:
        return any(ln.startswith("FAIL ") for ln in self.lines)


@dataclasses.dataclass
class Ctx:
    """What every parent rule reads: the slice, its two commits and their frozen copies."""

    rec: Recorder
    program: Program
    state: st.State
    sl: st.Slice
    repo: Path
    head: str
    parent: str
    head_copy: Path
    parent_copy: Path
    settings: Settings
    beat: Path
    files: list[str]  # changed between parent and head
    deleted: list[str]  # deleted between parent and head
    support: list[str]  # changed test support files (test modules, conftest, files under tests/)
    packages: list[Package]


@dataclasses.dataclass
class NewTests:
    name: str
    log: Path
    modules: list[str]  # the changed test modules, relative to the package root
    new: list[str]  # test ids at the head the parent did not have
    parent: TestRun
    head: TestRun


def new_tests(ctx: Ctx, name: str, package: Package, modules: list[str]) -> NewTests | None:
    """The new test cases of `modules`, run at the parent (the slice's test support copied in) and at the head.
    None when there is nothing to judge; its FAIL or NOTRUN line is recorded then."""
    rec, settings, t = ctx.rec, ctx.settings, ctx.settings.git_timeout_s
    log = rec.out / f"{name}.log"
    rel = [package.rel(m) for m in modules]
    at_parent = [package.rel(m) for m in modules
                 if git_rc(ctx.repo, "cat-file", "-e", f"{ctx.parent}:{m}", timeout=t) == 0]
    before = run_tests(ctx.parent_copy, package, at_parent, rec.out / f"{name}-parent-own.log",
                       settings.check_timeout_s, settings, ctx.program.runs, ctx.beat).outcomes if at_parent else {}
    for path in ctx.support:
        target = ctx.parent_copy / path
        if git_rc(ctx.repo, "cat-file", "-e", f"{ctx.head}:{path}", timeout=t) == 0:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git(ctx.repo, "show", f"{ctx.head}:{path}", timeout=t).encode("utf-8"))
        else:
            target.unlink(missing_ok=True)
    parent_run = run_tests(ctx.parent_copy, package, rel, rec.out / f"{name}-parent.log", settings.check_timeout_s,
                           settings, ctx.program.runs, ctx.beat)
    head_run = run_tests(ctx.head_copy, package, rel, rec.out / f"{name}-head.log", settings.check_timeout_s,
                         settings, ctx.program.runs, ctx.beat)
    if not head_run.junit_ok or not parent_run.junit_ok:
        rec.record("FAIL", name, "no JUnit report from the test command", log)
        return None
    new = sorted(k for k in head_run.outcomes if k not in before and "::::" not in k)
    if not new:
        rec.record("NOTRUN", name, "no new test cases in the changed test files", log)
        return None
    return NewTests(name, log, rel, new, parent_run, head_run)


def fail_at_parent(ctx: Ctx, package: Package, modules: list[str]) -> None:
    """kind feature: each new test fails at the parent on an assertion and passes at the head."""
    got = new_tests(ctx, f"fail-at-parent-{package.label}", package, modules)
    if got is None:
        return
    bad = []
    with open(got.log, "a", encoding="utf-8", newline="\n") as fh:
        for test_id in got.new:
            at_p = got.parent.outcomes.get(test_id)
            at_h = got.head.outcomes[test_id]
            fh.write(f"{test_id} parent={at_p or 'not collected'} head={at_h}\n")
            if at_p != Outcome.ASSERTION:
                bad.append(f"{test_id} at parent: {at_p or 'not collected (import or collection error)'}")
            if at_h != Outcome.PASSED:
                bad.append(f"{test_id} at head: {at_h}")
    if bad:
        ctx.rec.record("FAIL", got.name, f"{len(bad)} of {len(got.new)} new tests: " + "; ".join(bad), got.log)
    else:
        ctx.rec.record("PASS", got.name,
                       f"{len(got.new)} new tests fail at the parent on an assertion and pass at the head", got.log)


def node_id(test_id: str, modules: list[str]) -> str | None:
    """A JUnit test id (`<root>::<classname>::<name>`) as a pytest node id relative to the package root, found
    among the changed test modules (relative to the package root); None when none of them holds it."""
    parts = test_id.split("::")
    if len(parts) < 3:
        return None
    classname, name = parts[-2], parts[-1].split("[")[0]

    def same(dotted: str, module: str) -> bool:
        return dotted == module or dotted.endswith("." + module)

    for rel in modules:
        dotted = rel.removesuffix(".py").replace("/", ".")
        if same(dotted, classname):
            return f"{rel}::{name}"
        if "." in classname:
            module, klass = classname.rsplit(".", 1)
            if same(dotted, module):
                return f"{rel}::{klass}::{name}"
    return None


def pin_rule(ctx: Ctx, package: Package, modules: list[str]) -> int:
    """kind pin: each new test passes at the parent and at the head, and the probe shows it can fail. Returns
    how many new tests it judged."""
    from ship.probe import probe

    got = new_tests(ctx, f"pin-{package.label}", package, modules)
    if got is None:
        return 0
    bad = []
    with open(got.log, "a", encoding="utf-8", newline="\n") as fh:
        for test_id in got.new:
            at_p = got.parent.outcomes.get(test_id)
            at_h = got.head.outcomes[test_id]
            fh.write(f"{test_id} parent={at_p or 'not collected'} head={at_h}\n")
            if at_p != Outcome.PASSED:
                bad.append(f"{test_id} at parent: {at_p or 'not collected'} (a pin must describe today's behaviour)")
            if at_h != Outcome.PASSED:
                bad.append(f"{test_id} at head: {at_h}")
    if bad:
        ctx.rec.record("FAIL", got.name, f"{len(bad)} of {len(got.new)} new tests: " + "; ".join(bad), got.log)
        return len(got.new)
    ids = {t: node_id(t, got.modules) for t in got.new}
    bad = [f"{t}: not found in the changed test files" for t, n in ids.items() if n is None]
    nodes = sorted({n for n in ids.values() if n})
    tsv = ctx.rec.out / f"probe-{package.label}.tsv"
    rows = probe(ctx.head_copy, package, nodes, tsv, ctx.settings, ctx.program.runs, ctx.beat) if nodes else []
    with open(got.log, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"probe: {tsv}\n" + "".join(r.line() + "\n" for r in rows))
    bad += [f"{r.test_id} is {r.verdict} under the probe (none={r.none} sentinel={r.sentinel})"
            for r in rows if r.verdict != "can-fail"]
    if bad:
        ctx.rec.record("FAIL", got.name, f"{len(bad)} of {len(got.new)} new tests: " + "; ".join(bad), got.log)
    else:
        ctx.rec.record("PASS", got.name, f"{len(got.new)} new tests pass at the parent and the head, and each fails "
                                         f"when its subject returns None or a sentinel (probe {tsv.name})", got.log)
    return len(got.new)


def pin_dependencies(state: st.State, sl: st.Slice) -> list[st.Slice]:
    """The pin slices `sl` depends on, directly or through other slices."""
    seen: dict[str, st.Slice] = {}
    todo = list(sl.depends_on)
    while todo:
        sid = todo.pop()
        dep = state.slices.get(sid)
        if dep is None or sid in seen:
            continue
        seen[sid] = dep
        todo += dep.depends_on
    return [d for _, d in sorted(seen.items()) if d.kind == "pin"]


def pin_test_files(repo: Path, pins: list[st.Slice], timeout: float) -> tuple[set[str], list[str]]:
    """(the test modules the pin slices changed, problems reading them)."""
    files: set[str] = set()
    problems = []
    for pin in pins:
        if not (pin.parent and pin.head):
            problems.append(f"pin {pin.id} has no recorded head ({pin.status})")
            continue
        try:
            files |= {f for f in changed_files(repo, pin.parent, pin.head, timeout) if is_test_module(f)}
        except GitError as exc:
            problems.append(f"pin {pin.id}: {exc}")
    return files, problems


def refactor_rule(ctx: Ctx) -> None:
    """kind refactor: the test files of the pins it depends on pass at the head; no test file is deleted."""
    gone = [f for f in ctx.deleted if is_test_module(f)]
    ctx.rec.record("FAIL" if gone else "PASS", "deleted-tests",
                   f"a refactor deletes no test file: {', '.join(gone)}" if gone else "no test file deleted")
    pins = pin_dependencies(ctx.state, ctx.sl)
    log = ctx.rec.out / "pins.log"
    if not pins:
        ctx.rec.record("NOTRUN", "pins", "no pin slice among its dependencies", log)
        return
    t = ctx.settings.git_timeout_s
    files, problems = pin_test_files(ctx.repo, pins, t)
    missing = sorted(f for f in files if git_rc(ctx.repo, "cat-file", "-e", f"{ctx.head}:{f}", timeout=t) != 0)
    problems += [f"{f} is gone at the head" for f in missing]
    present = sorted(files - set(missing))
    ran = 0
    for package in touched(ctx.packages, present):
        mine = [package.rel(f) for f in present if package_of(ctx.packages, f) == package]
        run = run_tests(ctx.head_copy, package, mine, ctx.rec.out / f"pins-{package.label}.log",
                        ctx.settings.check_timeout_s, ctx.settings, ctx.program.runs, ctx.beat)
        if not run.junit_ok:
            problems.append(f"{package.label}: no JUnit report")
            continue
        ran += len(run.outcomes)
        problems += [f"{k} is {v}" for k, v in sorted(run.outcomes.items()) if v != Outcome.PASSED]
    with open(log, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"pins: {', '.join(p.id for p in pins)}\nfiles: {', '.join(sorted(files))}\n"
                 + "".join(f"{x}\n" for x in problems))
    if problems or not ran:
        ctx.rec.record("FAIL", "pins", "the pins it depends on do not all pass at the head: "
                       + ("; ".join(problems) or "no pin test ran"), log)
    else:
        ctx.rec.record("PASS", "pins", f"{ran} tests of pins {', '.join(p.id for p in pins)} pass at the head", log)


REPLACED_BY = re.compile(r"^[ \t]*(?:[-*][ \t]*)?(?:\*\*)?Replaced by:?(?:\*\*)?:?[ \t]*(.*)$", re.M | re.I)
PROBE_LINE = re.compile(r"^[ \t]*(?:[-*][ \t]*)?`?probe`?\b.*$", re.M)


def replaced_by(text: str) -> str:
    """The brief's `Replaced by:` value, "" when it has none."""
    found = REPLACED_BY.search(text)
    return found.group(1).strip() if found else ""


def imported_modules(source: str) -> set[str]:
    """Every dotted module name a file imports (for `from a import b`, both `a` and `a.b`)."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
            names |= {f"{node.module}.{a.name}" for a in node.names if a.name != "*"}
    return names


def subject_deleted(ctx: Ctx, test_file: str) -> str | None:
    """A module the deleted test file imported (read at the parent) that the slice deletes too, or None."""
    try:
        imported = imported_modules(git(ctx.repo, "show", f"{ctx.parent}:{test_file}",
                                        timeout=ctx.settings.git_timeout_s))
    except (GitError, SyntaxError, ValueError):
        return None
    gone = [f for f in ctx.deleted if not is_test_support(f)]
    for name in sorted(imported):
        path = name.replace(".", "/")
        for suffix in (f"{path}.py", f"{path}/__init__.py"):
            for f in gone:
                if f == suffix or f.endswith("/" + suffix):
                    return f
    return None


def probe_lines(program: Program, slice_id: str) -> list[str]:
    """Every `probe` line of the slice's evidence reports."""
    lines = []
    for report in sorted((program.evidence_root / slice_id).glob("*/report.md")):
        lines += [m.group(0) for m in PROBE_LINE.finditer(report.read_text("utf-8", errors="replace"))]
    return lines


def remove_rule(ctx: Ctx) -> None:
    """kind remove: the CALLERS fact at the head, deleted tests accounted for, `Replaced by:` filled."""
    rec = ctx.rec
    brief = ctx.program.brief(ctx.sl.id)
    try:
        text = brief.read_text("utf-8")
        facts = [f for f in read_brief_facts(brief) if f.id.upper().startswith("CALLERS")]
    except (OSError, PlanError) as exc:
        rec.record("FAIL", "callers", f"brief unreadable: {exc}")
        rec.record("FAIL", "replaced-by", f"brief unreadable: {exc}")
    else:
        log = rec.out / "callers.log"
        if not facts:
            rec.record("FAIL", "callers", "a remove slice's brief has no CALLERS fact", log)
        else:
            lines = run_facts(facts, ctx.head_copy, ctx.settings)
            log.write_text("\n".join(lines) + "\n", "utf-8", newline="\n")
            failed = [ln.split()[2] for ln in lines if ln.startswith("FAIL")]
            if failed:
                rec.record("FAIL", "callers", f"{', '.join(failed)} differs at the head: something still names what "
                                              "the slice removes, see callers.log", log)
            else:
                rec.record("PASS", "callers", f"{len(facts)} CALLERS facts hold at the head", log)
        value = replaced_by(text)
        rec.record("PASS" if value else "FAIL", "replaced-by",
                   f"Replaced by: {value}" if value else "the brief's `Replaced by:` is missing or empty")
    probes = probe_lines(ctx.program, ctx.sl.id)
    bad, ok = [], []
    for f in (x for x in ctx.deleted if is_test_module(x)):
        subject = subject_deleted(ctx, f)
        if subject:
            ok.append(f"{f} (its subject {subject} is deleted too)")
        elif any(f in line and "cannot-fail" in line for line in probes):
            ok.append(f"{f} (probe: cannot-fail)")
        else:
            bad.append(f)
    if bad:
        rec.record("FAIL", "deleted-tests", "deleted with no deleted subject and no `probe <path> cannot-fail` line "
                                            f"in report.md: {', '.join(bad)}")
    else:
        rec.record("PASS", "deleted-tests", "; ".join(ok) if ok else "no test file deleted")


DOCS_PATTERNS = ("docs/**", "contracts/CHANGELOG.md", "**/*.md")


def docs_rule(ctx: Ctx) -> None:
    """kind docs: only documentation changes."""
    other = [f for f in ctx.files if not any(matches(p, f) for p in DOCS_PATTERNS)]
    ctx.rec.record("FAIL" if other else "PASS", "docs-only",
                   f"a docs slice changes {', '.join(other)}" if other
                   else f"{len(ctx.files)} files, all under docs/, contracts/CHANGELOG.md or *.md")


def parent_rule(kind: str, ctx: Ctx, package: Package | None = None, modules: list[str] | None = None) -> int:
    """U29: the slice's parent rule by its kind. Per package (`package` given) for feature and pin, which judge
    the new tests of `modules`; once per slice (no package) for refactor, remove and docs. Returns how many new
    tests a pin judged."""
    if package is not None:
        if kind == "feature":
            fail_at_parent(ctx, package, modules or [])
        elif kind == "pin":
            return pin_rule(ctx, package, modules or [])
        return 0
    if kind == "refactor":
        refactor_rule(ctx)
    elif kind == "remove":
        remove_rule(ctx)
    elif kind == "docs":
        docs_rule(ctx)
    return 0


REMOVED_ROOT_NAMERS = ("checks.toml", "tools/test_all.py", "tools/ci.py")


def removed_root(ctx: Ctx, package: Package) -> bool:
    """The slice deletes this package's root folder."""
    t = ctx.settings.git_timeout_s
    return (package.root != "." and git_rc(ctx.repo, "cat-file", "-e", f"{ctx.head}:{package.root}", timeout=t) != 0
            and git_rc(ctx.repo, "cat-file", "-e", f"{ctx.parent}:{package.root}", timeout=t) == 0)


def removed_package(ctx: Ctx, package: Package) -> None:
    """A package root the slice deletes: its commands are skipped; nothing that runs CI or tests may name it."""
    for check in ("lint", "types", "test", "quality-vulture", "quality-skylos"):
        ctx.rec.record("NOTRUN", f"{check}-{package.label}", "removed-package")
    t = ctx.settings.git_timeout_s
    naming = [path for path in REMOVED_ROOT_NAMERS
              if git_rc(ctx.repo, "cat-file", "-e", f"{ctx.head}:{path}", timeout=t) == 0
              and package.root in git(ctx.repo, "show", f"{ctx.head}:{path}", timeout=t)]
    name = f"removed-package-{package.label}"
    if naming:
        ctx.rec.record("FAIL", name, f"{', '.join(naming)} still names the removed root {package.root} at the head")
    else:
        ctx.rec.record("PASS", name, f"{package.root} is removed and no {', '.join(REMOVED_ROOT_NAMERS)} at the head "
                                     "names it")


def safety_at_head(program: Program, slice_id: str, head_copy: Path, out: Path,
                   settings: Settings) -> tuple[str, str, str]:
    """The brief's SAFETY fact, rerun at the head: the fixed line the slice depends on still holds."""
    try:
        facts = [f for f in read_brief_facts(program.brief(slice_id)) if f.id == "SAFETY"]
    except PlanError as exc:
        return "FAIL", "safety", f"brief unreadable: {exc}"
    if not facts:
        return "NOTRUN", "safety", "the brief has no SAFETY fact"
    (line,) = run_facts(facts, head_copy, settings)
    (out / "safety.log").write_text(line + "\n", "utf-8", newline="\n")
    if line.startswith("PASS"):
        return "PASS", "safety", "the SAFETY fact gives the brief's output at the head"
    return "FAIL", "safety", "the SAFETY fact differs at the head, see safety.log"


def slice_checks(program: Program, slice_id: str, settings: Settings) -> tuple[bool, list[str]]:
    state = st.load(program)
    sl = state.slices[slice_id]
    if sl.status not in CHECKABLE or not sl.head or not sl.parent:
        return False, [f"{slice_id} is {sl.status}; checks run on a ready slice"]
    repo, head, parent = Path(state.repo), sl.head, sl.parent
    out = program.checks(slice_id, head)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    rec = Recorder(out, slice_id, head)
    beat = program.heartbeat(slice_id)
    t = settings.git_timeout_s
    git(repo, "fetch", "-q", state.remote, timeout=t)

    whitespace = git(repo, "diff", "--check", parent, head, timeout=t, check=False)
    (out / "diff-check.log").write_text(whitespace, "utf-8", newline="\n")
    rec.record("FAIL" if whitespace.strip() else "PASS", "diff-check")

    names = git(repo, "ls-tree", "-r", "--name-only", head, timeout=t).splitlines()
    clashes = sorted(n for n, c in Counter(x.casefold() for x in names).items() if c > 1)
    rec.record("FAIL" if clashes else "PASS", "case-collision", ", ".join(clashes))

    files = changed_files(repo, parent, head, t)
    deleted = [x for x in git(repo, "diff", "--no-renames", "--name-only", "--diff-filter=D", parent, head,
                              timeout=t).splitlines() if x.strip()]
    packages = load_packages(program)
    head_copy = checkout_copy(repo, program.tmp / f"check-{slice_id}-head", head, settings)
    parent_copy = checkout_copy(repo, program.tmp / f"check-{slice_id}-parent", parent, settings)
    support = [f for f in files if is_test_support(f)]
    ctx = Ctx(rec, program, state, sl, repo, head, parent, head_copy, parent_copy, settings, beat, files, deleted,
              support, packages)
    pinned = 0
    baseline = baseline_for(repo, parent, t)  # D-L25: at the parent, so a slice cannot excuse its own red
    ratchet = RepoRatchet.at(parent_copy)  # the parent's baseline: a slice cannot excuse its own finding
    for package in touched(packages, files):
        if removed_root(ctx, package):
            removed_package(ctx, package)
            continue
        for copy in (head_copy, parent_copy):
            if package.setup:
                where = "head" if copy == head_copy else "parent"
                done = run_timed(list(package.setup), copy / package.root, out / f"setup-{package.label}-{where}.log",
                                 settings.check_timeout_s, settings, program.runs, beat)
                rec.record("PASS" if done.rc == 0 else "FAIL", f"setup-{package.label}-{where}",
                           f"rc={done.rc}", done.log)
        mine = [f for f in files if package_of(packages, f) == package]
        for kind in ("lint", "types"):
            argv = getattr(package, kind)
            name = f"{kind}-{package.label}"
            if not argv:
                rec.record("NOTRUN", name, "no command in checks.toml")
                continue
            done = run_timed(list(argv), head_copy / package.root, out / f"{name}.log", settings.check_timeout_s,
                             settings, program.runs, beat)
            if kind == "types" and done.rc != 0:
                verdict, detail = types_ratchet(package, head_copy, mine, done, ratchet, out)
                rec.record(verdict, name, detail, done.log)
                continue
            rec.record("PASS" if done.rc == 0 else "FAIL", name, f"rc={done.rc}", done.log)
        name = f"test-{package.label}"
        run = run_tests(head_copy, package, [], out / f"{name}.log", settings.check_timeout_s, settings,
                        program.runs, beat)
        run = rerun_reds(head_copy, package, run, out / f"{name}.log", settings.check_timeout_s, settings,
                         program.runs, beat)
        judged = baseline.judge([run], files)
        detail = (f"rc={run.run.rc} red={len(run.red())}" + (f" known={len(judged.known)}" if judged.known else "")
                  + (f" flaky={len(judged.flaky)}" if judged.flaky else "")
                  + (f" blocking: {', '.join(judged.blocking)}" if judged.blocking else "")
                  + ("" if run.junit_ok else " no JUnit report"))
        green = run.junit_ok and not judged.blocking and (run.run.rc == 0 or bool(run.red()))
        rec.record("PASS" if green else "FAIL", name, detail, run.run.log)
        modules = [f for f in files if is_test_module(f) and package_of(packages, f) == package
                   and git_rc(repo, "cat-file", "-e", f"{head}:{f}", timeout=t) == 0]
        if modules:
            pinned += parent_rule(sl.kind, ctx, package, modules)
        for tool in ("vulture", "skylos"):
            # D-L25: Vulture is judged against the baseline alone, as CI's slice level; Skylos also knows what
            # the parent shows, standing in for CI's `--diff-base` scan of the slice
            verdict, detail = check_package(tool, package, head_copy, parent_copy if tool == "skylos" else None, mine,
                                            out, "slice", settings, program, ratchet, beat)
            rec.record(verdict, f"quality-{tool}-{package.label}", detail)
    if sl.kind == "pin" and not pinned:
        rec.record("FAIL", "pin", "a pin slice adds no new test case")
    parent_rule(sl.kind, ctx)
    rec.record(*safety_at_head(program, slice_id, head_copy, out, settings))
    other = "linux" if sys.platform == "win32" else "windows"
    linux = None
    if settings.ci == "github":
        sha = sl.ci.get("sha") if sl.ci.get("rebased") == head else head
        linux = ci.slice_linux(state, settings, dataclasses.replace(sl, ci={"sha": sha}))
        rec.record(linux[0], "linux", " ".join(x for x in linux[1:] if x))
        if ci.FAIL_AT_PARENT_NOTE in linux[1]:  # D-L27: recorded, never a block
            rec.record("NOTE", "ci-fail-at-parent", f"CI's fail-at-parent job is red on this {sl.kind} slice; the "
                                                    "kit's parent rule judges it (D-L27)")
    if other == "windows" or linux is None:
        rec.record("NOTRUN", other, f"this machine is {sys.platform}; {other} checks run in CI later")
    rec.record("NOTRUN", "mutation", "mutmut runs on the changed functions at the checkpoint (ship quality)")
    (out / "summary.txt").write_text("\n".join(rec.lines) + "\n", "utf-8", newline="\n")

    with st.locked(program) as fresh:
        now = fresh.slices[slice_id]
        if now.head == head and linux is not None:
            sha = now.ci.get("sha") if now.ci.get("rebased") == head else head
            now.ci = {**now.ci, "sha": sha, "linux": linux[0].lower(), "url": linux[2]}
        if now.head == head and now.status in CHECKABLE:
            fails = [ln for ln in rec.lines if ln.startswith("FAIL ")]
            if fails:
                fresh.move(slice_id, Status.RED, f"slice_checks: {len(fails)} FAIL at {head[:8]}")
            else:
                fresh.move(slice_id, Status.CHECKED, f"slice_checks green at {head[:8]}")
    return not rec.red, rec.lines
