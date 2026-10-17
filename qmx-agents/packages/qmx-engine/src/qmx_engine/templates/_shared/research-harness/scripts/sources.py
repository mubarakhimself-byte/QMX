"""Stands in for the search step: prints the sources in the fixture beside this script."""

import json
from pathlib import Path

found = json.loads((Path(__file__).parents[1] / "fixtures" / "sources.json").read_text("utf-8"))
print(json.dumps(found["sources"]))
