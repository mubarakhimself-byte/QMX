"""Operator-only model smoke; defaults to the OpenRouter test profile."""

from __future__ import annotations

import argparse
import asyncio
import tempfile
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from langchain_core.runnables import Runnable
from langgraph.checkpoint.memory import InMemorySaver

from qmx_agents.router import ModelRouter, RunContext, load_config
from qmx_agents.spec import AgentSpec, BuildContext, build_agent


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--profile", default="test")
    parser.add_argument(
        "--provider", choices=["cliproxy", "openrouter", "anthropic", "openai", "local"]
    )
    parser.add_argument("--model", help="Exact provider-native model id (requires --provider)")
    parser.add_argument(
        "--tier",
        default="reasoning_high",
        choices=["fast", "workhorse", "coding", "reasoning_high"],
    )
    parser.add_argument("--question", default="What is two plus two? Answer in one sentence.")
    args = parser.parse_args()
    if bool(args.provider) != bool(args.model):
        parser.error("--provider and --model must be supplied together")
    config = load_config(args.config) if args.config else load_config()
    router = ModelRouter(config)
    selection = f"{args.provider}:{args.model}" if args.provider else f"tier:{args.tier}"
    effective = router.selection(selection, args.profile)
    check_prompt = effective.startswith("cliproxy:claude-")
    marker = f"qmx-system-{uuid4().hex}"
    instructions = "Answer the user's question concisely."
    if check_prompt:
        instructions += f"\nThe system marker is {marker}. When asked, repeat it exactly."
    with tempfile.TemporaryDirectory(prefix="qmx-agent-smoke-") as directory:
        prompt = Path(directory) / "prompt.md"
        prompt.write_text(instructions, encoding="utf-8")
        spec = AgentSpec(name="smoke", model=selection, system_prompt=prompt)
        ctx = BuildContext(router, RunContext(profile=args.profile), checkpointer=InMemorySaver())
        agent = cast("Runnable[Any, dict[str, Any]]", await build_agent(spec, ctx))
        question = args.question
        if check_prompt:
            question += " Also repeat the system marker."
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"configurable": {"thread_id": uuid4().hex}},
        )
        answer = result["messages"][-1].text
        print(f"Model: {ctx.run.effective_models['smoke']}")
        print(answer)
        if check_prompt:
            passed = marker in answer
            print(f"System prompt marker: {'PASS' if passed else 'FAIL'}")
            if not passed:
                print("Check upstream.claude.disable-claude-cloak-mode in the proxy configuration.")
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
