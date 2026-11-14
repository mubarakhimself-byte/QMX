"""Check that a planning program's chain holds, from his words to slices.

Usage:
  python check_chain.py <program folder> --stage <expand|ground|anneal|arch|technical|handoff>
                        [--ship D:/QMX-worktrees/ship-kit/tools/ship]

Each stage checks its own files plus every earlier stage's. Prints PASS, FAIL and INFO
lines and exits 1 on any FAIL. Shapes are defined in CHAIN.md beside this file. It reads
who decided what as data: a decision he never saw cannot pass as his, an agent cannot
"dissolve" a question, and every plan line, element and edge case must reach a brief.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = ["expand", "ground", "anneal", "arch", "technical", "handoff"]
TRANSCRIPT_DIRS = [
    Path("C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX"),
    Path("C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Documents-QMX"),
]

ASK = re.compile(r"^\s*-\s*\*\*(S\d+)\.\*\*(.*)$", re.M)
PLAN = re.compile(r"^\s*-\s*\*\*(S\d+\.[a-z]+)\*\*(.*)$", re.M)
PLAN_NEAR = re.compile(r"\*\*S\d+\.[a-z]+[^*\s]*\*\*")
EDGE = re.compile(r"^\s*-\s*\*\*(E\d+)\*\*\s*\(([^)]*)\)(.*)$", re.M)
ARCH = re.compile(r"^\s*-\s*\*\*(A\d+)\*\*\s*\(([^)]*)\)(.*)$", re.M)
CHANGE = re.compile(r"^\s*-\s*\*\*(X\d+)\*\*(.*)$", re.M)
RETIRED = re.compile(r"~~(S\d+(?:\.[a-z]+)?|A\d+|E\d+)~~\s*retired")
PLAN_ID = re.compile(r"\bS\d+\.[a-z]+\b")
ROUND = re.compile(r"^## Round (\d+) \((plan|technical) mode", re.M)
QROW = re.compile(r"^\|\s*(Q\d+)\s*\|([^|]*)\|([^|]*)\|\s*([a-z-]+)\s*\|([^|]*)\|", re.M)
NEW_Q = re.compile(r"^New questions this round:\s*(\d+)", re.M)
STOPPED = re.compile(r"^Stopped after (\d+) rounds? \((plan|technical) mode\): round (\d+) raised no new question\.", re.M)
QUOTE = re.compile(r"[\"\u201c]([^\"\u201d]*\w[^\"\u201d]*)[\"\u201d]")
TRANSCRIPT_SRC = re.compile(r"\b([0-9a-f]{8})[: ]L(\d+)")
FILE_SRC = re.compile(r"[\w./-]+\.\w+:\d+")
FOLDED = re.compile(r"\b(dissolved|folded)\b", re.I)
KINDS = {"fact", "vague", "edge", "change", "defect", "decision-his", "decision-tech", "dup"}

# Settings, not caps. Each makes a WARN line, or asks for a written reason; none refuses a plan.
SLICES_PER_ASK_WARN = 4  # above this many slices per ask, SLICES.md needs a "Growth:" line saying why
CHECKPOINT_AIM = (5, 8)  # slices per checkpoint (stop point) the planner aims for


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.failed = False

    def check(self, ok: bool, name: str, detail: str = "") -> None:
        self.failed |= not ok
        self.lines.append(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))

    def info(self, name: str, detail: str) -> None:
        self.lines.append(f"INFO {name}: {detail}")

    def warn(self, name: str, detail: str) -> None:
        self.lines.append(f"WARN {name}: {detail}")


def read(program: Path, name: str, r: Report, required: bool = True) -> str:
    path = program / name
    if required:
        r.check(path.exists(), f"file-{name}", "" if path.exists() else f"missing {path}")
    return path.read_text("utf-8", errors="replace") if path.exists() else ""


def section(text: str, title: str) -> str:
    m = re.search(rf"^##+ {re.escape(title)}[^\n]*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def norm(text: str) -> str:
    text = text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


def ship_parser(ship: Path):
    try:
        sys.path.insert(0, str(ship.parent))
        from ship.plan import parse_facts, parse_slices  # type: ignore

        return parse_facts, parse_slices
    except Exception:  # the ship kit is optional for the early stages
        return None, None


def ship_overlaps(ship: Path):
    try:
        sys.path.insert(0, str(ship.parent))
        from ship.plan import overlaps  # type: ignore

        return overlaps
    except Exception:
        return None


def transcript_turn(id8: str, line_no: int) -> str | None:
    sys.path.insert(0, str(HERE))
    from his_words import turn_text  # type: ignore

    for folder in TRANSCRIPT_DIRS:
        for path in folder.glob(f"{id8}*.jsonl"):
            with path.open(encoding="utf-8", errors="replace") as fh:
                for n, line in enumerate(fh, 1):
                    if n == line_no:
                        try:
                            return turn_text(json.loads(line), True) or ""
                        except json.JSONDecodeError:
                            return ""
    return None


def template_placeholders() -> list[str]:
    found: list[str] = []
    tmpl = HERE.parent / "templates" / "SCOPE.md"
    if tmpl.exists():
        body = re.sub(r"<!--.*?-->", "", tmpl.read_text("utf-8"), flags=re.S)
        found += re.findall(r"<[^<>\n]{3,}>", body)
    chain = HERE / "CHAIN.md"
    if chain.exists():
        block = re.search(r"## SCOPE.md additions.*?```markdown(.*?)```", chain.read_text("utf-8"), re.S)
        if block:
            found += re.findall(r"<[^<>\n]{3,}>", block.group(1))
    return sorted(set(found))


def decisions(program: Path, r: Report) -> dict[str, str]:
    folder = program / "decisions"
    out: dict[str, str] = {}
    if not folder.exists():
        return out
    for path in sorted(folder.glob("D*.md")):
        m = re.match(r"D(\d+)-", path.name)
        r.check(m is not None, f"decision-file-name-{path.name}", "name it D<n>-<slug>.md")
        if not m:
            continue
        r.check(m.group(1) not in out, f"decision-D{m.group(1)}-unique", path.name)
        out[m.group(1)] = path.read_text("utf-8", errors="replace")
    return out


def field(text: str, name: str) -> str:
    m = re.search(rf"^{name}:\s*(.+)$", text, re.M)
    return m.group(1).strip().lower() if m else ""


# ---------------------------------------------------------------- stages


def check_expand(program: Path, r: Report, ctx: dict) -> None:
    scope = read(program, "SCOPE.md", r)
    ctx["scope"] = scope
    ctx["retired"] = set(RETIRED.findall(scope))
    asks = {m.group(1): m.group(2) for m in ASK.finditer(scope)}
    ctx["asks"] = set(asks) - ctx["retired"]
    r.check(bool(ctx["asks"]), "scope-asks", ", ".join(sorted(ctx["asks"])) or "no **S1.** lines")
    restatement = section(scope, "Restatement")
    for sid, rest in asks.items():
        if sid in ctx["retired"]:
            continue
        quotes = QUOTE.findall(rest)
        own_sources = TRANSCRIPT_SRC.findall(rest) + FILE_SRC.findall(rest)
        r.check(bool(quotes) and bool(own_sources), f"ask-{sid}-quoted-and-sourced-in-his-words",
                "" if quotes and own_sources else "needs a quote and a transcript or file source; an agent note alone is not his words")
        texts = [t for t in (transcript_turn(i, int(n)) for i, n in TRANSCRIPT_SRC.findall(rest)) if t is not None]
        if texts and not FILE_SRC.findall(rest):
            pool = norm(" ".join(texts))
            for q in quotes:
                pieces = [p for p in re.split(r"\.\.\.|\u2026", norm(q)) if len(p.strip()) >= 4]
                r.check(all(p.strip() in pool for p in pieces), f"ask-{sid}-quote-matches-source", q[:60])
        if len(quotes) >= 2:
            r.check(sid in restatement, f"ask-{sid}-narrowing-in-confirm-list",
                    "two quotes: put the later reading to him under Restatement")
    r.info("ask-count", f"{len(ctx['asks'])}; each must answer the ask as given")
    if len(ctx["asks"]) > 8:
        r.info("ask-split", "more than 8 asks: propose a split into programs as a decision for him")
    r.check(QUOTE.search(section(scope, "Destination")) is not None, "destination-quotes-him")
    prose = re.sub(r"`[^`\n]*`", "", re.sub(r"<!--.*?-->", "", scope, flags=re.S))
    left = sorted(set([p for p in template_placeholders() if p in scope] + re.findall(r"<[A-Za-z][^<>\n]{0,60}>", prose)))
    r.check(not left, "scope-no-placeholders", f"{left[:3]}")
    r.check(bool(re.search(r"^Ask as given:", scope, re.M)), "ask-as-given-stated")
    r.check(bool(restatement.strip()), "restatement-section")
    r.check(bool(re.search(r"^## Out of scope", scope, re.M)), "out-of-scope-section")
    depth = re.search(r"^Expand depth:\s*\**(light|medium|deep)\b", scope, re.M)
    ctx["depth"] = depth.group(1) if depth else "medium"
    r.check(bool(depth), "expand-depth-stated", ctx["depth"])
    if ctx["depth"] != "light":
        notes = list((program / "expand").glob("*.md")) if (program / "expand").exists() else []
        r.check(bool(notes), "expand-notes-for-depth", f"{len(notes)} notes in expand/")
    for m in re.finditer(r"^\s*-\s*\*\*(P\d+)\.\*\*(.*)$", scope, re.M):
        r.check("Why:" in m.group(2) and "Would serve:" in m.group(2), f"proposal-{m.group(1)}-why-and-serves")
    ctx["decisions"] = decisions(program, r)
    for d in sorted(set(re.findall(r"\bD(\d+)\b", scope)), key=int):
        r.check(d in ctx["decisions"], f"scope-D{d}-has-file")


def check_ground(program: Path, r: Report, ctx: dict) -> None:
    ground = read(program, "GROUND.md", r)
    tip = re.search(r"^Tip:\s*([0-9a-f]{40})\b", ground, re.M)
    r.check(bool(tip), "ground-tip-sha", tip.group(1)[:8] if tip else "add 'Tip: <full sha>'")
    r.check(bool(re.search(r"^Fetch:\s*ok\b", ground, re.M)), "ground-fetch-ok", "add 'Fetch: ok <date>' after a successful fetch")
    parse_facts = ctx.get("parse_facts")
    if parse_facts:
        try:
            ids = [f.id for f in parse_facts(ground)]
        except Exception as exc:  # PlanError
            ids = []
            r.check(False, "ground-facts-parse", str(exc))
    else:
        ids = re.findall(r"^\s*```fact (\S+)", ground, re.M)
    r.check(bool(ids), "ground-facts", f"{len(ids)} fact blocks")
    r.check(len(ids) == len(set(ids)), "ground-fact-ids-unique")
    for name in ("Open items", "Removed", "Doc drift", "Fixed lines touched"):
        r.check(bool(re.search(rf"^## {name}", ground, re.M)), f"ground-section-{name.lower().replace(' ', '-')}")
    checkout = ctx.get("rerun_facts")
    if checkout and tip and parse_facts:
        import subprocess
        head = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        r.check(head == tip.group(1), "rerun-checkout-at-tip", f"{checkout} is at {head[:8]}")
        if head == tip.group(1):
            from ship.dispatch import run_facts  # type: ignore
            from ship.settings import Settings  # type: ignore

            for line in run_facts(parse_facts(ground), Path(checkout), Settings()):
                head_line, _, detail = line.partition("\n")
                r.check(line.startswith("PASS"), "rerun-" + head_line[5:], detail)
    ctx["ground_incomplete"] = bool(re.search(r"Open items:\s*incomplete", ground))
    if ctx["ground_incomplete"]:
        r.info("ground-open-items", "incomplete; must be completed before handoff")


def rounds(log: str) -> list[dict]:
    heads = list(ROUND.finditer(log))
    out = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(log)
        body = log[h.start():end]
        new = NEW_Q.search(body)
        out.append({"n": int(h.group(1)), "mode": h.group(2), "start": h.start(), "new": int(new.group(1)) if new else None})
    return out


def check_rounds(log: str, mode: str, r: Report, required: bool = True) -> None:
    rs = rounds(log)
    numbers = [x["n"] for x in rs]
    r.check(numbers == sorted(set(numbers)), "anneal-round-numbers-increase", f"{numbers}")
    mine = [x for x in rs if x["mode"] == mode]
    if not mine:
        r.check(not required, f"anneal-{mode}-rounds", "none")
        return
    last = mine[-1]
    r.check(last["new"] == 0, f"anneal-{mode}-last-round-no-new-question", f"round {last['n']}: {last['new']}")
    stops = [s for s in STOPPED.finditer(log) if s.group(2) == mode and s.start() > last["start"]]
    r.check(bool(stops), f"anneal-{mode}-stop-line-after-last-round")
    if stops:
        r.check(int(stops[-1].group(3)) == last["n"], f"anneal-{mode}-stop-names-last-round")


def check_decision_provenance(r: Report, ctx: dict, stage: str) -> None:
    for d, text in ctx["decisions"].items():
        rec, why = section(text, "Recommendation").strip(), section(text, "Why").strip()
        r.check(bool(rec) and bool(why), f"decision-D{d}-recommendation-and-why")
        r.check(not FOLDED.search(text), f"decision-D{d}-not-folded", "a question is answered or open, never dissolved")
        status, who = field(text, "Status"), field(text, "For")
        answer = section(text, "Answer").strip()
        if who.startswith("him"):
            if status.startswith("settled"):
                sourced = bool(TRANSCRIPT_SRC.search(answer)) or "(him," in answer.lower()
                r.check(bool(QUOTE.search(answer)) and sourced and "decided" not in answer.lower(),
                        f"decision-D{d}-his-answer-is-his", "settled For: him needs his quoted words with a source")
            else:
                r.info(f"decision-D{d}", "open, waits for him")
        if who.startswith("fable") and status.startswith("settled"):
            ok = re.search(r"^(Fable|Opus) decided .+ because ", answer, re.M) is not None
            r.check(ok, f"decision-D{d}-agent-answer-logged-as-agent", "log as 'Fable decided X because Y'")
        if who.startswith("fable") and not status.startswith("settled"):
            if stage in ("technical", "handoff"):
                r.check(False, f"decision-D{d}-fable-open", "run the answer-linker before leaving stage 5")
            else:
                r.info(f"decision-D{d}", "open, for the stage 5 answer-linker")


def check_anneal(program: Path, r: Report, ctx: dict) -> None:
    plan = read(program, "PLAN.md", r)
    ctx["retired"] |= set(RETIRED.findall(plan))
    lines = {m.group(1) for m in PLAN.finditer(plan)} - ctx["retired"]
    ctx["plan"] = lines
    near = [t for t in PLAN_NEAR.findall(plan) if not re.fullmatch(r"\*\*S\d+\.[a-z]+\*\*", t)]
    r.check(not near, "plan-line-shape", f"near misses {near[:3]}")
    r.check(bool(lines), "plan-lines", ", ".join(sorted(lines)) or "no **S1.a** lines")
    for pid in sorted(lines):
        r.check(pid.split(".")[0] in ctx["asks"], f"plan-{pid}-cites-a-live-ask")
    for sid in sorted(ctx["asks"]):
        r.check(any(p.startswith(sid + ".") for p in lines), f"ask-{sid}-has-plan-lines")

    edges = read(program, "EDGE-CASES.md", r)
    ctx["retired"] |= set(RETIRED.findall(edges))
    ctx["edges"] = {m.group(1) for m in EDGE.finditer(edges)} - ctx["retired"]
    for m in EDGE.finditer(edges):
        if m.group(1) in ctx["retired"]:
            continue
        refs = set(PLAN_ID.findall(m.group(2)))
        r.check(bool(refs) and refs <= lines, f"edge-{m.group(1)}-cites-plan", f"cites {sorted(refs)}")
        r.check("Must hold:" in m.group(3), f"edge-{m.group(1)}-must-hold")

    log = read(program, "ANNEAL-LOG.md", r)
    ctx["log"] = log
    qids = [m.group(1) for m in QROW.finditer(log)]
    r.check(len(qids) == len(set(qids)), "anneal-question-ids-unique", f"{len(qids)} questions")
    stray = [ln[:40] for ln in log.splitlines() if re.match(r"^\|\s*Q\d+\s*\|", ln) and not QROW.match(ln)]
    r.check(not stray, "anneal-question-row-shape", f"{stray[:2]}")
    for m in QROW.finditer(log):
        r.check(m.group(4) in KINDS, f"anneal-{m.group(1)}-kind", m.group(4))
    r.check(not FOLDED.search(log), "anneal-nothing-dissolved")
    check_rounds(log, "plan", r)
    r.check(not list((program / "rounds").glob("round-*.md")) if (program / "rounds").exists() else True,
            "anneal-no-unfinished-round", "a rounds/round-<n>.md left behind means a round did not finish")
    check_decision_provenance(r, ctx, "anneal")
    changes = read(program, "CAN-CHANGE.md", r, required=False)
    for m in CHANGE.finditer(changes):
        ok = all(k in m.group(2) for k in ("Serves:", "Callers:", "Blast radius:", "Frees:", "Decider:"))
        r.check(ok, f"change-{m.group(1)}-justified")
    ctx["changes"] = {m.group(1) for m in CHANGE.finditer(changes)}
    for m in QROW.finditer(log):
        if m.group(4) == "dup":
            target = re.search(r"dup of ([QD]\d+)", m.group(5))
            ok = bool(target) and (target.group(1) in qids or target.group(1)[1:] in ctx["decisions"])
            r.check(ok, f"anneal-{m.group(1)}-dup-target", m.group(5).strip()[:40])
    proposals = len(re.findall(r"^\s*-\s*\*\*P\d+\.\*\*", ctx["scope"], re.M))
    r.info("growth", f"{len(ctx['asks'])} asks -> {len(lines)} plan lines; {len(ctx['edges'])} edge cases; {proposals} proposals parked for him")


def check_arch(program: Path, r: Report, ctx: dict) -> None:
    arch = read(program, "arch/ARCH.md", r)
    ctx["retired"] |= set(RETIRED.findall(arch))
    elements = {m.group(1): (set(PLAN_ID.findall(m.group(2))), m.group(3)) for m in ARCH.finditer(arch)}
    elements = {k: v for k, v in elements.items() if k not in ctx["retired"]}
    ctx["arch"] = set(elements)
    r.check(bool(elements), "arch-elements", f"{len(elements)}")
    covered_plan, covered_edges = set(), set()
    for aid, (refs, rest) in elements.items():
        r.check(bool(refs) and refs <= ctx["plan"], f"arch-{aid}-cites-plan", f"cites {sorted(refs)}")
        covered_plan |= refs
        covers = re.search(r"Covers:\s*([^.]*)", rest)
        if covers:
            covered_edges |= set(re.findall(r"\bE\d+\b", covers.group(1)))
    for pid in sorted(ctx["plan"] - covered_plan):
        r.check(False, f"plan-{pid}-has-arch")
    for eid in sorted(ctx["edges"] - covered_edges):
        r.check(False, f"edge-{eid}-in-an-element-covers-field")
    ops = section(arch, "Operations")
    for point in ("Logging", "Observability", "Monitoring", "Self-recovery", "Backend operations"):
        r.check(re.search(rf"\*\*{point}:?\*\*", ops) is not None, f"arch-operations-{point.lower().replace(' ', '-')}")
    r.info("growth", f"{len(ctx['asks'])} asks -> {len(ctx['plan'])} plan lines -> {len(elements)} elements")


def check_technical(program: Path, r: Report, ctx: dict) -> None:
    log = ctx.get("log", "")
    has_tech = "decision-tech" in log or any(field(t, "Mode") == "technical" for t in ctx["decisions"].values())
    check_rounds(log, "technical", r, required=ctx["depth"] != "light" or has_tech)
    check_decision_provenance(r, ctx, "technical")


def slice_rows(slices_text: str, ids: list[str]) -> dict[str, dict]:
    header = next((ln for ln in slices_text.splitlines() if ln.lstrip().startswith("|") and "depends on" in ln.lower()), "")
    columns = [c.strip().casefold() for c in header.strip().strip("|").split("|")]
    rows = {}
    for ln in slices_text.splitlines():
        cells = [c.strip().strip("`") for c in ln.strip().strip("|").split("|")]
        if ln.lstrip().startswith("|") and len(cells) == len(columns) and cells[0] in ids:
            rows[cells[0]] = dict(zip(columns, cells))
    return rows


def check_layout(r: Report, ctx: dict, slices_text: str, parsed: list, table: dict) -> None:
    """Checkpoints of 5 to 8 slices, lanes that share no files, and slice count against the asks."""
    r.check(all("lane" in row and row["lane"] for row in table.values()) and bool(table), "slices-lane-column")
    by_id = {s.id: s for s in parsed}
    stops: dict[str, list[str]] = {}
    for sid, row in table.items():
        stops.setdefault(row.get("stop", ""), []).append(sid)
    lo, hi = CHECKPOINT_AIM
    for stop, members in stops.items():
        lanes = sorted({table[s].get("lane", "") for s in members})
        r.info(f"checkpoint-{stop}", f"{len(members)} slices in {len(lanes)} lanes")
        if len(members) > hi:
            r.warn(f"checkpoint-{stop}-size", f"{len(members)} slices; aim for {lo} to {hi}, split it ({stop}1, {stop}2)")
    overlaps = ctx.get("overlaps")
    if overlaps and by_id:
        for stop, members in stops.items():
            for i, a in enumerate(members):
                for b in members[i + 1:]:
                    if table[a].get("lane") == table[b].get("lane"):
                        continue
                    shared = overlaps(by_id[a].files, by_id[b].files)
                    r.check(not shared, f"lanes-{a}-{b}-share-no-files", f"{shared[:2]}" if shared else "")
                    if b in by_id[a].depends_on or a in by_id[b].depends_on:
                        r.warn(f"lanes-{a}-{b}-cross-lane-dependency", "one builder waits; put them in one lane")
        order = list(stops)
        for prev, nxt in zip(order, order[1:]):
            ready = [s for s in stops[nxt]
                     if not any(overlaps(by_id[s].files, by_id[p].files) for p in stops[prev])
                     and not set(by_id[s].depends_on) & set(stops[prev])]
            r.info(f"prebuild-{nxt}", f"{len(ready)} of {len(stops[nxt])} slices can be built while {prev} is reviewed")
    asks = max(len(ctx["asks"]), 1)
    ratio = len(table) / asks
    if ratio > SLICES_PER_ASK_WARN:
        r.check(bool(re.search(r"^Growth:\s*\S", slices_text, re.M)), "growth-justified",
                f"{len(table)} slices for {asks} asks ({ratio:.1f} per ask, setting {SLICES_PER_ASK_WARN}): add a 'Growth:' line saying why")
    else:
        r.info("growth-ratio", f"{ratio:.1f} slices per ask (setting {SLICES_PER_ASK_WARN})")


def check_brief_handover(r: Report, sid: str, text: str, chain: str, row: dict, program: Path) -> None:
    """The brief carries its lane and everything its merge request needs."""
    lane = re.search(r"Lane:\s*([\w-]+)", text)
    r.check(bool(lane) and lane.group(1) == row.get("lane"), f"brief-{sid}-lane-matches", lane.group(1) if lane else "no Lane:")
    mr = section(text, "11. Merge request")
    trace = re.search(r"TRACE:\s*(\S+)\s*->\s*([^>\n]+?)\s*->\s*(S\d+)", mr)
    ok = bool(trace) and trace.group(1) == sid and trace.group(3) == row.get("ask", "").strip() \
        and set(PLAN_ID.findall(trace.group(2))) <= set(PLAN_ID.findall(chain)) and bool(PLAN_ID.findall(trace.group(2)))
    r.check(ok, f"brief-{sid}-trace-line", trace.group(0) if trace else "add 'TRACE: <slice> -> <plan ids> -> <ask>' to section 11")
    for field_name in ("In plain words:", "Door:", "DOC:"):
        r.check(field_name in mr, f"brief-{sid}-merge-request-{field_name.rstrip(':').lower().replace(' ', '-')}")
    edges = section(text, "7a. Edge-case scenarios")
    for eid in re.findall(r"\bE\d+\b", chain):
        r.check(re.search(rf"^\s*-\s*{eid}\b.*\(test:", edges, re.M) is not None, f"brief-{sid}-{eid}-has-a-test")
    r.check((program / "slices" / sid / "CHAIN.md").exists(), f"brief-{sid}-chain-packet",
            "run standing/funnel/chain_packet.py <program>")


def check_handoff(program: Path, r: Report, ctx: dict) -> None:
    slices_text = read(program, "SLICES.md", r)
    parse_slices = ctx.get("parse_slices")
    ids: list[str] = []
    parsed: list = []
    if parse_slices:
        try:
            parsed = parse_slices(slices_text)
            ids = [s.id for s in parsed]
        except Exception as exc:
            r.check(False, "slices-parse", str(exc))
    else:
        ids = [c.strip("` ") for c in re.findall(r"^\|\s*(`?[\w.-]+-[\w.-]+`?)\s*\|", slices_text, re.M)]
    r.check(bool(ids), "slices", ", ".join(ids))
    table = slice_rows(slices_text, ids)
    check_layout(r, ctx, slices_text, parsed, table)
    hit_plan, hit_arch, hit_edges, cited = set(), set(), set(), set()
    for sid in ids:
        brief = program / "slices" / sid / "BRIEF.md"
        if not brief.exists():
            r.check(False, f"brief-{sid}", "missing")
            continue
        text = brief.read_text("utf-8", errors="replace")
        chain = re.search(r"^Chain:(.*)$", text, re.M)
        r.check(bool(chain), f"brief-{sid}-chain-line")
        if chain:
            plan_refs = set(PLAN_ID.findall(chain.group(1)))
            arch_refs = set(re.findall(r"\bA\d+\b", chain.group(1)))
            edge_refs = set(re.findall(r"\bE\d+\b", chain.group(1)))
            cited |= plan_refs | arch_refs | edge_refs
            r.check(bool(plan_refs) and plan_refs <= ctx["plan"], f"brief-{sid}-plan-refs", f"{sorted(plan_refs)}")
            r.check(arch_refs <= ctx["arch"], f"brief-{sid}-arch-refs", f"{sorted(arch_refs)}")
            r.check(edge_refs <= ctx["edges"], f"brief-{sid}-edge-refs", f"{sorted(edge_refs)}")
            hit_plan |= plan_refs
            hit_arch |= arch_refs
            hit_edges |= edge_refs
        done = section(text, "9. Done when")
        r.check(re.search(r"Operations:\s*\S", done) is not None, f"brief-{sid}-operations-in-done-line")
        r.check(re.search(r"Operations:.*(\(test:\s*\S|none, because)", done) is not None, f"brief-{sid}-operations-test-named")
        check_brief_handover(r, sid, text, chain.group(1) if chain else "", table.get(sid, {}), program)
    for pid in sorted(ctx["plan"] - hit_plan):
        r.check(False, f"plan-{pid}-in-a-brief")
    for aid in sorted(ctx["arch"] - hit_arch):
        r.check(False, f"arch-{aid}-in-a-brief")
    for eid in sorted(ctx["edges"] - hit_edges):
        r.check(False, f"edge-{eid}-in-a-brief")
    program_yaml = read(program, "PROGRAM.yaml", r)
    parts = program_yaml.split("\nchains:", 1)
    r.check(len(parts) == 2, "program-chains-section")
    if len(parts) == 2:
        body = parts[1]
        r.check(not re.search(r"^\s*-\s*id:", body, re.M), "chains-no-id-keys", "check_plan reads '- id:' as a stop point")
        rows = re.split(r"^\s*-\s*ask:\s*", body, flags=re.M)[1:]
        chain_asks = {row.split()[0] for row in rows if row.split()}
        r.check(chain_asks == ctx["asks"], "chains-cover-every-ask", f"chains {sorted(chain_asks)}, asks {sorted(ctx['asks'])}")
        known = {"plan": ctx["plan"], "arch": ctx["arch"], "slices": set(ids), "edge_cases": ctx["edges"]}
        for row in rows:
            for key, valid in known.items():
                m = re.search(rf"^\s*{key}:\s*\[([^\]]*)\]", row, re.M)
                for item in [x.strip() for x in (m.group(1).split(",") if m else []) if x.strip()]:
                    r.check(item in valid, f"chain-{key}-{item}-exists")
    for rid in sorted(ctx["retired"] & cited):
        r.check(False, f"retired-{rid}-still-cited")
    open_him = [d for d, t in ctx["decisions"].items() if field(t, "For").startswith("him") and not field(t, "Status").startswith("settled")]
    later = section(ctx["scope"], "Not yet specified")
    for d in open_him:
        r.check(f"D{d}" in later, f"open-D{d}-listed-under-not-yet-specified")
    r.check(not ctx.get("ground_incomplete"), "ground-open-items-complete")
    r.info("growth", f"{len(ctx['asks'])} asks -> {len(ctx['plan'])} plan lines -> {len(ctx['arch'])} elements -> {len(ids)} slices")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("program", type=Path)
    ap.add_argument("--stage", choices=STAGES, required=True)
    ap.add_argument("--ship", type=Path, default=Path("D:/QMX-worktrees/ship-kit/tools/ship"))
    ap.add_argument("--rerun-facts", type=Path, help="a clean checkout at the GROUND.md tip; reruns every fact there")
    args = ap.parse_args()
    r = Report()
    ctx: dict = {}
    ctx["parse_facts"], ctx["parse_slices"] = ship_parser(args.ship)
    ctx["overlaps"] = ship_overlaps(args.ship)
    ctx["rerun_facts"] = args.rerun_facts
    steps = [check_expand, check_ground, check_anneal, check_arch, check_technical, check_handoff]
    for step in steps[: STAGES.index(args.stage) + 1]:
        step(args.program, r, ctx)
    print("\n".join(r.lines))
    fails = sum(ln.startswith("FAIL") for ln in r.lines)
    print(f"\n{args.stage}: {'FAIL' if r.failed else 'PASS'} ({fails} failing checks)")
    return 1 if r.failed else 0


if __name__ == "__main__":
    sys.exit(main())
