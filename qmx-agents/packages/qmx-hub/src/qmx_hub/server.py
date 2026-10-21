"""`qmx_hub`, the Library Hub: the same `LibraryPort` over the tailnet (Library AD-11, AD-19).

One process, one store, one writer. The store is the server's Library; the Hub opens it as the
`writer` when `hub.toml` says `primary = server` and as a `replica` when the PC is still primary,
which is the whole of AD-19's flip. Every call carries the pairing key, because identity is not
authorisation (AD-11); the principal travels beside it and the door refuses one that does not
parse.

Routes. `GET /healthz` answers the doctor. `POST /v1/op/<verb>` is one `LibraryPort` verb (or one
replication step) as JSON. `GET|POST /v1/blob` moves blob bytes by hash. `GET /v1/blob/<hex>` too.
`events` is the ref-log read an `event` trigger needs: the rows after a `seq`, each with the
object's kind, fields and the principal that placed it (AD-64).

The Hub monitors itself (AD-11): `hub/health` writes one `test-report` object on `refs/hub/health`
with its ref count, claim count and store size, and the PC's doctor reads it.
"""

from __future__ import annotations

import argparse
import hmac
import json
import signal
import ssl
import sys
import threading
import traceback
from collections.abc import Mapping, Sequence
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Final, cast

from pydantic import JsonValue
from qmx_engine.ledger import redact
from qmx_library.client import draft_from_payload
from qmx_library.port import (
    Claim,
    Commit,
    Draft,
    LibraryRefused,
    ObjectView,
    PurgeResult,
    StoreRole,
)
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_hub.purge import Purged, purge_everywhere

VERSION: Final = "qmx-hub/1"
CONFIG: Final = "hub.toml"
BODY_LIMIT: Final = 64 * 1024 * 1024
ALLOWED: Final = frozenset({"operator", "hub", "migrator", "agent", "run", "engine"})
"""The principals the door accepts. A pairing key names a machine, not a right (AD-11)."""


