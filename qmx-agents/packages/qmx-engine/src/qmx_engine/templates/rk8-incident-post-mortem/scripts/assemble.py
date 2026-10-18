"""The post-mortem: the timeline as a story (before, trigger, guard reaction, aftermath), the
impact, the cited account, the candidate causes, the challenger's objections and the proposed
actions for him to accept. Its inputs, the citations check's pass (timeline and draft), the impact
and the challenge, are told apart by shape."""

import json
import sys


def flat(given):
    found = []
    for value in given if isinstance(given, list) else [given]:
        if isinstance(value, dict) and set(value) == {"input", "verdict", "feedback"}:
            found += flat(value["input"])
        else:
            found.append(value)
    return found


given = flat(json.load(sys.stdin)["in"])
incident = next(v for v in given if "timeline" in v)
draft = next(v for v in given if "what_happened" in v)
impact = next(v for v in given if "loss_usd" in v)
challenge = next(v for v in given if "challenges" in v)
print(
    json.dumps(
        {
            "incident": incident["incident"],
            "timeline": sorted(incident["timeline"], key=lambda e: e["at"]),
            "impact": impact,
            "what_happened": draft["what_happened"],
            "contributing_factors": draft["contributing_factors"],
            "candidate_causes": draft["candidate_causes"],
            "challenges": challenge["challenges"],
            "actions": draft["actions"],
        }
    )
)
