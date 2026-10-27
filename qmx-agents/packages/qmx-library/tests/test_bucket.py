"""The bucket's run folders: one folder becomes one `workflow-run` with its artifacts, and a rerun
imports nothing twice (MIGRATION step 4, LIB4)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from hashlib import sha256
from pathlib import Path

import pytest
from qmx_engine.ledger import redact

from qmx_library.migrate.from_bucket import Imported, import_bucket
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")
BODY = b"the run output"


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact, name="server") as opened:
        yield opened


def bucket_with_one_run(tmp_path: Path) -> Path:
    folder = tmp_path / "bucket" / "runs" / "run-7"
    (folder / "artifacts").mkdir(parents=True)
    hexdigest = sha256(BODY).hexdigest()
    (folder / "artifacts" / hexdigest).write_bytes(BODY)
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": "run-7",
                "status": "passed",
                "mode": "live",
                "workflow_item": "paper",
                "title": "A remote run",
                "placement": {"name": "contabo"},
                "artifacts": [{"name": "out.txt", "sha256": hexdigest, "type": "run-output"}],
            }
        ),
        encoding="utf-8",
    )
    return tmp_path / "bucket"


def test_one_run_folder_becomes_one_workflow_run_with_its_artifact(
    store: Store, tmp_path: Path
) -> None:
    done = import_bucket(store, bucket_with_one_run(tmp_path))

    assert done == Imported(runs=1, artifacts=1, blobs=1, skipped=0)
    (run_id, ref, head, _at, principal) = store.refs()[0]
    assert (run_id, ref, principal) == ("run-7", "refs/runs/run-7", "run:run-7")
    view = store.get(OPERATOR, head, blobs="fetch")
    assert (view.kind, view.title) == ("artifact", "out.txt")
    assert view.data["content"] == BODY
    run = store.get(OPERATOR, view.relations[0][1])
    assert (run.kind, run.fields["status"], run.fields["workflow_item"]) == (
        "workflow-run",
        "passed",
        "paper",
    )


def test_a_rerun_imports_nothing_twice(store: Store, tmp_path: Path) -> None:
    bucket = bucket_with_one_run(tmp_path)
    import_bucket(store, bucket)

    again = import_bucket(store, bucket)

    assert again == Imported(runs=0, artifacts=0, blobs=0, skipped=1)


def test_a_run_whose_manifest_does_not_say_live_or_test_imports_as_unknown(
    store: Store, tmp_path: Path
) -> None:
    for run_id, mode in (("run-a", None), ("run-b", "remote"), ("run-c", "test")):
        folder = tmp_path / "bucket" / "runs" / run_id
        folder.mkdir(parents=True)
        manifest = {"run_id": run_id, "status": "passed", "workflow_item": "paper"}
        if mode is not None:
            manifest["mode"] = mode
        (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    done = import_bucket(store, tmp_path / "bucket")

    modes = {item: store.get(OPERATOR, head).fields["mode"] for item, _, head, _, _ in store.refs()}
    assert done == Imported(runs=3, artifacts=0, blobs=0, skipped=0)
    assert modes == {"run-a": "unknown", "run-b": "unknown", "run-c": "test"}
