"""Accounts: the one Claude Max, ChatGPT sign-in, and API-key providers.

Reached as `harness.accounts`. Writes go through the harness Store (single writer).

Claude: QMX never sees a token. `claude_login_command` returns the unmodified Claude Code
binary's own login, run by the operator in a terminal with CLAUDE_CONFIG_DIR set to QMX's
claude-home (H1 fact 4). `claude_status` is the copied `check_environment` preflight.

ChatGPT: dynamic client registration + PKCE against OpenAI; tokens to the SecretStore;
QMX refreshes them. Requests go to https://api.openai.com/v1/responses only, never
chatgpt.com/backend-api (H1 fact 17). Unit U8 probes this route before building on it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from qma2.model import Account, AccountId, ApiKeyAccount, ChatGPTAccount, OperatorProof, Wire


@dataclass(frozen=True, slots=True)
class ClaudeStatus:
    """From `claude auth status` under claude-home. Never reads credential files."""

    signed_in: bool
    auth_method: str | None  # must be "claude.ai"
    first_party: bool
    config_dir_matches: bool
    cli_version: str
    problem: Literal["api_env_present", "not_signed_in", "wrong_auth", "version", None]


@dataclass(frozen=True, slots=True)
class ApiKeyAccountInput:
    provider: str
    label: str
    base_url: str
    wire: Wire
    models: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SignInStart:
    authorize_url: str
    state: str


class Accounts:
    async def list(self) -> Sequence[Account]:
        raise NotImplementedError

    async def claude_status(self) -> ClaudeStatus:
        """# TODO pseudocode (copied from native_claude._preflight, minus version pin)
        # refuse when any ANTHROPIC_* / CLAUDE_CODE_USE_* name is in the control env
        # run `<claude> auth status` with env = secrets.host_env(ClaudeRoute...)
        # require loggedIn, authMethod == "claude.ai", apiProvider in {None, firstParty},
        #         configDirectory == claude_home
        """
        raise NotImplementedError

    def claude_login_command(self) -> Sequence[str]:
        """argv the console shows and `python -m qma2 login claude` runs."""
        raise NotImplementedError

    async def put_api_key(self, spec: ApiKeyAccountInput, key: str, proof: OperatorProof) -> ApiKeyAccount:
        """Stores `key` under qmx/<provider>/<label>; settings and DB keep only the ref.
        Refuses Anthropic and OpenAI first-party base URLs (operator: never pay API for
        Claude or GPT)."""
        raise NotImplementedError

    async def chatgpt_begin(self, proof: OperatorProof) -> SignInStart:
        raise NotImplementedError

    async def chatgpt_complete(self, code: str, state: str) -> ChatGPTAccount:
        """OAuth redirect target. `state` binds it to a begin() the operator started."""
        raise NotImplementedError

    async def disable(self, account: AccountId, proof: OperatorProof) -> None:
        raise NotImplementedError
