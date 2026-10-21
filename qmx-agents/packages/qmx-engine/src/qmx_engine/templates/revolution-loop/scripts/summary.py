"""The loop card: every revolution, the candidate the loop kept, the negative results it refused to
throw away, and the line that says whether the idea plateaued."""

import json
import sys

given = json.load(sys.stdin)["in"]
state = given if isinstance(given, dict) else given[-1]
attempts = list(state.get("attempts") or [])
negatives = list(state.get("negatives") or [])
rounds = int(state.get("rounds") or 0)
kept = state.get("candidate")
passed = bool(state.get("passed"))
word = "one" if rounds == 1 else "several"
text = (
    f"The loop ran {word} revolution(s) of the idea, in {len(attempts)} attempts. "
    + (
        "One attempt kept a candidate that passed every gate."
        if passed or kept
        else "Every candidate was refused, so the loop plateaued and stopped."
    )
    + (
        " The negative results are kept beside the card, one per refused candidate, so the next "
        "run does not repeat them."
        if negatives
        else ""
    )
    + " Nothing here is a signal to trade."
).replace("revolution(s)", "revolution" if rounds == 1 else "revolutions")
print(
    json.dumps(
        {
            "summary": text,
            "figures": {
                "revolutions": rounds,
                "attempts": len(attempts),
                "kept": 1 if kept else 0,
                "negatives": len(negatives),
                "score": int(state.get("score") or 0),
            },
            "revolutions": rounds,
            "attempts": attempts,
            "negatives": negatives,
            "kept": kept,
            "plateau": bool(state.get("plateau")),
        }
    )
)
