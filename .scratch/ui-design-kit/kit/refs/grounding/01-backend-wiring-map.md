# 01 Backend wiring map (engine/base @ 3ae41ffc, 2026-11-08)

Read-only grounding. Code: `D:/QMX-worktrees/engine-base-read`. Paths below are relative to
`qmx-agents/packages/` unless they start with `apps/` or `tracker/`.
Abbreviations: **CS** = `qmx-control/src/qmx_control/service.py`, **SRV** = `qmx-control/src/qmx_control/server.py`,
**HR** = `qma-harness/src/qma/harness/routes.py`, **HOST** = `qmx-host/src/qmx_host/`.

How the route list was built: every `@operation(..., rest=(verb, path))` on `ControlService`
(CS, 66 rows, turned into routes by `rest_routes`, `qmx-control/src/qmx_control/catalog.py:1023`
and SRV:445-452), plus every FastAPI router the host composes (`HOST/host.py:1169-1455`,
`compose` at `HOST/host.py:2831`). Catalog rows without `rest=` (broker, backtest, unit, blocks,
node, readings, journal, memory, context, router, lab, primary) have **no HTTP route**: they
are model tools only (MCP/in-process), never reachable by the UI bearer.

---

## 1. The door

| Item | What the code says | Cite |
|---|---|---|
| Process | One program: `python -m qmx_host serve --home <folder> --port <p> --role pc --ui-origin <origin>`. Chats, workflows, Library, apps, data, backups, connect dialog all on one port. | `HOST/__main__.py:1-2`, `HOST/host.py:1169` |
| Port | Default `8766`; UI origin default `http://127.0.0.1:5173`. | `HOST/__main__.py:99,105` |
| Before a folder exists | Separate card app `first-start --serve` on the same port, loopback, **no bearer**, CORS GET/POST/PUT from the UI origin. Hands over with `POST /api/first-start/handover` -> `{folder, port}`; the desktop shell then starts `serve`. | `HOST/first_start.py:1729-1742,1879-1900` |
| Transport | REST (JSON) + SSE (`text/event-stream` via FastAPI `EventSourceResponse`). No WebSocket anywhere. MCP over HTTP at `/mcp` exists but is for agents (principal `agent:mcp`), and carries only ControlService rows. | SRV:454-469, SRV:367-378, SRV:487, `HOST/door.py:60` |
| Auth | One bearer on every host route: `Authorization: Bearer <token>`. Token = keyring entry `qmx/control-token` (Windows Credential Manager), created by the host on first `serve`. The UI cannot fetch it from the host; the desktop shell must read the keyring and inject it. On headless Linux it is `<QMX>/keys/control-token`. | SRV:55-74, SRV:336-363, `HOST/host.py:1193` |
| Principal | `PrincipalDoor` (outermost middleware) names the caller: UI bearer = `user`/operator; chat routes = `agent:<sid>`; observer tokens restamped and limited to `ops` reads; run passes only on `POST /api/data/read`; host passes only on forward/venue/host routes. Operator-only routes (`/api/units/promote`, collection publish, seal move) check this. | `HOST/door.py:1-50,243`, `HOST/host.py:2860-2867` |
| CORS | Exactly one origin (`--ui-origin`), methods **GET, POST, PUT only**, headers Authorization, Content-Type, Last-Event-ID, Mcp-*. A desktop shell whose page origin differs must pass it as `--ui-origin`. `DELETE /api/library/upload/{id}` exists but is blocked cross-origin. | SRV:488-504, SRV:323 |
| SSE auth caveat | Every stream needs the bearer header; browser `EventSource` cannot send headers and there is no query-token path, so the UI must stream with `fetch()` (or the shell proxies). | SRV:356-363 |
| Health / readiness | `GET /api/health` -> `{status:"ok", pid, read_only:[{store,line}]}` (bearer). Card up = `GET /api/first-start` 200 without bearer. | SRV:471-477 |
| Error shapes (verified) | Control rows: `{"error":{code,message}}` (SRV:431-436). Card, backups, templates, connect, keys: `{"detail":"<line>"}`. Price door shut: 503 `{detail:{refused,retryability,context,line}}` (`HOST/host.py:2685-2696`). Promote: `{ok:false,code,message,next_step}` (`HOST/promote.py:707-716`). Body errors: FastAPI 422. |  |

