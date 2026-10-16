# Adversarial review — two units that obey every AD and still diverge

Reviewer: this run, inline (no sub-agent tool in the session). Method: for each AD, construct two builders one level down that follow the letter and clash.

**Verdict: 5 holes to close before handoff, 3 medium, 2 low.**

## Critical / high

1. **AD-2 contradicts itself for governed kinds.** It says `object_id = fp1(canonical manifest)` *and* "the same fp1 the QMF registry computes". A manifest carrying Library fields (`title`, `tags`, `aliases`, `author`, `created`) can never hash to the registry's record fp1. Builder A hashes the whole manifest; builder B hashes the CT-06 identity content; both obey the text and produce different ids for one bot. **Fix:** split the manifest into `identity` (hashed) and `annotations` (not hashed, carried in an occurrence sidecar exactly as `qmf-registry` persistence already does for writer/sequence/created). Each kind schema declares `identity: ct06 | manifest`. `author` and `created` leave identity for every kind so two agents producing identical content dedupe.
2. **AD-3 mapping is ambiguous for pods.** `book-definition`/`bms-definition`/`book-binding → pod`/`pod-block`/`pod-block` can be read three ways. Two importers would map `book-binding` differently. **Fix:** one row per source kind, and add `binding` to the roster (a bot placed in a pod with seat and mode; the UI already shows it as `Connection {server, pod, mode, seat}`).
3. **AD-7/AD-11 ref ownership for runs is split-brained.** AD-11 says the hub owns `refs/runs/*`; a local run on the PC also needs `refs/runs/<run_id>`. Two stores both "own" the namespace. **Fix:** ownership of `refs/runs/<run_id>` belongs to the store that minted the run (the PC for local runs, the hub for remote ones); run ids are globally unique, so no two stores can own the same ref.
4. **No principal model.** AD-7 and AD-9 say "a ref the caller owns" but nothing defines the caller. Builder A keys ownership on the MCP tool name; builder B on the HTTP bearer. **Fix:** a closed `Principal = operator | agent:<session_id> | run:<run_id> | hub | migrator`, derived once at each door: the UI bearer → `operator`; the per-chat in-process `qmx` MCP server → `agent:<session_id>`; a run token → `run:<run_id>`; the pairing key → `hub`/`operator-sync`. Put it in Consistency Conventions and in AD-7's owner table.
5. **Item state has no storage rule.** AD-6 says archiving is "a ref-log entry" but the ref log is defined over refs to objects. Builder A adds a `state` column to `items` (mutable row, violates AD-5); builder B writes a `state` object. **Fix:** item state changes are ref-log entries on the reserved ref `refs/items/<item_id>/state` whose "head" is the literal `active|archived`, with `reason` and `replaced_by` in the entry; the catalog rebuilds `items.state` from it.

## Medium

6. **PC restored from an older backup.** AD-14 says a `stale_head` on a PC-owned ref is "a bug alarm", but after a restore the hub's mirror of `main` is legitimately ahead. Needs an explicit operator-only `adopt(ref, from=hub)` verb (or sync command) and an FM row. Not an AD change; LLD.
7. **Hub health is unmonitored.** AD-13 covers runs; nothing covers the hub itself. Add a `/healthz`, hub logs to `refs/hub/health` objects, and the PC's doctor page showing hub reachability and replication lag.
8. **Comparison view renderer is unnamed.** AD-17 lists renderers but not `diff`; the merge-conflict object has nothing declared to draw it. Add `diff` to the renderer list and make `merge-conflict`'s schema use it.

## Low

9. **Blob slot wildcard semantics** (`pinned/*`) are not defined for merge: say wildcard slots merge per concrete slot name.
10. **ULID** is named without a library; Python 3.14 has stdlib UUIDv7 (`uuid.uuid7()`), which gives the same time-ordered property with no dependency. Switch if the web check confirms it.

## Checked and found closed

- Two agents on one item: AD-7 namespaces + CAS. Closed.
- Remote run writing `main`: token `write_prefix`. Closed.
- An LLM adding an edge: AD-4 closed vocabulary + AD-8 parse-only. Closed.
- A second definition store in the engine: AD-15. Closed from the Library side; the engine architect must agree.
- Index mistaken for evidence: AD-5. Closed.
