"""MA03 adapter for the documented flat panel model; no renderer."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Final, cast

from qma.core.app_candidate import validate_unicode
from qma.wire.app_candidate import invalid_input, policy_rejection
from qma.wire.schemas import load_schema, validate_instance
from qmf.core import Ok, Result, is_refusal

VALIDATION_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {"get_app_ui_catalog", "validate_app_candidate", "get_app_candidate_validation"}
)
VALIDATION_READS: Final[frozenset[str]] = VALIDATION_CAPABILITIES - {"validate_app_candidate"}
COMPOSITION_SCHEMA: Final[str] = "qma.miniapp.composition.v1"
CATALOG_SCHEMA: Final[str] = "qma.miniapp.catalog.v1"
VALIDATOR_ID: Final[str] = "qma.daemon.panel-composition.v1"
RESULT_SCHEMA: Final[str] = "qma.miniapp.validation.v1"
COMPONENTS: Final[tuple[str, ...]] = (
    "Stack",
    "Grid",
    "Heading",
    "Text",
    "Metric",
    "Table",
    "LineChart",
    "Badge",
    "Callout",
    "Button",
)
# Safety ceilings only; no production selections and no demo defaults.
LIMIT_CEILINGS: Final[dict[str, int]] = {
    "max_bytes": 65536,
    "max_panels": 128,
    "max_elements": 1024,
    "max_depth": 32,
    "max_json_depth": 32,
    "max_nodes": 8192,
    "max_array_items": 1024,
    "max_string_bytes": 16384,
    "max_errors": 64,
}


@dataclass(frozen=True)
class ValidationLimits:
    max_bytes: int
    max_panels: int
    max_elements: int
    max_depth: int
    max_json_depth: int
    max_nodes: int
    max_array_items: int
    max_string_bytes: int
    max_errors: int

    def to_payload(self) -> dict[str, int]:
        return asdict(self)

    @classmethod
    def parse(cls, value: object) -> Result[ValidationLimits]:
        if not isinstance(value, Mapping) or set(cast(Mapping[object, object], value)) != set(
            LIMIT_CEILINGS
        ):
            return invalid_input("miniapp_validation_limits", "provide every named host limit")
        body = cast(Mapping[str, object], value)
        for key, ceiling in LIMIT_CEILINGS.items():
            item = body[key]
            if isinstance(item, bool) or not isinstance(item, int) or not 1 <= item <= ceiling:
                return invalid_input(
                    key, "limit must be an integer within safety ceiling", ceiling=ceiling
                )
        return Ok(cls(**cast(dict[str, int], dict(body))))


def data_bytes(value: object) -> bytes:
    """Stable finite-JSON data bytes; fp1 byte identity permits values like chart floats."""
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def error(path: str, code: str, message: str, remediation: str) -> dict[str, object]:
    return {"path": path, "code": code, "message": message, "remediation": remediation}


def budget(value: object, limits: ValidationLimits) -> list[dict[str, object]]:
    """Iterative before schema recursion/canonicalization; bounds work including cycles."""
    pending: list[tuple[object, int, str, frozenset[int]]] = [(value, 0, "$", frozenset())]
    nodes = 0
    while pending:
        item, depth, path, ancestors = pending.pop()
        nodes += 1
        if nodes > limits.max_nodes or depth > limits.max_json_depth:
            return [
                error(path, "LIMIT", "JSON depth or node limit exceeded", "Reduce nesting or data")
            ]
        if isinstance(item, str):
            try:
                length = len(item.encode("utf-8"))
            except UnicodeEncodeError:
                return [error(path, "UNICODE", "Lone Unicode surrogate", "Use valid UTF-8 text")]
            if length > limits.max_string_bytes:
                return [error(path, "LIMIT", "String byte limit exceeded", "Shorten the string")]
        elif isinstance(item, (dict, list)):
            if id(cast(object, item)) in ancestors:
                return [error(path, "CYCLE", "Cyclic JSON container", "Remove the cycle")]
            nested = ancestors | {id(cast(object, item))}
            if isinstance(item, dict):
                mapped = cast(dict[object, object], item)
                if len(mapped) > limits.max_nodes:
                    return [error(path, "LIMIT", "Object count exceeds node limit", "Reduce keys")]
                if any(not isinstance(k, str) for k in mapped):
                    return [
                        error(
                            path, "TYPE", "Too many or non-string keys", "Use bounded string keys"
                        )
                    ]
                for key, child in mapped.items():
                    pending.append((key, depth + 1, path, nested))
                    pending.append(
                        (
                            child,
                            depth + 1,
                            path + "/" + str(key).replace("~", "~0").replace("/", "~1"),
                            nested,
                        )
                    )
            else:
                sequence = cast(list[object], item)
                if len(sequence) > limits.max_array_items:
                    return [
                        error(path, "LIMIT", "Array item limit exceeded", "Reduce array length")
                    ]
                pending.extend(
                    (child, depth + 1, path + "/" + str(i), nested)
                    for i, child in enumerate(sequence)
                )
        elif item is not None and not isinstance(item, (bool, int, float)):
            return [error(path, "TYPE", "Value outside finite JSON", "Use JSON data only")]
        elif isinstance(item, float) and not math.isfinite(item):
            return [error(path, "TYPE", "Nonfinite number", "Use a finite number")]
    if len(data_bytes(value)) > limits.max_bytes:
        return [error("$", "LIMIT", "Composition byte limit exceeded", "Reduce bytes")]
    return []


def validate_structure(value: object, limits: ValidationLimits) -> list[dict[str, object]]:
    problems = budget(value, limits)
    if problems:
        return problems
    checked = validate_instance(value, "miniapp_composition")
    if is_refusal(checked):
        return [
            error(
                str(checked.context.get("path", "$")),
                "UNSUPPORTED_COMPONENT"
                if ".type:" in str(checked.context.get("reason"))
                else "SCHEMA",
                str(checked.context.get("reason")),
                "Match the served composition schema",
            )
        ]
    body = cast(dict[str, object], value)
    panels = cast(list[dict[str, object]], body["panels"])
    bindings = cast(dict[str, object], body["bindings"])
    if not panels or len(panels) > limits.max_panels:
        return [
            error(
                "$/panels",
                "LIMIT",
                "Panel count outside host bounds",
                "Use a nonempty bounded panel list",
            )
        ]
    total = 0
    for i, panel in enumerate(panels):
        path = f"$/panels/{i}"
        elements = cast(dict[str, dict[str, object]], panel["elements"])
        total += len(elements)
        if total > limits.max_elements:
            return [
                error(
                    path + "/elements", "LIMIT", "Total element limit exceeded", "Reduce elements"
                )
            ]
        if not cast(str, panel["title"]).strip():
            problems.append(error(path + "/title", "TYPE", "Title is blank", "Provide a title"))
        if "data" not in panel or panel["data"] not in bindings:
            problems.append(
                error(
                    path + "/data",
                    "REFERENCE",
                    "Data must name a binding",
                    "Use a binding key, never URL or code",
                )
            )
        for ident in (*elements, *bindings):
            if (
                not ident
                or not (ident[0].isalpha() or ident[0] == "_")
                or any(not (c.isalnum() or c in "_.-") for c in ident)
            ):
                problems.append(
                    error(
                        path,
                        "IDENTIFIER",
                        "Element/binding names must be simple identifiers",
                        "Use letters, digits, underscore, dot or dash",
                    )
                )
        if "size" in panel:
            size = cast(dict[str, int], panel["size"])
            if any(value > limits.max_array_items for value in size.values()):
                problems.append(
                    error(path + "/size", "LIMIT", "Size exceeds host bound", "Reduce dimensions")
                )
        parents: dict[str, int] = dict.fromkeys(elements, 0)
        for ident, element in sorted(elements.items()):
            ep = path + "/elements/" + ident
            component = cast(str, element["type"])
            props = cast(dict[str, object], element.get("props", {}))
            prop_check = validate_instance(props, "miniapp_props_" + component)
            if is_refusal(prop_check):
                problems.append(
                    error(
                        ep + "/props" + str(prop_check.context.get("path", "$"))[1:],
                        "COMPONENT_PROPS",
                        str(prop_check.context.get("reason")),
                        "Use the served prop schema",
                    )
                )
            children = cast(list[str], element.get("children", []))
            if children and component not in {"Stack", "Grid"}:
                problems.append(
                    error(
                        ep + "/children", "TYPE", "Leaf cannot hold children", "Use Stack or Grid"
                    )
                )
            for child in children:
                if child not in elements:
                    problems.append(
                        error(
                            ep + "/children", "REFERENCE", "Child undeclared", "Declare the child"
                        )
                    )
                else:
                    parents[child] += 1
            if component == "Button" and (
                not isinstance(props.get("action"), str)
                or props.get("action") not in bindings
                or props.get("action") != panel.get("data")
            ):
                problems.append(
                    error(
                        ep + "/props/action",
                        "REFERENCE",
                        "Action must name a read binding",
                        "Use a declared binding key",
                    )
                )
            if component == "Grid":
                minimum = props.get("min")
                columns = props.get("columns")
                # Optional dimensions stay absent; renderer fallback is not a requirement.
                if (
                    "min" in props
                    and (
                        not isinstance(minimum, (int, float))
                        or isinstance(minimum, bool)
                        or not 0 < minimum <= limits.max_array_items
                    )
                ) or (
                    "columns" in props
                    and (
                        not isinstance(columns, int)
                        or isinstance(columns, bool)
                        or not 0 < columns <= limits.max_array_items
                    )
                ):
                    problems.append(
                        error(
                            ep + "/props",
                            "LIMIT",
                            "Grid dimensions outside bounds",
                            "Use positive bounded dimensions",
                        )
                    )
            if (
                component == "Table"
                and isinstance(props.get("columns"), list)
                and isinstance(props.get("rows"), list)
            ):
                columns = cast(list[object], props["columns"])
                rows = cast(list[object], props["rows"])
                if not columns or any(
                    not isinstance(row, list) or len(cast(list[object], row)) != len(columns)
                    for row in rows
                ):
                    problems.append(
                        error(
                            ep + "/props/rows",
                            "TYPE",
                            "Rows must match nonempty columns",
                            "Use rectangular rows; empty rows is valid",
                        )
                    )
        root = cast(str, panel["root"])
        seen: set[str] = set()
        pending: list[tuple[str, int, frozenset[str]]] = [(root, 1, frozenset())]
        while pending:
            ident, depth, ancestors = pending.pop()
            if ident in ancestors:
                problems.append(
                    error(path + "/elements/" + ident, "CYCLE", "Element cycle", "Remove the cycle")
                )
                continue
            if ident in seen or ident not in elements:
                continue
            seen.add(ident)
            if depth > limits.max_depth:
                problems.append(
                    error(
                        path + "/elements/" + ident,
                        "LIMIT",
                        "Element depth exceeds bound",
                        "Flatten the tree",
                    )
                )
            pending.extend(
                (child, depth + 1, ancestors | {ident})
                for child in cast(list[str], elements[ident].get("children", []))
            )
        if (
            root not in elements
            or seen != set(elements)
            or parents.get(root) != 0
            or any(count != 1 for ident, count in parents.items() if ident != root)
        ):
            problems.append(
                error(
                    path + "/elements",
                    "TOPOLOGY",
                    "Require one reachable tree and one parent per child",
                    "Remove orphan, duplicate or shared children",
                )
            )
    return problems[: limits.max_errors]


def catalog_definition() -> dict[str, object]:
    return {
        "schema": CATALOG_SCHEMA,
        "version": 1,
        "composition_schema": load_schema("miniapp_composition"),
        "components": {
            name: {
                "props_schema": load_schema("miniapp_props_" + name),
                "children": name in {"Stack", "Grid"},
            }
            for name in COMPONENTS
        },
        "renderer": "json-render",
        "slots": ["app-nav", "canvas-widget", "detail", "copilot-panel", "preview-tab"],
        "read_state_schema": load_schema("miniapp_read_state"),
        "data_contract": {
            "schema": "qma.miniapp.read-state.v1",
            "states": ["ready", "empty", "stale", "unavailable", "failed"],
            "authority": "existing operation owner",
            "validation_executes_reads": False,
        },
    }


def parse_validation_args(name: str, args: object) -> Result[dict[str, object]]:
    if not isinstance(args, dict):
        return invalid_input("params", "expected an object")
    body = cast(dict[str, object], args)
    checked = validate_unicode(body, "params")
    if is_refusal(checked):
        return checked
    required = {"product_session_ref"}
    if name != "get_app_ui_catalog":
        required |= {"candidate_id", "revision"}
    if name == "validate_app_candidate":
        required |= {"expected_context_revision", "catalog_fp1"}
    elif name == "get_app_candidate_validation":
        required |= {"validation_fp1"}
    elif name != "get_app_ui_catalog":
        return invalid_input("name", "unknown MA03 method")
    if set(body) != required:
        return invalid_input("params", "unknown or missing MA03 fields")
    for key in required - {"expected_context_revision"}:
        if (
            not isinstance(body[key], str)
            or not cast(str, body[key]).strip()
            or body[key] != cast(str, body[key]).strip()
        ):
            return invalid_input(key, "expected an exact nonempty token")
    if "expected_context_revision" in body:
        revision = body["expected_context_revision"]
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            return invalid_input("expected_context_revision", "expected a nonnegative integer")
    schema_name = {
        "get_app_ui_catalog": "app_ui_catalog_args",
        "validate_app_candidate": "app_candidate_validate_args",
        "get_app_candidate_validation": "app_candidate_validation_args",
    }[name]
    checked_args = validate_instance(body, schema_name)
    if is_refusal(checked_args):
        return checked_args
    return Ok(dict(body))


def require_validation_capability(name: str, capabilities: object) -> Result[None]:
    if (
        isinstance(capabilities, Mapping)
        and cast(Mapping[str, object], capabilities).get(name) is True
    ):
        return Ok(None)
    return policy_rejection("capabilities", "MA03 capability not negotiated", missing=name)
