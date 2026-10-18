import importlib.util
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "stats.py"
if not path.exists():
    sys.exit("stats.py missing")
spec = importlib.util.spec_from_file_location("stats_under_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cases = [
    (module.mean([1, 2, 3, 4]), 2.5),
    (module.median([5, 1, 3]), 3),
    (module.median([4, 1, 3, 2]), 2.5),
    (module.median([9, 7, 8]), 8),
]
if any(got != want for got, want in cases):
    sys.exit(f"wrong results: {cases}")
