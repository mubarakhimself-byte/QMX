# Exact additions to qmx-control

All additive. No existing route, table or block kind changes. `qmx_control` imports `qma2`; `qma2` never imports `qmx_control`.

## server.py

```python
from qmx_control.agent_ops import build as build_harness, harness_operations, operator_routes, operator_only

OPERATIONS = ( ...existing 52 rows..., ) + harness_operations()      # one list, derived

def create_app(service, token=None, ui_origin=...):
    harness, ops, op_routes = build_harness(service, service.home)
    # existing: bind OPERATIONS rows; now `getattr(service, name)` falls back to `getattr(ops, name)`
    for method, path, handler in operator_routes(op_routes):
        app.add_api_route(path, handler, methods=[method],
                          dependencies=[Depends(authenticate), Depends(operator_only(harness))])
    # /api/apps/{app_id}/sign: the inline `sign` route is removed; op_routes.apps_sign replaces it
    # lifespan: `await harness.start()` after mcp lifespan enters; `await harness.close()` in finally
```

`_mcp_method` gets an async twin: an `async def` bound method is wrapped with `async def call(...)` so FastMCP awaits it (Gotcha 11). Both wrappers map `qma2` errors (`RouterError`, `StaleTurn`, `AlreadyAnswered`, `NotPaired`) to `ToolError` / JSON error documents with codes.

## service.py

```python
type EventTopic = Literal["runs", "jobs", "sessions", "apps", "library", "settings", "aggregates",
                          "approvals", "usage"]        # two new topics, additive
```

- qma2 emits `approvals` events (`{type:"requested"|"answered"|"expired", approval}`) and `usage` events (`{type:"recorded", row}` / `{type:"limits", snapshot}`) through a second small sink method on `ControlBlockSink`: `event(topic, subject, data)` → `ControlService._event` inside a `sessions_append`-style transaction. (Add `def emit(self, topic, subject, data)` to `ControlService`, a 6-line public wrapper over `_event`.)
- `SessionInput.origin` gains the value `"qma2"`; no type change (it is a free string).
- No new tables in control.db. Threads, segments, turns, approvals, accounts, usage, limits and the operator verifier live in `<home>/qma2/agents.db`, owned by `qma2.store.Store` (single writer thread).
- `SettingsSection` unchanged: harness settings are files under the QMX config home, served by `/api/harness/settings/{layer}`.

## Block content conventions (14 kinds, no new kind)

Every block qma2 writes carries `content.v = 1` and `content.agent_path`. Per research 32 B11:

| Event | Block kind | content keys |
|---|---|---|
| TextDone | `text` | `text`, `role` (assistant/reasoning/compaction/error), `item_id` |
| ToolStarted / ToolFinished | `tool` | `id`, `name`, `arguments`, `state` (started/completed/failed/denied), `result`, `effect` |
| files changed | `changed` | `paths`, `turn_id` |
| PlanUpdated | `plan` | `steps` |
| Subagent* | `agents` | `session_id`, `name`, `model`, `state` |
| approval parked / answered | `permission` | `approval_id`, `request`, `decision`, `by` |
| AskUser | `question` | `approval_id`, `questions`, `answer` |
| needs_input / expired approval | `needs_you` | `reason`, `approval_id` |

## CI wiring (packet 0)

- `qmx-agents/pyproject.toml`: add `packages/qma-v2` to workspace members, `[tool.uv.sources]`, the `--ignore`, ruff `extend-exclude` and pyright `exclude` lists (the package has its own strict config); runtime pins `claude-agent-sdk>=0.2.165`, `openai-agents`, `openai`, `httpx`, `argon2-cffi`, `pynacl` (sealed tier), `keyring`.
- `tools/ci.py` and `tools/test_all.py`: a `qma-v2` row with `fmt-check`, `lint`, `types`, `test`.
- `import-linter` contract in `packages/qma-v2/pyproject.toml`: forbid `qma2 → qmx_*`, `qma2 → qma`, `qma2 → langchain*`; `claude_agent_sdk` only from `qma2.engines.claude`; `agents`/`openai` only from `qma2.engines.openai`; `qma2.engines` only from `qma2.session`.
