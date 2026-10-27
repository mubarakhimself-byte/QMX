"""A synthetic QMX folder for the backup tests and lanes, never copied from his own folder.

`filled_folder` makes a folder with `qmx_home.resolve(..., create=True)` and fills `data/` with
every kind of file a copy meets: SQLite stores in WAL, the Library's files written once, its
logs (one with a torn last line), a writer's temporary name, a working copy's `.checkout.json`,
price months open and frozen, launch files, evictable caches, locks, a junction, a path past 300
characters and, with `secrets`, a fake file at every secret path, each holding a value planted
nowhere else.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

from qmx_home import Layout, resolve
from qmx_home.files import long_path

STORES = (
    "engine/engine.sqlite",
    "control.db",
    "runs.db",
    "apps.db",
    "portfolio.db",
    "engine/inbox.sqlite",
)
SECRETS = (
    "vault/pairing-key",
    "vault/pairing-key.previous",
    "vault/run-pass-key",
    "vault/tokens.json",
    "rclone.conf",
    "claude/.credentials.json",
    "claude/.claude.json",
    "claude-relayed/.credentials.json",
    "claude-relayed/.claude.json",
)
LEFT_OUT = (
    "library/catalog.db",
    "library/writer.lock",
    "library/uploads/u1.part",
    "library/blobs/fetched/ef/01/ef01aa",
    "library/blobs/transient/0011",
    "library/refs/.claims.json.0123456789abcdef0123456789abcdef",
    "memory/fts.db",
    "memory/hindsight/pg/PG_VERSION",
    "cache/prices/p.parquet",
    "queue/telemetry/t.json",
    "chats/c1/launch.json",
    "settings.tmp",
    "apps/demo/data/heartbeat-1",
    "apps/demo/data/tmp/scratch.bin",
    "locks/demo.lock",
    "engine.lock",
    "control-process.json",
    "router.port",
    "market/binance/btc/ticks/raw/2026-02/.state.tmp",
    "market/binance/btc/ticks/raw/2026-02/.incoming.parquet",
)
MONTH = "market/binance/btc/ticks/raw"


@dataclass(frozen=True, slots=True)
class Filled:
    layout: Layout
    stores: tuple[str, ...]
    written_once: tuple[str, ...]
    planted: dict[str, bytes] = field(default_factory=dict[str, bytes])
    """Each secret path and the value only it holds."""
    long: str | None = None
    junction: str | None = None


def filled_folder(
    root: Path,
    *,
    files: int = 40,
    stores: int = 3,
    store_bytes: int = 64 * 1024,
    once_bytes: int = 256 * 1024,
    long_path_file: bool = True,
    secrets: bool = True,
) -> Filled:
    """A labelled QMX folder at `root` (made empty), filled as the module says."""
    layout = resolve(root, create=True)
    data = layout.data
    made = tuple(STORES[:stores])
    for number, path in enumerate(made):
        _store(data / path, rows=max(1, store_bytes // 1024), seed=number)
    once: list[str] = []
    for index, size in enumerate(_split(once_bytes, 4)):
        body = hashlib.sha256(f"blob {index}".encode()).digest() * (size // 32 + 1)
        digest = hashlib.sha256(body[:size]).hexdigest()
        once.append(_write(data, f"library/blobs/{digest[:2]}/{digest[2:4]}/{digest}", body[:size]))
    objects: list[str] = []
    for index in range(3):
        manifest = json.dumps({"kind": "note", "n": index}).encode()
        digest = hashlib.sha256(manifest).hexdigest()
        objects.append(digest)
        once.append(
            _write(data, f"library/objects/{digest[:2]}/{digest[2:4]}/{digest}.json", manifest)
        )
    once.append(_write(data, "library/blobs/tombstones/dead.json", b'{"reason": "purged"}'))
    moves = [
        {"seq": i + 1, "new_head": f"sha256:{h}", "item": f"i{i}"} for i, h in enumerate(objects)
    ]
    _write(
        data,
        "library/refs/log.jsonl",
        b"".join(json.dumps(m).encode() + b"\n" for m in moves) + b'{"seq": 4, "tor',
    )
    _write(data, "library/refs/claims.json", b"{}")
    _write(data, "library/edges/pc.jsonl", b'{"from": "a", "to": "b"}\n')
    _write(data, "library/checkout/main/i0/.checkout.json", b'{"ref": "main"}')
    frozen = b"PAR1 frozen month"
    fingerprint = hashlib.sha256(frozen).hexdigest()
    once.append(_write(data, f"{MONTH}/2026-01/{fingerprint}.parquet", frozen))
    _write(
        data,
        f"{MONTH}/2026-01/state.json",
        json.dumps({"fingerprint": fingerprint, "frozen": True}).encode(),
    )
    _write(data, f"{MONTH}/2026-02/open.parquet", b"PAR1 open month")
    _write(
        data,
        f"{MONTH}/2026-02/state.json",
        json.dumps({"fingerprint": "open1", "frozen": False}).encode(),
    )
    for path in LEFT_OUT:
        if path.endswith(".db"):
            _store(data / path, rows=2, seed=99)
        else:
            _write(data, path, b"left out")
    _write(data, "settings.toml", b'[engine]\nhost_name = "pc"\n')
    _write(data, "chats/c1.json", b'{"title": "first chat"}')
    _write(data, "vault-store.json", b'{"sealed": "ciphertext"}')
    _write(data, "passes/revoked.json", b"[]")
    _write(data, "apps/demo/data/state.json", b'{"n": 1}')
    _write(data, "apps/demo/road/r.json", b'{"road": 1}')
    _write(data, "claude/projects/p/chat.jsonl", b'{"role": "user"}\n')
    for index in range(files):
        _write(data, f"workspaces/w/file-{index:04d}.txt", f"file {index}\n".encode())
    long: str | None = None
    if long_path_file:
        long = _write(data, f"workspaces/deep/{'a' * 100}/{'b' * 100}/{'c' * 80}.txt", b"deep")
    junction = _junction(data / "claude" / "projects", data / "claude-relayed" / "projects")
    planted: dict[str, bytes] = {}
    if secrets:
        for path in SECRETS:
            planted[path] = f"planted-{path}-{uuid.uuid4().hex}".encode()
            _write(data, path, planted[path])
        planted["../keys/vault.key"] = f"planted-vault-key-{uuid.uuid4().hex}".encode()
        _write(layout.root, "keys/vault.key", planted["../keys/vault.key"])
    return Filled(layout, made, tuple(once), planted, long, junction)


def rows(path: Path) -> dict[str, int]:
    """Each table's row count in the SQLite file at `path`."""
    with closing(sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)) as reading:
        names = [
            str(r[0])
            for r in reading.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        return {
            n: int(reading.execute(f'SELECT count(*) FROM "{n}"').fetchone()[0])  # noqa: S608
            for n in sorted(names)
        }


def _store(path: Path, *, rows: int, seed: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, isolation_level=None)) as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, at TEXT, body BLOB)")
        db.execute("CREATE TABLE IF NOT EXISTS qmx_meta (key TEXT PRIMARY KEY, value TEXT)")
        db.execute("INSERT OR REPLACE INTO qmx_meta VALUES ('min_reader', '1')")
        db.execute("PRAGMA user_version = 1")
        db.execute("BEGIN")
        db.executemany(
            "INSERT INTO events (at, body) VALUES (?, ?)",
            ((f"2026-10-{seed:02d}T{n}", os.urandom(900)) for n in range(rows)),
        )
        db.execute("COMMIT")


def _split(total: int, parts: int) -> list[int]:
    share = max(1, total // parts)
    return [share] * parts


def _write(base: Path, relative: str, data: bytes) -> str:
    target = long_path(base / relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return relative


def _junction(target: Path, link: Path) -> str:
    target.mkdir(parents=True, exist_ok=True)
    link.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))  # pyright: ignore[reportAttributeAccessIssue]
    else:
        os.symlink(target, link, target_is_directory=True)
    return "claude-relayed/projects"
