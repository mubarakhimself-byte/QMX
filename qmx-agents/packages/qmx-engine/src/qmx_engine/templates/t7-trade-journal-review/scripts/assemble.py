"""The weekly explainer: the slice stats beside at most three lessons, each kept only when the judge
found it matches its slice's stats and is not a lesson already proposed. Its inputs, the stats,
the analyst's lessons and the judge's verdicts, are told apart by shape."""

import json
import sys

MOST_LESSONS = 3

given = json.load(sys.stdin)["in"]
stats = next(v for v in given if "significant" in v)
drafted = next(v["lessons"] for v in given if "lessons" in v)
verdicts = {v["slice"]: v for v in next(v["verdicts"] for v in given if "verdicts" in v)}
kept = [
    lesson | {"judge": verdicts[lesson["slice"]]["why"]}
    for lesson in drafted
    if verdicts.get(lesson["slice"], {}).get("keep")
][:MOST_LESSONS]
print(
    json.dumps(
        stats
        | {
            "summary": f"{len(stats['significant'])} slices pass the filter; "
            f"{len(kept)} lessons kept for his yes or no.",
            "lessons": kept,
        }
    )
)
