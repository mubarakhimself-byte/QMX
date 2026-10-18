"""Stands in for the capture step: prints the source in the fixture beside this script."""

import json
from pathlib import Path

found = json.loads((Path(__file__).parents[1] / "fixtures" / "source.json").read_text("utf-8"))
print(json.dumps(found["sources"]))
