"""Build PLAN.md from the part files, then run both checks and embed their output.

Run from anywhere: <python> -I assemble.py
PR sections come from prs-a.txt, prs-b.txt and prs-c.txt. Generated parts are the dispatch table,
Appendix C (who can run beside whom), F (swap ledger), G (coverage) and K (check output).
"""

import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
BUILD = HERE.parent
TREE = "D:/QMX-worktrees/bld-repair-24"
SEEDS = HERE.parent.parent / "SEEDS-2.md"
PYTHON = sys.executable
RULE = "Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked."
PREFIX = {
    "{QT}": "qml/tests",
    "{QB}": "qmb/src/qmb",
    "{BT}": "qmb/tests",
    "{Q}": "qml/src/qml",
    "{NT}": "qmn/tests",
    "{N}": "qmn/src/qmn",
    "{RT}": "packages/qmf-risk/tests",
    "{R}": "packages/qmf-risk/src/qmf/risk",
    "{D}": "packages/qmf-data/src/qmf/data",
    "{H}": "qmx-agents/packages/qmx-host/src/qmx_host",
    "{T}": "qmx-agents/packages/qmx-tools/src/qmx_tools",
    "{CTL}": "qmx-agents/packages/qmx-control/src/qmx_control",
    "{LIB}": "qmx-agents/packages/qmx-library/src/qmx_library",
    "{APP}": "qmx-agents/packages/qmx-apps/src/qmx_apps",
    "{AT}": "qmx-agents/packages/qmx-apps/tests",
    "{APPS}": "qmx-agents/apps",
    "{ENG}": "qmx-agents/packages/qmx-engine/src/qmx_engine/templates",
}
SINGLE = {"stop", "slice", "what", "read", "gates", "depends", "see", "lens", "fact", "perf", "lane3"}
STOP_NAME = {"A": "Stop A, one unit trades on paper", "B": "Stop B, the whole single-unit baseline", "C": "Stop C, groups, pods and shipping", "D": "After stop C, the demo facts"}


def parse():
    prs = []
    for name in ("prs-a.txt", "prs-b.txt", "prs-c.txt"):
        current = None
        for raw in (HERE / name).read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            if raw.startswith("@@ "):
                pr, title = raw[3:].split(" | ", 1)
                current = {"id": pr, "title": title, "new": [], "edit": [], "build": [], "test": [], "swaps": [], "fault": []}
                prs.append(current)
                continue
            key, value = raw.split(": ", 1)
            for short, long in PREFIX.items():
                value = value.replace(short, long)
            if key in SINGLE:
                current[key] = value
            elif key in ("swaps", "fault"):
                current[key] += value.split()
            else:
                current[key].append(value)
    return prs


def suites(pr):
    found = []
    for path in pr["edit"] + pr["new"]:
        if path.startswith("qml/"):
            found.append("qml/tests")
            if path.startswith("qml/src/"):
                found += ["qmb/tests -k unit", "qmn/tests/test_app_runtime.py"]
        elif path.startswith("qmb/"):
            found.append("qmb/tests -k unit")
        elif path.startswith("qmn/"):
            found.append("qmn/tests -k app")
        elif path.startswith("tools/"):
            found.append("tools/tests")
        else:
            m = re.match(r"(packages/[^/]+|qmx-agents/packages/[^/]+|qmx-agents/apps/[^/]+)/", path)
            if m:
                found.append(m.group(1) + "/tests")
    return list(dict.fromkeys(found))


def section(pr):
    low = pr["id"].lower().replace("-", "")
    out = [f"## {pr['title']} ({pr['id']})", ""]
    out.append(f"{STOP_NAME[pr['stop']]}. Slice {pr['slice']}. **What it does.** {pr['what']}")
    out.append("")
    out.append(f"**Read.** {pr['read']}")
    out.append("")
    out.append(f"**Gates and fallbacks.** {pr['gates']}")
    out.append("")
    if pr["swaps"]:
        out += [f"**Swaps.** {' '.join(pr['swaps'])}.", ""]
    depends = pr["depends"]
    out += [f"**Depends on.** {'Nothing beyond the stack root.' if depends == 'none' else depends + '.'}", ""]
    out += ["**Files.**", ""]
    out += [f"- [ ] Edit `{p}`." for p in pr["edit"]] + [f"- [ ] Create `{p}`." for p in pr["new"]]
    out += ["", "**Build.**", ""] + [f"- [ ] {b}" for b in pr["build"]]
    out += ["", "**You see.**", "", f"- [ ] {pr['see']}"]
    out += ["", f"**Verify, unit.** {RULE}", ""] + [f"- [ ] {t}" for t in pr["test"]]
    out += ["", f"**Verify, live.** {RULE} Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.", ""]
    scenario, slug, passes = [s.strip() for s in pr["lane3"].split(" | ")]
    named = ", ".join(f"`{s}`" for s in suites(pr))
    out += [
        f"- [ ] Lane 1. Touched suites at the head, {named}, and rerun at the parent only a test that failed. Save `{low}-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.",
        f"- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `{low}-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.",
        f"- [ ] Lane 3. {scenario}. Save `{low}-{slug}.log`. Pass when {passes}.",
        f"- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `{low}-fact.log`. Pass when the script exits 0 and prints the fact.",
        f"- [ ] Lane 5. Run the PR's new tests three times in a row. Save `{low}-repeat.log`. Pass when the three runs agree.",
        f"- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `{low}-leak.log`. Pass when none appears.",
        f"- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `{low}-boot.log`. Pass when it answers and stops clean.",
        f"- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `{low}-scans.log`. Pass when both exit 0.",
        f"- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `{low}-k7.log`. Pass when it ends in a filled paper entry.",
        f"- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `{low}-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.",
    ]
    perf = pr.get("perf", "Wall time of this PR's new tests, recorded, no fail rule.")
    out += ["", f"**Verify, perf.** {RULE}", "", f"- [ ] Metric. {perf}", "- [ ] Probe. Time the run at the parent and the head, interleaved.", "- [ ] Baseline. The parent's value, measured first.", "- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail."]
    out += ["", f"**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses {pr['lens']}. The blast-radius fact is this. {pr['fact']}", ""]
    out += [
        f"- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/{low}-check-<head8>.md`, first line CLEAN or NOT CLEAN.",
        "- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.",
    ]
    out += ["", "**Merge.**", "", "- [ ] The CLEAN verdict at the exact head, or after the one fix round.", "- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.", "- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.", "", ""]
    return "\n".join(out)


