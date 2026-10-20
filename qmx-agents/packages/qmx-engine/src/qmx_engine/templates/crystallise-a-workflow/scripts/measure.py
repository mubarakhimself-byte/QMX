"""Measure the script against the agent on the sampled items.

The agreement rate is what keeps the crystallised step honest: when the script and the agent disagree
on a sample, the card says so and the step goes back to the agent on titles like it."""

import json
import sys

given = json.load(sys.stdin)["in"]
items = given if isinstance(given, list) else [given]
batch = next((v for v in items if isinstance(v, dict) and "sampled" in v), {})
asked = next((v for v in items if isinstance(v, dict) and "labels" in v), {"labels": []})
by_id = {str(item["item_id"]): item for item in batch.get("sampled") or []}
labels = {
    str(entry.get("item_id")): str(entry.get("label")) for entry in asked.get("labels") or []
}
samples = [
    {
        "item_id": item["item_id"],
        "title": item["title"],
        "script": item["label"],
        "agent": labels.get(str(item["item_id"])),
        "agree": labels.get(str(item["item_id"])) == item["label"],
    }
    for item in by_id.values()
]
agreeing = sum(1 for sample in samples if sample["agree"])
print(
    json.dumps(
        {
            "rules": batch.get("rules") or {},
            "items": batch.get("items") or [],
            "sampled": list(by_id.values()),
            "samples": samples,
            "agreement": (agreeing / len(samples)) if samples else None,
            "agreeing": agreeing,
            "sampled_count": len(samples),
        }
    )
)
