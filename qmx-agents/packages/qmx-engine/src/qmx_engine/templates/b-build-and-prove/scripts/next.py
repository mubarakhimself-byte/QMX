"""What the `lineage` block links: the unit the stored verdict judged and the first result it was
tested by. Zero tokens.
"""

import json
import sys

stored = json.load(sys.stdin)["in"]
first = stored["verdict"]["result_ids"][0]
print(json.dumps({"lineage": {"unit": stored["unit"], "result": first}}))
