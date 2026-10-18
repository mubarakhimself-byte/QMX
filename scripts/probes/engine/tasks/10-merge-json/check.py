import json
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "merged.json"
if not path.exists():
    sys.exit("merged.json missing")
try:
    got = json.loads(path.read_text(encoding="utf-8"))
except ValueError as error:
    sys.exit(f"not JSON: {error}")
want = {
    "name": "svc",
    "port": 9000,
    "db": {"host": "localhost", "pool": 20, "ssl": True},
    "tags": ["c"],
}
if got != want:
    sys.exit(f"wrong merge: {got}")
