# OpenRouter, the Anthropic-compatible door and PDFs

Sources, read on 2026-10-28.
- https://openrouter.ai/docs/api/api-reference/anthropic-messages/create-a-message (WebFetch, first 100,000 characters)
- https://openrouter.ai/docs/guides/overview/multimodal/pdfs (WebFetch)
- https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration (search excerpt): Claude Code reaches OpenRouter with base URL `https://openrouter.ai/api`, the door QMX's `openrouter.toml` uses.

What they say.
- `POST https://openrouter.ai/api/v1/messages` takes user content blocks of type `text`, `image` and `document`, and `tool_result` content that may hold images and documents. The part read states no size limit for them.
- PDFs on OpenRouter's own API are parsed by an engine. `native` for models that take files, billed as input tokens; `mistral-ocr` at 2 USD per 1,000 pages (2.2 USD in the US data region), the default when a model has no native file input; `cloudflare-ai`, free, to markdown. `pdf-text` is deprecated and goes to `cloudflare-ai`.
- The PDF page states no file size or page limit.

What stays unproven. Whether the Anthropic-compatible door applies the same engines to a `document` block for a model with no file input. The plan does not rely on it. A row whose `pdf` is false gets the PDF's text from QMX instead (ATTACH-PLAN AT5), which also avoids a paid OCR engine running without his choice.
