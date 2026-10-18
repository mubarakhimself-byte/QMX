"""The agent zone service.

Runs as the zone OS account (`qmx-agent` on Windows and Linux, `_qmxagent` on
macOS), started by the OS service manager at boot. It hosts one
ClaudeSDKClient per live thread and dials the door's link on loopback.

This is the only module in QMX that imports claude_agent_sdk. qmx-control,
the broker and the door never import it.

Invariants:
- The zone runtime contains this package, qma_zone_wire and the pinned
  claude-agent-sdk wheel with its bundled CLI. Nothing else from QMX.
- This module never opens the CLI's credential store (`.credentials.json` or
  the Keychain item). Sign-in state comes from `claude auth status` only.
  A lint test bans the strings ".credentials" and "Claude Code-credentials"
  in this package.
- The CLI env is built by `cli_env` from an allow-list, never from os.environ.
- Every ClaudeAgentOptions carries an explicit permission_mode.
- Approvals relayed from here are user experience, not security. Anything an
  agent could do by tampering with this process it could already do with Bash
  as the same account. Money and QMX authority live behind the door.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qma_zone_wire import (
    Ask,
    AskId,
    Block,
    Command,
    Event,
    LoginDone,
    LoginUrl,
    ModelRoute,
    PermissionMode,
    ProbeFinding,
    ProbeTarget,
    PutUserTier,
    Seq,
    ThreadId,
    ThreadSpec,
)

ZONE_VERSION = "0.1.0"


@dataclass(frozen=True)
class ZonePaths:
    """Resolved once at start from the service definition.

    `home` is the zone account's home. The CLI's config home is the default
    `<home>/.claude`; no CLAUDE_CONFIG_DIR is set, because the whole account
    belongs to QMX."""

    home: Path
    runtime: Path  # read-only to this account
    credential_file: Path  # the zone credential, written by the operator side
    door_base: str  # for example http://127.0.0.1:8767


@dataclass(frozen=True)
class ZoneCredential:
    """Proves "this is the zone" to the door. Grants exactly the zone's rights
    (read, propose with approval, model relay). Not money-capable."""

    value: str

    def __repr__(self) -> str:
        return "ZoneCredential(<redacted>)"


ALLOWED_PARENT_ENV: frozenset[str] = frozenset(
    {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP",
     "USERPROFILE", "HOME", "LANG", "LC_ALL", "TZ"}
)
"""The only names copied from the service environment into the CLI env."""


def cli_env(route: ModelRoute, credential: ZoneCredential, paths: ZonePaths,
            spec: ThreadSpec, parent: dict[str, str]) -> dict[str, str]:
    """Pure. Build the CLI child env.

    Always: copy ALLOWED_PARENT_ENV from `parent`; set
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1, ENABLE_CLAUDEAI_MCP_SERVERS=false,
    CLAUDE_CODE_ENABLE_TODO_TOOLS=1, CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH from
    the spec, CLAUDE_AGENT_SDK_CLIENT_APP=QMA, and ANTHROPIC_API_KEY="" (an
    empty value, so a merged parent key can never win).

    Direct: no ANTHROPIC_BASE_URL and no ANTHROPIC_AUTH_TOKEN. The CLI uses
    its own login.

    ViaDoor: ANTHROPIC_BASE_URL=<door_base>/zone/model/<profile_id>,
    ANTHROPIC_AUTH_TOKEN=<zone credential>, all four tier variables pinned,
    and one variable per quirk. BASE_URL is never set without AUTH_TOKEN, so
    the plan login can never be sent to the door.
    """
    raise NotImplementedError


def build_options(spec: ThreadSpec, paths: ZonePaths, credential: ZoneCredential,
                  asks: "AskRelay", parent_env: dict[str, str]) -> Any:
    """Pure apart from constructing the SDK object. Returns ClaudeAgentOptions.

    - tools: the claude_code preset, minus spec.disabled_tools (Workflow by default).
    - system_prompt: preset claude_code with append=spec.append.
    - permission_mode: spec.mode, always.
    - setting_sources: ["user"]. The user tier is this account's own ~/.claude,
      which the operator side mirrors. Project and local sources stay off, so a
      shared repo's .claude/ hooks never run here.
    - cwd: spec.workspace.
    - mcp_servers: {"qmx": http server at <door_base>/zone/mcp with headers
      Authorization: Bearer <credential> and X-QMX-Thread: <thread id>},
      plus spec.extra_mcp. strict_mcp_config=True.
    - env: cli_env(...).
    - can_use_tool: asks.ask (forwards to the operator, waits for AnswerAsk).
    - resume: spec.resume. model, effort from the spec.
    - include_partial_messages=True, enable_file_checkpointing=True,
      extra_args={"replay-user-messages": None}.
    """
    raise NotImplementedError


def to_blocks(message: Any) -> list[Block]:
    """Pure. One SDK message to zero or more wire blocks.

    TextBlock from assistant text and stream deltas, ToolBlock from tool_use and
    tool results (agent_id from parent_tool_use_id), PlanBlock from the task
    tools, AgentsBlock from Agent tool start and finish. Ported from the
    mapping in qmx_agents.copilot.stream_turn, which is deleted after."""
    raise NotImplementedError


class AskRelay:
    """Turns the SDK's can_use_tool callback into an Ask event and waits.

    Pending asks are kept by AskId and re-announced in every Hello, so an ask
    survives a link drop. The callback may stay pending for as long as the
    operator takes. On AnswerAsk it returns PermissionResultAllow or Deny."""

    async def ask(self, tool_name: str, tool_input: dict[str, Any], context: Any) -> Any:
        raise NotImplementedError

    def answer(self, ask: AskId, allow: bool, message: str) -> None:
        raise NotImplementedError

    def pending(self) -> tuple[Ask, ...]:
        raise NotImplementedError


class ThreadHost:
    """One chat: one ClaudeSDKClient, one CLI process while live.

    State: idle client disconnected (no process), live (process up), turn
    running. Events get a per-thread Seq and go into a bounded buffer that is
    replayed after a reconnect, so an operator-side restart loses nothing.
    After spec.idle_reap_seconds with no turn and no background task, the
    client disconnects and the CLI exits. The next Send reconnects with resume.
    """

    def __init__(self, spec: ThreadSpec, paths: ZonePaths, credential: ZoneCredential,
                 asks: AskRelay) -> None:
        raise NotImplementedError

    async def send(self, text: str, typed_by_operator: bool) -> None:
        raise NotImplementedError

    async def interrupt(self) -> None:
        raise NotImplementedError

    async def set_mode(self, mode: PermissionMode) -> None:
        raise NotImplementedError

    async def set_model(self, model: str) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError

    def events_after(self, seq: Seq) -> list[Event]:
        """Buffered events with seq above `seq`, for replay after reconnect."""
        raise NotImplementedError


class Runner:
    """The service main loop.

    1. Read the zone credential. Set the whole-zone memory cap where the OS
       has one inside the process (Windows Job Object; Linux and macOS take it
       from the service manager).
    2. Dial <door_base>/zone/link with the credential. Send Hello.
    3. Apply commands in order, acking each CommandId once.
    4. On link loss keep running turns, buffer events, redial with backoff.
    """

    def __init__(self, paths: ZonePaths) -> None:
        raise NotImplementedError

    async def serve(self) -> None:
        raise NotImplementedError

    async def apply(self, command: Command) -> None:
        raise NotImplementedError

    def apply_user_tier(self, put: PutUserTier) -> None:
        """Write only MIRRORED_PATHS under <home>/.claude, atomically, and skip
        if the stored hash matches. Removes mirrored files the operator deleted."""
        raise NotImplementedError


async def run_login(paths: ZonePaths) -> AsyncIterator[LoginUrl | LoginDone]:
    """Run the bundled CLI's own sign-in as this account and report progress.

    Starts `claude auth login` with the zone env. Reads the CLI's stdout for
    the authorize URL and yields it as LoginUrl. The operator's browser opens
    the URL; Anthropic redirects to the CLI's loopback callback, which this
    account is listening on, because loopback is shared by all accounts on the
    machine. The CLI exchanges the code and stores its own credential.

    This function never writes to the CLI's stdin. If the CLI needs a pasted
    code instead of the loopback callback (check L1), it yields LoginDone with
    signed_in=False and method="needs_native_terminal", and the operator signs
    in through the per-OS native path in design.md. QMA never relays the code.

    Ends with LoginDone from `claude auth status`.
    """
    raise NotImplementedError
    yield  # pragma: no cover


async def run_probe(targets: tuple[ProbeTarget, ...]) -> tuple[ProbeFinding, ...]:
    """Inside-out boundary check, run as this account.

    For each target: try to read the path, create and delete a file, read the
    keyring entry with the platform backend, or open the TCP port. `reachable`
    True on a protected target is a leak. The operator side treats the result
    as evidence, not proof, and pairs it with its own outside-in ACL audit."""
    raise NotImplementedError


def main() -> None:
    raise NotImplementedError
