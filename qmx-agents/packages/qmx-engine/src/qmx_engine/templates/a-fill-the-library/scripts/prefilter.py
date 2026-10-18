"""The zero-token pre-filter before triage (funnel stage 3): only captured items that say at least
one trading word go on to the triage model. The rest stay inventory rows, and the Library entry
step names why each was skipped."""

import json
import re
import sys

WORDS = re.compile(
    r"\b(entry|enter|exit|stop|target|take profit|timeframe|chart|candle|breakout|trend|"
    r"buy|sell|long|short|indicator|moving average|session|pips?|risk)\b",
    re.IGNORECASE,
)


def text_of(row):
    return row.get("text") or " ".join(s["text"] for s in row.get("segments") or [])


kept = []
for row in json.load(sys.stdin)["in"]:
    hits = len(WORDS.findall(text_of(row)))
    if hits:
        kept.append(row | {"keyword_hits": hits})
print(json.dumps(kept))
