"""S17, no key value at rest. Searches the QMX homes the HP7 checks used, the evidence logs in
`QMA_EVIDENCE_DIR`, and every transcript and run journal under them for each key value the
checks used: the OpenRouter key from the keyring and the fake model's key. Values are compared
in memory and never printed; the log names only the key and the files that hold it.

PASS when no file holds any value.

    s17_secrets.py [--root <folder> ...]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from common import SCRATCH, SHIP_HOME, Log, files_holding
from fake_model import FAKE_KEY
from spend import openrouter_key


def main() -> int:
    parser = argparse.ArgumentParser(prog="s17_secrets.py")
    parser.add_argument("--root", type=Path, action="append", default=[])
    args = parser.parse_args()
    log = Log("hp7-s17")
    evidence = Path(os.environ["QMA_EVIDENCE_DIR"])
    roots = [SCRATCH / "homes", SCRATCH / "workspaces", evidence, SHIP_HOME, *args.root]
    roots = [root for root in roots if root.exists()]
    log(f"searching: {[str(root) for root in roots]}")
    keys = {"openrouter": openrouter_key(), "fake provider key": FAKE_KEY}
    for name, value in keys.items():
        if value is None:
            log(f"{name}: no keyring entry, nothing to search for")
            continue
        holders = files_holding(roots, value)
        log.check(f"no file holds the {name}", not holders, [str(path) for path in holders])
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
