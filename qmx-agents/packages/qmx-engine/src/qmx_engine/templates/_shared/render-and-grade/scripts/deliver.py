"""Hands on the graded output alone, without its evidence, as the run's result."""

import json
import sys

graded = json.load(sys.stdin)["in"]
at = graded["feedback"]["output"]
print(json.dumps(graded["input"] if at is None else graded["input"][at]))
