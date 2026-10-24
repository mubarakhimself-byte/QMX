"""CCXT public endpoints: recent days from an exchange without a key or a sign-in.

A `kind: data` connection under this adapter reads public market data only. A keyed CCXT row is
the `ccxt` broker adapter, which is a different connection: one key on one machine (AD-67).
"""

from __future__ import annotations

import time
from collections.abc import Mapping

from qmx_broker.models import Broker, Connection
from qmx_broker.providers.http import Fetch, answered, declared_object, urllib_fetch
from qmx_broker.registry import Declaration, ProbeResult, register, register_probe

TIME_ENDPOINTS = {
    "binance": "https://api.binance.com/api/v3/time",
    "kraken": "https://api.kraken.com/0/public/Time",
    "coinbase": "https://api.exchange.coinbase.com/time",
}

DECLARATION = Declaration(
    name="ccxt-public",
    kind="data",
    auth="none",
    credential_fields=(),
    environments=("live",),
    reads=("bars", "quotes", "instrument_specs"),
    runs_on=("any",),
    session="step",
    limit_signals=("HTTP 429 with Retry-After", "HTTP 418"),
    limit_scope="egress",
    error_map={"429": "retry", "418": "retry", "5xx": "retry"},
    health_check="The exchange's own server-time call",
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
    del connection, secret
    exchange = provider.exchange.casefold() or "binance"
    endpoint = TIME_ENDPOINTS.get(exchange)
    if endpoint is None:
        raise ValueError(f"CCXT public data has no time endpoint for {exchange}")
    started = time.monotonic()
    response = fetch(endpoint, {}, "GET")
    result = answered(started, response)
    declared_object(response)
    return result


register_probe("ccxt-public", probe)
