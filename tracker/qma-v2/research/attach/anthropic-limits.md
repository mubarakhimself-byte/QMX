# Claude API, image and PDF limits

Sources, read with WebFetch on 2026-10-28.
- https://platform.claude.com/docs/en/build-with-claude/vision
- https://platform.claude.com/docs/en/build-with-claude/pdf-support

Images.
- Source types are base64, url and a Files API `file_id`.
- Formats are JPEG, PNG, GIF and WebP. An animation uses its first frame.
- Up to 100 images per request for models with a 200k-token window, 600 for others. Each image at most 8000x8000 px; above 20 images in one request a stricter per-image size applies (resize to 2000 px or keep to 20 image and document blocks).
- At most 10 MB per image (base64) on the Claude API; the request size limit is 32 MB on standard endpoints, and it can be reached first.
- Images over the model's native resolution are downscaled, not refused, except tool-result images for computer and browser use.

PDFs.
- Maximum request size 32 MB. Maximum 600 pages per request, 100 when the request's window is under 1M tokens. Standard PDFs only, no password or encryption.

QMX adds no cap of its own. When one of these limits refuses a turn, the plan's line names the limit and the provider.
