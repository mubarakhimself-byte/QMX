# Connections health

One reading per connection, every five minutes, on the machine that owns the connection's home. The workflow walks the five setup states of AD-30 (`available | configured | authorized | reachable | healthy`) and writes one word per connection into the host's next heartbeat row. Only `down` is an incident.

## Steps

1. `Read every connection` reads `[connections]` from the home's Settings, or the old `[brokers]` section the control plane read into it. Each row's adapter must have a declaration in `qmx_broker.registry`; a row whose adapter is installed nowhere reads `needs_you`.
2. A keyless provider is asked for one small resource: a Dukascopy hourly `.bi5`, the Binance public bucket index, an exchange server time, or the `http` row's base URL. A keyed provider's secret is read from its `qmx/*` entry for the length of that one request, never printed and never written anywhere.
3. The walk writes `logs/connections-health.json`, which the host's heartbeat loop attaches to its next row as `connections`, with the measured `clock_offset_ms`. A provider's own slow-down signal sets `slowed_until`; while it is live the probe is skipped and the reading stays `slowed`.

A `down` reading files one incident with the masked signature `connection:<id>:<code>`. `needs_you` (a missing keyring entry, a key that can trade live money on the PC, an adapter not yet installed) is not an incident, it is a task for him.

## Cadence

Every five minutes (Claude's default). The catalogue row installs the cron trigger disabled, as every row does; the interval is editable in Settings.

## Test runs

A run started with `{"dry_run": true}` probes nothing and reports each configured connection as `needs_you` with `dry_run`, which is the shape a home with no network answers.

## Left out, and why

- The broker-side homes (cTrader's long-running session, MT5's terminal) belong to DR5B. Their declarations are here; their `health()` is not.
- No model call is involved, so there is no recorded fixture.
