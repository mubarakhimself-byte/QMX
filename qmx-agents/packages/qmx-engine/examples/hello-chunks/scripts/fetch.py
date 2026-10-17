"""Stands in for a fetch from a feed: reads the fixture beside this script and prints one item per
word. A script's cwd is the run's write zone, so the fixture is found from this file's path."""

import json
from pathlib import Path

words = json.loads((Path(__file__).parent.parent / "fixtures" / "words.json").read_text("utf-8"))
print(json.dumps([{"id": i, "word": word} for i, word in enumerate(words)]))
