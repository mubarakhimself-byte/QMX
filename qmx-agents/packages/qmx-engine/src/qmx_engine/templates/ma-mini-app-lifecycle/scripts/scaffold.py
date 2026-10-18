"""Scaffolds the app folder (card D7 step 3 and its gates). Its inputs, the request with the apps
read and the interview, are told apart by shape. Zero tokens.

Refuses an app whose tool list names anything that moves money or touches the broker, or whose
risk class is money: an agent cannot create one. The folder starts at lifecycle `draft`; a change
to an installed app is a new draft version, never an edit of the published one.
"""

import json
import re
import sys

MONEY = re.compile(r"order|position|trade|broker|ctrader|withdraw|deposit|transfer|resize", re.I)

given = json.load(sys.stdin)["in"]
read = next(v for v in given if "request" in v)
interview = next(v for v in given if "provides" in v)
request = read["request"]
problems = [f"tool {t} is a money tool" for t in interview["tools"] if MONEY.search(t)]
if interview["risk_class"] == "money":
    problems.append("an agent cannot create an app of the money risk class")
name = request.get("app_id") or re.sub(r"[^a-z0-9]+", "-", interview["shows"].casefold())[:40]
name = name.strip("-")
version = len((read.get("app") or {}).get("versions", [])) + 1
files = [
    ".claude-plugin/plugin.json",
    "app.toml",
    ".mcp.json",
    "skills/",
    "monitors/",
    "tests/unit/",
    "tests/contract/",
    "evals/",
    "fixtures/",
]
app_toml = {
    "ui.targets": [interview["slot"]],
    "io": {"reads": interview["reads"], "provides": [p["name"] for p in interview["provides"]]},
    "health": {"probe": "monitors/health"},
    "lifecycle": "draft",
}
print(
    json.dumps(
        {
            "ok": not problems,
            "problems": problems,
            "app": name,
            "version": version,
            "files": files,
            "app_toml": app_toml,
            "tools": interview["tools"],
        }
    )
)
