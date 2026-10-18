"""The CLI's environment: scrubbed once at boot, derived per session after that.

No per-thread host process is needed for env hygiene. The old design needed one
because key-provider tokens would ride the CLI env (WHY "Preserve: host process").
Here no provider key ever enters a CLI env: the gateway holds them. What is left
is the plan-versus-API-key precedence trap (02a trap 6), handled by scrubbing
qmx-control's own environment before the SDK is imported, plus explicit values.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, NewType

from qma_gateway.contract import LeaseGrant, ModelId, RouteTable

LeaseSecret = NewType("LeaseSecret", str)
"""Random 256-bit value. Lives in harness memory and one CLI env only."""

SCRUB_PREFIXES: Final[tuple[str, ...]] = (
    "ANTHROPIC_",
    "CLAUDE_CODE_",  # includes CLAUDE_CODE_OAUTH_TOKEN and CLAUDE_CODE_USE_BEDROCK/VERTEX/...
    "CLAUDE_CONFIG_DIR",
    "OPENAI_",
    "AWS_BEARER_TOKEN_BEDROCK",
)

KEY_ONLY_MARKER: Final[str] = "qmx-key-only"
"""Set as ANTHROPIC_AUTH_TOKEN in a session that may not reach Claude. It outranks
/login (02a section 11 precedence), so the CLI never sends its plan login at all.
Not a secret: the lease travels in x-qmx-lease."""


def scrub_process_env(environ: MutableMapping[str, str]) -> tuple[str, ...]:
    """Remove every inherited variable matching SCRUB_PREFIXES from qmx-control's own
    environment. Returns the removed names (never values) for `doctor`. Idempotent."""
    raise NotImplementedError


@dataclass(frozen=True, slots=True)
class SessionEnv:
    values: Mapping[str, str]


def session_env(
    *,
    lease: LeaseGrant,
    secret: LeaseSecret,
    table: RouteTable,
    main_model: ModelId,
    subagent_default: ModelId,
    background_model: ModelId,
    config_home: Path,
    project_dir_name: str,
    gateway_url: str,
    max_subagent_depth: int,
    max_concurrent_subagents: int,
) -> SessionEnv:
    """Pure. Every routing value derives from the lease and the route table.

    # TODO pseudocode
    # v = {
    #   CLAUDE_CONFIG_DIR: config_home,  CLAUDE_CODE_PROJECT_DIR_NAME: project_dir_name,
    #   ANTHROPIC_BASE_URL: gateway_url,
    #   ANTHROPIC_CUSTOM_HEADERS: f"x-qmx-lease: {secret}",
    #   ANTHROPIC_MODEL: main_model,
    #   ANTHROPIC_DEFAULT_OPUS_MODEL / _SONNET_ / _HAIKU_ / _FABLE_: pinned from the
    #       lease's allowed set (haiku tier = background_model, so titles and other
    #       background calls stay inside the lease),
    #   CLAUDE_CODE_SUBAGENT_MODEL: subagent_default,
    #   CLAUDE_CODE_GATEWAY_HINT_HEADERS: "1",
    #   ENABLE_TOOL_SEARCH: "true" if every reachable route has caps.tool_search else "false",
    #   CLAUDE_CODE_AUTO_COMPACT_WINDOW: route(main_model).caps.context_window,
    #   CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH, CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS,
    #   CLAUDE_CODE_ENABLE_TODO_TOOLS: "1",
    #   CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
    #   ENABLE_CLAUDEAI_MCP_SERVERS: "false",
    #   CLAUDE_AGENT_SDK_CLIENT_APP: "QMA",
    # }
    # if not lease.carries_plan(table): v["ANTHROPIC_AUTH_TOKEN"] = KEY_ONLY_MARKER
    # never: ANTHROPIC_API_KEY, any provider key, CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS
    #   (betas are stripped per route by the gateway, so Claude keeps them)
    """
    raise NotImplementedError
