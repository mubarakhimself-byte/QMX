#!/usr/bin/env python3
"""Print the Wayfinder frontier for the local Markdown tracker.

Usage: python frontier.py [--all]

Reads every tickets/*.md, parses the YAML-like frontmatter (flat keys and
inline lists only), and prints the open, unblocked, unclaimed tickets first.
Exits with code 2 when a blocked_by slug does not exist or a cycle is found.
Standard library only.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TICKETS = HERE / "tickets"


def parse_frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        raw = raw.split("#", 1)[0].strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            out[key.strip()] = [s.strip().strip('"') for s in inner.split(",") if s.strip()]
        else:
            out[key.strip()] = raw.strip('"')
    return out


def load() -> dict[str, dict]:
    tickets: dict[str, dict] = {}
    for path in sorted(TICKETS.glob("*.md")):
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        fm.setdefault("blocked_by", [])
        fm.setdefault("status", "open")
        fm.setdefault("claimed_by", "")
        fm.setdefault("type", "?")
        fm.setdefault("mode", "?")
        tickets[path.stem] = fm
    return tickets


def check(tickets: dict[str, dict]) -> list[str]:
    problems = []
    for slug, fm in tickets.items():
        for dep in fm["blocked_by"]:
            if dep not in tickets:
                problems.append(f"{slug}: unknown blocker '{dep}'")
    # cycle check by DFS
    state: dict[str, int] = {}

    def visit(node: str, trail: list[str]) -> None:
        if state.get(node) == 1:
            problems.append("cycle: " + " -> ".join(trail + [node]))
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for dep in tickets.get(node, {}).get("blocked_by", []):
            if dep in tickets:
                visit(dep, trail + [node])
        state[node] = 2

    for slug in tickets:
        visit(slug, [])
    return problems


def main(argv: list[str]) -> int:
    show_all = "--all" in argv
    tickets = load()
    problems = check(tickets)
    if problems:
        for p in problems:
            print("ERROR", p)
        return 2

    def closed(slug: str) -> bool:
        return tickets[slug]["status"] == "closed"

    frontier, blocked, claimed, done = [], [], [], []
    for slug, fm in tickets.items():
        if closed(slug):
            done.append(slug)
        elif any(not closed(d) for d in fm["blocked_by"]):
            blocked.append(slug)
        elif fm["claimed_by"]:
            claimed.append(slug)
        else:
            frontier.append(slug)

    def row(slug: str) -> str:
        fm = tickets[slug]
        return f"  {fm['title']:<42} {fm['type']:<9} {fm['mode']:<4} [{slug}]"

    print(f"FRONTIER ({len(frontier)}): open, unblocked, unclaimed")
    for s in frontier:
        print(row(s))
    print(f"\nBLOCKED ({len(blocked)})")
    for s in blocked:
        open_deps = [d for d in tickets[s]["blocked_by"] if not closed(d)]
        print(row(s) + "  waits on: " + ", ".join(open_deps))
    if claimed or show_all:
        print(f"\nCLAIMED ({len(claimed)})")
        for s in claimed:
            print(row(s) + f"  by {tickets[s]['claimed_by']}")
    print(f"\nCLOSED ({len(done)})")
    for s in done:
        print(row(s))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
