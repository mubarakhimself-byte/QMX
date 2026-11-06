"""What the `lineage` block links: the unit's pin and the first result it was tested by. Zero
tokens. Its inputs are `Ready to test?`'s answer and the referee step's `verdict`.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
ready = next(r for r in rows if "recorded" in r)
verdict = next(r["verdict"] for r in rows if isinstance(r.get("verdict"), dict))
pin = ready["unit"]["pin"]
print(json.dumps({"lineage": {"unit": pin, "result": verdict["result_ids"][0]}}))
