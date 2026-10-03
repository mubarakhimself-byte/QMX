"""Optional authenticated CT-40 agent-request commands and status query.

Clients select a host-installed profile, never provider/model/grants/instructions.
Each method has its own server-owned negotiated capability. These DTOs carry no
principal: the authenticated connection and bound session supply that authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, cast

from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection

SUBMIT_AGENT_REQUEST_CAPABILITY: Final[str] = "submit_agent_request"
GET_AGENT_REQUEST_CAPABILITY: Final[str] = "get_agent_request"
CANCEL_AGENT_REQUEST_CAPABILITY: Final[str] = "cancel_agent_request"
AGENT_REQUEST_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {
        SUBMIT_AGENT_REQUEST_CAPABILITY,
        GET_AGENT_REQUEST_CAPABILITY,
        CANCEL_AGENT_REQUEST_CAPABILITY,
    }
)


@dataclass(frozen=True, slots=True)
class SubmitAgentRequest:
    product_session_ref: str
    profile_id: str
    prompt: str
    idempotency_key: str

    def to_payload(self) -> dict[str, object]:
        return {
            "product_session_ref": self.product_session_ref,
            "profile_id": self.profile_id,
            "prompt": self.prompt,
            "idempotency_key": self.idempotency_key,
        }


@dataclass(frozen=True, slots=True)
class AgentRequestReference:
    request_id: str
    product_session_ref: str

    def to_payload(self) -> dict[str, object]:
        return {"request_id": self.request_id, "product_session_ref": self.product_session_ref}


def require_agent_request_capability(capabilities: object, method: str) -> Result[None]:
    if method not in AGENT_REQUEST_CAPABILITIES:
        return invalid_input("method", "not an agent-request method")
    if (
        not isinstance(capabilities, Mapping)
        or cast("Mapping[str, object]", capabilities).get(method) is not True
    ):
        return policy_rejection(
            "capabilities", "agent-request method is not enabled by this host", missing=method
        )
    return Ok(None)


def _body(value: object, expected: frozenset[str]) -> Result[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return invalid_input("params", "agent-request params must be an object")
    raw = cast("Mapping[object, object]", value)
    if any(not isinstance(key, str) for key in raw):
        return invalid_input("params", "agent-request keys must be strings")
    body = cast("Mapping[str, object]", value)
    if frozenset(body) != expected:
        return invalid_input(
            "params", "exact agent-request fields are required", expected=sorted(expected)
        )
    return Ok(body)


def _bounded_text(value: object, limit: int) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        return len(value.encode("utf-8")) <= limit
    except UnicodeError:
        return False


def _identity(body: Mapping[str, object], name: str, *, prefix: str = "") -> Result[str]:
    value = body[name]
    if not _bounded_text(value, 512):
        return invalid_input(name, "nonempty bounded text identity is required")
    value = cast("str", value).strip()
    if prefix and not value.startswith(prefix):
        return invalid_input(name, "identity has an invalid namespace")
    return Ok(value)


def parse_submit_agent_request(value: object) -> Result[SubmitAgentRequest]:
    body = _body(
        value, frozenset({"product_session_ref", "profile_id", "prompt", "idempotency_key"})
    )
    if is_refusal(body):
        return body
    session = _identity(body.value, "product_session_ref", prefix="psess:")
    profile = _identity(body.value, "profile_id")
    key = _identity(body.value, "idempotency_key")
    for parsed in (session, profile, key):
        if is_refusal(parsed):
            return parsed
    prompt = body.value["prompt"]
    if not _bounded_text(prompt, 16_384):
        return invalid_input("prompt", "nonempty UTF-8 prompt of at most 16384 bytes is required")
    if is_refusal(session) or is_refusal(profile) or is_refusal(key):
        return invalid_input("params", "invalid agent-request identity")
    return Ok(SubmitAgentRequest(session.value, profile.value, cast("str", prompt), key.value))


def _reference(value: object) -> Result[AgentRequestReference]:
    body = _body(value, frozenset({"product_session_ref", "request_id"}))
    if is_refusal(body):
        return body
    session = _identity(body.value, "product_session_ref", prefix="psess:")
    request = _identity(body.value, "request_id", prefix="req:")
    if is_refusal(session):
        return session
    if is_refusal(request):
        return request
    return Ok(AgentRequestReference(request.value, session.value))


def parse_get_agent_request(value: object) -> Result[AgentRequestReference]:
    return _reference(value)


def parse_cancel_agent_request(value: object) -> Result[AgentRequestReference]:
    return _reference(value)