### Streams that exist

| Stream | Path | Event shape | Cite |
|---|---|---|---|
| Control topics | `GET /api/events/{topic}?after=&subject=&max_events=` (+`Last-Event-ID`) | `event: <topic>`, `id: <seq>`, `data: <json>`. Topics: `runs, jobs, sessions, apps, library, settings, aggregates`. | SRV:454-469, CS:87 |
| Chat durable blocks | `GET /api/events/sessions?subject=<sid>` | `{type:"block", block:{seq, type, content}}`, also `{type:"created"}`, `{type:"delegate_completion", handle, state}` | CS:1395-1432, CS:1460-1474 |
| Chat live deltas | `GET /api/sessions/{sid}/live` | `event: delta`, `data:{kind: text|thinking|tool_progress, text, tool_use_id}`; never stored | HR:356-363, `qma-harness/src/qma/harness/project.py:91,188-193` |
| Workflow run ledger | `GET /api/engine/events?run_id=<id>` | `event: <kind>`, `id: <seq>`, data = ledger event. Kinds: run_created, run_input, clock_tick, node_scheduled, node_started, heartbeat, log, node_finished, node_failed, node_waiting, gate_opened, gate_resolved, event_received, ladder_step, doctor_verdict, run_paused, run_resumed, run_finished, run_cancelled, compacted, memory_written, tool_called, zone_committed | `qmx-engine/src/qmx_engine/service/rest.py:38-46`, `qmx-engine/src/qmx_engine/ledger/events.py:17-41` |

Topics actually written: `apps`, `library`, `runs`, `sessions`, `settings`, `aggregates` (CS:1011). **`jobs` is declared but nothing writes it**, and `runs` is only refreshed when someone calls `GET /api/aggregates` (CS:1851,1861-1867). Host jobs (backup, connect, template install, first-start) are poll-only.

Session block types (backend vocabulary, CS:158-176): `user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you`. The §1 renames (`tool`, `changed`, `entity`, `question`, `needs_you`) are in the backend.

---

## 2. Per-screen map

Legend: E = exists, P = partial, M = missing.

### Home
| Need | Route / stream | Payload (one line) | State |
|---|---|---|---|
| Totals tiles | `GET /api/aggregates` (CS:1848); push via `/api/events/aggregates` | `{revision, library_items, runs, active_jobs}` | E |
| Needs you | `GET /api/inbox` (CS:2380) | observer notes + open incidents + open workflow inbox items (`severity normal|urgent|black`) | E (poll only, no inbox topic) |
| Act on an item | `POST /api/inbox/{item_id}/resolve` `{action}` (`qmx-engine/.../service/rest.py:34`) | action `retry|stronger_model|skip_node|open_trace|stop|resume` | E for workflow items; incident resolve not verified |
| Going on (runs) | `GET /api/workflow-runs` (CS:2213) | list, newest first, no `placement` on list rows | P (poll) |
| Proposals | `GET /api/portfolio/proposals` (CS:1376) | unsigned broker proposals | P (unit-promotion proposal cards are Library items; no dedicated list) |
| Nodes strip / heartbeats | only `ops_heartbeats` tool (`qmx-control/.../catalog.py` HOST_ROWS) and host-pass verb `heartbeats` (`HOST/host_route.py:66`) | — | M for the UI bearer; per-node status reachable via `POST /api/apps/trading-node/tools/status` |
| Getting-started panel | — | — | M (no facts-computed state; UI-NOTES-UNITS §19 row 1 still true) |
| Doctor lines | `GET /api/doctor` (HR:411) | `{lines:[{name, ok, detail}]}` incl. backups, vault, library, clock | E |

