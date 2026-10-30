"""Extract dictionary entries (slug, title, family folder, family field, aliases) to dict_entries.json."""
import json, re, pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "C:/Users/Mubarak/Desktop/Stats/dictionary")
out = []
for f in sorted(ROOT.glob("*/*.md")):
    text = f.read_text(encoding="utf-8")
    for block in re.split(r"(?m)^## ", text)[1:]:
        head, _, body = block.partition("\n")
        m = re.match(r"([a-z0-9][a-z0-9-]*)(?:\s+[—-]\s+(.*))?$", head.strip())
        if not m or "- **Definition:**" not in body:
            continue
        def field(name):
            mm = re.search(r"- \*\*" + re.escape(name) + r":\*\*\s*(.*)", body)
            return mm.group(1).strip() if mm else ""
        aliases_raw = field("Aliases")
        aliases = [a.strip() for a in re.split(r"[;,]", re.sub(r"\([^)]*\)", "", aliases_raw)) if a.strip()]
        out.append({"slug": m.group(1), "title": (m.group(2) or m.group(1)).strip(),
                    "folder": f.parent.name, "family": field("Family"), "aliases": aliases,
                    "definition": field("Definition")[:300]})
pathlib.Path("dict_entries.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
from collections import Counter
print(len(out)); print(Counter(e["folder"] for e in out))
for e in out: print(e["folder"][:12], "|", e["slug"], "|", e["family"][:40], "|", "; ".join(e["aliases"])[:150])
