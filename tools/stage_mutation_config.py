"""Stage bounded nightly mutation scopes for the pinned Mutmut 3.3 CLI.

Mutmut 3.3 reads ``paths_to_mutate`` and ``do_not_mutate``. Keeping src as
the copied root preserves imports of sibling modules while excluding those
siblings from mutation. Pytest arguments belong in its own ``addopts``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

import tomllib

_MUTATION_OPTIONS = {
    "source_paths",
    "only_mutate",
    "also_copy",
    "pytest_add_cli_args",
    "pytest_add_cli_args_test_selection",
}


def _table(value: object, name: str, allowed: set[str]) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a table")
    table = cast("dict[str, object]", value)
    unknown = table.keys() - allowed
    if unknown:
        raise ValueError(f"{name}: unsupported options: {sorted(unknown)}")
    return table


def _strings(value: object, name: str, *, required: bool = True) -> list[str]:
    if not isinstance(value, list) or (required and not value):
        raise ValueError(f"{name} must be a nonempty list of strings")
    items = cast("list[object]", value)
    if any(not isinstance(item, str) or not item.strip() for item in items):
        raise ValueError(f"{name} must contain nonempty strings")
    result = cast("list[str]", items)
    if len(set(result)) != len(result):
        raise ValueError(f"{name} contains duplicates")
    return result


def _contained(component: Path, value: str) -> Path:
    if any(part in {"", ".", ".."} for part in value.split("/")) or any(
        character in value for character in "\\:*?[]"
    ):
        raise ValueError(f"unsafe component-relative path: {value}")
    path = component / value
    if not path.resolve().is_relative_to(component.resolve()) or not path.exists():
        raise ValueError(f"path is missing or outside the component: {value}")
    if any(
        candidate.is_symlink()
        for candidate in (path, *path.parents)
        if candidate.is_relative_to(component)
    ):
        raise ValueError(f"symlinks are not allowed in mutation inputs: {value}")
    return path


def _array(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def stage(manifest: Path, declaration: Path) -> None:
    """Append compatible tool tables to a disposable component manifest."""
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError("component manifest must be a regular file, not a symlink")
    original = manifest.read_text(encoding="utf-8")
    config = _table(tomllib.loads(declaration.read_text(encoding="utf-8")), "declaration", {"tool"})
    tool = _table(config.get("tool"), "tool", {"mutmut", "pytest"})
    mutation = _table(tool.get("mutmut"), "tool.mutmut", _MUTATION_OPTIONS)
    pytest_tool = _table(tool.get("pytest"), "tool.pytest", {"ini_options"})
    pytest = _table(pytest_tool.get("ini_options"), "tool.pytest.ini_options", {"testpaths"})
    roots = _strings(mutation.get("source_paths"), "source_paths")
    if roots != ["src"]:
        raise ValueError("source_paths must be ['src'] for the pinned staging contract")
    source = _contained(manifest.parent, "src")
    if not source.is_dir():
        raise ValueError("source_paths must name a directory")
    targets = _strings(mutation.get("only_mutate"), "only_mutate")
    for target in targets:
        path = _contained(manifest.parent, target)
        if not path.is_file() or path.suffix != ".py" or not path.is_relative_to(source):
            raise ValueError(f"only_mutate must name a Python file under src: {target}")
    for candidate in source.rglob("*"):
        _contained(manifest.parent, candidate.relative_to(manifest.parent).as_posix())
    testpaths = _strings(pytest.get("testpaths"), "testpaths")
    for testpath in testpaths:
        if not _contained(manifest.parent, testpath).is_dir():
            raise ValueError(f"testpaths must name directories: {testpath}")
    selection = _strings(
        mutation.get("pytest_add_cli_args_test_selection"), "pytest_add_cli_args_test_selection"
    )
    if selection != testpaths:
        raise ValueError("pytest test selection must match testpaths")
    copies = _strings(mutation.get("also_copy", []), "also_copy", required=False)
    for copied in copies:
        path = _contained(manifest.parent, copied)
        if path.is_dir():
            for candidate in path.rglob("*"):
                _contained(manifest.parent, candidate.relative_to(manifest.parent).as_posix())
    addopts = _strings(
        mutation.get("pytest_add_cli_args", []), "pytest_add_cli_args", required=False
    )
    excluded = sorted(
        path.relative_to(manifest.parent).as_posix()
        for root in roots
        for path in (manifest.parent / root).rglob("*.py")
        if path.relative_to(manifest.parent).as_posix() not in targets
    )
    lines = [
        "",
        "[tool.mutmut]",
        "paths_to_mutate = " + _array(roots),
        "do_not_mutate = " + _array(excluded),
    ]
    if "also_copy" in mutation:
        lines.append("also_copy = " + _array(copies))
    lines.extend(
        [
            "",
            "[tool.pytest.ini_options]",
            "testpaths = " + _array(testpaths),
        ]
    )
    if "pytest_add_cli_args" in mutation:
        lines.append("addopts = " + _array(addopts))
    staged = original + "\n".join(lines) + "\n"
    tomllib.loads(staged)
    with manifest.open("a", encoding="utf-8", newline="\n") as output:
        output.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Stage a component manifest and report invalid configuration as failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("declaration", type=Path)
    args = parser.parse_args(argv)
    try:
        stage(args.manifest, args.declaration)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"mutation staging: FAIL: {exc}", file=sys.stderr)
        return 2
    print("mutation staging: compatible Mutmut 3.3 configuration appended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
