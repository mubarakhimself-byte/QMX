"""Fails the step when the note failed its receipts check, naming every number no receipt holds and
every receipt the run never recorded."""

import json
import sys

feedback = json.load(sys.stdin)["in"]["feedback"]
problems = list(feedback.get("problems", []))
if feedback.get("uncited"):
    problems.append(f"no cited receipt holds {', '.join(feedback['uncited'])}")
if feedback.get("unknown_receipts"):
    names = ", ".join(feedback["unknown_receipts"])
    problems.append(f"{names} is no script or app step of this run")
print(f"[QMX_FAILURE] the note fails its receipts: {'; '.join(problems)}")
