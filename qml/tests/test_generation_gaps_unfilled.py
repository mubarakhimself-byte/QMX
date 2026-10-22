"""Story 38.3 — GAP-0085 nouns and GAP-0063 algorithm stay unfilled."""

from __future__ import annotations

import ast
import os
import stat
from pathlib import Path
from typing import TypeVar, cast

import pytest
import yaml
from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import RefusalCategory, Result, is_ok, is_refusal
from qml.declaration import LEG_ROLES, LegRole
from qml.footprint import ProducerBinding
from qml.generation import (
    CHEAP_VETO_A1,
    CONNECT_WAVE_EPICS,
    DEFAULT_GENERATOR_ALGORITHM,
    DOES_NOT_BLOCK_EPICS,
    DOES_NOT_BLOCK_SURFACES,
    DOOR_EPIC,
    GAP_0063_ALGORITHM_CHOICES,
    GAP_0063_RECORD,
    GAP_0063_STATUS,
    GAP_0085_ID,
    GAP_0085_NOUNS,
    GAP_0085_RECORD,
    GAP_0085_STATUS,
    GAP_0085_WRITE_INCREMENT,
    GAP_0085_WRITE_OWNER,
    GENERATION_EPIC,
    GENERATOR_ALGORITHM_UNRULED,
    HOST_MINTS_MECHANISM_VOCABULARY,
    LIBRARY_EPIC,
    LOGIC_PATH,
    LOGIC_PATH_RUNG,
    LOGIC_PATH_STORY,
    MECHANISM_VOCABULARY_MINTED,
    TRAILS_CONNECT_WAVE,
    WHATIF_EPIC,
    admit_decided_generator_algorithm,
    author_new_structure,
    blocks_library_whatif_or_door,
    mint_mechanism_vocabulary,
    minted_mechanism_type_hits,
    prose_fills_gap_0063,
    refuse_gap_0085_nouns,
    refuse_generator_algorithm,
    refuse_no_code_authoring,
    trails_connect_wave,
    write_ownership_is_qml_host,
)

T = TypeVar("T")

_REPO = Path(__file__).resolve().parents[2]
_QML_SRC = _REPO / "qml" / "src" / "qml"
_QML_EXAMPLES = _REPO / "qml" / "examples"
_QMB_SRC = _REPO / "qmb" / "src" / "qmb"
_AGENT_PACKAGES = _REPO / "qmx-agents" / "packages"
_CONTRACTS = _REPO / "docs" / "contracts"
_SKIP_DIR_NAMES = {".git", "__pycache__", ".venv"}
_MAX_READ_BYTES = 1 << 20  # 1 MiB


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _pinned(tag: str) -> ProducerBinding:
    fp = _ok(fingerprint({"class": "test-producer", "tag": tag}))
    return _ok(ProducerBinding.try_create(fp))


def _iter_py(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in _SKIP_DIR_NAMES for part in path.parts):
            continue
        paths.append(path)
    return paths


def _read_contained(
    path: Path,
    *,
    contain_within: Path,
    max_bytes: int = _MAX_READ_BYTES,
) -> str:
    """Read UTF-8 text from a regular, in-root, non-symlink file under *max_bytes*."""
    try:
        resolved = Path(os.path.realpath(path))
        root_real = Path(os.path.realpath(contain_within))
    except OSError as exc:
        raise OSError(
            f"could not resolve a contained filesystem path ({path}): {type(exc).__name__}"
        ) from exc
    if path.is_symlink() or not resolved.is_relative_to(root_real):
        raise OSError(f"refusing to follow a symlink or read outside the intended root ({path})")
    if not path.is_file() or path.is_symlink():
        raise OSError(f"refusing to read a path that is not a regular in-root file ({path})")
    try:
        # getattr keeps the "O_NOFOLLOW" token on this open so SKY-D324/D325
        # see the no-follow flag; Windows has no O_NOFOLLOW (value 0).
        fd = os.open(  # skylos: ignore[SKY-D215] contained, no-follow read
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0),
        )
    except OSError as exc:
        raise OSError(f"contained no-follow open failed for {path} ({type(exc).__name__})") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(f"refusing to read a path that is not a regular in-root file ({path})")
        size = info.st_size
        if size > max_bytes:
            raise OSError(
                f"refusing to read a file above the size cap ({path}: {size} > {max_bytes})"
            )
        limit = max_bytes if size <= 0 else min(size, max_bytes)
        buf = bytearray()
        while len(buf) < limit:
            chunk = os.read(fd, limit - len(buf))
            if not chunk:
                break
            buf.extend(chunk)
        if size <= 0 and len(buf) >= max_bytes:
            extra = os.read(fd, 1)
            if extra:
                raise OSError(f"refusing to read a file above the size cap ({path}: > {max_bytes})")
    finally:
        os.close(fd)
    try:
        return bytes(buf).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OSError(f"contained file is not UTF-8 text ({path})") from exc


