"""EP0 p_runtime. No model. Records the Python and SQLite versions the engine will run on,
whether `uuid.uuid7` exists, and whether `qmx_ledger.journal.fingerprint` gives the same digest
for one document in two separate processes. PASS when every value is recorded and the two
fingerprints match.

    p_runtime.py
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import uuid

from common import log

DOCUMENT = (
    '{"run_id": "r-1", "seq": 3, "event": "node_finished", '
    '"payload": {"node": "scan", "out": ["a", "b"], "cost": 0.25, "note": "caf\\u00e9"}}'
)
PRINT_FINGERPRINT = (
    "import json, sys; from qmx_ledger.journal import fingerprint; "
    "print(fingerprint(json.loads(sys.argv[1])))"
)


def fingerprint_in_new_process() -> str:
    found = subprocess.run(
        [sys.executable, "-c", PRINT_FINGERPRINT, DOCUMENT],
        capture_output=True,
        text=True,
        check=True,
    )
    return found.stdout.strip()


def main() -> int:
    say = log("ep0-runtime")
    say(f"sys.version: {sys.version}")
    say(f"sqlite3.sqlite_version: {sqlite3.sqlite_version}")
    has_uuid7 = hasattr(uuid, "uuid7")
    say(f"uuid.uuid7 exists: {has_uuid7}" + (f" (sample {uuid.uuid7()})" if has_uuid7 else ""))
    first, second = fingerprint_in_new_process(), fingerprint_in_new_process()
    say(f"fingerprint, process 1: {first}")
    say(f"fingerprint, process 2: {second}")
    say.check("every value is recorded", all((sys.version, sqlite3.sqlite_version)), True)
    say.check(
        "the two processes give one fingerprint",
        len(first) == 64 and first == second,
        [first, second],
    )
    return int(say.verdict())


if __name__ == "__main__":
    sys.exit(main())
