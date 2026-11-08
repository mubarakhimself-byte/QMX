"""The trading node's process: what its MCP entry serves (Part C AD-301, AD-302).

:func:`open_node` composes the node in its volume: the store, the identity (minted on first start,
compared on every start), and the node journal with its ``node_lifecycle`` start row.
:meth:`Node.call` is the one way in. It answers every operation of :data:`OPERATIONS` and never
raises, because a tool exception counts toward the supervisor's breaker and a call past its 30 s
timeout stops the app (``qmx_apps/supervisor.py`` ``call``). The FastMCP wiring lives in the app
folder's ``server.py`` (``qmx-agents/apps/trading-node``), so this package needs no MCP library.

:attr:`Node.runtime` is the thread that reconciles ``desired`` with the venues (C-12a). The node
the supervisor starts has no venue set up until his setup steps register one (C-11), so it trades
nothing and reads "Ready, no units yet"; a composition with venues, such as the conformance venue,
trades the units it is asked to deploy.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Final, cast

from qmf.core import is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_writer import JournalWriter, WriterScope

from qmn.app.identity import INSTALL_ID_BYTES, establish, install_id_of, machine_fingerprint
from qmn.app.operations import (
    CHANGES,
    READS,
    Answer,
    Context,
    answer_change,
    answer_read,
    refused,
)
from qmn.app.runtime import Runtime, Venue, deploy_preflight
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

    def __init__(
        self, context: Context, journal: JournalWriter | None, runtime: Runtime | None
    ) -> None:
        self.context = context
        self.journal = journal
        self.runtime = runtime

    def start(self) -> None:
        """Start the runtime thread; the operations answer whether it runs or not."""
        if self.runtime is not None:
            self.runtime.start()

    def stop(self) -> None:
        if self.runtime is not None:
            self.runtime.stop()

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


def _os_random(size: int) -> bytes:
    """``size`` bytes of OS entropy: the node's one random source."""
    return secrets.token_bytes(size)  # ambient-scan: allow - the node's composition root


def open_node(
    data: Path,
    *,
    here: str | None,
    machine: str,
    clock_ns: Callable[[], int] = time.time_ns,
    monotonic_ns: Callable[[], int] = time.monotonic_ns,
    sleep: Callable[[float], None] = time.sleep,
    random_bytes: Callable[[int], bytes] = _os_random,
    venues: Mapping[str, Venue] | Callable[[JournalWriter, str], Mapping[str, Venue]] | None = None,
) -> Node:
    """Compose the node in ``data`` (the volume's ``data/``) on the machine ``here`` names.

    The clock and the random source are read here and nowhere below: every op id, the boot
    epoch and the install id minted on first start come from ``random_bytes``. ``venues`` are
    the account bindings the runtime trades on, keyed by account id, or a factory given the
    node journal and the boot epoch. The runtime is built but not started; ``Node.start``
    starts it.
    """
    store = Store(data / "node.sqlite")
    started = clock_ns()
    standing = establish(
        store,
        install_id=install_id_of(random_bytes(INSTALL_ID_BYTES)),
        here=here,
        now_ns=started,
    )
    journal_root = data / "journal"
    scope = WriterScope(JournalStream.NODE, standing.tag, WORLD, machine, ROLE, BUILD)
    boot_epoch = random_bytes(6).hex()
    opened = JournalWriter.open(journal_root, scope, clock=clock_ns, boot_epoch_id=boot_epoch)
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
    waker: list[Runtime] = []

    def wake() -> None:
        for runtime in waker:
            runtime.wake()

    context = Context(
        store=store,
        here=here,
        journal_root=journal_root,
        data=data,
        build=BUILD,
        clock_ns=clock_ns,
        new_id=lambda: random_bytes(16).hex(),
        started_ns=started,
        wake=wake,
        deploy_preflight=lambda document: deploy_preflight(data, document),
    )
    runtime: Runtime | None = None
    if journal is not None:
        bound = venues(journal, boot_epoch) if callable(venues) else venues
        runtime = Runtime(
            context,
            journal,
            bound or {},
            machine=machine,
            build=BUILD,
            clock_ns=clock_ns,
            steady_ns=monotonic_ns,
            sleep=sleep,
            boot_epoch_id=boot_epoch,
        )
        waker.append(runtime)
    return Node(context, journal, runtime)


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
    node = open_node(data, here=machine_fingerprint(), machine=machine)
    node.start()
    return node
