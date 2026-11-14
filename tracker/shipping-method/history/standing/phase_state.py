"""Say which shipping phase a program is in, and the values the next phase's prompt needs.

Usage:
  python phase_state.py                 every program under D:/QMX-worktrees, one block each
  python phase_state.py <program dir>   one program

For each program it prints `key: value` lines: program, folder, next (plan, plan-review,
build, running, stop-review, merge, waits-on-him, done), why, coordinator_alive (notes/LOG.md
changed in the last 20 minutes), and where they apply stop, round,
from, tip, reviewed_tip, fix_program, parent_program, after_stop, plus the PROGRAM.yaml
header values (repo, ship, standing, worktree_root, target_branch, planner_session).
Reads files only. Standard library only.
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT = Path("D:/QMX-worktrees")
ALIVE_MINUTES = 20  # the same freshness rule STOP-REVIEW uses for notes/LOG.md
HEADER_KEYS = ["program", "repo", "build_branch", "parent_tip", "target_branch", "worktree_root",
               "ship", "standing", "planner_session", "scope_gate"]


def header(text: str) -> dict:
    head = text.split("\nfiles:")[0]
    out = {}
    for key in HEADER_KEYS:
        m = re.search(rf"^{key}:\s*(.*?)\s*(?:#.*)?$", head, re.M)
        out[key] = m.group(1).strip() if m else ""
    return out


def stops(text: str) -> list[dict]:
    block = text.split("\nstop_points:", 1)[1].split("\nfiles:")[0] if "\nstop_points:" in text else ""
    found = []
    for m in re.finditer(r"^\s*-\s*id:\s*(\S+)(.*?)(?=^\s*-\s*id:|\Z)", block, re.M | re.S):
        merged = re.search(r"merged:\s*(\S+)", m.group(2))
        found.append({"id": m.group(1), "merged": (merged.group(1) if merged else "null")})
    return found


def read(path: Path) -> str:
    return path.read_text("utf-8", errors="replace") if path.exists() else ""


def verdict(path: Path) -> tuple[str, str]:
    text = read(path)
    v = re.search(r"VERDICT:\s*(CLEAN|BLOCKED)", text)
    end = re.search(r"^END\s+([0-9a-f]{7,40})\s", text, re.M)
    return (v.group(1) if v else ""), (end.group(1) if end else "")


def stop_tip(folder: Path, stop: str) -> str:
    m = re.search(r"\b([0-9a-f]{40})\b", read(folder / "notes" / f"stop-{stop}.md"))
    return m.group(1) if m else ""


def coordinator_alive(folder: Path) -> tuple[bool, str]:
    """The rule STOP-REVIEW uses: a coordinator is alive when notes/LOG.md changed in the last 20 minutes."""
    log = folder / "notes" / "LOG.md"
    if not log.exists():
        return False, "no notes/LOG.md"
    minutes = (time.time() - log.stat().st_mtime) / 60
    return minutes < ALIVE_MINUTES, f"notes/LOG.md changed {minutes:.0f} minutes ago"


def state(folder: Path) -> dict:
    info = _state(folder)
    alive, why = coordinator_alive(Path(info.get("build_folder") or folder))
    info["coordinator_alive"] = f"{'yes' if alive else 'no'} ({why})"
    if alive and info["next"] == "build":
        # Never start a second coordinator; a live one picks the next checkpoint up on its next wake.
        info["next"], info["why"] = "running", f"a coordinator is alive ({why}); it continues on its next wake"
    return info


def _state(folder: Path) -> dict:
    yaml_text = read(folder / "PROGRAM.yaml")
    info = header(yaml_text)
    info["folder"] = folder.as_posix()
    fix = re.match(r"(.+)-fix-([A-Za-z0-9]+)$", folder.name)
    if fix:
        info["parent_program"] = (folder.parent / fix.group(1)).as_posix()
        info["after_stop"] = f"STOP-REVIEW round 2 for {info['parent_program']}, stop {fix.group(2)}"
    else:
        info["after_stop"] = f"STOP-REVIEW round 1 for {info['folder']}"

    def done(nxt: str, why: str, **extra) -> dict:
        info.update(extra)
        info["next"], info["why"] = nxt, why
        return info

    if not (folder / "SLICES.md").exists() or not yaml_text:
        return done("plan", "no SLICES.md or PROGRAM.yaml yet")
    if info["scope_gate"] in ("", "null", "~"):
        return done("plan-review", "scope_gate not set")
    previous_tip = info["parent_tip"]
    for stop in stops(yaml_text):
        sid = stop["id"]
        merge_text = read(folder / "merge" / f"{sid}.md")
        if stop["merged"] not in ("null", "") or "MERGED" in merge_text.split("WAITS")[0]:
            previous_tip = verdict(folder / "stop-review" / sid / "REVIEW-2.md")[1] or verdict(folder / "stop-review" / sid / "REVIEW.md")[1] or previous_tip
            continue
        tip = stop_tip(folder, sid)
        if fix:
            if not tip:
                return done("build", f"fix program for stop {sid} not finished", stop=sid)
            return done("stop-review", "fix program finished", stop=fix.group(2), round="2",
                        program_for_review=info["parent_program"], fix_program=info["folder"], tip=tip)
        if not tip:
            return done("build", f"stop {sid} not built yet (no notes/stop-{sid}.md)", stop=sid)
        v1, end1 = verdict(folder / "stop-review" / sid / "REVIEW.md")
        v2, end2 = verdict(folder / "stop-review" / sid / "REVIEW-2.md")
        if "WAITS FOR HIS WORD" in merge_text:
            return done("waits-on-him", f"merge of stop {sid} waits for his word (no CI yet)", stop=sid,
                        reviewed_tip=end2 or end1)
        if v2 == "CLEAN" or (v1 == "CLEAN" and not v2):
            return done("merge", f"stop {sid} review is CLEAN", stop=sid, reviewed_tip=end2 or end1)
        if v2 == "BLOCKED":
            return done("waits-on-him", f"stop {sid} blocked after round 2", stop=sid)
        if v1 == "BLOCKED":
            fix_dir = folder.parent / f"{folder.name}-fix-{sid}"
            fix_tip = stop_tip(fix_dir, sid) if fix_dir.exists() else ""
            if fix_tip:
                return done("stop-review", "fix program finished", stop=sid, round="2",
                            fix_program=fix_dir.as_posix(), tip=fix_tip, **{"from": previous_tip})
            return done("build", f"stop {sid} blocked; its fix program is not finished", stop=sid,
                        build_folder=fix_dir.as_posix())
        return done("stop-review", f"stop {sid} built, not reviewed", stop=sid, round="1", tip=tip,
                    **{"from": previous_tip})
    return done("done", "every stop merged")


def main() -> int:
    if len(sys.argv) > 1:
        folders = [Path(sys.argv[1])]
    else:
        folders = sorted({p.parent for p in ROOT.glob("*/PROGRAM.yaml")}
                         | {p.parent for p in ROOT.glob("*/*/PROGRAM.yaml")}
                         | {p.parent for p in ROOT.glob("*/*/*/PROGRAM.yaml")}
                         | {p.parent for p in ROOT.glob("*/*/*/*/PROGRAM.yaml")})
    for folder in folders:
        for key, value in state(folder).items():
            print(f"{key}: {value}")
        print()
    if not folders:
        print("no program folders found under D:/QMX-worktrees")
    return 0


if __name__ == "__main__":
    sys.exit(main())
