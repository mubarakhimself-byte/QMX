"""One searcher item per source: the source with the plan's question and what to look for, so
every chunk of searchers works to the same brief. Its inputs, the sources and the plan, are told
apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
found = next(v for v in given if isinstance(v, dict) and "sources" in v)
plan = next(v for v in given if isinstance(v, dict) and "look_for" in v)
print(
    json.dumps(
        [
            source | {"question": plan["question"], "look_for": plan["look_for"]}
            for source in found["sources"]
        ]
    )
)
