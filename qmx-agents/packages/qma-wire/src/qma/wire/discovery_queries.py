"""MA-01 bounded discovery arguments over existing CT-40 query admission.

Capabilities are server-owned. This mounted slice serves live contributions;
other federated classes and instance health remain explicitly unavailable.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

from qma.wire.federated_discovery import FEDERATED_HIT_CLASSES, parse_federated_hit
from qma.wire.list_mailbox import query_unavailable
from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal

DISCOVERY_READ_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {"list_installed_plugins", "facade_search", "facade_get"}
)
DISCOVERY_SERVER_OWNED_KEYS: Final[frozenset[str]] = DISCOVERY_READ_CAPABILITIES | {
    "get_instance_health",
    "discovery_hit_classes",
    "invoke_contribution_pin",
}
DISCOVERY_SCHEMA: Final[str] = "qma.wire.discovery_read.v1"


def _invalid(field: str, reason: str) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context={"field": field, "reason": reason},
    )


def require_discovery_capability(name: str, capabilities: object) -> Result[None]:
    """No client echo or declared-only route may authorize a query."""
    if (
        isinstance(capabilities, Mapping)
        and cast("Mapping[object, object]", capabilities).get(name) is True
    ):
        return Ok(None)
    return query_unavailable(name)


def parse_discovery_args(name: str, value: object) -> Result[Mapping[str, object]]:
    """Closed request fields. References retain their existing DTO grammar."""
    if not isinstance(value, Mapping):
        return _invalid("params", "expected discovery argument object")
    raw = cast("Mapping[object, object]", value)
    if any(not isinstance(key, str) for key in raw):
        return _invalid("params", "discovery argument keys must be strings")
    args = dict(cast("Mapping[str, object]", value))
    allowed = {"product_session_ref"}
    if name == "facade_search":
        allowed |= {"query", "hit_class"}
    elif name == "facade_get":
        allowed |= {"hit"}
    elif name != "list_installed_plugins":
        return query_unavailable(name)
    if set(args) - allowed:
        return _invalid("params", "unknown discovery argument fields")
    if "product_session_ref" in args:
        ref = args["product_session_ref"]
        if not isinstance(ref, str) or not ref.startswith("psess:") or ref == "psess:":
            return _invalid("product_session_ref", "expected nonempty psess: reference")
    if name == "facade_search":
        query = args.get("query")
        if not isinstance(query, str) or not query.strip():
            return _invalid("query", "expected nonempty literal query")
        args["query"] = query.strip()
        hit_class = args.get("hit_class", "contribution")
        if not isinstance(hit_class, str) or hit_class not in FEDERATED_HIT_CLASSES:
            return _invalid("hit_class", "expected existing federated hit class")
        args["hit_class"] = hit_class
    elif name == "facade_get":
        hit = parse_federated_hit(args.get("hit"))
        if is_refusal(hit):
            return hit
        args["hit"] = dict(hit.value.to_payload())
    return Ok(args)
