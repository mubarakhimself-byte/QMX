"""The digest card: what landed, what ran, what failed and needs him, and the line that says the
digest reads from his last look.

The card is assembled from the collected log and the writer's digest. Every line the writer wrote
names an object or a run the collect step really saw, so a line cannot invent an item.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
items = given if isinstance(given, list) else [given]
collected = next((v for v in items if isinstance(v, dict) and "landed" in v), {})
written = next((v for v in items if isinstance(v, dict) and "opening" in v), {})
landed = {str(item["object_id"]) for item in collected.get("landed") or []}
runs = {str(item["run_id"]) for item in collected.get("failed") or []}
problems = [
    f"line {n} names an item the collect step did not see"
    for n, line in enumerate(written.get("landed") or [], start=1)
    if str(line.get("object_id")) not in landed
]
problems += [
    f"needs_you {n} names a run that did not fail"
    for n, line in enumerate(written.get("needs_you") or [], start=1)
    if str(line.get("run_id")) not in runs
]
counts = {
    "landed": len(collected.get("landed") or []),
    "ran": len(collected.get("ran") or []),
    "failed": len(collected.get("failed") or []),
}
text = (
    f"Since your last look: {counts['landed']} items landed, {counts['ran']} runs finished and "
    f"{counts['failed']} failed. "
    + (written.get("opening") or "")
)
print(
    json.dumps(
        {
            "summary": text,
            "figures": counts,
            "opening": written.get("opening", ""),
            "landed": collected.get("landed") or [],
            "lines": written.get("landed") or [],
            "moved": written.get("moved") or [],
            "ran": collected.get("ran") or [],
            "failed": collected.get("failed") or [],
            "needs_you": written.get("needs_you") or [],
            "quiet": bool(written.get("quiet")),
            "read_from": collected.get("position"),
            "cursor_to": collected.get("highest"),
            "problems": problems,
        }
    )
)
