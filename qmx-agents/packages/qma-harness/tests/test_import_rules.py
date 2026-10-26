"""DESIGN section 2 module rules, read from the source tree with `ast`."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import NamedTuple

from qma.boot import KEEP_NAMES, banned_fragment

SRC = Path(__file__).resolve().parents[1] / "src"
STDLIB_ONLY = ("qma.boot", "qma.launcher", "qma.telemetry")
SDK_ALLOWED = ("qma.harness", "qma.gpt.probe")


class Source(NamedTuple):
    tree: ast.Module
    package: str


Modules = dict[str, Source]


def modules(src: Path = SRC) -> Modules:
    found: Modules = {}
    for path in sorted((src / "qma").rglob("*.py")):
        parts = path.relative_to(src).with_suffix("").parts
        package = ".".join(parts[:-1])
        name = package if parts[-1] == "__init__" else ".".join(parts)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        found[name] = Source(tree, package)
    return found


def imports(source: Source) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(source.tree):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            parts = source.package.split(".")
            base = parts[: len(parts) - node.level + 1] if node.level else []
            origin = ".".join([*base, *([node.module] if node.module else [])])
            names.add(origin)
            names |= {f"{origin}.{alias.name}" for alias in node.names if alias.name != "*"}
    return names


def calls(source: Source, name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == name)
            or (isinstance(node.func, ast.Attribute) and node.func.attr == name)
        )
        for node in ast.walk(source.tree)
    )


def within(module: str, packages: tuple[str, ...]) -> bool:
    return any(module == package or module.startswith(f"{package}.") for package in packages)


def sdk_offenders(found: Modules) -> list[str]:
    return [
        module
        for module, source in found.items()
        if not within(module, SDK_ALLOWED)
        and any(within(name, ("claude_agent_sdk",)) for name in imports(source))
    ]


def non_stdlib_imports(found: Modules) -> dict[str, list[str]]:
    allowed = sys.stdlib_module_names | {"__future__"}
    return {
        module: sorted(name for name in imports(found[module]) if name.split(".")[0] not in allowed)
        for module in STDLIB_ONLY
        if module in found
    }


def harness_submodule_imports(found: Modules) -> list[tuple[str, str]]:
    return [
        (module, name)
        for module, source in found.items()
        if not within(module, ("qma.harness",))
        for name in sorted(imports(source))
        if name.startswith("qma.harness.")
    ]


def probe_pass_builders(found: Modules) -> list[str]:
    """Modules outside `qma.gpt.probe` that call `ProbePassed(` or import its mint. Only `src/`
    is scanned; tests build passes on purpose."""
    return sorted(
        module
        for module, source in found.items()
        if module != "qma.gpt.probe"
        and (calls(source, "ProbePassed") or "qma.gpt.probe._MINT" in imports(source))
    )


def plant(root: Path, files: dict[str, str]) -> Modules:
    for relative, source in files.items():
        path = root / "qma" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    return modules(root)


def test_the_sdk_is_imported_only_in_the_harness_and_the_gpt_probe() -> None:
    assert sdk_offenders(modules()) == []


def test_boot_and_launcher_import_only_the_standard_library() -> None:
    found = modules()
    assert set(STDLIB_ONLY) <= set(found)
    assert non_stdlib_imports(found) == {module: [] for module in STDLIB_ONLY}


def test_the_console_imports_nothing_from_the_harness() -> None:
    console = modules().get("qma.console")
    assert console is None or not any(within(name, ("qma.harness",)) for name in imports(console))


def test_nothing_outside_the_harness_imports_its_submodules() -> None:
    assert harness_submodule_imports(modules()) == []


def test_relative_and_from_package_imports_are_resolved(tmp_path: Path) -> None:
    found = plant(
        tmp_path,
        {
            "harness/__init__.py": "",
            "harness/procs.py": "from . import chat\nfrom .chat import Chat\n",
            "launcher.py": "from .harness import procs\n",
            "boot.py": "from qma.harness import procs\nfrom ctypes import wintypes\n",
            "serve.py": "from qma import harness\n",
        },
    )
    assert non_stdlib_imports(found) == {
        "qma.boot": ["qma.harness", "qma.harness.procs"],
        "qma.launcher": ["qma.harness", "qma.harness.procs"],
    }
    assert harness_submodule_imports(found) == [
        ("qma.boot", "qma.harness.procs"),
        ("qma.launcher", "qma.harness.procs"),
    ]


def test_test_mode_and_probe_passed_are_built_only_where_allowed() -> None:
    found = modules()
    assert [module for module, source in found.items() if calls(source, "TestMode")] == []
    assert probe_pass_builders(found) == []


def test_a_planted_probe_pass_outside_probe_py_is_caught(tmp_path: Path) -> None:
    found = plant(
        tmp_path,
        {
            "gpt/probe.py": "ProbePassed(at, version, model, _mint=_MINT)\n",
            "harness/usage.py": "from qma.gpt.probe import ProbePassed\nProbePassed(a, b, c)\n",
            "harness/harness.py": "from qma.gpt.probe import _MINT\n",
            "console.py": "from qma.gpt import probe\nprobe.ProbePassed(a, b, c)\n",
        },
    )
    assert probe_pass_builders(found) == ["qma.console", "qma.harness.harness", "qma.harness.usage"]


def test_keep_names_hold_no_banned_fragment() -> None:
    assert {name: banned_fragment(name) for name in KEEP_NAMES if banned_fragment(name)} == {}
