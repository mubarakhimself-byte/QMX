"""Ranks what the brief may mention (card T1 step 3): alerts first, then at most three decisions,
then the watchlist's releases above low impact (high before medium, then by time), then the desk's
lines (HIGH first), then at most three research items. Each ranked item keeps its source link or
the run it came from, and a calendar row keeps its `qmx.marked/1` mark as outside text."""

import json
import re
import sys

MOST_DECISIONS = 3
MOST_RESEARCH = 3
LINK = re.compile(r"https?://\S+")
SECTION_ORDER = {"HIGH": 0, "MEDIUM": 1, "CALENDAR": 2}

day = json.load(sys.stdin)["in"]
ranked = []
for line in day["alerts"]:
    found = LINK.search(line)
    ranked.append({"kind": "alert", "text": line, "link": found.group() if found else ""})
for item in day["decisions"][:MOST_DECISIONS]:
    ranked.append(
        {"kind": "decision", "text": f"{item['title']}: {item['cause']}", "run_id": item["run_id"]}
    )
events = sorted(
    (e for e in day["events"] if e["impact"] != "low"),
    key=lambda e: (e["impact"] != "high", e.get("date", day["date"]), e["time_utc"]),
)
for event in events:
    text = f"{event['time_utc']} UTC {event['currency']} {event['title']} ({event['impact']})"
    marked = {"marked": event["marked"]} if "marked" in event else {}
    ranked.append({"kind": "event", "text": text, "link": event["source"], **marked})
for line in sorted(day["desk"], key=lambda d: SECTION_ORDER.get(d["section"], 3)):
    ranked.append({"kind": "desk", "text": line["text"], "link": line["links"][0]})
for paper in day["research"][:MOST_RESEARCH]:
    ranked.append({"kind": "research", "text": paper["title"], "link": paper["link"]})
print(json.dumps(day | {"ranked": ranked}))
