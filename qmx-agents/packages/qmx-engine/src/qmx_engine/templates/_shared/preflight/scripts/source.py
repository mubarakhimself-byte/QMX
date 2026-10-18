"""Stands in for a feed: prints the ids in the fixture beside this script. A real pre-check reads
its feed here, costs no tokens, and changes its output only when the feed has something new."""

import json
from pathlib import Path

found = json.loads((Path(__file__).parents[1] / "fixtures" / "items.json").read_text("utf-8"))
print(json.dumps({"ids": found["ids"], "source": "feed"}))
