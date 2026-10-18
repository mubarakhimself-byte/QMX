"""The desk's cut rules, as code rather than the coordinator's discretion (card T4).

Claims are grouped by instrument and direction, scheduled tier-one releases apart, and a group's
strength is its count of distinct news items. A claim whose source is no item of the night is cut.
A group backed by one item is cut, unless that item is a scheduled tier-one release (a fact, not
an opinion: CALENDAR) or a positioning reading at least 5 standard deviations from its own 30-day
normal (POSITIONING). Two or more items make the group HIGH when they agree on a direction, MEDIUM
when the direction is unclear, and CROSS-ASSET when every item behind it is on the cross-asset
beat. Every cut names the analyst (the chunk) whose claim it was.

Claim ids and analyst names are letters, never digits (`ca`, `cb`, ... and `analyst A`), because
the grade reads every digit run in the brief's prose as a number that must come from the news.

The input is the quotes check's pass: the analyst items and every chunk's claims, told apart by
shape.
"""

import json
import sys

SENTIMENT_SD = 5


def letters(n):
    """0 -> a, 25 -> z, 26 -> aa, like spreadsheet columns."""
    out = ""
    n += 1
    while n:
        n, rest = divmod(n - 1, 26)
        out = chr(ord("a") + rest) + out
    return out


def flat(given):
    found = []
    for value in given if isinstance(given, list) else [given]:
        if isinstance(value, dict) and set(value) == {"input", "verdict", "feedback"}:
            found += flat(value["input"])
        else:
            found.append(value)
    return found


given = flat(json.load(sys.stdin)["in"])
items = next(v for v in given if isinstance(v, list) and all("link" in i for i in v))
chunks = next(v for v in given if isinstance(v, list) and v is not items)
by_id = {item["id"]: item for item in items}
night = items[0]["night"]

seen, claims, cut = set(), [], []
for analyst, chunk in enumerate(chunks):
    for given_claim in chunk.get("claims", []):
        claim = given_claim | {"analyst": f"analyst {letters(analyst).upper()}"}
        key = (claim["source_id"], claim["quote"], claim["instrument"], claim["direction"])
        if key in seen:
            continue
        seen.add(key)
        if claim["source_id"] not in by_id:
            cut.append(claim | {"why": "no source: the item is not in tonight's news"})
        else:
            claims.append(claim)

groups = {}
for claim in claims:
    tier1 = by_id[claim["source_id"]]["tier1"]
    groups.setdefault((claim["instrument"], claim["direction"], tier1), []).append(claim)


def section(members):
    sources = {c["source_id"] for c in members}
    backing = [by_id[s] for s in sources]
    if any(item["tier1"] for item in backing):
        return "CALENDAR", None
    if len(sources) >= 2:
        if all(item["beat"] == "cross_asset" for item in backing):
            return "CROSS-ASSET", None
        if members[0]["direction"] == "unclear":
            return "MEDIUM", None
        return "HIGH", None
    item = backing[0]
    sd = item.get("sentiment_sd")
    if item["beat"] == "positioning" and sd is not None and abs(sd) >= SENTIMENT_SD:
        return "POSITIONING", None
    if item["beat"] == "positioning":
        return None, f"a sentiment reading alone counts only from {SENTIMENT_SD} sd; this is {sd}"
    return None, "single source: one item only, and not a scheduled tier-one release"


kept, grouped = [], []
for (instrument, direction, _), members in groups.items():
    name, why = section(members)
    if name is None:
        cut += [c | {"why": why} for c in members]
        continue
    ids = []
    for claim in members:
        found = f"c{letters(len(kept))}"
        ids.append(found)
        kept.append(
            claim | {"id": found, "section": name, "link": by_id[claim["source_id"]]["link"]}
        )
    grouped.append(
        {
            "section": name,
            "instrument": instrument,
            "direction": direction,
            "claim_ids": ids,
            "sources": sorted({c["source_id"] for c in members}),
        }
    )
print(
    json.dumps(
        {
            "date": night["date"],
            "watchlist": sorted({i for item in items for i in item["instruments"]}),
            "kept": kept,
            "groups": grouped,
            "cut": [
                {k: c[k] for k in ("analyst", "instrument", "text", "source_id", "why")}
                for c in cut
            ],
            "could_not_check": night["could_not_check"],
        }
    )
)
