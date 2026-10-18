import subprocess
import sys
from pathlib import Path

work = Path(sys.argv[1])
if not (work / "fizzbuzz.py").exists():
    sys.exit("fizzbuzz.py missing")
out = subprocess.run(
    [sys.executable, "fizzbuzz.py"], capture_output=True, text=True, timeout=30, cwd=work
)
want = [
    "FizzBuzz" if n % 15 == 0 else "Fizz" if n % 3 == 0 else "Buzz" if n % 5 == 0 else str(n)
    for n in range(1, 31)
]
if out.stdout.split() != want:
    sys.exit(f"wrong output: {out.stdout[:200]!r}")
