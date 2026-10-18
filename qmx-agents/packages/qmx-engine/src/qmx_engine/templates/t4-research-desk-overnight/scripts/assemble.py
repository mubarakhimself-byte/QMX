"""The ranked brief: the coordinator's lines put in their sections, each with the links and labels
of the claims it rests on, then what the cut rules cut and why, then the hint-card proposals. A HIGH
line whose claims name a mechanism becomes a proposal, parked; nothing is written to the Library.
The input is the lines check's pass, holding the cut rules' result and the coordinator's lines."""

import json
import sys

SECTIONS = ("HIGH", "MEDIUM", "CALENDAR", "POSITIONING", "CROSS-ASSET")


def flat(given):
    found = []
    for value in given if isinstance(given, list) else [given]:
        if isinstance(value, dict) and set(value) == {"input", "verdict", "feedback"}:
            found += flat(value["input"])
        else:
            found.append(value)
    return found


given = flat(json.load(sys.stdin)["in"])
desk = next(v for v in given if "kept" in v)
brief = next(v for v in given if "lines" in v)
claims = {claim["id"]: claim for claim in desk["kept"]}
sections = {name: [] for name in SECTIONS}
hints = []
for line in brief["lines"]:
    backing = [claims[c] for c in line["claim_ids"]]
    links = sorted({c["link"] for c in backing})
    sections[line["section"]].append(
        {
            "text": line["text"],
            "label": line["label"],
            "links": links,
            "claim_ids": line["claim_ids"],
        }
    )
    mechanisms = [c["mechanism"] for c in backing if c["mechanism"]]
    if line["section"] == "HIGH" and mechanisms:
        hints.append(
            {
                "instrument": backing[0]["instrument"],
                "direction": backing[0]["direction"],
                "mechanism": mechanisms[0],
                "links": links,
                "status": "parked: a hint-card proposal, not written to the Library",
            }
        )
print(
    json.dumps(
        {
            "date": desk["date"],
            "instruments": desk["watchlist"],
            "summary": brief["summary"],
            "sections": sections,
            "cut": desk["cut"],
            "hint_cards": hints,
            "could_not_check": desk["could_not_check"],
        }
    )
)
