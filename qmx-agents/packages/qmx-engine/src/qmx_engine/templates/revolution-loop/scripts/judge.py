"""The plateau check between revolutions: the parent loop stops on `plateau`, and reframes while a
revolution still keeps a candidate. It counts the revolution it just finished, because the value the
loop hands back is one revolution's result and nothing else counts the rounds."""

import json
import sys


def payload(given):
    """The first dict in the input that looks like a revolution's result."""
    if isinstance(given, dict):
        if "negatives" in given or "candidate" in given:
            return given
        for found in given.values():
            inner = payload(found)
            if inner:
                return inner
        return {}
    if isinstance(given, list):
        for found in given:
            inner = payload(found)
            if inner:
                return inner
    return {}


state = payload(json.load(sys.stdin)["in"])
print(
    json.dumps(
        {
            "idea": state.get("idea"),
            "plateau": not bool(state.get("passed")),
            "score": int(state.get("score") or 0),
            "rounds": int(state.get("rounds") or 0) + 1,
            "attempts": list(state.get("attempts") or []),
            "negatives": list(state.get("negatives") or []),
            "candidate": state.get("candidate"),
        }
    )
)
