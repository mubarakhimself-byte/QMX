"""The trading node's process: what its MCP entry serves (Part C AD-301, AD-302).

:func:`open_node` composes the node in its volume: the store, the identity (minted on first start,
compared on every start), and the node journal with its ``node_lifecycle`` start row.
:meth:`Node.call` is the one way in. It answers every operation of :data:`OPERATIONS` and never
raises, because a tool exception counts toward the supervisor's breaker and a call past its 30 s
timeout stops the app (``qmx_apps/supervisor.py`` ``call``). The FastMCP wiring lives in the app
folder's ``server.py`` (``qmx-agents/apps/trading-node``), so this package needs no MCP library.

The runtime thread that reconciles ``desired`` with the venues arrives with C-12a; until then no
venue is set up, nothing trades, and the node reads "Ready, no units yet".
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Final, cast

from qmf.core import is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_writer import JournalWriter, WriterScope

from qmn.app.identity import establish, machine_fingerprint
from qmn.app.operations import (
    CHANGES,
    READS,
    Answer,
    Context,
    answer_change,
    answer_read,
    refused,
)
from qmn.app.store import Json, Store, StoreBusyError

__all__ = ["BUILD", "OPERATIONS", "ROLE", "WORLD", "Node", "from_environment", "open_node"]

BUILD: Final = "0.1.0"
"""The node shell's build, stamped on its journal rows; the app manifest carries the same."""
ROLE: Final = "node"
WORLD: Final = JournalWorld.DEMO
"""The node's own journal world. The practice node holds demo grants only; a live world needs
a live binding, which arrives with C-21."""
OPERATIONS: Final[tuple[str, ...]] = (*READS, *CHANGES)
HOST_FACTS: Final = Path("road/host/facts.json")


class Node:
    """One running node: every operation answers here."""

    def __init__(self, context: Context, journal: JournalWriter | None) -> None:
        self.context = context
        self.journal = journal

    def call(self, name: str, arguments: object) -> Answer:
        try:
            if not isinstance(arguments, dict):
                return refused("bad_argument", f"{name}: the arguments are one object")
            given = cast(Mapping[str, Json], arguments)
            if name in READS:
                return answer_read(self.context, name, given)
            if name in CHANGES:
                return answer_change(self.context, name, given)
            return refused("unknown_operation", f"the trading node has no operation {name}")
        except StoreBusyError:
            return refused(
                "busy",
                f"{name}: the node's store stayed locked; nothing was changed",
                next_step="Ask again with the same op id.",
            )
        except Exception as error:  # the boundary: a raise would count toward the breaker
            print(
                json.dumps({"event": "operation_failed", "operation": name, "error": repr(error)}),
                file=sys.stderr,
            )
            return refused("internal", f"{name} failed inside the node ({type(error).__name__})")


def open_node(
    data: Path,
    *,
    here: str | None,
    machine: str,
    clock_ns: Callable[[], int] = time.time_ns,
) -> Node:
    """Compose the node in ``data`` (the volume's ``data/``) on the machine ``here`` names."""
    store = Store(data / "node.sqlite")
    started = clock_ns()
    standing = establish(store, here=here, now_ns=started)
    journal_root = data / "journal"
    scope = WriterScope(JournalStream.NODE, standing.tag, WORLD, machine, ROLE, BUILD)
    opened = JournalWriter.open(
        journal_root, scope, clock=clock_ns, boot_epoch_id=uuid.uuid4().hex[:12]
    )
    journal: JournalWriter | None = None
    problem: str | None = None
    if is_refusal(opened):
        problem = f"the journal writer refused to open ({opened.category.value})"
    else:
        journal = opened.value
        body: dict[str, object] = {"event": "start", "build": BUILD, "mismatch": standing.mismatch}
        written = journal.append("node_lifecycle", body, RowFacts(ts_recv=started, clock_ok=False))
        if is_refusal(written):
            problem = f"the start row was refused ({written.category.value})"
    store.observe("journal_problem", problem, started)
    store.observe("journal_write", None if problem else started, started)
    context = Context(
        store=store,
        here=here,
        journal_root=journal_root,
        data=data,
        build=BUILD,
        clock_ns=clock_ns,
        started_ns=started,
    )
    return Node(context, journal)


def from_environment() -> Node:
    """The node the supervisor started: its ``data/`` from ``QMX_DATA_DIR``, its machine from
    the host facts the host wrote into the volume (C-05c), and this machine's fingerprint."""
    data = Path(os.environ["QMX_DATA_DIR"])
    machine = "local"
    try:
        facts: object = json.loads((Path(os.environ["QMX_VOLUME"]) / HOST_FACTS).read_text("utf-8"))
        placement = (
            cast(dict[str, object], facts).get("placement") if isinstance(facts, dict) else None
        )
        if isinstance(placement, str) and placement:
            machine = placement
    except (KeyError, OSError, ValueError):
        pass
    return open_node(data, here=machine_fingerprint(), machine=machine)
