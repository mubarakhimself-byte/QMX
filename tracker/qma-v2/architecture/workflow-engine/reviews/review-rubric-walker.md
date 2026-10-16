# Review: rubric walker (good-spine checklist)

Inline, sequential (no sub-agent available in this process). Verdict first, then findings by tier.

**Verdict: pass with fixes.** The spine fixes the real divergence points for the level below (definition, execution, triggers, pool, Library contract, surfaces) and leaves no whole dimension silent, but five rules are under-specified enough that two builders could still drift, and one Deferred row lets defaults diverge.

## Critical

None.

## High

1. **Canonical hashing is unbound (AD-7).** The memo key and the content hash both say `sha256(...)` of JSON. Two units (core, remote worker) could canonicalise JSON differently and never share a memo. Fix: bind the hashing function once: `qmx_ledger.journal.fingerprint` (sort_keys, compact separators, `allow_nan=False`) for JSON values; raw `sha256` for artifact bytes. Add a convention row.
2. **Error signature normalisation is loose (conventions).** "type plus first line" lets two executors produce different signatures for one error (timestamps, paths, ids in the line). Fix: signature = `sha256(code + message with digits, uuids, hashes and paths replaced by placeholders)`; one function in `qmx_engine.ledger.signature`.
3. **Chat-slot pressure (AD-9, AD-12).** Pool leases spread across accounts but the harness still refuses at `max_live_chats` with a `needs_you` block, which AD-9 promises never to trigger. Fix: admission also reserves a chat slot from `max_live_chats − interactive_reserve`; fan-out width is bound by the slot reserve, not only by leases.
4. **Concurrent runs of one workflow share a workspace (AD-18).** Two live runs would write the same folder and their reversible snapshots would collide. Fix: a run's write zone is `workspaces/wf-<id>/runs/<run_id>/`; the chat workspace stays the workflow folder for memory; `max_concurrent` on a version defaults to 1 for workflows with agent nodes; the snapshot covers the run zone only.
5. **The ledger's relation to `qmx_ledger.RunJournal` is unstated (AD-23).** Brownfield has an append-only fingerprinted JSONL journal per run; the spine binds SQLite without saying why or how they relate. Fix: SQLite is the source of truth (transactions for fire claims, leases and memos); the run's trace export is written through `RunJournal` so the artifact carries the fingerprint chain; `model_call` rows the harness already writes per chat stay where they are and the span records the chat id to join them.

## Medium

6. **Defaults can diverge (Deferred).** "Exact default numbers" are listed in SOLUTION-DESIGN but no AD says where they live in code. Fix: convention row: every default lives once in `qmx_engine.settings.DEFAULTS` and is read through `SettingsPort`; no literal default elsewhere.
7. **Registry declares ports (AD-4).** The Rule names typed ports but not that the registry entry fixes each kind's input and output port names (`main` default; `pass`/`fail`, `changed`/`silent`, gate option names). Add one sentence.
8. **Engine bus envelope (AD-10, AD-19).** Events are named in the conventions but the envelope and durability are not: a trigger filter needs a stable shape. Fix: `name, at, run_id?, source, data`; an event is appended to the ledger (or the Library/app journal that owns it) before it is published; the bus is in-process.
9. **Ledger schema evolution.** Nothing says how `engine.sqlite` migrates or how an old run folds under a new core. Fix: convention: forward-only migrations with a `schema_version` row; the fold is versioned by the definition's `typeVersion`s, never by the engine build; an event the current core cannot fold parks the run with a `black` item.
10. **Backup of engine state.** The operational envelope covers deployment but not backup of `engine.sqlite`. Fix: Deferred row pointing at the Library agent's backup design, with the rule that a finished run is fully represented in the Library (summary + trace) so the ledger is rebuildable except for in-flight runs.

## Low

11. AD-21 names Graph mode only; Code mode is a second projection (reconcile finding).
12. AD-2 should bind the folder shape (reconcile finding).
13. `uuid7` on Python 3.14 is [remembered], not verified; the verification lens should flag it.
14. SOLUTION-DESIGN section 2.1 example uses `"effect": "irreversible"` on `llm` and the kinds table says the same; consistent. No action.

## Checklist tally

- Real divergence points fixed: yes, after highs 1-5.
- Every Rule enforceable: AD-21 and AD-22 are review-enforced only; acceptable at initiative altitude.
- Deferred safe: after medium 6 and 10.
- Named tech verified: brownfield pins only; see verification lens.
- Brownfield ratified: control stubs, qmx tools, RunBundle, RunJournal (after high 5), `agent-memory` per workspace.
- Spec coverage: the brief's nine items map; no parent spine inherited.
- Dimensions: deployment, environments, infra, operations, security, testing, observability all present; backup now covered by medium 10.
