"""Splits each captured source into sections with locators, one flat list for the section readers.

A video's transcript segments are grouped by its triage time map when it has one (windows marked
promo or chatter are skipped), else into windows of about two minutes; the locator is
`mm:ss-mm:ss`. Text is grouped by paragraph into stretches of about 1,200 characters; the locator
is `paragraphs a-b`. The input is a list of sources, or an object holding one under `sources` or
`items`; any other value in a list is passed over. A section id is `<source id>#s<n>`."""

import json
import sys

WINDOW_S = 120
TEXT_CHARS = 1200
SKIPPED = ("promo", "chatter", "sponsor", "intro", "outro")


def clock(seconds):
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def video_sections(item):
    segments = item.get("segments") or []
    windows = [
        w
        for w in item.get("time_map") or []
        if not any(word in str(w.get("label", "")).casefold() for word in SKIPPED)
    ]
    if not windows and segments:
        start, end = int(segments[0]["start"]), int(segments[-1]["end"]) + 1
        windows = [{"start": s, "end": s + WINDOW_S} for s in range(start, end, WINDOW_S)]
    for window in windows:
        inside = [s for s in segments if window["start"] <= s["start"] < window["end"]]
        if inside:
            locator = f"{clock(inside[0]['start'])}-{clock(inside[-1]['end'])}"
            yield locator, " ".join(s["text"] for s in inside)


def text_sections(item):
    paragraphs = [p.strip() for p in str(item.get("text") or "").split("\n\n") if p.strip()]
    first, stretch = 1, []
    for number, paragraph in enumerate(paragraphs, 1):
        stretch.append(paragraph)
        if sum(len(p) for p in stretch) >= TEXT_CHARS or number == len(paragraphs):
            yield f"paragraphs {first}-{number}", "\n\n".join(stretch)
            first, stretch = number + 1, []


given = json.load(sys.stdin)["in"]
if isinstance(given, dict):
    given = given.get("sources") or given.get("items") or []
sections = []
for item in given:
    if not isinstance(item, dict) or "id" not in item:
        continue
    found = video_sections(item) if item.get("segments") else text_sections(item)
    for number, (locator, text) in enumerate(found, 1):
        section_id = f"{item['id']}#s{number}"
        sections.append({"id": section_id, "item_id": item["id"], "locator": locator, "text": text})
print(json.dumps(sections))
