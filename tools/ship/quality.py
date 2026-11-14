"""The quality ratchet, read from the repo: only a NEW finding blocks (FACTORY-DESIGN 5, "One ratchet").

There is one baseline and it lives in the repo: `ci/baselines/<tool>.txt` (`vulture`, `skylos`, `mutmut`,
`pyright`), the files qmx-ci judges by. A finding is keyed exactly as qmx-ci keys it, `path|rule|message`
with no line number, by the checkout's own `tools/ci/ratchet.py` (loaded from the checkout, standard
library only), so a finding CI accepts is accepted here and one it blocks is blocked here. Keys are
counted: a second copy of a known finding in the same file is new. A checkout without `tools/ci/ratchet.py`,
or without the tool's baseline file, gives `NOTRUN no baseline`. The kit never writes a baseline: CI's
`baseline` level takes them, and `qci ratchet --prune` (run at merge, the profile's `[generators]`)
shrinks them.

- Per slice, inside slice_checks: Vulture and Skylos over each touched package at the head and at the
  parent; only findings in the slice's changed files count, and those already at the parent are known
  too. The baseline is read at the parent, so a slice cannot add its own finding to it. The package's
  `types` command, when it fails, is ratcheted the same way against `pyright.txt` (`types_ratchet`).
- Per checkpoint (`ship quality --from <sha>`): with `ci = "github"` and qmx-ci's `summary.json` for the
  tip (`ci.fetch_summary`), its `quality` rows are the verdict and nothing runs here; otherwise the same
  tools at the build tip against <sha>, plus mutmut on the functions that hold a changed line.

The commands come from checks.toml (`vulture`, `skylos`, `mutmut` per package: one argv, or a list of
argv run in order). `{mutants}` expands to mutmut 3 name globs. A tool without a command is NOTRUN.
"""

from __future__ import annotations

import ast
import collections
import dataclasses
import fnmatch
import hashlib
import json
import re
import sys
import types
from pathlib import Path, PurePosixPath
from typing import Iterable

from ship import state as st
from ship.gitx import changed_files, git, remote_sha
from ship.layout import Program
from ship.settings import Settings
from ship.suite import Package, load_packages, package_of, touched
from ship.worktree import checkout_copy, drop_copy
from ship.wrapper import TIMEOUT_RC, RunResult, run_timed

TOOLS = ("vulture", "skylos", "mutmut")
VULTURE = re.compile(r"^(?P<path>\S.*?\.py):(?P<line>\d+): (?P<what>.+?)(?: \(\d+% confidence[^)]*\))?\s*$")
MUTANT = re.compile(r"^\s*(?P<name>\S+__mutmut_\d+): (?P<status>.+?)\s*$")
MUTANT_FINDINGS = ("survived", "no tests")  # qmx-ci's ci_mutate.SURVIVING
# The finding lists in Skylos's JSON, as qmx-ci reads them (qci.SKYLOS_FINDING_CATEGORIES); other top-level
# lists (`whitelisted`, `suppressed`) are not findings.
SKYLOS_CATEGORIES = frozenset({
    "unused_functions", "unused_imports", "unused_classes", "unused_variables", "unused_parameters",
    "unused_files", "unused_fixtures", "unused_exports", "forgotten", "danger", "reliability", "ai_defects",
    "quality", "secrets", "custom_rules", "circular_dependencies", "dependency_vulnerabilities",
    "publisher_change_findings"})
PYRIGHT_DIAG = re.compile(r"^\s+(?P<path>\S.*?):(?P<line>\d+):(?P<col>\d+) - (?P<sev>error|warning|information): "
                          r"(?P<msg>.*)$")
PYRIGHT_SUMMARY = re.compile(r"^(?P<errors>\d+|No) errors?, (?:\d+|No) warnings?, (?:\d+|No) informations?\s*$",
                             re.M)
PYRIGHT_RULE = re.compile(r"\s+\((report\w+)\)\s*$")
NUMBER = re.compile(r"\d+")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


