"""P-NOTRADE, the allow-list half (W6, acceptance): `is_replicable` is false for a trade key, the
backup payload key and any token entry, and true only for `qmx/read/*`, `qmx/data/*` and a
model-provider row (AD-28, N5, ruling 135).

Names only. This probe never reads a keyring, a key file or a secret: it asks the module's own rule
about the names the plan lists, then proves the vault refuses a forced install and publishes no
tombstone for a name that was never in it. The W13 half, which adds a key through a stub adapter,
is not this probe's.

**Pass:** every trade, token and backup name is refused and stays out of the sync payload, the three
allowed kinds are taken, and a refused deletion publishes nothing.
**Fail:** any of those names replicates, a forced install seals one, or a deletion spreads by
tombstone for a name the vault never held.

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
    finally:
        if not arguments.keep:
            shutil.rmtree(ROOT, ignore_errors=True)
    return report.render()


if __name__ == "__main__":
    raise SystemExit(main())
