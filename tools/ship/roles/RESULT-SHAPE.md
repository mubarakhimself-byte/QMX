# Result shape of a headless run

Recorded by `ship spike` on 2026-11-14 with `claude 2.1.322 (Claude Code)`, `-p ... --output-format json`.
`launch.parse_result` follows this file. Stdout is one JSON object on one line.

## A normal ending

| Field | Type |
|---|---|
| `api_error_status` | NoneType |
| `credential_expires_at` | str |
| `duration_api_ms` | int |
| `duration_ms` | int |
| `fast_mode_disabled_reason` | str |
| `fast_mode_state` | str |
| `first_content_frame_ms` | int |
| `is_error` | bool |
| `modelUsage` | dict |
| `num_turns` | int |
| `permission_denials` | list |
| `queued_turn_count` | int |
| `result` | str |
| `result_index` | int |
| `safety_stops` | int |
| `session_id` | str |
| `stop_reason` | str |
| `subagent_stats` | dict |
| `subtype` | str |
| `terminal_reason` | str |
| `time_to_request_ms` | int |
| `total_cost_usd` | float |
| `ttft_ms` | int |
| `ttft_stream_ms` | int |
| `type` | str |
| `usage` | dict |
| `uuid` | str |

Used by the kit:

- `result`: the final text. Its last non-blank line is the reply contract (`READY`, `BLOCKED`, `DONE`, `WAITS`).
- `session_id`: equals the `--session-id` passed.
- `modelUsage`: one key per model that ran, the full id (`claude-haiku-5-5` for `--model haiku`). Fields of one
  entry: `inputTokens`, `outputTokens`, `cacheReadInputTokens`, `cacheCreationInputTokens`, `webSearchRequests`, `costUSD`, `contextWindow`, `maxOutputTokens`, `thinkingTokens`, `cacheCreationEphemeral5mInputTokens`, `cacheCreationEphemeral1hInputTokens`, `canonicalModel`, `provider`, `costBasis`. A run may list a second, smaller model for housekeeping, so a
  fallback is read as "the asked model is absent and the fallback model is present".
- `permission_denials`: one object per refused tool call, fields `tool_name`, `tool_use_id`, `tool_input`.
- `is_error`, `subtype` (`success` on a normal end), `api_error_status` (null on a normal end).

## A usage-limit ending

None was seen during the spike. Until one is recorded here, `launch.parse_result` calls a run a limit when its
text (or stderr, or `api_error_status`) holds one of the `limit_patterns` settings and it has no contract line,
and reads the reset time from a `|<epoch seconds>` suffix (the CLI's `Claude AI usage limit reached|<epoch>`
form), else from an ISO time in the text, else now plus `limit_backoff_s`. Record the real shape here the first
time a worker ends on a limit (its `workers/<id>/stdout.log`).
