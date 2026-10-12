"""Routines, cron, continuation budget and escalation (AD-29).

Task Graph scheduling and ``dispatch_lease`` / ``environment_lease`` evaluation
for FR-Q27 live in ``qma.daemon.taskgraph`` (AD-12). Quant ``WakePolicy``
evaluation at mailbox delivery time lives here (AD-20; FR-Q61). Quant-owned
Routines fire deterministically from this package (AD-29; FR-Q62). Agent-run
continuation stays inside the three registry bounds (AD-29; FR-Q63).
"""

from __future__ import annotations

from qma.daemon.scheduler.wake import (
    WAKE_EXEMPTIONS,
    WakeDecision,
    WakeExemption,
    civil_window_id,
    evaluate_delivery_wake,
    in_quiet_hours,
    next_quiet_hours_end,
    resolve_iana_zone,
    routine_fire_suppressed_by_quiet_hours,
    running_agent_paused_by_quiet_hours,
)
from qma.daemon.taskgraph.projection import (
    PROCEDURE_RUNTIME,
    SECOND_SCHEDULER_MINTED,
    refuse_second_scheduler,
)

__all__ = [
    "PROCEDURE_RUNTIME",
    "SECOND_SCHEDULER_MINTED",
    "WAKE_EXEMPTIONS",
    "WakeDecision",
    "WakeExemption",
    "civil_window_id",
    "evaluate_delivery_wake",
    "in_quiet_hours",
    "next_quiet_hours_end",
    "refuse_second_scheduler",
    "resolve_iana_zone",
    "routine_fire_suppressed_by_quiet_hours",
    "running_agent_paused_by_quiet_hours",
]
