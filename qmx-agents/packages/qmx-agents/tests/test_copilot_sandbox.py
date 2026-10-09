from __future__ import annotations

import asyncio
from pathlib import Path

from conftest import fake
from langgraph.checkpoint.memory import InMemorySaver
from qmx_control.service import ControlService, SessionInput
from test_copilot import FakeSandbox, models
from test_spec import call

from qmx_agents.copilot import build_copilot, stream_turn
from qmx_agents.router import RouterConfig, RunContext
from qmx_agents.spec import BuildContext


def test_data_analyst_executes_python_after_backend_wrapping(
    tmp_path: Path, config: RouterConfig
) -> None:
    service = ControlService(tmp_path)
    session_id = str(service.sessions_create(SessionInput(title="Analysis"))["id"])
    sandbox = FakeSandbox()
    model = fake(
        call("task", {"subagent_type": "data-analyst", "description": "Summarise a small slice"}),
        call("execute", {"command": "python -c 'print(2 + 2)'"}),
        "Analysis: /artifacts/result.json",
        "Done",
    )

    async def run() -> None:
        ctx = BuildContext(
            models(config, model),
            run=RunContext(session_id=session_id),
            control=service,
            qmx_home=tmp_path,
            checkpointer=InMemorySaver(),
            agent_backends={"data-analyst": sandbox},
        )
        try:
            graph = await build_copilot(ctx)
            await stream_turn(graph, service, session_id, "Analyse", context=ctx.run)
            assert sandbox.calls == ["python -c 'print(2 + 2)'"]
        finally:
            await ctx.close_memory()
            service.close()

    asyncio.run(run())
