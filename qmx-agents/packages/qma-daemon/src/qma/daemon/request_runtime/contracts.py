"""Provider-neutral request contracts. Behavior profiles confer no authority."""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol


def _is_text(value: object) -> bool:
    """Validate deserialized/plugin-supplied values at the runtime boundary."""
    return isinstance(value, str)


@dataclass(frozen=True, slots=True)
class CopilotProfile:
    profile_id: str
    role: Literal["global", "application", "page"] = "global"
    instructions: str = ""
    app_instance_id: str | None = None
    page_id: str | None = None

    def __post_init__(self) -> None:
        if (
            not _is_text(self.profile_id)
            or not self.profile_id.strip()
            or self.role not in {"global", "application", "page"}
        ):
            raise ValueError("profile id and supported role are required")
        if not _is_text(self.instructions):
            raise ValueError("profile instructions must be text")
        if any(
            value is not None and not _is_text(value)
            for value in (self.app_instance_id, self.page_id)
        ):
            raise ValueError("profile scope ids must be text")
        if self.role in {"application", "page"} and not self.app_instance_id:
            raise ValueError("application and page profiles require an app instance")
        if self.role == "page" and not self.page_id:
            raise ValueError("page profiles require a page id")
        if self.role == "global" and (self.app_instance_id or self.page_id):
            raise ValueError("global profile has no app or page binding")
        if self.role == "application" and self.page_id:
            raise ValueError("application profile has no page binding")


@dataclass(frozen=True, slots=True)
class RequestSpec:
    idempotency_key: str
    principal: str
    product_session_id: str
    context_revision: int
    profile: CopilotProfile
    prompt: str
    provider_id: str
    model: str | None = None
    timeout_seconds: float = 120


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    provider_id: str
    resume: bool = False
    native_tools: bool = False
    execution_kind: Literal["inference", "agent_session"] = "inference"


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    prompt: str
    model: str | None = None
    cwd: str = ""
    thread_id: str | None = None
    timeout_seconds: float = 120
    instructions: str = ""
    request_id: str = ""
    graph_thread_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderEvent:
    name: str
    payload: Mapping[str, object] = field(default_factory=dict[str, object])


@dataclass(frozen=True, slots=True)
class ProviderResult:
    content: str
    thread_id: str | None = None
    turn_id: str | None = None
    deployment_id: str | None = None

    def __post_init__(self) -> None:
        if not _is_text(self.content):
            raise ValueError("provider content must be text")
        if any(
            value is not None and not _is_text(value)
            for value in (self.thread_id, self.turn_id, self.deployment_id)
        ):
            raise ValueError("provider references must be text")


class ProviderAdapter(Protocol):
    @property
    def capabilities(self) -> ProviderCapabilities: ...

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult: ...


RequestStatus = Literal[
    "queued", "running", "cancellation_requested", "cancelled", "completed", "failed", "interrupted"
]


@dataclass(frozen=True, slots=True)
class RequestRecord:
    request_id: str
    spec: RequestSpec
    status: RequestStatus = "queued"
    attempt: int = 0
    result: ProviderResult | None = None
    error: str | None = None
    journal_seq: int = 0
    context_binding: str = ""
