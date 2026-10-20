"""The one error classifier (engine AD-40 (6), AD-12).

Every provider answer that is not a success, and every error a provider raises inside a 200
stream, becomes one `Classification` here: a closed class, the provider's own words, and the
reset the provider named. The pool reads the class to cool, bench or rotate an account, and the
engine's ladder reads the same class to retry, compress, step down or park. No other module
words a provider error.

The class set is the plan's seven: `rate_limit`, `billing`, `auth`, `model_entitlement`,
`content`, `transient` and `fatal`. The finer distinction a provider makes is a hint on the
classification, never a class of its own:

- `usage_limit` separates an account's own limit (rotate at once, cool until the reset the
  provider named) from a burst of traffic (retry the same account once, then cool).
- `reset_in` (seconds, as `retry-after` defines it) and `reset_at` (an absolute stamp a body
  carried) are the two shapes a provider states its reset in. `until()` turns either into the
  absolute moment, against the caller's clock.

Classification reads no clock, so a replayed body classifies the same way on any day.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any, Final, Literal, cast

type ErrorClass = Literal[
    "rate_limit", "billing", "auth", "model_entitlement", "content", "transient", "fatal"
]
"""The closed set. Adding a member is a contract change: the pool and the ladder both switch on
it."""
CLASSES: Final[frozenset[str]] = frozenset(
    {"rate_limit", "billing", "auth", "model_entitlement", "content", "transient", "fatal"}
)

USAGE_WORDS: Final = (
    "usage limit",
    "usage_limit",
    "quota",
    "insufficient_quota",
    "insufficient credits",
    "credit balance",
    "credits",
    "billing",
    "payment required",
    "exceeded your current quota",
)
"""A 429 whose body carries one of these is the account's own limit, not traffic."""

ENTITLEMENT_WORDS: Final = (
    "model_not_found",
    "model not found",
    "model not exist",
    "not exist",
    "does not exist",
    "not available",
    "no access",
    "not entitled",
    "unknown model",
    "unsupported model",
    "not supported",
)
"""A 400 or 404 naming the model, which benches that model on that account only."""

CONTENT_WORDS: Final = (
    "content policy",
    "content_policy",
    "content filter",
    "content_filter",
    "safety",
    "moderation",
    "blocked",
    "context_length",
    "context length",
    "maximum context",
    "prompt is too long",
    "too many tokens",
)
"""A refusal of the request's content: a policy block, or a prompt past the window. Neither is
the account's fault, and both are the request's to change (compress or reword)."""

AUTH_WORDS: Final = ("invalid api key", "invalid_api_key", "unauthorized", "authentication")
DELAY_CEILING_S: Final = 100_000_000
"""A numeric reset at or above this is a Unix stamp; below it, a delay in seconds. Ten digits is
2001 in Unix seconds and over three years as a delay."""
RESET_KEYS: Final = ("resets_at", "reset_at", "reset", "retry_after", "expires_at")
"""Fields a provider uses for the moment it serves again, in ISO 8601 or Unix seconds."""
DELAY_HEADERS: Final = ("retry-after",)
STAMP_HEADERS: Final = ("x-ratelimit-reset-requests", "x-ratelimit-reset-tokens")


@dataclass(frozen=True)
class Classification:
    """One provider error, read once."""

    kind: ErrorClass
    status: int
    message: str
    """The provider's own words, trimmed. Never a key: the caller words its own refusals."""
    usage_limit: bool = False
    """A 429 that is the account's limit rather than traffic."""
    reset_in: float | None = None
    """Seconds until the provider serves again, as `retry-after` states it."""
    reset_at: datetime | None = None
    """The absolute moment a body named."""

    def until(self, now: datetime) -> datetime | None:
        """When this error's cooldown ends, against `now`, or None when it named no reset."""
        if self.reset_at is not None:
            return self.reset_at
        if self.reset_in is not None:
            return now + timedelta(seconds=self.reset_in)
        return None


def classify(
    status: int,
    body: object = None,
    headers: Mapping[str, str] | None = None,
) -> Classification:
    """`status` and `body` as one class. `status` 0 is an error a provider raised inside a 200
    stream, which is always `transient`."""
    text = message(body)
    lowered = f"{text} {_code(body)}".lower()
    reset_in, reset_at = _reset(body, headers)
    if status == 0:
        return Classification("transient", 0, text, reset_in=reset_in, reset_at=reset_at)
    if status in (401, 403):
        return Classification("auth", status, text, reset_in=reset_in, reset_at=reset_at)
    if status == 402:
        return Classification(
            "billing", status, text, usage_limit=True, reset_in=reset_in, reset_at=reset_at
        )
    if status == 429:
        if "insufficient_quota" in lowered:
            kind: ErrorClass = "billing"
        else:
            kind = "rate_limit"
        limit = any(word in lowered for word in USAGE_WORDS)
        return Classification(
            kind, status, text, usage_limit=limit, reset_in=reset_in, reset_at=reset_at
        )
    if status in (404, 410):
        return Classification(
            "model_entitlement", status, text, reset_in=reset_in, reset_at=reset_at
        )
    if status in (400, 409, 413, 422):
        return Classification(
            _bad_input(lowered), status, text, reset_in=reset_in, reset_at=reset_at
        )
    if status in (408, 425, 500, 502, 503, 504, 529) or status >= 520:
        return Classification("transient", status, text, reset_in=reset_in, reset_at=reset_at)
    if 400 <= status < 500:
        return Classification("fatal", status, text, reset_in=reset_in, reset_at=reset_at)
    return Classification("transient", status, text, reset_in=reset_in, reset_at=reset_at)


