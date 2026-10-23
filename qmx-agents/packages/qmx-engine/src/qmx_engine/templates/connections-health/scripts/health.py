"""Read every connection on this home and leave one word each for the host heartbeat.

The row is what Settings holds: `[connections]`, or the old `[brokers]` section that the control
plane has already read into `connections`. A provider with `auth: none` is probed without a key.
A keyed provider's secret is read from its `qmx/*` entry and never printed. `ok | slowed |
maintenance | needs_you | down` is the one word per connection; only `down` files an incident,
under the masked signature `connection:<id>:<code>` (AD-67).
"""

import json
import os
import sys
import time
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from qmx_broker.credentials import credentials
from qmx_broker.models import BrokerSettings
from qmx_broker.registry import NeedsYou, describe, probe_for, walk

from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.workers.zones import home_of

TYPE = "connections-health"


def settings_rows(home: Path) -> BrokerSettings:
    path = home / "settings.toml"
    if not path.exists():
        return BrokerSettings()
    document = tomllib.loads(path.read_text("utf-8"))
    if isinstance(document.get("connections"), list):
        return BrokerSettings(connections=document["connections"])
    if isinstance(document.get("brokers"), list):
        return BrokerSettings(brokers=document["brokers"])
    return BrokerSettings()


def resolve(provider, connection, probe):
    """The probe bound to its secret; a missing entry is `needs_you`, not a network failure."""
    if describe(provider.adapter).auth == "none":
        secret = None
    else:
        try:
            secret = credentials(connection.credential_ref)
        except ValueError as error:
            raise NeedsYou("credential_missing", str(error)) from error
    return probe(provider, connection, secret=secret)


def report(connection, reading) -> dict:
    return {
        "connection": connection.id,
        "word": reading.word,
        "setup": reading.setup,
        "code": reading.code,
        "latency_ms": reading.latency_ms,
        "clock_offset_ms": reading.clock_offset_ms,
        "slowed_until": reading.slowed_until,
        "at": datetime.now(UTC).isoformat(),
    }


def main() -> int:
    given = json.load(sys.stdin).get("in") or {}
    home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
    dry_run = bool(given.get("dry_run"))
    rows = []
    for provider in settings_rows(home).providers:
        for connection in provider.connections:
            now = time.time()
            probe = probe_for(provider.adapter)
            if dry_run:
                rows.append(
                    {"connection": connection.id, "word": "needs_you", "setup": "configured",
                     "code": "dry_run", "latency_ms": None, "clock_offset_ms": None,
                     "slowed_until": None, "at": datetime.now(UTC).isoformat()}
                )
                continue
            reading = walk(
                provider,
                connection,
                probe=None if probe is None else lambda p, c: resolve(p, c, probe),
                now=now,
            )
            rows.append(report(connection, reading))
    offsets = [row["clock_offset_ms"] for row in rows if row["clock_offset_ms"] is not None]
    document = {
        "at": datetime.now(UTC).isoformat(),
        "clock_offset_ms": max(offsets, key=abs) if offsets else None,
        "readings": rows,
    }
    logs = home / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    target = logs / "connections-health.json"
    scratch = target.with_suffix(".tmp")
    scratch.write_text(json.dumps(document), encoding="utf-8")
    os.replace(scratch, target)
    with InboxTable.open(home) as table:
        for row in rows:
            if row["word"] == "down":
                table.incident(
                    TYPE,
                    f"connection:{row['connection']}:{row['code'] or 'down'}",
                    f"connection {row['connection']} is down",
                    f"health check failed with {row['code'] or 'no answer'}",
                    at=row["at"],
                )
    print(json.dumps({"readings": rows}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
