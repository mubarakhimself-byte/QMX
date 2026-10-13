"""Small edits to existing qmx_control/qmx_apps/qmx_agents files (sketch).

qmx_control/service.py
    from qma2.model import BlockKind
    type EventTopic = Literal["runs", "jobs", "sessions", "apps", "library", "settings",
                              "aggregates", "approvals", "usage"]          # additive
    type SettingsSection = Literal[..., "router"]                           # RouterPolicy
    class SessionBlock(BaseModel):
        type: BlockKind            # single source moves to qma2.model (no second Literal)
        content: Document

qmx_control/__main__.py  (start)
    `start` makes the pairing code, hands it to the detached `serve` child on the child's
    stdin (never disk, env or log), waits for health, then opens the operator's browser at
        http://localhost:8766/console/pair#code=<code>
    Re-pairing later is `qmx_control pair` (same path). Every successful pairing posts a
    needs_you block "a console was paired at HH:MM" so an unexpected pairing is visible.
    Same-user code could run `pair` too: speed bump, stated in design.md tension 2.

qmx_apps/supervisor.py
    - from qmx_agents.guards.money_path import check_descriptor
    + from qma2.money import check_descriptor   # langchain-free; cuts one LangChain chain
                                                  # out of `import qmx_control`

qmx_agents/guards/money_path.py
    MoneyPathAct, check_descriptor, ... re-exported from qma2.money (one source of the
    money vocabulary) until the old package is deleted; LangChain tool classes stay here.

Not changed: control.db schema, the 14 block kinds, the events/SSE loop, BearerGate,
sessions_append semantics. The harness writes its own harness.db.
"""

from __future__ import annotations
