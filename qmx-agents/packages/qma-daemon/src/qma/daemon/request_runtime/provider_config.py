"""Operator-owned SDK configuration; renderer input never creates providers."""

from __future__ import annotations

import hashlib
import json
import math
import re
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, cast

from qma.core.barriers.reachability import is_forbidden_model_adapter
from qmf.core import Ok, Result
from qmf.data.store.refusals import invalid_input

from .agent_extensions import AgentExtensions, load_agent_extensions
from .contracts import (
    CopilotProfile,
    ProviderAdapter,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
)
from .daemon_bridge import AgentRequestPolicy
from .http_provider import ChatCompletionsProvider
from .native_configuration import NativeProviderConfiguration
from .providers import CodexAppServerProvider


@dataclass(frozen=True, slots=True)
class AgentRequestConfiguration:
    providers: Mapping[str, ProviderAdapter]
    policies: Mapping[str, AgentRequestPolicy]
    profile_tools: Mapping[str, frozenset[str]]
    research_browse: Mapping[str, object]
    instance_revisions: Mapping[str, int]
    research_workflow: Mapping[str, object]
    max_workers: int = 2
    max_inflight: int = 16
    shutdown_timeout_seconds: float = 2
    agent_extensions: AgentExtensions | None = None


class _ConfiguredProvider:
    """Bind accepted requests to nonsecret host configuration, not mutable aliases."""

    def __init__(self, provider: ProviderAdapter, identity: str) -> None:
        self.provider = provider
        self.identity = identity

    @property
    def capabilities(self) -> ProviderCapabilities:
        return replace(self.provider.capabilities, provider_id=self.identity)

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        return self.provider.execute(request, emit, cancellation)


def _mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("configuration requires string-keyed objects")
    raw = cast("dict[object, object]", value)
    if any(not isinstance(key, str) for key in raw):
        raise ValueError("configuration requires string-keyed objects")
    return cast("dict[str, Any]", value)


