"""The replication scorecard: the verdict on top, one row per reported number (reported, ours,
ours with costs, after publication), the decay ratio, the assumptions and any pick card. A source
already in the ledger ends here with its hash and no new reading. Its inputs are told apart by
shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
source = next(v for v in given if "source_hash" in v)
spec = next((v for v in given if "assumptions" in v), None)
compared = next((v for v in given if "decay_ratio" in v), None)
prose = next((v for v in given if "summary" in v), {"summary": ""})
if source["seen"]:
    verdict = f"already processed: source {source['source_hash']}; showing the old result"
else:
    verdict = compared["verdict"]
print(
    json.dumps(
        {
            "source_hash": source["source_hash"],
            "verdict": verdict,
            "rows": compared["rows"] if compared else [],
            "decay_ratio": compared["decay_ratio"] if compared else None,
            "assumptions": spec["assumptions"] if spec else [],
            "dropped": spec["dropped"] if spec else [],
            "pick_card": spec["pick_card"] if spec else None,
            "summary": prose["summary"],
        }
    )
)
