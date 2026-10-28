import tempfile, pathlib, json, time
home = pathlib.Path(tempfile.mkdtemp(dir="."))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_control.server import upload_router
app = FastAPI(); app.include_router(upload_router(home))
c = TestClient(app)
r = c.post("/api/library/upload", content=b"%PDF-1.4 abc", headers={"X-Upload-Name":"a.pdf","Content-Type":"application/pdf"})
print("F5 upload with no server", r.status_code, r.json())
print("F5 staged files", sorted(p.relative_to(home).as_posix() for p in home.rglob("*")))
from qmx_control.library import Library, OPERATOR
from qmx_library.port import Draft
from qmx_library.principal import MAIN
lib = Library(home); store = lib.store
commit = store.put(OPERATOR, Draft("source", title="London breakout notes", fields={"origin":"upload","media_type":"application/pdf","bytes":12}, blobs={"original": open("sample.pdf","rb").read(), "text": b"Sharpe ratio of the London breakout"}), on=MAIN, expected_head=None)
print("F6 put source", commit.object_id[:20])
try: print("F6 legacy get", lib.get(commit.object_id)["kind"])
except Exception as e: print("F6 legacy get fails", type(e).__name__, e)
from qmx_library.view import view, family
t=time.perf_counter(); card = view(store, OPERATOR, commit.object_id, "card").as_json(); dt=(time.perf_counter()-t)*1000
print("F7 card", json.dumps(card)[:300], f"{dt:.1f} ms")
page = view(store, OPERATOR, commit.object_id, "page").as_json()
print("F7 page tabs", [t.get("name") or t.get("title") for t in page["tabs"]])
hits = store.search(OPERATOR, "London", kind="source")
print("F8 search kind=source", len(hits), [h.kind for h in hits])
try: print("F8 search kind=unit", len(store.search(OPERATOR, "London", kind="unit")))
except Exception as e: print("F8", e)
store.close() if hasattr(store,"close") else None