class Hub:
    """The verbs, as functions over the one store. Every refusal is a `LibraryRefused`."""

    def __init__(self, store: Store, *, buckets: Sequence[Path] = ()) -> None:
        self.store = store
        self.buckets = tuple(buckets)

    def health(self) -> dict[str, Any]:
        refs = self.store.refs()
        return {
            "ok": True,
            "version": VERSION,
            "store": self.store.name,
            "role": self.store.role,
            "primary": "server" if self.store.role == "writer" else "pc",
            "refs": len(refs),
            "objects": len(self.store.object_ids()),
            "blobs": len(self.store.blob_ids()),
            "claims": len(self.store.live_claims()),
            "seq": self.store.catalog.last_seq(),
        }

    def door(self, who: str) -> Principal:
        """The caller's principal, mapped onto this store's engine.

        A forwarded `engine:<other>` becomes `engine:<this store>`: the ref-ownership rule is per
        store (AD-7), and the store that lands an object is the one that owns the ref. The
        original caller is not kept in the ref-log entry; that is a low finding for the backlog.
        """
        principal = Principal.parse(who)
        if principal.who not in ALLOWED:
            raise LibraryRefused("ref_not_owned", f"{who!r} is not a principal the Hub accepts")
        if principal.who == "engine" and principal.id != self.store.name:
            return Principal("engine", self.store.name)
        return principal

    def op(self, verb: str, who: Principal, args: Mapping[str, JsonValue]) -> JsonValue:
        match verb:
            case "refs":
                return cast(
                    JsonValue,
                    [
                        {"item": item, "ref": ref, "head": head, "at": at, "principal": principal}
                        for item, ref, head, at, principal in self.store.refs()
                    ],
                )
            case "object_ids":
                return cast(JsonValue, self.store.object_ids())
            case "blob_ids":
                return cast(JsonValue, self.store.blob_ids())
            case "manifest":
                return cast(JsonValue, self.store.manifest(str(args["object_id"])))
            case "put_manifest":
                return self.store.ingest(cast(Mapping[str, Any], args["manifest"]))
            case "ancestry":
                return cast(JsonValue, sorted(self.store.ancestry_of(str(args["object_id"]))))
            case "mirror":
                at = args.get("at")
                self.store.mirror(
                    str(args["item"]),
                    str(args["ref"]),
                    str(args["head"]),
                    expected_head=None
                    if args.get("expected_head") is None
                    else str(args["expected_head"]),
                    who=str(args.get("principal") or "hub"),
                    at=None if at is None else str(at),
                )
                return None
            case "tombstone":
                return cast(JsonValue, self._tombstone(str(args["blob_id"])))
            case "apply_purge":
                return self.store.apply_purge(
                    str(args["blob_id"]), reason=str(args["reason"]), at=str(args["at"])
                )
            case "purge":
                done = purge_everywhere(
                    self.store,
                    str(args["blob_id"]),
                    str(args["reason"]),
                    who=who,
                    buckets=self.buckets,
                )
                return cast(JsonValue, _purge_payload(done))
            case "claim":
                return cast(
                    JsonValue,
                    _claim_payload(
                        self.store.claim(
                            self.store.engine,
                            str(args["intent_key"]),
                            str(args["run_id"]),
                            int(str(args["ttl"])),
                        )
                    ),
                )
            case "release":
                self.store.release(self.store.engine, str(args["intent_key"]), str(args["run_id"]))
                return None
            case "renew":
                return cast(
                    JsonValue,
                    self.store.renew_claims(
                        self.store.engine, str(args["run_id"]), int(str(args["ttl"]))
                    ),
                )
            case "head":
                found = self.store.head(str(args["item"]), str(args["ref"]))
                return None if found is None else cast(JsonValue, found[0])
            case "put":
                done = self.store.put(
                    who,
                    draft_from_payload(cast(Mapping[str, JsonValue], args["draft"])),
                    on=str(args["on"]),
                    expected_head=None
                    if args.get("expected_head") is None
                    else str(args["expected_head"]),
                )
                return cast(JsonValue, _commit_payload(done))
            case "get":
                return cast(
                    JsonValue,
                    _view_payload(
                        self.store.get(
                            who,
                            str(args["object_id"]),
                            blobs=cast(Any, args.get("blobs") or "meta"),
                        )
                    ),
                )
            case "search":
                kind = args.get("kind")
                return cast(
                    JsonValue,
                    [
                        {
                            "object_id": hit.object_id,
                            "item": hit.item,
                            "kind": hit.kind,
                            "title": hit.title,
                            "rank": hit.rank,
                        }
                        for hit in self.store.search(
                            who,
                            str(args["text"]),
                            kind=None if kind is None else str(kind),
                            limit=int(str(args.get("limit") or 20)),
                        )
                    ],
                )
            case "record_health":
                return cast(JsonValue, self.record_health())
            case "events":
                return cast(
                    JsonValue,
                    self.ref_log(
                        int(str(args.get("after") or 0)),
                        limit=int(str(args.get("limit") or 500)),
                    ),
                )
            case _:
                raise LibraryRefused("not_found", f"no verb {verb!r}")

    def ref_log(self, after: int, *, limit: int = 500) -> list[JsonValue]:
        """The ref-log rows after `after` that placed an object first, with what an `event`
        trigger matches on: the object's kind and fields, and the principal that placed it.

        This is the read a PC-side engine or an `event` trigger makes through the Hub; the row
        order is the log's own `seq`, so a caller's cursor is a `seq` and never a wall clock.
        """
        found: list[JsonValue] = []
        for row in self.store.placements(after)[:limit]:
            object_id = str(row["new_head"])
            manifest = self.store.manifest(object_id) or {}
            placed = self.store.placement(object_id) or ("", "", "")
            fields = manifest.get("fields") if manifest else None
            found.append(
                {
                    "seq": int(row["seq"]),
                    "item": str(row["item"]),
                    "ref": str(row["ref"]),
                    "object_id": object_id,
                    "kind": str(row["kind"]),
                    "producer": str(placed[1]),
                    "at": str(placed[2]),
                    "fields": cast(JsonValue, fields or {}),
                }
            )
        return found

    def record_health(self) -> str:
        """One `test-report` on `refs/hub/health`, so the PC's doctor sees the Hub's lag (AD-11).
        A replica does not write, so it records nothing until the flip makes it the writer."""
        if self.store.role != "writer":
            return ""
        health = self.health()
        draft = Draft(
            "test-report",
            "hub-health",
            title=f"{VERSION} on {self.store.name}",
            summary=f"{health['refs']} refs, {health['objects']} objects",
            fields={
                "workflow_item": "refs/hub/health",
                "status": "passed",
                "content_hash": None,
                "hub": cast(JsonValue, health),
            },
        )
        found = self.store.head("hub-health", "refs/hub/health")
        done = self.store.put(
            Principal("hub"),
            draft,
            on="refs/hub/health",
            expected_head=None if found is None else found[0],
        )
        return done.object_id

    def _tombstone(self, blob_id: str) -> dict[str, Any] | None:
        path = self.store.tombstones / f"{blob_id.removeprefix('sha256:')}.json"
        if not path.exists():
            return None
        return cast(dict[str, Any], json.loads(path.read_bytes()))


