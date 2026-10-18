"""E24, the CLI half: does a sub-agent's full non-Claude model id reach the wire unchanged?

A raw `claude_agent_sdk` client points at the fake model's loopback provider with a fake key,
from a throwaway config folder, so no plan login and no real key is used. Two sub-agents are
defined with `AgentDefinition(model=...)`, one a full DeepSeek id and one a Kimi id. The fake
model scripts the main agent to call both, then records the `model` field of every request.

Three variants run: no alias env; the tier alias env (`ANTHROPIC_DEFAULT_*_MODEL`) set to
markers; and `CLAUDE_CODE_SUBAGENT_MODEL` set to a marker.

PASS when each variant's log lists every request's `model` field and says whether both full
ids arrived unchanged. The verdict on the ids themselves is a finding, not a pass condition.

    <ep1-venv>/Scripts/python.exe scripts/probes/engine/p_model_ids.py
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Final

from raw_client import HOMES, Log, home_env, scrub_process_env

sys.path.append(str(Path(__file__).resolve().parents[2] / "live" / "qma"))
from fake_model import FAKE_KEY, FakeModel, Turn, text, tool_use

MAIN_MODEL: Final = "fake-main-model"
DEEPSEEK: Final = "deepseek/deepseek-v4.1-flash"
KIMI: Final = "kimi-k3"
SUBAGENTS: Final = {"ds-helper": (DEEPSEEK, "EP1-DS-MARK"), "kimi-helper": (KIMI, "EP1-KIMI-MARK")}
SUBAGENT_TOOLS: Final = ("Agent", "Task")
VARIANTS: Final[dict[str, dict[str, str]]] = {
    "plain": {},
    "tier-alias-env": {
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "alias-opus-marker",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "alias-sonnet-marker",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "alias-haiku-marker",
        "ANTHROPIC_SMALL_FAST_MODEL": "alias-small-fast-marker",
    },
    "subagent-model-env": {"CLAUDE_CODE_SUBAGENT_MODEL": "subagent-env-marker"},
}


class ScriptedMain(FakeModel):
    """The main conversation calls each sub-agent in turn through whichever sub-agent tool
    the CLI offers, then ends. Sub-agent conversations route by the marker in their prompt."""

    def __init__(self) -> None:
        routes = {marker: [Turn([text(f"{name} done")])] for name, (_, marker) in SUBAGENTS.items()}
        super().__init__([], routes=routes)
        self.calls = list(SUBAGENTS.items())
        self.tool_name: str | None = None

    def next_turn(self, scripted: bool, request: dict[str, Any] | None = None) -> Turn:
        messages = (request or {}).get("messages") or [{}]
        if not scripted or any(m in json.dumps(messages[0]) for _, m in SUBAGENTS.values()):
            return super().next_turn(scripted, request)
        with self.lock:
            offered = {tool.get("name") for tool in (request or {}).get("tools", [])}
            self.tool_name = next((n for n in SUBAGENT_TOOLS if n in offered), None)
            if self.tool_name is None or not self.calls:
                return Turn([text("main done")])
            name, (_, marker) = self.calls.pop(0)
            call = {"subagent_type": name, "description": name, "prompt": f"{marker} say hi"}
            return Turn([tool_use(self.tool_name, call)])


async def run_variant(log: Log, variant: str, extra_env: dict[str, str]) -> bool:
    from claude_agent_sdk import (  # noqa: PLC0415
        AgentDefinition,
        ClaudeAgentOptions,
        ClaudeSDKClient,
    )

    root = HOMES / f"ep1-model-ids-{variant}"
    shutil.rmtree(root, ignore_errors=True)
    fake = ScriptedMain().start()
    env = home_env(root / "home", root / "claude") | {
        "ANTHROPIC_BASE_URL": fake.url,
        "ANTHROPIC_API_KEY": FAKE_KEY,
    }
    agents = {
        name: AgentDefinition(
            description=f"{name}, says hi", prompt="Say hi.", model=model, tools=[]
        )
        for name, (model, _) in SUBAGENTS.items()
    }
    options = ClaudeAgentOptions(
        env=env | extra_env,
        setting_sources=[],
        strict_mcp_config=True,
        model=MAIN_MODEL,
        cwd=str(root),
        tools=list(SUBAGENT_TOOLS),
        agents=agents,
        permission_mode="bypassPermissions",
        max_turns=6,
    )
    try:
        async with asyncio.timeout(180), ClaudeSDKClient(options) as client:
            await client.query("Call ds-helper, then kimi-helper.")
            async for _ in client.receive_response():
                pass
    finally:
        fake.stop()
    posts = [seen for seen in fake.requests if seen.method == "POST"]
    log(f"[{variant}] env {sorted(extra_env)}; sub-agent tool offered: {fake.tool_name}")
    for index, seen in enumerate(posts):
        body = seen.json
        first = json.dumps((body.get("messages") or [{}])[0])
        who = next((n for n, (_, m) in SUBAGENTS.items() if m in first), "main/side")
        log(f"[{variant}] request {index} {seen.path} model={body.get('model')!r} chat={who}")
    seen_models = Counter(str(seen.json.get("model")) for seen in posts)
    log(f"[{variant}] model field counts: {dict(seen_models)}")
    verdicts = []
    for name, (model, marker) in SUBAGENTS.items():
        theirs = [
            s.json.get("model")
            for s in posts
            if marker in json.dumps((s.json.get("messages") or [{}])[0])
        ]
        unchanged = bool(theirs) and all(m == model for m in theirs)
        log(f"[{variant}] FINDING {name} asked {model!r}; wire saw {theirs}; unchanged={unchanged}")
        verdicts.append(bool(theirs))
    return bool(posts) and all(verdicts)


def main() -> int:
    removed = scrub_process_env(os.environ)
    log = Log("ep1-model-ids")
    log(f"scrubbed {len(removed)} names from the process env (names only, no values)")
    import claude_agent_sdk  # noqa: PLC0415

    log(f"claude_agent_sdk {claude_agent_sdk.__version__}")
    for variant, extra in VARIANTS.items():
        recorded = asyncio.run(run_variant(log, variant, extra))
        log.check(
            f"[{variant}] every request's model field is listed, both sub-agents reached the wire",
            recorded,
            recorded,
        )
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
