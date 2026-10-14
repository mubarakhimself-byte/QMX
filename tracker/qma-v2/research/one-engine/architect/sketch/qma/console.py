"""Temporary console (deleted when the UI lands, R11). `python -m qma.console`.

It uses only the HTTP routes in `qma.harness.routes` and the existing SSE stream, the same
doors the UI will use, so talking to it tests the real path. It never imports
`qma.harness` or `claude_agent_sdk`. It does import `qma.boot` and scrubs its own
environment first, because `/login` starts the bundled CLI from this process.

Commands, mirroring Claude Code where a twin exists:
    /login                 runs the bundled CLI's own login with CLAUDE_CONFIG_DIR set to QMX's
                           folder, in this terminal. QMA never sees the token.
    /login chatgpt         SIWC sign-in for QMA, then runs the GPT probe.
    /model <alias|id>      quote, show the cache warning, ask y/N, apply.
    /provider <name>       same flow for a provider switch.
    /mode <mode>           permission mode (applies at once, no warning).
    /effort <level>        quote and apply (a relaunch with resume).
    /usage  /doctor        read-only pages; /usage shows the money posture and what agent
                           Bash can reach.
    /resume  /new  /export  /rewind  /stop
    anything else starting with "/" is sent as text, so CLI built-ins such as /compact
    and /context and QMX plugin commands work as they do in Claude Code.
Ctrl+C interrupts the turn. An ask prints the tool, its input and the choices
(allow once, allow always, reject) and posts the answer.
"""

from __future__ import annotations


def main() -> None:
    raise NotImplementedError
