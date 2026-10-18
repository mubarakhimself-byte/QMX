"""The loopback translator endpoint the CLI of a GPT chat calls as its ANTHROPIC_BASE_URL.

Compliance with the SIWC terms (02b D item 9) is structural:
- binds 127.0.0.1 on an ephemeral port, never 0.0.0.0;
- every request must carry the per-run secret as its bearer (the GPT profile's
  ANTHROPIC_AUTH_TOKEN); a new secret per start;
- accepts only the GPT profile's model ids, so it is not general-purpose API access;
- uses QMA's own SIWC registration (`agent_name_hint="QMA"`), never Codex's login.

Runs as a task inside the qmx-control process, on its own listener (not under BearerGate).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qma.gpt.probe import ProbePassed
    from qma.gpt.siwc import SiwcSession


@dataclass(frozen=True)
class TranslatorHandle:
    """Proof that a translator is running. `launch.launch_env` needs one for a GPT chat."""

    base_url: str
    secret: str


class Translator:
    @classmethod
    async def start(cls, passed: ProbePassed, session: SiwcSession, allowed_models: frozenset[str]) -> tuple[Translator, TranslatorHandle]:
        """The only way to get a `TranslatorHandle`. Requires a `ProbePassed`, so GPT cannot
        run on an unprobed route or after the translator code changed (the probe result is
        keyed to `translate.py`'s version hash)."""
        raise NotImplementedError

    async def stop(self) -> None:
        raise NotImplementedError


# Endpoints:
#   POST /v1/messages               to_responses -> POST api.openai.com/v1/responses (SSE) -> StreamState
#   POST /v1/messages/count_tokens  local estimate (the CLI falls back to estimates anyway)
#   anything else                   404
