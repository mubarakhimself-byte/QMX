"""Check 'covered' claims: does the concept's own regex match the named entries' slug, title or aliases?
A covered concept whose regex finds none of its MQL5 surface terms in the entry names is really 'renamed'."""
import json, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from concepts import C
D = {e["slug"]: e for e in json.load(open("dict_entries.json"))}
bad = []
for x in C:
    if x["status"] != "covered": continue
    names = " | ".join((s + " " + D[s]["title"] + " " + " ; ".join(D[s]["aliases"])).replace("-", " ") for s in [t.strip() for t in x["slugs"].split(";")] if s in D).lower()
    if not re.search(x["rx"], names, re.I): bad.append((x["id"], x["slugs"]))
print(len(bad), "covered claims whose MQL5 wording is not in the entry names:")
for b in bad: print("  ", b)