def _class_names(path: Path) -> list[str]:
    tree = ast.parse(_read_contained(path, contain_within=_QML_SRC), filename=str(path))
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]


def test_gap_0085_vocabulary_is_not_minted() -> None:
    assert MECHANISM_VOCABULARY_MINTED is False
    assert HOST_MINTS_MECHANISM_VOCABULARY is False
    assert GAP_0085_RECORD["gap"] == GAP_0085_ID
    assert GAP_0085_RECORD["status"] == GAP_0085_STATUS
    assert GAP_0085_RECORD["minted"] is False
    assert write_ownership_is_qml_host() is True
    assert GAP_0085_WRITE_OWNER == "qml-host"
    assert GAP_0085_WRITE_INCREMENT == "later"
    minted = mint_mechanism_vocabulary()
    assert is_refusal(minted)
    assert minted.category is RefusalCategory.POLICY_REJECTION
    assert minted.context["gap"] == "GAP-0085"
    assert minted.context["gap_status"] == "deferred"
    assert minted.context["minted"] is False
    assert minted.context["write_owner"] == "qml-host"
    assert minted.context["later_increment"] is True
    for noun in sorted(GAP_0085_NOUNS):
        refused = refuse_gap_0085_nouns(noun)
        assert is_refusal(refused)
        assert refused.context["gap"] == "GAP-0085"
        assert refused.context["minted"] is False


def test_epic_source_does_not_define_gap_0085_types() -> None:
    names: list[str] = []
    for path in _iter_py(_QML_SRC):
        names.extend(_class_names(path))
    hits = _ok(minted_mechanism_type_hits(names))
    assert hits == ()
    assert _ok(minted_mechanism_type_hits(("BotDefinition", "Confluence", "LegRole"))) == ()
    assert _ok(minted_mechanism_type_hits(("EntryMechanism", "HardConstraintFilter"))) == (
        "EntryMechanism",
    )


def test_ct34_filter_role_is_not_the_gap_0085_filter_noun() -> None:
    assert frozenset({"level", "trigger", "confirmation", "filter"}) == LEG_ROLES
    assert LegRole.FILTER.value == "filter"
    authored = _ok(
        author_new_structure(
            confluence_legs=[{"role": "filter", "producer_binding": _pinned("zone")}],
        )
    )
    assert authored.confluence is not None
    assert authored.confluence.legs[0].role is LegRole.FILTER
    nested = author_new_structure(
        confluence_legs=[
            {
                "role": "level",
                "producer_binding": _pinned("zone"),
                "EntryMechanism": {"kind": "breakout"},
            }
        ],
    )
    assert is_refusal(nested)
    assert nested.context["field"] == "mechanisms"
    assert nested.context["gap"] == "GAP-0085"


def _reject_duplicate_keys(node: yaml.Node) -> None:
    if isinstance(node, yaml.MappingNode):
        keys: set[str] = set()
        for key, value in node.value:
            assert isinstance(key, yaml.ScalarNode) and key.tag == "tag:yaml.org,2002:str"
            assert key.value not in keys, f"duplicate YAML key: {key.value}"
            keys.add(key.value)
            _reject_duplicate_keys(value)
    elif isinstance(node, yaml.SequenceNode):
        for value in node.value:
            _reject_duplicate_keys(value)


