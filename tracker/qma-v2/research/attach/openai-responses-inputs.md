# OpenAI Responses API, image and file inputs

Sources, read with WebFetch on 2026-10-28.
- https://developers.openai.com/api/docs/guides/pdf-files (redirected from platform.openai.com/docs/guides/pdf-files)
- https://developers.openai.com/api/docs/guides/images-vision

Files.
- `input_file` with base64 `file_data`, an uploaded `file_id` (purpose `user_data`) or a `file_url`. Chat Completions accepts only PDFs.
- Each file under 50 MB; all files in one request together 50 MB. No page limit is stated.
- Accepted types include PDF, spreadsheets, Word and rich documents, presentations, and text and code files.

Images.
- `input_image` takes a URL, a base64 data URL or a file id. PNG, JPEG, WebP and non-animated GIF.
- Up to 512 MB total payload and 1,500 images per request; up to 30,000 patches per image after resizing, and an image over that is refused, not resized.

QMX's GPT lane maps an Anthropic `image` block to `input_image` and a base64 PDF `document` to `input_file` (`qmx_router/gpt/translate.py:167-169,212-222`). These pages describe the API; the ChatGPT sign-in route may refuse a capability with `subscription_sharing_unsupported_capability`, which the lane names with its param (`translate.py:455,469-470`).
