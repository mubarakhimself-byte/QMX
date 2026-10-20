"""The crystallise card: the rule the replays agreed on, its equivalence, the sampling rate, what
fell back to the agent and how the sample held up."""

import json
import sys

given = json.load(sys.stdin)["in"]
items = given if isinstance(given, list) else [given]
agreed = next((v for v in items if isinstance(v, dict) and "rules" in v and "replays" in v), {})
measured = next((v for v in items if isinstance(v, dict) and "sampled_count" in v), {})
classified = list(measured.get("items") or [])
sampling = agreed.get("sampling")
text = (
    (
        "The replays agree with the script on every item, so the agent step is crystallised: the "
        "script labels the batch and only what it cannot label goes back to the agent. "
        if agreed.get("crystallised")
        else "The replays do not agree with the script, so nothing is crystallised and the agent "
        "keeps the step. "
    )
    + (
        f"One item in {sampling.get('one_in')} is sampled back to the agent to keep measuring."
        if sampling
        else "No sampling is set until the equivalence check passes."
    )
    + f" {sum(1 for item in classified if item.get('fallback'))} items fell back to the agent."
)
print(
    json.dumps(
        {
            "summary": text,
            "figures": {
                "replays": int(agreed.get("replays") or 0),
                "agreeing": int(agreed.get("agreeing") or 0),
                "rules": len(agreed.get("rules") or {}),
                "sampled": int(measured.get("sampled_count") or 0),
                "fallbacks": sum(1 for item in classified if item.get("fallback")),
                "batch": len(classified),
            },
            "crystallised": bool(agreed.get("crystallised")),
            "equivalent": bool(agreed.get("equivalent")),
            "sampling": sampling,
            "rules": agreed.get("rules") or {},
            "wrong": agreed.get("wrong") or [],
            "items": classified,
            "samples": measured.get("samples") or [],
            "agreement": measured.get("agreement"),
        }
    )
)
