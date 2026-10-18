"""Basis labels for at most five headline items, from a pointer check, never from a model. An item
whose `quote` appears in its `source_id`'s text is `retrieved`; one that names the items it was
reasoned `from` is `inferred`; any other is `remembered`. Each item keeps its evidence: the quote
and the start of its source, so the samples after this judge the evidence, not the claim alone."""

import json
import re
import sys

MOST = 5
EVIDENCE_CHARS = 600


def plain(text):
    return " ".join(re.sub(r"[^\w%.]+", " ", str(text).casefold()).split()).strip(" .")


given = json.load(sys.stdin)["in"]
sources = {
    str(s["id"]): " ".join(str(s.get(k, "")) for k in ("title", "abstract", "text"))
    for s in given.get("sources", [])
    if isinstance(s, dict) and "id" in s
}
labelled = []
for item in given.get("items", [])[:MOST]:
    quote = str(item.get("quote") or "")
    source = sources.get(str(item.get("source_id")), "")
    if plain(quote) and plain(quote) in plain(source):
        basis = "retrieved"
    elif item.get("from"):
        basis = "inferred"
    else:
        basis = "remembered"
    evidence = f"{quote} | source: {source[:EVIDENCE_CHARS]}" if basis == "retrieved" else ""
    labelled.append(
        {"id": str(item["id"]), "text": str(item["text"]), "basis": basis, "evidence": evidence}
    )
print(json.dumps({"items": labelled}))
