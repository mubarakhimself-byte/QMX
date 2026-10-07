"""Scoped persistent memory and bounded, provider-independent agent hooks."""

from __future__ import annotations

import asyncio
import hashlib
import importlib.metadata
import json
import re
import sqlite3
from collections.abc import Awaitable, Callable, Mapping, Sequence
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Protocol, cast, runtime_checkable
from uuid import uuid4

from deepagents.backends import StateBackend
from deepagents.backends.protocol import BackendProtocol
from deepagents.middleware.summarization import create_summarization_middleware
from langchain.agents.middleware import AgentMiddleware, AgentState, ModelRequest, ModelResponse
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, StructuredTool, ToolException
from langgraph.runtime import Runtime
from langgraph.store.base import Item
from langgraph.store.sqlite import SqliteStore  # pyright: ignore[reportMissingTypeStubs]
from langgraph.types import Command

from qmx_agents.router import RunContext

Kind = Literal["facts", "episodes", "profile", "notes"]
KINDS: tuple[Kind, ...] = ("facts", "episodes", "profile", "notes")
Role = Literal["primary", "subagent", "scheduled", "headless"]
_INJECTION = re.compile(
    r"ignore\s+(?:(?:all|the)\s+)?(?:previous|prior|above)\s+instructions"
    r"|<\s*/?\s*(?:system|developer)\b|\[im_start\]\s*(?:system|developer)"
    r"|(?:^|\n)\s*(?:system|developer)\s*:",
    re.IGNORECASE,
)


def _prompt_text(text: str) -> str:
    if _INJECTION.search(text) or "\x00" in text:
        return "[Memory withheld: instruction-like content]"
    return text


class Scope(StrEnum):
    TASK = "task"
    WORKFLOW = "workflow"
    SESSION = "session"
    GLOBAL = "global"


@dataclass(frozen=True, slots=True)
class MemoryContext:
    profile: str
    node: str = "laptop"
    role: Role = "primary"
    session_id: str | None = None
    workflow_id: str | None = None
    task_id: str | None = None


@dataclass(slots=True)
class MemoryRecord:
    content: str
    kind: Kind = "facts"
    data: dict[str, Any] = field(default_factory=dict[str, Any])
    tags: tuple[str, ...] = ()
    source: str = ""
    id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    score: float | None = None


Approval = Callable[[Scope, MemoryRecord | None], Awaitable[bool]]


@dataclass(frozen=True, slots=True)
class ConfigField:
    key: str
    description: str
    secret: bool = False
    required: bool = False
    default: Any = None
    choices: tuple[str, ...] = ()
    env_var: str | None = None


@runtime_checkable
class MemoryProvider(Protocol):
    name: str
    capabilities: frozenset[str]

    def is_available(self) -> bool: ...
    async def open(self, ctx: MemoryContext, config: Mapping[str, Any]) -> None: ...
    async def close(self) -> None: ...
    async def put(
        self, scope: Scope, record: MemoryRecord, *, ttl_minutes: float | None = None
    ) -> str: ...
    async def get(self, scope: Scope, record_id: str) -> MemoryRecord | None: ...
    async def delete(self, scope: Scope, record_id: str) -> None: ...
    async def search(
        self,
        scopes: Sequence[Scope],
        query: str | None = None,
        *,
        kinds: Sequence[str] | None = None,
        filter: Mapping[str, Any] | None = None,
        limit: int = 10,
    ) -> list[MemoryRecord]: ...
    def system_block(self) -> str | None: ...
    async def prefetch(self, query: str, scopes: Sequence[Scope]) -> str | None: ...
    def on_turn_end(
        self, user: str, assistant: str, messages: Sequence[Mapping[str, Any]] | None = None
    ) -> None: ...
    async def on_pre_compress(
        self, messages: Sequence[Mapping[str, Any]], *, require_checkpoint: bool = False
    ) -> str | None: ...
    async def on_scope_end(
        self, scope: Scope, messages: Sequence[Mapping[str, Any]] | None = None
    ) -> None: ...
    def tools(self) -> list[BaseTool]: ...
    def config_schema(self) -> list[ConfigField]: ...


