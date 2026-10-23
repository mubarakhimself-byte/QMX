"""The declarative `http` data adapter and the one transport every data provider probe shares.

A plain HTTP data provider needs no code: its row names a base URL in `exchange`, and its health
check is one request to that URL. The generic adapter checks the response body against the
declared shape, so an error inside HTTP 200 is an error (AD-67).

`Fetch` is the boundary the probes parse: a deployment passes `urllib_fetch`, a test passes a
recorded response, and no probe reaches the network by itself.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Protocol

from qmx_broker.models import Broker, Connection
from qmx_broker.registry import (
    Declaration,
    Down,
    NeedsYou,
    ProbeResult,
    SlowDown,
    register,
    register_probe,
)

TIMEOUT_S = 10.0
OK = frozenset({200, 206})


@dataclass(frozen=True, slots=True)
class Response:
    status: int
    headers: Mapping[str, str]
    body: bytes = b""


class Fetch(Protocol):
    def __call__(
        self, url: str, headers: Mapping[str, str], method: str
    ) -> Response: ...


def urllib_fetch(url: str, headers: Mapping[str, str], method: str) -> Response:
    request = urllib.request.Request(  # noqa: S310 - the provider's own published URL
        url, headers=dict(headers), method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as answer:  # noqa: S310
            return Response(answer.status, dict(answer.headers), answer.read(4096))
    except urllib.error.HTTPError as error:
        return Response(error.code, dict(error.headers or {}), b"")


def latency_ms(started: float) -> int:
    return max(0, round((time.monotonic() - started) * 1000))


def retry_after(headers: Mapping[str, str]) -> float | None:
    value = {key.casefold(): item for key, item in headers.items()}.get("retry-after")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        try:
            when = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        return max(0.0, when.timestamp() - time.time())


def clock_offset_ms(headers: Mapping[str, str]) -> int | None:
    value = {key.casefold(): item for key, item in headers.items()}.get("date")
    if value is None:
        return None
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        return None
    return round((when.timestamp() - time.time()) * 1000)


def answered(started: float, response: Response) -> ProbeResult:
    """A 2xx answer is a healthy reading; anything else is the fault its status names."""
    if response.status in (429, 418):
        raise SlowDown("rate_limited", retry_after=retry_after(response.headers))
    if response.status in (401, 403):
        raise NeedsYou("unauthorized")
    if response.status >= 500:
        raise Down("provider_error")
    if response.status not in OK:
        raise Down(f"http_{response.status}")
    return ProbeResult(latency_ms(started), clock_offset_ms(response.headers))


def payload(response: Response) -> object:
    try:
        return json.loads(response.body)
    except ValueError as error:
        raise Down("invalid_body") from error


def declared_object(response: Response) -> dict[str, object]:
    value = payload(response)
    if not isinstance(value, dict):
        raise Down("invalid_body")
    return {str(key): item for key, item in value.items()}


def base_url(provider: Broker, connection: Connection) -> str:
    url = provider.exchange.strip()
    if not url.startswith(("https://", "http://")):
        raise NeedsYou("url_missing", "Set the provider's base URL in exchange")
    return url


DECLARATION = Declaration(
    name="http",
    kind="data",
    auth="api_key",
    credential_fields=(),
    environments=("live",),
    reads=("bars", "quotes"),
    runs_on=("any",),
    session="step",
    limit_signals=("429", "useful Retry-After"),
    limit_scope="connection",
    error_map={"429": "retry", "5xx": "retry", "401": "needs_you", "403": "needs_you"},
    health_check="One request to the declared base URL; the body must parse as the declared object",
    published_limits=(),
)
register(DECLARATION)


def probe(
    provider: Broker,
    connection: Connection,
    *,
    fetch: Fetch = urllib_fetch,
    secret: Mapping[str, str] | None = None,
) -> ProbeResult:
    del secret
    started = time.monotonic()
    response = fetch(base_url(provider, connection), {}, "GET")
    result = answered(started, response)
    declared_object(response)
    return result


register_probe("http", probe)


__all__ = [
    "DECLARATION",
    "Fetch",
    "OK",
    "Response",
    "answered",
    "base_url",
    "clock_offset_ms",
    "declared_object",
    "latency_ms",
    "payload",
    "probe",
    "retry_after",
    "urllib_fetch",
]
