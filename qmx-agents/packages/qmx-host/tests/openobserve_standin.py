"""A stand-in for OpenObserve: it answers `/healthz` on `ZO_HTTP_ADDR:ZO_HTTP_PORT`, takes OTLP
posts under `/api/default/v1/` only with the root sign-in its environment names, and finds what
it took through `POST /api/default/_search`. With `QMX_STANDIN_DENY` set it prints Windows'
access-denied line and exits 5, as a program that needs administrator rights does."""

import base64
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

if os.environ.get("QMX_STANDIN_DENY"):
    print("Error: Access is denied. (os error 5)", flush=True)
    sys.exit(5)

SIGN_IN = (
    "Basic "
    + base64.b64encode(
        f"{os.environ['ZO_ROOT_USER_EMAIL']}:{os.environ['ZO_ROOT_USER_PASSWORD']}".encode()
    ).decode()
)
TAKEN: list[dict[str, object]] = []


class Answer(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def reply(self, code: int, body: object) -> None:
        text = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(text)))
        self.end_headers()
        self.wfile.write(text)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.reply(200, {"status": "ok"})
        else:
            self.reply(404, {})

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.headers.get("Authorization") != SIGN_IN:
            self.reply(401, {"error": "unauthorized"})
            return
        if self.path.startswith("/api/default/v1/"):
            TAKEN.append({"signal": self.path.rsplit("/", 1)[1], "body": json.loads(body)})
            self.reply(200, {})
        elif self.path == "/api/default/_search":
            self.reply(200, {"total": len(TAKEN), "hits": TAKEN})
        else:
            self.reply(404, {})


ThreadingHTTPServer(
    (os.environ["ZO_HTTP_ADDR"], int(os.environ["ZO_HTTP_PORT"])), Answer
).serve_forever()
