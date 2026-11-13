"""ship phase: which step a program folder is at, and the values that step needs (FACTORY-DESIGN 11.7).

`read` applies the 20 rules of 11.7 in order and returns `key: value` pairs. It reads files only:
PROGRAM.yaml, phase.json, SLICES.md, plan-review/REVIEW.md, state.json, notes/stop-<X>.json,
stop-review/<X>/REVIEW.md and REVIEW-2.md, merge/<X>.md, docs/<X>.json, chain.lock, WAITING.md and
notes/WAITS-ON-YOU.md. `set_phase` is the one writer of phase.json.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from ship import program as prog
from ship import state as st
from ship.layout import Program
from ship.plan import PlanError, parse_slices
from ship.proc import pid_alive
from ship.settings import Settings

NEXT_WORDS = ("intake", "plan", "audit", "sweep-handoff", "review", "planner-fix", "go", "arm", "later-handoff",
              "build", "checkpoint-review", "waits", "merge", "docs", "done")
AUDIT_STAGES = ("census", "intent", "intent-check", "quality", "judgement", "verdicts", "audit-handoff")
PLAN_STAGES = ("expand", "ground", "challenge", "anneal", "subtract", "architect", "technical", "cut", "handoff")
WORDS = NEXT_WORDS + AUDIT_STAGES + PLAN_STAGES
PHASE_STATUSES = ("running", "done", "waits")
UNANSWERED = re.compile(r"^\s*-\s\[\s\]\s", re.M)


def _read(path: Path) -> str:
    return path.read_text("utf-8", errors="replace") if path.exists() else ""


def verdict(path: Path) -> tuple[str, str]:
    """(CLEAN|BLOCKED|"", the END sha or "") of a stop review file, as phase_state.py read it."""
    text = _read(path)
    v = re.search(r"VERDICT:\s*(CLEAN|BLOCKED)", text)
    end = re.search(r"^END\s+([0-9a-f]{7,40})\s", text, re.M)
    return (v.group(1) if v else ""), (end.group(1) if end else "")


def review_result(path: Path) -> str:
    """The last `RESULT: CLEAN|FIXES|QUESTIONS` line of plan-review/REVIEW.md, or ""."""
    found = re.findall(r"^RESULT:\s*(CLEAN|FIXES|QUESTIONS)\b", _read(path), re.M)
    return found[-1] if found else ""


def stop_tip(program: Program, stop: str) -> str:
    """The built tip of a stop: notes/stop-<X>.json's `tip`, or a legacy notes/stop-<X>.md's 40-char sha."""
    note = program.stop_note(stop)
    if note.exists():
        try:
            return str(json.loads(_read(note)).get("tip") or "")
        except json.JSONDecodeError:
            return ""
    m = re.search(r"\b([0-9a-f]{40})\b", _read(program.notes_dir / f"stop-{stop}.md"))
    return m.group(1) if m else ""


def conveyor(program: Program) -> tuple[bool, str]:
    """(alive, words) for chain.lock: alive when its pid runs."""
    text = _read(program.chain_lock)
    if not text.strip():
        return False, "none"
    try:
        pid = int(json.loads(text).get("pid") or 0)
    except (json.JSONDecodeError, AttributeError, ValueError, TypeError):
        return False, "unreadable chain.lock"
    return (True, f"alive {pid}") if pid_alive(pid) else (False, f"dead {pid}")


def open_questions(program: Program) -> str:
    """The first file holding an unanswered `- [ ]` line, or ""."""
    for path in (program.waiting, program.waits):
        if UNANSWERED.search(_read(path)):
            return path.as_posix()
    return ""


def phase_json(program: Program) -> dict:
    try:
        return json.loads(_read(program.phase_file) or "{}")
    except json.JSONDecodeError:
        return {}


def set_phase(program: Program, phase: str, status: str, by: str) -> dict:
    """Write phase.json whole, then replace it."""
    if status not in PHASE_STATUSES:
        raise ValueError(f"status {status!r}; want one of {list(PHASE_STATUSES)}")
    record = {"phase": phase, "status": status, "at": st.now_iso(), "by": by}
    tmp = program.phase_file.with_suffix(".json.tmp")
    program.dir.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(record) + "\n", "utf-8", newline="\n")
    os.replace(tmp, program.phase_file)
    return record


def _merge_word(program: Program, stop: str) -> str:
    text = _read(program.merge_note(stop))
    if re.search(r"^MERGED\s+[0-9a-f]{7,40}", text, re.M):
        return "MERGED"
    if re.search(r"^EMPTY\b", text, re.M):
        return "EMPTY"
    return ""


def _reviewed_tip(program: Program, stop: str) -> str:
    """The END sha of the stop's last CLEAN verdict, or ""."""
    for name in ("REVIEW-2.md", "REVIEW.md"):
        v, end = verdict(program.stop_review(stop) / name)
        if v:
            return end if v == "CLEAN" else ""
    return ""


