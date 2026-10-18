"""Stands in for the fetch step: prints the papers in the fixture beside this script."""

import json
from pathlib import Path

found = json.loads((Path(__file__).parents[1] / "fixtures" / "papers.json").read_text("utf-8"))
print(json.dumps(found["papers"]))
