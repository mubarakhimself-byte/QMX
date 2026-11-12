"""The quality ratchet: Skylos, Vulture and mutmut, where only a NEW finding blocks.

A finding is keyed by tool, file and the tool's words, never its line, so it survives code moving.
Known findings never block: those in the baseline files (`ship baseline`, taken once and refreshed
on a schedule) and, for Vulture and Skylos, those already at the commit the work started from.
Every baseline finding is a row in BACKLOG.md for a later fixer.

- Per slice, inside slice_checks: Vulture and Skylos over each touched package, at the head and at
  the parent, keeping findings in the slice's changed files.
- Per checkpoint (`ship quality --from <sha>`): the same at the build tip against <sha>, plus mutmut
  on the functions that hold a changed line.
- `ship baseline [--part K/N]`: every finding of the named tools over every package. mutmut is slow,
  so it can run in parts on a schedule; each part replaces only its own modules' rows.

The commands come from checks.toml (`vulture`, `skylos`, `mutmut` per package: one argv, or a list of
argv run in order). `{mutants}` expands to mutmut 3 name globs. A tool without a command is NOTRUN.
"""

from __future__ import annotations

import ast
import collections
import dataclasses
import datetime as dt
import fnmatch
import json
import re
from pathlib import Path, PurePosixPath
from typing import Iterable

from ship import state as st
from ship.gitx import changed_files, git, remote_sha
from ship.layout import Program
from ship.settings import Settings
from ship.suite import Package, load_packages, package_of, touched
from ship.worktree import checkout_copy, drop_copy
from ship.wrapper import TIMEOUT_RC, run_timed

TOOLS = ("vulture", "skylos", "mutmut")
VULTURE = re.compile(r"^(?P<path>\S.*?\.py):(?P<line>\d+): (?P<what>.+?)(?: \(\d+% confidence[^)]*\))?\s*$")
MUTANT = re.compile(r"^\s*(?P<name>\S+__mutmut_\d+): (?P<status>.+?)\s*$")
MUTANT_FINDINGS = ("survived", "no tests")
FILE_KEYS, LINE_KEYS = ("file", "filename", "path"), ("line", "lineno", "line_number")
RULE_KEYS, NAME_KEYS = ("rule_id", "rule"), ("full_name", "name", "symbol", "simple_name", "message")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


@dataclasses.dataclass(frozen=True)
class Finding:
    tool: str
    path: str  # repo-relative, forward slashes
    line: int  # 0 when the tool gives none
    what: str  # the tool's words, without anything that moves with the line

    @property
    def key(self) -> str:
        return f"{self.tool}\t{self.path}\t{self.what}"

    def __str__(self) -> str:
        return f"{self.path}:{self.line} {self.what}" if self.line else f"{self.path} {self.what}"


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


def _skylos_items(node: object, where: str) -> Iterable[tuple[str, dict]]:
    if isinstance(node, dict):
        if any(isinstance(node.get(k), str) for k in FILE_KEYS) and any(k in node for k in LINE_KEYS):
            yield where, node
            return
        for key, value in node.items():
            yield from _skylos_items(value, f"{where}.{key}" if where else key)
    elif isinstance(node, list):
        for item in node:
            yield from _skylos_items(item, where)


def _json_in(text: str) -> object:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"^[{\[]", text, re.M):
        try:
            return decoder.raw_decode(text, match.start())[0]
        except json.JSONDecodeError:
            continue
    raise ValueError("no JSON report in the output")


def parse(tool: str, text: str, checkout: Path, package: Package) -> list[Finding]:
    """The findings in one tool's output. Raises ValueError when Skylos printed no JSON report."""
    found: list[Finding] = []
    if tool == "vulture":
        for line in text.splitlines():
            hit = VULTURE.match(line)
            if hit:
                found.append(Finding(tool, _repo_path(hit["path"], checkout, package), int(hit["line"]), hit["what"]))
    elif tool == "skylos":
        for category, item in _skylos_items(_json_in(text), ""):
            path = next(item[k] for k in FILE_KEYS if isinstance(item.get(k), str))
            line = next((item[k] for k in LINE_KEYS if isinstance(item.get(k), int)), 0)
            rule = next((str(item[k]) for k in RULE_KEYS if item.get(k)), "")
            name = next((str(item[k]) for k in NAME_KEYS if item.get(k)), "")
            what = " ".join(part for part in (category, rule, name) if part)
            found.append(Finding(tool, _repo_path(path, checkout, package), line, what))
    elif tool == "mutmut":
        for line in text.splitlines():
            hit = MUTANT.match(line)
            if hit and hit["status"] in MUTANT_FINDINGS:
                module = hit["name"].rsplit(".", 1)[0]
                found.append(Finding(tool, _module_file(checkout, package, module), 0, f"{hit['status']} {hit['name']}"))
    else:
        raise ValueError(f"unknown quality tool {tool}")
    return found