def _commit_payload(done: Commit) -> dict[str, JsonValue]:
    return {
        "object_id": done.object_id,
        "item": done.item,
        "ref": done.ref,
        "prev_head": done.prev_head,
        "seq": done.seq,
    }


def _claim_payload(claim: Claim) -> dict[str, JsonValue]:
    return {
        "granted": claim.granted,
        "run_id": claim.run_id,
        "expires": None if claim.expires is None else claim.expires.isoformat(),
    }


def _purge_payload(done: Purged | PurgeResult) -> dict[str, JsonValue]:
    if isinstance(done, Purged):
        return {
            "blob_id": done.blob_id,
            "reason": done.reason,
            "at": done.at,
            "targets": list(done.targets),
            "ref": done.ref,
            "tombstone": done.tombstone,
        }
    return {
        "blob_id": done.blob_id,
        "reason": "",
        "at": "",
        "targets": [],
        "ref": done.ref,
        "tombstone": str(done.tombstone),
    }


def _view_payload(view: ObjectView) -> dict[str, JsonValue]:
    return {
        "object_id": view.object_id,
        "item": view.item,
        "kind": view.kind,
        "class": view.klass,
        "title": view.title,
        "summary": view.summary,
        "fields": view.fields,
        "blobs": {
            slot: {"blob_id": blob.blob_id, "size": blob.size, "media_type": blob.media_type}
            for slot, blob in view.blobs.items()
        },
        "parents": cast(JsonValue, list(view.parents)),
        "relations": [list(relation) for relation in view.relations],
        "annotations": view.annotations,
        "locators": dict(view.locators),
        "purged": cast(JsonValue, sorted(view.purged)),
    }


