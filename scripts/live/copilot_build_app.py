"""Operator-only Copilot build journey; needs configured models and a reviewed sandbox app."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any, cast

from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command
from qmx_apps.volume import Volume
from qmx_control.service import ControlService, SessionInput

from qmx_agents.copilot import AppSandbox, build_copilot, stream_turn
from qmx_agents.router import ModelRouter, RunContext, load_config
from qmx_agents.spec import BuildContext


def global_request(value: Any) -> bool:
    return isinstance(value, dict) and cast(dict[str, Any], value).get("kind") == "global_memory"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--sandbox-app", required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument(
        "--description",
        default=(
            "Build Macro daily bias: read qmx-data daily, summarise drivers with an agent, "
            "save bias and rationale to app.db, and show a tier-1 panel. Test before publication."
        ),
    )
    args = parser.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=True)
    service = ControlService(args.home)
    session = service.sessions_create(SessionInput(title="Build Macro daily bias"))
    session_id = str(session["id"])
    path = args.home / "copilot/threads.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(path)) as saver:
        ctx = BuildContext(
            ModelRouter(load_config(args.config) if args.config else load_config()),
            run=RunContext(session_id=session_id),
            qmx_home=args.home,
            control=service,
            checkpointer=saver,
            backend=FilesystemBackend(root_dir=args.workspace, virtual_mode=True),
            agent_backends={
                "data-analyst": AppSandbox(
                    service, args.sandbox_app, Volume(args.home, args.sandbox_app).root
                )
            },
        )
        try:
            graph = await build_copilot(ctx)
            print(f"Session: {session_id}; stream /api/events/sessions?subject={session_id}")
            await stream_turn(graph, service, session_id, args.description, context=ctx.run)
            config = {"configurable": {"thread_id": session_id}}
            while (state := await graph.aget_state(config)).next:
                for task in state.tasks:
                    for request in task.interrupts:
                        print(request.value)
                accepted = input("Approve this request? [y/N] ").strip().lower() == "y"
                resume: Any = {"decisions": [{"type": "approve" if accepted else "reject"}]}
                if any(
                    global_request(item.value) for task in state.tasks for item in task.interrupts
                ):
                    resume = accepted
                await stream_turn(
                    graph, service, session_id, Command(resume=resume), context=ctx.run
                )
            for event in service.sessions_stream(session_id, limit=1000):
                print(event)
        finally:
            await ctx.close_memory()
            service.close()


if __name__ == "__main__":
    asyncio.run(main())
