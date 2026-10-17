import sys
from pathlib import Path

total = Path(sys.argv[1]) / "total.txt"
if not total.exists():
    sys.exit("total.txt missing")
if total.read_text(encoding="utf-8").strip() != "525.10":
    sys.exit(f"wrong total: {total.read_text(encoding='utf-8')!r}")
