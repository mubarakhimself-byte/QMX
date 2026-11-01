"""Immutable payload references, landed as Library artifacts; the host index never writes an
app's database.

An output is a *leave* (AD-64): the app names one of its `[provides]` contracts, the payload is
validated against that contract, stored by hash in the app's volume, and landed in the Library as
one `artifact` object whose `type` is the provides name. The landing goes through `LibrarySink`,
the seam the host wires to the Library store it owns; with no sink attached the payload is still
hashed, validated and registered here, and only the landing waits. An output whose contract
names a lander skips that sink: it lands through the lander's `close`, against the run the lander
opened for the job (AD-33 change 2).

`provides.<name>.stale_after` makes an output lose freshness: a read past it returns
`stale: true`, the age and the declared share, never an error.

`compatible` and `contract_problems` are the publish gate: when a release changes a provides
schema, every installed app whose `feeds` reads that name must still accept the new shape, or the
publish is refused and the refusal names the consumer.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, Protocol, cast

from jsonschema import Draft202012Validator, validate
from jsonschema.exceptions import ValidationError
from pydantic import BaseModel, ConfigDict, JsonValue

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition
from qmx_apps.volume import Volume

TYPE_KEY: Final = "type"
"""The one key every contract is compared on: an artifact's `type` is its provides name."""


class ArtifactRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    producer_app: str
    definition_hash: str
    output: str
    sha256: str


class Ticket(Protocol):
    """What a lander's `open` hands back. The supervisor reads only the run id it minted."""

    @property
    def run_id(self) -> str: ...


type Ending = Literal["failed", "killed"]
"""How a run the tester never finished ends: its job raised or its leave was refused (`failed`),
or the app stopped or died under it (`killed`)."""


class Lander(Protocol):
    """A core lander the host registers by name (AD-33 change 2, Part B CONTRACTS §3). `open`
    answers None for an app version that lands nothing through it. All three are idempotent by
    run id, so a retry writes nothing twice."""

    def open(
        self, app_id: str, version: str, job: str, inputs: Document, principal: str
    ) -> Ticket | None: ...

    def close(self, landing: Landing) -> str: ...

    def fail(self, ticket: Ticket, reason: str, status: Ending) -> str: ...


@dataclass(frozen=True, slots=True)
class Run:
    """A job its lander opened: the lander, its ticket and the run folder in the app's volume."""

    name: str
    lander: Lander
    ticket: Ticket
    folder: Path


@dataclass(frozen=True, slots=True)
class Landing:
    """What a Library sink is handed: one artifact, ready to be one `artifact` object."""

    app_id: str
    version: str
    output: str
    ref: ArtifactRef
    data: JsonValue
    schema: Document
    stale_after: float | None
    at: str
    fields: Document = field(default_factory=dict[str, JsonValue])
    """The Library object's `fields`: its `type` is the provides name and its `metadata` carries
    the reference, so `@app:<id>/<name>` finds it and reads its freshness."""
    lander: str | None = None
    """The lander the contract names; such a landing goes to that lander's `close`."""
    run: Run | None = None
    """The run the lander opened for the job that left this output."""


type LibrarySink = Callable[[Landing], str]
"""`Landing -> the Library object id`. The host closes over the store it holds the writer for."""


def now() -> str:
    return datetime.now(UTC).isoformat()


def _age(landed_at: str, at: str) -> float:
    return (datetime.fromisoformat(at) - datetime.fromisoformat(landed_at)).total_seconds()


