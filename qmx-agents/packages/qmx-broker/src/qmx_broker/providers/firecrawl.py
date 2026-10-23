"""Firecrawl: the one web-fetch path, keyed by `qmx/data/<connection>`; its credit call is the probe."""

from __future__ import annotations

import time
from collections.abc import Mapping

from qmx_broker.models import Broker, Connection
from qmx_broker.registry import Declaration, NeedsYou, ProbeResult, register, register_probe

from qmx_broker.providers.http import Fetch, answered, declared_object, urllib_fetch

ENDPOINT = "https://api.firecrawl.dev/v2/team/credit-usage"

DECLARATION = Declaration(
    name="firecrawl",
    kind="data",
    auth="api_key",
    credential_fields=("apiKey",),
    environments=("live",),
    reads=("pages",),
    runs_on=("any",),
    session="step",
    limit_signals=("HTTP 429 with Retry-After",),
    limit_scope="connection",
    error_map={"429": "retry", "5xx": "retry", "401": "needs_you", "403": "needs_you"},
    health_check="The team credit-usage call",
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
    del provider
    key = (secret or {}).get("apiKey") or (secret or {}).get("api_key")
    if not key:
        raise NeedsYou("credential_missing", f"keyring entry {connection.credential_ref} has no apiKey")
    started = time.monotonic()
    response = fetch(ENDPOINT, {"Authorization": f"Bearer {key}"}, "GET")
    result = answered(started, response)
    declared_object(response)
    return result


register_probe("firecrawl", probe)