class BaseMemoryProvider:
    """Optional hooks are inert; providers implement their own CRUD."""

    capabilities: frozenset[str] = frozenset()

    def is_available(self) -> bool:
        return True

    async def open(self, ctx: MemoryContext, config: Mapping[str, Any]) -> None:
        self.ctx = ctx

    async def close(self) -> None:
        pass

    def system_block(self) -> str | None:
        return None

    async def prefetch(self, query: str, scopes: Sequence[Scope]) -> str | None:
        return None

    def on_turn_end(
        self, user: str, assistant: str, messages: Sequence[Mapping[str, Any]] | None = None
    ) -> None:
        pass

    async def on_pre_compress(
        self, messages: Sequence[Mapping[str, Any]], *, require_checkpoint: bool = False
    ) -> str | None:
        if require_checkpoint:
            raise RuntimeError("This provider cannot durably checkpoint a transcript")
        return None

    async def on_scope_end(
        self, scope: Scope, messages: Sequence[Mapping[str, Any]] | None = None
    ) -> None:
        pass

    def tools(self) -> list[BaseTool]:
        return []

    def config_schema(self) -> list[ConfigField]:
        return []


def _segment(value: str | None) -> str:
    # SqliteStore joins namespace segments with dots; disallow ambiguous identities.
    if not value or any(char in value for char in (".", "*", "/", "\\")):
        raise ValueError("Memory identities must be nonempty, without dots, wildcards or slashes")
    return value


def namespace(ctx: MemoryContext, scope: Scope, kind: str | None = None) -> tuple[str, ...]:
    prefix = ("qmx", _segment(ctx.profile))
    if scope == Scope.GLOBAL:
        prefix += ("global",)
    elif scope == Scope.SESSION:
        prefix += ("session", _segment(ctx.session_id))
    elif scope == Scope.WORKFLOW:
        prefix += ("workflow", _segment(ctx.workflow_id))
    else:
        prefix += ("workflow", _segment(ctx.workflow_id), "task", _segment(ctx.task_id))
    return (*prefix, kind) if kind else prefix


def memory_path(home: Path, profile: str) -> Path:
    _segment(profile)
    if profile == "copilot":
        return home / "copilot" / "memory.db"
    if profile.startswith("app:"):
        app_id = _segment(profile[4:])
        if any(char in app_id for char in ':<>"|?\x00'):
            raise ValueError("App memory identity must be a valid folder name")
        return home / "apps" / app_id / "memory.db"
    raise ValueError("Memory profile must be copilot or app:<id>")


