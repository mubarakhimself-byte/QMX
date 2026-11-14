"""Stand-ins for Vulture, Skylos, mutmut 3 and pyright in the tests. Same output shapes; what they report
follows the source text: every `def unused_*` is dead code, every mutant a run was asked for survives, every
line holding `# type-error` is a pyright error (printed over two lines, as pyright prints a long one), and
Skylos prints the JSON report the checkout holds in `fake-skylos.json` (an empty one without it)."""

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
if tool == "skylos":
    report = Path("fake-skylos.json")
    print("scanning ...")
    print(report.read_text("utf-8") if report.exists() else "{}")
    sys.exit(0)
if tool == "pyright":
    errors = 0
    for path in sorted(Path(".").rglob("*.py")):
        full = str(path.resolve())
        hits = [n for n, line in enumerate(path.read_text("utf-8").splitlines(), 1) if "# type-error" in line]
        if hits:
            print(full)
        for n in hits:
            errors += 1
            print(f"  {full}:{n}:5 - error: Argument count 2 is wrong")
            print('    "int" is not "str" (reportCallIssue)')
    print(f"{errors} error{'' if errors == 1 else 's'}, 0 warnings, 0 informations ")
    sys.exit(1 if errors else 0)
if tool == "mutmut-run":
    Path(".fake-mutmut").write_text("\n".join(sys.argv[2:]), "utf-8")
elif tool == "mutmut-results":
    for glob in Path(".fake-mutmut").read_text("utf-8").split():
        print(f"    {glob.replace('*', '1')}: survived")
        print(f"    {glob.replace('*', '2')}: killed")
