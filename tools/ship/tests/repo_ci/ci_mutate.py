"""Which functions mutmut mutates: the ones a diff touched, or one part of the whole-repo walk.

mutmut 3 mutates code inside functions and names each mutant `<module>.<mangled>__mutmut_<n>`, where
a top-level function `f` mangles to `x_f` and a method `C.m` to `xǁCǁm`. A glob on that name runs
every mutant of one function, so a target is (source package, module, function) and the job turns it
into `mutmut run "<module>.<mangled>__mutmut_*"`.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import re
from collections.abc import Iterable
from pathlib import Path

WALK_PARTS = 24
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)


@dataclasses.dataclass(frozen=True, order=True)
class Target:
    package: str  # folder holding src/ and tests/, repo-relative
    module: str  # dotted, e.g. qmf.core.exact
    function: str  # `f` or `C.m`

    @property
    def mangled(self) -> str:
        if "." in self.function:
            cls, name = self.function.split(".", 1)
            return f"xǁ{cls}ǁ{name}"
        return f"x_{self.function}"

    @property
    def glob(self) -> str:
        return f"{self.module}.{self.mangled}__mutmut_*"

    @property
    def key(self) -> str:
        return f"{self.package}|{self.module}.{self.function}"


def source_package(path: str) -> tuple[str, str] | None:
    """(package folder, path inside its src/) for a .py file under some `<package>/src/`."""
    if not path.endswith(".py") or "/src/" not in path:
        return None
    package, inside = path.split("/src/", 1)
    if (
        "/tests/" in f"/{inside}"
        or inside.endswith("__init__.py")
        or inside.endswith("__main__.py")
    ):
        return None
    return package, inside


def module_name(inside_src: str) -> str:
    return inside_src[: -len(".py")].replace("/", ".")


def functions(source: str) -> list[tuple[str, int, int]]:
    """(name, first line, last line) of every top-level function and class method mutmut mutates."""
    tree = ast.parse(source)
    found: list[tuple[str, int, int]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found.append((node.name, node.lineno, node.end_lineno or node.lineno))
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    found.append(
                        (f"{node.name}.{item.name}", item.lineno, item.end_lineno or item.lineno)
                    )
    return found


def changed_lines(unified_zero_diff: str) -> set[int]:
    """New-side line numbers from `git diff -U0` of one file."""
    lines: set[int] = set()
    for match in HUNK.finditer(unified_zero_diff):
        start, count = int(match.group(1)), int(match.group(2) or "1")
        lines.update(range(start, start + count))
    return lines


def touched_functions(source: str, lines: set[int]) -> list[str]:
    return [
        name for name, first, last in functions(source) if any(first <= n <= last for n in lines)
    ]


def all_targets(repo: Path, packages: Iterable[str]) -> list[Target]:
    targets: list[Target] = []
    for package in packages:
        src = repo / package / "src"
        for path in sorted(src.rglob("*.py")):
            rel = path.relative_to(repo).as_posix()
            found = source_package(rel)
            if found is None:
                continue
            try:
                names = functions(path.read_text("utf-8"))
            except SyntaxError:
                continue
            targets.extend(Target(package, module_name(found[1]), name) for name, _, _ in names)
    return targets


def walk_part(targets: list[Target], part: int, parts: int) -> list[Target]:
    """A stable split: a function stays in its part while other functions come and go."""

    def bucket(t: Target) -> int:
        return int(hashlib.sha256(t.key.encode()).hexdigest(), 16) % parts

    return [t for t in targets if bucket(t) == part]


RESULT = re.compile(r"^\s*(\S+__mutmut_\d+): (.+?)\s*$")
SURVIVING = frozenset({"survived", "no tests"})


def parse_results(text: str) -> dict[str, str]:
    """mutant name -> status, from `mutmut results --all true`."""
    return {m.group(1): m.group(2) for line in text.splitlines() if (m := RESULT.match(line))}


def survivors_by_function(results: dict[str, str], targets: list[Target]) -> dict[str, int]:
    prefix = {f"{t.module}.{t.mangled}__mutmut_": t.key for t in targets}
    counts = dict.fromkeys(prefix.values(), 0)
    for name, status in results.items():
        stem = name.rsplit("__mutmut_", 1)[0] + "__mutmut_"
        if stem in prefix and status in SURVIVING:
            counts[prefix[stem]] += 1
    return counts
