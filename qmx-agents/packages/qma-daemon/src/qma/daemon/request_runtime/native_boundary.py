"""Configuration checks for supplied-text native launches, not an OS sandbox."""

from __future__ import annotations

import asyncio
import contextlib
import os
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .providers import ProviderError


async def call_blocking(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Bound the await without stranding asyncio.run's default executor.

    Native SDK close/CLI subprocess timeouts own eventual cleanup. Cancelling
    this await cannot prove native cancellation or stop an arbitrary callback.
    """
    loop = asyncio.get_running_loop()
    result: asyncio.Future[Any] = loop.create_future()

    def deliver(value: Any, error: BaseException | None) -> None:
        if not result.done():
            if error is None:
                result.set_result(value)
            else:
                result.set_exception(error)

    def work() -> None:
        try:
            value, error = function(*args, **kwargs), None
        except BaseException as exc:
            value, error = None, exc
        with contextlib.suppress(RuntimeError):
            loop.call_soon_threadsafe(deliver, value, error)

    threading.Thread(target=work, name="qmx-native-sdk", daemon=True).start()
    return await result


def check_environment(*, provider: str) -> None:
    """Inspect variable names only. Never read credentials or silently select API auth."""
    names = {key.upper() for key in os.environ}
    blocked = {
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_API_BASE",
        "CODEX_SQLITE_HOME",
        "CODEX_AUTH_JSON",
        "CODEX_AUTH_TOKEN",
        "NODE_OPTIONS",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
        "CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR",
        "CLAUDE_CODE_SESSION_ACCESS_TOKEN",
        "CLAUDE_CODE_CUSTOM_HEADERS",
    }
    if blocked & names or any(name.startswith(("ANTHROPIC_", "AZURE_OPENAI_")) for name in names):
        raise ProviderError(
            "subscription_required", f"{provider} API routing environment is present"
        )


def check_directories(home: Path, workspace: Path, *, configuration_names: tuple[str, ...]) -> None:
    """Check metadata only; native auth/session files remain opaque to QMX."""
    if not home.is_absolute() or not workspace.is_absolute():
        raise ProviderError("unsafe_config", "Absolute dedicated native directories required")
    if not home.is_dir() or not workspace.is_dir():
        raise ProviderError("unsafe_config", "Dedicated native home and empty workspace required")
    if home.is_symlink() or workspace.is_symlink() or home.is_junction() or workspace.is_junction():
        raise ProviderError("unsafe_config", "Native directories cannot be redirected")
    actual_home, actual_workspace = home.resolve(), workspace.resolve()
    if (
        actual_home == Path.home().resolve()
        or actual_home == actual_workspace
        or actual_home in actual_workspace.parents
        or actual_workspace in actual_home.parents
        or any(workspace.iterdir())
    ):
        raise ProviderError("unsafe_config", "Distinct dedicated home and empty workspace required")
    if any((home / name).exists() for name in configuration_names):
        raise ProviderError("unsafe_config", "Dedicated home contains unreviewed configuration")


def check_claude_managed_policy() -> None:
    """Reject known local managed policy; account policy needs the human's review."""
    locations = (
        Path("C:/Program Files/ClaudeCode/managed-settings.json"),
        Path("C:/Program Files/ClaudeCode/managed-settings.d"),
    )
    if any(path.exists() for path in locations):
        raise ProviderError(
            "unsafe_config", "Claude local managed policy requires separate isolation"
        )
    if os.name == "nt":
        import winreg  # noqa: PLC0415 - Windows-only metadata inspection

        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(hive, r"SOFTWARE\Policies\ClaudeCode"):
                    raise ProviderError(
                        "unsafe_config", "Claude managed policy registry key is present"
                    )
            except FileNotFoundError:
                continue
            except PermissionError as exc:
                raise ProviderError(
                    "unsafe_config", "Claude managed policy cannot be inspected"
                ) from exc
