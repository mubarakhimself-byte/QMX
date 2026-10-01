# Independent Sol ATC and CT12 review

Reviewer: GPT 6.1 Sol. Candidates: ATC `830dfda3e09e4dae6c4f5f0ccf6ee787f9418da2`; CT12/CT10 `34aa8a0af1df5fad684b72cd3a02349c83c2888d`. Read-only production review; no product edits. Verdict: **changes required**, not full CLI acceptance.

## Blocking held-out findings

1. `qmb.execution.alternative.execute_alternative_run` assumes an append acknowledgment's value is complete. Patching the actual `JournalWriter.record` to return `Ok(None)` or `Ok('ack')` raises `AttributeError` at `receipt.event`, rather than returning a typed refusal. More seriously, wrapping the real append and replacing only its typed `StoreReceipt` with an unrelated fingerprint (`fingerprint({'unrelated':'artifact'})`), LIVE world, sequence 999, and false evidence/retention flags still returns an accepted ATC receipt. The persisted event is real, so ordinary event fingerprint reread passes, while the result cites a false physical receipt. Validate the complete typed event/store acknowledgment and actual stored artifact relationship before advancing state or issuing a result.

2. `qmb.host.replay.read_recorded_replay_source` accepts `dataclasses.replace(valid_manifest, embargo_width=Duration(value_ns=999))` retaining the original manifest fingerprint. It admits real persisted TRAIN observations and emits the original split fingerprint despite using changed partition rules. Verify/reconstruct the manifest identity before admission; typed dataclass membership alone does not bind its fields.

3. The generic `AppendStore.read_raw_self_guarded` content guard does not account for a CT10 row's `known_at_ns`. Actual persisted source evidence with event time below the seal and knowledge time exactly at the seal is correctly refused by `SourceObservationBoundary.read`. However, reading the same archive through `read_raw_self_guarded` with `derive_position=lambda rows: Ok(eventInstant)` returns sealed bytes. This contradicts the method's explicit defense against understated caller derivation. Derive CT10 knowledge time in the shared content guard as well. The new CT10 boundary itself correctly supplies knowledge time.

All findings were sent to root; CT12 findings were sent directly to execution owner. No corrective candidate was reviewed in this verdict.

## Independent positive and negative checks

Command: `.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_alternative_execution.py packages/qmf-data/tests/test_splits.py packages/qmf-data/tests/test_source_boundary.py qmb/tests/test_replay_materializer.py` — **81 passed**, 0.61 seconds.

Held-out actual `partition_source_observation` checks: embargo gap exactly 100 admitted, gap 101 refused; purge distance exactly 100 admitted, distance 99 refused; ordinary TRAIN observation admitted. These five controls passed. Actual source boundary read refuses a source observation whose stored knowledge time equals the seal.

Actual JSONL `os.fsync` failure during ATC decision append yields a typed refusal, blocks the writer, and retains next sequence 0. After removing the fault, `retry_blocked` succeeds and advances to sequence 1; checked reopen finds exactly one decision. A subsequent successful ATC result rejects final-state mutation with `TypeError`, and recomputing its fp1 identity equals its result fingerprint.

## Scope

The registered interpreter is an explicit trusted fixture policy using exact integer recorded quotes. This does not define the illustrative financial `fixed-fraction`/`max_gross` grammar, prove provider behavior, or complete adopted ATC optimization. These controls do not approve the installed CLI-to-selected-source-to-Book-to-economic CT29/CT32-to-one-terminal chain. Complete ACK corrections, broader callback/admission mutation controls, and the pending Book handler review remain independent follow-up work.

## Corrective candidate retest

ATC `f13d607c45dc4f9191ca9608480dcf06d7c16c27` closes the original `Ok(None)`, `Ok('ack')`, and false physical store receipt controls: each now returns a typed refusal. Inspection confirms exact expected event payload, type, outcome, writer, sequence, instant, and correlation are compared before state advance; the physical row fingerprint and receipt position are checked against the journal and the event is reopened through the checked reader.

CT12/request `3e598bbe37fce6bac1aff393340e9c5683ed174a` closes the original stale manifest and understated knowledge-time seal controls. Both independent reproductions now refuse. The new shared content guard explicitly considers stored `known_at_ns`; partitioning recomputes the manifest identity.