@dataclasses.dataclass(frozen=True)
class Finding:
    tool: str
    path: str  # the key's path: a repo-relative file, or for mutmut the package folder, as qmx-ci keys it
    line: int  # 0 when the tool gives none; never part of the key
    rule: str
    message: str
    file: str = ""  # the file it sits in, when the key's path is not one (mutmut)
    raw: str = ""  # the tool's own name for it (a mutant's name), never part of the key

    @property
    def where(self) -> str:
        return self.file or self.path

    def __str__(self) -> str:
        at = f"{self.where}:{self.line}" if self.line else self.where
        return f"{at} [{self.rule}] {self.message}"


# ---- the repo's own ratchet ----------------------------------------------------------------------------


class RatchetError(Exception):
    pass


def _load(script: Path) -> types.ModuleType:
    """The checkout's `tools/ci/ratchet.py` as a module, once per distinct file content."""
    code = script.read_bytes()
    name = f"_ship_repo_ratchet_{hashlib.sha1(code).hexdigest()[:16]}"
    module = sys.modules.get(name)
    if module is not None:
        return module
    module = types.ModuleType(name)
    module.__file__ = str(script)
    sys.modules[name] = module  # a dataclass looks its module up while it is being made
    try:
        exec(compile(code, str(script), "exec"), module.__dict__)  # noqa: S102 - the repo's own CI code
    except BaseException as exc:
        del sys.modules[name]
        raise RatchetError(f"{script} does not load: {exc!r}") from exc
    missing = [n for n in ("Finding", "read_baseline", "new_findings") if not hasattr(module, n)]
    if missing:
        del sys.modules[name]
        raise RatchetError(f"{script} has no {missing}")
    return module


@dataclasses.dataclass
class RepoRatchet:
    """`tools/ci/ratchet.py` and `ci/baselines/` of one checkout."""

    module: types.ModuleType
    baselines: Path

    @classmethod
    def at(cls, checkout: Path) -> "RepoRatchet | None":
        """None when the checkout has no ratchet (or it does not load): every tool is then NOTRUN."""
        script = checkout / "tools" / "ci" / "ratchet.py"
        if not script.is_file():
            return None
        try:
            return cls(_load(script), checkout / "ci" / "baselines")
        except (OSError, RatchetError):
            return None

    def baseline(self, tool: str) -> list[str] | None:
        """The tool's baseline keys, or None when the repo has no baseline file for it."""
        path = self.baselines / f"{tool}.txt"
        return list(self.module.read_baseline(path)) if path.is_file() else None

    def _theirs(self, f: Finding):
        return self.module.Finding(f.path, f.line, f.rule, f.message)

    def key(self, f: Finding) -> str:
        return self._theirs(f).key

    def new(self, found: list[Finding], known: Iterable[str]) -> list[Finding]:
        """The findings beyond the known keys' counts, by the repo's own `new_findings`."""
        theirs = [self._theirs(f) for f in found]
        back = {id(t): f for t, f in zip(theirs, found)}
        return [back[id(t)] for t in self.module.new_findings(theirs, list(known))]


# ---- reading the tools ---------------------------------------------------------------------------------


def _repo_path(raw: str, checkout: Path, package: Package) -> str:
    raw = raw.replace("\\", "/")
    absolute = re.match(r"^([A-Za-z]:)?/", raw)
    if absolute:
        base = str(checkout).replace("\\", "/").rstrip("/") + "/"
        if raw.casefold().startswith(base.casefold()):
            return raw[len(base):]
        return raw
    rel = raw.removeprefix("./")
    return rel if package.root == "." else f"{package.root}/{rel}"


def _module_file(checkout: Path, package: Package, module: str) -> str:
    rel = module.replace(".", "/")
    for candidate in (f"{rel}.py", f"src/{rel}.py", f"{rel}/__init__.py", f"src/{rel}/__init__.py"):
        if (checkout / package.root / candidate).is_file():
            return candidate if package.root == "." else f"{package.root}/{candidate}"
    return module


