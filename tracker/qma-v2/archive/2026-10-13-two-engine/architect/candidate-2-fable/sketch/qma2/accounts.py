"""Accounts, the router and limit snapshots.

Router rule (operator, 16:22): balance sessions by usage left and capability, never a single
request. `pick` runs at segment start only. Within a segment the account is sticky.

Family guard: Claude models run only on a CLAUDE_SUBSCRIPTION account (never API); GPT only
on CHATGPT_OAUTH. Every other provider is API_KEY on the OpenAI engine. There is exactly one
Claude account; the seam for more exists (`accounts` table) but no Claude rotation until the
operator says so.

Background cap: a background thread may start on the Claude account only while the latest
`five_hour` snapshot is below `background_cap_pct` (default 50, UI-editable). Foreground
threads ignore the cap; the operator sees the window on the usage page.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from qma2.secrets import SecretStore
from qma2.store import Store
from qma2.types import Account, AccountId, EngineKind, LimitSnapshot, ModelRef, Provider


class RouterError(Exception): ...


@dataclass(frozen=True)
class SessionNeed:
    model: ModelRef | None  # explicit choice beats everything else
    engine: EngineKind | None
    background: bool
    prefer: str  # "capable" | "cheap"


@dataclass(frozen=True)
class Pick:
    account: Account
    model: ModelRef
    engine: EngineKind
    reason: str  # shown in the console: "claude-max: 31% of 5h used"


class Router:
    def __init__(self, store: Store, secrets: SecretStore) -> None:
        raise NotImplementedError

    def pick(self, need: SessionNeed) -> Pick:
        """Pure over store reads.
        # TODO: candidates = enabled accounts whose engine/model family fits `need`;
        #       drop accounts with latest status == "rejected" or (background and used_pct >= cap);
        #       prefer capable: Claude > GPT > others; cheap: lowest estimated $/MTok;
        #       tie → least recently used. No candidate → RouterError with the reason."""
        raise NotImplementedError

    def family_of(self, model: ModelRef) -> EngineKind:
        """ANTHROPIC → CLAUDE; everything else → OPENAI. Claude models are never routed through
        an API-key account (operator 17:11)."""
        raise NotImplementedError

    def latest_limits(self, account_id: AccountId | None = None) -> Sequence[LimitSnapshot]:
        raise NotImplementedError

    async def refresh_limits(self, account_id: AccountId) -> Sequence[LimitSnapshot]:
        """Pull where a pull exists (OpenRouter `GET /api/v1/key`); Claude and ChatGPT windows
        arrive as events during turns and are cached as the latest row (H1 fact 10, 12)."""
        raise NotImplementedError


def default_claude_account(claude_home: object) -> Account:
    """The one Claude Max account: kind CLAUDE_SUBSCRIPTION, credential_ref None."""
    raise NotImplementedError


def provider_base_url(provider: Provider) -> str | None:
    """Known OpenAI-compatible bases (OpenRouter, Meta, GLM, Kimi, DeepSeek, MiniMax)."""
    raise NotImplementedError
