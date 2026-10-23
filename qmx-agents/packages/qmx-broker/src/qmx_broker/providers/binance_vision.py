"""Binance public bulk files (`data.binance.vision`): keyless, one bucket request proves reach.

The bucket serves klines, trades and checksums. Binance limits per client address, so the
connection's slowdown wait is shared per egress address (AD-67).
"""

from __future__ import annotations

import time
from collections.abc import Mapping

from qmx_broker.models import Broker, Connection
from qmx_broker.registry import Declaration, ProbeResult, register, register_probe

from qmx_broker.providers.http import Fetch, answered, urllib_fetch

BUCKET = "https://data.binance.vision/"

DECLARATION = Declaration(
    name="binance-vision",
    kind="data",
    auth="none",
    credential_fields=(),
    environments=("live",),
    reads=("bars", "trades", "instrument_specs"),
    runs_on=("any",),
    session="step",
    limit_signals=("HTTP 429 with Retry-After", "HTTP 418"),
    limit_scope="egress",
    error_map={"429": "retry", "418": "retry", "403": "retry", "5xx": "retry"},
    health_check="One request to the public bucket index",
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
    del provider, connection, secret
    started = time.monotonic()
    return answered(started, fetch(BUCKET, {}, "GET"))


register_probe("binance-vision", probe)
