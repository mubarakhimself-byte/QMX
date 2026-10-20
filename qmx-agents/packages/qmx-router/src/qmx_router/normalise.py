"""AD-50's normaliser: one request, edited once, for the model row it is going to.

The CLI shapes one request for Anthropic whatever its main profile is: tool search with
`defer_loading`, beta fields, `metadata.user_id`, `x-claude-code-*` headers, 1-hour cache
markers, `max_tokens` sized for a Claude window. A third-party row answers 400 to most of that
or silently bills differently. So the router runs this on the key, chat and GPT lanes, on the
request about to leave, against the row the `model` field resolved to.

Everything not named here is forwarded unchanged. The plan lane never calls it.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Final, Literal, cast

from qmx_router.registry import ModelRow

OAUTH_BETA: Final = "oauth-2025-04-20"
"""Always dropped, even if a row lists it: it declares the bearer an OAuth token, which only
Anthropic issues."""
GATED_FIELDS: Final[Mapping[str, str]] = {
    "context_management": "context-management-2025-06-27",
    "container": "code-execution-2025-05-22",
    "inference_geo": "inference-geo-2025-08-01",
}
"""Each top-level body field one beta carries. The field goes when its beta did."""
STRICT_BETA: Final = "structured-outputs-2025-11-13"
CACHE_TTL_BETA: Final = "extended-cache-ttl-2025-04-11"
TOOL_SEARCH_TYPE: Final = "tool_search_tool"
"""The deferred-tool loader's `type` prefix. The tool itself is useless once `defer_loading` is
gone, and third parties refuse the type outright."""
IMAGE_PLACEHOLDER: Final = "[image omitted: this model cannot see images]"
CREDENTIAL_HEADERS: Final = "x-claude-code-"
"""Headers that carry the operator's account identity to Anthropic; never to a third party."""

type ErrorClass = Literal[
    "usage_limit", "rate_limit", "auth", "bad_input", "not_found", "provider", "transport"
]

# Message text that means the provider's own limit was hit, rather than a burst of traffic.
USAGE_WORDS: Final = (
    "usage limit",
    "usage_limit",
    "quota",
    "insufficient_quota",
    "insufficient credits",
    "billing",
    "credit balance",
)


@dataclass(frozen=True)
class Egress:
    """The request as it will leave: the body to send and the headers to send it with."""

    body: bytes
    headers: dict[str, str]


def normalise(row: ModelRow, body: bytes, headers: Mapping[str, str]) -> Egress:
    """`body` and `headers` edited for `row`. Bytes are returned untouched when the row takes the
    request as sent, so the common path never re-serializes."""
    kept, betas = _headers(row, headers)
    try:
        parsed = json.loads(body)
    except ValueError:
        return Egress(body, kept)
    if not isinstance(parsed, dict):
        return Egress(body, kept)
    document = cast("dict[str, Any]", parsed)
    _identity(document)
    _output(row, document)
    tools = _tools(row, document, betas)
    _messages(row, document)
    _cache(row, document, tools)
    _thinking(row, document)
    for field, beta in GATED_FIELDS.items():
        if beta not in betas:
            document.pop(field, None)
    return Egress(_dumps(document), kept)


def _dumps(document: object) -> bytes:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()


def _headers(row: ModelRow, headers: Mapping[str, str]) -> tuple[dict[str, str], frozenset[str]]:
    """The headers to send and the betas that survive. A beta survives only when the row lists
    it; the OAuth beta never does."""
    kept: dict[str, str] = {}
    betas: frozenset[str] = frozenset()
    for name, value in headers.items():
        low = name.lower()
        if low == "anthropic-beta":
            kept_betas = [
                beta.strip()
                for beta in value.split(",")
                if beta.strip() in row.accepts_betas and beta.strip() != OAUTH_BETA
            ]
            betas = frozenset(kept_betas)
            if kept_betas:
                kept[low] = ",".join(kept_betas)
            continue
        if low.startswith(CREDENTIAL_HEADERS) and low not in row.forward_headers:
            continue
        kept[low] = value
    return kept, betas


def _identity(document: dict[str, Any]) -> None:
    metadata = document.get("metadata")
    if not isinstance(metadata, dict):
        return
    table = cast("dict[str, Any]", metadata)
    table.pop("user_id", None)
    if not table:
        document.pop("metadata")


def _output(row: ModelRow, document: dict[str, Any]) -> None:
    wanted = document.get("max_tokens")
    if isinstance(wanted, int) and not isinstance(wanted, bool) and wanted > row.max_output:
        document["max_tokens"] = row.max_output


