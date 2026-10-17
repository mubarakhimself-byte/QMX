"""Joins triage's verdict to the fetched papers: the kept papers, in triage's order, each with its
title, abstract and the reason it was kept. Its two inputs are told apart by shape, not order."""

import json
import sys

given = json.load(sys.stdin)["in"]
papers = next(v for v in given if isinstance(v, list))
triage = next(v for v in given if isinstance(v, dict))
by_id = {p["id"]: p for p in papers}
kept = [by_id[k["id"]] | {"why": k["why"]} for k in triage.get("keep", []) if k["id"] in by_id]
print(json.dumps(kept))
