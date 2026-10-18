"""Checks and dedupes a generation's children (card D3 step 5 and its gates). Its inputs, the
generation's state and the proposed children, are told apart by shape.

A child is refused when it names no diagnosed weakness, when its spec differs from the best only in
parameter values (a nudge, not a structural child), or when its spec hash is already in the family
ledger or this run. At most 4 children per generation. A refused child is recorded with its reason
and never built.
"""

import hashlib
import json
import sys

MAX_CHILDREN = 4

given = json.load(sys.stdin)["in"]
state = next(v for v in given if "best_score" in v)
proposed = next(v for v in given if "children" in v and "best_score" not in v)["children"]
buckets = {w["bucket"] for w in state["weaknesses"]}
seen = set(state["family_hashes"]) | {c["spec_hash"] for c in state["children"]}
best = state["best"]["spec"]
kept, refused = [], []
for child in proposed:
    spec_hash = hashlib.sha256(json.dumps(child["spec"], sort_keys=True).encode()).hexdigest()
    structure = {k: v for k, v in child["spec"].items() if k != "params"}
    if child["bucket"] not in buckets:
        why = "it names no diagnosed weakness"
    elif structure == {k: v for k, v in best.items() if k != "params"}:
        why = "a parameter nudge is not a structural child"
    elif spec_hash in seen:
        why = "already tried in this family"
    elif len(kept) == MAX_CHILDREN:
        why = "over the 4 children of a generation"
    else:
        seen.add(spec_hash)
        kept.append(child | {"spec_hash": spec_hash})
        continue
    refused.append({"change": child["change"], "spec_hash": spec_hash, "why": why})
print(json.dumps({"build": kept, "refused": refused, "generation": state["generation"] + 1}))