def _json_in(text: str) -> object:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"^[{\[]", text, re.M):
        try:
            return decoder.raw_decode(text, match.start())[0]
        except json.JSONDecodeError:
            continue
    raise ValueError("no JSON report in the output")


def _function_of(mangled: str) -> str:
    """mutmut 3's mangled name back to qmx-ci's: `x_f` is `f`, `xǁCǁm` is `C.m`."""
    if mangled.startswith("xǁ"):
        return ".".join(p for p in mangled[2:].split("ǁ") if p)
    return mangled[2:] if mangled.startswith("x_") else mangled


def parse(tool: str, text: str, checkout: Path, package: Package) -> list[Finding]:
    """The findings in one tool's output, keyed as qmx-ci keys them. Raises ValueError when Skylos printed
    no JSON report."""
    found: list[Finding] = []
    if tool == "vulture":
        for line in text.splitlines():
            hit = VULTURE.match(line)
            if hit:
                found.append(Finding(tool, _repo_path(hit["path"], checkout, package), int(hit["line"]), "vulture",
                                     hit["what"]))
    elif tool == "skylos":
        data = _json_in(text)
        if not isinstance(data, dict):
            raise ValueError("the Skylos report is not an object")
        for category, items in sorted(data.items()):
            if category not in SKYLOS_CATEGORIES or not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                path = str(item.get("file") or item.get("filename") or "")
                if not path:
                    continue
                rule = str(item.get("rule_id") or item.get("rule") or category)
                name = str(item.get("full_name") or item.get("name") or item.get("message") or "")
                line = item.get("line")
                found.append(Finding(tool, _repo_path(path, checkout, package), line if isinstance(line, int) else 0,
                                     f"{category}:{rule}", name))
    elif tool == "mutmut":
        for line in text.splitlines():
            hit = MUTANT.match(line)
            if hit and hit["status"] in MUTANT_FINDINGS:
                module, _, last = hit["name"].rpartition(".")
                function = _function_of(re.sub(r"__mutmut_\d+$", "", last))
                found.append(Finding(tool, package.root, 0, "mutmut", f"{module}.{function} {hit['status']}",
                                     file=_module_file(checkout, package, module), raw=hit["name"]))
    else:
        raise ValueError(f"unknown quality tool {tool}")
    return found


def parse_pyright(text: str, checkout: Path, package: Package) -> tuple[list[Finding], bool]:
    """pyright's errors, keyed as qmx-ci keys them (`path|rule|message`, every number in the message `#`),
    from its `--outputjson` report or its text output; and whether the reading is complete (the text's
    summary line counts as many errors as were read)."""
    if '"generalDiagnostics"' in text:
        try:
            report = _json_in(text[text.index("{"):])
        except ValueError:
            return [], False
        found = []
        for item in (report.get("generalDiagnostics") or []) if isinstance(report, dict) else []:
            if not isinstance(item, dict) or item.get("severity") != "error":
                continue
            start = (item.get("range") or {}).get("start") or {}
            message = NUMBER.sub("#", " ".join(str(item.get("message") or "").split()))
            found.append(Finding("pyright", _repo_path(str(item.get("file") or ""), checkout, package),
                                 int(start.get("line", -1)) + 1, str(item.get("rule") or "pyright"), message))
        return found, True
    rows: list[list] = []  # [path, line, severity, message lines]
    current: list | None = None
    for line in text.splitlines():
        hit = PYRIGHT_DIAG.match(line)
        if hit:
            current = [hit["path"], int(hit["line"]), hit["sev"], [hit["msg"]]]
            rows.append(current)
        elif current is not None and line.startswith("    ") and line.strip():
            current[3].append(line.strip())  # a message pyright printed over more lines
        else:
            current = None  # a file header, a blank line or the summary ends the message
    found = []
    for path, number, severity, parts in rows:
        if severity != "error":
            continue
        message = " ".join(" ".join(parts).split())
        rule = PYRIGHT_RULE.search(message)
        if rule:
            message = message[:rule.start()].rstrip()
        found.append(Finding("pyright", _repo_path(path, checkout, package), number,
                             rule.group(1) if rule else "pyright", NUMBER.sub("#", message)))
    summary = PYRIGHT_SUMMARY.search(text)
    errors = 0 if summary is None or summary["errors"] == "No" else int(summary["errors"])
    return found, summary is not None and errors == len(found)


