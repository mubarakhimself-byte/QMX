"""Operator-only remote smoke: one placed job, run as a one-node engine run on Contabo.

The job is REM's `run-on-a-machine` template (engine AD-57: a placed CPU or GPU job is a one-node
workflow). The engine's remote `WorkerPort` adapter ships the attempt to the box, where
`qmx_remote.sidecar` runs it. The transport is the E57 lane's ssh provider and gateway
(`server/e57_remote.py`), because the box has no Docker daemon and the Hub does not serve run
tails yet. Prints the run as JSON; exits 0 only when the run passed and its placed node finished in
the home ledger.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import cast

import qmx_engine.templates
from qmx_engine.__main__ import home_library
from qmx_engine.definition.folder import load
from qmx_engine.definition.model import Workflow
from qmx_engine.ledger.store import Reader
from qmx_engine.service.api import EngineService
from qmx_engine.workers.remote import GatewayPort, PlacementWorker

sys.path.insert(0, str(Path(__file__).resolve().parent / "server"))
from e57_remote import SshGateway, SshProvider, pass_mint, settings

FOLDER = Path(qmx_engine.templates.__file__).parent / "run-on-a-machine"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True, help="a throwaway QMX home")
    parser.add_argument("--command", nargs="+", default=["python3", "-c", "print(42)"])
    args = parser.parse_args()
    folder = load(FOLDER)
    if folder.document is None:
        parser.error(f"the run-on-a-machine template does not load: {folder.problems}")
    workflow = Workflow.model_validate(folder.document)
    with home_library(args.home) as library, EngineService.open(args.home, library=library) as svc:
        svc.ctx.engine.worker = PlacementWorker(
            gateway=cast(GatewayPort, SshGateway()),
            providers={"contabo": SshProvider()},
            settings=settings(),
            mint=pass_mint,
            remote={"contabo"},
            heartbeat_timeout=90.0,
            clock=time.time,
        )
        outcome = asyncio.run(
            svc.ctx.engine.start(FOLDER, workflow, mode="test", inputs={"command": args.command})
        )
        finished = [
            event
            for event in Reader.open(args.home).events(outcome.run_id)
            if event.kind == "node_finished" and event.data.get("node_id") == "run"
        ]
    print(
        json.dumps(
            {
                "run_id": outcome.run_id,
                "status": outcome.status,
                "outputs": outcome.outputs,
                "placed_node_finished": len(finished) == 1,
            },
            indent=2,
        )
    )
    return 0 if outcome.status == "passed" and len(finished) == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