def _sequence(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("configuration requires arrays")
    return cast("list[object]", value)


def _keys(row: Mapping[str, object], permitted: set[str]) -> None:
    if set(row) - permitted:
        raise ValueError("unsupported configuration fields")


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 32768:
        raise ValueError("nonempty bounded configuration text required")
    return value


def _integer(value: object, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 < value <= maximum:
        raise ValueError("configuration integer is outside the supported range")
    return value


def _duration(value: object, maximum: int) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or not 0 < value <= maximum
    ):
        raise ValueError("configuration duration is outside the supported range")
    return float(value)


def _duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate configuration fields")
        result[key] = value
    return result


def _provider(alias: str, row: dict[str, Any], manifest: Mapping[str, object]) -> ProviderAdapter:
    if is_forbidden_model_adapter(alias):
        raise ValueError("Configured adapter violates host reachability")
    protocol = row.get("protocol")
    digest = hashlib.sha256(
        json.dumps({"provider": row, "host_tools": dict(manifest)}, sort_keys=True).encode()
    ).hexdigest()[:24]
    if protocol == "native-session":
        _keys(
            row,
            {
                "protocol",
                "backend",
                "executable",
                "dedicated_home",
                "empty_workspace",
                "native_policy_reviewed",
            },
        )
        backend = row.get("backend")
        if backend not in {"codex", "claude"}:
            raise ValueError("explicit supported native backend required")
        reviewed = row.get("native_policy_reviewed", False)
        if not isinstance(reviewed, bool) or (backend == "claude" and reviewed is not True):
            raise ValueError("Claude requires reviewed personal unmanaged native policy")
        if backend == "codex" and "native_policy_reviewed" in row:
            raise ValueError("native_policy_reviewed applies only to Claude")
        executable, home, workspace = (
            Path(_text(row.get(key))) for key in ("executable", "dedicated_home", "empty_workspace")
        )
        if not all(path.is_absolute() for path in (executable, home, workspace)):
            raise ValueError("absolute native paths required")
        if home == workspace or home in workspace.parents or workspace in home.parents:
            raise ValueError("distinct dedicated native directories required")
        return NativeProviderConfiguration(
            f"configured:{alias}:{digest}",
            cast("Literal['codex', 'claude']", backend),
            executable,
            home,
            workspace,
            reviewed,
        )
    if protocol == "chat-completions":
        _keys(row, {"protocol", "endpoint", "model", "deployment_id", "api_key_env", "stream"})
        key_env = row.get("api_key_env")
        if key_env is not None and (
            not isinstance(key_env, str) or re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", key_env) is None
        ):
            raise ValueError("api_key_env must be a named environment reference")
        stream = row.get("stream", False)
        if not isinstance(stream, bool):
            raise ValueError("stream must be boolean")
        provider: ProviderAdapter = ChatCompletionsProvider(
            _text(row.get("endpoint")),
            _text(row.get("model")),
            deployment_id=_text(row.get("deployment_id")),
            api_key_env=key_env,
            stream=stream,
        )
    elif protocol == "codex-app-server":
        _keys(row, {"protocol", "executable", "dedicated_home"})
        provider = CodexAppServerProvider(
            Path(_text(row.get("executable"))), Path(_text(row.get("dedicated_home")))
        )
    else:
        raise ValueError("unsupported provider protocol")
    return _ConfiguredProvider(provider, f"configured:{alias}:{digest}")


def _policy(
    row: dict[str, Any], providers: Mapping[str, ProviderAdapter], profile_id: str
) -> AgentRequestPolicy:
    _keys(
        row,
        {
            "role",
            "instructions",
            "authority_profile",
            "app_instance_id",
            "page_id",
            "session_app_instance_id",
            "provider_id",
            "model",
            "timeout_seconds",
            "max_prompt_bytes",
            "tools",
            "authoring_task_id",
        },
    )
    role = row.get("role")
    if role not in {"global", "application", "page"}:
        raise ValueError("unsupported Copilot role")
    authority = row.get("authority_profile")
    if authority not in {"authoring", "app-use"}:
        raise ValueError("explicit authority_profile required")
    instructions = row.get("instructions", "")
    if not isinstance(instructions, str) or len(instructions.encode()) > 32768:
        raise ValueError("bounded host instructions required")
    scope: dict[str, str | None] = {}
    for field in ("app_instance_id", "page_id", "session_app_instance_id"):
        scope[field] = _text(row[field]) if field in row else None
    profile = CopilotProfile(
        profile_id,
        role,
        instructions,
        scope["app_instance_id"],
        scope["page_id"],
    )
    session_app = scope["session_app_instance_id"]
    if authority == "app-use" and role == "global" and not session_app:
        raise ValueError("global app-use policy requires an explicit session app binding")
    if profile.app_instance_id and session_app not in {None, profile.app_instance_id}:
        raise ValueError("conflicting host app bindings")
    alias = _text(row.get("provider_id"))
    if alias not in providers:
        raise ValueError("profile provider is not configured")
    if isinstance(providers[alias], NativeProviderConfiguration):
        if row.get("tools") != ["research_browse"]:
            raise ValueError("native supplied-text profiles require the exact metadata callback")
    elif row.get("tools") and providers[alias].capabilities.execution_kind == "agent_session":
        raise ValueError("native agent-session profiles cannot use the inference tool graph")
    model = _text(row["model"]) if "model" in row else None
    return AgentRequestPolicy(
        profile=profile,
        authority_profile=authority,
        provider_id=providers[alias].capabilities.provider_id,
        model=model,
        timeout_seconds=_duration(row.get("timeout_seconds", 120), 600),
        max_prompt_bytes=_integer(row.get("max_prompt_bytes", 32768), 262144),
        session_app_instance_id=session_app,
        authoring_task_id=_text(row["authoring_task_id"]) if "authoring_task_id" in row else None,
    )


def load_agent_request_config(root: Path | str) -> Result[AgentRequestConfiguration | None]:
    """Read optional operator-config.json agent_sdk; construct adapters without I/O."""
    path = Path(root) / "operator-config.json"
    if not path.is_file():
        return Ok(None)
    try:
        with path.open(encoding="utf-8") as source:
            content = source.read(1_048_577)
        if len(content.encode()) > 1_048_576:
            raise ValueError("operator configuration exceeds size limit")
        config = _mapping(json.loads(content, object_pairs_hook=_duplicates))
        if "agent_sdk" not in config:
            return Ok(None)
        sdk = _mapping(config["agent_sdk"])
        _keys(
            sdk,
            {
                "enabled",
                "providers",
                "profiles",
                "research_browse",
                "research_workflow",
                "instance_revisions",
                "max_workers",
                "max_inflight",
                "shutdown_timeout_seconds",
                "agent_extensions",
            },
        )
        if not isinstance(sdk.get("enabled"), bool):
            raise ValueError("explicit enabled boolean required")
        if not sdk["enabled"]:
            return Ok(None)
        raw_providers = _mapping(sdk.get("providers"))
        raw_profiles = _mapping(sdk.get("profiles"))
        if not 0 < len(raw_providers) <= 16 or not 0 < len(raw_profiles) <= 32:
            raise ValueError("bounded nonempty provider and profile maps required")
        extensions = (
            load_agent_extensions(Path(root), sdk["agent_extensions"])
            if "agent_extensions" in sdk
            else None
        )
        manifest = {
            "runtime_revision": "langchain-agent-1",
            "research_browse": sdk.get("research_browse", {}),
            "research_workflow": sdk.get("research_workflow", {}),
            "instance_revisions": sdk.get("instance_revisions", {}),
            "profile_tools": {
                key: _mapping(row).get("tools", []) for key, row in raw_profiles.items()
            },
        }
        if extensions is not None:
            manifest["agent_extensions"] = extensions.manifest()
        aliases = {
            _text(alias): _provider(alias, _mapping(row), manifest)
            for alias, row in raw_providers.items()
        }
        policies = {
            _text(key): _policy(_mapping(row), aliases, key) for key, row in raw_profiles.items()
        }
        if extensions is not None:
            for association in extensions.profiles:
                if association.profile_id not in policies:
                    raise ValueError("extension profile is not configured")
                alias = _text(_mapping(raw_profiles[association.profile_id]).get("provider_id"))
                if aliases[alias].capabilities.execution_kind != "inference":
                    raise ValueError("generic extensions require an inference profile")
        tools: dict[str, frozenset[str]] = {}
        for profile_id, raw in raw_profiles.items():
            values = _sequence(_mapping(raw).get("tools", []))
            if any(value != "research_browse" for value in values):
                raise ValueError("only the installed scoped research_browse tool is supported")
            tools[profile_id] = frozenset(_text(value) for value in values)
        browse = _mapping(sdk.get("research_browse", {}))
        workflow = _mapping(sdk.get("research_workflow", {}))
        _keys(workflow, {"specialist_id", "version", "instructions", "profiles"})
        if workflow:
            for name in ("specialist_id", "version", "instructions"):
                _text(workflow.get(name))
            selected = (
                _sequence(workflow["profiles"])
                if "profiles" in workflow
                else [name for name, names in tools.items() if names]
            )
            if selected:
                if not 0 < len(selected) <= 64:
                    raise ValueError("bounded workflow profile selection required")
                for profile in selected:
                    name = _text(profile)
                    if name not in policies:
                        raise ValueError("workflow profile is not configured")
                    provider = aliases[_text(_mapping(raw_profiles[name]).get("provider_id"))]
                    if provider.capabilities.execution_kind != "inference":
                        raise ValueError("research workflow requires inference profiles")
            if not any(tools.values()):
                raise ValueError("research workflow requires scoped research_browse profiles")
        _keys(browse, {"source_id", "snapshot_ref", "allowed_locators"})
        if any(tools.values()):
            _text(browse.get("source_id"))
            _text(browse.get("snapshot_ref"))
            locators = _sequence(browse.get("allowed_locators"))
            if not 0 < len(locators) <= 64:
                raise ValueError("explicit bounded research locators required")
            for locator in locators:
                _text(locator)
        revisions: dict[str, int] = {}
        for instance, revision in _mapping(sdk.get("instance_revisions", {})).items():
            if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
                raise ValueError("explicit nonnegative instance revisions required")
            revisions[_text(instance)] = revision
        for profile_id, names in tools.items():
            policy = policies[profile_id]
            instance = policy.profile.app_instance_id or policy.session_app_instance_id
            if names and instance not in revisions:
                raise ValueError(
                    "domain tool policy requires a configured current instance revision"
                )
        workers = _integer(sdk.get("max_workers", 2), 8)
        inflight = _integer(sdk.get("max_inflight", 16), 64)
        if inflight < workers:
            raise ValueError("inflight capacity must cover the configured workers")
        return Ok(
            AgentRequestConfiguration(
                providers=MappingProxyType(
                    {item.capabilities.provider_id: item for item in aliases.values()}
                ),
                policies=MappingProxyType(policies),
                profile_tools=MappingProxyType(tools),
                research_browse=MappingProxyType(browse),
                instance_revisions=MappingProxyType(revisions),
                research_workflow=MappingProxyType(workflow),
                max_workers=workers,
                max_inflight=inflight,
                shutdown_timeout_seconds=_duration(sdk.get("shutdown_timeout_seconds", 2), 10),
                agent_extensions=extensions,
            )
        )
    except OSError, UnicodeError, ValueError, TypeError, KeyError:
        return invalid_input(
            "agent_sdk", "operator SDK configuration is invalid; no provider was started"
        )
