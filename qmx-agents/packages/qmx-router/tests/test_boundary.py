"""AD-56 boundary rules, read from the router's source tree with `ast`."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
BARRED = ("qma", "qmx_engine", "qmx_control", "qmx_host", "qmx_library")


def sources() -> dict[str, ast.Module]:
    found: dict[str, ast.Module] = {}
    for path in sorted((SRC / "qmx_router").rglob("*.py")):
        parts = path.relative_to(SRC).with_suffix("").parts
        name = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
        found[name] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return found


def imported(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module)
    return names


def test_the_router_imports_no_harness_engine_control_host_or_library_module() -> None:
    offenders = {
        module: sorted(name for name in imported(tree) if name.split(".")[0] in BARRED)
        for module, tree in sources().items()
    }
    assert {module: names for module, names in offenders.items() if names} == {}


def test_a_probe_pass_is_built_only_in_the_probe_module() -> None:
    builders = sorted(
        module
        for module, tree in sources().items()
        if module != "qmx_router.gpt.probe"
        and any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name | ast.Attribute)
            and (node.func.id if isinstance(node.func, ast.Name) else node.func.attr)
            == "ProbePassed"
            for node in ast.walk(tree)
        )
    )
    assert builders == []


def test_the_old_paths_are_the_moved_modules() -> None:
    import qma.gpt.probe
    import qma.gpt.siwc
    import qma.gpt.translate

    import qmx_router.gpt.probe
    import qmx_router.gpt.siwc
    import qmx_router.gpt.translate

    assert qma.gpt.translate is qmx_router.gpt.translate
    assert qma.gpt.siwc is qmx_router.gpt.siwc
    assert qma.gpt.probe is qmx_router.gpt.probe
