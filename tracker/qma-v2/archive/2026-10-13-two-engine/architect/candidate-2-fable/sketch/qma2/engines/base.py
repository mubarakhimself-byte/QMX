"""Engine protocol: the whole SDK behind six methods. Only session.py imports this package.

An adapter owns: the SDK client, the message → EngineEvent translation, wiring the Gate into
the SDK's permission path, the prompt/compaction/sub-agent machinery its SDK lacks, and
usage/limit extraction. It never touches the store, the sink or the approvals table.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from qma2.config import ResolvedConfig
from qma2.gate import Gate
from qma2.supervisor import ProcessTree
from qma2.tools.registry import ToolRegistry
from qma2.types import (
    Account,
    ApprovalAnswer,
    Effort,
    EngineEvent,
    EngineKind,
    ModelRef,
    ProbeResult,
    Segment,
    Turn,
    TurnInput,
)


@dataclass(frozen=True)
class SegmentContext:
    """Everything an engine session needs; built by the actor, passed once."""

    cwd: Path
    config: ResolvedConfig
    gate: Gate
    registry: ToolRegistry
    account: Account
    env: Mapping[str, str]  # scrubbed + injected
    tree: ProcessTree
    history_seed: str | None  # when the segment continues a thread from another engine
    trace_dir: Path


class EngineSession(Protocol):
    def run(self, turn: Turn) -> AsyncIterator[EngineEvent]:
        """Stream one turn to completion. Always ends with TurnFinished."""
        ...

    async def steer(self, input: TurnInput) -> None: ...
    async def interrupt(self) -> None: ...
    async def switch(self, model: ModelRef | None, effort: Effort | None) -> None: ...
    async def compact(self, focus: str) -> None: ...
    async def resume_from(self, engine_state: bytes, answer: ApprovalAnswer) -> AsyncIterator[EngineEvent]:
        """OpenAI only: continue a run parked on an approval after a process restart.
        Claude raises `NotResumable` (the SDK's Future died with the process)."""
        ...

    async def close(self) -> None: ...


class Engine(Protocol):
    kind: EngineKind

    async def probe(self, account: Account, home_env: Mapping[str, str]) -> ProbeResult:
        """Claude: `claude auth status` under CLAUDE_CONFIG_DIR says loggedIn + claude.ai; no
        ANTHROPIC_* in the env; SDK importable. OpenAI: a 1-token request on the account's
        route (ChatGPT token or API key)."""
        ...

    async def open(self, segment: Segment, ctx: SegmentContext) -> EngineSession:
        """Resume when `segment.engine_session_id` is set; else start fresh (seeding with
        `ctx.history_seed` if present)."""
        ...
