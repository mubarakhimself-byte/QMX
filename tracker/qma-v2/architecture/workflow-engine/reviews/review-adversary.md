# Review: adversary (two units that obey every AD and still build incompatibly)

Inline, sequential (no sub-agent available in this process). Each pair below obeys the spine to the letter; each is a hole to close.

**Verdict: six holes, all closable with a tightened rule or a convention row.**

| # | Unit A | Unit B | Incompatibility | Close with |
| --- | --- | --- | --- | --- |
| 1 | `core` hashes node inputs with `json.dumps(obj)` (default separators, insertion order) | `workers.remote` hashes with `sort_keys=True` | memo keys never match across placements; every remote node reruns on resume | bind `qmx_ledger.journal.fingerprint` as the one JSON hash (convention) |
| 2 | `nodes.script` reports `failed(signature="ValueError: file /tmp/run-8f3a/x.csv missing")` | `ledger` dedupes inbox items by exact signature | every retry is a new incident; AD-17 "one item per incident" silently fails | bind the signature normaliser (`ledger.signature`) and require every executor to call it |
| 3 | `pool` grants 2 leases on each of 3 plan accounts (6 live chats) | `harness` has `max_live_chats = 4` and refuses the fifth with `ChatTableFull` plus a `needs_you` block | AD-9's "never a needs_you for a cap" breaks; the run parks on a slot, not a limit | AD-9 admission reserves a chat slot from `max_live_chats − interactive_reserve`; fan-out width bound by the slot reserve |
| 4 | `nodes.agent` writes outputs into `workspaces/wf-paper-scout/` (the chat cwd, so memory is workflow-scoped) | `core` starts two runs of the same version at once (trigger `max_concurrent = 2`) | both runs write one folder; the reversible snapshot of run A restores over run B's files | run write zone = `runs/<run_id>/` inside the workflow workspace; snapshot covers that zone; `max_concurrent` default 1 when agent nodes exist |
| 5 | `nodes.library` in test mode writes `test_report` evidence to the live Library | `service.tests.run` promises "scratch namespace discarded or kept as evidence" | `LibraryPort` has no scope parameter, so test writes land live and `supersede` chains fill with test junk | add `scope: live | test` to every `LibraryPort` write; test-scope rows are invisible to live reads and are archived with the report |
| 6 | `triggers` publishes `run.finished` events as `{"run": id, "when": ts}` | `nodes.app_op` publishes `app.news.refreshed` as `{"id": …, "at": …}` | an `event` trigger filter cannot be written once; two event dialects | bind the bus envelope `name, at, run_id?, source, data` and that every event is journaled before publish |

Also probed and found closed by the spine as written:

- Two executors returning different envelopes: AD-4 fixes `ok | failed | waiting | gate`.
- A draft run live through a subgraph: AD-11 says live refuses drafts, subgraphs on drafts are test mode only.
- A run creating a trigger: AD-10 refuses `caller_kind: workflow` on `service.triggers.*`.
- A node naming a model: AD-13 forbids it and validation refuses.
- Two writers on `engine.sqlite`: AD-23 one writer thread; the fire-claim lease stops a second process.
- A doctor patching a definition: AD-16 forbids; proposals are drafts.
- Prefix replay creeping back through `subworkflow`: the child run has its own memos; the parent's memo for the node is the child `run_id` plus output hash.
- A remote worker appending to the ledger: AD-20 says the engine appends from gateway events; the worker never holds the ledger.
- Secrets in a definition: AD-23 validator refuses token shapes.
- An `llm` node calling a key directly: AD-13 forbids; the relay is the only key reader.

Residual, accepted: AD-21/AD-22 are review-enforced (a surface could re-implement readiness and nobody would notice until it drifts); a lint that greps the UI for engine-state computation is a later guard.
