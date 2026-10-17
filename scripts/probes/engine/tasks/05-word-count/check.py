import json
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "top.json"
if not path.exists():
    sys.exit("top.json missing")
try:
    got = json.loads(path.read_text(encoding="utf-8"))
except ValueError as error:
    sys.exit(f"not JSON: {error}")
if got != {"the": 5, "cat": 3, "dog": 3}:
    sys.exit(f"wrong counts: {got}")
