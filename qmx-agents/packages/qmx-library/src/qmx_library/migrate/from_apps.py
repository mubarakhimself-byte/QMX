"""MIGRATION step 4, without the bucket's run folders (LIB4 imports those): the apps'
`artifacts.db` rows and their definition folders into the store.

Each `artifacts.db` row is an `artifact` whose `content` is the app's blob
`apps/<app>/blobs/<sha>.json` (same bytes, same hash), `fields.output` and
`fields.definition_hash` from its ref, `produced-by` the app's `mini-app-instance` and
`instance-of` the `component` that holds the output's `provides` schema. Each definition folder
`definitions/<hash>/` with an `app.toml` is a `mini-app` whose `bundle.tar` is the folder, packed
in name order with fixed times so one folder is always one blob.
"""

from __future__ import annotations

import io
import json
import sqlite3
import tarfile
import tomllib
import uuid
from contextlib import closing
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from pydantic import JsonValue

from qmx_library.migrate import place, pre, with_legacy
from qmx_library.migrate.snapshot import definitions
from qmx_library.port import Draft, JsonObject, ObjectId
from qmx_library.store import Store


@dataclass(frozen=True, slots=True)
class Imported:
    artifacts: int
    definitions: int
    skipped: int


def tar(folder: Path) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as bundle:
        for path in sorted(p for p in folder.rglob("*") if p.is_file()):
            data = path.read_bytes()
            info = tarfile.TarInfo(path.relative_to(folder).as_posix())
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            bundle.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def once(store: Store, key: str, value: str, draft: Draft) -> tuple[ObjectId, bool]:
    """The object whose `fields.<key>` is `value`, put from `draft` when there is none."""
    found = with_legacy(store, key, value)
    if found is not None:
        return found, False
    return place(store, draft).object_id, True


def instance(store: Store, app: str) -> ObjectId:
    fields: JsonObject = {"legacy_app": app, "app_id": app}
    draft = Draft("mini-app-instance", str(uuid.uuid7()), title=app, fields=fields)
    return once(store, "legacy_app", app, draft)[0]


def component(store: Store, app: str, output: str, schema: JsonValue) -> ObjectId:
    key = sha256(json.dumps([app, output, schema], sort_keys=True).encode()).hexdigest()
    fields: JsonObject = {"legacy_provides": key, "app_id": app, "output": output, "schema": schema}
    draft = Draft("component", str(uuid.uuid7()), title=f"{app} {output}", fields=fields)
    return once(store, "legacy_provides", key, draft)[0]


def import_apps(store: Store, home: Path) -> Imported:
    put = defined = skipped = 0
    index = pre(home) / "artifacts.db"
    rows: list[tuple[str, str]] = []
    if index.exists():
        with closing(sqlite3.connect(index)) as db:
            rows = [(str(r), str(s)) for r, s in db.execute("SELECT ref, schema FROM artifacts")]
    for raw, schema in sorted(rows):
        ref = cast(dict[str, Any], json.loads(raw))
        app, output = str(ref["producer_app"]), str(ref["output"])
        body = (home / "apps" / app / "blobs" / f"{ref['sha256']}.json").read_bytes()
        fields: JsonObject = {
            "legacy_ref": raw,
            "output": output,
            "definition_hash": str(ref["definition_hash"]),
            "producer_app": app,
        }
        relations = [
            ("produced-by", instance(store, app)),
            ("instance-of", component(store, app, output, json.loads(schema))),
        ]
        draft = Draft(
            "artifact",
            str(uuid.uuid7()),
            title=f"{app} {output}",
            fields=fields,
            blobs={"content": body},
            relations=relations,
        )
        _, fresh = once(store, "legacy_ref", raw, draft)
        put, skipped = put + fresh, skipped + (not fresh)
    for folder in definitions(home):
        manifest = tomllib.loads((folder / "app.toml").read_text("utf-8"))
        fields = {
            "legacy_definition": folder.name,
            "manifest": cast(JsonValue, json.loads(json.dumps(manifest, default=str))),
        }
        title = str(manifest.get("name") or manifest.get("id") or folder.name)
        draft = Draft(
            "mini-app",
            str(uuid.uuid7()),
            title=title,
            fields=fields,
            blobs={"bundle.tar": tar(folder)},
        )
        _, fresh = once(store, "legacy_definition", folder.name, draft)
        defined, skipped = defined + fresh, skipped + (not fresh)
    return Imported(put, defined, skipped)
