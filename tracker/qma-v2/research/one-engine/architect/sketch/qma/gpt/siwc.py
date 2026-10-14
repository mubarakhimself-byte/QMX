"""Sign in with ChatGPT for QMA, per developers.openai.com/siwc (02b D items 1, 2, 9).

Flow: `client_id=dynamic_agent_client`, `agent_name_hint="QMA"`, a persisted
`ext_agent_host_id` (urn:uuid), PKCE S256, loopback callback on 127.0.0.1. Scopes include
`chatgpt.tokens.use.direct`. The access token lives about an hour; the refresh token rotates.

Storage: the refresh token and host id go in the OS secret store under `qmx/chatgpt`
(local and under the user's control). The access token stays in memory only.
Background use needs express consent (SIWC terms), stored as a flag the console asks for.
It is enforced at grant time: `Relay.grant(..., unattended=True)` refuses a GPT grant unless
`background_consent` is True (B17).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qma.harness.launch import SecretLookup


@dataclass(frozen=True)
class Grant:
    scopes: frozenset[str]
    client_id: str


class SiwcSession:
    async def access_token(self) -> str:
        """Refresh under one asyncio lock when within 5 minutes of expiry, store the rotated
        refresh token, return the access token. Concurrent GPT chats share one session, and
        the lock is the one real single-writer invariant here (rotating refresh tokens)."""
        raise NotImplementedError

    @property
    def background_consent(self) -> bool:
        raise NotImplementedError


async def sign_in(secrets: SecretLookup) -> tuple[SiwcSession, Grant]:
    """Opens the browser to OpenAI's page; the operator approves "QMA". Refuses a grant
    without `chatgpt.tokens.use.direct`."""
    raise NotImplementedError


def load(secrets: SecretLookup) -> SiwcSession | None:
    raise NotImplementedError
