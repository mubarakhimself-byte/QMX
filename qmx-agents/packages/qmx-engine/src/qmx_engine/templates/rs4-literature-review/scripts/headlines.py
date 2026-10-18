"""The items to calibrate (card R4 step 7): the verdicts of the first five rows of the methods
matrix, each with the first cited claim from that row's sources, and the sources themselves. Its
input is the citation check's verdict on the searcher items and the synthesis."""

import json
import sys

graded = json.load(sys.stdin)["in"]
sources = next(v for v in graded["input"] if isinstance(v, list))
synthesis = next(v for v in graded["input"] if isinstance(v, dict) and "matrix" in v)
uncited = {(u["source_id"], u["quote"]) for u in (graded.get("feedback") or {}).get("uncited", [])}
cited = [
    c for c in synthesis["claims"] if (str(c["source_id"]), str(c["quote"])[:160]) not in uncited
]
items = []
for row in synthesis["matrix"][:5]:
    claim = next((c for c in cited if c["source_id"] in row["source_ids"]), {})
    items.append(
        {
            "id": row["method"],
            "text": f"{row['method']}: {row['verdict']}",
            "quote": claim.get("quote", ""),
            "source_id": claim.get("source_id", ""),
        }
    )
print(json.dumps({"items": items, "sources": sources}))
