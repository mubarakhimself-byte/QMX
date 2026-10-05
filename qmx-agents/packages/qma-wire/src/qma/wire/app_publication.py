"""MA04 local data-only lifecycle; no deployment or invocation authority."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

from qma.core.app_candidate import validate_unicode
from qma.wire.app_candidate import invalid_input, policy_rejection
from qma.wire.list_mailbox import query_unavailable
from qmf.core import Ok, Result, is_refusal
from qmf.core.fingerprint import Fingerprint

PUBLICATION_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {"publish_app_candidate", "undo_app_publication", "get_app_publication"}
)
PUBLICATION_READS: Final[frozenset[str]] = frozenset({"get_app_publication"})
PUBLICATION_SCHEMA: Final[str] = "qma.miniapp.publication.v1"
HOST_PLUGIN_ID: Final[str] = "dev-factory"


def require_publication_capability(name: str, capabilities: object) -> Result[None]:
    if name not in PUBLICATION_CAPABILITIES:
        return invalid_input("method", "unknown local publication operation")
    if (
        isinstance(capabilities, Mapping)
        and cast(Mapping[str, object], capabilities).get(name) is True
    ):
        return Ok(None)
    if name in PUBLICATION_READS:
        return query_unavailable(name)
    return policy_rejection(
        "capabilities", "local publication requires literal-true opt-in", missing=name
    )


def parse_publication_args(name: str, args: object) -> Result[dict[str, object]]:
    if name not in PUBLICATION_CAPABILITIES or not isinstance(args, Mapping):
        return invalid_input("params", "expected a known local publication method and object")
    body = dict(cast(Mapping[str, object], args))
    unicode = validate_unicode(body, "params")
    if is_refusal(unicode):
        return unicode
    required = {"product_session_ref", "candidate_id"}
    if name not in PUBLICATION_READS:
        required |= {
            "expected_context_revision",
            "expected_active_revision",
            "expected_availability_revision",
            "validation_fp1",
        }
        required |= (
            {"revision"} if name == "publish_app_candidate" else {"target_publication_revision"}
        )
    if set(body) != required:
        return invalid_input("params", "unknown or missing local publication fields")
    for key, value in body.items():
        if key in {"expected_context_revision", "expected_availability_revision"}:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                return invalid_input(key, "expected a non-negative integer")
        elif key == "expected_active_revision" and value is None:
            continue
        elif not isinstance(value, str) or not value or len(value.encode("utf-8")) > 1024:
            return invalid_input(key, "expected a bounded non-empty string")
        if key in {
            "revision",
            "validation_fp1",
            "target_publication_revision",
            "expected_active_revision",
        }:
            fp = Fingerprint.try_create(value)
            if is_refusal(fp):
                return fp
    if not cast(str, body["product_session_ref"]).startswith("psess:") or not cast(
        str, body["candidate_id"]
    ).startswith("appcand:"):
        return invalid_input("params", "expected daemon-issued session and candidate identities")
    return Ok(body)