### Copilot (chats)
| Need | Route / stream | Payload | State |
|---|---|---|---|
| New chat | `POST /api/chats` (HR:267) | body `{title, model, effort, mode, workspace, profile}` -> `{session_id}`; `extra=forbid` | E |
| Chat list / one chat | `GET /api/chats`, `GET /api/chats/{sid}` (HR:283,287) | `{session_id,title,workspace,started,turn: idle|running, profile,model,effort,mode}` (+`tokens`) | E |
| Send turn / stop | `POST /api/sessions/{sid}/turns` `{text}` 202; `POST .../interrupt` 202 (HR:296,306) | `{status}`; 409 `launch_refused`/`chat_table_full` | E |
| Transcript | `GET /api/sessions/{sid}/events?after=&limit=` page (CS:1436-1449) + SSE topic `sessions` | blocks as above | E |
| Live tokens | `GET /api/sessions/{sid}/live` | delta | E |
| Approvals / questions | `POST /api/approvals/{sid}.{seq}` (HR:365) | decisions allow_once / allow_always / reject / answers -> `{status}` | E |
| Model/effort/mode switch with cost | `POST .../quote` then `POST .../apply {quote_id}` (HR:311,324) | quote doc; 409 `quote_stale` | E |
| Rewind, export | `GET/POST .../rewind`, `POST .../export` (HR:333-354) | points; `{folder, files}` | E |
| Session home badge (`home:{kind,project_id}`) | stored on the chat record (`qma-harness/.../home.py:743,794`) but **not accepted** by `NewChatIn` (HR:134-141) and **not returned** by `chat_entry` (HR:229-237) | — | M at REST (§1 row 2 claim "sent in POST /api/chats body" is not true at 3ae41ffc) |
| Attach from Library on click | only model tool `context_add` (catalog CONTEXT_ROWS) | — | M (§18 row 1 still open) |
| @file/@folder/@url/@youtube | refused "arrives with REF2" (`qmx-control/.../context.py:50-62`) | — | M |
| Rename / delete / archive chat, compact now, steer | — | — | M |
| Helpers (sub-agents) | `delegate_completion` events on sessions topic; `delegate_list` is a model tool only | `{handle, state}` | P |
| Model picker list, provider Test | `GET /api/settings/providers`, `GET /api/settings/roles`, `GET /api/settings/agents/model-card` (CS:1100,1581); `ops_providers`/`ops_provider_test` are model tools only | settings docs | P (no REST "Test" button) |

### Library
| Need | Route | Payload | State |
|---|---|---|---|
| Browse / search | `GET /api/library?query=&offset=&limit=` (CS:1531) | FTS over title/tags/text; blank = all placements | P: no kind/shelf/draft/status filter |
| Item, versions, history, blame, links | `GET /api/library/{id}`, `/versions`, `/history`, `/blame`, `/links`; `POST /api/library/links` (CS:1536,1640-1806) | item with verified blob | E |
| Save, branch, merge (=publish a draft), conflicts, resolve | `POST /api/library`, `.../branch`, `.../merge`, `GET /api/library/conflicts`, `.../resolve` (CS:1516,1691-1759) | | E |
| Publish card | `GET /api/library/{id}/publish-card` (CS:1598) | what publishing would do | E |
| Publish a collection in one click | `POST /api/library/collections/{collection_id}/publish` operator-only (`HOST/publish_collection.py:27,74`) | per-member result | E |
| Upload a file | `POST /api/library/upload`, `GET/DELETE .../{upload_id}` (SRV:241-323) | resumable chunks | P (DELETE blocked by CORS) |
| Archive / quarantine from the screen | `library_mark` is a model tool (HOST/host.py `mark_read`) | — | M at REST |
| Push updates | SSE topic `library` | `{type:"saved", item_id}` | E |

### Lab
| Need | Route | State |
|---|---|---|
| Levels, new project, open project, workspace save, data panel, training placement, model landing | `Lab` class exists (`qmx-control/src/qmx_control/lab.py:190`, rows in `catalog.py:805-893` marked "served at the host's user door") but **nothing instantiates `Lab` or mounts a route** (no import outside tests) | M (backend logic built, HTTP not wired) |
| Template install | `POST /api/templates/install {templates}` 202, `GET .../{job_id}` (`HOST/door.py:361,403`) | E (poll) |
| Data card / sample for a panel | `GET /api/data/card`, `GET /api/data/instruments`, `POST /api/data/read` (`HOST/market_data.py:1196-1231`) | E (usable as a stand-in for `lab.panel`) |
| Pods, Lab copilot tools | — | M |

