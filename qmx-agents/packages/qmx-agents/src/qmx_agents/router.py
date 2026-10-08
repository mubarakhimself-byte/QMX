"""UI-editable model profiles, credential lookup and LangChain routing."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import quote, urlsplit

import httpx
import keyring
import yaml
from deepagents import HarnessProfileConfig, register_harness_profile
from keyring.errors import KeyringError
from langchain.agents.middleware import (
    AgentMiddleware,
    ModelFallbackMiddleware,
    ModelRequest,
    ModelResponse,
    ModelRetryMiddleware,
    wrap_model_call,
)
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, ConfigDict, Field, field_validator

Tier = Literal["fast", "workhorse", "coding", "reasoning_high"]
Provider = Literal["anthropic", "openai", "openrouter", "local", "cliproxy"]
TIERS: frozenset[Tier] = frozenset({"fast", "workhorse", "coding", "reasoning_high"})
DEFAULT_CONFIG = Path(__file__).with_name("models.yaml")
FIRECRAWL_SERVER: dict[str, Any] = {
    "url": "https://mcp.firecrawl.dev/v2/mcp",
    "enabled": False,
    "credential_ref": "qmx/firecrawl",
}


def model_selector(value: str) -> str:
    """Require an explicit tier or pinned provider model, never a latest alias."""
    provider, separator, model = value.partition(":")
    if not separator or not model or value != value.strip():
        raise ValueError("Use tier:<tier> or provider:<exact model id>")
    if provider == "tier":
        if model not in TIERS:
            raise ValueError(f"Unknown model tier: {model}")
    elif provider not in {"anthropic", "openai", "openrouter", "local", "cliproxy"}:
        raise ValueError(f"Unknown model provider: {provider}")
    elif "~" in model or model.endswith("latest"):
        raise ValueError("Model ids must be pinned; latest aliases are not supported")
    return value


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_url: str | None = None
    timeout: float = Field(default=600, gt=0)

    @field_validator("base_url")
    @classmethod
    def valid_url(cls, value: str | None) -> str | None:
        if value is not None:
            url = urlsplit(value)
            if (
                url.scheme not in {"http", "https"}
                or not url.hostname
                or any((url.username, url.password, url.query, url.fragment))
            ):
                raise ValueError("Provider URL must be HTTP(S), without credentials or query")
        return value


class RouterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: str = "daily"
    profiles: dict[str, dict[Tier, str]]
    providers: dict[Provider, ProviderConfig]
    fallbacks: list[str] = Field(default_factory=list)
    max_retries: int = Field(default=2, ge=0)
    harness_profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    mcp_servers: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @field_validator("profiles")
    @classmethod
    def valid_profiles(cls, value: dict[str, dict[Tier, str]]) -> dict[str, dict[Tier, str]]:
        for tiers in value.values():
            if frozenset(tiers) != TIERS:
                raise ValueError("Each profile must define all four tiers")
            for selection in tiers.values():
                if model_selector(selection).startswith("tier:"):
                    raise ValueError("Profile entries must resolve directly to provider models")
        return value

    @field_validator("fallbacks")
    @classmethod
    def valid_fallbacks(cls, value: list[str]) -> list[str]:
        return [model_selector(item) for item in value]


def load_config(path: str | Path = DEFAULT_CONFIG) -> RouterConfig:
    config = RouterConfig.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
    if config.profile not in config.profiles:
        raise ValueError(f"Unknown model profile: {config.profile}")
    for key, profile in config.harness_profiles.items():
        register_harness_profile(key, HarnessProfileConfig.from_dict(profile))
    return config


def credential(provider: str) -> str:
    """Windows credentials are authoritative; only CI may use environment keys."""
    try:
        secret = keyring.get_password(f"qmx/{provider}", provider)
    except KeyringError:
        if os.environ.get("CI", "").lower() not in {"1", "true"}:
            raise
        secret = None
    if not secret and os.environ.get("CI", "").lower() in {"1", "true"}:
        secret = os.environ.get(f"QMX_{provider.upper().replace('-', '_')}_API_KEY")
    if not secret:
        raise ValueError(f"Missing credential qmx/{provider} (username {provider})")
    return secret


@dataclass
class RunContext:
    """Model overrides follow the same order as the Settings screens."""

    profile: str | None = None
    model: str = "tier:workhorse"
    node: str | None = None
    app: str | None = None
    workflow: str | None = None
    agent_node: str | None = None
    subagent: str | None = None
    session_id: str | None = None
    workflow_id: str | None = None
    task_id: str | None = None
    app_id: str | None = None
    request_model: str | None = None
    effective_models: dict[str, str] = field(default_factory=dict[str, str])


class ModelRouter:
    def __init__(
        self, config: RouterConfig, models: dict[str, BaseChatModel] | None = None
    ) -> None:
        self.config = config
        self._models = dict(models or {})

    def selection(self, selector: str, profile: str | None = None) -> str:
        if selector in TIERS:
            selector = f"tier:{selector}"
        selector = model_selector(selector)
        if selector.startswith("tier:"):
            profile = profile or self.config.profile
            if profile not in self.config.profiles:
                raise ValueError(f"Unknown model profile: {profile}")
            return self.config.profiles[profile][cast("Tier", selector[5:])]
        return selector

    def resolve(self, tier: str, profile: str | None = None) -> BaseChatModel:
        selection = self.selection(tier, profile)
        if selection not in self._models:
            provider, model = selection.split(":", 1)
            settings = self.config.providers[cast("Provider", provider)]
            kwargs: dict[str, Any] = {
                "api_key": credential(provider),
                "timeout": settings.timeout,
                # LangChain middleware owns retries, not the provider SDK too.
                "max_retries": 0,
            }
            if settings.base_url:
                kwargs["base_url"] = settings.base_url.rstrip("/")
            api_provider = provider
            if provider == "cliproxy":
                if not settings.base_url:
                    raise ValueError("CLIProxy requires a base_url")
                api_provider = "anthropic" if model.startswith("claude-") else "openai"
                base = settings.base_url.rstrip("/").removesuffix("/v1")
                kwargs["base_url"] = base if api_provider == "anthropic" else f"{base}/v1"
            elif provider in {"local", "openrouter"}:
                if not settings.base_url:
                    raise ValueError(f"{provider} requires a base_url")
                api_provider = "openai"
            self._models[selection] = init_chat_model(f"{api_provider}:{model}", **kwargs)
        return self._models[selection]

    def resolve_model(self, ctx: RunContext, agent: str = "agent") -> BaseChatModel:
        selection = ctx.model
        for override in (ctx.node, ctx.app, ctx.workflow, ctx.agent_node, ctx.subagent):
            if override is not None:
                selection = override
        if ctx.request_model is not None:
            selection = ctx.request_model
        effective = self.selection(selection, ctx.profile)
        ctx.effective_models[agent] = effective
        return self.resolve(effective)

    def router_middleware(self, ctx: RunContext, agent: str) -> AgentMiddleware[Any, RunContext]:
        def routed(request: ModelRequest[RunContext]) -> ModelRequest[RunContext]:
            runtime = cast("RunContext | None", request.runtime.context)
            context = (
                ctx
                if runtime is None
                else replace(
                    runtime,
                    agent_node=runtime.agent_node or ctx.agent_node,
                    subagent=ctx.subagent or runtime.subagent,
                )
            )
            return request.override(model=self.resolve_model(context, agent))

        @wrap_model_call
        def route(
            request: ModelRequest[RunContext],
            handler: Callable[[ModelRequest[RunContext]], ModelResponse[Any]],
        ) -> ModelResponse[Any]:
            return handler(routed(request))

        class RouterMiddleware(AgentMiddleware[Any, RunContext]):
            def wrap_model_call(
                self,
                request: ModelRequest[RunContext],
                handler: Callable[[ModelRequest[RunContext]], ModelResponse[Any]],
            ) -> ModelResponse[Any]:
                return cast("ModelResponse[Any]", route.wrap_model_call(request, handler))

            async def awrap_model_call(
                self,
                request: ModelRequest[RunContext],
                handler: Callable[[ModelRequest[RunContext]], Awaitable[ModelResponse[Any]]],
            ) -> ModelResponse[Any]:
                return await handler(routed(request))

        return RouterMiddleware()

    def middleware(self, ctx: RunContext, agent: str) -> list[AgentMiddleware[Any, RunContext]]:
        middlewares = [self.router_middleware(ctx, agent)]
        fallbacks = [self.resolve(item, ctx.profile) for item in self.config.fallbacks]
        if fallbacks:
            middlewares.append(ModelFallbackMiddleware(fallbacks[0], *fallbacks[1:]))
        middlewares.append(
            ModelRetryMiddleware(max_retries=self.config.max_retries, on_failure="error")
        )
        router = self

        class RecordModel(AgentMiddleware[Any, RunContext]):
            def record(self, request: ModelRequest[RunContext]) -> None:
                context = request.runtime.context or ctx
                for selection, model in router._models.items():
                    if request.model is model:
                        context.effective_models[agent] = selection
                        break

            def wrap_model_call(
                self,
                request: ModelRequest[RunContext],
                handler: Callable[[ModelRequest[RunContext]], ModelResponse[Any]],
            ) -> ModelResponse[Any]:
                self.record(request)
                return handler(request)

            async def awrap_model_call(
                self,
                request: ModelRequest[RunContext],
                handler: Callable[[ModelRequest[RunContext]], Awaitable[ModelResponse[Any]]],
            ) -> ModelResponse[Any]:
                self.record(request)
                return await handler(request)

        middlewares.append(RecordModel())
        return middlewares

    def list_models(self) -> list[str]:
        base = self.config.providers["cliproxy"].base_url
        if not base:
            raise ValueError("CLIProxy requires a base_url")
        url = f"{base.rstrip('/').removesuffix('/v1')}/v1/models"
        data = _get_json(url, credential("cliproxy"))
        return [str(item["id"]) for item in data["data"]]

    def accounts(self) -> dict[str, Any]:
        return self._management("credentials")

    def quotas(self, plugin_id: str) -> dict[str, Any]:
        """The documented quota API is plugin-specific, not a core account endpoint."""
        if not plugin_id or plugin_id in {".", ".."}:
            raise ValueError("A quota plugin id is required")
        return self._management(f"plugins/{quote(plugin_id, safe='')}/quota")

    def _management(self, path: str) -> dict[str, Any]:
        base = self.config.providers["cliproxy"].base_url
        if not base:
            raise ValueError("CLIProxy requires a base_url")
        url = f"{base.rstrip('/').removesuffix('/v1')}/v8/management/{path}"
        return _get_json(url, credential("cliproxy-management"))


def _get_json(url: str, key: str) -> dict[str, Any]:
    response = httpx.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    response.raise_for_status()
    return cast("dict[str, Any]", response.json())


def resolve(tier: str, config: RouterConfig | None = None) -> BaseChatModel:
    return ModelRouter(config or load_config()).resolve(tier)


def resolve_model(ctx: RunContext, config: RouterConfig | None = None) -> BaseChatModel:
    return ModelRouter(config or load_config()).resolve_model(ctx)


def router_middleware(
    ctx: RunContext, config: RouterConfig | None = None
) -> AgentMiddleware[Any, RunContext]:
    return ModelRouter(config or load_config()).router_middleware(ctx, "agent")
