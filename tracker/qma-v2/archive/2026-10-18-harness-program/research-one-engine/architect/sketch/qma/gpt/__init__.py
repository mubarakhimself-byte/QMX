"""The GPT patch: Anthropic-to-Responses format knowledge, the ChatGPT sign-in and the probe.

Not an engine and not a server. GPT chats still run the Claude Code CLI. Their base URL is
the harness relay (`qma.harness.relay`), whose GPT lane calls `translate.py`. There is one
loopback service in QMA, not two.
"""
