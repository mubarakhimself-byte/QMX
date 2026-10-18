# Harness changes (a plain change list)

Rewritten 2026-10-18 by the unlock pass (ruling 118, `research/methodology/43-whole-app-unlocked.md`). The harness is an ordinary module of QMX. Nothing below is a request, a grant or a round he must approve, and no row keeps a "fallback if refused". Each change ships like any other change: one build, one check (light verification), and a probe first only where a row names one. Ids are kept from the earlier request rounds (H0 to H38) so older documents still resolve; new rows start at H39.

The file name stays `HARNESS-REQUESTS.md` because the spine and older studies link to it. The code that moves out of the harness into its own package (`qmx_router`, engine AD-56) is listed here too, because it leaves `qma-harness`.

Code truth for every "today" below: `origin/engine/base` = `132169c7`, read with `git show`.

## A. Built already

| Id | Change | State |
| --- | --- | --- |
| H0 | Export `Background`, `Child`, `Interactive` from `qma/harness/__init__.py` | built (HG1 #92) |
| H15 | `NewChat.compact_at` for Background and Child chats (`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`) | built (HG1); persisted by H19 below |
| H16 | Per-chat observe-only hooks after the gate | built (HG1) as callables; re-shaped by H19 below |
| H17 | `AGENT_OPERATIONS` rows for the engine's `workflow_*` tools | built (HG1) |
| HG2 | `Harness.meter()` (one haiku turn for a plan reading) | built; gains the cooldown in section I |

## B. Programmatic chats (engine AD-53, AD-60)

| Id | Change | Why | Deletes or replaces | Check |
| --- | --- | --- | --- | --- |
| H1 | `Harness.run_turn(sid, prompt) -> TurnHandle`: `events()` yields the projected blocks plus `queued`, `started`, tool, compaction and `waiting_on_model` facts; `result()` resolves once with status, final text, usage (cache and thinking tokens), tool calls, compactions, context read and terminal reason. Built on `Chat.next_end()`, which exists. | the engine waits for a turn by polling `chats/<sid>.json` every 50 ms and re-paging all of the turn's session events each poll (`qmx_engine/ports/harness_adapter.py` `wait_turn`, `_blocks`): slow, racy, and quadratic on long turns | the engine's polling code (`wait_turn`, `_turn`, `_blocks`, `_last_event`, `_journal` reads, about 200 of the adapter's 375 lines) | unit: a turn's `result()` equals its blocks; live: a 40-tool-call agent turn ends with no poll loop running |
| H2 | `NewChat.tools: list[str] or None` passed to the SDK `tools` option (`[]` means none) | a node gets exactly the tools it declares and a plan-row `llm` chat none (B-51, B-70) | "use only these tools" text in the brief as the only control | a resumed `tools: []` chat calls no tool |
| H5 | dropped | the engine keeps its own attempt-to-session table | — | — |
| H8 | `NewChat.mcp_servers`: extra per-chat MCP servers (the sandbox tool server for `runner_outside`) | AD-25 containers and remote placements | the "not scheduled until granted" note on `cli_inside` and `host_harness` | an agent in a container calls `sandbox_bash` and the host's `Bash` is absent |
| H18 | `Harness.close_chat(sid)`: end the CLI process of a finished Background or Child chat; nothing is deleted | idle CLIs held RAM until the reaper (B-50) | reliance on the reaper | after an `llm` attempt on a plan row, no CLI process of it is left |
| H19 | Persist every `NewChat` option on the chat record (`compact_at`, `tools`, `agents`, `mcp_servers`, `append_system_prompt`, `home`, `packs`, `hook_sink`, `permissions`, `policy_args`, `claude_hooks`); hook sinks and permission policies are **named** objects the host registers on the `Harness` at start (`register_sink`, `register_policy`) and are resolved by name when a chat is reloaded | a chat reloaded after a restart lost its compaction point and hooks (B-6, L-7), because callables cannot be stored | the engine's context-watch restart in a fresh chat (the H15 fallback in `nodes/agent.py`) and the callable form of H16 | kill the host mid-attempt; the resumed chat compacts at 0.40 and its PostToolUse spans still arrive |
| H20 | Generate CLI allow rules from the Effect table at launch: READ and `DOMAIN_WRITE` `qmx` rows never ask while `[agents] domain_write = "allow"`; MANAGE rows always ask | a draft save and a test run asked once in default mode (B-5) | the first-run "add this allow rule" card | E42: the copilot builds and test-runs a workflow with no ask |
| H21 | `NewChat.append_system_prompt` for Background and Child chats, after the harness's own `append`; Claude settings move from the command line to a per-chat settings file (the SDK's `settings` takes a path [retrieved: claude-agent-sdk 0.2.166 `ClaudeAgentOptions.settings`]); the existing command-line length check stays and is the only bound | the node brief and memory snapshot belong in the cached prefix (B-53, about 5,470 tokens paid per chunk today) | the 8,000-character cap and the brief in each chunk's first user message | probe P-SET, then a two-chunk run reads the brief from cache on chunk 2 |
| H22 | Ship `py.typed` in `qma-harness` | strict typing for every consumer (B-10) | pyright `extraPaths` workaround | pyright clean without it |
| H23 | dropped: `qmx_host` owns the one `ControlService` (engine AD-52) | — | — | — |
| H24 | moved to `qmx_host`: the principal of every call is set at the one REST door (`user`, `agent:<session_id>`, `workflow:<run_id>`) | publish, enable and live start are `user` acts (AD-11) | the "publish only on the engine host's own REST routes" fallback | a copilot `workflows_put` returns a card; the same call over the UI bearer publishes |
| H25 | dropped: one host serves chat and engine routes (AD-52) | — | — | — |
| H39 | Named permission policies for Background and Child chats, answered in-process from `can_use_tool`: the engine's `engine` policy allows the node's declared tools with writes only under the attempt overlay, denies anything else at once with a reason, and defers a declared `irreversible_external` tool to the inbox | agent nodes can write (AD-60); asks were answered by a poller (`Reject("unattended run")` in the adapter) | the poller's ask handling | probe P-PERM, then E55 |
| H40 | `NewChat.home` and `NewChat.packs`, written at birth; a Child copies its parent's home; `Harness.set_packs(sid, packs)` | session homes and pack sets (AD-35) without a second record and a write-once route | the designed `session_homes` table and `PUT /api/sessions/<id>/home` (never built) | the UI creates a Lab chat; the hub lists it with its Lab badge |
| H41 | `NewChat.claude_hooks`: his Claude Code hooks for one workflow, written into its agent chats' settings file, checked by `HOOK_KEYS` | "we have hooks" for workflows (alignment B chat item 4) | the rule that his hooks reach workflows only as bus scripts | a workflow's PostToolUse command hook runs in its agent chats and not in copilot chats |
| H45 | `qma.harness.stuck`: the stuck detector's pure chat rules (no progress, loop, no convergence) fed by `run_turn` events, used for every Background and Child chat and by the engine's watchdog | one judgement for copilot helpers and engine attempts (AD-16) | a second copy in the engine | E41 fixtures pass for a copilot helper and an engine attempt alike |

## C. The guard (engine AD-54)

| Id | Change | Why | Deletes or replaces | Check |
| --- | --- | --- | --- | --- |
| H31 | `qma.harness.guard`: one PreToolUse callback, first on every call, fails closed on its own error. Denies plan-login and secret files, keyring and credential-store readers, writes into the QMX home outside `workspaces/` and `agent-memory/`, writes into any store or the install tree, recursive deletes outside run zones, disk, format and registry tools, NT device and UNC paths, a secret in an outbound command body, invisible or bidirectional Unicode, `delegate` from a native sub-agent, an external MCP tool in an unattended chat unless listed; then his never-allow list. His always-allow list and policy allow rules never lift a floor row. Context-file and persona injection scan and Unicode tag stripping on MCP results stay in this module. | Claude Code-like permissions with the protections that are real (AD-43) | the money gate's rule set as code constants | E56 |
| H42 | Retire the money vocabulary: `name_money_act` on tool names and dispatch targets, broker-host refusals in shell and WebFetch, the runtime money vocabulary in `check_tool_surface`, the exposure probe (`/api/doctor/probe`, `probe_exposure`), `money_posture`, scope proofs, and the import of `qma.core` | rulings 116 and 118: agents have no path to money; `money.py`'s own docstring says each layer is "a guard against accidents" that Bash gets around, and "the read-only broker token is the real guard" (engine run `lows.md`) | `money.py` (1,198 lines) becomes `guard.py`; deny rules on the command line shrink to login and secret paths | a unit test still asserts `Effect` has no money member and no `AGENT_OPERATIONS` row names an order act; `propose_order` still asks |

## D. Packs as plugins (engine AD-55, AD-35)

| Id | Change | Why | Deletes or replaces | Check |
| --- | --- | --- | --- | --- |
| H32 | Every chat registers one in-process SDK MCP server per enabled pack and switches it with `toggle_mcp_server` [retrieved: `ClaudeSDKClient.toggle_mcp_server`, claude-agent-sdk 0.2.166] when the session's pack set changes | packs added mid-session (M-15) with no restart and no MCP process per pack per chat | the `tools/list_changed` plan and the namespaced `app.<id>.<tool>` rows in the one `qmx` server | probe P-TG |
| H43 | Load several plugins per chat: the core plugin (install tree, checked against the installer manifest) plus one materialised view per enabled pack (`<home>/plugins/<object_id>/`: `plugin.json`, `skills/`, `agents/`, `commands/`; never `hooks/` or `.mcp.json`), each checked against its Library object hash; a pack published later joins a chat at its next relaunch-by-resume | ruling 10: mini apps are plugins; Hermes built-in plugin groups (ruling 93) | `PLUGIN_SHA256` in `home.py` and the "one SHA-locked plugin" rule; the QMX skill-reading tool AD-19 had planned | probe P-PL |

## E. Moves into `qmx_router` (engine AD-56)

| Id | Change | State |
| --- | --- | --- |
| H44 | Move `qma/harness/relay.py` (1,147 lines), `qma/gpt/translate.py`, `qma/gpt/siwc.py`, `qma/gpt/probe.py`, `qma/harness/profiles.py` and the plan-usage readings of `usage.py` into the new package `qmx_router`; the harness keeps the launch env and asks the router for grants | first step of the router packet; behaviour unchanged |
| H3 | `router.complete(role_or_model, messages, schema?, session?)` on the key and GPT lanes (plan refused) | to build; `llm` nodes, `llm_complete`, native-video role |
| H6 | per-account readings | lands with the pool |
| H10 | route every request by model id to one of four lanes, normalised per target model (AD-38, AD-50) | to build |
| H11 | the router on the tailnet with run-pass bearers | to build |
| H12 | the chat-completions lane (thinking to `reasoning_content`, translator-owned signatures, `tool_use` ids to `tool_calls` ids) | to build; probe P3 |
| H13 | per-machine plan homes, `qmx node login` | to build |
| H14 | `model_scope` on every grant and pass | to build |
| H27 | plan-lane launch and router hardening | to build dark; **probes P0 and P1 first, P4 and P2 against the dark build**; if P1 fails the plan lane is not built (unchanged: these rest on CLI behaviour and plan billing, not on any lock) |
| H29 | data profiles and the model registry | to build |
| H33 | several GPT sign-ins, one owner machine each | to build |
| H36 | journal fields and hint headers | to build |

## F. No QMX caps (engine AD-40)

| Id | Change | Check |
| --- | --- | --- |
| H28 | `[budgets] max_budget_usd`, `background_cap` and Background/Child `max_turns` accept unset and default to it; `BackgroundCap`, `cap_note` and the usage page's cap rows go; a Background or Child send with no free slot waits (`queued` in `run_turn` events); a child started by a parent blocked on it borrows the parent's slot; `hard_stop` (no paid extra usage) stays | E43 |

## G. Helpers and copilot features

| Id | Change | Check |
| --- | --- | --- |
| H26 | `delegate` v2 (AD-41): handle at once, parallel children, list, steer, stop, completions stored before announce, `output_schema`, images, live transcripts, process ownership, stall monitor, `role`/`model`/`effort` in one bundle, targets `chat` and `cli` (a local process by default) | P5, E52 |
| H38 | `NewChat.agents`: registry-generated sub-agent definitions per role, plus one per model he pins, filtered by the chat's lanes, regenerated on relaunch | **P1 for plan mains, P1k for key and GPT mains** |
| H30 | attachments on turns through the multimodal layer (AD-42) | E44 |
| H34 | session loops: loop rows on the chat record; the loop's prompt is his own stored text, sent as `OperatorText`; the reaper skips a chat with a standing loop | a heartbeat survives a host restart |
| H35 | browser pack and `read_window_below` as copilot tool rows with Effects | E45 |
| H37 | background review fork with `fork_session` [retrieved: `ClaudeAgentOptions.fork_session`] and narrow tools | probe P-FK |

## H. Retired or superseded

| Id | Was | Why |
| --- | --- | --- |
| H4 | a per-chat switch for Claude Code workflows | the `claude_workflow` node kind is retired (AD-5; one engine) |
| H7 | per-chat `agents` for Background chats | superseded by H38 |
| H9 | the relay on the Docker network | superseded by H11 |
| H2 (first form) | `output_format`, `tools`, `max_turns` | superseded by H2 above; no `max_turns` (AD-40); native structured output stays deferred (engine Deferred) |

## I. Bug fixes from the first build

`meter()` gets a cooldown so a turn with no rate-limit event does not spend another haiku turn on every later call (L-16); `meter()` cleans up before awaiting `chat.close()` (L-17); `Harness._options` is pruned when a chat ends (L-8); `_observer` also catches `CancelledError` (L-9); `GET /api/runs` stops listing chat journals as agent runs (B-67, now part of engine AD-57).

## J. Not changed, on purpose (each for a reason that is not a lock)

- The plan sign-in stays with the unmodified CLI's own `/login`; no QMX code holds, stores or swaps a plan token (37d §6.5: an app holding the token bills extra usage, not the plan).
- An Interactive chat refuses `InjectedText`; Background and Child chats are verbatim (no slash command or `@path` from model-written text).
- The launcher's OS limits and kill-on-close per chat.
- The SDK JSONL is the transcript; `setting_sources=[]` stays (QMX writes the settings it wants, now into a per-chat file).
- `PROPOSE_MONEY` (`propose_order`) always asks.
- The relay's token canary on every non-plan lane and the one redaction function.

## Probes named above

| Probe | Gates | Pass |
| --- | --- | --- |
| P-PERM | H39, AD-60 | in a Background chat in `default` mode: the guard sees every call first; a write under the overlay passes through an allow rule without reaching `can_use_tool`; a write outside, an undeclared `Bash` and an MCP tool not in the allow rules reach the named policy and are denied with its reason; a declared irreversible tool waits on the policy's deferral and runs when it resolves allow |
| P-PL | H43 | with `setting_sources=[]` and `strict_mcp_config=True`, a chat launched with the core plugin and two materialised pack views lists both packs' skills (`plugin:skill`), spawns a pack agent, runs a pack command, and starts no MCP server and runs no hook from either pack; **fail:** one combined plugin view per pack set instead |
| P-TG | H32 | an in-process SDK MCP server registered switched off is toggled on mid-session and its tool answers on the next model request with no relaunch; toggled off, a call to it fails; **fail:** an added pack joins at the next turn by resuming the same session id |
| P-SET | H21 | the launcher passes `settings` as a file path on Windows; the command line shrinks by the settings' size; a hook in that file fires |
| P-FK | H37 | unchanged (SOLUTION-DESIGN §26.14) |
| P0, P1, P1k, P2, P3, P4 | H27, H38, H12 | unchanged (SOLUTION-DESIGN §26.14) |
