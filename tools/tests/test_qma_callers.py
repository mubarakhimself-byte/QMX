"""The deletion inventory must fail closed around external and dynamic callers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "qma_callers", Path(__file__).resolve().parents[2] / "scripts/dev/qma_callers.py"
)
assert _SPEC is not None and _SPEC.loader is not None
callers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(callers)

CORE = "qmx-agents/packages/qma-core/src/qma/core/"


def scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, str],
    *,
    trim: bool = False,
    retired: set[str] | None = None,
) -> dict[str, Any]:
    for path, source in files.items():
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8")

    def git(*args: str) -> bytes:
        if args[0] == "ls-files":
            return "\0".join(files).encode()
        assert args == ("rev-parse", "HEAD")
        return b"fixture"

    monkeypatch.setattr(callers, "ROOT", tmp_path)
    monkeypatch.setattr(callers, "git", git)
    return callers.inventory(None, retired or set(), trim)


def test_cycle_retires_together_but_external_import_keeps_transitive_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = {
        CORE + "alpha.py": "from .beta import value\n",
        CORE + "beta.py": "from .alpha import value\nvalue = 1\n",
        "qmx-agents/packages/qma-core/tests/test_old.py": "import qma.core.alpha\n",
    }
    result = scan(tmp_path, monkeypatch, files)
    assert result["deletion_sets"] == [
        {
            "modules": ["qma.core.alpha", "qma.core.beta"],
            "lines": 3,
            "retiring_callers": ["qmx-agents/packages/qma-core/tests/test_old.py"],
        }
    ]
    files["qmn/src/consumer.py"] = "def run():\n    from qma.core.alpha import value\n"
    result = scan(tmp_path, monkeypatch, files)
    assert result["deletion_sets"] == []
    assert result["modules"]["qma.core.beta"]["kept_because"][0].startswith("qmn/src/consumer.py:2")


@pytest.mark.parametrize(
    "consumer",
    [
        "from qma.core import Public\n",
        "import qma.core as legacy\nlegacy.Public()\n",
        "from qma.core import *\n",
    ],
)
def test_named_aliased_and_star_reexports_survive_facade_planning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, consumer: str
) -> None:
    result = scan(
        tmp_path,
        monkeypatch,
        {
            CORE + "__init__.py": "from .alpha import Public\nfrom .unused import Old\n",
            CORE + "alpha.py": "class Public: pass\n",
            CORE + "unused.py": "class Old: pass\n",
            "qmx-agents/packages/qmx-agents/src/qmx_agents/consumer.py": consumer,
        },
        trim=True,
    )
    assert result["modules"]["qma.core.alpha"]["kept_because"]
    if "*" in consumer:
        assert result["deletion_sets"] == []
    else:
        assert result["deletion_sets"] == [
            {"modules": ["qma.core.unused"], "lines": 1, "retiring_callers": []}
        ]


def test_literal_cli_and_manifest_loader_keep_entrypoints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    daemon = "qmx-agents/packages/qma-daemon/src/qma/daemon/"
    result = scan(
        tmp_path,
        monkeypatch,
        {
            daemon + "__init__.py": "",
            daemon + "__main__.py": "from qma.daemon.plugins.packs import load\n",
            daemon + "plugins/packs.py": (
                "def load():\n    importlib.util.spec_from_file_location('pack', path)\n"
            ),
            daemon + "bundled_packs/demo/daemon/plugin.py": "def activate(): pass\n",
            "qmb/src/host.py": "SPAWN = 'qma.daemon'\n",
        },
        trim=True,
    )
    assert result["deletion_sets"] == []
    assert any(edge["kind"] == "manifest-loader" for edge in result["edges"])


def test_protected_tests_cannot_be_retired_and_unrelated_parse_errors_are_fatal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = {CORE + "alpha.py": "", "qmb/tests/test_old.py": "import qma.core.alpha\n"}
    with pytest.raises(ValueError, match="protected"):
        scan(tmp_path, monkeypatch, files, retired={"qmb/tests/test_old.py"})
    files["unrelated.py"] = "def broken("
    with pytest.raises(SyntaxError):
        scan(tmp_path, monkeypatch, files)


def test_external_categories_and_sizes_are_reported_without_untracked_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "untracked.py").write_text("invalid python!!", encoding="utf-8")
    files = {CORE + "alpha.py": "# comment\n\nvalue = 1\n"}
    for path in (
        "qmx-agents/packages/qmx-control/src/qmx_control/api.py",
        "qmb/src/door.py",
        "qmn/tests/test_door.py",
        "tools/probe.py",
    ):
        files[path] = "import qma.core.alpha\n"
    result = scan(tmp_path, monkeypatch, files)
    assert result["parsed_files"] == 5
    assert result["lines"]["qma-core"] == 3
    assert {
        edge["category"] for edge in result["modules"]["qma.core.alpha"]["external_callers"]
    } == {"new", "protected", "tests", "other"}


def test_missing_import_cannot_disappear_from_after_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match="Imports of missing QMA modules"):
        scan(
            tmp_path,
            monkeypatch,
            {CORE + "__init__.py": "", "qmb/src/door.py": "import qma.core.deleted\n"},
        )


def test_facade_plan_keeps_imports_used_by_initializer_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = scan(
        tmp_path,
        monkeypatch,
        {
            CORE + "__init__.py": "from .alpha import register\nregister()\n",
            CORE + "alpha.py": "def register(): pass\n",
            "qmb/src/door.py": "import qma.core\n",
        },
        trim=True,
    )
    assert result["deletion_sets"] == []


def test_ids_comparisons_and_history_notes_are_not_callers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    daemon = "qmx-agents/packages/qma-daemon/src/qma/daemon/"
    files = {
        daemon + "__init__.py": "",
        daemon + "__main__.py": "",
        CORE + "__init__.py": "",
        CORE + "checker.py": "def hit(name):\n    return name == 'qma.daemon'\n",
        "qmb/src/variants.py": (
            "SCHEMA = 'qma.daemon.field_diff.v1'\nID = 'qma.daemon.panel-x.v1'\n"
        ),
        "rebuild/notes.md": "Run `python -m qma.daemon` to start.\n",
        "qmx-agents/packages/qma-daemon/examples/demo.py": "import qma.daemon\n",
    }
    result = scan(tmp_path, monkeypatch, files)
    assert {m for s in result["deletion_sets"] for m in s["modules"]} == {
        "qma.core",
        "qma.core.checker",
        "qma.daemon",
        "qma.daemon.__main__",
    }
    assert result["stale_doc_mentions"] == ["rebuild/notes.md:1: qma.daemon.__main__"]
    files["docs/run.md"] = "Run `python -m qma.daemon` to start.\n"
    result = scan(tmp_path, monkeypatch, files)
    assert result["modules"]["qma.daemon.__main__"]["kept_because"][0].startswith("docs/run.md:1")


def test_pinned_schema_keeps_parent_initializer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wire = "qmx-agents/packages/qma-wire/src/qma/wire/"
    result = scan(
        tmp_path,
        monkeypatch,
        {
            wire + "__init__.py": "from .old import X\n",
            wire + "old.py": "X = 1\n",
            wire + "schemas.py": "",
        },
    )
    assert result["modules"]["qma.wire"]["kept_because"]
    assert result["modules"]["qma.wire.old"]["kept_because"]


def test_facade_plan_never_trims_a_reexport_a_caller_uses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = scan(
        tmp_path,
        monkeypatch,
        {
            CORE + "__init__.py": "from .alpha import Public\nfrom .unused import Old\n",
            CORE + "alpha.py": "class Public: pass\n",
            CORE + "unused.py": "class Old: pass\n",
            "qmb/src/door.py": "from qma.core import Public\n",
        },
        trim=True,
    )
    trimmed = {(edge["path"], edge["line"]) for edge in result["planned_facade_trims"]}
    assert trimmed == {(CORE + "__init__.py", 2)}


def test_facade_plan_ignores_reexports_only_the_package_tests_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = scan(
        tmp_path,
        monkeypatch,
        {
            CORE + "__init__.py": "from .old import Old\n",
            CORE + "old.py": "class Old: pass\n",
            "qmx-agents/packages/qma-core/tests/test_old.py": "from qma.core import Old\n",
            "qmb/src/door.py": "import qma.core\n",
        },
        trim=True,
    )
    assert result["deletion_sets"] == [
        {
            "modules": ["qma.core.old"],
            "lines": 1,
            "retiring_callers": ["qmx-agents/packages/qma-core/tests/test_old.py"],
        }
    ]
