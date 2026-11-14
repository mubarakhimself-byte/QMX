"""Check a program folder before plan review signs it off.

    python check_plan.py <program folder> <ship kit folder, e.g. D:/QMX-worktrees/ship-kit/tools/ship>

Prints one PASS or FAIL line per check and exits 1 on any FAIL. It parses SLICES.md and every
brief with the ship scripts' own parser, so what passes here is what `ship init` and `ship dispatch`
will read. It runs no fact; GROUNDING.md does that against the code.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"<[a-z][^<>\n]*>")
SPAWNING_SKILLS = ("arena", "swarm", "interrogate", "no-comments", "code-review")
CHECKPOINT_WARN_ABOVE = 8  # setting: warn when a stop point (checkpoint) holds more slices; never a refusal


def main(program: Path, ship: Path) -> int:
    sys.path.insert(0, str(ship.parent))
    from ship.plan import PlanError, parse_facts, parse_slices

    lines: list[str] = []

    def check(ok: bool, name: str, detail: str = "") -> None:
        lines.append(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))

    slices_text = (program / "SLICES.md").read_text("utf-8")
    try:
        slices = parse_slices(slices_text)
    except PlanError as exc:
        check(False, "slices-table", str(exc))
        return report(lines)
    check(True, "slices-table", f"{len(slices)} slices")

    header = next(ln for ln in slices_text.splitlines() if ln.lstrip().startswith("|") and "depends on" in ln.lower())
    columns = [c.strip().casefold() for c in header.strip().strip("|").split("|")]
    rows = {}
    for ln in slices_text.splitlines():
        cells = [c.strip().strip("`") for c in ln.strip().strip("|").split("|")]
        if ln.lstrip().startswith("|") and len(cells) == len(columns) and cells[0] in {s.id for s in slices}:
            rows[cells[0]] = dict(zip(columns, cells))
    check({"ask", "stop"} <= set(columns), "ask-and-stop-columns")

    scope = (program / "SCOPE.md").read_text("utf-8")
    asks = set(re.findall(r"\*\*(S\d+)\.\*\*", scope))
    program_yaml = (program / "PROGRAM.yaml").read_text("utf-8")
    stops = set(re.findall(r"^\s*-\s*id:\s*(\S+)", program_yaml, re.M))
    check(bool(asks), "scope-asks", f"{sorted(asks)}")
    check(bool(stops), "program-stop-points", f"{sorted(stops)}")
    above_files = program_yaml.split("\nfiles:")[0].splitlines()
    head = "\n".join(ln.split("#")[0] for ln in above_files)
    check(not PLACEHOLDER.findall(head), "program-header-filled", f"placeholders left: {PLACEHOLDER.findall(head)}")

    for s in slices:
        row = rows.get(s.id, {})
        cited = set(re.findall(r"S\d+", row.get("ask", "")))
        check(bool(cited) and cited <= asks, f"ask-{s.id}", f"cites {sorted(cited) or 'nothing'}")
        check(row.get("stop", "") in stops, f"stop-{s.id}", f"stop {row.get('stop', '')!r}")
        brief = program / "slices" / s.id / "BRIEF.md"
        if not brief.exists():
            check(False, f"brief-{s.id}", f"missing {brief}")
            continue
        text = brief.read_text("utf-8")
        try:
            facts = parse_facts(text)
        except PlanError as exc:
            check(False, f"facts-{s.id}", str(exc))
            continue
        ids = [f.id for f in facts]
        check("SAFETY" in ids, f"safety-fact-{s.id}", f"facts {ids}")
        check(len(ids) > 1, f"code-facts-{s.id}", "at least one fact besides SAFETY")
        # Fact blocks hold real command output, which may contain <...> (Svelte, HTML): not placeholders.
        prose = re.sub(r"^```fact.*?^```", "", re.sub(r"<!--.*?-->", "", text, flags=re.S), flags=re.S | re.M)
        left = PLACEHOLDER.findall(prose)
        check(not left, f"filled-{s.id}", f"placeholders left: {left[:5]}")
        serves = set(re.findall(r"S\d+", (re.search(r"^Serves:.*$", text, re.M) or [""])[0]))
        check(serves == cited, f"brief-ask-{s.id}", f"brief serves {sorted(serves)}, SLICES.md cites {sorted(cited)}")
        spawning = [k for k in SPAWNING_SKILLS if re.search(rf"\b{re.escape(k)}\b", text)]
        check(not spawning, f"no-spawning-skills-{s.id}", f"names {spawning}")
    per_stop: dict[str, int] = {}
    for s in slices:
        stop = rows.get(s.id, {}).get("stop", "")
        per_stop[stop] = per_stop.get(stop, 0) + 1
    for stop, count in sorted(per_stop.items()):
        if count > CHECKPOINT_WARN_ABOVE:
            lines.append(f"WARN checkpoint-{stop}-size: {count} slices; aim for 5 to 8 and split it ({stop}1, {stop}2). A guide, not a refusal")
    return report(lines)


def report(lines: list[str]) -> int:
    print("\n".join(lines))
    fails = sum(ln.startswith("FAIL") for ln in lines)
    print(f"{'FAIL' if fails else 'PASS'} plan: {fails} failing checks")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