class Artifacts:
    def __init__(self, home: Path, library: LibrarySink | None = None) -> None:
        self.home = home
        self.index = home / "artifacts.db"
        self.library = library
        home.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.index)) as db, db:
            db.executescript(
                "PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS artifacts "
                "(ref TEXT PRIMARY KEY, schema TEXT NOT NULL);"
            )
            columns = {row[1] for row in db.execute("PRAGMA table_info(artifacts)").fetchall()}
            for name in ("landed_at", "library_id", "stale_after"):
                if name not in columns:
                    db.execute(f"ALTER TABLE artifacts ADD COLUMN {name}")

    def attach(self, library: LibrarySink | None) -> None:
        self.library = library

    @staticmethod
    def _key(ref: ArtifactRef) -> str:
        return ref.model_dump_json()

    @staticmethod
    def contract(definition: Definition, output: str) -> tuple[Document, float | None]:
        declared = definition.manifest.provides.get(output)
        if declared is None:
            raise AppError("undeclared_output", "The app did not declare this output.")
        return declared.schema_, declared.stale_after

    def save(
        self, definition: Definition, output: str, data: JsonValue, *, run: Run | None = None
    ) -> Document:
        """Validate, store and land one output. An output whose contract names a lander lands
        only from a job that lander opened, through its `close`; any other lands as today."""
        schema, stale_after = self.contract(definition, output)
        lander = definition.manifest.provides[output].lander
        if lander is not None and (run is None or run.name != lander):
            raise AppError(
                "lander_required",
                f"{output} lands only through the {lander} lander, from a job it opened.",
                409,
            )
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
        volume.check_write("blobs").mkdir(parents=True, exist_ok=True)
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
        at = now()
        landing = Landing(
            app_id=definition.manifest.id,
            version=definition.manifest.version,
            output=output,
            ref=ref,
            data=data,
            schema=schema,
            stale_after=stale_after,
            at=at,
            fields={TYPE_KEY: output, "metadata": _metadata(ref, stale_after)},
            lander=lander,
            run=None if lander is None else run,
        )
        if landing.run is not None:
            try:
                library_id = landing.run.lander.close(landing)
            except ValueError as error:
                raise AppError("result_refused", str(error), 422) from error
        else:
            library_id = self.library(landing) if self.library is not None else None
        with closing(sqlite3.connect(self.index)) as db, db:
            db.execute(
                "INSERT OR REPLACE INTO artifacts"
                "(ref, schema, landed_at, library_id, stale_after) VALUES(?,?,?,?,?)",
                (self._key(ref), json.dumps(schema), at, library_id, stale_after),
            )
        return cast(Document, ref.model_dump(mode="json"))

    def accept(self, consumer: Definition, feed: str, value: JsonValue) -> Document:
        declared = consumer.manifest.feeds.get(feed)
        if declared is None:
            raise AppError("undeclared_feed", "The consumer did not declare this feed.")
        try:
            ref = ArtifactRef.model_validate(value)
        except ValueError as error:
            raise AppError("invalid_reference", "Use a registered artifact reference.") from error
        row = self._row(ref)
        source = Volume(self.home, ref.producer_app).check_write(f"blobs/{ref.sha256}.json")
        try:
            encoded = source.read_bytes()
            if hashlib.sha256(encoded).hexdigest() != ref.sha256:
                raise AppError("artifact_corrupt", "The artifact content hash changed.", 409)
            data = cast(JsonValue, json.loads(encoded))
            validate(data, row.schema, cls=Draft202012Validator)
            validate(data, declared.schema_, cls=Draft202012Validator)
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
        accepted: Document = {
            **cast(Document, ref.model_dump(mode="json")),
            "path": target.relative_to(volume.root).as_posix(),
            "landed_at": row.landed_at,
        }
        if row.library_id is not None:
            accepted["library_id"] = row.library_id
        return accepted

    def latest(self, app_id: str, output: str) -> Document | None:
        """The newest landing of `output` by `app_id`, with its freshness: `stale`, its
        `stale_after` and `age_seconds`. None when the app never landed it."""
        found = self._landed(app_id, output)
        if found is None:
            return None
        return self._fresh(found)

    def read(self, ref: Document) -> Document:
        """One registered artifact by its reference, with its freshness."""
        try:
            found = ArtifactRef.model_validate(ref)
        except ValueError as error:
            raise AppError("invalid_reference", "Use a registered artifact reference.") from error
        return self._fresh(self._row(found))

    @dataclass(frozen=True, slots=True)
    class _Found:
        ref: ArtifactRef
        data: JsonValue
        schema: Document
        landed_at: str
        library_id: str | None
        stale_after: float | None

    def _fresh(self, found: Artifacts._Found) -> Document:
        age = _age(found.landed_at, now())
        document = cast(
            Document,
            {
                **cast(Document, found.ref.model_dump(mode="json")),
                "data": found.data,
                "schema": found.schema,
                "landed_at": found.landed_at,
                "age_seconds": round(age, 3),
                "stale_after": found.stale_after,
                "stale": found.stale_after is not None and age > found.stale_after,
            },
        )
        if found.library_id is not None:
            document["library_id"] = found.library_id
        return document

    def _row(self, ref: ArtifactRef) -> Artifacts._Found:
        with closing(sqlite3.connect(self.index)) as db:
            row = db.execute(
                "SELECT schema, landed_at, library_id, stale_after FROM artifacts WHERE ref=?",
                (self._key(ref),),
            ).fetchone()
        if row is None:
            raise AppError("unknown_artifact", "This artifact reference is not registered.", 404)
        return self._found(ref, row)

    def _landed(self, app_id: str, output: str) -> Artifacts._Found | None:
        with closing(sqlite3.connect(self.index)) as db:
            row = db.execute(
                "SELECT ref, schema, landed_at, library_id, stale_after FROM artifacts "
                "WHERE json_extract(ref, '$.producer_app') = ? "
                "AND json_extract(ref, '$.output') = ? AND landed_at IS NOT NULL "
                "ORDER BY landed_at DESC, rowid DESC LIMIT 1",
                (app_id, output),
            ).fetchone()
        if row is None:
            return None
        return self._found(ArtifactRef.model_validate_json(str(row[0])), row[1:])

    def _found(self, ref: ArtifactRef, row: Sequence[object]) -> Artifacts._Found:
        schema = cast(Document, json.loads(str(row[0])))
        landed_at, library_id, stale_after = str(row[1]), row[2], row[3]
        source = Volume(self.home, ref.producer_app).check_write(f"blobs/{ref.sha256}.json")
        try:
            encoded = source.read_bytes()
            if hashlib.sha256(encoded).hexdigest() != ref.sha256:
                raise AppError("artifact_corrupt", "The artifact content hash changed.", 409)
            data = cast(JsonValue, json.loads(encoded))
        except (OSError, ValueError) as error:
            raise AppError(
                "artifact_corrupt", "The artifact content is unreadable.", 409
            ) from error
        return Artifacts._Found(
            ref=ref,
            data=data,
            schema=schema,
            landed_at=landed_at,
            library_id=None if library_id is None else str(library_id),
            stale_after=float(stale_after) if isinstance(stale_after, int | float) else None,
        )