**Changes still required at these candidates:**

- A typed `JournalAppendReceipt` with a typed `JournalEvent` whose `event_type`, `world`, or `outcome` was replaced by a string raises `AttributeError` in mismatch diagnostic `.value` access. These were separate wrappers around real successful filesystem appends, using `dataclasses.replace`. Complete ACK validation needs safe field-type checks or diagnostics before accessing enum members.
- `ReplayInputRequest` claims recursive immutability but wraps only the top-level dictionaries. Actual `request.bot_identity['body']['review_mutation']='changed'` succeeds, and recomputation differs from the stored request fingerprint. `persist_replay_request` then returns `Ok` and writes these changed bytes under the stale original fingerprint in a fresh root. The resolver later rejects the mismatch, but persistence itself falsely acknowledges a content-addressed artifact. Freeze nested bot/assignment/scope values and recompute the identity before any write.

Actual filesystem positive `test_durable_request_resolves_registered_split_and_manifest_bound_bot` was independently invoked and passed before applying its held-out nested mutation. It proves persisted CT12/CT10 refs reach the selected manifest-bound QML hosted callback, not child Book or economics.

Expanded command: `.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_alternative_execution.py packages/qmf-data/tests/test_splits.py packages/qmf-data/tests/test_source_boundary.py packages/qmf-data/tests/test_seal.py qmb/tests/test_replay_materializer.py qmb/tests/test_ql7_host.py` — **122 passed**, 2.55 seconds. Remaining findings were sent directly to root and execution owner. No full-chain approval.

## Final bounded corrective verdict

**Approved for the bounded registered-policy ATC and immutable persisted-request seams**, after ATC correction `99863c9f4c1f7bc7b743a4f1bb51f723d00425b2` and request correction `3f964d1c758df035af6a66bd2e9ed26f0823d363`, on top of the preceding candidates. The historical changes-required findings above are closed within this scope.

Independent wrapped-real-append controls for string `event_type`, `world`, and `outcome` now each yield typed refusals. Actual persisted request positive was repeated; nested CT33 body mutation raises `TypeError`, its fp1 recomputes correctly, and `replace(request, stream_id='changed-stream')` refuses persistence before creating the configured request root.

Additional actual ATC negative controls refuse malformed grant token `['']`, blank health reference, health revision 0, LIVE source world, and mismatched host epoch. A callback returning and retaining a mutable nested accounting graph was accepted after normalization; subsequently mutating its original nested list to 999 leaves the result tuple `(2,)` unchanged and its recomputed fp1 intact. The existing internal-simulation admission parser permits an empty list of checked grants; this review proves malformed token/health/epoch checks, not an external grant or health authority resolver.

Final combined command adds `tools/tests/test_release_install.py` to the expanded command above: **140 passed**, 3.07 seconds. Installer snapshot source was still uncommitted in that run, so its approval is separately bound when its source commit is available. No financial-example grammar, provider, optimization, Book partial-fill, child economic CLI, or final installed-bundle acceptance follows from this bounded verdict.
# Corrective follow-up: strict typing and rich metadata

Independent bounded review binds `6c6abda0e45583e09af309ca8ef70e1d6835aec2` (ATC trust-boundary typing) and `aa9d595a37b9524c3e47320a6123781f79364e17` (full pinned price-metadata identity retention). **APPROVED for these corrective deltas only**; earlier full-product limitations remain.

Inspected both commit diffs. `.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_alternative_execution.py qmb/tests/test_ql7_host.py` passed **19 tests**, including complete actual persistence/reopen positives, missing/string ACK refusal, false physical receipt and malformed typed event enum refusal.

Additional independent controls wrapped actual successful physical appends, replacing either the typed receipt's `event` or `store_receipt` with None/string. All four returned typed refusals without attribute errors; actual writer sequence remained one, truthfully reflecting the already completed append. The actual filesystem rich-metadata durable-request positive passed. A separate metadata identity with nested list content retained its original immutable tuple after caller mutation, recomputed to the exact original fingerprint, refused nested assignment, and rejected the changed identity paired with its stale fingerprint. Full metadata content now survives request serialization instead of being narrowed to instrument/scale.
