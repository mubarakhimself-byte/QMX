"""Find his own words in Claude Code transcripts, with a citable source for each.

Usage:
  python his_words.py <regex> [<regex> ...] [--dir <projects folder>] [--full] [--since YYYY-MM-DD]

Prints every turn he typed (or dictated) that matches all the regexes, case-insensitive,
as `<id8>:L<line> (<title>, <date>)` followed by the text. Skips what only looks like his
turn: tool results, skill and system injections (isMeta), compaction summaries (agent
paraphrase), local command output, and messages relayed from other sessions or agents.
Text inside <pasted_content> is dropped unless --pastes is given: a paste is often a
document, but sometimes his own dictation, so the reader decides. A turn repeated
in a continuation file is printed once, at its first appearance. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

DEFAULT_DIRS = [
    Path("C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX"),
    Path("C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Documents-QMX"),
]
ANSWER = re.compile(r"^\s*(The user answered|User has answered)")
NOT_HIS = re.compile(
    r"^\s*(<command-|<local-command|Caveat:|Another Claude session sent a message|"
    r"<cross-session-message|<agent-message|<task-notification|<system-reminder|\[SYSTEM NOTIFICATION)"
)
PASTE = re.compile(r"<pasted_content[^>]*>.*?</pasted_content[^>]*>", re.S)


def turn_text(record: dict, pastes: bool = False) -> str | None:
    if record.get("type") != "user" or record.get("isMeta") or record.get("isCompactSummary"):
        return None
    content = record.get("message", {}).get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        results = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_result"]
        if results:
            # His answers to AskUserQuestion come back as a tool result; keep those, drop the rest.
            texts = []
            for b in results:
                inner = b.get("content")
                if isinstance(inner, list):
                    inner = "\n".join(x.get("text", "") for x in inner if isinstance(x, dict))
                if isinstance(inner, str) and ANSWER.match(inner):
                    texts.append(inner)
            return "\n".join(texts).strip() or None
        text = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    else:
        return None
    if not text.strip() or NOT_HIS.match(text) or text.lstrip().startswith("This session is being continued"):
        return None
    return (text if pastes else PASTE.sub("[pasted content omitted]", text)).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("patterns", nargs="+")
    ap.add_argument("--dir", type=Path, action="append", help="transcript folder; repeatable (default: both QMX folders)")
    ap.add_argument("--full", action="store_true", help="print whole turns, not 600-character excerpts")
    ap.add_argument("--pastes", action="store_true", help="keep pasted text, marked by its tags")
    ap.add_argument("--since", default="", help="skip turns before this date, YYYY-MM-DD")
    args = ap.parse_args()
    regexes = [re.compile(p, re.I) for p in args.patterns]
    seen: set[str] = set()
    hits = []
    paths = sorted(p for d in (args.dir or DEFAULT_DIRS) if d.exists() for p in d.glob("*.jsonl"))
    for path in paths:
        title = path.stem[:8]
        with path.open(encoding="utf-8", errors="replace") as fh:
            for n, line in enumerate(fh, 1):
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("customTitle"):
                    title = rec["customTitle"]
                text = turn_text(rec, args.pastes)
                if text is None or not all(r.search(text) for r in regexes):
                    continue
                date = str(rec.get("timestamp", ""))[:10]
                if args.since and date and date < args.since:
                    continue
                key = hashlib.sha1(text.encode("utf-8")).hexdigest()
                if key in seen:
                    continue
                seen.add(key)
                hits.append((date, f"{path.stem[:8]}:L{n} ({title}, {date})", text))
    for date, source, text in sorted(hits):
        body = text if args.full else (text[:600] + (" ..." if len(text) > 600 else ""))
        print(f"== {source}\n{body}\n")
    print(f"{len(hits)} turns", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
