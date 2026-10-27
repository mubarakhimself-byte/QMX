"""At the end of each drive of a run: the span tree as a journal, that journal as a `trace`
artifact on the run's branch, and the run summary as a `workflow-run` object, linked `produced-by`
and `run-of` (AD-15, LIBRARY-REQUESTS L13, L14).

The journal is `<home>/engine/runs/<run_id>/trace-<last seq>.jsonl`, written through
`qmx_ledger.RunJournal` with the run's recorded clock, so exporting the same ledger twice writes
nothing new. It stays out of `<home>/runs/`, whose journals `qmx_control` lists as its own runs.
Each drive adds one `workflow-run` object (SOLUTION-DESIGN 3.1); all of a run's writes carry the
principal `run:<run_id>`. Its `placement` is where the run ran (`ran_on`), with the line its run
card shows.

Every file a finished node listed as an artifact is read from the run's write zone and stored as a
`run-file` artifact linked `produced-by` to the summary, once per run: a later drive stores only
the files no earlier summary of the run already holds. Every artifact a script node wrote through
the runner (its `library_written` receipts) is linked `produced-by` to the summary too, so a
duplicate check finds it once the run passed. A run that ran on the fake provider says so on its
summary, and the Library lands nothing of it.

The journal on disk is a store too, so each record passes the one redaction (AD-37) before it is
appended; the Library adapter redacts the artifact and the summary again as it writes them.
"""

from __future__ import annotations

import logging
import platform
from dataclasses import asdict
from pathlib import Path
from typing import Final, cast

from pydantic import JsonValue
from qmx_ledger.journal import RunJournal

from qmx_engine.ledger.events import Event
from qmx_engine.ledger.redact import redact_json
from qmx_engine.ledger.spans import Span
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import JsonObject, LibraryPort, Mode, RunStatus, RunSummary, Stored
from qmx_engine.settings import PC
from qmx_engine.workers.zones import RunZone

LOG = logging.getLogger(__name__)

PLACE_FIELDS: Final = ("place", "place_id", "machine", "placed_by")
BY: Final[dict[str, str]] = {
    "default": "by default",
    "chosen": "as chosen",
    "spilled": "spilled over",
    "stand_in": "standing in",
}
"""How the run card says why a run ran where it did."""


def ran_on(events: list[Event]) -> JsonObject:
    """Where the run ran (AD-72), and the run card's line for it: the record of its first attempt
    placed on a place it named, so a trigger node or any other node on This PC by default never
    hides work that ran on a named place; else its first attempt's; else This PC by default when no
    attempt started."""
    started = [e.data for e in events if e.kind == "node_started" and "place" in e.data]
    named = (data for data in started if data.get("placed_by") != "default")
    first = next(named, started[0] if started else None)
    record: JsonObject = (
        {key: first.get(key) for key in PLACE_FIELDS}
        if first is not None
        else {"place": PC, "place_id": PC, "machine": platform.node(), "placed_by": "default"}
    )
    record["line"] = f"ran on {record['place']}, {BY.get(str(record['placed_by']), 'by default')}"
    return record


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
            placement=ran_on(events),
            trace_artifact_hash=trace.blob,
            started_by=started_by,
            fake=events[0].kind == "run_created" and events[0].data.get("fake") is True,
        ),
        principal=principal,
    )
    library.link(trace.object_id, "produced-by", summary.object_id, principal=principal)
    for stored in files:
        library.link(stored.object_id, "produced-by", summary.object_id, principal=principal)
    for made in written(events):
        library.link(made, "produced-by", summary.object_id, principal=principal)
    library.link(summary.object_id, "run-of", object_id, principal=principal)
    return summary


def written(events: list[Event]) -> list[str]:
    """The artifacts the run's finished script nodes wrote, by their receipts."""
    found: dict[str, None] = {}
    for event in events:
        outputs = event.data.get("outputs") if event.kind == "node_finished" else None
        main = outputs.get("main") if isinstance(outputs, dict) else None
        receipts = main.get("library_written") if isinstance(main, dict) else None
        for receipt in receipts if isinstance(receipts, list) else []:
            if isinstance(receipt, dict) and receipt.get("op") == "put_artifact":
                object_id = receipt.get("object_id")
                if isinstance(object_id, str):
                    found[object_id] = None
    return list(found)


def run_files(home: Path, run_id: str, events: list[Event], library: LibraryPort) -> list[Stored]:
    """The artifact files of the run's finished nodes not yet stored by an earlier drive. A
    listed file a later node deleted or moved is logged and left out (L-80)."""
    held = {
        (str(meta.get("node_id")), str(meta.get("path")))
        for earlier in library.objects(run_id, "workflow-run")
        for edge in library.edges(earlier.object_id, "produced-by", reverse=True)
        if isinstance(meta := library.get(edge.from_id).fields.get("metadata"), dict)
    }
    zone = RunZone.of(home, run_id).work
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
            try:
                body = (zone / str(name)).read_bytes()
            except OSError:
                LOG.warning("run %s: %s listed %s, which is gone", run_id, node_id, name)
                continue
            stored.append(
                library.put_artifact(
                    body,
                    "run-file",
                    {"node_id": node_id, "path": str(name)},
                    run_id=run_id,
                    principal=f"run:{run_id}",
                )
            )
    return stored