def new_findings(found: list[Finding], known: Iterable[str], ratchet: RepoRatchet) -> list[Finding]:
    return ratchet.new(found, known)


def _module_name(rel: str) -> str:
    parts = list(PurePosixPath(rel).with_suffix("").parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def mutant_globs(checkout: Path, package: Package, changed: dict[str, set[int]]) -> list[str]:
    """mutmut 3 name globs for every function or method that holds a changed line. mutmut mutates
    whole functions, so this is the finest "changed lines" it can run."""
    globs: list[str] = []
    for path in sorted(changed):
        source = checkout / path
        if not path.endswith(".py") or not source.is_file() or not package.owns(path):
            continue
        module = _module_name(package.rel(path))
        tree = ast.parse(source.read_text("utf-8", errors="replace"))
        lines = changed[path]

        def holds(node: ast.AST) -> bool:
            first = min([node.lineno, *(d.lineno for d in getattr(node, "decorator_list", []))])
            return any(first <= n <= node.end_lineno for n in lines)

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and holds(node):
                globs.append(f"{module}.x_{node.name}__mutmut_*")
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and holds(item):
                        globs.append(f"{module}.xǁ{node.name}ǁ{item.name}__mutmut_*")
    return globs


def changed_lines(repo: Path, base: str, head: str, paths: list[str], timeout: float) -> dict[str, set[int]]:
    """Line numbers at `head` that the diff from `base` adds or changes; a deletion marks the lines around it."""
    out: dict[str, set[int]] = {}
    current = None
    for line in git(repo, "diff", "-U0", "--no-renames", base, head, "--", *paths, timeout=timeout).splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
            continue
        hit = HUNK.match(line)
        if hit and current:
            start, count = int(hit[1]), int(hit[2] if hit[2] is not None else 1)
            out.setdefault(current, set()).update(range(start, start + count) if count else (start, start + 1))
    return out


def _is_source(path: str) -> bool:
    parts = PurePosixPath(path).parts
    name = parts[-1] if parts else ""
    return (path.endswith(".py") and not name.startswith("test_") and not name.endswith("_test.py")
            and name != "conftest.py" and not any(p in ("tests", "test") for p in parts[:-1]))


# ---- running and judging -------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ToolRun:
    ok: bool  # the tool ran and its output parsed
    findings: list[Finding]
    problem: str = ""


def run_tool(tool: str, package: Package, checkout: Path, out: Path, tag: str, settings: Settings,
             program: Program, globs: list[str] | None = None, heartbeat: Path | None = None) -> ToolRun:
    texts = []
    for i, argv in enumerate(package.quality(tool)):
        expanded = [g for arg in argv for g in ((globs or []) if arg == "{mutants}" else [arg])]
        log = out / f"{tool}-{package.label}-{tag}-{i}.log"
        done = run_timed(expanded, checkout / package.root, log, settings.quality_timeout_s, settings,
                         program.runs, heartbeat)
        if done.rc in (TIMEOUT_RC, 127):
            return ToolRun(False, [], f"{tool} did not run (rc={done.rc}), see {log}")
        texts.append(log.read_text("utf-8", errors="replace"))
    try:
        found = parse(tool, "\n".join(texts), checkout, package)
    except ValueError as exc:
        return ToolRun(False, [], f"{tool} output unreadable: {exc}")
    if globs is not None:
        found = [f for f in found if any(fnmatch.fnmatchcase(f.raw, g) for g in globs)]
    return ToolRun(True, found)


def no_baseline(ratchet: RepoRatchet | None, tool: str) -> str | None:
    """Why `tool` cannot be ratcheted here, or None."""
    if ratchet is None:
        return "no baseline: the checkout has no tools/ci/ratchet.py"
    if ratchet.baseline(tool) is None:
        return f"no baseline: the checkout has no ci/baselines/{tool}.txt"
    return None


def known_union(baseline: Iterable[str], at_base: Iterable[str]) -> list[str]:
    """The keys known from either side, each as often as the side that has it most: a finding the baseline
    holds and the base also shows is one finding, not two (so a second copy at the head is still new)."""
    return list((collections.Counter(baseline) | collections.Counter(at_base)).elements())


def _write_new(out: Path, tool: str, package: Package, new: list[Finding], ratchet: RepoRatchet) -> None:
    (out / f"new-{tool}-{package.label}.txt").write_text("".join(f"{ratchet.key(f)}\t{f}\n" for f in new), "utf-8",
                                                          newline="\n")


def check_package(tool: str, package: Package, head: Path, base: Path | None, files: list[str], out: Path,
                  tag: str, settings: Settings, program: Program, ratchet: RepoRatchet | None,
                  heartbeat: Path | None = None, globs: list[str] | None = None) -> tuple[str, str]:
    """(PASS | FAIL | NOTRUN, detail) for one tool on one package. Only findings in `files` count; known
    ones are the repo baseline's (`ratchet`) and, when `base` is given, those already at `base`."""
    if not package.quality(tool):
        return "NOTRUN", "no command in checks.toml"
    why = no_baseline(ratchet, tool)
    if why:
        return "NOTRUN", why
    if globs is not None and not globs:
        return "NOTRUN", "no changed function to mutate"
    scope = set(files)
    at_head = run_tool(tool, package, head, out, f"{tag}-head", settings, program, globs, heartbeat)
    if not at_head.ok:
        return "FAIL", at_head.problem
    found = [f for f in at_head.findings if f.where in scope]
    known = ratchet.baseline(tool) or []
    if base is not None:
        at_base = run_tool(tool, package, base, out, f"{tag}-base", settings, program, globs, heartbeat)
        if not at_base.ok:
            return "FAIL", at_base.problem
        known = known_union(known, [ratchet.key(f) for f in at_base.findings if f.where in scope])
    new = ratchet.new(found, known)
    _write_new(out, tool, package, new, ratchet)
    if new:
        return "FAIL", f"{len(new)} new: " + "; ".join(str(f) for f in new)
    return "PASS", f"no new findings ({len(found)} known)"


def types_ratchet(package: Package, head: Path, base: Path | None, files: list[str], done: RunResult, out: Path,
                  settings: Settings, program: Program, ratchet: RepoRatchet | None,
                  heartbeat: Path | None = None) -> tuple[str, str]:
    """A failed `types` run judged against `ci/baselines/pyright.txt`, as qmx-ci's slice level judges it:
    only an error not in the baseline, in a file the slice changed, blocks; one already at `base` (run only
    when needed) is known too. Fails closed: no baseline, a pyright that did not finish, or output whose
    error count does not add up stays FAIL."""
    if done.rc == 0:
        return "PASS", "rc=0"
    why = no_baseline(ratchet, "pyright")
    if why:
        return "FAIL", f"rc={done.rc} ({why})"
    if done.rc != 1:
        return "FAIL", f"rc={done.rc}: pyright did not finish"
    found, complete = parse_pyright(done.log.read_text("utf-8", errors="replace"), head, package)
    if not complete:
        return "FAIL", f"rc={done.rc}: pyright's errors could not be read from {done.log.name}"
    scope = set(files)
    mine = [f for f in found if f.path in scope]
    known = ratchet.baseline("pyright") or []
    new = ratchet.new(mine, known)
    if new and base is not None and package.types:
        log = out / f"types-{package.label}-base.log"
        at_base = run_timed(list(package.types), base / package.root, log, settings.check_timeout_s, settings,
                            program.runs, heartbeat)
        theirs, ok = parse_pyright(log.read_text("utf-8", errors="replace"), base, package)
        if at_base.rc in (0, 1) and ok:
            new = ratchet.new(mine, known_union(known, [ratchet.key(f) for f in theirs if f.path in scope]))
    _write_new(out, "pyright", package, new, ratchet)
    if new:
        return "FAIL", f"rc={done.rc}: {len(new)} new: " + "; ".join(str(f) for f in new)
    return "PASS", f"rc={done.rc}: {len(found)} errors, none new in the slice's files ({len(mine)} known)"


# ---- the checkpoint ------------------------------------------------------------------------------------


def summary_quality(summary: dict, tools: tuple[str, ...], tip: str) -> list[str]:
    """qmx-ci's verdict on the quality tools, read from its summary.json: a `new` row that `blocks` fails."""
    rows = [q for q in summary.get("quality") or [] if isinstance(q, dict)]
    lines = []
    for tool in tools:
        mine = [q for q in rows if q.get("tool") == tool]
        blocking = [q for q in mine if q.get("kind") == "new" and q.get("blocks", True)]
        notes = sum(1 for q in mine if q.get("kind") == "new" and not q.get("blocks", True))
        gone = sum(1 for q in mine if q.get("kind") == "gone")
        if blocking:
            lines.append(f"FAIL quality-{tool}-ci {tip[:8]} {len(blocking)} new: "
                         + "; ".join(str(q.get("key")) for q in blocking))
        else:
            lines.append(f"PASS quality-{tool}-ci {tip[:8]} no new blocking rows in summary.json "
                         f"({notes} notes, {gone} gone)")
    return lines


def checkpoint_quality(program: Program, settings: Settings, base: str, tools: tuple[str, ...]) -> tuple[bool, list[str]]:
    """The checkpoint's quality step at the build tip, against the commit the checkpoint started from."""
    state = st.load(program)
    repo, t = Path(state.repo), settings.git_timeout_s
    git(repo, "fetch", "-q", state.remote, timeout=t)
    tip = remote_sha(repo, state.remote, state.build_branch, t)
    out = program.quality(tip)
    out.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if settings.ci == "github":
        from ship import ci

        found = ci.fetch_summary(program, settings, tip)
        if found.path is not None:
            lines = summary_quality(json.loads(found.path.read_text("utf-8")), tools, tip)
            (out / "summary.txt").write_text("\n".join(lines) + "\n", "utf-8", newline="\n")
            return not any(ln.startswith("FAIL ") for ln in lines), lines
        lines.append(f"NOTE no qmx-ci summary.json for {tip[:8]} ({found.why}); the tools run here")
    files = changed_files(repo, base, tip, t)
    tip_copy = checkout_copy(repo, program.tmp / "quality-tip", tip, settings)
    base_copy = checkout_copy(repo, program.tmp / "quality-base", base, settings)
    ratchet = RepoRatchet.at(base_copy)
    try:
        for package in touched(load_packages(program), files):
            mine = [f for f in files if package_of(load_packages(program), f) == package]
            for tool in tools:
                if tool == "mutmut":
                    sources = [f for f in mine if _is_source(f)]
                    globs = mutant_globs(tip_copy, package, changed_lines(repo, base, tip, sources, t)) if sources else []
                    verdict, detail = check_package(tool, package, tip_copy, None, sources, out, "tip", settings,
                                                    program, ratchet, globs=globs)
                else:
                    verdict, detail = check_package(tool, package, tip_copy, base_copy, mine, out, "tip", settings,
                                                    program, ratchet)
                lines.append(f"{verdict} quality-{tool}-{package.label} {tip[:8]} {detail}")
    finally:
        drop_copy(repo, tip_copy, settings)
        drop_copy(repo, base_copy, settings)
    (out / "summary.txt").write_text("\n".join(lines) + "\n", "utf-8", newline="\n")
    return not any(ln.startswith("FAIL ") for ln in lines), lines


BASELINE_MOVED = ("REFUSED the kit takes no baseline: the repo's ci/baselines/ is the one ratchet. Run the "
                  "`baseline` level in CI (push a `baseline/<name>` branch); `qci ratchet --prune` shrinks it at merge.")
