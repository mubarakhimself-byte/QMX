"""QMX's own maintenance, listed apart from his workflows (design 06 section 6).

`GET /api/maintenance` lists the host's jobs (sync to my storage, the monthly upkeep of each
storage, the monthly restore drill, bringing records in and, on This PC, bringing node records
home) and the shipped workflows whose definition is marked `meta.kind = "maintenance"`, each
with its own off switch: a backup job's is one `[backup]` key, the records jobs' is `[records]
on`, and a workflow's are its triggers' enable and disable routes. Turning one off stops it and
nothing else.

Each host job ends by landing a Library `artifact` whose `fields.type` is `maintenance-result`
(`landed`), written as the operator's, whom the host acts for. A workflow of his follows it with
an event trigger on `kind = "artifact"` and `output = "maintenance-result"`, with an agent step if
he wants one; the work itself never moves into the engine.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

from fastapi import APIRouter
from pydantic import JsonValue
from qmx_engine.templates.catalog import PACK
from qmx_library.port import Draft
from qmx_library.principal import MAIN, Principal

type JsonObject = dict[str, JsonValue]

if TYPE_CHECKING:
    from qmx_library.store import Store

    from qmx_host.backups import Backups
    from qmx_host.records import Records

RESULT: Final = "maintenance-result"
MARK: Final = "maintenance"
HOST_JOBS: Final[tuple[tuple[str, str, str], ...]] = (
    ("sync", "Sync to my storage", "on"),
    ("upkeep", "Monthly upkeep of each storage: tidy and read back", "upkeep.on"),
    ("drill", "Monthly restore drill", "upkeep.drill"),
)
"""Each host job: its id, its name and the `[backup]` key that switches it."""
RECORDS_JOB: Final = "records"
RECORDS_NAME: Final = "Bring records in: file every app's journals, bars and readings"
"""The records job, switched by `[records] on` (Part B CONTRACTS section 6)."""


def landed(
    store: Store, job: str, state: str, line: str, extra: Mapping[str, object] | None = None
) -> None:
    """One `maintenance-result` artifact for a host job that ended, with the job's own counts in
    ``extra``. A landing that fails is a line on stderr: it never fails the job."""
    result: JsonObject = {**cast("JsonObject", dict(extra or {})), "job": job, "state": state}
    result["line"] = line
    draft = Draft(
        "artifact",
        None,
        title=f"QMX maintenance: {job} {state}",
        summary=line,
        fields={"type": RESULT, "metadata": result},
        blobs={"content": json.dumps(result, sort_keys=True).encode("utf-8")},
    )
    try:
        store.put(Principal("operator"), draft, on=MAIN, expected_head=None)
    except Exception as failed:  # a result that cannot land leaves the job as it ended
        print(f"maintenance: the {job} result did not land: {failed}", file=sys.stderr)


def marked(pack: Path = PACK) -> list[dict[str, object]]:
    """The shipped workflows marked `meta.kind = "maintenance"`, by id and name."""
    found: list[dict[str, object]] = []
    for path in sorted(pack.glob("*/definition.json")):
        try:
            definition = json.loads(path.read_text(encoding="utf-8"))
        except OSError, ValueError:
            continue
        read = cast("dict[str, object]", definition) if isinstance(definition, dict) else {}
        meta = read.get("meta")
        if isinstance(meta, dict) and cast("dict[str, object]", meta).get("kind") == MARK:
            found.append({"id": read.get("id"), "name": read.get("name")})
    return found


def maintenance_router(
    backups: Backups,
    triggers: Callable[[str], Sequence[Mapping[str, object]]] | None = None,
    records: Records | None = None,
) -> APIRouter:
    """`GET /api/maintenance` over the host's backup service, its records job and `triggers`,
    which lists one installed workflow's triggers (none when it is not installed). Behind the
    bearer."""
    router = APIRouter()

    def listed() -> dict[str, object]:
        plan = backups.plan()
        switches = {"on": plan.on, "upkeep.on": plan.upkeep.on, "upkeep.drill": plan.upkeep.drill}
        places = ["quick", *(s.id for s in plan.sending)]
        kinds = {
            "sync": ["backup", *(f"send:{p}" for p in places[1:])],
            "upkeep": [f"upkeep:{p}" for p in places],
            "drill": ["drill"],
        }
        host: list[dict[str, object]] = []
        for ident, name, key in HOST_JOBS:
            jobs = [backups.jobs.latest(kind) for kind in kinds[ident]]
            running = [job.id for job in jobs if job is not None and job.state == "running"]
            host.append(
                {
                    "id": ident,
                    "kind": "host",
                    "name": name,
                    "on": switches[key],
                    "switch": {"section": "backup", "key": key},
                    "running": running,
                    "output": RESULT,
                }
            )
        if records is not None:
            host.append(
                {
                    "id": RECORDS_JOB,
                    "kind": "host",
                    "name": RECORDS_NAME,
                    "on": records.on(),
                    "switch": {"section": "records", "key": "on"},
                    "running": [],
                    "output": RESULT,
                }
            )
            if records.pull is not None:
                host.append(records.pull.entry(records.on()))
        workflows: list[dict[str, object]] = []
        for workflow in marked():
            found: Sequence[Mapping[str, object]] = []
            installed = False
            if triggers is not None:
                try:
                    found, installed = triggers(str(workflow["id"])), True
                except Exception:
                    found = []
            rows = [
                {
                    "id": t.get("id"),
                    "enabled": t.get("enabled"),
                    "switch": {
                        "on": f"POST /api/triggers/{t.get('id')}/enable",
                        "off": f"POST /api/triggers/{t.get('id')}/disable",
                    },
                }
                for t in found
            ]
            workflows.append(
                {**workflow, "kind": "workflow", "installed": installed, "triggers": rows}
            )
        return {"host": host, "workflows": workflows}

    router.add_api_route("/api/maintenance", listed, methods=["GET"])
    return router
