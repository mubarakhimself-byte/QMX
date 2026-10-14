"""DESIGN section 2 module rules, read from the source tree with `ast`."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from qma.boot import KEEP_NAMES, banned_fragment

SRC = Path(__file__).resolve().parents[1] / "src"
STDLIB_ONLY = ("qma.boot", "qma.launcher")
SDK_ALLOWED = ("qma.harness", "qma.gpt.probe")


def modules() -> dict[str, ast.Module]:
    found: dict[str, ast.Module] = {}
    for path in sorted((SRC / "qma").rglob("*.py")):
        parts = path.relative_to(SRC).with_suffix("").parts
        name = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
        found[name] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return found


def imports(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module)
    return names


def calls(tree: ast.Module, name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == name)
            or (isinstance(node.func, ast.Attribute) and node.func.attr == name)
        )
        for node in ast.walk(tree)
    )


def within(module: str, packages: tuple[str, ...]) -> bool:
    return any(module == package or module.startswith(f"{package}.") for package in packages)


def test_the_sdk_is_imported_only_in_the_harness_and_the_gpt_probe() -> None:
    offenders = [
        module
        for module, tree in modules().items()
        if not within(module, SDK_ALLOWED)
        and any(within(name, ("claude_agent_sdk",)) for name in imports(tree))
    ]
    assert offenders == []


def test_boot_and_launcher_import_only_the_standard_library() -> None:
    allowed = sys.stdlib_module_names | {"__future__"}
    found = modules()
    assert set(STDLIB_ONLY) <= set(found)
    offenders = {
        module: sorted(name for name in imports(found[module]) if name.split(".")[0] not in allowed)
        for module in STDLIB_ONLY
    }
    assert offenders == {module: [] for module in STDLIB_ONLY}


def test_the_console_imports_nothing_from_the_harness() -> None:
    console = modules().get("qma.console")
    assert console is None or not any(within(name, ("qma.harness",)) for name in imports(console))


def test_nothing_outside_the_harness_imports_its_submodules() -> None:
    offenders = [
        (module, name)
        for module, tree in modules().items()
        if not within(module, ("qma.harness",))
        for name in imports(tree)
        if name.startswith("qma.harness.")
    ]
    assert offenders == []


def test_test_mode_and_probe_passed_are_built_only_where_allowed() -> None:
    found = modules()
    assert [module for module, tree in found.items() if calls(tree, "TestMode")] == []
    probe_passed = [module for module, tree in found.items() if calls(tree, "ProbePassed")]
    assert set(probe_passed) <= {"qma.gpt.probe"}


def test_keep_names_hold_no_banned_fragment() -> None:
    assert {name: banned_fragment(name) for name in KEEP_NAMES if banned_fragment(name)} == {}