def dispatch(prs):
    rows = ["| # | Id | Stop | PR | Depends on |", "|---|---|---|---|---|"]
    for n, pr in enumerate(prs, 1):
        rows.append(f"| {n} | {pr['id']} | {pr['stop']} | {pr['title']} | {pr['depends']} |")
    return "\n".join(rows)


def closure(prs):
    deps = {p["id"]: re.findall(r"RC-\d+", p["depends"]) for p in prs}
    cache = {}

    def up(pr):
        if pr not in cache:
            found = set()
            for d in deps[pr]:
                found.add(d)
                found |= up(d)
            cache[pr] = found
        return cache[pr]

    return {p: up(p) for p in deps}


def beside(prs):
    up = closure(prs)
    files = {p["id"]: set(p["edit"]) | set(p["new"]) for p in prs}
    rows = ["| PR | Can run beside (neither depends on the other, no shared path) | Shares a path with | The shared paths |", "|---|---|---|---|"]
    for p in prs:
        me = p["id"]
        free, clash, paths = [], [], set()
        for q in prs:
            other = q["id"]
            if other == me:
                continue
            shared = files[me] & files[other]
            if shared:
                clash.append(other)
                paths |= shared
            elif other not in up[me] and me not in up[other]:
                free.append(other)
        rows.append(f"| {me} | {', '.join(free) or 'none'} | {', '.join(clash) or 'none'} | {', '.join(f'`{x}`' for x in sorted(paths)[:4])}{' and more' if len(paths) > 4 else ''} |")
    return "\n".join(rows)


def ledger(prs):
    table = {}
    for line in (HERE / "ledger.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            key, name, verdict, none = [c.strip() for c in line.split(" | ")]
            table[key] = (name, verdict, none)
    rows = ["| Row | What | Verdict | PR |", "|---|---|---|---|"]
    for key, (name, verdict, none) in table.items():
        tag = key.replace("PH ", "PH").replace("`streams_not_built`", "STREAMS")
        named = [p["id"] for p in prs if tag in p["swaps"]]
        rows.append(f"| {key} | {name} | {verdict} | {', '.join(named) if named else none} |")
    return "\n".join(rows)


def coverage(prs):
    text = SEEDS.read_text(encoding="utf-8")
    words = dict(re.findall(r"\*\*(H-\d+)\*\* ([^.\"]+)", text))
    rows = ["| Line | What he asked | Held by |", "|---|---|---|"]
    for line in (HERE / "coverage.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            key, *rest = [c.strip() for c in line.split(" | ")]
            if key.startswith("H-"):
                what, who = words.get(key, "").strip(), rest[0]
            else:
                what, who = rest[0], rest[1]
            rows.append(f"| {key} | {what.replace('|', '/').replace(': ', ', ').rstrip(':,')} | {who} |")
    return "\n".join(rows)


def main():
    prs = parse()
    head = (HERE / "00-head.md").read_text(encoding="utf-8").replace("{{DISPATCH}}", dispatch(prs)).replace("{{COUNT}}", str(len(prs)))
    tail = (HERE / "90-tail.md").read_text(encoding="utf-8")
    tail = tail.replace("{{BESIDE}}", beside(prs)).replace("{{LEDGER}}", ledger(prs)).replace("{{COVERAGE}}", coverage(prs))
    body = head + "\n" + "".join(section(p) for p in prs) + tail
    out = BUILD / "PLAN.md"
    out.write_text(body.replace("{{CHECK}}", "pending"), encoding="utf-8", newline="\n")
    check = subprocess.run([PYTHON, "-I", str(HERE / "check_program.py"), str(out), TREE, str(SEEDS)], capture_output=True, text=True)
    skill = subprocess.run(["node", "C:/Users/Mubarak/.claude/skills/poteto-mode/scripts/check-plan.mjs", str(out)], capture_output=True, text=True)
    skill_last = (skill.stdout.strip().splitlines() or [""])[-1]
    combined = check.stdout + check.stderr + f"\ncheck-plan.mjs: {skill_last}\n"
    out.write_text(body.replace("{{CHECK}}", combined.strip()), encoding="utf-8", newline="\n")
    print(combined)
    if skill.stderr.strip():
        print(skill.stderr[:6000])
    return 1 if check.returncode or skill.returncode else 0


sys.exit(main())
