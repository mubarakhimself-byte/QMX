"""Inventory tracked Python callers and closed QMA deletion sets.

Run with Python 3.14 from any directory. By default inspect tracked working-tree
files (including edits/deletions); --ref inspects an immutable Git revision.
Physical source lines include blanks/comments, exclude tests and resources.

Imports include relative, conditional and local imports, named re-exports,
package initialization, and literal dotted QMA references (conservative dynamic
loads/monkeypatches/entrypoints). Computed module names and external deployments
cannot be proven statically. Parse failures are fatal, never silently skipped.

--trim-facades plans removal of initializer re-exports that nothing outside the
package's own tests/examples imports; its sets are NOT safe until those exports
are actually trimmed and a normal scan is clean.
--retire-caller names individual unprotected legacy examples/tests to retire
with their implementation. Protected callers cannot be excluded. Neither flag
edits files. QMA's own tests are reported separately and require review before
retirement; they do not keep the runtime alive by themselves.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = {f"qma.{name}": f"qmx-agents/packages/qma-{name}" for name in ("daemon", "core", "wire")}
PINNED = {"qma.wire.schemas", "qma.wire.money_path_diff"}
# Possessive, so "qma.daemon.panel-composition.v1" (an id) is not read as "qma.daemon".
REFERENCE = re.compile(r"\bqma\.(?:core|daemon|wire)(?:\.[A-Za-z_]\w*)*+(?![-\w])")
CLI_REFERENCE = re.compile(r"\bpython(?:\.exe)?(?:\s+-[BIu])*\s+-m\s+(qma\.[\w.]+)")


def git(*args: str) -> bytes:
    executable = shutil.which("git")
    if executable is None:
        raise RuntimeError("git is required")
    return subprocess.check_output([executable, *args], cwd=ROOT)


def protected(path: str) -> bool:
    return path.split("/", maxsplit=1)[0] in {
        "qml",
        "qmb",
        "qmn",
        "extensions",
        "apps",
        "docs",
    } or path.startswith("packages/qmf-")


def category(path: str) -> str:
    if "tests" in Path(path).parts or Path(path).name.startswith("test_"):
        return "tests"
    if protected(path):
        return "protected"
    if any(
        path.startswith(f"qmx-agents/packages/{name}/")
        for name in ("qmx-agents", "qmx-control", "qmx-apps")
    ):
        return "new"
    return "other"


def owned_extra(path: str) -> bool:
    return any(
        path.startswith(f"{root}/{folder}/")
        for root in PACKAGES.values()
        for folder in ("tests", "examples")
    )


def module_name(path: str) -> str:
    tail = path.split("/src/", 1)[-1].removesuffix(".py").replace("/", ".")
    return tail.removesuffix(".__init__")


def from_module(node: ast.ImportFrom, module: str, initializer: bool) -> str:
    if not node.level:
        return node.module or ""
    package = module if initializer else module.rpartition(".")[0]
    parts = package.split(".")
    prefix = parts[: len(parts) - node.level + 1]
    return ".".join([*prefix, *([node.module] if node.module else [])])


def inventory(ref: str | None, retired: set[str], trim: bool) -> dict:
    paths = (
        git("ls-tree", "-rz", "--name-only", ref).decode().split("\0")
        if ref
        else git("ls-files", "-z").decode().split("\0")
    )
    sources = {}
    trees = {}
    for path in sorted(p for p in paths if p.endswith(".py")):
        if ref:
            raw = git("show", f"{ref}:{path}")
        elif (ROOT / path).exists():
            raw = (ROOT / path).read_bytes()
        else:
            continue
        sources[path] = raw
        trees[path] = ast.parse(raw, filename=path)
    invalid = {p for p in retired if p not in sources or protected(p)}
    if invalid:
        raise ValueError(f"Unknown or protected retired callers: {sorted(invalid)}")
    modules = {
        module_name(p): p
        for p in sources
        if any(p.startswith(root + "/src/") for root in PACKAGES.values())
    }
    by_path = {p: m for m, p in modules.items()}
    exports = {}
    for module, path in modules.items():
        for node in trees[path].body:
            if isinstance(node, ast.ImportFrom):
                base = from_module(node, module, path.endswith("/__init__.py"))
                for alias in node.names:
                    exports[module, alias.asname or alias.name] = (base, alias.name)

    # Which files import each re-export from its package; the current file is
    # tracked while scanning so resolve() can record it.
    used_exports = defaultdict(set)
    current = [""]

    def resolve(base: str, name: str = "", seen: frozenset = frozenset()) -> set[str]:
        if (base, name) in seen:
            return {base} if base in modules else set()
        qualified = f"{base}.{name}" if name else base
        result = {base} if base in modules else set()
        if name == "*":
            for owner, symbol in exports:
                if owner == base:
                    result |= resolve(base, symbol, seen | {(base, name)})
        if qualified in modules:
            result.add(qualified)
        elif (base, name) in exports:
            used_exports[base, name].add(current[0])
            target, symbol = exports[base, name]
            result |= resolve(target, symbol, seen | {(base, name)})
        return result

    edges = []
    planned_trims = []
    trim_candidates = []
    missing_imports = set()
    for path, tree in trees.items():
        current[0] = path
        module = module_name(path)
        initializer = path.endswith("/__init__.py")
        expression_strings = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr)}
        # Strings that are only compared against (`name == "qma.daemon"`,
        # `name.startswith("qma.daemon.")`) inspect imports; they load nothing.
        for n in ast.walk(tree):
            compared = []
            if isinstance(n, ast.Compare):
                compared = [n.left, *n.comparators]
            elif (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr in {"startswith", "endswith", "removeprefix", "removesuffix"}
            ):
                compared = list(n.args)
            for part in compared:
                expression_strings |= {id(c) for c in ast.walk(part) if isinstance(c, ast.Constant)}
        loaded_names = {
            n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
        }
        aliases = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    aliases[alias.asname or alias.name.split(".")[0]] = (
                        alias.name if alias.asname else alias.name.split(".")[0]
                    )
            elif isinstance(node, ast.ImportFrom):
                base = from_module(node, module, initializer)
                for alias in node.names:
                    aliases[alias.asname or alias.name] = f"{base}.{alias.name}"
        for node in ast.walk(tree):
            targets = set()
            kind = "import"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    targets |= resolve(alias.name)
                    if REFERENCE.fullmatch(alias.name) and alias.name not in modules:
                        missing_imports.add(f"{path}:{node.lineno}: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                base = from_module(node, module, initializer)
                if REFERENCE.fullmatch(base) and base not in modules:
                    missing_imports.add(f"{path}:{node.lineno}: {base}")
                for alias in node.names:
                    targets |= resolve(base, alias.name)
            elif isinstance(node, ast.Attribute):
                parts = [node.attr]
                owner = node.value
                while isinstance(owner, ast.Attribute):
                    parts.insert(0, owner.attr)
                    owner = owner.value
                if isinstance(owner, ast.Name):
                    qualified = ".".join([aliases.get(owner.id, owner.id), *parts])
                    while qualified.startswith("qma."):
                        base, _, name = qualified.rpartition(".")
                        targets |= resolve(base, name)
                        qualified = base
                kind = "attribute"
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                kind = "literal"
                # This analyzer and its synthetic graph inputs describe QMA;
                # their strings never load the runtime they are inventorying.
                if path in {"scripts/dev/qma_callers.py", "tools/tests/test_qma_callers.py"}:
                    continue
                # Include dotted strings in executable statements, not docstrings.
                if id(node) in expression_strings:
                    continue
                for match in REFERENCE.finditer(node.value):
                    target = match.group()
                    while target and target not in modules:
                        target = target.rpartition(".")[0]
                    # "qma.wire.money_path_field_diff.v1" is a schema id, not a
                    # module: allow a module plus at most one attribute name.
                    if target and match.group().count(".") - target.count(".") > 1:
                        continue
                    if target:
                        targets.add(target)
                        # A literal package can be invoked with python -m.
                        if target + ".__main__" in modules:
                            targets.add(target + ".__main__")
            if not targets:
                continue
            for target in list(targets):
                parent = target.rpartition(".")[0]
                while parent:
                    if parent in modules:
                        targets.add(parent)
                    parent = parent.rpartition(".")[0]
            for target in sorted(targets):
                if target == by_path.get(path):
                    continue
                edge = {
                    "path": path,
                    "line": node.lineno,
                    "target": target,
                    "kind": kind,
                    "category": category(path),
                    "protected": protected(path),
                }
                if (
                    trim
                    and path in by_path
                    and initializer
                    and isinstance(node, ast.ImportFrom)
                    and node in tree.body
                    and not any(
                        (alias.asname or alias.name) in loaded_names for alias in node.names
                    )
                ):
                    names = {(module, alias.asname or alias.name) for alias in node.names}
                    trim_candidates.append((edge, names))
                else:
                    edges.append(edge)
    # A re-export some caller imports from the package is not dead facade,
    # unless that caller is the package's own test or example, which retires
    # with whatever the re-export points at.
    for edge, names in trim_candidates:
        users = set().union(*(used_exports.get(n, set()) for n in names))
        live = {u for u in users if not owned_extra(u) and u not in retired}
        (edges if live else planned_trims).append(edge)
    if missing_imports:
        raise ValueError("Imports of missing QMA modules:\n" + "\n".join(sorted(missing_imports)))
    # The retained loader uses spec_from_file_location with manifest entrypoints,
    # not Python import statements. Keep these edges explicit and reproducible.
    loader = modules.get("qma.daemon.plugins.packs")
    if loader:
        loader_line = next(
            (
                n.lineno
                for n in ast.walk(trees[loader])
                if isinstance(n, ast.Attribute) and n.attr == "spec_from_file_location"
            ),
            1,
        )
        for module, path in modules.items():
            if "/bundled_packs/" in path and path.endswith("/daemon/plugin.py"):
                edges.append(
                    {
                        "path": loader,
                        "line": loader_line,
                        "target": module,
                        "kind": "manifest-loader",
                        "category": "other",
                        "protected": False,
                    }
                )
    # Documented CLI entrypoints are real invocation surfaces even without a
    # Python importer. Do not mistake their absence from the AST for dead code.
    # Only scripts and operator docs instruct anyone to run something; planning
    # notes, reviews and release evidence describe the past and are listed only.
    stale_mentions = []
    for path in sorted(
        p for p in paths if Path(p).suffix in {".md", ".ps1", ".sh", ".cmd", ".bat"}
    ):
        if ref:
            raw = git("show", f"{ref}:{path}")
        elif (ROOT / path).exists():
            raw = (ROOT / path).read_bytes()
        else:
            continue
        for line, value in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
            for match in CLI_REFERENCE.finditer(value):
                target = match.group(1)
                if target + ".__main__" in modules:
                    target += ".__main__"
                if target in modules and path.endswith(".md") and not path.startswith("docs/"):
                    stale_mentions.append(f"{path}:{line}: {target}")
                elif target in modules:
                    edges.append(
                        {
                            "path": path,
                            "line": line,
                            "target": target,
                            "kind": "documented-cli",
                            "category": category(path),
                            "protected": protected(path),
                        }
                    )
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for edge in edges:
        outgoing[edge["path"]].append(edge)
        incoming[edge["target"]].append(edge)
    reasons = {}
    for pinned in PINNED:
        # Importing a module runs its parent package initializers too.
        owner = pinned
        while owner in modules:
            reasons.setdefault(owner, ["DESIGN section 12c: preserve QMB wire schema contract"])
            owner = owner.rpartition(".")[0]
    for edge in sorted(
        edges, key=lambda e: (not e["protected"], e["category"] != "new", e["path"], e["line"])
    ):
        path = edge["path"]
        if path in by_path or path in retired:
            continue
        # A QMA package's own tests and usage examples retire with its code.
        if owned_extra(path):
            continue
        reasons.setdefault(edge["target"], [f"{path}:{edge['line']} ({edge['kind']})"])
    pending = deque(sorted(reasons))
    while pending:
        module = pending.popleft()
        for edge in outgoing[modules[module]]:
            target = edge["target"]
            if target not in reasons:
                reasons[target] = [
                    *reasons[module],
                    f"{edge['path']}:{edge['line']} ({edge['kind']})",
                ]
                pending.append(target)
    candidates = set(modules) - reasons.keys()
    neighbors = defaultdict(set)
    for edge in edges:
        source = by_path.get(edge["path"])
        target = edge["target"]
        if source in candidates and target in candidates:
            neighbors[source].add(target)
            neighbors[target].add(source)
    sets = []
    remaining = set(candidates)
    while remaining:
        component = set()
        pending = deque([min(remaining)])
        while pending:
            module = pending.popleft()
            if module in component:
                continue
            component.add(module)
            pending.extend(neighbors[module] - component)
        remaining -= component
        sets.append(
            {
                "modules": sorted(component),
                "lines": sum(len(sources[modules[m]].splitlines()) for m in component),
                # Own tests/examples and named retired callers that touch the set.
                "retiring_callers": sorted(
                    {
                        e["path"]
                        for e in edges
                        if e["target"] in component
                        and (owned_extra(e["path"]) or e["path"] in retired)
                    }
                ),
            }
        )
    sets.sort(key=lambda item: (-item["lines"], item["modules"]))
    return {
        "revision": ref or git("rev-parse", "HEAD").decode().strip() + " (tracked working tree)",
        "parsed_files": len(trees),
        "lines": {
            root.rsplit("/", 1)[-1]: sum(
                len(sources[p].splitlines())
                for p in modules.values()
                if p.startswith(root + "/src/")
            )
            for root in PACKAGES.values()
        },
        "modules": {
            m: {
                "path": p,
                "lines": len(sources[p].splitlines()),
                "external_callers": [
                    e
                    for e in incoming[m]
                    if not any(e["path"].startswith(root + "/") for root in PACKAGES.values())
                ],
                "kept_because": reasons.get(m, []),
            }
            for m, p in sorted(modules.items())
        },
        "edges": edges,
        "planned_facade_trims": planned_trims,
        "retired_callers": sorted(retired),
        "stale_doc_mentions": stale_mentions,
        "deletion_sets": sets,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", help="Git revision; default: tracked working tree")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--trim-facades", action="store_true")
    parser.add_argument("--retire-caller", action="append", default=[])
    args = parser.parse_args()
    result = inventory(args.ref, set(args.retire_caller), args.trim_facades)
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"Revision: {result['revision']}; parsed {result['parsed_files']} Python files")
    for package, lines in result["lines"].items():
        print(f"{package}: {lines} physical source lines")
    for module, info in result["modules"].items():
        print(f"\n{module} ({info['lines']} lines)")
        for group in ("new", "protected", "tests", "other"):
            callers = [e for e in info["external_callers"] if e["category"] == group]
            print(f"  {group}:")
            for edge in callers:
                label = "; protected" if edge["protected"] else ""
                print(f"    {edge['path']}:{edge['line']} ({edge['kind']}{label})")
            if not callers:
                print("    none")
        if info["kept_because"]:
            print("  retained via: " + " -> ".join(info["kept_because"]))
    print(
        "\nDeletion sets, largest first" + (" (requires facade edits)" if args.trim_facades else "")
    )
    for index, component in enumerate(result["deletion_sets"], 1):
        print(f"{index}: {component['lines']} lines; " + ", ".join(component["modules"]))
        for path in component["retiring_callers"]:
            print(f"    retires with: {path}")
    if result["stale_doc_mentions"]:
        print(f"\nHistorical doc mentions (not callers): {len(result['stale_doc_mentions'])}")


if __name__ == "__main__":
    main()
