"""`python -m qma2.host`: one engine host process, one thread.

Started only by harness._HostSupervisor with an allow-listed env. Reads `Spawn` from
stdin, builds the adapter for the route's engine, then loops: Down messages in, Up
messages out. Imports exactly one SDK (lazily, by engine), never qmx_* and never
LangChain, so the agent-side process is small and its import graph is clean.
"""

from __future__ import annotations

from typing import Protocol

from qma2.wire import Compact, Interrupt, Reconfigure, Rotate, Spawn, Steer, Turn


class Adapter(Protocol):
    """The whole per-engine surface: six verbs. Everything else (policy, hooks, storage,
    routing, UI) lives on the control side, so the two adapters stay small and alike."""

    async def turn(self, message: Turn) -> None:
        """Run one turn to completion, emitting events and asking the link before every
        tool call. Ends with exactly one TurnEnded."""
        ...

    async def steer(self, message: Steer) -> None: ...
    async def interrupt(self, message: Interrupt) -> None: ...
    async def reconfigure(self, message: Reconfigure) -> None: ...
    async def compact(self, message: Compact) -> None: ...
    async def rotate(self, message: Rotate) -> None: ...
    async def close(self) -> None: ...


async def build_adapter(spawn: Spawn) -> Adapter:
    """# TODO pseudocode
    # match engine_of(spawn.route):
    #   CLAUDE -> from qma2.host.claude import ClaudeAdapter;  return await ClaudeAdapter.start(spawn, link)
    #   OPENAI -> from qma2.host.openai import OpenAIAdapter;  return await OpenAIAdapter.start(spawn, link)
    """
    raise NotImplementedError


def main() -> None:
    """# TODO pseudocode
    # wire_out = os.fdopen(os.dup(1), "wb"); sys.stdout = sys.stderr   # nothing else writes fd 1
    # link = Link(stdin, wire_out)
    # spawn = await link.first()            # must be Spawn
    # adapter = await build_adapter(spawn)
    # async for message in link.downs(): dispatch; turns run as tasks so Steer/Interrupt
    #                                    arrive while a turn is running
    # on Shutdown or stdin EOF: adapter.close(); send Bye; exit 0
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
