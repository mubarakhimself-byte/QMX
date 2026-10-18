"""The edit lint (card R9 step 6): an edit that loosens a gate, threshold, budget, retry count or
limit is rejected outright, whatever its evidence. Every other edit is marked untested: replaying
past runs on a fix set and a guard set is not built, and an untested edit cannot be approved."""

import json
import re
import sys

LOOSEN = re.compile(
    r"\b(raise|increase|lower|reduce|loosen|relax|remove|drop|disable|skip|widen|double)\b"
    r".{0,40}\b(gate|threshold|budget|limit|cap|retr(y|ies)|timeout|runaway|tokens?|check)",
    re.IGNORECASE,
)

edits = []
for edit in json.load(sys.stdin)["in"]["edits"][:3]:
    loosens = LOOSEN.search(f"{edit['change']} {edit['why']}")
    status = (
        "rejected: it loosens a gate, threshold or budget, which only the operator changes"
        if loosens
        else "untested: replay on past runs is not built, so it cannot be approved yet"
    )
    edits.append(edit | {"status": status})
print(json.dumps({"edits": edits}))