class StoreMemoryProvider(BaseMemoryProvider):
    name = "sqlite"
    capabilities = frozenset({"ttl"})

    def __init__(self, store: SqliteStore, *, approval: Approval | None = None) -> None:
        if store.conn.in_transaction:
            raise ValueError("Memory store connection must not have an active transaction")
        # SqliteStore starts and commits its own transactions, including migrations.
        store.conn.isolation_level = None
        self.store = store
        self.approval = approval
        self._owned_connection: sqlite3.Connection | None = None

    @classmethod
    def from_home(
        cls, home: Path, profile: str, *, approval: Approval | None = None
    ) -> StoreMemoryProvider:
        path = memory_path(home, profile)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        provider = cls(SqliteStore(conn), approval=approval)
        provider._owned_connection = conn
        return provider

    async def open(self, ctx: MemoryContext, config: Mapping[str, Any]) -> None:
        await super().open(ctx, config)
        await asyncio.to_thread(self.store.setup)

    async def close(self) -> None:
        if self._owned_connection is not None:
            self._owned_connection.close()
            self._owned_connection = None

    def config_schema(self) -> list[ConfigField]:
        return [ConfigField("provider", "Memory provider", default="sqlite")]

    async def _approve(self, scope: Scope, record: MemoryRecord | None) -> None:
        if scope == Scope.GLOBAL and (
            self.approval is None or not await self.approval(scope, record)
        ):
            raise PermissionError("Global memory writes require approval")

    async def put(
        self, scope: Scope, record: MemoryRecord, *, ttl_minutes: float | None = None
    ) -> str:
        await self._approve(scope, record)
        if record.kind not in KINDS:
            raise ValueError("Unknown memory kind")
        if ttl_minutes is not None and ttl_minutes <= 0:
            raise ValueError("Memory TTL must be positive")
        key = record.id or uuid4().hex
        value = {
            "content": record.content,
            "kind": record.kind,
            "data": record.data,
            "tags": list(record.tags),
            "source": record.source,
        }
        json.dumps(value, allow_nan=False)
        await asyncio.to_thread(
            self.store.put, namespace(self.ctx, scope, record.kind), key, value, ttl=ttl_minutes
        )
        return key

    @staticmethod
    def _record(item: Item) -> MemoryRecord:
        return MemoryRecord(
            content=item.value["content"],
            kind=item.value["kind"],
            data=item.value.get("data", {}),
            tags=tuple(item.value.get("tags", [])),
            source=item.value.get("source", ""),
            id=item.key,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    async def get(self, scope: Scope, record_id: str) -> MemoryRecord | None:
        for kind in KINDS:
            item = await asyncio.to_thread(
                self.store.get, namespace(self.ctx, scope, kind), record_id
            )
            if item is not None:
                return self._record(item)
        return None

    async def delete(self, scope: Scope, record_id: str) -> None:
        await self._approve(scope, await self.get(scope, record_id))
        for kind in KINDS:
            await asyncio.to_thread(self.store.delete, namespace(self.ctx, scope, kind), record_id)

    async def search(
        self,
        scopes: Sequence[Scope],
        query: str | None = None,
        *,
        kinds: Sequence[str] | None = None,
        filter: Mapping[str, Any] | None = None,
        limit: int = 10,
    ) -> list[MemoryRecord]:
        if limit <= 0:
            return []
        found: dict[tuple[tuple[str, ...], str], Item] = {}
        for scope in scopes:
            prefix = namespace(self.ctx, scope)
            offset = 0
            while True:
                items = await asyncio.to_thread(
                    self.store.search, prefix, filter=dict(filter or {}), limit=100, offset=offset
                )
                for item in items:
                    # Only workflow recall includes child tasks; the other scopes stay exact.
                    if scope != Scope.WORKFLOW and len(item.namespace) != len(prefix) + 1:
                        continue
                    if kinds is not None and item.value.get("kind") not in kinds:
                        continue
                    if (
                        query
                        and query.casefold() not in str(item.value.get("content", "")).casefold()
                    ):
                        continue
                    found[item.namespace, item.key] = item
                if len(items) < 100:
                    break
                offset += len(items)
        return [
            self._record(item)
            for item in sorted(found.values(), key=lambda item: item.updated_at, reverse=True)[
                :limit
            ]
        ]

    def system_block(self) -> str | None:
        items = self.store.search(namespace(self.ctx, Scope.GLOBAL, "profile"), limit=10)
        return "\n".join(str(item.value["content"]) for item in items)

    async def prefetch(self, query: str, scopes: Sequence[Scope]) -> str | None:
        records = await self.search(scopes, query)
        # A full user question rarely matches verbatim; keep recent scoped context useful.
        if not records and query:
            records = await self.search(scopes)
        return "\n".join(record.content for record in records)


def load_provider(name: str) -> MemoryProvider:
    """Enumerating installed plugins does not import an unselected provider."""
    matches = list(importlib.metadata.entry_points(group="qmx.memory_providers", name=name))
    if len(matches) != 1:
        raise ValueError(f"Expected one installed memory provider named {name!r}")
    provider = matches[0].load()()
    if not isinstance(provider, MemoryProvider) or not provider.is_available():
        raise ValueError(f"Memory provider {name!r} is unavailable or incompatible")
    return provider


class MemoryManager:
    def __init__(
        self,
        builtin: MemoryProvider,
        external: MemoryProvider | None = None,
        *,
        spill_dir: Path,
        profile_cap: int = 2000,
        prefetch_cap: int = 10000,
        approval: Approval | None = None,
    ) -> None:
        if profile_cap <= 0 or prefetch_cap < 256:
            raise ValueError(
                "Memory prompt caps must be positive; prefetch cap must be at least 256"
            )
        if external is not None and not isinstance(cast("object", external), MemoryProvider):
            raise ValueError("MemoryManager accepts at most one compatible external provider")
        self.builtin = builtin
        self.external = external
        self.spill_dir = spill_dir
        self.profile_cap = profile_cap
        self.prefetch_cap = prefetch_cap
        self.approval = approval
        if isinstance(builtin, StoreMemoryProvider) and approval is not None:
            builtin.approval = approval
        self._pinned: dict[tuple[str, str], str] = {}
        self.summary_messages: ContextVar[Sequence[BaseMessage]] = ContextVar(
            "memory_summary", default=()
        )
        self.delegating: ContextVar[bool] = ContextVar("memory_delegating", default=False)

    @property
    def providers(self) -> tuple[MemoryProvider, ...]:
        return (self.builtin, self.external) if self.external is not None else (self.builtin,)

    async def open(self, ctx: MemoryContext, config: Mapping[str, Any] | None = None) -> None:
        self.ctx = ctx
        for provider in self.providers:
            await provider.open(ctx, config or {})

    async def close(self) -> None:
        for provider in reversed(self.providers):
            await provider.close()

    def pinned(self) -> str:
        key = (self.ctx.profile, self.ctx.session_id or "")
        if key not in self._pinned:
            self._pinned[key] = _prompt_text(
                "\n".join(
                    block for provider in self.providers if (block := provider.system_block())
                )
            )[: self.profile_cap]
        return self._pinned[key]

    async def prefetch(self, query: str, scopes: Sequence[Scope]) -> str:
        text = "\n".join(
            [
                block
                for provider in self.providers
                if (block := await provider.prefetch(query, scopes))
            ]
        )
        return await self.bound(text)

    async def bound(self, text: str) -> str:
        """Bound both recalled context and explicit search tool results."""
        text = _prompt_text(text)
        if len(text) <= self.prefetch_cap:
            return text
        self.spill_dir.mkdir(parents=True, exist_ok=True)
        path = self.spill_dir / f"{hashlib.sha256(text.encode()).hexdigest()}.txt"
        await asyncio.to_thread(path.write_text, text, encoding="utf-8")
        reference = f"\n[Full memory: /memory-recall/{path.name}]\n"
        remaining = self.prefetch_cap - len(reference)
        if remaining < 0:
            raise ValueError("Spill path exceeds the memory prompt cap")
        head = remaining // 2
        return text[:head] + reference + (text[-(remaining - head) :] if remaining - head else "")

    def on_turn_end(self, messages: Sequence[BaseMessage]) -> None:
        if self.ctx.role != "primary" or self.delegating.get():
            return
        user = next((msg.text for msg in reversed(messages) if msg.type == "human"), "")
        assistant = next((msg.text for msg in reversed(messages) if msg.type == "ai"), "")
        transcript = _transcript(messages)
        # Providers own their executor; the contract requires this hook to return immediately.
        for provider in self.providers:
            provider.on_turn_end(user, assistant, transcript)

    async def on_pre_compress(
        self, messages: Sequence[BaseMessage], *, require_checkpoint: bool = False
    ) -> None:
        if self.ctx.role != "primary" or self.delegating.get():
            return
        for provider in self.providers:
            await provider.on_pre_compress(
                _transcript(messages), require_checkpoint=require_checkpoint
            )

    def tools(self, scope: Scope = Scope.TASK) -> list[BaseTool]:
        async def memory_put(content: str, kind: Kind = "facts") -> str:
            record = MemoryRecord(content=content, kind=kind)
            if (
                scope == Scope.GLOBAL
                and not isinstance(self.builtin, StoreMemoryProvider)
                and (self.approval is None or not await self.approval(scope, record))
            ):
                raise ToolException("Global memory writes require approval")
            try:
                return await self.builtin.put(scope, record)
            except PermissionError as exc:
                raise ToolException(str(exc)) from exc

        async def memory_search(query: str = "", limit: int = 10) -> str:
            return await self.bound(
                json.dumps(
                    [
                        {"id": record.id, "content": record.content, "kind": record.kind}
                        for record in await self.builtin.search([scope], query, limit=limit)
                    ]
                )
            )

        def put_sync(content: str, kind: Kind = "facts") -> str:
            return asyncio.run(memory_put(content, kind))

        def search_sync(query: str = "", limit: int = 10) -> str:
            return asyncio.run(memory_search(query, limit))

        result = [
            StructuredTool.from_function(
                func=put_sync,
                coroutine=memory_put,
                name="memory_put",
                description="Save an explicit memory in the configured scope.",
                handle_tool_error=True,
            ),
            StructuredTool.from_function(
                func=search_sync,
                coroutine=memory_search,
                name="memory_search",
                description="Search memory in the configured scope.",
            ),
            *self.builtin.tools(),
        ]
        if self.external is not None:
            result.extend(
                tool.model_copy(update={"name": f"{self.external.name}_{tool.name}"})
                for tool in self.external.tools()
            )
        return result

    def middleware(self, scope: Scope = Scope.TASK) -> list[AgentMiddleware[Any, Any, Any]]:
        return [MemoryMiddleware(self, scope)]

    def summarization(
        self, model: BaseChatModel, backend: BackendProtocol | None
    ) -> AgentMiddleware[Any, Any, Any]:
        callbacks = model.callbacks
        if callbacks is not None and not isinstance(callbacks, list):
            raise ValueError("Memory summarization expects a list of model callbacks")
        summary_model = model.model_copy(
            update={"callbacks": [*(callbacks or []), _PreCompress(self)]}
        )
        delegate = create_summarization_middleware(summary_model, backend or StateBackend())
        return _MemorySummarization(self, delegate)


def _transcript(messages: Sequence[BaseMessage]) -> list[Mapping[str, Any]]:
    return [
        {"role": message.type, "content": message.text}
        for message in messages
        if message.type in {"human", "ai"}
    ]


class MemoryState(AgentState[Any]):
    memory_profile: str
    memory_prefetch: str


class MemoryMiddleware(AgentMiddleware[MemoryState, Any]):
    state_schema = MemoryState

    def __init__(self, manager: MemoryManager, scope: Scope) -> None:
        self.manager = manager
        self.scope = scope

    def before_agent(self, state: MemoryState, runtime: Runtime[Any]) -> dict[str, Any]:
        context = runtime.context
        if isinstance(context, RunContext):
            for key in ("session_id", "workflow_id", "task_id"):
                supplied = getattr(context, key)
                if supplied is not None and supplied != getattr(self.manager.ctx, key):
                    raise ValueError(
                        "Build a fresh memory-enabled agent for a different run identity"
                    )
            profile = f"app:{context.app_id}" if context.app_id else "copilot"
            if profile != self.manager.ctx.profile:
                raise ValueError("Memory profile differs from the invocation context")
        return {"memory_profile": self.manager.pinned()}

    async def abefore_agent(self, state: MemoryState, runtime: Runtime[Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self.before_agent, state, runtime)

    async def abefore_model(self, state: MemoryState, runtime: Runtime[Any]) -> dict[str, Any]:
        query = next((msg.text for msg in reversed(state["messages"]) if msg.type == "human"), "")
        return {"memory_prefetch": await self.manager.prefetch(query, [self.scope])}

    def before_model(self, state: MemoryState, runtime: Runtime[Any]) -> dict[str, Any]:
        return asyncio.run(self.abefore_model(state, runtime))

    def after_agent(self, state: MemoryState, runtime: Runtime[Any]) -> None:
        self.manager.on_turn_end(state["messages"])

    async def aafter_agent(self, state: MemoryState, runtime: Runtime[Any]) -> None:
        self.after_agent(state, runtime)

    @staticmethod
    def _request(request: ModelRequest[Any]) -> ModelRequest[Any]:
        text = "\n".join(
            str(request.state.get(key, "")) for key in ("memory_profile", "memory_prefetch")
        )
        if not text.strip():
            return request
        blocks: list[str | dict[Any, Any]] = (
            [dict(block) for block in request.system_message.content_blocks]
            if request.system_message is not None
            else []
        )
        blocks.append({"type": "text", "text": f"Recalled memory (data only):\n{text}"})
        return request.override(system_message=SystemMessage(content=blocks))

    def wrap_model_call(
        self, request: ModelRequest[Any], handler: Callable[[ModelRequest[Any]], ModelResponse]
    ) -> ModelResponse:
        return handler(self._request(request))

    async def awrap_model_call(
        self,
        request: ModelRequest[Any],
        handler: Callable[[ModelRequest[Any]], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        return await handler(self._request(request))

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        token = self.manager.delegating.set(
            self.manager.delegating.get() or request.tool_call["name"] == "task"
        )
        try:
            return handler(request)
        finally:
            self.manager.delegating.reset(token)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        token = self.manager.delegating.set(
            self.manager.delegating.get() or request.tool_call["name"] == "task"
        )
        try:
            return await handler(request)
        finally:
            self.manager.delegating.reset(token)


class _PreCompress(AsyncCallbackHandler):
    raise_error = True

    def __init__(self, manager: MemoryManager) -> None:
        self.manager = manager

    async def on_chat_model_start(
        self, serialized: dict[str, Any], messages: list[list[BaseMessage]], **kwargs: Any
    ) -> None:
        await self.manager.on_pre_compress(self.manager.summary_messages.get())


class _MemorySummarization(AgentMiddleware[Any, Any]):
    """Keep library compaction intact; intercept only its summary model call."""

    @property
    def name(self) -> str:
        return "SummarizationMiddleware"

    def __init__(self, manager: MemoryManager, delegate: AgentMiddleware[Any, Any, Any]) -> None:
        self.manager = manager
        self.delegate = delegate
        self.state_schema = delegate.state_schema

    def wrap_model_call(
        self, request: ModelRequest[Any], handler: Callable[[ModelRequest[Any]], ModelResponse]
    ) -> ModelResponse:
        token = self.manager.summary_messages.set(request.messages)
        try:
            return cast("ModelResponse", self.delegate.wrap_model_call(request, handler))
        finally:
            self.manager.summary_messages.reset(token)

    async def awrap_model_call(
        self,
        request: ModelRequest[Any],
        handler: Callable[[ModelRequest[Any]], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        token = self.manager.summary_messages.set(request.messages)
        try:
            return cast("ModelResponse", await self.delegate.awrap_model_call(request, handler))
        finally:
            self.manager.summary_messages.reset(token)