def _metadata(ref: ArtifactRef, stale_after: float | None) -> JsonValue:
    """What the Library object says about its producer: the reference itself, which is how
    `@app:<id>/<name>` and `produces` walks find a landing, and the freshness it declared."""
    return {
        **cast(dict[str, JsonValue], ref.model_dump(mode="json")),
        "producer_app": ref.producer_app,
        "stale_after": stale_after,
    }


def _typed(schema: Mapping[str, object]) -> str | None:
    found = schema.get(TYPE_KEY)
    return found if isinstance(found, str) else None


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in cast("list[object]", value)]


def compatible(provider: Mapping[str, object], consumer: Mapping[str, object]) -> list[str]:
    """Why a `provides` schema does not satisfy a `feeds` schema, one line per mismatch. The
    consumer is the reader, so every property it requires must still be produced and keep its
    type, every value it fixes must hold, and an array's items must still fit. What the consumer
    leaves open accepts anything."""
    problems: list[str] = []
    gave, wanted = _typed(provider), _typed(consumer)
    if wanted is not None and gave is not None and wanted != gave:
        return [f"the producer gives {gave}, the consumer needs {wanted}"]
    allowed = _strings(consumer.get("enum"))
    if allowed and not set(allowed) <= set(_strings(provider.get("enum"))):
        problems.append(f"the producer's values are not among the consumer's {allowed}")
    wanted_properties = consumer.get("properties")
    gave_properties = provider.get("properties")
    if isinstance(wanted_properties, Mapping) and isinstance(gave_properties, Mapping):
        given = cast(Mapping[str, object], gave_properties)
        required = _strings(consumer.get("required"))
        for name, want in cast(Mapping[str, object], wanted_properties).items():
            have = given.get(name)
            if have is None:
                if name in required:
                    problems.append(f"{name} is required by the consumer and never produced")
                continue
            if isinstance(have, Mapping) and isinstance(want, Mapping):
                problems += [
                    f"{name}: {line}"
                    for line in compatible(
                        cast(Mapping[str, object], have), cast(Mapping[str, object], want)
                    )
                ]
    items, wanted_items = provider.get("items"), consumer.get("items")
    if isinstance(items, Mapping) and isinstance(wanted_items, Mapping):
        problems += [
            f"items: {line}"
            for line in compatible(
                cast(Mapping[str, object], items), cast(Mapping[str, object], wanted_items)
            )
        ]
    return problems


def contract_problems(
    published: Definition, consumers: Sequence[Definition], previous: Definition | None
) -> dict[str, list[str]]:
    """Every installed consumer that the new image's `provides` would break, by output name. An
    output whose declaration did not change is not checked; a new or changed one must still fit
    every other app that declares a `feeds` entry of the same name."""
    changed = {
        name: contract
        for name, contract in published.manifest.provides.items()
        if previous is None or previous.manifest.provides.get(name) != contract
    }
    broken: dict[str, list[str]] = {}
    for output, contract in changed.items():
        for consumer in consumers:
            if consumer.manifest.id == published.manifest.id:
                continue
            wanted = consumer.manifest.feeds.get(output)
            if wanted is None:
                continue
            problems = compatible(contract.schema_, wanted.schema_)
            if problems:
                broken.setdefault(output, []).extend(
                    f"{consumer.manifest.id}: {problem}" for problem in problems
                )
    return broken
