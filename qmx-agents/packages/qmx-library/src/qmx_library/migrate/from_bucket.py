"""MIGRATION step 4's bucket run folders: one folder becomes one `workflow-run` (LIB4).

The bucket is the directory the server pushes to (AD-16), and it holds what the old remote runs
left behind:

    runs/<run_id>/manifest.json    the run: its status, mode, workflow item and placement
    runs/<run_id>/artifacts/<sha>  the run's blobs, by hash
    blobs/<sha> | blobs/ab/cd/<sha>  the same blobs when a run folder only references them

One run folder becomes one `workflow-run` object on `refs/runs/<run_id>` (the ref is owned by
`run:<run_id>`, which is the principal the import writes as), and each listed blob becomes one
`artifact` object on the same ref with `produced-by → workflow-run`. The blobs move byte for byte,
so their hashes are the old names. A folder whose manifest is unreadable is skipped and counted,
never half-imported; a rerun skips every run ref that already has a head.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

from pydantic import JsonValue

from qmx_library.port import Draft, JsonObject
from qmx_library.principal import Principal, runs_ref
from qmx_library.store import Store

STATUSES: Final = frozenset(
    {"queued", "running", "waiting", "passed", "failed", "stopped", "interrupted"}
)
MANIFEST: Final = "manifest.json"


@dataclass(frozen=True, slots=True)
class Imported:
    runs: int
    artifacts: int
    blobs: int
    skipped: int


def blob_bytes(bucket: Path, hexdigest: str) -> bytes | None:
    """The bucket's copy of a blob, wherever it keeps it."""
    for path in (
        bucket / "blobs" / hexdigest,
        bucket / "blobs" / hexdigest[:2] / hexdigest[2:4] / hexdigest,
    ):
        if path.exists():
            return path.read_bytes()
    return None


def run_folders(bucket: Path) -> list[Path]:
    runs = bucket / "runs"
    if not runs.is_dir():
        return []
    return sorted(path for path in runs.iterdir() if path.is_dir())


def draft_for(manifest: dict[str, Any], run_id: str) -> Draft:
    """One `workflow-run` object: the manifest's own words, never an invented status."""
    status = str(manifest.get("status", "interrupted"))
    fields: JsonObject = {
        "run_id": run_id,
        "mode": str(manifest.get("mode", "live")),
        "status": status if status in STATUSES else "interrupted",
        "workflow_item": manifest.get("workflow_item") or manifest.get("target"),
        "legacy_bucket_run": True,
    }
    placement = manifest.get("placement")
    if isinstance(placement, dict):
        fields["placement"] = cast(JsonValue, placement)
    title = str(manifest.get("title") or f"Remote run {run_id[:8]}")
    summary = str(manifest.get("summary") or "")
    return Draft("workflow-run", run_id, title=title, summary=summary, fields=fields)


def import_bucket(store: Store, bucket: Path) -> Imported:
    """Every run folder under `bucket/runs/` into the store, at most once each."""
    runs = artifacts = blobs = skipped = 0
    for folder in run_folders(bucket):
        manifest_path = folder / MANIFEST
        if not manifest_path.exists():
            skipped += 1
            continue
        try:
            manifest = cast(dict[str, Any], json.loads(manifest_path.read_bytes()))
        except ValueError:
            skipped += 1
            continue
        run_id = str(manifest.get("run_id") or folder.name)
        who = Principal("run", run_id)
        if store.head(run_id, runs_ref(run_id)) is not None:
            skipped += 1
            continue
        run = store.put(who, draft_for(manifest, run_id), on=runs_ref(run_id), expected_head=None)
        runs += 1
        head = run.object_id
        for entry in cast(list[dict[str, Any]], manifest.get("artifacts") or []):
            hexdigest = str(entry.get("sha256") or entry.get("blob") or "")
            body = (folder / "artifacts" / hexdigest).read_bytes() if hexdigest else None
            if body is None and hexdigest:
                body = blob_bytes(bucket, hexdigest)
            if body is None:
                skipped += 1
                continue
            artifact = Draft(
                "artifact",
                title=str(entry.get("name") or hexdigest[:12]),
                fields={
                    "type": str(entry.get("type", "run-output")),
                    "metadata": {"run_id": run_id, "sha256": hexdigest},
                },
                blobs={str(entry.get("slot", "content")): body},
                relations=[("produced-by", run.object_id)],
            )
            committed = store.put(who, artifact, on=runs_ref(run_id), expected_head=head)
            head = committed.object_id
            artifacts += 1
            blobs += 1
    return Imported(runs, artifacts, blobs, skipped)
