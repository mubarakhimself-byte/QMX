"""The entry checker on every draft the agent wrote; only a draft that passes lands. Zero tokens.

Its inputs are the match step's answer and the agent's `entries` (each `{for, entry, code}`) and
`already_held`. Each draft is checked by QML's own checker, `compute_status`, with its code, and
against the whole catalogue by `corpus_problems`, so a name another entry holds is refused. The
status is the script's; an agent never types one. A draft that passes lands as one `entry-draft`
artifact on the run's own ref with its computed status and fingerprint: a governed draft, never
published here. A draft that fails lands nothing and is listed under `refused` with every
problem. A sentence the agent says an entry already holds is listed under `already_held`; its
append request stands.
"""

import json
import os
import sys
from pathlib import Path

from qml.catalogue.entry import compute_status, corpus_problems
from qml.catalogue.loader import block_fingerprint
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


given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
matched = next(r for r in rows if "append_requests" in r)
written = next((r for r in rows if "entries" in r), {"entries": [], "already_held": []})
others = [entry for entry, _ in entries()]
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
drafts, refused, writes = [], [], []
for index, draft in enumerate(written["entries"]):
    entry, code = draft["entry"], draft.get("code")
    source = None if code is None else code.encode("utf-8")
    computed = compute_status(entry, source)
    pin = f"{entry.get('entry_id')}@{entry.get('version')}"
    clashes = [p for p in corpus_problems([*others, entry]) if p.where.startswith(f"{pin}@")]
    problems = [p.as_json() for p in (*computed.problems, *clashes)]
    if computed.status is None or problems:
        refused.append({"for": draft["for"], "pin": pin, "problems": problems})
        continue
    found = {
        "for": draft["for"],
        "pin": pin,
        "status": computed.status.value,
        "missing": list(computed.missing),
        "fingerprint": None if source is None else block_fingerprint(source).value,
    }
    body = bodies / f"entry-draft-{index}.json"
    body.write_text(json.dumps({"entry": entry, "code": code}, sort_keys=True), encoding="utf-8")
    writes.append(
        {
            "op": "put_artifact",
            "type": "entry-draft",
            "body": f"library/{body.name}",
            "metadata": found,
            "intent_key": f"entry-draft|{pin}|{found['fingerprint']}",
        }
    )
    drafts.append(found)
print(
    json.dumps(
        {
            "source": matched["source"]["title"],
            "matched": [s for s in matched["sentences"] if s["entry"] != "unmatched"],
            "append_requests": [r["sentence"] for r in matched["append_requests"]],
            "drafts": drafts,
            "refused": refused,
            "already_held": written.get("already_held", []),
            "library": writes,
        }
    )
)
