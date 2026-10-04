"""Host-only native SDK composition, separate from generic API inference config."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Literal

from .native_claude import ClaudeSessionBackend
from .native_codex import CodexSessionBackend
from .native_sessions import NativeSessionProvider, SessionBackend
from .service import RequestRuntime
from .tool_loop import ToolBinding


def compose_native_metadata_provider(
    runtime: RequestRuntime,
    *,
    provider_id: str,
    backend: Literal["codex", "claude"],
    executable: Path,
    dedicated_home: Path,
    empty_workspace: Path,
    now: Callable[[], str],
    metadata_binding: ToolBinding,
    profile_tools: Mapping[str, frozenset[str]],
    native_policy_reviewed: bool = False,
) -> NativeSessionProvider:
    """Expose one retained-corpus metadata operation with its original host grant.

    No model-provided paths/grants, native filesystem tools, API keys, or worker
    provisioning. The host must resolve current target/instance/grant before
    composing this provider. Dispatch independently validates them each call.
    """
    if (
        metadata_binding.descriptor.op_id != "qml.research.browse"
        or metadata_binding.descriptor.version != 1
        or metadata_binding.descriptor.effect_class != "read"
    ):
        raise ValueError("Native supplied-text composition supports corpus metadata reads only")
    if any(names - {"research_browse"} for names in profile_tools.values()):
        raise ValueError("Native profile contains an unsupported operation")
    scope = dict(metadata_binding.argument_scope)
    snapshot, locators = scope.get("snapshot_ref"), scope.get("locator")
    if not isinstance(snapshot, str) or not isinstance(locators, tuple) or not locators:
        raise ValueError("Explicit retained snapshot and locator scope required")
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "snapshot_ref": {"type": "string", "enum": [snapshot]},
            "locator": {"type": "string", "enum": list(locators)},
        },
        "required": ["snapshot_ref"],
        "additionalProperties": False,
    }

    def factory() -> SessionBackend:
        if backend == "codex":
            return CodexSessionBackend(
                executable=executable,
                dedicated_home=dedicated_home,
                empty_workspace=empty_workspace,
                tool_schemas={"research_browse": schema},
            )
        if backend == "claude":
            return ClaudeSessionBackend(
                executable=executable,
                dedicated_home=dedicated_home,
                empty_workspace=empty_workspace,
                native_policy_reviewed=native_policy_reviewed,
                tool_schemas={"research_browse": schema},
            )
        raise ValueError("Unknown native backend")

    provider = NativeSessionProvider(
        factory,
        provider_id=provider_id,
        now=now,
        tools={"research_browse": metadata_binding},
        profile_tools=profile_tools,
        max_tool_calls=1,
    )
    provider.bind_runtime(runtime)
    return provider
