"""Check PLAN.md's program facts by reading the assembled file and the code tree.

Run: <python> -I check_program.py PLAN.md D:/QMX-worktrees/bld-repair-24 ../../SEEDS-2.md
Prints PASS or FAIL per check and exits non-zero on any FAIL. Standard library only.
"""

import pathlib
import re
import subprocess
import sys

plan_path, tree, seeds_path = sys.argv[1:4]
plan = pathlib.Path(plan_path).read_text(encoding="utf-8")
tree_path = pathlib.Path(tree)
head = subprocess.run(
    ["git", "-C", tree, "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True
).stdout.strip()

failures = 0


def report(ok, name, detail=""):
    global failures
    if not ok:
        failures += 1
    print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + detail if detail else ''}")


sections = {}
for match in re.finditer(r"^## ([^\n]+) \((RC-\d+)\)\n(.*?)(?=^## )", plan, re.M | re.S):
    sections[match.group(2)] = match.group(3)
ids = list(sections)
print(f"INFO {len(ids)} PR sections, code tree {tree} at {head}")

deps = {}
for pr, body in sections.items():
    line = re.search(r"^\*\*Depends on\.\*\* (.+)$", body, re.M).group(1)
    deps[pr] = re.findall(r"RC-\d+", line)

missing = [(p, d) for p, ds in deps.items() for d in ds if d not in sections]
report(not missing, "every dependency names a PR that exists", str(missing) if missing else f"{sum(map(len, deps.values()))} edges")

later = [(p, d) for p, ds in deps.items() for d in ds if d in sections and ids.index(d) >= ids.index(p)]
report(not later, "no PR depends on itself or a later PR, so no cycle exists", str(later) if later else "")

state = {}
cycle = []


def visit(node, trail):
    if state.get(node) == 2:
        return
    if state.get(node) == 1:
        cycle.append(trail + [node])
        return
    state[node] = 1
    for dep in deps.get(node, []):
        visit(dep, trail + [node])
    state[node] = 2


for pr in ids:
    visit(pr, [])
report(not cycle, "a depth-first walk of the graph finds no cycle", str(cycle[:2]) if cycle else "")

closure = {}


def ancestors(pr):
    if pr not in closure:
        found = set()
        for dep in deps.get(pr, []):
            found.add(dep)
            found |= ancestors(dep)
        closure[pr] = found
    return closure[pr]


edits, creates = {}, {}
for pr, body in sections.items():
    block = re.search(r"^\*\*Files\.\*\*\n(.*?)^\*\*Build\.\*\*", body, re.M | re.S).group(1)
    edits[pr] = re.findall(r"- \[ \] Edit `([^`]+)`", block)
    creates[pr] = re.findall(r"- \[ \] Create `([^`]+)`", block)

made_by = {}
for pr in ids:
    for path in creates[pr]:
        made_by.setdefault(path, []).append(pr)

new_exists = [(p, f) for p in ids for f in creates[p] if (tree_path / f).exists()]
report(not new_exists, "every path marked new is absent from the code tree", str(new_exists) if new_exists else f"{sum(map(len, creates.values()))} new paths")

double = {f: p for f, p in made_by.items() if len(p) > 1}
report(not double, "no path is created twice", str(double) if double else "")

bad_edits = []
early_edits = 0
for pr in ids:
    for path in edits[pr]:
        if (tree_path / path).exists():
            continue
        makers = made_by.get(path, [])
        if any(m in ancestors(pr) for m in makers):
            early_edits += 1
        else:
            bad_edits.append((pr, path, makers))
report(
    not bad_edits,
    "every edited path exists in the tree or is created by a PR this one depends on",
    "\n     ".join(map(str, bad_edits)) if bad_edits else f"{sum(map(len, edits.values()))} edits, {early_edits} on paths an earlier PR creates",
)

