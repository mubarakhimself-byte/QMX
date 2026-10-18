"""The citation grader. A claim is any object with a `quote` and a `source_id`; a source is any
object with an `id` and an `abstract` or `text`. Every claim's quote must appear, ignoring case,
spacing and punctuation, in its source's title, abstract or text. Passes when every claim is cited;
the feedback lists each uncited claim so the next step drops it."""

import json
import re
import sys


def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def plain(text):
    return " ".join(re.sub(r"[^\w%.]+", " ", str(text).casefold()).split()).strip(" .")


given = json.load(sys.stdin)["in"]
sources = {
    str(found["id"]): plain(" ".join(str(found.get(k, "")) for k in ("title", "abstract", "text")))
    for found in walk(given)
    if "id" in found and ("abstract" in found or "text" in found)
}
claims = [found for found in walk(given) if "quote" in found and "source_id" in found]
uncited = [
    {"source_id": str(c["source_id"]), "quote": str(c["quote"])[:160]}
    for c in claims
    if not plain(c["quote"]) or plain(c["quote"]) not in sources.get(str(c["source_id"]), "")
]
feedback = {"claims": len(claims), "cited": len(claims) - len(uncited), "uncited": uncited}
print(json.dumps({"verdict": "fail" if uncited or not claims else "pass", "feedback": feedback}))
