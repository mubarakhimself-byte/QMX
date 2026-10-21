"""Import the three old Libraries into the store (MIGRATION steps 0 to 5).

A home's migration lives under `<home>/migration/`: `pre/` is step 0's frozen copy and its
`counts.json`, `dry/library/` is the store a dry run fills, and `alarms.jsonl` records every
import that stopped. Importers read only `pre/` and the home's app folders, never the live
`library.db`, and refuse to run before `pre/` exists, so nothing is ever written over the only
copy of anything. Every imported object carries `fields.legacy_*`, which is how `verify` finds it
again and how a rerun skips what is already there.

Refs move as `operator` because `migrator` owns no ref yet (LIB1's `may_advance`); edges are
written by `migrator`, as MIGRATION's tables say.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from qmx_library.kinds import kind
from qmx_library.port import Commit, Draft, LibraryRefused, ObjectId
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Redactor, Store

OPERATOR: Final = Principal("operator")
MIGRATOR: Final = Principal("migrator")
COUNTS: Final = "counts.json"


class MigrationAlarm(LibraryRefused):
    """An import that stopped before writing anything (FM-14)."""


def migration(home: Path) -> Path:
    return home / "migration"


def pre(home: Path) -> Path:
    return migration(home) / "pre"


def dry(home: Path) -> Path:
    return migration(home) / "dry" / "library"


def target(home: Path, *, dry_run: bool) -> Path:
    return dry(home) if dry_run else home / "library"


def open_target(home: Path, *, dry_run: bool, redactor: Redactor) -> Store:
    """The store an import writes: the dry store, or the home's own. Refused before step 0 has
    frozen a copy, since the importers would then read the only one."""
    if not (pre(home) / COUNTS).exists():
        raise LibraryRefused("storage_failure", f"no step 0 snapshot under {pre(home)}")
    return Store.open(target(home, dry_run=dry_run), redactor=redactor, name="pc")


def alarm(home: Path, code: str, detail: Mapping[str, object]) -> MigrationAlarm:
    """Record the alarm beside the migration and return it for the importer to raise."""
    line = {"at": datetime.now(UTC).isoformat(), "code": code, **detail}
    path = migration(home) / "alarms.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, sort_keys=True, default=str) + "\n")
    return MigrationAlarm(code, json.dumps(detail, sort_keys=True, default=str))


def place(store: Store, draft: Draft) -> Commit:
    """Put `draft` onto `main` of its item: a record directly, any other class through its draft
    ref and a merge, which is how `main` moves for a definition or a governed kind."""
    item = str(draft.item)
    if kind(draft.kind).klass == "record":
        return store.put(OPERATOR, draft, on=MAIN, expected_head=head(store, item, MAIN))
    ref = drafts_ref(item)
    done = store.put(OPERATOR, draft, on=ref, expected_head=head(store, item, ref))
    store.merge(OPERATOR, item, from_ref=ref, into=MAIN, strategy="ff-only")
    return done


def head(store: Store, item: str, ref: str) -> ObjectId | None:
    found = store.head(item, ref)
    return None if found is None else found[0]


def with_legacy(store: Store, key: str, value: str) -> ObjectId | None:
    """The first placed object whose `fields.<key>` is `value`, of any kind."""
    row = store.catalog.db.execute(
        "SELECT o.object_id FROM objects o JOIN moves m ON m.new_head = o.object_id "
        "WHERE json_extract(o.fields, '$.' || ?) = ? ORDER BY m.seq LIMIT 1",
        (key, value),
    ).fetchone()
    return None if row is None else str(row[0])
