# Engine notes

These notes are for the operator reviewing the engine and for the next engineer who owns it. They
record what the engine's checks showed at EP14, where the build departs from the architecture, which
harness requests are in use, and how to start the engine.

## Every engine check, rerun

`scripts/live/engine/run_all.py` reruns every `e*.py` and `x*.py` check in plan order, each in its
own process with all its lanes, and prints one table. Run it from `qmx-agents/` with the agents
venv:

```
uv run --no-sync python ../scripts/live/engine/run_all.py
```

A check passes when it exits 0. Lane logs carry the prefix `run-all-` (after any
`ENGINE_LOG_PREFIX`), so a rerun never overwrites another PR's evidence. The ship home's
`settings.toml` is hashed before the run and after every check. A check that changes it fails and
stops the run. Checks that need a plan turn (`e09_roles`, `x11_agent_chunks`) take the lane lock
themselves. Pass `--only "<name>"` to rerun one row.

The table at EP14's head (builder's run, 2026-10-17):

RUN_ALL_TABLE

Spend of that run: SPEND_LINE

## Departures from the architecture

Each departure ends when the later packet named in the last column lands.

| AD | Departure | Reason | Ends when |
|---|---|---|---|
| AD-3 | The engine runs under `qmx_engine.host`, not `qma.serve`. | The composition root is inside the harness package. HG1 grants H0's exports, and H0 does not cover composing the engine in `qma.serve`. | L1 |
| AD-12 | No account pool, so the ladder's account step is skipped and recorded. | The pool is a later packet. | L2 |
| AD-25 | `cli_inside` and `host_harness` nodes are refused at dispatch. | They need relay run passes. | H11, then L4 |
| AD-35 | The engine records each Background chat's home on `node_started` but does not write `session_homes` in `qmx_control`. | AD-35 is outside this program's scope. | L17 |
| AD-25 | Agent nodes run as harness Background chats with every ask rejected, so they cannot write. | The sandbox is a later packet. | L6 |
| AD-11 | Test mode marks `test_only` rows in the engine's `[roles]`, not in a pool. | No pool yet. | L2 |
| AD-14 | The Library is a SQLite fake behind `LibraryPort`. | The real Library ships later. | L11 |

## Harness requests

The operator granted H0, H15, H16 and H17 on 2026-10-17 (ruling 89). HG1 built them, and HG2 added
`Harness.meter()`. The engine uses the real APIs; each fallback stays only as safety. H1 to H14 are
not granted, so the engine runs on each one's fallback.

| Id | Request | In use at EP14 |
|---|---|---|
| H0 | Export `Background`, `Child` and `Interactive` from `qma.harness`. | HG1's API. `ports/harness_adapter.py` imports `Background` from `qma.harness`; no engine module imports a harness submodule. `qmx_engine.host` stays the composition root until L1. |
| H1 | `Harness.wait_turn`, or a terminal item from `live()`. | Fallback. A turn ends when the chat record reads `turn == "idle"` (EP0's detector). |
| H2 | Per-chat `output_format`, `tools` and `max_turns`. | Fallback. The engine validates the answer against the node's schema with one repair turn, states the tool list in the brief, and relies on the global turn cap. The tool list is not enforced (see the known gaps below). |
| H3 | One relayed request without a CLI. | Fallback. An `llm` node is a one-turn, tool-less Background chat. |
| H4 | A per-chat switch for Claude Code workflows. | Fallback. The `claude_workflow` node kind is unavailable. |
| H5 | A chat tag to find an attempt's chat. | Fallback. The ledger keeps each attempt's session id. |
| H6 | `Harness.usage()` per account. | Fallback. Admission reads the plan account's reading; per-account readings land with the pool (L2). |
| H7 | Per-chat sub-agent definitions and caps. | Fallback. Sub-agents stay on with the global caps; their tokens are counted from the journal. |
| H8 | A per-chat sandbox tool server. | Fallback. Every ask is rejected, so agent nodes cannot write (L6). |
| H9 | The relay reachable from the Docker network. | Superseded by H11. Not needed while every node runs `runner_outside`. |
| H10 | Relay routing by model id. | Fallback. Mixed providers come from fan-out across agent nodes. |
| H11 | The relay on the tailnet with run passes. | Fallback. `cli_inside` and `host_harness` nodes are refused at dispatch. |
| H12 | An OpenAI chat-completions translator lane. | Fallback. Kimi is reached through the OpenRouter row. |
| H13 | Per-machine plan homes. | Fallback. Plan accounts serve the PC only. |
| H14 | Per-chat `model_scope`. | Fallback. The relay allows every configured provider; the engine records the provider on each span. |
| H15 | Per-chat compaction threshold on `NewChat`. | HG1's API. Agent chats start with `compact_at` 0.40. The restart with a `memory_note` runs only when the option is refused or a chat is picked up after a restart. |
| H16 | Per-chat SDK hooks after the money gate. | HG1's API. `NewChat(hooks=ChatHooks(...))`; tool spans arrive live from PostToolUse. The turn-end reconcile against the session's `tool` blocks stays as safety. |
| H17 | `AGENT_OPERATIONS` rows for the `workflow_*` tools. | HG1's rows, wired by EP13. Saving a draft and running a test never ask; publishing and a live run each ask once. The `library_save` watcher that test-runs a draft whose `meta.test_requested` changed stays as safety. |

## Start the engine host

The host serves the control app with the engine attached to its workflow doors. It does not serve
the harness's chat routes, so chats still need `qma.serve`.

1. Pick a QMX home. Never run the host on a home where `qma.serve` is running. The host refuses to
   start when the home's `control-process.json` names a live host, and prints that host's PID.
2. From `qmx-agents/`, run
   `uv run --no-sync python -m qmx_engine.host serve --home <home> --port <port>`.
3. Call it at `http://127.0.0.1:<port>` with the local control token from the OS vault as the
   bearer, the same token `qma.serve` uses. `GET /api/health` answers once it is ready.
4. Stop it with Ctrl+C. A killed host leaves its runs in the ledger; restart it and call
   `POST /api/workflow-runs/{id}/resume`.

The engine's own routes are under `/api/workflows`, `/api/workflow-runs`, `/api/triggers`,
`/api/inbox` and `/api/engine/events`. `GET /api/workflow-runs/{id}/explain` returns the same
document as `python -m qmx_engine explain <run_id> --home <home> --json`.

## The example

`examples/hello-chunks/` is the smallest workflow that shows the engine's shape. A script fetches
twelve words from a fixture, an `agent` node on the `scanner` role sorts them in three chunks of
four, a join collects the chunks, and a deterministic grader checks every word got one answer.

`scanner` is a cheap role. A test run takes the test-only OpenRouter Kimi row first, so it spends
about three Kimi turns. On a home with the plan login, a live run takes `claude/haiku`. The EP14
lanes (`scripts/live/engine/x14_hello.py`) run it on a throwaway home with only the OpenRouter row
and `scanner` set to Kimi for live runs too, so they never touch the plan.

## Known gaps found at EP14

- A killed `agent` chunk is resumed on its saved chat with a one-line "finish the task". If the
  host died before the CLI wrote the task to that chat, the model has no task. On Kimi it explored
  with tools, failed the schema, and the run parked. Lane 4 kills after the task reached each chat.
  The fix belongs to `nodes/agent.py` (BACKLOG).
- An agent node's `tools: []` is stated in the brief only, so a confused chat can still call tools
  until H2 lands. The money gate still blocks every money act and shell access to QMX state.
- `python -m qmx_engine explain` text lists attempts but not spans; chunk partitions show in
  `--json` and over REST.
