"""The service's ports at its edges: settings read through the control service, a live run's
trace and summary in the Library, the operator-only inbox resolve, and the memory stub."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest
from fake_library import fake_service
from flows import CHAIN
from qmx_control.models import Document
from qmx_control.service import ControlService, SettingsSection

from qmx_engine.ledger.store import ledger_path
from qmx_engine.ports.inbox import Category, Raise
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.service.context import OPERATOR, Caller, Refused
from qmx_engine.settings import DEFAULTS

SETTINGS = """
[engine]
"scheduler.tick" = 5
unknown = "ignored"

[engine.retry]
backoff = [1, 2]

[roles]
writer = ["claude/opus"]
scout = ["claude/haiku"]
"""


class Watched(ControlService):
    puts: list[str]

    def settings_put(self, section: SettingsSection, values: Document) -> Document:
        self.puts.append(section)
        return super().settings_put(section, values)


def test_engine_and_roles_settings_override_the_defaults_without_a_write(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text(SETTINGS, encoding="utf-8")
    control = Watched(tmp_path)
    control.puts = []
    values = ControlSettings(control).values()

    assert (values["scheduler.tick"], values["retry.backoff"]) == (5, (1, 2))
    assert (values["roles.writer"], values["roles.scout"]) == (("claude/opus",), ("claude/haiku",))
    assert (values["roles.judge"], "unknown" in values) == (DEFAULTS["roles.judge"], False)
    assert control.puts == []


def test_a_live_run_leaves_its_summary_and_trace_in_the_library_only(tmp_path: Path) -> None:
    with fake_service(tmp_path) as svc:
        item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
        asyncio.run(svc.tests.run(item, caller=OPERATOR))
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        run = asyncio.run(svc.runs.start(version, caller=OPERATOR))
        library = svc.ctx.library
        summary = library.objects(run.run_id, "workflow-run")[-1]
        run_of = [e.to_id for e in library.edges(summary.object_id, "run-of")]
        produced = library.edges(summary.object_id, "produced-by", reverse=True)
        trace = library.get(produced[0].from_id)
        runs = svc.runs.list(item, version)
    with sqlite3.connect(ledger_path(tmp_path)) as db:
        tables = [t for (t,) in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        dumped = " ".join(str(db.execute(f"SELECT * FROM {t}").fetchall()) for t in tables)  # noqa: S608

    assert (run.mode, run.status, run.object_id) == ("live", "passed", version)
    assert (summary.principal, summary.fields["started_by"]) == (f"run:{run.run_id}", "operator")
    assert run_of == [version]
    assert (trace.kind, trace.fields["type"], trace.blob) == (
        "artifact",
        "trace",
        summary.fields["trace_artifact_hash"],
    )
    assert [(r.mode, r.status) for r in runs] == [("live", "passed")]
    assert "double them, add them up" not in dumped


def test_only_the_operator_resolves_an_inbox_item_and_memory_notes_land_in_run_scope(
    tmp_path: Path,
) -> None:
    with fake_service(tmp_path) as svc:
        found = Raise("r1", "sig", Category.SYSTEM_FAULT, "engine fault", "boom")
        item_id = svc.ctx.inbox.raise_item(found, at="2026-10-17T09:00:00+00:00")
        with pytest.raises(Refused, match=r"^ui_only:"):
            svc.inbox.resolve(item_id, "stop", caller=Caller("agent", "s1"))
        resolved = svc.inbox.resolve(item_id, "stop", caller=OPERATOR)
        row = svc.ctx.library.get(svc.memory.note("r1", {"content": "the feed was empty"}))
        palette = {p["type"]: p["available"] for p in svc.registry()}

    assert (resolved.resolved_by, resolved.resolution) == ("operator", "stop")
    assert (row.kind, row.ref, row.fields["scope"]) == ("memory-row", "refs/runs/r1", "run")
    assert (palette["script"], palette["llm"], palette["note"]) == (True, True, False)
