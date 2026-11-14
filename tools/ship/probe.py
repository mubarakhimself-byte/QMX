"""probe: can a test fail? The "returns nothing" probe of a `pin` slice's new tests (U29, D-L18).

The technique of the factory's `audit-area/scripts/probe_tests.py`, here in the kit: for each test, every name
from the package under test that the test calls (in its body and in the module-level helpers and fixtures of
its own file it calls, followed through; as a function, a class, `Class.method` or `module.function`) is found
by reading the test file. Then the tests run three ways, through the package's own `test` command in the
checkout (so through the kit's timed wrapper):

- as they are (normal);
- with every one of those names swapped for a function returning None (none);
- with every one swapped for a function returning a sentinel no code would produce (sentinel).

A test that fails under either swap `can-fail`. One that passes under both `cannot-fail`: whatever its subject
returns, it stays green. One that calls nothing from the package is `no-subject`. A run that errors, skips,
times out, gives no result, or a swap that could not be made (the name did not resolve, or resolved to code
outside the checkout) is `error`, never a verdict. Each test has its own watchdog (`probe_test_timeout_s`): a
test that hangs is recorded `timeout` and the rest rerun, so one hang loses one row.

`probe(...)` writes `<out>` (tab-separated: test_id subjects normal none sentinel verdict) and the logs of
each run beside it, and returns the rows. Standard library only.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import os
import shutil
import tempfile
from pathlib import Path

from ship.settings import Settings
from ship.suite import Package, expand
from ship.wrapper import GUARD_DIR, run_timed

PLUGIN_NAME = "ship_probe_plugin"
PLUGIN = r'''"""Written by ship/probe.py: run the plan's tests, swap their subjects, record outcomes as they come."""
import importlib
import json
import os
import threading

import pytest

with open(os.environ["SHIP_PROBE_PLAN"], encoding="utf-8") as _fh:
    _PLAN = json.load(_fh)
_MODE = _PLAN["mode"]
_ROOT = os.path.normcase(os.path.realpath(_PLAN["root"]))
_RANK = {"passed": 0, "skipped": 1, "failed": 2, "error": 3, "swap-failed": 4, "outside-checkout": 5, "timeout": 6}
_results = {}
_flags = {}
_saved = []


class _ProbeSentinel:
    """What no code under test returns."""

    def __repr__(self):
        return "<probe sentinel>"


_SENTINEL = _ProbeSentinel()
_MISSING = object()


def _fake(*args, **kwargs):
    return None if _MODE == "none" else _SENTINEL


def _base(nodeid):
    return nodeid.split("[")[0]


def _flush():
    tmp = _PLAN["out"] + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(_results, fh)
    os.replace(tmp, _PLAN["out"])


def _record(base, outcome):
    if base not in _results or _RANK[outcome] > _RANK[_results[base]]:
        _results[base] = outcome
    _flush()


def _resolve(subject):
    module_name, _, attr = subject.partition(":")
    module = importlib.import_module(module_name)
    path = os.path.normcase(os.path.realpath(getattr(module, "__file__", "") or ""))
    if not path.startswith(_ROOT + os.sep):
        raise LookupError("outside-checkout")
    owner = module
    if "." in attr:
        owner_name, attr = attr.split(".", 1)
        owner = getattr(module, owner_name)
    return module, owner, attr, getattr(owner, attr)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    base = _base(item.nodeid)

    def hang():
        _record(base, "timeout")
        os._exit(97)

    timer = threading.Timer(_PLAN["timeout"], hang)
    timer.daemon = True
    timer.start()
    try:
        yield
    finally:
        timer.cancel()


def pytest_runtest_setup(item):
    base = _base(item.nodeid)
    for subject in _PLAN["subjects"].get(base, []):
        try:
            module, owner, attr, original = _resolve(subject)
        except LookupError as exc:
            if str(exc) == "outside-checkout":
                _flags[base] = "outside-checkout"
            elif _MODE != "normal":
                _flags[base] = "swap-failed"
            continue
        except Exception:
            if _MODE != "normal":
                _flags[base] = "swap-failed"
            continue
        if _MODE == "normal":
            continue
        if isinstance(owner, type):
            _saved.append((owner, attr, owner.__dict__.get(attr, _MISSING)))
            setattr(owner, attr, staticmethod(_fake))
            continue
        _saved.append((owner, attr, original))
        setattr(owner, attr, _fake)
        if owner is module:
            for target in {getattr(item, "module", None)} - {None}:
                for name, value in list(vars(target).items()):
                    if value is original:
                        _saved.append((target, name, value))
                        setattr(target, name, _fake)


