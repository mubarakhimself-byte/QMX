"""Reads the request (cards D7 and D8 triggers). `create` builds a new app, `change` builds a new
version of an installed one (a published version is never edited in place), `deprecate` and
`archive` retire one. There is no delete. Zero tokens."""

import json
import sys

KINDS = ("create", "change", "deprecate", "archive")

request = json.load(sys.stdin)["in"]["request"]
if request.get("kind") not in KINDS:
    sys.stderr.write(f"a request is one of {', '.join(KINDS)}; there is no delete")
    raise SystemExit(1)
if request["kind"] != "create" and not request.get("app_id"):
    sys.stderr.write(f"a {request['kind']} request names the app it is for")
    raise SystemExit(1)
print(json.dumps({"request": request, "build": request["kind"] in ("create", "change")}))
