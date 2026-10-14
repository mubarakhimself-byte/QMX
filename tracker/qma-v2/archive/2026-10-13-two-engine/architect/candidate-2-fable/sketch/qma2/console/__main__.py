"""Temporary operator console. Talks HTTP to qmx-control; holds the operator session in
memory. Deleted when the real UI is wired. This is the sign-off surface.

    python -m qma2.console set-passphrase          # first run; then `login`
    python -m qma2.console login                   # prompts; mints the operator session
    python -m qma2.console claude-signin           # runs `claude /login` with CLAUDE_CONFIG_DIR=<qma2>/claude-home
    python -m qma2.console chatgpt-signin          # PKCE flow; token → SecretStore (operator put)
    python -m qma2.console add-key openrouter      # prompts for the key; never echoed; → SecretStore
    python -m qma2.console chat [--model openai/gpt-5.6] [--cwd .]
        /model <ref>   /effort <lvl>   /mode <mode>   /compact [focus]   /stop   /steer <text>
        /approve <id> once|session|always   /deny <id>   /answer <id> <text>
        /usage   /export   /accounts   /threads   /resume <thread>
    python -m qma2.console usage
    python -m qma2.console export <thread-id> <dir>

Chat renders blocks from the sessions SSE stream (fetch-based, Bearer agent token) and
pending approvals from GET /api/approvals. It never trusts a `permission` block alone.
Secrets are typed with getpass and sent once over loopback; the console keeps nothing on disk.
"""

from __future__ import annotations


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
