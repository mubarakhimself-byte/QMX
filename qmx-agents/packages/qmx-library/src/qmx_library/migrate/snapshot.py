"""MIGRATION step 0: freeze a copy of the old Libraries and record the acceptance numbers.

`snapshot` copies `library.db` (through SQLite's backup, from a read-only connection),
`artifacts/` and the apps' `artifacts.db` into `<home>/migration/pre/`, then counts from that
copy: items per kind, versions per root, links, memo rows, blobs and their bytes, app artifacts,
app definitions and, when a registry port is given, registry records per kind. A second call
returns the frozen numbers and copies nothing, so the acceptance numbers never move under an
import. The weekly backup (step 0.1) and the server copy stay the operator's on landing day.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
from collections import Counter
from contextlib import closing
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

from qmx_library.migrate import COUNTS, pre
from qmx_library.migrate.from_registry import RegistryRead


@dataclass(frozen=True, slots=True)
class Counts:
    kinds: dict[str, int] = field(default_factory=dict[str, int])
    """Library B items per old kind string."""
    versions: dict[str, int] = field(default_factory=dict[str, int])
    """Library B versions per root id."""
    links: int = 0
    memo: int = 0
    blobs: int = 0
    blob_bytes: int = 0
    app_artifacts: int = 0
    app_definitions: int = 0
    registry: dict[str, int] = field(default_factory=dict[str, int])
    """Registry records per record kind."""

    @classmethod
    def read(cls, home: Path) -> Counts:
        return cls(**json.loads((pre(home) / COUNTS).read_text("utf-8")))


def copy_db(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    uri = f"{source.resolve().as_uri()}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as src, closing(sqlite3.connect(dest)) as dst:
        src.backup(dst)


def definitions(home: Path) -> list[Path]:
    """App definition folders, `<home>/definitions/<hash>/` holding an `app.toml`."""
    return sorted(p.parent for p in (home / "definitions").glob("*/app.toml"))


def snapshot(home: Path, registry: RegistryRead | None = None) -> Counts:
    frozen = pre(home)
    if (frozen / COUNTS).exists():
        return Counts.read(home)
    frozen.mkdir(parents=True, exist_ok=True)
    if (home / "library.db").exists():
        copy_db(home / "library.db", frozen / "library.db")
    if (home / "artifacts").is_dir():
        shutil.copytree(home / "artifacts", frozen / "artifacts", dirs_exist_ok=True)
    if (home / "artifacts.db").exists():
        copy_db(home / "artifacts.db", frozen / "artifacts.db")
    counts = count(home, registry)
    (frozen / COUNTS).write_text(json.dumps(asdict(counts), indent=1, sort_keys=True), "utf-8")
    return counts


def count(home: Path, registry: RegistryRead | None) -> Counts:
    frozen = pre(home)
    kinds: Counter[str] = Counter()
    versions: Counter[str] = Counter()
    links = memo = 0
    if (frozen / "library.db").exists():
        with closing(sqlite3.connect(frozen / "library.db")) as db:
            for (raw,) in db.execute("SELECT data FROM items"):
                data = cast(dict[str, Any], json.loads(raw))
                kinds[str(data["kind"])] += 1
                versions[str(data["root_id"])] += 1
            (links,) = db.execute("SELECT count(*) FROM links").fetchone()
            (memo,) = db.execute("SELECT count(*) FROM memo").fetchone()
    blobs = [p for p in (frozen / "artifacts").glob("*") if p.is_file()]
    apps = 0
    if (frozen / "artifacts.db").exists():
        with closing(sqlite3.connect(frozen / "artifacts.db")) as db:
            (apps,) = db.execute("SELECT count(*) FROM artifacts").fetchone()
    records = Counter(r.kind for r in registry.bound.records) if registry else Counter[str]()
    return Counts(
        kinds=dict(kinds),
        versions=dict(versions),
        links=int(links),
        memo=int(memo),
        blobs=len(blobs),
        blob_bytes=sum(p.stat().st_size for p in blobs),
        app_artifacts=int(apps),
        app_definitions=len(definitions(home)),
        registry=dict(records),
    )
