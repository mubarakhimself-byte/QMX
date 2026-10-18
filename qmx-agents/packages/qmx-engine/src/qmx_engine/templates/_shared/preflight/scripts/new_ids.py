"""Hands on only the ids the monitor before it had not seen. On the monitor's first look there is no
earlier value, so every id is new. A fixture replay (`source: fixture`) also counts every id as new,
so a test run always reaches the steps after this one."""

import json
import sys

changed = json.load(sys.stdin)["in"]
value = changed.get("value") or {}
diff = changed.get("diff") or {}
ids = value.get("ids") or []
if value.get("source") == "fixture" or ("ids" not in diff and "after" in diff):
    new = ids
else:
    new = (diff.get("ids") or {}).get("added") or []
print(json.dumps({"ids": new, "source": value.get("source")}))
