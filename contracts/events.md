# Event streams

The host pushes changes over Server-Sent Events at `GET /api/events/{topic}`, behind the same bearer
as every route. A browser's `EventSource` cannot send that header, so a page reads the stream with
`fetch()`. This file is written by hand from the code at `engine/base` `bef6e8084`. The route and its
query parameters are also in `host-openapi.json` (operation `stream_events_api_events__topic__get`).

## The stream

- **Query:** `after` (an event id; the stream starts after it), `subject` (only events about one
  subject; empty means all), `max_events` (stop after this many, 0 to 1000; 0 means never stop).
  The `Last-Event-ID` header does the same as `after`; the larger of the two wins.
- **Each event:** `event:` is the topic, `id:` is the event's sequence number (one counter across
  all topics), `data:` is a JSON object, the topic's payload below.
- **Where it comes from:** `ControlService._event` in
  `qmx-agents/packages/qmx-control/src/qmx_control/service.py` writes a row to the `events` table of
  `control.db`; `ControlService.stream` polls that table every 50 ms.
- **What is kept:** rows of `apps` and `aggregates` carry `recorded_at` (UTC, ISO 8601) and are
  removed after `[apps] events_keep_days`. The other topics are records and stay.

## Topics

| Topic | Subject | Payload fields | Written by |
|---|---|---|---|
| `runs` | run id | `id`, `kind`, `target`, `node`, `model` (agent name to model), `status`, `cost`, `started`, `ended`, `artifacts`, `journal`, and from the run's start record any of `app_id`, `workflow_id`, `session_id` | `ControlService._refresh_runs`, when it projects a changed run journal (`runs.py` `RunIndex.refresh`). It runs on `GET /api/aggregates`, so a run event appears only when something reads the totals |
| `jobs` | - | - | Declared in `EventTopic`, never written. Nothing reaches a screen on this topic |
| `sessions` | session id | `type` is `created` with `session`, `block` with `block` (the block and its `seq`), or `delegate_completion` with `handle` and `state` | `sessions_create`, `sessions_append`, `delegate_completion_save` |
| `apps` | app id | The supervisor's instance document (`app_id`, `instance_id`, `definition_hash`, `version`, `profile`, `data`, `status`, `pid`, `node`, `tier`, `breaker`, `metrics`, `heartbeat_age_seconds`, `limits`) on every state change; `{app_id, status: "installed", definition_hash}` on install; `type: "road_step"` and `type: "published"` records from the publish road; `type: "log"` with `event` from the Docker runner. Plus `recorded_at` | `qmx_apps` `Supervisor.emit` through `ControlService._app_event`; `ControlService.notify_app` (no caller at `bef6e8084`) |
| `library` | item id | `type` is `saved` (`item_id`, and `memo_key` for a memoized save), `linked` (the link's fields), `branched` (`ref`), `resolved`, or a merge's outcome (`into`, `from_ref`) | `library_save`, `library_publish_card` (its memoized card), `library_link`, `library_branch`, `library_merge`, `library_resolve` |
| `settings` | section name | `section` | `settings_put` and `settings_update` (through `_settings_put`), after the section's file is written |
| `aggregates` | empty | `library_items`, `runs`, `active_jobs`, `recorded_at` | `ControlService._push_totals`, after a runs, apps or library event, and only when a total changed |

## Other streams

These are routes of their own, listed in `host-openapi.json`; each is Server-Sent Events behind the
bearer.

- `GET /api/engine/events?run_id=...`: one engine run's events; `event:` is the event's `kind`, `id:`
  its `seq`.
- `GET /api/sessions/{sid}/live`: a chat turn as it streams.
- `GET /api/engine/forward/stream`: the node's forwarding stream (a host pass, not the UI's bearer).
- `GET /api/sessions/{session_id}/events`: a page of the `sessions` topic for one session, as JSON
  (not a stream).
