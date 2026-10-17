import importlib.util
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "primes.py"
if not path.exists():
    sys.exit("primes.py missing")
spec = importlib.util.spec_from_file_location("primes_under_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cases = [(10, [2, 3, 5, 7]), (2, []), (3, [2]), (30, [2, 3, 5, 7, 11, 13, 17, 19, 23, 29])]
bad = [(n, module.primes_below(n)) for n, want in cases if list(module.primes_below(n)) != want]
if bad or len(module.primes_below(1000)) != 168:
    sys.exit(f"wrong results: {bad}")
