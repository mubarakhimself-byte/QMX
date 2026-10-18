"""P1 (SOLUTION-DESIGN 26.14): a native third-party sub-agent under the real plan login.

A haiku main runs under the ship home's plan login with its base URL on `router.py`, the
router's grant in `ANTHROPIC_CUSTOM_HEADERS` and the plan-lane launch env, and with
`agents={"kimi-reviewer": AgentDefinition(model="kimi/k3", ...)}`. The router sends Claude ids
to `api.anthropic.com` unchanged and `kimi/k3` to a local Kimi echo. The main is told to use
`kimi-reviewer`.

PASS when the CLI spawns the sub-agent, a request with `model: kimi/k3` reaches the router
carrying `x-claude-code-agent-id`, the echo's answer comes back as the sub-agent's result, and
the main's own requests reach the plan path with the OAuth bearer. FAIL when the CLI refuses
or rewrites the model, stops on `unrecognized_model`, or never sends the request. The log lists
every method and path, and the raw incoming sub-agent request is kept, secrets withheld, for
RTR7's P4. `--runs 2` is the echo canary twice in a row.

    uv run --no-sync python ../scripts/probes/router/p1_definitions.py [--runs N]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import secrets
import sys
from collections import Counter
from typing import Any, Final

from common import (
    PLAN_LANE_ENV,
    evidence,
    lane_lock,
    log,
    plan_env,
    plan_options,
    run_session,
    scrub_process_env,
)
from router import (
    ANTHROPIC_URL,
    CREDENTIAL_HEADERS,
    GRANT_HEADER,
    Echo,
    Exchange,
    Router,
    Upstream,
    is_claude,
    raw_request,
)

KIMI: Final = "kimi/k3"
REVIEWER: Final = "kimi-reviewer"
ECHO_TEXT: Final = "KIMI-ECHO-7F3A the sentence is false"
PROMPT: Final = (
    f"Use the {REVIEWER} agent to review this sentence: 'The sky is green.' "
    "Then reply with exactly the reviewer's answer and nothing else."
)
SUBAGENT_TOOLS: Final = ("Agent", "Task")


def oauth_bearer(exchange: Exchange) -> bool:
    return (exchange.header("authorization") or "").startswith("Bearer sk-ant-oat")


async def one_run(say: Any, run: int) -> bool:
    from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions  # noqa: PLC0415

    echo = Echo(ECHO_TEXT).start()
    kimi = echo.upstream("kimi-echo")
    anthropic = Upstream("anthropic", ANTHROPIC_URL)
    route = lambda model: anthropic if is_claude(model) else kimi if model == KIMI else None  # noqa: E731
    try:
        with Router(route) as router:
            router.recorder.run = f"p1-{run}"
            env = (
                plan_env("p1")
                | PLAN_LANE_ENV
                | {
                    "ANTHROPIC_BASE_URL": router.url,
                    "ANTHROPIC_CUSTOM_HEADERS": f"x-qmx-grant: {secrets.token_urlsafe(24)}",
                }
            )
            reviewer = AgentDefinition(
                description="Reviews one sentence. Runs on Kimi.",
                prompt="You review sentences. Answer in one line.",
                model=KIMI,
                tools=[],
            )
            options = ClaudeAgentOptions(
                **plan_options(
                    env=env,
                    cwd=str(plan_env("p1")["HOME"]),
                    tools=list(SUBAGENT_TOOLS),
                    allowed_tools=list(SUBAGENT_TOOLS),
                    agents={REVIEWER: reviewer},
                )
            )
            outcome = await run_session(options, PROMPT)
            exchanges = list(router.recorder.exchanges)
    finally:
        echo.stop()
    say(f"[run {run}] env names added to the plan launch: {sorted(PLAN_LANE_ENV)}")
    say(f"[run {run}] main tool calls: {outcome.tool_uses}")
    say(f"[run {run}] result {outcome.result[:160]!r} is_error={outcome.is_error}")
    say(f"[run {run}] error {outcome.error!r}; message kinds {dict(Counter(outcome.kinds))}")
    say(f"[run {run}] methods and paths the CLI used through the router:")
    for e in exchanges:
        credential = any(e.header(name) is not None for name in CREDENTIAL_HEADERS)
        say(
            f"    {e.method} {e.path} model={e.model!r} lane={e.lane} -> {e.status} "
            f"agent-id={e.header('x-claude-code-agent-id')!r} "
            f"oauth bearer={oauth_bearer(e)} credential header present={credential}"
        )
    at_echo = any(
        k in s.headers for s in echo.requests for k in (*CREDENTIAL_HEADERS, GRANT_HEADER)
    )
    say(
        f"[run {run}] the echo upstream received {len(echo.requests)} requests; "
        f"credential or grant header at the echo: {at_echo}"
    )
    spawned = [
        i
        for n, i in outcome.tool_uses
        if n in SUBAGENT_TOOLS and i.get("subagent_type") == REVIEWER
    ]
    kimi_requests = [e for e in exchanges if e.model == KIMI and e.path.startswith("/v1/messages")]
    rewritten = sorted({str(e.model) for e in exchanges if e.lane == "refused"})
    main_requests = [
        e for e in exchanges if e.lane == "anthropic" and e.path.startswith("/v1/messages")
    ]
    if kimi_requests:
        evidence(f"prb-r-p1-subagent-request-{run}.http").write_bytes(raw_request(kimi_requests[0]))
        say(f"[run {run}] kept the raw sub-agent request (secrets withheld) for P4")
    tagged = bool(kimi_requests) and all(e.header("x-claude-code-agent-id") for e in kimi_requests)
    returned = [r for r in outcome.tool_results if ECHO_TEXT in r]
    on_plan = bool(main_requests) and all(
        oauth_bearer(e) and e.status == 200 for e in main_requests
    )
    say.check(f"[run {run}] the CLI spawned {REVIEWER}", bool(spawned), spawned)
    say.check(
        f"[run {run}] a request with model {KIMI} reached the router with an agent id",
        tagged,
        [(e.model, e.header("x-claude-code-agent-id")) for e in kimi_requests]
        or f"none; refused ids {rewritten}",
    )
    say.check(
        f"[run {run}] the echo's answer came back as the sub-agent's result",
        bool(returned),
        returned[:1],
    )
    say.check(
        f"[run {run}] the main's own requests reached the plan path with the OAuth bearer",
        on_plan,
        [(e.model, e.status, oauth_bearer(e)) for e in main_requests],
    )
    return bool(spawned and tagged and returned and on_plan)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()
    removed = scrub_process_env(os.environ)
    say = log("p1" if args.runs == 1 else "canary")
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    verdicts = []
    with lane_lock(say):
        for run in range(args.runs):
            verdicts.append(asyncio.run(one_run(say, run)))
    if args.runs > 1:
        say.check(
            "the canary gave the same verdict on every run", len(set(verdicts)) == 1, verdicts
        )
    return say.verdict()


if __name__ == "__main__":
    sys.exit(main())
