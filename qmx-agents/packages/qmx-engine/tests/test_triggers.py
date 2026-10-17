"""Trigger rows: a run cannot create one, and preflight tells the workflow's own faults from a
provider's."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from flows import node, workflow

from qmx_engine.ledger.store import Ledger
from qmx_engine.service.context import Caller, Refused
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Cron
from qmx_engine.triggers.preflight import preflight

T0 = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)


def test_a_workflow_caller_cannot_create_a_trigger(tmp_path: Path) -> None:
    def create(caller: Caller) -> rows.Trigger:
        return rows.create(
            ledger,
            workflow_item="wf-1",
            pinned_object="obj-1",
            spec=Cron("0 * * * *", "Europe/London"),
            caller=caller,
            now=T0,
        )

    with Ledger.open(tmp_path) as ledger:
        with pytest.raises(Refused, match=r"^trigger_refused:"):
            create(Caller("workflow", "run-1"))
        made = create(Caller("agent", "s1"))

    assert (made.created_by, made.next_fire_at) == ("agent:s1", "2026-10-17T10:00:00.000000+00:00")


def test_a_missing_role_is_the_workflows_fault_and_a_missing_key_the_providers() -> None:
    ghost = workflow([node("Ask", "llm") | {"role": "ghost"}], {})
    keyed = workflow([node("Ask", "llm") | {"role": "triage", "credentials": {"key": "qmx/x"}}], {})

    lost = preflight(ghost, DEFAULTS, profiles={"claude"}, credentials=None, skills=None)
    unkeyed = preflight(keyed, DEFAULTS, profiles={"claude"}, credentials=set(), skills=None)

    assert lost is not None
    assert (lost.cause, lost.code) == ("config", "role_missing")
    assert unkeyed is not None
    assert (unkeyed.cause, unkeyed.code) == ("provider", "credential_missing")
