"""At the end of each drive of a run: the span tree as a journal, that journal as a `trace`
artifact on the run's branch, and the run summary as a `workflow-run` object, linked `produced-by`
and `run-of` (AD-15, LIBRARY-REQUESTS L13, L14).

The journal is `<home>/engine/runs/<run_id>/trace-<last seq>.jsonl`, written through
`qmx_ledger.RunJournal` with the run's recorded clock, so exporting the same ledger twice writes
nothing new. It stays out of `<home>/runs/`, whose journals `qmx_control` lists as its own runs.
Each drive adds one `workflow-run` object (SOLUTION-DESIGN 3.1); all of a run's writes carry the
principal `run:<run_id>`.

Every file a finished node listed as an artifact is read from the run's write zone and stored as a
`run-file` artifact linked `produced-by` to the summary, once per run: a later drive stores only
the files no earlier summary of the run already holds.

The journal on disk is a store too, so each record passes the one redaction (AD-37) before it is
appended; the Library adapter redacts the artifact and the summary again as it writes them.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import cast

from pydantic import JsonValue
from qmx_ledger.journal import RunJournal

from qmx_engine.ledger.events import Event
from qmx_engine.ledger.redact import redact_json
from qmx_engine.ledger.spans import Span
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import JsonObject, LibraryPort, Mode, RunStatus, RunSummary, Stored
from qmx_engine.runner import workspace

PLACEMENT: JsonObject = {"name": "pc", "kind": "local"}


def totals(events: list[Event], spans: list[Span]) -> JsonObject:
    tokens: dict[str, int] = {}
    for span in spans:
        for name, count in span.tokens.items():
            tokens[name] = tokens.get(name, 0) + count
    costs = [span.cost_estimate_usd for span in spans if span.cost_estimate_usd is not None]
    return {
        "attempts": len(spans),
        "events": len(events),
        "tokens": dict[str, JsonValue](tokens),
        "cost_estimate_usd": sum(costs) if costs else None,
    }


def clean(record: JsonObject) -> JsonObject:
    return cast(JsonObject, redact_json(record)[0])


def export(
    home: Path,
    run_id: str,
    library: LibraryPort,
    *,
    workflow_item: str,
    object_id: str,
    mode: Mode,
    status: RunStatus,
    reason: str | None,
    started_by: str,
) -> Stored:
    with Reader.open(home) as reader:
        events = reader.events(run_id)
        spans = reader.spans(run_id)
    summed = totals(events, spans)
    path = home / "engine" / "runs" / run_id / f"trace-{events[-1].seq}.jsonl"
    if not path.exists():
        at = events[-1].at
        with RunJournal(path, run_id, clock=lambda: at) as journal:
            for span in spans:
                journal.append("span", clean(asdict(span)))
            journal.append("summary", clean({"status": status, "reason": reason, "totals": summed}))
    principal = f"run:{run_id}"
    trace = library.put_artifact(
        path.read_bytes(),
        "trace",
        {"format": "jsonl", "spans": len(spans), "journal": path.name},
        run_id=run_id,
        principal=principal,
    )
    files = run_files(home, run_id, events, library)
    summary = library.put_run_summary(
        RunSummary(
            run_id=run_id,
            workflow_item=workflow_item,
            object_id=object_id,
            mode=mode,
            status=status,
            reason=reason,
            totals=summed,
            placement=PLACEMENT,
            trace_artifact_hash=trace.blob,
            started_by=started_by,
        ),
        principal=principal,
    )
    library.link(trace.object_id, "produced-by", summary.object_id, principal=principal)
    for stored in files:
        library.link(stored.object_id, "produced-by", summary.object_id, principal=principal)
    library.link(summary.object_id, "run-of", object_id, principal=principal)
    return summary


def run_files(home: Path, run_id: str, events: list[Event], library: LibraryPort) -> list[Stored]:
    """The artifact files of the run's finished nodes not yet stored by an earlier drive."""
    held = {
        (str(meta.get("node_id")), str(meta.get("path")))
        for earlier in library.objects(run_id, "workflow-run")
        for edge in library.edges(earlier.object_id, "produced-by", reverse=True)
        if isinstance(meta := library.get(edge.from_id).fields.get("metadata"), dict)
    }
    workflow_id = str(events[0].data.get("workflow_id"))
    zone = workspace(home, workflow_id) / "runs" / run_id
    stored: list[Stored] = []
    for event in events:
        listed = event.data.get("artifacts") if event.kind == "node_finished" else None
        if not isinstance(listed, list):
            continue
        node_id = str(event.data.get("node_id"))
        for name in listed:
            if (node_id, str(name)) in held:
                continue
            held.add((node_id, str(name)))
            stored.append(
                library.put_artifact(
                    (zone / str(name)).read_bytes(),
                    "run-file",
                    {"node_id": node_id, "path": str(name)},
                    run_id=run_id,
                    principal=f"run:{run_id}",
                )
            )
    return stored
