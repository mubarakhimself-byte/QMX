"""Diffs the home's live `library.db` against the Library store, read-only, and prints the diff.
A diff that is not clean fails the run, so its test report reads failed."""

import json
import sys
from pathlib import Path

from qmx_library.migrate.verify import dual_diff

given = json.load(sys.stdin)["in"]
home = Path(given["home"])
diff = dual_diff(home, Path(given.get("store") or home / "library")).as_json()
if not diff["clean"]:
    print(f"[QMX_FAILURE] the Libraries differ: {json.dumps(diff)[:250]}")
    raise SystemExit(0)
print(json.dumps(diff))