### Portfolio
| Need | Route | State |
|---|---|---|
| Balances, positions, quotes, symbol info, bars | `broker_read` rows are model tools only (catalog BROKER_ROWS, `catalog.py:229`) | M (§26 row 2 still true) |
| Node positions / units | `POST /api/apps/trading-node/tools/positions` / `units` (CS:2038-2063; ops in `qmx-agents/apps/trading-node/app.toml:28-46`) | P (through the generic app-call door, `manage` row, local supervisor) |
| Promote toward paper/live (deploy) | `POST /api/units/promote` operator-only (`HOST/promote.py:61,722`) | E |
| Proposals to sign | `GET /api/portfolio/proposals` (CS:1376) | E (read only; no sign route found) |
| MIS tab | `POST /api/apps/mis/tools/{status|board|round|configure}` (`qmx-agents/apps/mis/app.toml:16-34`) | P (generic door; `readings_query` is a model tool only) |

### Apps
| Need | Route | State |
|---|---|---|
| List, get, create, update, versions, test, publish, rollback, start, stop, restart, enable, logs, evidence, registry, resources (ui:// panels), call a tool | CS:1875-2128 (`/api/apps…`), sign at SRV:423 | E |
| Archive app | `POST /api/apps/{id}/archive` always answers 501 `not_implemented` (CS:2387-2390) | M |
| Push | SSE topic `apps` | E |
| First-party app screens (QMB, trading node, MIS) | all three manifests are `kind = "headless"`, no `ui` folder (`qmx-agents/apps/*/app.toml:5`) | M (UI-NOTES-UNITS §9/§19 "one manifest line" still true) |

### Workflows
| Need | Route | State |
|---|---|---|
| Definition, draft get/put, validate, publish (put), versions, archive version, test run (`?fake=`), live run with inputs | CS:2145-2210 | E |
| Runs list / get / explain / cancel / resume, spans | CS:2213-2245, 2321-2332 | E; `GET /api/workflow-runs/{id}` now carries `placement` (CS:2218-2235); list rows do not |
| Run live view | `GET /api/engine/events?run_id=` | E (one run at a time; no all-runs stream) |
| Triggers list/create/enable/disable/inputs/run-now/explain | CS:2334-2378, `qmx-engine/.../rest.py:48` | E |
| Webhook in | `POST /api/hooks/{trigger_id}` (`HOST/host.py:2877`) | E |
| Maintenance list | `GET /api/maintenance` (`HOST/maintenance.py:160`) | E: `{host:[jobs with switch], workflows:[with trigger on/off routes]}` |
| Session / trade-count triggers | — | M (UI-NOTES-UNITS §14, §19) |

### Usage
| Need | Route | State |
|---|---|---|
| Plan windows, readings, tokens per profile, account pool, hard stop | `GET /api/usage`, `POST /api/usage/meter` (HR:373,377; shape `qmx-router/src/qmx_router/readings.py:305-335`) | E |
| Per-run cost | `GET /api/ops/spans/{run_id}` cost (CS:2245-2259) | E |
| Cost over time / per workflow rollup | — | M |

### Inbox / notifications
| Need | Route | State |
|---|---|---|
| List | `GET /api/inbox` (CS:2380-2385): notes, open incidents (backup places etc.), workflow items | E (§26 row 4 now closed) |
| Resolve | `POST /api/inbox/{id}/resolve` | E (workflow items) |
| Data inbox | `GET /api/data/inbox` (`HOST/market_data.py:1275`) | E (separate list) |
| Push | no `inbox` SSE topic | M (poll) |
| Phone / wake alarms | ntfy + Healthchecks cards exist only in the trading-node connect kind (`HOST/connect_node.py:25,1433`) | P |

### Places / Machines + Accounts (Settings)
| Need | Route | State |
|---|---|---|
| Place list | `GET/PUT /api/settings/engine` (`placement.<name>.*`) | E |
| Connect a storage / server (compute) / deep logs / trading node | `GET /api/connect/kinds`, `POST /api/connect/jobs {kind, place, answer}` 202, `GET /api/connect/jobs/{id}`, `POST .../cancel` (`HOST/connect.py:304-331`; kinds `HOST/connect.py:390`) | E: job with `needs:{card,line,fields,key,link,job}` cards |
| Type a key once | `PUT /api/keys/{qmx/name}` 204, `GET /api/keys` -> `{set:[names]}` (`HOST/keys.py:86-87`) | E (§26 row 3 closed: cTrader client id/secret are in `KEY_NAMES`) |
| cTrader sign-in on This PC | `POST/GET /api/venue/ctrader/sign-in` (`HOST/venue_session.py:496,505`) | E |
| Live machine states, sessions in use, vault sync age | heartbeats are model-tool only | M at REST |
| Broker/connection rows | `GET/PUT /api/settings/brokers`, `/connections` (whole-section) | E |
| Observer tokens | `PUT /api/settings/observers {name}` mints once, `{revoke}` (CS:1223) | E |

### Settings (rest)
`GET/PUT /api/settings/{section}` (CS:1100,1198), sections: providers, mcp_servers, budgets, memory_provider, backup, brokers, connections, claude, environment, agents, engine, roles, rules, observers, telemetry, data, units, qmb, records, journals, apps, node (CS:55-78). Merge semantics with `remove:[dotted keys]` (CS:1202-1221). `GET/PUT /api/claude-settings` (HR:420,424). Telemetry is now validated (`invalid_telemetry`, CS:501-540, 1316). Backups: `/api/backups*` (`HOST/backups.py:1559-1612`), now including `restore/check`, `restore`, `restore/cancel`, `restore/carry-on`, `keys-to-fill`.

### Unit screens
| Screen | What exists | State |
|---|---|---|
| Unit page (logic, checks, results, markets) | Library item reads; `unit_check`/`unit_explain`/`blocks_*` are model tools only | P |
| Journal view | `journal_query` model tool only; node `journal_tail` via app-call door | M at REST for the unit journal |
| QMB app | runs = `backtest-result` Library items; `backtest_run/status/results/compare/judge_run` model tools only; QMB app ops only `capabilities`, `instruments` | M (no REST to start a backtest from a screen) |
| Trading node app | 19 ops via `POST /api/apps/trading-node/tools/{op}` (status, units, positions, journal_tail, passport, deployments, records, deploy, withdraw, pause, resume, kill, flatten, bind, confirm_same_node, take_over, sign_in_begin, sign_in_code, self_test, rotate_keys) | P (works through the generic door; no push stream; remote nodes not verified through this door) |
| MIS | 4 ops via the same door | P |
| Promotion / deploy dialog | `POST /api/units/promote` | E |
| Dictionary publish | collection publish route | E |

### First start / install
Card routes (`HOST/first_start.py:1730-1742`): `GET ""`, `POST /new`, `/open`, `/copies`, `/restore/check`, `/restore` 202, `/bring-in` 202, **new since §19:** `/connect` 202, `/keep` 202, `PUT /keys/{name}`, `POST /jobs/{id}/cancel`; plus `GET /jobs/{id}`, `POST /handover`. Exit-code contract per §19 rows 3-4 (not re-verified line by line). Status: E.

---

## 3. Gaps ranked by how much they block a release UI

1. **Token handoff to the UI.** Every route needs the keyring bearer and the host never serves it. The desktop shell (not built in this repo) must read `qmx/control-token` and inject it, and must run SSE over `fetch`. Without the shell nothing wires. (SRV:55-74, 336-363)
2. **No push for most state.** `jobs` topic is never written; `runs` topic refreshes only on `GET /api/aggregates`; no inbox topic; engine SSE is one run at a time. Home, Workflows runs board and Inbox must poll. (CS:87, 1011, 1851-1867)
3. **Lab has no HTTP at all.** `qmx_control.lab.Lab` is built but never mounted. (`lab.py:190`, `catalog.py:805-893`)
4. **Broker reads over REST** (balances, positions, quotes, bars). Still model-only. Blocks Portfolio. (§26 row 2: still true)
5. **Domain reads behind screens are model-only:** backtest run/status/results, journal_query, unit_check/explain, blocks_*, readings_query, heartbeats, provider Test. Blocks QMB app, Journal, unit Checks tab, nodes strip, Machines live state, Settings "Test".
6. **Chat home field** not accepted or returned at REST; Library attach on click; @file family (REF2). Blocks session-home badge and paperclip.
7. **Library list filters** (kind, shelf, drafts, status) and archive from the screen.
8. **First-party app UIs**: QMB, trading node, MIS are `headless`.
9. **Run list lacks `placement`** (single run read has it now).
10. **Smaller:** apps archive 501; no chat rename/delete/compact; CORS blocks DELETE; getting-started state; session/trade-count triggers; usage rollups over time.

### Check of the 2026-10-28 claims (UI-HANDOFF §26 and UI-NOTES-UNITS §19)

| Claim | At 3ae41ffc |
|---|---|
| §26.1 run place missing on run read | **changed**: `GET /api/workflow-runs/{id}` returns `placement` (CS:2218-2235); still missing on `GET /api/workflow-runs` list |
| §26.2 broker reads not over REST | **still missing** |
| §26.3 cTrader app key entry | **exists**: `PUT /api/keys/{name}` (`HOST/keys.py`, `KEY_NAMES` has client id/secret) |
| §26.4 backup incidents not in inbox | **exists**: `open_incidents` merged into `GET /api/inbox` (CS:2380-2385) |
| §26.5 read-only store said up front | **exists**: `GET /api/health` `read_only` (SRV:471-477) |
| §26.6 telemetry value check | **exists**: `invalid_telemetry` (CS:501-540) |
| §26.7 local deep logs | **exists (partial)**: `deep_logs` starts OpenObserve on This PC for `send_to=this-pc` (`HOST/host.py:1555-1569`), plus the `deep_logs` connect kind |
| §26.8 backup/restore beyond the card | **partial/changed**: restore check/run/cancel/carry-on and keys-to-fill routes now exist (`HOST/backups.py:1589-1612`); "sync to my account" design pending (maintenance lists sync/upkeep/drill) |
| §26.9 / §18 attach route + @file family | **still missing** |
| §1.1 block renames | **exists** in backend vocabulary (CS:158-176) |
| §1.2 `home` in `POST /api/chats` body | **missing** at REST (stored internally only) |
| §1.4 approval decisions | exists (HR:365) |
| §1.6 compact now | **missing** at REST |
| §19 card routes | **changed**: adds connect, keep, keys, job cancel |
| §19 port 8766, origin 5173, bearer from keyring | exists as written |
| §23.4 cTrader sign-in | exists |
| §24.7 restore etc. not built | **changed** (see §26.8) |
| UNITS §19 getting-started state | still missing |
| UNITS §19 run list place | partial (see §26.1) |
| UNITS §19 cTrader app key | exists |
| UNITS §19 session/trade-count triggers | still missing |
| UNITS §19 QMB own screen | still missing (`kind = "headless"`) |

---

## 4. apps/qmx-ui on engine/base

- **History on engine/base:** one commit only, `aeccd2fd` (2026-10-01, "Assemble pinned published backend, governing docs and reserved UI baseline"), 77 files; zero commits since through 3ae41ffc. No README.
- **What it is:** a small SvelteKit 5 static-SPA scaffold (56 files under `src/`: Bootstrap and Home screens, a shell rail, a `host/` client). `package.json` describes it as a "Svelte client of qma-wire"; qma-wire exists on engine/base only as docs (`docs/components/qma-wire.md`, `docs/contracts/ct-40-qma-wire-envelope.yaml`), not as the host's door.
- **Lineage:** same lineage as ui-review/repair, but much older. Its `apps/qmx-ui` tree (`542e2389`) is byte-identical to ui-review/repair's commit `f6ffaddf` (2026-09-28, "story 66.4: Home is attention and resume..."), the factory's early UI stories 66.1-66.4. ui-review/repair then added 117 more `apps/qmx-ui` commits up to `eea09941` (2026-10-14), ~300 src files. engine/base's commit is a squashed copy, not a git ancestor (`aeccd2fd` is not an ancestor of ui-review/repair; merge-base is `7b65732f`, 2026-09-27).
- **Verdict:** a stale reserved stub of the 2026-09-28 factory scaffold. It is neither the drawn design (that is ui-review/repair) nor wired to the current host routes.
