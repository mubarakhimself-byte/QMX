"""Hands on the graded output alone, without its evidence, as the run's result. `flat` is the
grade script's own, so the output index means the same here."""

import json
import sys


def flat(given):
    """The inputs, with each grader's envelope opened, so a check before this one passes on what it
    checked."""
    found = []
    for value in given if isinstance(given, list) else [given]:
        if isinstance(value, dict) and set(value) == {"input", "verdict", "feedback"}:
            found += flat(value["input"])
        else:
            found.append(value)
    return found


graded = json.load(sys.stdin)["in"]
print(json.dumps(flat(graded["input"])[graded["feedback"]["output"]]))
