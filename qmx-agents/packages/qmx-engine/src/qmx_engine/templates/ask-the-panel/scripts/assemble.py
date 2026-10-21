"""The panel card: the seats, their families, where they agree, where they disagree, which
disagreement matters, and whether the judge shares a family with a seat it judged (AD-13).

A seat that never answered stays on the card as absent. A judge of the same family as a seat is
named beside that seat, because agreement from one family is weaker evidence than agreement across
families.
"""

import json
import os
import sys
from pathlib import Path

from qmx_engine.ledger.store import Reader
from qmx_engine.workers.zones import home_of

PLAN = {"claude": "anthropic", "gpt": "openai"}
PROVIDERS = {"moonshotai": "moonshot", "deepseek": "deepseek", "z-ai": "zhipu", "qwen": "alibaba"}


def family(profile, model):
    if profile == "openrouter":
        return PROVIDERS.get(str(model).split("/")[0], str(model).split("/")[0])
    return PLAN.get(str(profile), str(profile))


def judge_row():
    """The row the judge ran on, read from this run's ledger: the spread ran before it started."""
    home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
    with Reader.open(home) as reader:
        events = reader.events(os.environ["QMX_RUN_ID"])
    found = next(
        (
            event.data
            for event in events
            if event.kind == "node_started" and event.data.get("node_id") == "judge"
        ),
        {},
    )
    return {"family": family(found.get("profile"), found.get("model")),
            "model": found.get("candidate")}  # fmt: skip


given = json.load(sys.stdin)["in"]
items = given if isinstance(given, list) else [given]
spread = next((found for found in items if isinstance(found, dict) and "members" in found), {})
judged = next((found for found in items if isinstance(found, dict) and "matters_most" in found), {})
members = list(spread.get("members") or [])
absent = list(spread.get("absent") or [])
families = sorted({str(member.get("family")) for member in members})
judge = judge_row()
same_family = [
    member["slot"]
    for member in members
    if member.get("present") and judge["family"] == member.get("family")
]
words = {0: "no", 1: "one", 2: "two", 3: "three", 4: "four"}
text = (
    f"{words.get(len(members), str(len(members))).capitalize()} seats were asked the same question "
    f"across {words.get(len(families), str(len(families)))} model families. "
    + (
        "Every seat answered. "
        if not absent
        else f"Absent, not silently dropped: {', '.join(absent)}. "
    )
    + (
        "The seats agree on the reading and the disagreement is thin; treat agreement as weak "
        "evidence rather than a conclusion. "
        if not spread.get("disagreement")
        else "The spread is the answer: the disagreement below is what changes what to do. "
    )
    + (
        f"The judge shares a family with {', '.join(same_family)}, labelled on the card. "
        if same_family
        else ""
    )
    + "This is a read of the seats, not a signal to trade."
)
print(
    json.dumps(
        {
            "summary": text,
            "figures": {
                "members": len(members),
                "present": len(members) - len(absent),
                "families": len(families),
                "agreement": len(spread.get("agreement") or []),
                "disagreement": len(spread.get("disagreement") or []),
            },
            "question": spread.get("question"),
            "members": members,
            "absent": absent,
            "families": families,
            "agreement": list(spread.get("agreement") or []),
            "disagreement": list(spread.get("disagreement") or []),
            "matters_most": judged.get("matters_most", ""),
            "agreement_points": list(judged.get("points_of_agreement") or []),
            "disagreement_points": list(judged.get("points_of_disagreement") or []),
            "judge": judge,
            "judge_same_family_as": same_family,
        }
    )
)
