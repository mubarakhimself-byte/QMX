import csv
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "big.csv"
if not path.exists():
    sys.exit("big.csv missing")
with path.open(encoding="utf-8", newline="") as handle:
    rows = [row for row in csv.reader(handle) if row]
want = [
    ["symbol", "qty", "price"],
    ["GBPUSD", "150", "1.27"],
    ["USDJPY", "101", "151.2"],
    ["XAUUSD", "250", "2380.5"],
]
if rows != want:
    sys.exit(f"wrong rows: {rows}")
