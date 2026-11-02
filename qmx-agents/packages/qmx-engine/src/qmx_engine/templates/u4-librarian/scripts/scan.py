"""The librarian's scan of the dictionary QML holds and the content wave committed beside it
(`qml/catalogue-seed/wave-1/`, which lands in the Library at each start): repeated code, clashing
names and gaps, each with its receipts. Zero tokens, and it changes nothing: it lands one
`librarian-report` artifact on the run's own ref and moves, edits or publishes no entry.

- `repeated_code`: entries whose `block.py` bytes have one fingerprint under two or more pins.
  Each cluster is one proposal, a single block in place of the copies.
- `clashes`: what QML's corpus check finds across every entry, such as a name that is another
  entry's id or alias, or one pin holding two entries.
- `gaps`: entries the checker refuses, and entries whose next status lacks something, with the
  checker's own words.

Every finding names its pins and fingerprints, which `blocks_get` and `blocks_check` show again.
A script never opens the Library, so an entry only the Library holds (the port's drafts, his own
components) is not scanned here; see the README. A seed entry carries no code, so it is checked
by its face alone.
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import qml
from qml.catalogue.entry import compute_status, corpus_problems
from qml.catalogue.loader import block_fingerprint
from qmx_tools.gather import STDLIB

REPO = Path(qml.__file__).resolve().parents[3]
SEED = REPO / "qml" / "catalogue-seed" / "wave-1"


def golden(entry):
    declared = entry.get("golden")
    cases = declared.get("cases") if isinstance(declared, dict) else None
    path = REPO / cases if isinstance(cases, str) else None
    return json.loads(path.read_text("utf-8")) if path is not None and path.is_file() else None


json.load(sys.stdin)
held = []
for folder in sorted(STDLIB.iterdir(), key=lambda f: f.name):
    for version in sorted(folder.iterdir(), key=lambda f: f.name):
        face, code = version / "entry.json", version / "block.py"
        if face.is_file() and code.is_file():
            entry = json.loads(face.read_text("utf-8"))
            held.append((f"{entry['entry_id']}@{entry['version']}", entry, code.read_bytes()))
pins = {pin for pin, _, _ in held}
seeded = 0
for face in sorted(SEED.rglob("*.json")) if SEED.is_dir() else []:
    entry = json.loads(face.read_text("utf-8"))
    pin = f"{entry.get('entry_id')}@{entry.get('version')}"
    if pin not in pins:
        held.append((pin, entry, None))
        seeded += 1

by_code = defaultdict(list)
gaps = []
for pin, entry, code in held:
    if code is not None:
        by_code[block_fingerprint(code).value].append(pin)
    computed = compute_status(entry, code, golden(entry))
    if computed.status is None:
        gaps.append(
            {"pin": pin, "status": None, "problems": [p.as_json() for p in computed.problems]}
        )
    elif computed.missing:
        gaps.append(
            {"pin": pin, "status": computed.status.value, "missing": list(computed.missing)}
        )
repeated = [
    {"fingerprint": fp, "pins": pins, "proposal": f"one block in place of {', '.join(pins)}"}
    for fp, pins in sorted(by_code.items())
    if len(pins) > 1
]
clashes = [p.as_json() for p in corpus_problems([entry for _, entry, _ in held])]
report = {
    "scanned": {"qml": len(held) - seeded, "seed": seeded},
    "repeated_code": repeated,
    "clashes": clashes,
    "gaps": gaps,
}
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "librarian-report.json").write_text(json.dumps(report, sort_keys=True), "utf-8")
counts = {k: len(v) for k, v in report.items() if isinstance(v, list)} | {"scanned": len(held)}
write = {
    "op": "put_artifact",
    "type": "librarian-report",
    "body": "library/librarian-report.json",
    "metadata": counts,
    "intent_key": f"librarian|{os.environ['QMX_RUN_ID']}",
}
print(json.dumps(report | {"library": [write]}))
