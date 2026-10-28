# Claude Agent SDK, user message input

Sources, read through the context7 tool on 2026-10-28.
- https://code.claude.com/docs/en/agent-sdk/streaming-vs-single-mode
- https://code.claude.com/docs/en/agent-sdk/python

What they say.
- Streaming input mode is the recommended mode, and its listed benefits include attaching images directly to messages.
- `ClaudeSDKClient.query()` takes a string or an async iterable of user message dicts. A message dict is `{"type": "user", "message": {"role": "user", "content": [...]}}`, and its content may hold `{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": ...}}` beside text blocks.
- Claude Code starts answering the first yielded message at once, so everything Claude should read before answering goes into one message, and each `query()` call pairs with its own `receive_response()`.
- The pages show image blocks only. They name no `document` block for a user message, so a PDF block through the CLI is unproven (ATTACH-PLAN Appendix A, probe P-DOC in AT5).
- Custom tool results may return images as base64 with `mimeType`; PNG, JPEG, GIF and WebP reach Claude as visual input, other types as a file path.

The locked SDK is `claude-agent-sdk` 0.2.166 (`qmx-agents/uv.lock:528-529`). Its `ClaudeSDKClient.query(self, prompt: str | AsyncIterable[dict[str, Any]], session_id="default")` writes a string as one user message and streams an iterable as given (`claude_agent_sdk/client.py:272-302` in the agents venv). `verbatim_prompts` stamps every user message it sends (`claude_agent_sdk/types.py:2574-2579`).
