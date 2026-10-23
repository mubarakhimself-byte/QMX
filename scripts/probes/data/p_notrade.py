"""P-NOTRADE, the allow-list half (W6, acceptance): `is_replicable` is false for a trade key, the
backup payload key and any token entry, and true only for `qmx/read/*`, `qmx/data/*` and a
model-provider row (AD-28, N5, ruling 135).

Names only. This probe never reads a keyring, a key file or a secret: it asks the module's own rule
about the names the plan lists, then proves the vault refuses a forced install and publishes no
tombstone for a name that was never in it.

The W13 half adds a stub adapter whose probe returns a live account with trade scope. Its key is
stored nowhere and its row reads `needs_you`; a read-only key files under `qmx/read/*` and a data
key under `qmx/data/*` (AD-67).

**Pass:** every trade, token and backup name is refused and stays out of the sync payload, the three
allowed kinds are taken, a refused deletion publishes nothing, and the stub live-trade key stores
nothing and reads `needs_you`.
**Fail:** any of those names replicates, a forced install seals one, a deletion spreads by
tombstone for a name the vault never held, or a live-trade key is stored.

    uv run --no-sync python scripts/probes/data/p_notrade.py
    uv run --no-sync python scripts/probes/data/p_notrade.py --keep
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Final

from common import Report

from qmx_broker.credentials import file_credential
from qmx_broker.models import Broker, Connection
from qmx_broker.registry import Declaration, ProbeResult, register, walk

from qmx_router.vault import MemorySource, Vault, VaultKey, VaultStore, is_replicable

ROOT: Final = Path(os.environ.get("QMX_PROBE_SCRATCH", "D:/Temp/dr2c")) / "p-notrade"
VALUE: Final = "lanes-only-value"
REFUSED: Final[tuple[str, ...]] = (
    "qmx/ctrader-demo",
    "qmx/ctrader-live",
    "qmx/crypto",
    "qmx/backup-payload-key",
    "qmx/chatgpt",
    "qmx/read/ctrader-access-token",
    "qmx/data/binance-oauth",
    "qmx/brokers",
)
ALLOWED: Final[tuple[str, ...]] = ("qmx/read/x", "qmx/data/x", "qmx/kimi", "qmx/openrouter")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    arguments = parser.parse_args(argv)
    report = Report("P-NOTRADE")
    shutil.rmtree(ROOT, ignore_errors=True)
    ROOT.mkdir(parents=True)
    try:
        vault = Vault(VaultKey.generate(), MemorySource(), machine="pc")
        taken = [name for name in ALLOWED if is_replicable(name)]
        report.numbers["names checked"] = len(REFUSED) + len(ALLOWED)
        report.numbers["allowed"] = taken
        if taken != list(ALLOWED):
            report.fail(f"the allow-list took {taken}, expected {list(ALLOWED)}")
        for name in ALLOWED:
            vault.install(name, VALUE)
        for name in REFUSED:
            if is_replicable(name):
                report.fail(f"{name} replicates")
            entry = vault.install(name, VALUE, replicable=True)
            if entry.replicable or entry.sealed:
                report.fail(f"{name} was sealed when the caller forced it")
            vault.delete(name)
        document = json.dumps(vault.sync_document(), sort_keys=True)
        (ROOT / "document.json").write_text(document, encoding="utf-8")
        leaked = [name for name in REFUSED if name in document]
        report.numbers["refused names in the sync payload"] = leaked
        if leaked:
            report.fail(f"the sync payload carries {leaked}")
        store = VaultStore("contabo")
        store.sync(json.loads(document))
        report.numbers["names the server received"] = list(store.names())
        report.numbers["tombstones published"] = list(store.tombstones())
        if list(store.names()) != sorted(ALLOWED):
            report.fail(f"the server received {list(store.names())}, expected {sorted(ALLOWED)}")
        if store.tombstones():
            report.fail(f"deleting a non-vault name published {list(store.tombstones())}")

        class StubStore:
            def __init__(self) -> None:
                self.writes: list[str] = []

            def get_password(self, service: str, username: str) -> str | None:
                return None

            def set_password(self, service: str, username: str, password: str) -> None:
                self.writes.append(service)

            def delete_password(self, service: str, username: str) -> None:
                return None

        register(
            Declaration(
                name="stub-live",
                kind="broker",
                auth="api_key",
                credential_fields=("apiKey",),
                environments=("live",),
                reads=("accounts",),
                runs_on=("any",),
                session="host",
                limit_signals=("429",),
                limit_scope="connection",
                error_map={"429": "retry"},
                health_check="the stub's account list",
            )
        )
        stub_store = StubStore()
        filing = file_credential(
            "live-trade", {"apiKey": VALUE}, can_trade_live=True, store=stub_store
        )
        reading = walk(
            Broker(id="stub", name="Stub broker", adapter="stub-live"),
            Connection(
                id="live-trade",
                credential_ref="qmx/ctrader-live",
                environment="live",
                scope="trade",
                home="pc",
            ),
            probe=lambda _provider, _connection: ProbeResult(1),
            now=0.0,
        )
        report.numbers["W13 stub: live-trade key"] = (
            f"stored {filing.stored}, row {reading.word}, writes {len(stub_store.writes)}"
        )
        if filing.stored or stub_store.writes or reading.word != "needs_you":
            report.fail(
                f"a live-trade key was stored ({filing.stored}) or read {reading.word}"
            )
    finally:
        if not arguments.keep:
            shutil.rmtree(ROOT, ignore_errors=True)
    return report.render()


if __name__ == "__main__":
    raise SystemExit(main())
