"""Old-law names live only in their submodules, never on the top-level qml surface (AD-120)."""

from __future__ import annotations

import ast
import os
from pathlib import Path

import qml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PRUNED_DIRS = frozenset({"node_modules", "__pycache__"})

OLD_LAW_HOMES: dict[str, str] = {
    "refuse_auto_mint": "qml.conformance",
    "refuse_entry_toll_booth": "qml.conformance",
    "refuse_spawn_as_graduation": "qml.conformance",
    "refuse_gap_0085_nouns": "qml.generation",
    "refuse_generator_algorithm": "qml.generation",
    "refuse_no_code_authoring": "qml.generation",
    "refuse_qml_dsl": "qml.generation",
    "refuse_random_condition_schema": "qml.generation",
    "GAP_0063_ALGORITHM_CHOICES": "qml.generation",
    "GAP_0063_ID": "qml.generation",
    "GAP_0063_STATUS": "qml.generation",
    "GAP_0085_ID": "qml.generation",
    "GAP_0085_MECHANISM_FIELDS": "qml.generation",
    "GAP_0085_NOUNS": "qml.generation",
    "GAP_0085_STATUS": "qml.generation",
    "GAP_0085_WRITE_INCREMENT": "qml.generation",
    "GAP_0085_WRITE_OWNER": "qml.generation",
    "CONNECT_WAVE_EPICS": "qml.generation",
    "DOES_NOT_BLOCK_EPICS": "qml.generation",
    "DOOR_EPIC": "qml.generation",
    "GENERATION_EPIC": "qml.generation",
    "LIBRARY_EPIC": "qml.generation",
    "WHATIF_EPIC": "qml.generation",
}


def top_level_old_law_uses(source: str, label: str) -> list[str]:
    """Every place ``source`` reaches an old-law name through the top-level ``qml`` package."""
    tree = ast.parse(source, filename=label)
    qml_aliases = {"qml"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "qml" and alias.asname:
                    qml_aliases.add(alias.asname)
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "qml" and node.level == 0:
            hits += [
                f"{label}:{node.lineno} from qml import {alias.name}"
                for alias in node.names
                if alias.name in OLD_LAW_HOMES or alias.name == "*"
            ]
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in qml_aliases
            and node.attr in OLD_LAW_HOMES
        ):
            hits.append(f"{label}:{node.lineno} {node.value.id}.{node.attr}")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in qml_aliases
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value in OLD_LAW_HOMES
        ):
            hits.append(f"{label}:{node.lineno} getattr({node.args[0].id}, {node.args[1].value!r})")
    return hits


def scan_repo(root: Path) -> tuple[int, list[str]]:
    """Scan every ``.py`` under ``root``, skipping dot folders, and return (files read, hits)."""
    scanned = 0
    hits: list[str] = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in _PRUNED_DIRS]
        for name in files:
            if not name.endswith(".py"):
                continue
            path = Path(folder) / name
            try:
                source = path.read_text(encoding="utf-8")
                uses = (
                    top_level_old_law_uses(source, path.relative_to(root).as_posix())
                    if "qml" in source
                    else []
                )
            except (SyntaxError, UnicodeDecodeError, ValueError):
                continue
            scanned += 1
            hits += uses
    return scanned, hits


def test_no_old_law_name_is_on_the_top_level_surface() -> None:
    assert sorted(set(qml.__all__) & OLD_LAW_HOMES.keys()) == []
    assert [name for name in OLD_LAW_HOMES if hasattr(qml, name)] == []


def test_scan_catches_every_top_level_form() -> None:
    source = (
        "import qml\n"
        "import qml as q\n"
        "from qml import refuse_qml_dsl, BotDefinition\n"
        "from qml import *\n"
        "from qml.generation import GAP_0085_ID\n"
        "x = qml.DOOR_EPIC\n"
        "y = q.GAP_0063_ID\n"
        "z = getattr(qml, 'refuse_auto_mint')\n"
        "w = qml.BotDefinition\n"
    )
    assert top_level_old_law_uses(source, "probe.py") == [
        "probe.py:3 from qml import refuse_qml_dsl",
        "probe.py:4 from qml import *",
        "probe.py:6 qml.DOOR_EPIC",
        "probe.py:7 q.GAP_0063_ID",
        "probe.py:8 getattr(qml, 'refuse_auto_mint')",
    ]


def test_no_file_in_the_repo_reaches_old_law_through_top_level_qml() -> None:
    scanned, hits = scan_repo(_REPO_ROOT)
    assert scanned > 1000, f"scan read only {scanned} files under {_REPO_ROOT}"
    assert hits == []
