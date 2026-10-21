"""A revolution's result on the attempt loop's `next` port: the candidate when the gates passed, or
the negative result they left, with the score and the attempt list carried forward so the parent
loop never has to read another run's files."""

import json
import sys

given = json.load(sys.stdin)["in"]
gate = given if isinstance(given, dict) else given[-1]
chain = gate.get("chain") or {}
passed = bool(gate.get("passed"))
negatives = list(chain.get("negatives") or [])
attempts = list(chain.get("attempts") or [])
score = int(chain.get("score") or 0)
candidate = gate.get("candidate") if passed else None
if passed:
    score += 1
    attempts.append({"kept": candidate, "problems": []})
else:
    problem = "; ".join(gate.get("problems") or ["the gates refused it"])
    negatives.append({"problem": problem, "candidate": gate.get("candidate")})
    attempts.append({"kept": None, "problems": problem})
print(
    json.dumps(
        {
            "idea": chain.get("idea"),
            "fixture": chain.get("fixture"),
            "passed": passed,
            "candidate": candidate,
            "score": score,
            "rounds": int(chain.get("rounds") or 0),
            "attempts": attempts,
            "negatives": negatives,
        }
    )
)