def new_findings(found: list[Finding], known: Iterable[str]) -> list[Finding]:
    """Findings beyond the known ones, compared by key and counted, so a moved finding stays known."""
    left = collections.Counter(known)
    new = []
    for finding in sorted(found, key=lambda f: (f.path, f.what, f.line)):
        if left[finding.key] > 0:
            left[finding.key] -= 1
        else:
            new.append(finding)
    return new


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
        found = [f for f in found if any(fnmatch.fnmatchcase(f.what.split(" ")[-1], g) for g in globs)]
    return ToolRun(True, found)


def quality_dir(program: Program, settings: Settings) -> Path:
    if settings.quality_dir:
        return Path(settings.quality_dir)
    return Path(st.load(program).worktree_root) / "ship-quality"


def _baseline_path(folder: Path, tool: str) -> Path:
    return folder / f"baseline-{tool}.tsv"


def read_baseline(folder: Path, tool: str) -> list[tuple[Finding, str]]:
    """(finding, first seen) rows of one tool's baseline file."""
    path = _baseline_path(folder, tool)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text("utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        file, line_no, what, first = line.split("\t")
        rows.append((Finding(tool, file, int(line_no), what), first))
    return rows


def check_package(tool: str, package: Package, head: Path, base: Path | None, files: list[str], out: Path,
                  tag: str, settings: Settings, program: Program, heartbeat: Path | None = None,
                  globs: list[str] | None = None) -> tuple[str, str]:
    """(PASS | FAIL | NOTRUN, detail) for one tool on one package. Only findings in `files` count;
    known ones are the baseline's and, when `base` is given, those already at `base`."""
    if not package.quality(tool):
        return "NOTRUN", "no command in checks.toml"
    if globs is not None and not globs:
        return "NOTRUN", "no changed function to mutate"
    scope = set(files)
    at_head = run_tool(tool, package, head, out, f"{tag}-head", settings, program, globs, heartbeat)
    if not at_head.ok:
        return "FAIL", at_head.problem
    found = [f for f in at_head.findings if f.path in scope]
    known = [f.key for f, _ in read_baseline(quality_dir(program, settings), tool)]
    if base is not None:
        at_base = run_tool(tool, package, base, out, f"{tag}-base", settings, program, globs, heartbeat)
        if not at_base.ok:
            return "FAIL", at_base.problem
        known += [f.key for f in at_base.findings if f.path in scope]
    new = new_findings(found, known)
    (out / f"new-{tool}-{package.label}.txt").write_text("".join(f"{f}\n" for f in new), "utf-8", newline="\n")
    if new:
        return "FAIL", f"{len(new)} new: " + "; ".join(str(f) for f in new)
    return "PASS", f"no new findings ({len(found)} known)"


def checkpoint_quality(program: Program, settings: Settings, base: str, tools: tuple[str, ...]) -> tuple[bool, list[str]]:
    """The checkpoint's quality step at the build tip, against the commit the checkpoint started from."""
    state = st.load(program)
    repo, t = Path(state.repo), settings.git_timeout_s
    git(repo, "fetch", "-q", state.remote, timeout=t)
    tip = remote_sha(repo, state.remote, state.build_branch, t)
    out = program.quality(tip)
    out.mkdir(parents=True, exist_ok=True)
    files = changed_files(repo, base, tip, t)
    tip_copy = checkout_copy(repo, program.tmp / "quality-tip", tip, settings)
    base_copy = checkout_copy(repo, program.tmp / "quality-base", base, settings)
    lines: list[str] = []
    try:
        for package in touched(load_packages(program), files):
            mine = [f for f in files if package_of(load_packages(program), f) == package]
            for tool in tools:
                if tool == "mutmut":
                    sources = [f for f in mine if _is_source(f)]
                    globs = mutant_globs(tip_copy, package, changed_lines(repo, base, tip, sources, t)) if sources else []
                    verdict, detail = check_package(tool, package, tip_copy, None, sources, out, "tip", settings,
                                                    program, globs=globs)
                else:
                    verdict, detail = check_package(tool, package, tip_copy, base_copy, mine, out, "tip", settings,
                                                    program)
                lines.append(f"{verdict} quality-{tool}-{package.label} {tip[:8]} {detail}")
    finally:
        drop_copy(repo, tip_copy, settings)
        drop_copy(repo, base_copy, settings)
    (out / "summary.txt").write_text("\n".join(lines) + "\n", "utf-8", newline="\n")
    return not any(ln.startswith("FAIL ") for ln in lines), lines


def baseline(program: Program, settings: Settings, at: str | None, tools: tuple[str, ...],
             part: tuple[int, int] | None) -> tuple[bool, list[str]]:
    """Take the baseline at `at` (default: the build tip). Rewrites only the rows in scope, keeps each
    row's first-seen date, and regenerates BACKLOG.md. Run twice, the second run changes nothing."""
    state = st.load(program)
    repo, t = Path(state.repo), settings.git_timeout_s
    git(repo, "fetch", "-q", state.remote, timeout=t)
    sha = git(repo, "rev-parse", at, timeout=t).strip() if at else remote_sha(repo, state.remote, state.build_branch, t)
    folder = quality_dir(program, settings)
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / "runs" / sha[:8]
    out.mkdir(parents=True, exist_ok=True)
    copy = checkout_copy(repo, program.tmp / "quality-baseline", sha, settings)
    today = dt.date.today().isoformat()
    lines: list[str] = []
    try:
        tracked = git(copy, "ls-files", timeout=t).splitlines()
        for tool in tools:
            rows = read_baseline(folder, tool)
            first = {f.key: seen for f, seen in rows}
            for package in load_packages(program):
                if not package.quality(tool):
                    lines.append(f"NOTRUN baseline-{tool}-{package.label} no command in checks.toml")
                    continue
                owned = [f for f in tracked if package_of(load_packages(program), f) == package]
                globs = None
                scope = set(owned)
                if tool == "mutmut":
                    modules = sorted(f for f in owned if _is_source(f))
                    if part:
                        modules = modules[part[0] - 1::part[1]]
                    scope = set(modules)
                    whole = {m: set(range(1, len((copy / m).read_text("utf-8", errors="replace").splitlines()) + 2))
                             for m in modules}
                    globs = mutant_globs(copy, package, whole)
                ran = run_tool(tool, package, copy, out, "baseline", settings, program, globs) if globs != [] \
                    else ToolRun(True, [])
                if not ran.ok:
                    lines.append(f"FAIL baseline-{tool}-{package.label} {ran.problem}")
                    continue
                rows = [r for r in rows if r[0].path not in scope]
                rows += [(f, first.get(f.key, today)) for f in ran.findings if f.path in scope]
                lines.append(f"PASS baseline-{tool}-{package.label} {sum(f.path in scope for f in ran.findings)} findings")
            body = "".join(f"{f.path}\t{f.line}\t{f.what}\t{seen}\n"
                           for f, seen in sorted(rows, key=lambda r: (r[0].path, r[0].what, r[0].line)))
            _baseline_path(folder, tool).write_text(f"# {tool} baseline at {sha}\n{body}", "utf-8", newline="\n")
    finally:
        drop_copy(repo, copy, settings)
    write_backlog(folder)
    return not any(ln.startswith("FAIL ") for ln in lines), lines


def write_backlog(folder: Path) -> None:
    rows = [(f, seen) for tool in TOOLS for f, seen in read_baseline(folder, tool)]
    table = "".join(f"| {f.tool} | {f.path} | {f.line} | {f.what.replace('|', '/')} | {seen} |\n" for f, seen in rows)
    (folder / "BACKLOG.md").write_text(
        "# Quality backlog\n\n"
        "Generated by `ship baseline`; do not edit. These findings were in the code when the baseline was taken.\n"
        "They never block a slice or a checkpoint. A later fixer works through them; the next baseline drops\n"
        "the ones that are gone.\n\n"
        f"{len(rows)} findings.\n\n| tool | file | line | finding | first seen |\n|---|---|---|---|---|\n{table}",
        "utf-8", newline="\n")
