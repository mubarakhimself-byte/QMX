"""Read the clippings folder and give every clipping its content hash and its intent key.

The hash is over the bytes, so the same clipping saved twice under two names has one hash. The
intent key is a fingerprint of the kind, the hash and the source, computed with no model (AD-27), so
two runs that see the same clipping compute the same key and the second one can link instead of
working again.
"""

import hashlib
import json
import sys
from pathlib import Path

KIND = "clipping"
SUFFIXES = (".md", ".txt", ".json")


def filled(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = next((line.lstrip("# ").strip() for line in lines if line), "untitled clipping")
    return title[:200]


given = json.load(sys.stdin)["in"]
state = given if isinstance(given, dict) else next((v for v in given if isinstance(v, dict)), {})
folder = state.get("folder")
rows = []
if state.get("fixture"):
    for item in json.loads(
        (Path(__file__).parents[1] / "fixtures" / "clippings.json").read_text("utf-8")
    ):
        body = item["text"].encode("utf-8")
        rows.append(
            {
                "name": item["name"],
                "title": item["name"],
                "source": item.get("source", "fixture"),
                "hash": hashlib.sha256(body).hexdigest(),
                "text": item["text"],
            }
        )
elif folder:
    root = Path(folder).expanduser()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in SUFFIXES):
        body = path.read_bytes()
        text = body.decode("utf-8", "replace")
        rows.append(
            {
                "name": path.name,
                "title": filled(text),
                "source": str(path.parent),
                "hash": hashlib.sha256(body).hexdigest(),
                "text": text,
            }
        )
for row in rows:
    row["intent_key"] = hashlib.sha256(f"{KIND}|{row['hash']}|{row['source']}".encode()).hexdigest()
print(json.dumps({"kind": KIND, "clippings": rows, "count": len(rows)}))
