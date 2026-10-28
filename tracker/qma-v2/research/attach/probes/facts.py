import json, base64, tempfile, pathlib, traceback
from qmx_control.context import parse, ContextRefused
for ref in ("@file:C:/x.pdf", "@url:https://a.b", "@youtube:abc", "@folder:D:/r"):
    try: parse(ref)
    except ContextRefused as e: print("F1", ref, e.code, e.message)
from qmx_router.gpt import translate
from qmx_router import chat_lane
pdf = base64.b64encode(open("sample.pdf","rb").read()).decode()
img = {"type":"image","source":{"type":"base64","media_type":"image/png","data":"iVBORw0KGgo="}}
doc = {"type":"document","source":{"type":"base64","media_type":"application/pdf","data":pdf},"title":"s.pdf"}
txt = {"type":"document","source":{"type":"text","media_type":"text/plain","data":"hello"}}
req = {"model":"x","messages":[{"role":"user","content":[{"type":"text","text":"read"}, img, doc, txt]}],"max_tokens":10}
t = translate.to_responses(req, model="gpt-x")
body = t.body if hasattr(t,"body") else t
s = json.dumps(body if isinstance(body,dict) else getattr(t,"__dict__",str(t)), default=str)
print("F2 gpt types", [p.get("type") for it in (body.get("input") if isinstance(body,dict) else []) for p in (it.get("content") if isinstance(it.get("content"),list) else [])])
for blocks in ([img, txt], [doc]):
    r = {"model":"x","messages":[{"role":"user","content":[{"type":"text","text":"read"}, *blocks]}],"max_tokens":10}
    try:
        c = chat_lane.to_chat(r, model="m"); b = c.body if hasattr(c,"body") else c
        print("F3 chat ok", [p.get("type") for m in b["messages"] for p in (m["content"] if isinstance(m["content"],list) else [])])
    except Exception as e: print("F3 chat refused", type(e).__name__, e)
from qmx_router.registry import ModelRow
from qmx_router.normalise import normalise
row = ModelRow(qmx_id="openrouter/moonshotai/kimi-k2.5", provider="openrouter", native="moonshotai/kimi-k2.5")
print("F4 row vision/pdf", row.vision, row.pdf)
out = json.loads(normalise(row, json.dumps(req).encode(), {}).body)
print("F4 normalised", [b.get("type") + (":"+b.get("text","")[:40] if b["type"]=="text" else "") for b in out["messages"][0]["content"]])
