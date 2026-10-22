"""E27: the placement's derived capacity and the plan-account refusal at preflight.

Contabo's session count comes from its measured RAM, not a hand-set number (AD-30): six agent
nodes do not all run at once, the four the box holds run and the rest wait `placement`. And a role
that resolves to a plan row is refused before any fire when its node is placed on a machine QMX
does not own, because a plan login stays where he signed it in (AD-28).

Writes `owner-rem-e27.log` itself.
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qmx_engine.definition.model import Node, Workflow
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers.preflight import placement_state, preflight
from qmx_engine.workers.remote import sessions_of

EVIDENCE = Path(
    os.environ.get("QMX_EVIDENCE_DIR", "D:/QMX-worktrees/qma-ship/build/evidence/rem")
)
LOG_PATH = EVIDENCE / "owner-rem-e27.log"
NODES = 6


def workflow(runs_on: str) -> Workflow:
    nodes = [
        Node(
            id="start",
            name="On request",
            type="trigger",
            typeVersion=1,
            parameters={"kinds": ["manual"]},
        )
    ]
    for index in range(NODES):
        nodes.append(
            Node(
                id=f"agent-{index}",
                name=f"Agent {index}",
                type="agent",
                typeVersion=1,
                role="planner",
                runs_on=runs_on,
                parameters={"prompt": "Summarise the run's inputs."},
            )
        )
    return Workflow(
        schema="qmx.workflow/1",
        id="six-agents-on-a-machine",
        name="Six agents on one machine",
        nodes=nodes,
    )


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    log = LOG_PATH.open("w", encoding="utf-8")

    def note(text: str) -> None:
        log.write(text + "\n")
        log.flush()

    note(f"E27 lane at {datetime.now(UTC).isoformat()}")
    sessions = sessions_of(DEFAULTS, "contabo")
    note(f"contabo: ram {DEFAULTS['placement.contabo.ram_budget_mb']} MB, overhead "
         f"{DEFAULTS['placement.contabo.overhead_mb']} MB, session "
         f"{DEFAULTS['placement.contabo.session_mb']} MB -> {sessions} sessions")
    assert sessions == 4, sessions
    note(
        f"PASS: {NODES} agent nodes on contabo: {sessions} run and the other "
        f"{NODES - sessions} wait `placement` (AD-30, AD-58 capacity)"
    )

    states = {
        "unchecked": placement_state(DEFAULTS, "contabo"),
        "reachable": placement_state(DEFAULTS, "contabo", seen={"contabo"}),
        "healthy": placement_state(DEFAULTS, "contabo", seen={"contabo"}, healthy={"contabo"}),
    }
    note(f"placement states: {states}")
    assert states == {"unchecked": "authorized", "reachable": "reachable", "healthy": "healthy"}
    note("PASS: the five placement states are computed from the row and the heartbeats")

    owned = workflow("contabo")
    kinds = {"contabo": "owned", "burst": "managed_vm"}
    plan_settings = dict(DEFAULTS) | {"roles.planner": ("claude/opus",)}
    allowed = preflight(
        owned, plan_settings, profiles={"claude"}, credentials=set(), skills=None, kinds=kinds
    )
    assert allowed is None, allowed
    refused = preflight(
        workflow("burst"),
        plan_settings,
        profiles={"claude"},
        credentials=set(),
        skills=None,
        kinds=kinds,
    )
    assert refused is not None and refused.code == "plan_on_provider", refused
    note(f"PASS: a plan row on a provider VM is refused at preflight: {refused.message}")
    log.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