def read(program: Program, settings: Settings) -> dict:
    out: dict[str, str] = {"program": program.dir.name, "project": "", "kind": "", "folder": program.dir.as_posix()}
    alive, words = conveyor(program)
    questions = open_questions(program)

    def done(nxt: str, why: str, wait: bool = False, **extra: str) -> dict:
        out["next"], out["why"] = nxt, why
        if out.get("status") != "abandoned":
            if wait or questions:
                out["status"] = "waits-on-him"
            elif alive:
                out["status"] = "running"
            elif nxt == "done":
                out["status"] = "done"
            else:
                out["status"] = "idle"
        out["conveyor"] = words
        for key, value in extra.items():
            if value:
                out[key] = value
        if questions:
            out["waits"] = questions
        return out

    if not program.project_file.exists():
        return done("intake", "no PROGRAM.yaml")
    try:
        index = prog.load(program)
    except prog.ProgramError as exc:
        return done("waits", f"{exc}; the planner fixes it", wait=True)
    out["program"] = index.program or program.dir.name
    out["project"] = index.project or ""
    out["kind"] = index.kind
    if index.kind == "fix" and index.parent:
        out["parent"] = (program.dir.parent / index.parent).as_posix()
    if index.abandoned:
        out["status"] = "abandoned"
        return done("done", f"abandoned: {index.abandoned}")
    stage = str(phase_json(program).get("phase") or "")
    if not program.slices_md.exists():
        if index.kind == "audit":
            return done("audit", "no SLICES.md; the audit is not handed off", stage=stage)
        if index.kind == "sweep":
            return done("sweep-handoff", "no SLICES.md; the sweep is not handed off")
        return done("plan", "no SLICES.md", stage=stage)
    if index.kind != "fix" and index.gate("go") is None:
        result = review_result(program.dir / "plan-review" / "REVIEW.md")
        if not result:
            return done("review", "gates.go is null and plan-review/REVIEW.md has no RESULT line")
        if result == "FIXES":
            return done("planner-fix", "plan review asks for fixes")
        last = index.last_gate_before_go()
        last_gate = index.gate(last) if last else None
        if result == "CLEAN" and last_gate and last_gate.get("advance") is True:
            return done("go", f"plan review is CLEAN and gates.{last} says advance: yes; the conveyor writes go")
        return done("go", f"plan review says {result}; the go gate is his", wait=True)
    if not program.state.exists():
        return done("arm", "no state.json")
    state = st.load(program)
    try:
        named = {sl.checkpoint for sl in parse_slices(_read(program.slices_md))}
    except PlanError:
        named = set(state.checkpoints())
    previous = index.parent_tip or ""
    merged_stops = []
    for stop in index.stops:
        sid = stop.id
        word = _merge_word(program, sid)
        if sid in state.merged or word == "MERGED" or stop.merged:
            previous = _reviewed_tip(program, sid) or previous
            merged_stops.append(sid)
            continue
        if word == "EMPTY":
            continue
        if stop.handoff == "deferred" and sid not in named:
            return done("later-handoff", f"stop {sid} is deferred and no slice names it", stop=sid)
        tip = stop_tip(program, sid)
        if not tip:
            return done("build", f"stop {sid} is not built (no notes/stop-{sid}.json)", stop=sid)
        if index.kind == "fix" and "parent" in out:
            return _fix_built(program, settings, out, done, sid, tip)
        v1, end1 = verdict(program.stop_review(sid) / "REVIEW.md")
        if not v1:
            return done("checkpoint-review", f"stop {sid} is built and not reviewed", stop=sid, round="1",
                        tip=tip, **{"from": previous})
        if v1 == "CLEAN":
            return done("merge", f"stop {sid} review is CLEAN", stop=sid, reviewed_tip=end1, tip=tip,
                        **{"from": previous})
        fix = program.dir.parent / f"{program.dir.name}-fix-{sid}"
        fix_tip = stop_tip(Program(fix), sid)
        if not fix_tip:
            return done("build", f"stop {sid} round 1 is BLOCKED; its fix program is not built", stop=sid,
                        build_folder=fix.as_posix(), fix_program=fix.as_posix())
        v2, end2 = verdict(program.stop_review(sid) / "REVIEW-2.md")
        if not v2:
            return done("checkpoint-review", f"stop {sid} fix program is built; round 2 is not reviewed", stop=sid,
                        round="2", tip=fix_tip, fix_program=fix.as_posix(), **{"from": previous})
        if v2 == "BLOCKED":
            return done("waits", f"stop {sid} is BLOCKED after round 2", wait=True, stop=sid, round="2",
                        fix_program=fix.as_posix())
        return done("merge", f"stop {sid} round 2 is CLEAN", stop=sid, reviewed_tip=end2, tip=fix_tip,
                    fix_program=fix.as_posix(), **{"from": previous})
    for sid in merged_stops:
        if not (program.dir / "docs" / f"{sid}.json").exists():
            return done("docs", f"stop {sid} is merged and has no docs/{sid}.json", stop=sid)
    return done("done", "every stop merged")


def _fix_built(program: Program, settings: Settings, out: dict, done, sid: str, tip: str) -> dict:
    """A built fix program goes on as its parent's stop: round 2 review, then merge, read from the parent."""
    parent = Program(Path(out["parent"]))
    if not parent.project_file.exists():
        return done("waits", f"the fix is built but its parent {parent.dir.as_posix()} has no PROGRAM.yaml",
                    wait=True, stop=sid, tip=tip)
    theirs = read(parent, settings)
    extra = {k: theirs[k] for k in ("stop", "round", "from", "tip", "reviewed_tip", "fix_program", "build_folder")
             if theirs.get(k)}
    return done(theirs["next"], f"the fix is built; parent: {theirs['why']}",
                wait=theirs["status"] == "waits-on-him", **extra)


def all_programs(plans: Path) -> list[Path]:
    return sorted(p.parent for p in plans.glob("*/PROGRAM.yaml"))
