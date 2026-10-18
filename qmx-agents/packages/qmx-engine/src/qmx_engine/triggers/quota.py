"""Park a fire into a closed usage window (SOLUTION-DESIGN 4.2 step 5, AD-10, Hermes `quota_hold`).

When every allowed account for a role the workflow runs a model on is closed, the fire is held
until the window reopens plus `limits.slack`, which admission already adds, and the trigger's
later fires merge into it. One held fire runs once after the reset.
"""

from __future__ import annotations

from collections.abc import Mapping

from qmx_engine.admission import Admission
from qmx_engine.definition.model import Workflow
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.nodes.base import Waiting
from qmx_engine.ports.harness_adapter import HarnessPort
from qmx_engine.roles import order
from qmx_engine.triggers.cron import instant, stamp


async def closed_until(
    workflow: Workflow,
    settings: Mapping[str, object],
    harness: HarnessPort | None,
    admission: Admission | None,
) -> str | None:
    """When the hold ends, or None when every model role has an open account."""
    if harness is None or admission is None:
        return None
    profiles = harness.profiles()
    roles = {
        node.role
        for node in workflow.nodes
        if node.role is not None
        and not node.disabled
        and (kind := REGISTRY.kind(node.type)) is not None
        and kind.model_bearing
    }
    ends: list[str] = []
    for role in sorted(roles):
        candidates = [c for c in order(settings, role, "live") if c.profile in profiles]
        waits = [await admission.check(c) for c in candidates]
        resets = [w.resume_at for w in waits if isinstance(w, Waiting) and w.resume_at]
        if candidates and len(resets) == len(candidates):
            ends.append(stamp(min(instant(r) for r in resets)))
    return max(ends) if ends else None
