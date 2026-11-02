"""The `death-certificate` block's last step: land the certificate with its explanation.

Its input is the classify step's `{"certificate", "dead_end", "says"}` and the explain step's
`{"explanation"}`. It lands one `artifact` of type `death-certificate` on the run's own ref, keyed
by the verdict, so the same verdict lands one certificate: the classified fields as its metadata,
with the `dead_end` row beside them, and the explanation as its body. An answer with no
explanation lands the verdict's own words instead. The cause stays the script's; the explanation
never changes it.
"""

import json
import os
import sys
from pathlib import Path

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
classified = next(r for r in rows if "certificate" in r)
explained = next((r for r in rows if isinstance(r.get("explanation"), str)), None)
certificate, dead_end = classified["certificate"], classified["dead_end"]
explanation = explained["explanation"] if explained else classified["says"]

bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "explanation.md").write_text(explanation, encoding="utf-8")
write = {
    "op": "put_artifact",
    "type": "death-certificate",
    "body": "library/explanation.md",
    "metadata": {**certificate, "dead_end": dead_end},
    "intent_key": f"death|{certificate['verdict']}",
}
print(
    json.dumps(
        {
            "certificate": certificate,
            "dead_end": dead_end,
            "explanation": explanation,
            "library": [write],
        }
    )
)
