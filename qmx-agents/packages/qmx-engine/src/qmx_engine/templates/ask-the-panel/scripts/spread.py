"""The spread: what each seat answered, which family served it, where the seats agree and where they
do not.

The seats' answers are read from the run's own ledger by node id, because a list of four inputs does
not say which seat wrote which answer. The family comes from the row each seat resolved to, which
the run recorded when it dispatched the node: a member whose node never finished is absent, never
silently dropped.
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


def rows():
    """Each node's dispatch row and each node's finished output, from this run's ledger."""
    home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
    with Reader.open(home) as reader:
        events = reader.events(os.environ["QMX_RUN_ID"])
    started = {
        event.data["node_id"]: event.data
        for event in events
        if event.kind == "node_started" and "node_id" in event.data
    }
    finished = {
        event.data["node_id"]: (event.data.get("outputs") or {}).get("main")
        for event in events
        if event.kind == "node_finished" and "node_id" in event.data
    }
    return started, finished


given = json.load(sys.stdin)["in"]
items = given if isinstance(given, list) else [given]
plan = next((found for found in items if isinstance(found, dict) and "members" in found), {})
started, finished = rows()
seats = []
for member in plan.get("members") or []:
    node = member["node"]
    answer = finished.get(node)
    row = started.get(node) or {}
    present = isinstance(answer, dict) and "stance" in answer
    seats.append(
        {
            "slot": member["slot"],
            "node": node,
            "angle": member["angle"],
            "present": present,
            "stance": answer.get("stance") if present else None,
            "answer": answer.get("answer") if present else "",
            "claims": answer.get("claims") if present else [],
            "family": family(row.get("profile"), row.get("model")),
            "model": row.get("candidate"),
        }
    )
stances: dict[str, list[str]] = {}
for seat in seats:
    if seat["present"]:
        stances.setdefault(str(seat["stance"]), []).append(seat["slot"])
majority = max(stances, key=lambda name: len(stances[name])) if stances else None
agreement = [
    f"{', '.join(slots)} all read {name}" for name, slots in stances.items() if len(slots) > 1
]
disagreement = [
    {
        "slot": seat["slot"],
        "stance": seat["stance"],
        "against": majority,
        "claim": (seat["claims"] or [{}])[0].get("text", ""),
    }
    for seat in seats
    if seat["present"] and majority is not None and seat["stance"] != majority
]
print(
    json.dumps(
        {
            "question": plan.get("question"),
            "members": seats,
            "stances": stances,
            "majority": majority,
            "agreement": agreement,
            "disagreement": disagreement,
            "absent": [seat["slot"] for seat in seats if not seat["present"]],
            "families": sorted({str(seat["family"]) for seat in seats if seat["present"]}),
        }
    )
)
