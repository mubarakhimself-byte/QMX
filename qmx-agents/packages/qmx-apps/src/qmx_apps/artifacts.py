"""Immutable payload references; the host index never writes an app's database."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator, validate
from jsonschema.exceptions import ValidationError
from pydantic import BaseModel, ConfigDict, JsonValue

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition
from qmx_apps.volume import Volume


class ArtifactRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    producer_app: str
    definition_hash: str
    output: str
    sha256: str


class Artifacts:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.index = home / "artifacts.db"
        with closing(sqlite3.connect(self.index)) as db, db:
            db.executescript(
                "PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS artifacts "
                "(ref TEXT PRIMARY KEY, schema TEXT NOT NULL);"
            )

    @staticmethod
    def _key(ref: ArtifactRef) -> str:
        return ref.model_dump_json()

    def save(self, definition: Definition, output: str, data: JsonValue) -> Document:
        schema = definition.manifest.provides.get(output)
        if schema is None:
            raise AppError("undeclared_output", "The app did not declare this output.")
        try:
            validate(data, schema, cls=Draft202012Validator)
        except ValidationError as error:
            raise AppError(
                "invalid_output", "Output does not match the declared provides schema."
            ) from error
        encoded = json.dumps(
            data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
        sha = hashlib.sha256(encoded).hexdigest()
        volume = Volume(self.home, definition.manifest.id)
        target = volume.check_write(f"blobs/{sha}.json")
        temporary = volume.check_write(f"blobs/{sha}.tmp")
        temporary.write_bytes(encoded)
        temporary.replace(target)
        ref = ArtifactRef(
            producer_app=definition.manifest.id,
            definition_hash=definition.hash,
            output=output,
            sha256=sha,
        )
        with closing(sqlite3.connect(self.index)) as db, db:
            db.execute(
                "INSERT OR IGNORE INTO artifacts VALUES(?,?)", (self._key(ref), json.dumps(schema))
            )
        return cast(Document, ref.model_dump(mode="json"))

    def accept(self, consumer: Definition, feed: str, value: JsonValue) -> Document:
        schema = consumer.manifest.feeds.get(feed)
        if schema is None:
            raise AppError("undeclared_feed", "The consumer did not declare this feed.")
        try:
            ref = ArtifactRef.model_validate(value)
        except ValueError as error:
            raise AppError("invalid_reference", "Use a registered artifact reference.") from error
        with closing(sqlite3.connect(self.index)) as db:
            row = db.execute(
                "SELECT schema FROM artifacts WHERE ref=?", (self._key(ref),)
            ).fetchone()
        if row is None:
            raise AppError("unknown_artifact", "This artifact reference is not registered.", 404)
        source = Volume(self.home, ref.producer_app).check_write(f"blobs/{ref.sha256}.json")
        try:
            encoded = source.read_bytes()
            if hashlib.sha256(encoded).hexdigest() != ref.sha256:
                raise AppError("artifact_corrupt", "The artifact content hash changed.", 409)
            data = cast(JsonValue, json.loads(encoded))
            validate(data, json.loads(row[0]), cls=Draft202012Validator)
            validate(data, schema, cls=Draft202012Validator)
        except (OSError, ValueError, ValidationError) as error:
            raise AppError(
                "invalid_feed", "Artifact content does not match the declared schemas."
            ) from error
        volume = Volume(self.home, consumer.manifest.id)
        target = volume.check_write(f"blobs/imports/{ref.sha256}.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_bytes(encoded)
        temporary.replace(target)
        return {
            **cast(Document, ref.model_dump(mode="json")),
            "path": target.relative_to(volume.root).as_posix(),
        }
