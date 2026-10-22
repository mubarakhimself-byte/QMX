"""P1k (SOLUTION-DESIGN 26.14): native third-party sub-agents under key and GPT mains.

E24's shape with a real key. A Kimi main on the OpenRouter Kimi row runs from a throwaway home
with its base URL on `router.py`, launched with definitions naming a DeepSeek and a Qwen
sub-agent. The router sends the Kimi id to OpenRouter with the key it reads by keyring name
(`qmx/openrouter`) in place of the CLI's grant, and the DeepSeek and Qwen ids to two local echo
upstreams. Any other id gets a 400.

PASS for a main when each sub-agent spawns, its request reaches the router with its model id
unchanged, its echo's answer returns as its result, and nothing that leaves for an echo holds a
credential, a grant header or an `sk-ant-` value. The rest of P4's egress lines (betas,
`defer_loading`, `metadata.user_id`) belong to P4 against the normaliser, which is not built.
FAIL when the CLI refuses or rewrites an id. The GPT main runs only with a GPT sign-in in the
ship home.

    uv run --no-sync python ../scripts/probes/router/p1k_key_mains.py
"""

from __future__ import annotations

import asyncio
import os
import secrets
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Final

from common import HOMES, evidence, home_env, log, run_session, scrub_process_env
from router import Echo, Exchange, Router, Upstream

ENGINE_COMMON: Final = Path(__file__).resolve().parents[1] / "engine" / "common.py"
KIMI_MAIN: Final = "moonshotai/kimi-k2.5"
"""`OPENROUTER_ROW`'s model in `SP/engine/common.py`; checked against it at start."""
OPENROUTER_URL: Final = "https://openrouter.ai/api"
OPENROUTER_REF: Final = "qmx/openrouter"
SUBAGENTS: Final = {
    "deepseek-reviewer": ("deepseek/deepseek-v4-pro", "DEEPSEEK-ECHO-41C2"),
    "qwen-reviewer": ("qwen/qwen3.6-plus", "QWEN-ECHO-9B07"),
}
"""Claude's default ids for the probe: the strong DeepSeek row of SOLUTION-DESIGN section 9 and a
Qwen id. Only the echo answers them, so any id serves to see whether the CLI keeps it."""
SUBAGENT_TOOLS: Final = ("Agent", "Task")
GPT_SIGN_IN: Final = Path("D:/QMX-worktrees/qma-ship/home/gpt")
PROMPT: Final = (
    "Use the deepseek-reviewer agent, then the qwen-reviewer agent, each to review this "
    "sentence: 'The sky is green.' Then reply with both reviewers' answers, word for word."
)


def openrouter_row_model() -> str:
    """`KIMI_MODEL` from `SP/engine/common.py`, read as text so its import side effects stay out."""
    for line in ENGINE_COMMON.read_text("utf-8").splitlines():
        if line.startswith("KIMI_MODEL"):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


def openrouter_key() -> str:
    from qmx_router.relay import keyring_secret  # noqa: PLC0415

    return keyring_secret(OPENROUTER_REF)


def leaves_clean(echo: Echo) -> bool:
    """No credential, grant header or Claude token shape in what an echo received."""
    headers_clean = not any(
        name in seen.headers
        for seen in echo.requests
        for name in ("authorization", "x-api-key", "x-qmx-grant")
    )
    return headers_clean and b"sk-ant-" not in echo.bodies()


