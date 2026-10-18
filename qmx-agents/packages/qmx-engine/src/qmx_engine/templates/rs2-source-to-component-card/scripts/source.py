"""The source and the piece of it to make a component from. The run input gives `source` (`id`,
`title`, `text`) and `piece` ("the volatility filter in section 4"); a run started with
`{"fixture": true}` reads `fixtures/source.json`. Text arrives already captured: turning a PDF
into text needs the PDF tool, which is not wired yet."""

import json
import sys
from pathlib import Path

given = json.load(sys.stdin).get("in") or {}
if given.get("fixture"):
    given = json.loads((Path(__file__).parents[1] / "fixtures" / "source.json").read_text("utf-8"))
source = given.get("source") or {}
if not str(source.get("text") or "").strip() or not str(given.get("piece") or "").strip():
    sys.stderr.write("the run input needs source.text and piece")
    raise SystemExit(2)
captured = {
    "id": str(source.get("id") or "source"),
    "kind": "paper",
    "title": str(source.get("title") or ""),
    "text": str(source["text"]),
}
print(json.dumps({"sources": [captured], "piece": str(given["piece"])}))
