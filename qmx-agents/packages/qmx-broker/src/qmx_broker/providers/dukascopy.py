"""Dukascopy historical data: no key, no sign-in, one hourly `.bi5` request proves reach.

`dukascopy-node` is the downloader's fetcher (AD-68); this adapter is the connection row that names
where its data comes from, and the health check asks the public datafeed for one past hour.
"""

from __future__ import annotations

import time
from collections.abc import Mapping

from qmx_broker.models import Broker, Connection
from qmx_broker.providers.http import Fetch, answered, urllib_fetch
from qmx_broker.registry import Declaration, ProbeResult, register, register_probe

BASE = "https://datafeed.dukascopy.com/datafeed"
"""Month is zero-indexed in the provider's path: 2026/08/01 is 1 September 2026."""
PROBE_PATH = "EURUSD/2026/08/01/03h_ticks.bi5"
"""One Tuesday, 03:00 UTC, a past hour the public datafeed serves."""

DECLARATION = Declaration(
    name="dukascopy",
    kind="data",
    auth="none",
    credential_fields=(),
    environments=("live",),
    reads=("bars", "ticks"),
    runs_on=("any",),
    session="step",
    limit_signals=("an empty response rather than a failure",),
    limit_scope="connection",
    error_map={"429": "retry", "5xx": "retry", "404": "retry"},
    health_check="One hourly bi5 request to the public datafeed",
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
    return answered(started, fetch(f"{BASE}/{PROBE_PATH}", {}, "GET"))


register_probe("dukascopy", probe)
