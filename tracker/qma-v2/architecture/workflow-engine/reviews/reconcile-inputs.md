# Reconcile inputs against the spine

Inline pass (no sub-agent available in this process: the Agent tool was not loaded, so the skill's sequential fallback applies). One row per load-bearing input; "landed" means an AD or convention binds it; "gap" means the spine must change; "out" means deliberately outside this spine with a pointer.

## Rulings file 26

| Ruling | Status | Where / what to do |
| --- | --- | --- |
| 2 Claude Agent SDK, no LangGraph | landed | AD-3, AD-13 |
| 3 model-agnostic | landed | AD-13 |
| 7 animated/interactive explainer outputs | out | output renderer is the methodology/output layer; the engine hands artifacts to it. Add a Deferred row so the dimension is not silent. |
| 8 memory for autonomous workflows; study Deep Agents | landed, partial | AD-18 covers scopes and lessons. Episodic search over past runs and async steerable sub-agents are not bound. Add to Deferred. |
| 9 mini apps archived, DevOps, I/O | landed | AD-19, AD-15 |
| 10 plugins are the contract | landed | AD-19 |
| 12 hub is just a place; combined sessions | out | session homes are the copilot design; the engine API is home-agnostic (AD-21). |
| 19 agents and workflows are folders | **gap** | AD-2 speaks of "one JSON document" and `*_ref` files but never binds the folder shape. Bind: a workflow is a folder `definition.json` + referenced files; the content hash covers the folder. |
| 21 who writes, who monitors, notification, no rework | landed | AD-7, AD-15, AD-16, AD-17 |
| 22 one engine, templates as configurations | landed | AD-2 |
| 23 built in the editor or Lab, tested before use | landed | AD-11, AD-21 |
| 24 harness untouched, engine apart from chat | landed | AD-3, HARNESS-REQUESTS |
| 25 server/cloud, Hermes plugins and cron | landed, partial | AD-10, AD-20. Hermes' pluggable trigger provider (ticker now, a server/cloud trigger later; "a provider controls the trigger, never execution") is not named. Add to AD-10 or Deferred. |
| 26 several accounts, balancer, providers list | landed | AD-12, SD section 9 |
| 27 no caps, pause and resume | landed | AD-9 |
| 28 Library stores everything | landed (contract only, per coordinator) | AD-14, DOC-CHANGES 6 |
| 29 ends at paper trading | out | template content |
| 31 board saved; graph mode; "the board is simply code" | **gap** | AD-21 binds Graph mode but not Code mode. The UI's Code view is unsynced today (23 section 2). Bind: Graph and Code are two projections of the one draft document and round-trip. |
| 32 desktop app | landed | deployment diagram |
| 34 phone alerts later | landed | AD-17 |
| 35 plain template names | out | template content |
| 38 risks settled | honoured | not re-raised |
| 39 pool is the one harness extension | landed | AD-12, SD section 7 |
| 41-43 Library and intermediary by another agent | honoured | AD-14, AD-20 bind contracts only |
| 44 a workflow can be a single agent | landed | AD-2 |

## The brief's nine scope items

All nine map in the Capability → Architecture table. Two sub-points need tightening: item 1 "no-agent scripts" is bound inside AD-10 but a reader may miss it; item 7 "dead ends" is bound (AD-18 tags). Item 1 "pinned test data" is bound (AD-11); item 2 "fake model" is bound (AD-11, SD 6.2).

## Harness contract (DESIGN.md + hp17)

| Fact | Status |
| --- | --- |
| Background chats are verbatim; `InjectedText` only | landed (SD 8.4) |
| an unattended ask is rejected after `unattended_ask_seconds` | **gap**: the engine is the caller and can answer asks itself through `Harness.answer`. Bind an `ask_policy` on `agent` nodes: `reject` (default, immediate) or `inbox` (turn the ask into an inbox item, bounded by the harness timeout). |
| `ChatTableFull` at `max_live_chats`, nothing queues, writes `needs_you` | **gap**: admission control reads usage and the pool but not chat slots; a wide fan-out would hit `ChatTableFull`. Bind a slot reserve in AD-9. |
| one usage source per profile; plan windows lag | landed (AD-9 reads the last reading; alert threshold absorbs lag) |
| `delegate` denied inside sub-agents; one provider per CLI | landed (AD-13: reviewers are engine nodes, never cross-provider sub-agents) |
| auto memory per workspace | landed (AD-18) but see adversary finding on concurrent runs |
| `qmx_ledger.RunJournal` exists | **gap**: the spine binds SQLite as the ledger and never says whether the existing per-run JSONL journal is reused. Decide: SQLite is the source of truth (transactional claims and memo index need it); the trace export at run end is written through `RunJournal` so the artifact has the fingerprint chain. |

## Docs DECs

DEC-0417, 0418, 0439, 0455, 0428 ratified where kept; DEC-0271, 0312, 0328, 0420, 0443, 0487 changed in DOC-CHANGES. Nothing silent.

## UI ground truth (23)

| Fact | Status |
| --- | --- |
| Pod-block graphs and bot logic open in the same editor | **gap**: nothing says whether those graphs are `qmx.workflow/1`. They are unit internals (out of scope); bind that they are not workflow documents and the canvas may host more than one document type. Add to Deferred. |
| Train layout chip pipeline duplicates the editor | out (UI) |
| Library "Remove" exists for apps | landed (archive) |

## Research 03, 13, 25

| Idea | Status |
| --- | --- |
| `continuity` (a job sees its own last output) and `context_from` (latest output of another workflow) | **gap**: `after` triggers pass outputs, but recurring triggers have no `continuity`. Add to the trigger row and AD-10. |
| Shepherd intent/outcome split | landed (`effect_state before/after/unknown`) |
| `budget.remaining()` readable by nodes | landed (`NodeJob.budget_remaining`) |
| Hermes `[SILENT]`, delivery targets, failure streak | landed (`silent`, `delivery`, `failure_streak`) |
| n8n error workflow | present in the definition seed; fine |

## Actions

1. AD-2: bind the folder shape. 2. AD-21: Graph/Code as projections. 3. AD-4/AD-13: `ask_policy`. 4. AD-9: chat-slot reserve. 5. AD-10: `continuity`, pluggable trigger source. 6. AD-23 / SD 3.2: SQLite source of truth, `RunJournal` for the trace export. 7. Deferred: output renderer, episodic memory, non-workflow graphs on the canvas.