class Handler(BaseHTTPRequestHandler):
    hub: Hub
    key: str
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        if not self._authorised():
            return
        if self.path == "/healthz":
            self._json(HTTPStatus.OK, self.hub.health())
            return
        if self.path.startswith("/v1/blob/"):
            blob_id = f"sha256:{self.path.removeprefix('/v1/blob/')}"
            try:
                self._bytes(HTTPStatus.OK, self.hub.store.read_blob(blob_id))
            except LibraryRefused as refused:
                self._json(HTTPStatus.NOT_FOUND, {"ok": False, "code": refused.code})
            return
        self._json(HTTPStatus.NOT_FOUND, {"ok": False, "code": "not_found"})

    def do_POST(self) -> None:
        if not self._authorised():
            return
        body = self._body()
        if body is None:
            return
        if self.path == "/v1/blob":
            blob_id = self.hub.store.store_blob(body)
            self._json(HTTPStatus.OK, {"blob_id": blob_id})
            return
        if not self.path.startswith("/v1/op/"):
            self._json(HTTPStatus.NOT_FOUND, {"ok": False, "code": "not_found"})
            return
        verb = self.path.removeprefix("/v1/op/")
        try:
            call = cast(dict[str, JsonValue], json.loads(body))
            who = self.hub.door(str(call["who"]))
            value = self.hub.op(verb, who, cast(Mapping[str, JsonValue], call.get("args") or {}))
        except LibraryRefused as refused:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "code": refused.code, "message": str(refused)},
            )
            return
        except Exception as error:
            traceback.print_exc(file=sys.stderr)
            self._json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "code": "storage_failure", "message": str(error)},
            )
            return
        self._json(HTTPStatus.OK, {"ok": True, "value": value})

    def _authorised(self) -> bool:
        given = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if hmac.compare_digest(given, self.key):
            return True
        self._json(HTTPStatus.UNAUTHORIZED, {"ok": False, "code": "ref_not_owned"})
        return False

    def _body(self) -> bytes | None:
        length = int(self.headers.get("Content-Length") or 0)
        if length > BODY_LIMIT:
            self._json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"ok": False, "code": "storage_failure"}
            )
            return None
        return self.rfile.read(length)

    def _bytes(self, status: HTTPStatus, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: HTTPStatus, body: Mapping[str, object]) -> None:
        data = json.dumps(body, sort_keys=True, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        """One JSON line per call on stderr, which systemd keeps as the journal (AD-11)."""
        sys.stderr.write(
            json.dumps(
                {"hub": self.address_string(), "call": format % args},
                sort_keys=True,
            )
            + "\n"
        )


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(
    hub: Hub,
    *,
    host: str,
    port: int,
    key: str,
    tls: tuple[Path, Path] | None = None,
) -> Server:
    """Bind, publish the port on disk, and answer until the process is stopped."""
    handler = type("BoundHandler", (Handler,), {"hub": hub, "key": key})
    server = Server((host, port), handler)
    if tls is not None:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(tls[0], tls[1])
        server.socket = context.wrap_socket(server.socket, server_side=True)
    bound = int(server.server_address[1])
    hub.record_health()
    print(
        json.dumps(
            {"listening": f"http://{host}:{bound}", "store": hub.store.name, "v": VERSION},
            sort_keys=True,
        ),
        flush=True,
    )
    return server


def config(home: Path) -> dict[str, Any]:
    """`hub.toml`: `primary`, `host`, `port`, `bucket`, `cert`, `key`."""
    path = home / CONFIG
    if not path.exists():
        return {}
    import tomllib  # noqa: PLC0415

    with path.open("rb") as handle:
        document: dict[str, Any] = tomllib.load(handle)
    return document


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qmx-hub")
    parser.add_argument("--home", type=Path, default=Path("/var/lib/qmx"))
    parser.add_argument("--root", type=Path, default=None, help="the store root")
    parser.add_argument("--host", default=None, help="the tailnet address to bind")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--key-file", type=Path, default=None)
    parser.add_argument("--primary", choices=("pc", "server"), default=None)
    parser.add_argument("--bucket", type=Path, action="append", default=None)
    parser.add_argument("--cert", type=Path, default=None)
    parser.add_argument("--tls-key", type=Path, default=None)
    args = parser.parse_args(argv)

    found = config(args.home)
    primary = args.primary or str(found.get("primary", "server"))
    role: StoreRole = "writer" if primary == "server" else "replica"
    root = args.root or args.home / "library"
    key_file = args.key_file or args.home / "vault" / "pairing-key"
    buckets = args.bucket or [Path(str(item)) for item in found.get("bucket", [])]
    if not key_file.exists():
        print(json.dumps({"error": f"no pairing key at {key_file}"}), file=sys.stderr)
        return 2
    key = key_file.read_text(encoding="utf-8").strip()
    with Store.open(root, redactor=redact, name="server", role=role) as store:
        hub = Hub(store, buckets=buckets)
        host = args.host or str(found.get("host", "127.0.0.1"))
        tls = (args.cert, args.tls_key) if args.cert and args.tls_key else None
        server = serve(
            hub, host=host, port=args.port or int(str(found.get("port", 0))), key=key, tls=tls
        )
        (args.home / "hub.port").write_text(str(server.server_address[1]), encoding="utf-8")

        def stop(*_: object) -> None:
            threading.Thread(target=server.shutdown, daemon=True).start()

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            server.serve_forever()
        finally:
            server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
