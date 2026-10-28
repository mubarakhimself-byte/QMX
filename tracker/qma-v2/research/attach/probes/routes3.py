from qmx_control.catalog import control_rows, rest_routes
paths = sorted({rest.path for _, rest in rest_routes(control_rows())})
print([p for p in paths if p.startswith(("/api/items", "/api/kinds", "/api/blobs")) or "context" in p])
import re, pathlib
hits = []
for f in pathlib.Path("D:/Temp/attach-plan/qmx-agents/packages").rglob("*.py"):
    if "tests" in f.parts: continue
    t = f.read_text("utf-8", "replace")
    for m in re.finditer(r'"(/api/(items|kinds|blobs)[^"]*|/api/sessions/\{[a-z_]+\}/context[^"]*)"', t):
        hits.append((f.name, m.group(1)))
print("code hits", hits)