def _assert_approved_contract_schema(
    text: str, kind: str, fields: set[str], enum_headers: set[str] | None = None
) -> None:
    """Check schema declarations; governance denials are not new typed fields."""
    # PyYAML's compose stub omits its Node return type; narrow that one boundary.
    document_node = cast(
        "yaml.Node | None",
        yaml.compose(text, Loader=yaml.SafeLoader),  # pyright: ignore[reportUnknownMemberType]
    )
    assert document_node is not None
    _reject_duplicate_keys(document_node)
    document: object = yaml.safe_load(text)
    assert isinstance(document, dict)
    schema: object = cast("dict[str, object]", document)["schema"]
    assert isinstance(schema, dict)
    schema = cast("dict[str, object]", schema)
    assert set(schema) == {"type", "fields", "enums", "units", "nullability"}
    assert schema["type"] == kind
    headers: dict[str, set[str]] = {}
    for key in ("fields", "enums"):
        declarations = schema[key]
        assert isinstance(declarations, list)
        entries = cast("list[object]", declarations)
        parsed: list[str] = []
        for declaration in entries:
            assert isinstance(declaration, str) and ":" in declaration
            parsed.append(declaration.split(":", 1)[0])
        assert len(parsed) == len(set(parsed))
        headers[key] = set(parsed)
    assert headers["fields"] == fields
    assert headers["enums"] == (set() if enum_headers is None else enum_headers)
    if kind == "confluence" and enum_headers:
        enums = cast("list[str]", schema["enums"])
        roles = next(value for value in enums if value.startswith("leg role:"))
        assert roles.split(":", 1)[1].split("—", 1)[0].strip() == (
            "level | trigger | confirmation | filter"
        )


def test_ct33_ct34_contracts_do_not_mint_mechanism_nouns() -> None:
    _assert_approved_contract_schema(
        _read_contained(_CONTRACTS / "ct-33-bot-definition.yaml", contain_within=_CONTRACTS),
        "bot-definition",
        {
            "contract_format_version",
            "bot_definition_fingerprint",
            "strategy_family_id",
            "confluence_set",
            "parameter_space",
            "canonical_assignment",
            "footprint.stream_set",
            "footprint.required_calendars",
            "footprint.producer_bindings",
            "footprint.warm_up_horizon",
            "permitted_exit_intents",
            "logic_reference",
            "version_graph",
        },
        {
            "parameter type",
            "unit-kind (per parameter)",
            "producer binding form",
            "permitted exit-intent kinds (a subset, possibly empty)",
            "ui flag (per declared configurable variable)",
            "refusal categories on this contract's Layer-1 registration paths, per registry",
        },
    )
    _assert_approved_contract_schema(
        _read_contained(_CONTRACTS / "ct-34-confluence.yaml", contain_within=_CONTRACTS),
        "confluence",
        {
            "contract_format_version",
            "confluence_fingerprint",
            "legs",
            "leg.role",
            "leg.producer_binding",
            "leg.declared_parameters",
            "leg.confluence_ref",
            "display_ordinal",
            "order_significance",
        },
        {
            "leg role",
            "producer binding form",
            "ordering",
            "refusal categories on this contract's paths, per registry",
        },
    )
    assert set(LEG_ROLES) == {"level", "trigger", "confirmation", "filter"}


@pytest.mark.parametrize("noun", sorted(GAP_0085_NOUNS))
def test_contract_schema_detector_rejects_minted_mechanism(noun: str) -> None:
    text = (
        "constraints: ['No typed mechanism nouns Entry/Exit/Filter/Session']\n"
        '\nschema:\n  type: confluence\n  fields:\n    - "legs: existing"\n'
        "  enums: []\n  units: []\n  nullability:\nprovenance_note: unchanged\n"
    )
    _assert_approved_contract_schema(text, "confluence", {"legs"})
    with pytest.raises(AssertionError):
        _assert_approved_contract_schema(
            text.replace("  enums:", f'    - "{noun}: typed mechanism"\n  enums:'),
            "confluence",
            {"legs"},
        )
    with pytest.raises(AssertionError):
        _assert_approved_contract_schema(
            text.replace("type: confluence", f"type: {noun}"), "confluence", {"legs"}
        )
    with pytest.raises(AssertionError):
        _assert_approved_contract_schema(
            text.replace("  enums: []", f"  {noun}: typed mechanism\n  enums: []"),
            "confluence",
            {"legs"},
        )
    with pytest.raises(AssertionError):
        _assert_approved_contract_schema(
            text.replace("  enums: []", f'  enums:\n    - "{noun}: typed mechanism"'),
            "confluence",
            {"legs"},
        )
    with pytest.raises(AssertionError):
        _assert_approved_contract_schema(
            text.replace("type: confluence", f"type: confluence\n  type: {noun}"),
            "confluence",
            {"legs"},
        )


