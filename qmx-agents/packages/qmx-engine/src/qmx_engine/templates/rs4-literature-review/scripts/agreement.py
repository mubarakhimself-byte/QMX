"""Agreement across the blind samples, then the confidence rule (card R7 step 5).

high: retrieved, and every sample says `holds`. medium: retrieved with all but one sample saying
`holds`, or inferred with every sample saying `holds`. low: anything else, so a remembered claim
or a split vote is never more than low. A sample that gave no answer for an item counts as
disagreement. A low item is marked contested: it cannot be a headline."""

import json
import sys
from collections import Counter

given = json.load(sys.stdin)["in"]
basis = next(v for v in given if isinstance(v, dict) and "items" in v)
samples = [v for v in given if isinstance(v, dict) and "votes" in v]
k = len(samples)
by_sample = [{str(v.get("id")): v.get("answer") for v in s["votes"]} for s in samples]

calibration = []
for item in basis["items"]:
    answers = [found.get(item["id"], "no answer") for found in by_sample]
    holds = answers.count("holds")
    top, top_count = Counter(answers).most_common(1)[0] if answers else ("no answer", 0)
    if item["basis"] == "retrieved" and k and holds == k:
        confidence = "high"
    elif (item["basis"] == "retrieved" and k > 1 and holds == k - 1) or (
        item["basis"] == "inferred" and k and holds == k
    ):
        confidence = "medium"
    else:
        confidence = "low"
    calibration.append(
        {
            "id": item["id"],
            "text": item["text"],
            "basis": item["basis"],
            "answers": answers,
            "agreement": f"{top_count} of {k} say {top}",
            "confidence": confidence,
            "contested": confidence == "low",
        }
    )
print(json.dumps({"calibration": calibration}))
