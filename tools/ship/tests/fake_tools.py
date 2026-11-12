"""Stand-ins for Vulture and mutmut 3 in the tests. Same output shapes; what they report follows the
source text: every `def unused_*` is dead code, and every mutant a run was asked for survives."""

import re
import sys
from pathlib import Path

tool = sys.argv[1]
if tool == "vulture":
    found = 0
    for path in sorted(Path(".").rglob("*.py")):
        for n, line in enumerate(path.read_text("utf-8").splitlines(), 1):
            hit = re.match(r"def (unused_\w+)", line)
            if hit:
                found += 1
                print(f"{path}:{n}: unused function '{hit.group(1)}' (60% confidence)")
    sys.exit(3 if found else 0)
if tool == "mutmut-run":
    Path(".fake-mutmut").write_text("\n".join(sys.argv[2:]), "utf-8")
elif tool == "mutmut-results":
    for glob in Path(".fake-mutmut").read_text("utf-8").split():
        print(f"    {glob.replace('*', '1')}: survived")
        print(f"    {glob.replace('*', '2')}: killed")
