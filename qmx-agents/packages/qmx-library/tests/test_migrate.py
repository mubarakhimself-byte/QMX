"""MIGRATION steps 0 to 5 on fixture homes: step 0's counts, each importer's mapping and its
collision stop, a rerun that writes nothing, and the dual write that keeps the nightly diff
clean."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from contextlib import closing
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_control.library import Library
from qmx_control.models import LibraryInput, MemoKey
from qmx_control.service import ControlService
from qmx_engine.ledger import redact

from qmx_library.migrate import MigrationAlarm, open_target, pre
from qmx_library.migrate.from_apps import import_apps
from qmx_library.migrate.from_library_b import DualWrite, import_library_b, resolve_alias
from qmx_library.migrate.from_registry import import_registry
from qmx_library.migrate.snapshot import Counts, snapshot
from qmx_library.migrate.verify import dual_diff, verify
from qmx_library.port import LibraryRefused
from qmx_library.principal import MAIN, Principal

OPERATOR = Principal("operator")


def library_b(home: Path) -> dict[str, Any]:
    """Seven versions over five roots, two links and one memo row."""
    lib = Library(home)
    article = lib.save(
        LibraryInput(
            title="Carry paper",
            kind="article",
            content={"text": "carry works"},
            source="https://example.org/carry",
            fetched_date="2026-10-01",
        )
    )
    first = lib.save(LibraryInput(title="Rates", kind="backtest", content={"sharpe": 1.0}))
    second = lib.save(
        LibraryInput(
            title="Rates", kind="backtest", content={"sharpe": 1.1}, previous_id=str(first["id"])
        )
    )
    third = lib.save(
        LibraryInput(
            title="Rates", kind="backtest", content={"sharpe": 1.2}, previous_id=str(second["id"])
        )
    )
    tool = lib.save(LibraryInput(title="Answer", kind="tool-result", content={"rows": 3}))
    lib.save(LibraryInput(title="Run", kind="workflow-result", content={"ok": True}, tags=["x"]))
    key = MemoKey(strategy_version="v1", data_snapshot="s1", engine_version="e1", params={"n": 1})
    memo = lib.memoized(
        key, lambda: LibraryInput(title="Memo", kind="backtest", content={"sharpe": 0.5})
    )
    lib.link(str(article["id"]), str(third["id"]))
    lib.link(str(tool["id"]), str(article["id"]), "cites")
    return {"article": article, "first": first, "third": third, "memo": memo}


def test_a_dry_run_of_library_b_matches_step_0(tmp_path: Path) -> None:
    saved = library_b(tmp_path)
    counts = snapshot(tmp_path)
    with open_target(tmp_path, dry_run=True, redactor=redact) as store:
        done = import_library_b(store, tmp_path)
        ref = f"artifacts/{saved['first']['sha256']}"
        alias = resolve_alias(store, ref)
        third = resolve_alias(store, str(saved["third"]["id"]))
        assert third is not None
        chain = store.get(OPERATOR, third)
        root = store.get(OPERATOR, chain.parents[0]).parents[0]
        main = store.resolve(OPERATOR, chain.item, MAIN)
        article = store.get(OPERATOR, str(resolve_alias(store, str(saved["article"]["id"]))))
    result = verify(tmp_path, tmp_path / "migration/dry/library")

    assert counts.kinds == {"article": 1, "backtest": 4, "tool-result": 1, "workflow-result": 1}
    assert (counts.links, counts.memo, counts.blobs, len(counts.versions)) == (2, 1, 7, 5)
    assert (done.objects, done.skipped, done.edges) == (7, 0, 2)
    assert result.ok, result.render()
    assert result.blobs_checked == 7
    assert alias == root
    assert main == third
    assert (article.kind, article.fields["url"]) == ("source", "https://example.org/carry")


def test_a_rerun_writes_nothing_and_a_late_save_leaves_step_0_frozen(tmp_path: Path) -> None:
    library_b(tmp_path)
    snapshot(tmp_path)
    with open_target(tmp_path, dry_run=True, redactor=redact) as store:
        import_library_b(store, tmp_path)
        again = import_library_b(store, tmp_path)
    Library(tmp_path).save(LibraryInput(title="Late", kind="note", content={}))

    assert (again.objects, again.skipped, again.edges) == (0, 7, 2)
    assert sum(snapshot(tmp_path).kinds.values()) == 7


def test_an_import_refuses_without_a_step_0_copy(tmp_path: Path) -> None:
    library_b(tmp_path)

    with pytest.raises(LibraryRefused) as refused:
        open_target(tmp_path, dry_run=True, redactor=redact)

    assert refused.value.code == "storage_failure"
    assert not (tmp_path / "migration/dry/library").exists()


@dataclass(frozen=True)
class Fp:
    value: str


@dataclass(frozen=True)
class Record:
    kind: str
    stable_id: Fp
    body: dict[str, object]
    contract_format_version: int = 1
    at_birth_parent_refs: tuple[Fp, ...] = ()


@dataclass(frozen=True)
class Pointer:
    alias: str
    target: Fp


@dataclass(frozen=True)
class Pair:
    newer: Fp
    older: Fp


@dataclass(frozen=True)
class AsOf:
    records: Sequence[Record]
    pointers: Sequence[Pointer] = ()
    supersedes: Sequence[Pair] = ()


@dataclass(frozen=True)
class Port:
    bound: AsOf = field(default_factory=lambda: AsOf(()))


def fp(name: str) -> Fp:
    return Fp(f"fp1:sha256:{sha256(name.encode()).hexdigest()}")


def registry() -> Port:
    book1, book2, bot = fp("book1"), fp("book2"), fp("bot")
    records = [
        Record("book-definition", book1, {"note": "v1"}),
        Record("book-definition", book2, {"note": "v2"}),
        Record("bot-definition", bot, {"rule": "trend"}),
    ]
    return Port(AsOf(records, [Pointer("scalping", book2)], [Pair(book2, book1)]))


def started(home: Path, port: Port) -> None:
    home.mkdir(parents=True, exist_ok=True)
    snapshot(home, port)


def test_the_registry_imports_by_kind_with_its_chain_on_main(tmp_path: Path) -> None:
    port = registry()
    started(tmp_path, port)
    with open_target(tmp_path, dry_run=True, redactor=redact) as store:
        done = import_registry(store, tmp_path, port)
        book = store.get(OPERATOR, str(resolve_alias(store, "scalping")))
        main = store.resolve(OPERATOR, book.item, MAIN)
        edges = store.edges_of(book.object_id, reverse=False)
        older = store.get(OPERATOR, book.parents[0])
    result = verify(tmp_path, tmp_path / "migration/dry/library")

    assert (done.objects, done.skipped, done.edges) == (3, 0, 1)
    assert Counts.read(tmp_path).registry == {"book-definition": 2, "bot-definition": 1}
    assert result.ok, result.render()
    assert (book.kind, book.title, main) == ("book", "scalping", book.object_id)
    assert older.fields["body"] == {"note": "v1"}
    assert [(e[1], e[2]) for e in edges] == [("supersedes", older.object_id)]


def test_one_fp1_with_two_contents_stops_the_registry_import_with_an_alarm(
    tmp_path: Path,
) -> None:
    twin = fp("book1")
    port = Port(
        AsOf(
            [
                Record("book-definition", twin, {"note": "v1"}),
                Record("book-definition", twin, {"note": "forged"}),
            ]
        )
    )
    started(tmp_path, port)
    with open_target(tmp_path, dry_run=True, redactor=redact) as store:
        with pytest.raises(MigrationAlarm) as stopped:
            import_registry(store, tmp_path, port)
        placed = store.placements()
    alarms = (tmp_path / "migration/alarms.jsonl").read_text("utf-8").splitlines()

    assert stopped.value.code == "collision"
    assert placed == []
    assert [(json.loads(a)["code"], json.loads(a)["fp1"]) for a in alarms] == [
        ("collision", twin.value)
    ]


def test_an_fp1_already_imported_with_other_content_stops_a_later_import(tmp_path: Path) -> None:
    started(tmp_path, registry())
    forged = Port(AsOf([Record("bot-definition", fp("bot"), {"rule": "forged"})]))
    with open_target(tmp_path, dry_run=True, redactor=redact) as store:
        import_registry(store, tmp_path, registry())
        with pytest.raises(MigrationAlarm) as stopped:
            import_registry(store, tmp_path, forged)
        count = len(store.placements())

    assert stopped.value.code == "collision"
    assert count == 3


def app_home(home: Path) -> str:
    body = json.dumps({"rows": 2}, sort_keys=True, separators=(",", ":")).encode()
    sha = sha256(body).hexdigest()
    (home / "apps/screener/blobs").mkdir(parents=True)
    (home / f"apps/screener/blobs/{sha}.json").write_bytes(body)
    ref = {"producer_app": "screener", "definition_hash": "d1", "output": "rows", "sha256": sha}
    with closing(sqlite3.connect(home / "artifacts.db")) as db, db:
        db.execute("CREATE TABLE artifacts (ref TEXT PRIMARY KEY, schema TEXT NOT NULL)")
        db.execute(
            "INSERT INTO artifacts VALUES (?, ?)",
            (json.dumps(ref), json.dumps({"type": "object"})),
        )
    (home / "definitions/d1").mkdir(parents=True)
    (home / "definitions/d1/app.toml").write_text('id = "screener"\nname = "Screener"\n', "utf-8")
    (home / "definitions/d1/main.py").write_text("print('hi')\n", "utf-8")
    return sha


def test_app_artifacts_and_definitions_import_with_their_relations(tmp_path: Path) -> None:
    sha = app_home(tmp_path)
    counts = snapshot(tmp_path)
    with open_target(tmp_path, dry_run=True, redactor=redact) as store:
        done = import_apps(store, tmp_path)
        again = import_apps(store, tmp_path)
        (artifact,) = store.with_field("artifact", "producer_app", "screener")
        view = store.get(OPERATOR, artifact)
        kinds = [store.get(OPERATOR, to).kind for _, to in view.relations]
        (app,) = store.with_field("mini-app", "legacy_definition", "d1")
        bundle = store.get(OPERATOR, app, blobs="fetch").data["bundle.tar"]
    result = verify(tmp_path, tmp_path / "migration/dry/library")

    assert (counts.app_artifacts, counts.app_definitions) == (1, 1)
    assert (done.artifacts, done.definitions, done.skipped) == (1, 1, 0)
    assert again.skipped == 2
    assert view.blobs["content"].blob_id == f"sha256:{sha}"
    assert sorted(r for r, _ in view.relations) == ["instance-of", "produced-by"]
    assert sorted(kinds) == ["component", "mini-app-instance"]
    assert b"main.py" in bundle
    assert result.ok, result.render()


def test_every_library_save_reaches_both_stores_and_the_diff_stays_clean(tmp_path: Path) -> None:
    saved = library_b(tmp_path)
    snapshot(tmp_path)
    with open_target(tmp_path, dry_run=False, redactor=redact) as store:
        import_library_b(store, tmp_path)
        service = ControlService(tmp_path)
        service.attach_library_mirror(DualWrite(store))
        fresh = service.library_save(LibraryInput(title="New", kind="note", content={"a": 1}))
        newer = service.library_save(
            LibraryInput(
                title="Rates", kind="backtest", content={"sha": 2}, previous_id=saved["third"]["id"]
            )
        )
        events = [cast(dict[str, Any], e["data"]) for e in service.events("library")]
        clean = dual_diff(tmp_path, tmp_path / "library")
        service.library.save(LibraryInput(title="Unmirrored", kind="note", content={}))
        gap = dual_diff(tmp_path, tmp_path / "library")
        latest = store.get(OPERATOR, str(resolve_alias(store, str(newer["id"]))))
        fresh_kind = store.get(OPERATOR, str(resolve_alias(store, str(fresh["id"])))).kind

    assert [e.get("mirror") for e in events if e.get("type") == "saved"] == ["ok", "ok"]
    assert clean.as_json() == {
        "clean": True,
        "old": 9,
        "new": 9,
        "missing": [],
        "other_bytes": [],
        "stale_heads": [],
    }
    assert (gap.clean, gap.old, gap.new, len(gap.missing)) == (False, 10, 9, 1)
    assert latest.fields["legacy_version"] == 4
    assert fresh_kind == "artifact"


def test_the_step_0_copy_is_read_not_the_live_library(tmp_path: Path) -> None:
    library_b(tmp_path)
    snapshot(tmp_path)
    (tmp_path / "library.db").unlink()

    with open_target(tmp_path, dry_run=True, redactor=redact) as store:
        done = import_library_b(store, tmp_path)

    assert done.objects == 7
    assert (pre(tmp_path) / "library.db").exists()
