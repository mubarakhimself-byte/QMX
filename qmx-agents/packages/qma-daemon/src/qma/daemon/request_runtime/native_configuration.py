"""Nonsecret operator native selection; parsing performs no SDK or auth I/O."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .contracts import ProviderCapabilities, ProviderEvent, ProviderRequest, ProviderResult
from .providers import ProviderError


@dataclass(frozen=True, slots=True)
class NativeProviderConfiguration:
    identity: str
    backend: Literal["codex", "claude"]
    executable: Path
    dedicated_home: Path
    empty_workspace: Path
    native_policy_reviewed: bool = False

    @property
    def capabilities(self) -> ProviderCapabilities:
        # Configuration eligibility is not authentication or runtime availability.
        return ProviderCapabilities(self.identity, resume=True, execution_kind="agent_session")

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        raise ProviderError("unbound_session", "Native selection requires current host composition")
