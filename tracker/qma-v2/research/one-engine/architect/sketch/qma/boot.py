"""What a QMA process may inherit from its parent. Standard library only.

Runs as the first statement of every QMA entry point (`qma.serve`, `qma.console`), before
anything imports `claude_agent_sdk`. The SDK merges the per-chat `env` over this process's
environment (02a trap 6), so whatever survives here can reach every CLI it starts.

Belt and braces with `qma.harness.launch.launch_env`, which is still total over
`ROUTING_KEYS`. Neither layer has to be right on its own:
- the scrub means an inherited `ANTHROPIC_API_KEY` or `CLAUDE_CODE_USE_BEDROCK` is gone
  before any chat exists, so the design no longer depends on whether the CLI treats ""
  as unset (check S19 records that anyway);
- the total env means a key added back at run time is still overridden, and
  `launch.assert_scrubbed` refuses the launch when it sees one.

A unit test asserts every name in `launch.ROUTING_KEYS` matches a prefix here, so the two
lists cannot drift.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Final

SCRUB_PREFIXES: Final[tuple[str, ...]] = (
    "ANTHROPIC_",
    "CLAUDE_CODE_",
    "CLAUDE_CONFIG_DIR",
    "OPENAI_",
    "AWS_BEARER_TOKEN_BEDROCK",
    "ENABLE_TOOL_SEARCH",
    "ENABLE_CLAUDEAI_MCP_SERVERS",
)
"""The whole `CLAUDE_CODE_` prefix goes, not a list of known routing switches: the CLI
keeps adding them (`CLAUDE_CODE_USE_FOUNDRY`, `CLAUDE_CODE_USE_ANTHROPIC_AWS`), and every
CLI knob QMX wants comes from `launch.CONSTANT_ENV`, a profile's quirks or `settings.json`,
never from the parent process."""


def scrub_process_env(environ: MutableMapping[str, str]) -> tuple[str, ...]:
    """Delete every variable whose name starts with a `SCRUB_PREFIXES` entry.

    Returns the removed names, sorted, never their values. `doctor` shows them so the
    operator can see what his shell was carrying. Idempotent: a second call removes
    nothing and returns ().
    """
    raise NotImplementedError