def pytest_runtest_teardown(item, nextitem):
    while _saved:
        owner, attr, value = _saved.pop()
        if value is _MISSING:
            delattr(owner, attr)
        else:
            setattr(owner, attr, value)


def pytest_runtest_logreport(report):
    if report.when != "call" and report.outcome == "passed":
        return
    base = _base(report.nodeid)
    outcome = "error" if report.when != "call" and report.outcome == "failed" else report.outcome
    _record(base, _flags.get(base) or outcome)
    if report.when == "teardown" and base in _flags:
        _record(base, _flags[base])


def pytest_sessionfinish(session, exitstatus):
    for base, flag in _flags.items():
        _record(base, flag)
    _flush()
'''

BAD = frozenset({"error", "skipped", "missing", "swap-failed", "outside-checkout", "timeout"})
VERDICTS = ("cannot-fail", "can-fail", "no-subject", "error")


@dataclasses.dataclass(frozen=True)
class Row:
    test_id: str  # the pytest node id, relative to the package root
    subjects: tuple[str, ...]
    normal: str
    none: str
    sentinel: str
    verdict: str

    def line(self) -> str:
        return "\t".join((self.test_id, ",".join(self.subjects) or "-", self.normal, self.none, self.sentinel,
                          self.verdict))


def import_names(root: Path) -> list[str]:
    """The package's import names: src/<name>/__init__.py, a namespace src/<ns>/<name>/, or folders beside tests/."""
    names: list[str] = []
    for base in ([root / "src"] if (root / "src").is_dir() else []) + [root]:
        for d in sorted(p for p in base.iterdir() if p.is_dir() and p.name not in ("tests", "test", ".venv")):
            if (d / "__init__.py").exists():
                names.append(d.name)
            elif base.name == "src":
                names += [f"{d.name}.{s.name}" for s in sorted(d.iterdir()) if (s / "__init__.py").exists()]
        if names:
            break
    if not names and (root / "__init__.py").exists():
        names.append(root.name)
    return names


def _is_test_module(module: str) -> bool:
    return any(part in ("tests", "test", "conftest") or part.startswith("test_") for part in module.split("."))


def _under(module: str, names: list[str]) -> bool:
    return any(module == n or module.startswith(n + ".") for n in names) and not _is_test_module(module)


def subjects(source: str, rel: str, names: list[str]) -> dict[str, list[str]]:
    """{node id: every package name the test calls, as "module:attr" or "module:Class.attr"} per test function."""
    tree = ast.parse(source)
    imported: dict[str, tuple[str, str]] = {}  # local name -> (module, attr)
    modules: dict[str, str] = {}  # local alias -> module
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0 and _under(node.module, names):
            for a in node.names:
                if a.name != "*":
                    imported[a.asname or a.name] = (node.module, a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                if _under(a.name, names):
                    modules[a.asname or a.name] = a.name
    helpers = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def is_module(attr: str) -> bool:
        return attr == attr.lower() and not attr.startswith("_")  # `from pkg import mod`; a class is CamelCase

    def calls(fn: ast.AST, seen: set[str]) -> list[str]:
        found: list[str] = []
        args = getattr(fn, "args", None)
        for name in [a.arg for a in args.args] if isinstance(args, ast.arguments) else []:
            if name in helpers and name not in seen:  # fixtures defined in the same file
                seen.add(name)
                found += calls(helpers[name], seen)
        for call in sorted((n for n in ast.walk(fn) if isinstance(n, ast.Call)), key=lambda n: (n.lineno, n.col_offset)):
            f = call.func
            if isinstance(f, ast.Name) and f.id in imported:
                found.append("%s:%s" % imported[f.id])
            elif isinstance(f, ast.Name) and f.id in helpers and f.id not in seen:
                seen.add(f.id)
                found += calls(helpers[f.id], seen)
            elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                base = f.value.id
                if base in modules:
                    found.append(f"{modules[base]}:{f.attr}")
                elif base in imported:
                    module, attr = imported[base]
                    if is_module(attr):  # `from pkg import mod` then `mod.f()`
                        found.append(f"{module}.{attr}:{f.attr}")
                    else:  # `from pkg import Cls` then `Cls.make()`
                        found.append(f"{module}:{attr}.{f.attr}")
        return found

    out: dict[str, list[str]] = {}
    for node in tree.body:
        tests = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            tests.append((f"{rel}::{node.name}", node))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            tests += [(f"{rel}::{node.name}::{sub.name}", sub) for sub in node.body
                      if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name.startswith("test")]
        for nodeid, fn in tests:
            out[nodeid] = list(dict.fromkeys(calls(fn, set())))
    return out


def verdict(subjects_: list[str] | tuple[str, ...], normal: str, none: str, sentinel: str) -> str:
    if normal != "passed":
        return "error"
    if not subjects_:
        return "no-subject"
    if none in BAD:
        return "error"
    if none == "failed":
        return "can-fail"
    if sentinel in BAD:
        return "error"
    return "can-fail" if sentinel == "failed" else "cannot-fail"


class _Runner:
    def __init__(self, checkout: Path, package: Package, out: Path, settings: Settings, tmp_root: Path,
                 heartbeat: Path | None):
        self.checkout, self.package, self.out, self.settings = checkout, package, out, settings
        self.tmp_root, self.heartbeat = tmp_root, heartbeat
        tmp_root.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix="probe-", dir=tmp_root))
        (self.tmp / "plugin").mkdir()
        (self.tmp / "plugin" / f"{PLUGIN_NAME}.py").write_text(PLUGIN, "utf-8")
        self.n = 0

    def once(self, mode: str, ids: list[str], plan: dict[str, list[str]]) -> dict[str, str]:
        self.n += 1
        result = self.tmp / f"result-{self.n}.json"
        plan_file = self.tmp / f"plan-{self.n}.json"
        per_test = self.settings.probe_test_timeout_s
        plan_file.write_text(json.dumps({"mode": mode, "root": str(self.checkout), "timeout": per_test,
                                         "subjects": {i: plan.get(i, []) for i in ids}, "out": str(result)}), "utf-8")
        path = os.pathsep.join(p for p in (str(self.tmp / "plugin"), str(GUARD_DIR), os.environ.get("PYTHONPATH", ""))
                               if p)
        args = ["-p", PLUGIN_NAME, "-p", "no:cacheprovider", "-p", "no:xdist", "-o", "addopts=",
                "--rootdir", str(self.checkout / self.package.root), *ids]
        argv = expand(self.package.test, self.tmp / f"junit-{self.n}.xml", args)
        run_timed(argv, self.checkout / self.package.root, self.out.with_name(f"{self.out.stem}-{self.n}-{mode}.log"),
                  per_test * len(ids) + 120, self.settings, self.tmp_root, self.heartbeat,
                  extra_env={"SHIP_PROBE_PLAN": str(plan_file), "PYTHONPATH": path})
        try:
            return json.loads(result.read_text("utf-8"))
        except (OSError, ValueError):
            return {}

    def run(self, mode: str, ids: list[str], plan: dict[str, list[str]]) -> dict[str, str]:
        """Every id's outcome; a run cut short by a hang reruns the ids it had not reached."""
        results: dict[str, str] = {}
        pending = list(ids)
        while pending:
            got = self.once(mode, pending, plan)
            new = {i: got[i] for i in pending if i in got}
            if not new:
                results.update({i: "missing" for i in pending})
                break
            results.update(new)
            pending = [i for i in pending if i not in results]
        return results

    def close(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


def probe(checkout: Path, package: Package, node_ids: list[str], out: Path, settings: Settings, tmp_root: Path,
          heartbeat: Path | None = None) -> list[Row]:
    """Probe the tests `node_ids` (pytest node ids relative to the package root, `[params]` dropped) of `package`
    in `checkout`. Writes `out` and returns one Row per id."""
    root = checkout / package.root
    names = import_names(root)
    plan: dict[str, list[str]] = {}
    for rel in sorted({i.split("::", 1)[0] for i in node_ids}):
        try:
            found = subjects((root / rel).read_text("utf-8", errors="replace"), rel, names)
        except (OSError, SyntaxError):
            found = {}
        plan.update({i: s for i, s in found.items() if i in node_ids})
    out.parent.mkdir(parents=True, exist_ok=True)
    runner = _Runner(checkout, package, out, settings, tmp_root, heartbeat)
    try:
        normal = runner.run("normal", list(node_ids), plan)
        swap = [i for i in node_ids if plan.get(i) and normal.get(i) == "passed"]
        none = runner.run("none", swap, plan) if swap else {}
        again = [i for i in swap if none.get(i) == "passed"]
        sentinel = runner.run("sentinel", again, plan) if again else {}
    finally:
        runner.close()
    rows = []
    for i in node_ids:
        subj = tuple(plan.get(i, []))
        n, z, s = normal.get(i, "missing"), none.get(i, "-"), sentinel.get(i, "-")
        rows.append(Row(i, subj, n, z, s, verdict(subj, n, z, s)))
    out.write_text("test_id\tsubjects\tnormal\tnone\tsentinel\tverdict\n" + "".join(r.line() + "\n" for r in rows),
                   "utf-8", newline="\n")
    return rows