appendix_f = re.search(r"^## Appendix F\..*?(?=^## Appendix G)", plan, re.M | re.S).group(0)
required = [f"PH {n}" for n in range(1, 32)] + [f"E{n}" for n in range(1, 19)]
rows = {}
for line in appendix_f.splitlines():
    cells = [c.strip() for c in line.strip("|").split("|")]
    if len(cells) >= 4 and re.match(r"^(PH \d+|E\d+[a-c]?|`streams_not_built`)$", cells[0]):
        rows[cells[0]] = cells
absent, unrouted = [], []
for key in required:
    found = [r for k, r in rows.items() if k == key or re.fullmatch(key + r"[a-c]", k)]
    if not found:
        absent.append(key)
        continue
    for row in found:
        named = re.findall(r"RC-\d+", row[3])
        if not named and not row[3].lower().startswith("none"):
            unrouted.append(row[0])
        if any(n not in sections for n in named):
            unrouted.append(row[0])
report(not absent and not unrouted, "swap ledger holds all 31 placeholders and 18 sockets, each with a PR or a stated none", f"absent {absent} unrouted {unrouted}" if absent or unrouted else f"{len(rows)} rows")

named_in_prs = {}
for pr, body in sections.items():
    for tag in re.findall(r"^\*\*Swaps\.\*\* (.*?)\.$", body, re.M):
        for item in tag.split():
            named_in_prs.setdefault(item, []).append(pr)
mismatch = []
for key, row in rows.items():
    tag = key.replace("PH ", "PH").replace("`streams_not_built`", "STREAMS")
    listed = set(re.findall(r"RC-\d+", row[3]))
    declared = set(named_in_prs.get(tag, []))
    if listed != declared:
        mismatch.append((key, sorted(listed), sorted(declared)))
report(not mismatch, "each ledger row names exactly the PRs whose sections declare that swap", str(mismatch) if mismatch else "")

seeds = pathlib.Path(seeds_path).read_text(encoding="utf-8")
wanted = re.findall(r"\*\*(H-\d+)\*\*", seeds)
appendix_g = re.search(r"^## Appendix G\..*?(?=^## Appendix H)", plan, re.M | re.S).group(0)
covered = {}
for line in appendix_g.splitlines():
    cells = [c.strip() for c in line.strip("|").split("|")]
    if cells and re.match(r"^(H-\d+|Old \d+)$", cells[0]):
        covered[cells[0]] = cells
lost = [h for h in wanted if h not in covered]
empty = [k for k, c in covered.items() if not c[2]]
ghost = [k for k, c in covered.items() for n in re.findall(r"RC-\d+", c[2]) if n not in sections]
report(not lost and not empty and not ghost, "coverage table holds every H line of SEEDS-2 Part C, each with a PR or a named session", f"lost {lost} empty {empty} ghost {ghost}" if lost or empty or ghost else f"{len(wanted)} H lines, {len(covered) - len(wanted)} older lines")

appendix_i = re.search(r"^## Appendix I\..*?(?=^## Appendix J)", plan, re.M | re.S).group(0)
fault_rows = [
    [c.strip() for c in line.strip("|").split("|")]
    for line in appendix_i.splitlines()
    if line.startswith("| ") and "RC-" in line
]
fault_bad = []
for row in fault_rows:
    pr = re.search(r"RC-\d+", row[1]).group(0)
    test = row[2].strip("`")
    if test not in sections[pr]:
        fault_bad.append((row[0], pr, test))
report(not fault_bad and len(fault_rows) > 0, "every proven fault of CHECK.md names a test that sits in its PR's acceptance tests", str(fault_bad) if fault_bad else f"{len(fault_rows)} faults")

no_literal = [p for p in ids if not re.search(r"\*\*Verify, unit\.\*\*.*?`test_|`test_shipped_apps", sections[p], re.S)]
report(not no_literal, "every PR names at least one acceptance test", str(no_literal) if no_literal else "")

print(f"RESULT {'FAIL' if failures else 'PASS'}: {failures} failed checks")
sys.exit(1 if failures else 0)
