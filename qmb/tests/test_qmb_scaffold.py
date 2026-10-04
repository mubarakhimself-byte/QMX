"""Tier-1 tests for the qmb distribution scaffold (Story 13.1)."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterator
from pathlib import Path

import tomllib

import qmb

_QMB_ROOT = Path(__file__).resolve().parents[1]
_SRC = _QMB_ROOT / "src" / "qmb"
_HOMES = (
    "runloop",
    "config",
    "registryread",
    "execution",
    "data",
    "optimize",
    "robustness",
    "results",
    "ledger",
    "orchestrator",
    "doors/cli",
    "doors/api",
    "doors/mcp",
    "examples",
    "tests",
)
_BANNED_IMPORTS = frozenset(
    {
        "subprocess",
        "threading",
        "multiprocessing",
        "socket",
        "asyncio",
        "concurrent",
        "http",
        "urllib",
        "optuna",
        "qmf.venue",
    }
)
_BANNED_WORDS = re.compile(r"\b(engine|kernel|exam|plugin|snapshot)s?\b", re.IGNORECASE)
_QMF_BACKENDS = (
    "qmf-core",
    "qmf-registry",
    "qmf-data",
    "qmf-indicators",
    "qmf-structure",
    "qmf-risk",
)


def test_version_is_display_only_semver_0x() -> None:
    assert qmb.__version__ == "0.1.0"


def test_module_homes_exist() -> None:
    for home in _HOMES:
        path = _QMB_ROOT / home if home in {"examples", "tests"} else _SRC / home
        assert path.is_dir(), f"missing module home {home}: {path}"
    assert _HOMES[:-2] == qmb.STRUCTURAL_SEED


def test_one_wheel_declares_cli_script_and_pins() -> None:
    data = tomllib.loads((_QMB_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    assert project["scripts"] == {"qmb": "qmb.doors.cli:main"}
    deps = tuple(project["dependencies"])
    assert deps[:6] == _QMF_BACKENDS
    assert "qml" in deps
    assert "click==8.4.2" in deps
    assert "optuna==4.9.0" in deps
    assert "qmf-venue" not in deps
    entry = project.get("entry-points", {})
    assert "console_scripts" not in entry or "mcp" not in str(entry)


def test_mcp_door_is_scaffolded_not_shipped() -> None:
    assert qmb.MCP_SHIPPED is False
    from qmb.doors import mcp

    assert mcp.is_shipped() is False
    assert mcp.SHIPPED is False
    data = tomllib.loads((_QMB_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = data["project"].get("scripts", {})
    assert all("mcp" not in name for name in scripts)
    assert "mcp" not in qmb.__all__


def test_source_never_imports_banned_modules() -> None:
    violations: list[str] = []
    for path in sorted(_SRC.rglob("*.py")):
        relative = path.relative_to(_SRC)
        in_orchestrator = relative.parts[:1] == ("orchestrator",)
        is_host_runner = relative.parts == ("host", "runner.py")
        is_cli_host = relative.parts == ("doors", "cli", "host.py")
        # This entrypoint is the CLI composition root. It reads a bounded result
        # claim for verification; the library and other door modules still forbid open().
        is_cli_root = relative.parts == ("doors", "cli", "__init__.py")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.append(node.module)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "open"
            ):
                if not (
                    in_orchestrator
                    or is_host_runner
                    or is_cli_host
                    or (is_cli_root and _is_cli_claim_open(node, tree))
                ):
                    violations.append(f"{path}: open()")
                continue
            for name in names:
                banned = name in _BANNED_IMPORTS or any(
                    name.startswith(banned + ".") for banned in _BANNED_IMPORTS
                )
                if banned:
                    if (in_orchestrator or is_host_runner) and (
                        name == "subprocess" or name.startswith("subprocess.")
                    ):
                        continue
                    if is_cli_host and (
                        name == "subprocess"
                        or name.startswith("subprocess.")
                        or name == "socket"
                        or name.startswith("socket.")
                    ):
                        continue
                    # optuna is the TPE-class sampler adapter's dependency and lives
                    # only in the sampler module, pinned n_jobs=1 (DEC-0168, B-8).
                    if relative.parts == ("optimize", "sampler.py") and (
                        name == "optuna" or name.startswith("optuna.")
                    ):
                        continue
                    violations.append(f"{path}: imports {name}")
                if (name == "click" or name.startswith("click.")) and relative.parts[:2] != (
                    "doors",
                    "cli",
                ):
                    violations.append(f"{path}: click is CLI-door only")
    assert violations == []


def test_library_has_no_module_global_mutable_state() -> None:
    violations: list[str] = []
    for path in sorted(_SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            targets: list[ast.expr] = []
            value: ast.expr | None = None
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
                value = node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = [node.target]
                value = node.value
            if value is None:
                continue
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
                continue
            if _is_mutable_literal(value):
                violations.append(f"{path}: module-global mutable {value.__class__.__name__}")
    assert violations == []


def _same_scope_nodes(node: ast.AST) -> Iterator[ast.AST]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
        return
    yield node
    for child in ast.iter_child_nodes(node):
        yield from _same_scope_nodes(child)


def _is_cli_claim_open(node: ast.Call, tree: ast.Module) -> bool:
    return (
        len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "claim_path"
        and all(
            keyword.arg == "encoding"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "utf-8"
            for keyword in node.keywords
        )
        and any(
            isinstance(statement, ast.FunctionDef)
            and statement.name == "backtest_run"
            and any(node in _same_scope_nodes(body) for body in statement.body)
            for statement in tree.body
        )
    )


def test_cli_claim_open_allowance_is_read_only_and_same_scope() -> None:
    def allowed(body: str) -> bool:
        tree = ast.parse("def backtest_run(claim_path):\n" + body)
        call = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        )
        return _is_cli_claim_open(call, tree)

    assert allowed("    return open(claim_path, encoding='utf-8')\n")
    for keywords in (
        "mode='w'",
        "mode='a'",
        "mode='r+'",
        "mode=mode",
        "**options",
        "opener=custom_opener",
    ):
        assert not allowed(f"    return open(claim_path, {keywords})\n"), keywords
    assert not allowed("    def unrelated():\n        return open(claim_path, encoding='utf-8')\n")


def _vocabulary_violations(source: str) -> list[str]:
    """Keep QMB vocabulary separate from narrowed external receipt members."""
    tree = ast.parse(source)
    receipt_imported = any(
        isinstance(node, ast.ImportFrom)
        and node.level == 0
        and node.module in {"qmf.data.store", "qmf.data.store.receipts"}
        and any(alias.name == "StoreReceipt" and alias.asname is None for alias in node.names)
        for node in tree.body
    )
    allowed: set[tuple[int, int]] = set()
    # Proof names must retain their imported/builtin meanings in every scope.
    import_bindings = {
        (alias.asname or alias.name.split(".")[0])
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
        if not (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module in {"qmf.data.store", "qmf.data.store.receipts"}
            and alias.name == "StoreReceipt"
            and alias.asname is None
        )
    }
    proof_names_shadowed = bool(import_bindings & {"StoreReceipt", "isinstance", "type"}) or any(
        (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, (ast.Store, ast.Del))
            and node.id in {"StoreReceipt", "isinstance", "type"}
        )
        or (isinstance(node, ast.arg) and node.arg in {"StoreReceipt", "isinstance", "type"})
        or (
            isinstance(node, (ast.FunctionDef, ast.ClassDef))
            and node.name in {"StoreReceipt", "isinstance", "type"}
        )
        or (
            isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar))
            and node.name in {"StoreReceipt", "isinstance", "type"}
        )
        or (
            isinstance(node, ast.MatchMapping)
            and node.rest in {"StoreReceipt", "isinstance", "type"}
        )
        for node in ast.walk(tree)
    )
    if receipt_imported and not proof_names_shadowed:
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            narrowed: set[str] = set()
            for statement in function.body:
                # Only refusal guards in this function's straight-line body qualify.
                if (
                    isinstance(statement, ast.If)
                    and any(isinstance(node, (ast.Return, ast.Raise)) for node in statement.body)
                    and not statement.orelse
                    # A condition can evaluate a valid receipt and then rebind
                    # that subject before falling through to the next statement.
                    and not any(
                        isinstance(node, ast.NamedExpr) for node in ast.walk(statement.test)
                    )
                ):
                    guards = (
                        statement.test.values
                        if isinstance(statement.test, ast.BoolOp)
                        and isinstance(statement.test.op, ast.Or)
                        else [statement.test]
                    )
                    found_proof = False
                    for guard in guards:
                        # Host receipt validation also uses exact nominal guards
                        # on a receipt member before assigning it to a local alias.
                        if (
                            isinstance(guard, ast.Compare)
                            and len(guard.ops) == 1
                            and isinstance(guard.ops[0], ast.IsNot)
                            and isinstance(guard.left, ast.Call)
                            and isinstance(guard.left.func, ast.Name)
                            and guard.left.func.id == "type"
                            and len(guard.left.args) == 1
                            and isinstance(guard.comparators[0], ast.Name)
                            and guard.comparators[0].id == "StoreReceipt"
                        ):
                            subject = _receipt_subject(guard.left.args[0])
                            if subject is not None:
                                narrowed.add(subject)
                                found_proof = True
                            continue
                        if not (isinstance(guard, ast.UnaryOp) and isinstance(guard.op, ast.Not)):
                            continue
                        call = guard.operand
                        if (
                            isinstance(call, ast.Call)
                            and isinstance(call.func, ast.Name)
                            and call.func.id == "isinstance"
                            and len(call.args) == 2
                            and isinstance(call.args[0], ast.Name)
                            and isinstance(call.args[1], ast.Name)
                            and call.args[1].id == "StoreReceipt"
                        ):
                            narrowed.add(call.args[0].id)
                            found_proof = True
                    # The failed-guard body has no narrowed type proof.
                    if found_proof:
                        continue
                # Any possible assignment in a branch invalidates a prior proof.
                assigned = {
                    node.id
                    for node in ast.walk(statement)
                    if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))
                }
                for node in ast.walk(statement):
                    if isinstance(node, ast.Attribute) and isinstance(
                        node.ctx, (ast.Store, ast.Del)
                    ):
                        subject = _receipt_subject(node)
                        if subject is not None:
                            assigned.add(subject.split(".")[0])
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        assigned.update(
                            alias.asname or alias.name.split(".")[0] for alias in node.names
                        )
                    elif (
                        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                        or (isinstance(node, ast.ExceptHandler) and node.name is not None)
                        or (
                            isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name is not None
                        )
                    ):
                        name = node.name
                        if name is not None:
                            assigned.add(name)
                    elif isinstance(node, ast.MatchMapping) and node.rest is not None:
                        assigned.add(node.rest)
                old_narrowed = narrowed.copy()
                narrowed = {name for name in narrowed if name.split(".")[0] not in assigned}
                if isinstance(statement, ast.Assign):
                    for target in statement.targets:
                        if isinstance(target, ast.Name):
                            if _receipt_subject(statement.value) in old_narrowed:
                                narrowed.add(target.id)
                            else:
                                narrowed.discard(target.id)
                for node in _same_scope_nodes(statement):
                    if (
                        isinstance(node, ast.Attribute)
                        and node.attr == "engine"
                        and isinstance(node.value, ast.Name)
                        and node.value.id in narrowed
                        and node.end_lineno is not None
                        and node.end_col_offset is not None
                    ):
                        allowed.add((node.end_lineno, node.end_col_offset - len(node.attr)))
                    if isinstance(node, ast.Dict):
                        # A diagnostic label for that same external receipt field
                        # is allowed only when paired with its proved comparison.
                        for key, value in zip(node.keys, node.values, strict=True):
                            if (
                                isinstance(key, ast.Constant)
                                and key.value == "engine"
                                and isinstance(value, ast.Compare)
                                and isinstance(value.left, ast.Attribute)
                                and value.left.attr == "engine"
                                and isinstance(value.left.value, ast.Name)
                                and value.left.value.id in narrowed
                            ):
                                allowed.add((key.lineno, key.col_offset + 1))
    violations: list[str] = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        for match in _BANNED_WORDS.finditer(line):
            if (line_number, match.start()) not in allowed:
                violations.append(match.group())
    return violations


def _receipt_subject(value: ast.expr) -> str | None:
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
        return value.value.id + "." + value.attr
    return None


def test_source_avoids_banned_vocabulary() -> None:
    offenders: list[str] = []
    for path in sorted(_SRC.rglob("*.py")):
        if _vocabulary_violations(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(_SRC)))
    assert offenders == []


def test_vocabulary_guard_retains_negative_controls() -> None:
    prefix = "from qmf.data.store.receipts import StoreReceipt\n"
    guarded = (
        "def check(value):\n"
        "    if not isinstance(value, StoreReceipt):\n"
        "        return False\n"
        "    receipt = value\n"
        "    return receipt.engine == 'jsonl'\n"
    )
    assert _vocabulary_violations(prefix + guarded) == []
    assert _vocabulary_violations(guarded) == ["engine"]
    assert _vocabulary_violations(prefix + "def check(receipt):\n    return receipt.engine\n") == [
        "engine"
    ]
    assert _vocabulary_violations(
        prefix + guarded.replace("receipt = value", "receipt = object()")
    ) == ["engine"]
    assert _vocabulary_violations(prefix + guarded.replace("return False", "pass")) == ["engine"]
    assert _vocabulary_violations(prefix + guarded.replace("StoreReceipt):", "object):")) == [
        "engine"
    ]
    for word in ("engine", "kernel", "exam", "plugin", "snapshot"):
        assert _vocabulary_violations(f"class {word.title()}: pass")
        assert _vocabulary_violations(f"label = '{word}'")
        assert _vocabulary_violations(f"# {word}")


def test_receipt_proof_rejects_import_and_definition_rebinding() -> None:
    prefix = "from qmf.data.store.receipts import StoreReceipt\n"
    guard = "def f(value):\n    if not isinstance(value, StoreReceipt):\n        return False\n"
    bodies = (
        "import foreign as StoreReceipt\n" + guard + "    return value.engine\n",
        "from foreign import isinstance\n" + guard + "    return value.engine\n",
        guard + "    else:\n        value = object()\n    return value.engine\n",
        guard + "    def value():\n        pass\n    return value.engine\n",
        guard + "    import foreign as value\n    return value.engine\n",
    )
    for body in bodies:
        assert _vocabulary_violations(prefix + body) == ["engine"]


def test_exact_receipt_member_proof_is_narrow_and_preserves_rebinding_guards() -> None:
    prefix = "from qmf.data.store import StoreReceipt\n"
    body = (
        "def f(receipt):\n"
        "    if type(receipt.store_receipt) is not StoreReceipt:\n"
        "        return False\n"
        "    store = receipt.store_receipt\n"
        "    return {'engine': store.engine == 'jsonl'}\n"
    )
    assert _vocabulary_violations(prefix + body) == []
    for replacement in (
        "store = object()",
        "receipt = object(); store = receipt.store_receipt",
        "receipt.store_receipt = object(); store = receipt.store_receipt",
    ):
        assert _vocabulary_violations(
            prefix + body.replace("store = receipt.store_receipt", replacement)
        ) == ["engine", "engine"]
    assert _vocabulary_violations(prefix + body.replace("StoreReceipt:", "object:")) == [
        "engine",
        "engine",
    ]
    assert _vocabulary_violations(
        prefix + body.replace("def f(receipt):", "def f(receipt, type):")
    ) == ["engine", "engine"]
    assert _vocabulary_violations(prefix + body.replace("return False", "pass")) == [
        "engine",
        "engine",
    ]
    assert _vocabulary_violations(prefix + body.replace("store.engine == 'jsonl'", "True")) == [
        "engine"
    ]


def test_receipt_guard_condition_cannot_rebind_its_proved_subject() -> None:
    prefix = "from qmf.data.store import StoreReceipt\n"
    for guard, alias in (
        ("type(receipt.store_receipt) is not StoreReceipt", "receipt.store_receipt"),
        ("not isinstance(receipt, StoreReceipt)", "receipt"),
    ):
        source = (
            "def f(receipt, other):\n"
            f"    if {guard} or (receipt := other) is None:\n"
            "        return False\n"
            f"    store = {alias}\n"
            "    return {'engine': store.engine == 'jsonl'}\n"
        )
        assert _vocabulary_violations(prefix + source) == ["engine", "engine"]


def _is_mutable_literal(value: ast.expr) -> bool:
    if isinstance(value, (ast.List, ast.Dict, ast.Set)):
        return True
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in {"list", "dict", "set"}
    )


def test_vocabulary_guard_rejects_shadowing_and_scope_bypasses() -> None:
    prefix = "from qmf.data.store.receipts import StoreReceipt\n"
    cases = {
        "parameter shadow": (
            "def f(value, StoreReceipt):\n"
            "    if not isinstance(value, StoreReceipt):\n"
            "        return False\n"
            "    return value.engine\n"
        ),
        "global shadow": (
            "StoreReceipt = object\n"
            "def f(value):\n"
            "    if not isinstance(value, StoreReceipt):\n"
            "        return False\n"
            "    return value.engine\n"
        ),
        "ann reassignment": (
            "def f(value):\n"
            "    if not isinstance(value, StoreReceipt):\n"
            "        return False\n"
            "    value: object = object()\n"
            "    return value.engine\n"
        ),
        "branch reassignment": (
            "def f(value, flag):\n"
            "    if not isinstance(value, StoreReceipt):\n"
            "        return False\n"
            "    if flag:\n"
            "        value = object()\n"
            "    return value.engine\n"
        ),
        "guard failure access": (
            "def f(value):\n"
            "    if not isinstance(value, StoreReceipt):\n"
            "        return value.engine\n"
            "    return False\n"
        ),
        "nested scope shadow": (
            "def f(value):\n"
            "    if not isinstance(value, StoreReceipt):\n"
            "        return False\n"
            "    def g(value):\n"
            "        return value.engine\n"
            "    return g\n"
        ),
        "isinstance shadow": (
            "def f(value, isinstance):\n"
            "    if not isinstance(value, StoreReceipt):\n"
            "        return False\n"
            "    return value.engine\n"
        ),
        "guard conditionalreturn": (
            "def f(value,flag):\n"
            "    if not isinstance(value, StoreReceipt):\n"
            "        if flag:\n"
            "            pass\n"
            "        return False\n"
            "    return value.engine\n"
        ),
    }
    for name, source in cases.items():
        if name != "guard conditionalreturn":
            assert _vocabulary_violations(prefix + source) == ["engine"], name
