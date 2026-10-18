"""Temporary console (deleted when the UI lands, R11). `python -m qma.console`.

It uses only the HTTP routes in `qma.harness.routes` and the existing SSE stream, the same
doors the UI will use, so talking to it tests the real path. It never imports
`qma.harness` or `claude_agent_sdk`. It imports `qma.boot` and scrubs its own environment
first, because `/login` starts the bundled CLI from this process.

Commands, mirroring Claude Code where a twin exists:
    /login                 runs the bundled CLI's own login in this terminal, with
                           CLAUDE_CONFIG_DIR set to QMX's plan home and
                           `--settings '{"forceLoginMethod": "claudeai"}'`, so the Console
                           (API billing) choice is not offered. QMA never sees the token.
                           The bundled CLI is found with `importlib.util.find_spec`, without
                           importing the SDK; the child inherits the TTY.
    /login chatgpt         SIWC sign-in for QMA, then the GPT probe; asks for background consent.
    /model <alias|id>      quote, show the cache warning, ask y/N, apply.
    /provider <name>       same flow for a provider switch. The warning also names running
                           background tasks, which a relaunch stops.
    /mode <mode>           permission mode (applies at once, no warning).
    /effort <level>        quote and apply (a relaunch with resume).
    /usage  /doctor        read-only pages. `/doctor probe` runs the exposure probe.
    /resume  /new  /export  /rewind  /stop
    anything else starting with "/" is sent as text, so CLI built-ins such as /compact
    and /context and QMX plugin commands work as they do in Claude Code.
Ctrl+C interrupts the turn. An ask prints the tool, its input and the choices
(allow once, allow always, reject) and posts the answer.
"""

from __future__ import annotations


def main() -> None:
    raise NotImplementedError
