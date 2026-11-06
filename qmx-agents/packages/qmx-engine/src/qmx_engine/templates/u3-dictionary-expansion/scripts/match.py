"""Match each sentence of the source to the dictionary entry it states (Appendix F: unmatched
words become append requests, never silent new entries). Zero tokens.

Its input is the run's `source` (`title`, `text`, and `url` and `date` when it has them). QML's
own matcher, `qml.catalogue.index.match`, reads every sentence against every entry's names. Each
unmatched sentence lands as one `append-request` artifact on the run's own ref, keyed by the
source and the sentence, so a rerun lands nothing twice. It prints the matches, the append
requests and the source, and under `sources` the source and its unmatched sentences for the
`marked-sources` block, which is all the agent step reads of them.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

from qml.catalogue.index import match, row
from qmx_tools.gather import STDLIB


def entries():
    """QML's own entries and each one's `block.py` bytes. A script never opens the Library, so an
    entry only the Library holds (the port, a landed content wave) is not here; the agent step
    reads those through the `blocks` rows."""
    found = []
    for folder in sorted(STDLIB.iterdir(), key=lambda f: f.name):
        for version in sorted(folder.iterdir(), key=lambda f: f.name):
            face, code = version / "entry.json", version / "block.py"
            if face.is_file() and code.is_file():
                found.append((json.loads(face.read_text("utf-8")), code.read_bytes()))
    return found


source = json.load(sys.stdin)["in"]["source"]
report = match(source["text"], [row(entry, None) for entry, _ in entries()]).as_json()
cited = {k: source[k] for k in ("title", "url", "date") if source.get(k)}
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
writes = []
for index, request in enumerate(report["append_requests"]):
    body = bodies / f"append-request-{index}.json"
    record = request | {"source": cited}
    body.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    key = hashlib.sha256(f"{source['title']}|{request['sentence']}".encode()).hexdigest()[:16]
    writes.append(
        {
            "op": "put_artifact",
            "type": "append-request",
            "body": f"library/{body.name}",
            "metadata": record,
            "intent_key": f"append|{key}",
        }
    )
print(
    json.dumps(
        {
            "source": source,
            "sentences": report["sentences"],
            "append_requests": report["append_requests"],
            "sources": [
                source,
                {
                    "title": "the sentences no entry states",
                    "text": "\n".join(r["sentence"] for r in report["append_requests"]),
                },
            ],
            "library": writes,
        }
    )
)
