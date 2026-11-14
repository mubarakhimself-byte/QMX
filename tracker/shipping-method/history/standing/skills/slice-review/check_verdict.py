"""Check a slice verdict file against REVIEW.md's shape, using the ship scripts' own END and CLEAN checks.

    python check_verdict.py --ship <ship package folder> <verdict.md> <full head sha> <dispatch id>

Prints one line per rule, OK or FAIL, and exits 1 on any FAIL.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SECTIONS = ["Important", "Nits", "Pre-existing", "Safety fact at the head", "Rubric", "Fix at the source"]
FINDING_SECTIONS = {"Important": "I", "Nits": "N", "Pre-existing": "P"}
RUBRIC = ["right thing", "real tests", "callers covered", "scope", "fixed lines safe", "checks honest", "readable"]
MAX_NITS = 5
TITLE = re.compile(r"^# Review \S+ at [0-9a-f]{8}, round (\d+|range)$")
COUNT = re.compile(r"^(\d+) Important, (\d+) Nits?, (\d+) Pre-existing\.$")
FILE_LINE = re.compile(r"[\w./\\-]+\.\w+:\d+")
ROUND1 = re.compile(r"^- I\d+ (FIXED|STANDS|DISPUTE accepted|DISPUTE upheld)\b.*Evidence:")


def sections(lines: list[str]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    current = None
    for line in lines:
        if line.startswith("## "):
            current = line[3:].strip()
            found[current] = []
        elif current and line.strip() and not line.startswith(("VERDICT:", "END ")):
            found[current].append(line.strip())
    return found


def check(path: Path, sha: str, dispatch_id: str) -> list[tuple[bool, str]]:
    from ship.evidence import CLEAN, end_problem

    out: list[tuple[bool, str]] = []
    problem = end_problem(path, sha, dispatch_id)
    out.append((problem is None, problem or "END line is last and names this head and dispatch id"))
    if not path.is_file():
        return out
    lines = path.read_text("utf-8", errors="replace").splitlines()
    body = [ln.strip() for ln in lines if ln.strip()]

    title = TITLE.match(body[0]) if body else None
    out.append((title is not None, "title reads '# Review <slice> at <head8>, round <n>'"))
    round_label = title.group(1) if title else "1"

    secs = sections(lines)
    missing = [s for s in SECTIONS if s not in secs]
    if round_label not in ("1", "range"):
        missing += [] if "Round 1" in secs else ["Round 1"]
    out.append((not missing, f"sections present{': missing ' + ', '.join(missing) if missing else ''}"))
    empty = [s for s, rows in secs.items() if not rows]
    out.append((not empty, f"no empty section (write 'none'){': ' + ', '.join(empty) if empty else ''}"))

    counts = {}
    for name, prefix in FINDING_SECTIONS.items():
        rows = [r for r in secs.get(name, []) if r.lower() != "none"]
        counts[name] = len(rows)
        bad = [r for r in rows if not (re.match(rf"^- {prefix}\d+ ", r) and FILE_LINE.search(r) and "Evidence:" in r)]
        out.append((not bad, f"{name}: each line is '- {prefix}<n> <file>:<line> ... Evidence: ...'"
                     + (f"; bad: {bad[0][:80]}" if bad else "")))
    bad_blocker = [r for r in secs.get("Important", []) if r.lower() != "none" and not re.search(r"\(blocker [1-7]\)", r)]
    out.append((not bad_blocker, "each Important names its blocker number 1-7"))
    out.append((counts["Nits"] <= MAX_NITS, f"{counts['Nits']} Nits, at most {MAX_NITS}"))

    count_line = body[1] if len(body) > 1 else ""
    want = (counts["Important"], counts["Nits"], counts["Pre-existing"])
    m = COUNT.match(count_line)
    if m:
        ok = tuple(int(g) for g in m.groups()) == want
    else:
        ok = count_line == "Nothing needs fixing." and want[0] == 0 and want[1] == 0
    out.append((ok, f"count line '{count_line[:60]}' matches sections {want}"))

    verdicts = [ln for ln in body if ln.startswith("VERDICT:")]
    out.append((len(verdicts) == 1 and verdicts[0] in (CLEAN, "VERDICT: BLOCKED"),
                f"exactly one VERDICT line, CLEAN or BLOCKED (found {len(verdicts)})"))
    clean = verdicts == [CLEAN]
    out.append((clean == (counts["Important"] == 0), "VERDICT is CLEAN exactly when Important is none"))

    rubric = " ".join(secs.get("Rubric", [])).lower()
    absent = [r for r in RUBRIC if not re.search(rf"{re.escape(r)}\W+(pass|fail)\b", rubric)]
    out.append((not absent, "rubric gives pass or fail for all seven lines"
                 + (f"; missing: {', '.join(absent)}" if absent else "")))

    safety = " ".join(secs.get("Safety fact at the head", []))
    out.append(("matches the brief" in safety or "differs" in safety, "safety section says 'matches the brief' or 'differs'"))

    if "Round 1" in secs:
        bad = [r for r in secs["Round 1"] if not ROUND1.match(r)]
        out.append((not bad, "Round 1: each line is '- I<n> FIXED|STANDS|DISPUTE accepted|DISPUTE upheld ... Evidence: ...'"))
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--ship", required=True, help="the ship package folder, e.g. D:/QMX-worktrees/ship-kit/tools/ship")
    p.add_argument("verdict", type=Path)
    p.add_argument("sha")
    p.add_argument("dispatch_id")
    a = p.parse_args(argv)
    sys.path.insert(0, str(Path(a.ship).resolve().parent))
    results = check(a.verdict, a.sha, a.dispatch_id)
    for ok, what in results:
        print(("OK   " if ok else "FAIL ") + what)
    return 0 if all(ok for ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
