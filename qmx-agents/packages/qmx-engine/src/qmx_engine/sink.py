"""The `engine` hook sink (AD-53, H19): every engine chat names it in `NewChat.hook_sink`, so the
harness finds it by name for a chat reloaded after a restart. It hands each chat's hook events to
the attempt that listens on that chat now, and drops the events of a chat nobody listens on."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Final

from qma.harness import SessionId

ENGINE: Final = "engine"

type HookData = Mapping[str, object]
type Listener = Callable[[HookData], Awaitable[None]]


class EngineSink:
    def __init__(self) -> None:
        self.listeners: dict[str, Listener] = {}

    def listen(self, chat: str, listener: Listener | None) -> None:
        """Route `chat`'s hook events to `listener`; None stops them."""
        if listener is None:
            self.listeners.pop(chat, None)
        else:
            self.listeners[chat] = listener

    async def __call__(self, chat: SessionId, hook_input: HookData) -> None:
        listener = self.listeners.get(chat)
        if listener is not None:
            await listener(hook_input)