async def kimi_main(say: Any) -> bool:
    from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions  # noqa: PLC0415

    echoes = {name: Echo(f"{marker} reviewed").start() for name, (_, marker) in SUBAGENTS.items()}
    lanes = {model: echoes[name].upstream(f"echo-{name}") for name, (model, _) in SUBAGENTS.items()}
    lanes[KIMI_MAIN] = Upstream("openrouter", OPENROUTER_URL, key=openrouter_key, third_party=True)
    root = HOMES / "prb-r-p1k"
    shutil.rmtree(root, ignore_errors=True)
    try:
        with Router(lanes.get) as router:
            router.recorder.run = "p1k-kimi"
            env = home_env(root / "home", root / "claude") | {
                "ANTHROPIC_BASE_URL": router.url,
                "ANTHROPIC_AUTH_TOKEN": secrets.token_urlsafe(24),
                "ENABLE_TOOL_SEARCH": "false",
                "CLAUDE_CODE_GATEWAY_HINT_HEADERS": "1",
                **{
                    f"ANTHROPIC_DEFAULT_{tier}_MODEL": KIMI_MAIN
                    for tier in ("OPUS", "SONNET", "HAIKU")
                },
                "ANTHROPIC_SMALL_FAST_MODEL": KIMI_MAIN,
            }
            agents = {
                name: AgentDefinition(
                    description=f"Reviews one sentence. Runs on {model}.",
                    prompt="You review sentences. Answer in one line.",
                    model=model,
                    tools=[],
                )
                for name, (model, _) in SUBAGENTS.items()
            }
            options = ClaudeAgentOptions(
                env=env,
                setting_sources=[],
                strict_mcp_config=True,
                model=KIMI_MAIN,
                cwd=str(root),
                tools=list(SUBAGENT_TOOLS),
                allowed_tools=list(SUBAGENT_TOOLS),
                agents=agents,
                max_turns=8,
            )
            outcome = await run_session(options, PROMPT)
            exchanges: list[Exchange] = list(router.recorder.exchanges)
            router.recorder.write(
                evidence("prb-r-p1k-recording.json"), keep_body=lambda e: e.lane != "openrouter"
            )
    finally:
        for echo in echoes.values():
            echo.stop()
    say(f"[kimi main] model {KIMI_MAIN} on OpenRouter; tool calls: {outcome.tool_uses}")
    say(f"[kimi main] result {outcome.result[:200]!r} is_error={outcome.is_error}")
    say(f"[kimi main] error {outcome.error!r}; message kinds {dict(Counter(outcome.kinds))}")
    say("[kimi main] methods and paths through the router:")
    for e in exchanges:
        say(
            f"    {e.method} {e.path} model={e.model!r} lane={e.lane} -> {e.status} "
            f"agent-id={e.header('x-claude-code-agent-id')!r} "
            f"agent-type={e.header('x-claude-code-agent-type')!r}"
        )
    main_ok = any(e.lane == "openrouter" and e.status == 200 for e in exchanges)
    say.check(
        "[kimi main] the Kimi main's own requests were served by OpenRouter",
        main_ok,
        [(e.model, e.status) for e in exchanges if e.lane == "openrouter"],
    )
    passed = main_ok
    for name, (model, marker) in SUBAGENTS.items():
        spawned = [
            i
            for n, i in outcome.tool_uses
            if n in SUBAGENT_TOOLS and i.get("subagent_type") == name
        ]
        theirs = [
            e for e in exchanges if e.lane == f"echo-{name}" and e.path.startswith("/v1/messages")
        ]
        unchanged = bool(theirs) and all(e.model == model for e in theirs)
        returned = [r for r in outcome.tool_results if marker in r]
        clean = leaves_clean(echoes[name])
        say.check(f"[kimi main] {name} spawned", bool(spawned), spawned[:1])
        refused = sorted({str(e.model) for e in exchanges if e.lane == "refused"})
        say.check(
            f"[kimi main] {name}'s request reached the router with {model!r} unchanged",
            unchanged,
            f"{[e.model for e in theirs]}; ids the router refused: {refused}",
        )
        say.check(
            f"[kimi main] {name}'s echo answer returned as its result", bool(returned), returned[:1]
        )
        say.check(
            f"[kimi main] what left for {name}'s echo held no credential, grant or sk-ant- value",
            clean,
            clean,
        )
        passed &= bool(spawned and unchanged and returned and clean)
    say(f"P1k Kimi main: {'PASS' if passed else 'FAIL'}")
    return passed


def main() -> int:
    removed = scrub_process_env(os.environ)
    say = log("p1k")
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    row_model = openrouter_row_model()
    say.check(
        "the probe's Kimi id is the OpenRouter row's model", row_model == KIMI_MAIN, row_model
    )
    asyncio.run(kimi_main(say))
    say(f"P1k GPT main: not run, no GPT sign-in (gpt folder exists: {GPT_SIGN_IN.exists()})")
    return say.verdict()


if __name__ == "__main__":
    sys.exit(main())
