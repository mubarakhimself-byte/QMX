"""The model card: the scope, the splits with the sealed test, the leakage checks, the verdict and
the ablation, and the writer's summary. A leak, a touched sealed test or a spend above his number
ends at the checks, with nothing trained. Its inputs are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
scope = next(v for v in given if "horizon_bars" in v)
checks = next(v for v in given if "shuffle_score" in v and "problems" in v)
verdict = next((v for v in given if "train_validation_gap" in v), None)
prose = next((v for v in given if "summary" in v), {"summary": ""})
print(
    json.dumps(
        {
            "scope": {k: scope[k] for k in ("slot", "label", "horizon_bars", "features", "family")},
            "questions": scope["questions"],
            "checks": checks,
            "verdict": verdict["verdict"]
            if verdict
            else "stopped: " + "; ".join(checks["problems"]),
            "result": verdict,
            "summary": prose["summary"],
        }
    )
)