def _bad_input(lowered: str) -> ErrorClass:
    """A 4xx the provider refused for its own reasons: the model, the content, or the request."""
    if any(word in lowered for word in ENTITLEMENT_WORDS):
        return "model_entitlement"
    if any(word in lowered for word in CONTENT_WORDS):
        return "content"
    if any(word in lowered for word in AUTH_WORDS):
        return "auth"
    return "fatal"


def message(body: object) -> str:
    """The provider's message, from a decoded body, raw bytes or a bare string. Anthropic nests
    it under `error.message`, the OpenAI-compatible routes under `error.message` or `message`."""
    found: object = body
    if isinstance(body, bytes):
        try:
            found = json.loads(body)
        except ValueError:
            return body.decode("latin-1")[:400]
    if isinstance(found, str):
        return found[:400]
    if not isinstance(found, dict):
        return "" if found is None else str(found)[:400]
    table = cast("dict[str, Any]", found)
    error = table.get("error")
    if isinstance(error, str):
        return error[:400]
    if isinstance(error, dict):
        nested = cast("dict[str, Any]", error)
        for key in ("message", "code", "type"):
            if isinstance(nested.get(key), str):
                return str(nested[key])[:400]
    for key in ("message", "detail", "code"):
        if isinstance(table.get(key), str):
            return str(table[key])[:400]
    return ""


def _code(body: object) -> str:
    """The provider's own error code, from `error.code`, `error.type` or a top-level `code`.
    A code names the provider's reason even when its message is worded differently."""
    if isinstance(body, bytes):
        try:
            body = json.loads(body)
        except ValueError:
            return ""
    if not isinstance(body, dict):
        return ""
    table = cast("dict[str, Any]", body)
    error = table.get("error")
    holders = (cast("dict[str, Any]", error) if isinstance(error, dict) else {}, table)
    for holder in holders:
        for key in ("code", "type"):
            value = holder.get(key)
            if isinstance(value, str):
                return value
    return ""


def _reset(body: object, headers: Mapping[str, str] | None) -> tuple[float | None, datetime | None]:
    """The reset the provider named: a delay from its headers, then a stamp or delay from its
    body."""
    reset_in: float | None = None
    reset_at: datetime | None = None
    if headers is not None:
        for name, value in headers.items():
            low = name.lower()
            if low in DELAY_HEADERS:
                reset_in = _delay(value)
            elif low in STAMP_HEADERS:
                reset_at = _stamp(value)
    if isinstance(body, bytes):
        try:
            body = json.loads(body)
        except ValueError:
            return reset_in, reset_at
    if not isinstance(body, dict):
        return reset_in, reset_at
    table = cast("dict[str, Any]", body)
    error = table.get("error")
    holders: tuple[Mapping[str, Any], ...] = (
        cast("dict[str, Any]", error) if isinstance(error, dict) else {},
        table,
    )
    for holder in holders:
        found = _from_table(holder)
        if found is not None:
            stamp, delay = found
            return reset_in if reset_in is not None else delay, reset_at or stamp
    return reset_in, reset_at


def _from_table(table: Mapping[str, Any]) -> tuple[datetime | None, float | None] | None:
    for key in RESET_KEYS:
        value = table.get(key)
        if value is None or isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            if value <= 0:
                continue
            if value >= DELAY_CEILING_S:
                return datetime.fromtimestamp(float(value), UTC), None
            return None, float(value)
        if isinstance(value, str) and value.strip():
            delay = _delay(value)
            if delay is not None:
                return None, delay
            stamp = _stamp(value)
            if stamp is not None:
                return stamp, None
    return None


def _delay(value: object) -> float | None:
    """`retry-after` as seconds. A non-positive value is no wait."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value) if value > 0 else None
    if not isinstance(value, str):
        return None
    text = value.strip()
    try:
        found = float(text)
    except ValueError:
        return None
    return found if found > 0 else None


def _stamp(value: object) -> datetime | None:
    """An absolute reset: Unix seconds, an ISO 8601 stamp or an HTTP date."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return datetime.fromtimestamp(float(value), UTC) if value > 0 else None
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        return parsedate_to_datetime(text).astimezone(UTC)
    except TypeError, ValueError:
        pass
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.fromtimestamp(float(text), UTC)
        except ValueError, OSError, OverflowError:
            return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
