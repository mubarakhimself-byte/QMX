"""The engine's import rules (E15, AD-1, AD-3, AD-6), read from the source tree with `ast`.

AD-6 bans every clock in core and definition, `monotonic` and `perf_counter` too (L-20), and the
rules see through an alias, `importlib` and `__import__`, and the `uuid4`, `urandom` and `secrets`
entropy sources (L-22).

Each rule returns its offenders as `(file, name)` pairs, the file relative to the source root, so a
failure names the file to open.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import qma.harness

SRC = Path(__file__).resolve().parents[1] / "src"
HARNESS_PUBLIC = frozenset(qma.harness.__all__)
MONEY_PATH = "qma.core.barriers.money_path"
REFUSED = ("qma.daemon", "qmx_agents", "qma_wire", "claude_agent_sdk")
REFUSED_PREFIXES = ("langchain", "langgraph")
PURE = ("qmx_engine.core", "qmx_engine.definition")
IMPURE_IMPORTS = (
    "qmx_engine.ports",
    "qmx_engine.nodes",
    "qmx_engine.workers",
    "qmx_engine.ledger",
    "sqlite3",
    "subprocess",
    "httpx",
)
PURE_FROM_LEDGER = ("qmx_engine.ledger.redact",)
"""The one redaction function (AD-37) is pure text work; the definition lint shares its shapes."""
CLOCK_ENTROPY_ENVIRONMENT = (
    "time.time",
    "time.time_ns",
    "time.monotonic",
    "time.monotonic_ns",
    "time.perf_counter",
    "time.perf_counter_ns",
    "uuid.uuid1",
    "uuid.uuid4",
    "os.urandom",
    "secrets",
    "importlib",
    "__import__",
    "datetime.now",
    "datetime.utcnow",
    "datetime.today",
    "date.today",
    "random",
    "os.environ",
    "os.getenv",
)


class Source(NamedTuple):
    file: str
    package: str
    tree: ast.Module


Modules = dict[str, Source]
Offenders = list[tuple[str, str]]


def modules(src: Path = SRC) -> Modules:
    found: Modules = {}
    for path in sorted((src / "qmx_engine").rglob("*.py")):
        parts = path.relative_to(src).with_suffix("").parts
        package = ".".join(parts[:-1])
        name = package if parts[-1] == "__init__" else ".".join(parts)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        found[name] = Source(path.relative_to(src).as_posix(), package, tree)
    return found


def within(name: str, roots: tuple[str, ...]) -> bool:
    return any(name == root or name.startswith(f"{root}.") for root in roots)


def targets(source: Source) -> set[str]:
    """Every name an import statement binds, as a full dotted path, relative imports resolved."""
    names: set[str] = set()
    for node in ast.walk(source.tree):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            parts = source.package.split(".")
            base = parts[: len(parts) - node.level + 1] if node.level else []
            origin = ".".join([*base, *([node.module] if node.module else [])])
            names |= {
                origin if alias.name == "*" else f"{origin}.{alias.name}" for alias in node.names
            }
    return names


def dotted(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        head = dotted(node.value)
        return None if head is None else f"{head}.{node.attr}"
    return None


def aliases(source: Source) -> dict[str, str]:
    """Each name an import binds under another name, to the full dotted path it stands for."""
    found: dict[str, str] = {}
    for node in ast.walk(source.tree):
        if isinstance(node, ast.Import):
            found |= {a.asname: a.name for a in node.names if a.asname}
        elif isinstance(node, ast.ImportFrom) and node.module:
            found |= {a.asname: f"{node.module}.{a.name}" for a in node.names if a.asname}
    return found


def references(source: Source) -> set[str]:
    """Import targets plus every `a.b.c` attribute chain and bare name the module mentions, an
    aliased head read as the path it stands for."""
    named = aliases(source)
    resolved: set[str] = set()
    for node in ast.walk(source.tree):
        chain = dotted(node) if isinstance(node, ast.Attribute | ast.Name) else None
        if chain is None:
            continue
        head, _, rest = chain.partition(".")
        resolved.add(f"{named[head]}.{rest}".rstrip(".") if head in named else chain)
    return targets(source) | resolved


def reads_clock_entropy_or_environment(name: str) -> bool:
    return any(
        name == banned or name.endswith(f".{banned}") or name.startswith(f"{banned}.")
        for banned in CLOCK_ENTROPY_ENVIRONMENT
    )


def offenders(
    found: Modules, judge: Callable[[str, str], bool], names: Callable[[Source], set[str]]
) -> Offenders:
    return sorted(
        (source.file, name)
        for module, source in found.items()
        for name in names(source)
        if judge(module, name)
    )


def harness_submodule_imports(found: Modules) -> Offenders:
    return offenders(
        found,
        lambda _, name: (
            within(name, ("qma.harness",))
            and name != "qma.harness"
            and name.removeprefix("qma.harness.") not in HARNESS_PUBLIC
        ),
        targets,
    )


def core_imports_other_than_money_path(found: Modules) -> Offenders:
    return offenders(
        found,
        lambda _, name: within(name, ("qma.core",)) and not within(name, (MONEY_PATH,)),
        targets,
    )


def refused_imports(found: Modules) -> Offenders:
    return offenders(
        found,
        lambda _, name: within(name, REFUSED) or name.startswith(REFUSED_PREFIXES),
        targets,
    )


def impure_imports_in_pure_layers(found: Modules) -> Offenders:
    return offenders(
        found,
        lambda module, name: (
            within(module, PURE)
            and within(name, IMPURE_IMPORTS)
            and not within(name, PURE_FROM_LEDGER)
        ),
        targets,
    )


def clock_entropy_or_environment_in_pure_layers(found: Modules) -> Offenders:
    return offenders(
        found,
        lambda module, name: within(module, PURE) and reads_clock_entropy_or_environment(name),
        references,
    )


def builds_test_mode(found: Modules) -> list[str]:
    return sorted(
        source.file
        for source in found.values()
        if any(
            isinstance(node, ast.Call) and (dotted(node.func) or "").split(".")[-1] == "TestMode"
            for node in ast.walk(source.tree)
        )
    )


def plant(root: Path, files: dict[str, str]) -> Modules:
    for relative, text in files.items():
        path = root / "qmx_engine" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return modules(root)


def test_the_engine_source_breaks_no_rule() -> None:
    found = modules()
    assert "qmx_engine.core" in found
    assert {
        "harness submodules": harness_submodule_imports(found),
        "qma.core": core_imports_other_than_money_path(found),
        "refused": refused_imports(found),
        "impure imports in core and definition": impure_imports_in_pure_layers(found),
        "clock, entropy or environment in core and definition": (
            clock_entropy_or_environment_in_pure_layers(found)
        ),
        "TestMode": builds_test_mode(found),
    } == {
        "harness submodules": [],
        "qma.core": [],
        "refused": [],
        "impure imports in core and definition": [],
        "clock, entropy or environment in core and definition": [],
        "TestMode": [],
    }


def test_a_harness_submodule_import_fails_and_public_names_pass(tmp_path: Path) -> None:
    found = plant(
        tmp_path,
        {
            "ports/harness_adapter.py": (
                "from qma.harness import Background, ChatHooks, Child, Harness, NewChat\n"
                "from qma.harness.launch import Background as B\n"
            ),
            "nodes/agent.py": (
                "import qma.harness.chat\nimport qma.harness\nfrom qma import harness\n"
            ),
            "service/api.py": "from qma.harness import home\n",
        },
    )

    assert harness_submodule_imports(found) == [
        ("qmx_engine/nodes/agent.py", "qma.harness.chat"),
        ("qmx_engine/ports/harness_adapter.py", "qma.harness.launch.Background"),
        ("qmx_engine/service/api.py", "qma.harness.home"),
    ]


def test_qma_core_is_allowed_only_as_the_money_path_deny_list(tmp_path: Path) -> None:
    found = plant(
        tmp_path,
        {
            "definition/validate.py": (
                "from qma.core.barriers.money_path import MONEY_PATH_VERBS\n"
                "from qma.core.barriers import money_path\n"
                "import qma.core.barriers.money_path\n"
            ),
            "nodes/script.py": "from qma.core import barriers\nimport qma.core.models\n",
        },
    )

    assert core_imports_other_than_money_path(found) == [
        ("qmx_engine/nodes/script.py", "qma.core.barriers"),
        ("qmx_engine/nodes/script.py", "qma.core.models"),
    ]


def test_daemon_agents_wire_langchain_langgraph_and_the_sdk_are_refused(tmp_path: Path) -> None:
    found = plant(
        tmp_path,
        {
            "nodes/llm.py": (
                "import qma.daemon.store\nfrom qmx_agents import runtime\nimport qma_wire\n"
                "from langchain_core import messages\nimport langgraph.graph\n"
                "from claude_agent_sdk import query\nimport qma.dashboard\n"
            ),
        },
    )

    assert refused_imports(found) == [
        ("qmx_engine/nodes/llm.py", "claude_agent_sdk.query"),
        ("qmx_engine/nodes/llm.py", "langchain_core.messages"),
        ("qmx_engine/nodes/llm.py", "langgraph.graph"),
        ("qmx_engine/nodes/llm.py", "qma.daemon.store"),
        ("qmx_engine/nodes/llm.py", "qma_wire"),
        ("qmx_engine/nodes/llm.py", "qmx_agents.runtime"),
    ]


def test_core_and_definition_import_no_adapter_store_or_process(tmp_path: Path) -> None:
    found = plant(
        tmp_path,
        {
            "core/__init__.py": "",
            "core/replay.py": "from ..ledger import store\nfrom qmx_engine.ports import Clock\n",
            "definition/load.py": "import sqlite3\nfrom subprocess import run\nimport httpx\n",
            "core/ready.py": (
                "from qmx_engine.nodes import registry\nfrom qmx_engine import workers\n"
            ),
            "service/api.py": "import sqlite3\nfrom qmx_engine.ports import Clock\n",
        },
    )

    assert impure_imports_in_pure_layers(found) == [
        ("qmx_engine/core/ready.py", "qmx_engine.nodes.registry"),
        ("qmx_engine/core/ready.py", "qmx_engine.workers"),
        ("qmx_engine/core/replay.py", "qmx_engine.ledger.store"),
        ("qmx_engine/core/replay.py", "qmx_engine.ports.Clock"),
        ("qmx_engine/definition/load.py", "httpx"),
        ("qmx_engine/definition/load.py", "sqlite3"),
        ("qmx_engine/definition/load.py", "subprocess.run"),
    ]


def test_core_and_definition_read_no_clock_randomness_or_environment(tmp_path: Path) -> None:
    found = plant(
        tmp_path,
        {
            "core/tick.py": (
                "import time\nimport datetime\nstarted = time.time()\n"
                "today = datetime.datetime.now()\ntime.monotonic()\n"
            ),
            "definition/seed.py": "import random\nimport os\nhome = os.environ['HOME']\n",
            "nodes/script.py": "import time\nimport os\ntime.time()\nos.environ.get('X')\n",
        },
    )

    assert clock_entropy_or_environment_in_pure_layers(found) == [
        ("qmx_engine/core/tick.py", "datetime.datetime.now"),
        ("qmx_engine/core/tick.py", "time.monotonic"),
        ("qmx_engine/core/tick.py", "time.time"),
        ("qmx_engine/definition/seed.py", "os.environ"),
        ("qmx_engine/definition/seed.py", "random"),
    ]


def test_test_mode_is_built_nowhere_in_the_source(tmp_path: Path) -> None:
    found = plant(
        tmp_path,
        {
            "settings.py": "from qma.harness import TestMode\nPROBE = TestMode(gpt=None)\n",
            "service/tests.py": "import qma.harness\nqma.harness.TestMode()\n",
            "nodes/agent.py": "from qma.harness import TestMode\n",
        },
    )

    assert builds_test_mode(found) == ["qmx_engine/service/tests.py", "qmx_engine/settings.py"]


def test_l20_l22_an_alias_importlib_and_every_entropy_source_are_caught(tmp_path: Path) -> None:
    found = plant(
        tmp_path,
        {
            "core/hidden.py": (
                "import time as t\nimport importlib\nfrom os import urandom as u\n"
                "import uuid\nt.perf_counter()\nuuid.uuid4()\n__import__('random')\n"
            ),
            "definition/ids.py": "import secrets\nsecrets.token_hex(4)\n",
        },
    )

    assert clock_entropy_or_environment_in_pure_layers(found) == [
        ("qmx_engine/core/hidden.py", "__import__"),
        ("qmx_engine/core/hidden.py", "importlib"),
        ("qmx_engine/core/hidden.py", "os.urandom"),
        ("qmx_engine/core/hidden.py", "time.perf_counter"),
        ("qmx_engine/core/hidden.py", "uuid.uuid4"),
        ("qmx_engine/definition/ids.py", "secrets"),
        ("qmx_engine/definition/ids.py", "secrets.token_hex"),
    ]