def test_decided_default_algorithm_is_refused_as_unruled() -> None:
    assert DEFAULT_GENERATOR_ALGORITHM is None
    assert GENERATOR_ALGORITHM_UNRULED is True
    assert GAP_0063_RECORD["status"] == GAP_0063_STATUS
    assert GAP_0063_RECORD["default"] is None
    unnamed = admit_decided_generator_algorithm()
    assert is_refusal(unnamed)
    assert unnamed.category is RefusalCategory.UNSUPPORTED_CAPABILITY
    assert unnamed.context["gap"] == "GAP-0063"
    assert unnamed.context["gap_status"] == "unruled"
    assert unnamed.context["unruled"] is True
    assert unnamed.context["as_default"] is True
    assert unnamed.context["chosen"] is None
    for choice in sorted(GAP_0063_ALGORITHM_CHOICES):
        refused = admit_decided_generator_algorithm(choice)
        assert is_refusal(refused)
        assert refused.context["as_default"] is True
        assert refused.context["named_choice"] is True
        authored = author_new_structure(
            confluence_legs=[{"role": "level", "producer_binding": _pinned("zone")}],
            algorithm=choice,
        )
        assert is_refusal(authored)
        assert authored.context["field"] == "algorithm"
        assert authored.context["gap"] == "GAP-0063"


def test_no_prose_in_this_epic_fills_gap_0063() -> None:
    roots = (
        _QML_SRC / "generation",
        _QML_SRC / "host",
        _QML_EXAMPLES,
    )
    fills: list[str] = []
    for root in roots:
        paths = [root] if root.is_file() else list(root.rglob("*"))
        for path in paths:
            if not path.is_file() or path.suffix not in {".py", ".md"}:
                continue
            if any(part in _SKIP_DIR_NAMES for part in path.parts):
                continue
            text = _read_contained(path, contain_within=root)
            if _ok(prose_fills_gap_0063(text)):
                fills.append(str(path))
    assert fills == []
    assert _ok(prose_fills_gap_0063("the algorithm is unruled GAP-0063")) is False
    assert (
        _ok(
            prose_fills_gap_0063(
                "the first generator algorithm (placeholder-fill of CT-34 legs vs "
                "Python-logic synthesis) is unruled GAP-0063 and is not filled here"
            )
        )
        is False
    )
    assert _ok(prose_fills_gap_0063("the first algorithm is placeholder-fill")) is True
    assert _ok(prose_fills_gap_0063('DEFAULT_GENERATOR_ALGORITHM = "placeholder-fill"')) is True
    idle = refuse_generator_algorithm()
    assert is_ok(idle)


def test_generation_trails_connect_wave_and_does_not_block() -> None:
    assert TRAILS_CONNECT_WAVE is True
    assert CHEAP_VETO_A1 == "NFR-W06 A1"
    assert CONNECT_WAVE_EPICS == (32, 33, 34, 35, 36, 37)
    assert GENERATION_EPIC == 38
    assert max(CONNECT_WAVE_EPICS) < GENERATION_EPIC
    assert trails_connect_wave() is True
    assert LIBRARY_EPIC == 34
    assert WHATIF_EPIC == 35
    assert DOOR_EPIC == 36
    assert DOES_NOT_BLOCK_EPICS == (34, 35, 36)
    assert DOES_NOT_BLOCK_SURFACES == ("library", "what-if", "door")
    assert set(DOES_NOT_BLOCK_EPICS).issubset(set(CONNECT_WAVE_EPICS))
    assert blocks_library_whatif_or_door() is False


def test_library_whatif_and_door_do_not_import_qml_generation() -> None:
    surfaces = (
        (_QMB_SRC / "registryread" / "library.py", _QMB_SRC),
        (_QMB_SRC / "analysis", _QMB_SRC),
        (_QMB_SRC / "doors", _QMB_SRC),
        (_AGENT_PACKAGES, _AGENT_PACKAGES),
    )
    hits: list[str] = []
    for surface, contain_within in surfaces:
        paths = [surface] if surface.is_file() else _iter_py(surface)
        assert paths, f"{surface} has no Python to read"
        for path in paths:
            text = _read_contained(path, contain_within=contain_within)
            if "qml.generation" in text or "from qml.generation" in text:
                hits.append(str(path))
    assert hits == []


def test_no_code_authoring_is_refused_ordinary_python_remains_logic_path() -> None:
    assert LOGIC_PATH == "ordinary_python"
    assert LOGIC_PATH_RUNG == 2
    assert LOGIC_PATH_STORY == "32.3"
    refused = refuse_no_code_authoring(True)
    assert is_refusal(refused)
    assert refused.context["field"] == "no_code"
    assert refused.context["logic_path"] == "ordinary_python"
    assert refused.context["logic_rung"] == 2
    assert refused.context["logic_path_story"] == "32.3"
    authored = author_new_structure(no_code=True)
    assert is_refusal(authored)
    assert authored.context["field"] == "no_code"
    assert authored.context["logic_path"] == LOGIC_PATH