def _tools(row: ModelRow, document: dict[str, Any], betas: frozenset[str]) -> list[Any]:
    """The tool list after the row's rules, or an empty list when it had none."""
    raw = document.get("tools")
    if not isinstance(raw, list):
        return []
    kept: list[Any] = []
    for item in cast("list[Any]", raw):
        if not isinstance(item, dict):
            kept.append(item)
            continue
        tool = cast("dict[str, Any]", item)
        tool.pop("defer_loading", None)
        if row.tool_search != "native" and str(tool.get("type", "")).startswith(TOOL_SEARCH_TYPE):
            continue
        if STRICT_BETA not in betas:
            tool.pop("strict", None)
        kept.append(tool)
    document["tools"] = kept
    return kept


def _messages(row: ModelRow, document: dict[str, Any]) -> None:
    """History rewritten for blocks the target cannot parse, and images it cannot see."""
    for message in _tables(document.get("messages")):
        message["content"] = _blocks(row, message.get("content"))
    system = document.get("system")
    if isinstance(system, list):
        document["system"] = _blocks(row, system)


def _blocks(row: ModelRow, content: object) -> object:
    """One message's blocks, or its text unchanged. `tool_result` content nests one level."""
    if not isinstance(content, list):
        return content
    kept: list[Any] = []
    for item in cast("list[Any]", content):
        if not isinstance(item, dict):
            kept.append(item)
            continue
        block = cast("dict[str, Any]", item)
        match block.get("type"):
            case "tool_reference":
                kept.append({"type": "text", "text": f"[tool: {block.get('tool_name', '?')}]"})
            case "server_tool_use":
                continue
            case "thinking" | "redacted_thinking" if row.thinking == "none":
                continue
            case "image" if not row.vision:
                kept.append({"type": "text", "text": IMAGE_PLACEHOLDER})
            case "tool_result" if isinstance(block.get("content"), list):
                block["content"] = _blocks(row, block["content"])
                kept.append(block)
            case _:
                kept.append(block)
    return kept


def _cache(row: ModelRow, document: dict[str, Any], tools: list[Any]) -> None:
    """`cache_control` markers the row's TTL takes. `none` drops them all; a row on the default
    5-minute marker drops only an explicit `ttl` it does not take."""
    sites = list(_cache_sites([document, *tools]))
    if row.cache_ttl == "none":
        for parent, key in sites:
            parent.pop(key, None)
        return
    if row.cache_ttl == "1h":
        return
    for parent, key in sites:
        marker = parent.get(key)
        if isinstance(marker, dict):
            cast("dict[str, Any]", marker).pop("ttl", None)


def _cache_sites(values: list[object]) -> Iterator[tuple[dict[str, Any], str]]:
    """Every (parent, key) holding a `cache_control` marker under `values`."""
    pending = list(values)
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            for key, value in cast("dict[str, Any]", item).items():
                if key == "cache_control":
                    yield cast("dict[str, Any]", item), key
                elif isinstance(value, dict | list):
                    pending.append(value)
        elif isinstance(item, list):
            pending.extend(cast("list[Any]", item))


def _thinking(row: ModelRow, document: dict[str, Any]) -> None:
    if row.thinking == "none":
        document.pop("thinking", None)


def _tables(value: object) -> Iterator[dict[str, Any]]:
    if not isinstance(value, list):
        return
    for item in cast("list[Any]", value):
        if isinstance(item, dict):
            yield cast("dict[str, Any]", item)


def classify(status: int, body: object) -> ErrorClass:
    """What one provider answer is, once. A 429 splits on the provider's own words: its usage
    limit is final, a burst of traffic is not."""
    if status in (401, 403):
        return "auth"
    if status == 404:
        return "not_found"
    if status in (400, 409, 413, 422):
        return "bad_input"
    if status in (429, 402):
        text = _message(body).lower()
        return "usage_limit" if any(word in text for word in USAGE_WORDS) else "rate_limit"
    if status in (408, 425, 500, 502, 503, 504, 529):
        return "transport"
    if 400 <= status < 600:
        return "provider"
    return "transport"


def refuse_retry(status: int, body: object) -> dict[str, str]:
    """Headers that stop the CLI retrying what the provider will not serve: none unless this is
    the provider's usage limit or a rate limit the pool must rotate away from (AD-50 (7))."""
    if classify(status, body) in ("usage_limit", "rate_limit"):
        return {"x-should-retry": "false"}
    return {}


def _message(body: object) -> str:
    found = body
    if isinstance(body, bytes):
        try:
            found = json.loads(body)
        except ValueError:
            return body.decode("latin-1")
    if not isinstance(found, dict):
        return str(found)
    error = cast("dict[str, Any]", found).get("error")
    if isinstance(error, dict):
        return str(cast("dict[str, Any]", error).get("message", ""))
    return str(cast("dict[str, Any]", found).get("message", ""))
