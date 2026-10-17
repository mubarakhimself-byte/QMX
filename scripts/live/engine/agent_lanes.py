"""What EP11's lanes share: workflow folders with `agent` and `llm` nodes, a run driven over a
harness port with run inputs, and the hash of the ship home's `settings.toml`, which no lane may
change. `scripts/live/qma` goes on the end of `sys.path` for its `fake_model`.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from common import ENGINE_STORE, LIVE_QMA, SHIP_HOME, throwaway_home

sys.path.append(str(LIVE_QMA))
os.environ.setdefault("QMA_LIVE_SCRATCH", str(ENGINE_STORE / "homes" / "ep11-scratch"))

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.spans import Span
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.harness_adapter import HarnessPort
from qmx_engine.runner import Engine, Mode, Outcome
from qmx_engine.settings import DEFAULTS

PR: Final = "ep11"
SHIP_SETTINGS: Final = SHIP_HOME / "settings.toml"


def settings_sha() -> str:
    return hashlib.sha256(SHIP_SETTINGS.read_bytes()).hexdigest()


def node(node_id: str, kind: str, role: str | None = None, **parameters: Any) -> dict[str, Any]:
    found: dict[str, Any] = {
        "id": node_id,
        "name": node_id,
        "type": kind,
        "typeVersion": 1,
        "parameters": parameters,
    }
    return found | ({"role": role} if role is not None else {})


def edge(target: str, map_: str = "one", **extra: Any) -> dict[str, Any]:
    return {"node": target, "port": "in", "map": map_, **extra}


def workflow(
    slug: str,
    nodes: list[dict[str, Any]],
    connections: dict[str, dict[str, list[dict[str, Any]]]],
    files: Mapping[str, str],
) -> Path:
    """A workflow folder `homes/ep11-<slug>-wf` with its definition and its files by path."""
    root = throwaway_home(PR, f"{slug}-wf")
    document = {
        "schema": "qmx.workflow/1",
        "id": slug,
        "name": slug,
        "nodes": nodes,
        "connections": {
            source: {port: [targets] for port, targets in ports.items()}
            for source, ports in connections.items()
        },
    }
    (root / "definition.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    for path, text in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text, encoding="utf-8")
    return root


async def run(
    engine_home: Path,
    root: Path,
    port: HarnessPort,
    settings: Mapping[str, object] = DEFAULTS,
    *,
    mode: Mode = "test",
    inputs: Any = None,
    run_id: str | None = None,
) -> tuple[Outcome, list[Event], list[Span]]:
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: {root} does not validate: {found}")
    with Ledger.open(engine_home) as ledger:
        engine = Engine(engine_home, ledger, settings=settings, harness=port)
        outcome = await engine.start(root, found[1], mode=mode, inputs=inputs, run_id=run_id)
    return outcome, *read(engine_home, outcome.run_id)


def read(engine_home: Path, run_id: str) -> tuple[list[Event], list[Span]]:
    with Reader.open(engine_home) as reader:
        return reader.events(run_id), reader.spans(run_id)


def sessions(events: list[Event]) -> list[tuple[Any, Any, Any]]:
    """Each chat an attempt started or resumed: `(node and partition, attempt, session id)`."""
    return [
        ((e.data.get("node_id"), e.data.get("partition")), e.data.get("attempt"), sid)
        for e in events
        if e.kind == "heartbeat" and (sid := e.data.get("session_id")) is not None
    ]
