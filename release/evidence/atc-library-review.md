# Independent ATC library persistence review

Candidate: `c68cbcfca4618ddea1808e755f46bf8aafa0e250`. Status: **CHANGES REQUIRED**. Product paths untouched; root-only Git. This bounded review finds two actual filesystem blockers and does not approve the complete requested ATC scope, CLI/QMA chain, node, or external provider behavior.

1. **Same-stream new boot cannot persist its valid terminal.** `/tmp/review_atc_boot.py` runs the existing registered exact fixture interpreter against actual persisted CT10/QMF JournalStore. Boot 1 executes and appends its terminal/CT07 occurrence successfully. Boot 2 on the same stream executes successfully with logical sequence 0 and physical row index 1, but terminal append refuses `journal_refs`. `alternative_terminal.py:705` uses `checked.value[seq]`, conflating per-writer logical sequence with physical stream order. Resolve the exact writer/sequence/event-fingerprint tuple independently, then check its physical index, exact row body and digest. Both boot positives must persist/reopen; foreign writer/body/index must refuse.

2. **Execution-complete / terminal-missing retry repeats actual effects.** `/tmp/review_atc_retry.py` calls actual `run_alternative_study`, lets its evaluator complete a real CT13 action, then injects terminal append refusal before terminal persistence. After restoring terminal append and starting a fresh stepper, the same generation 0 / ask 0 evaluator executes again. Calls are `[(0,0), (0,0), (0,1)]`; the first trial's actual CT13 stream contains two durable decision actions, and the resumed Study succeeds. `alternative_study.py:540` reads terminal artifacts before execution but does not reconcile a previously completed labeled CT13 trial whose terminal is missing. Persist execution intent/completion or recover a validated labeled decision chain; otherwise refuse pending reconciliation before repeating effects. Completed terminal read-before-tell alone does not cover this gap.

Both repros use the existing clearly labeled local registered policy interpreter and actual filesystem journal/registry persistence. They prove library behavior, not provider conformance or opaque financial-example grammar completeness. Findings and exact scripts sent directly to data and root.

Existing focused check: `.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_alternative_execution.py` — **15 passed**. Those positives include actual measures, proposal-bound policy variation, terminal CT13/CT07 reopen and cancellation/resume after a completed terminal. They do not override the two held-out failures. Further receipt/torn-tail/objective/lineage approval remains pending corrected candidates and independent retest.

## 1276a31b corrective bounded review

Candidate `1276a31b0d012c67a18e2ae86660dfc8cf5b41e9`: **PASS for the corrected two-boot terminal proof and conservative no-duplicate retry boundary**. This is not completed terminal-gap recovery.

Original `/tmp/review_atc_boot.py` now passes both actual boot-1 and boot-2 same-stream runs/terminal appends (boot-2 logical 0, physical 1). Source inspection confirms logical event lookup uses exact writer + sequence + event fingerprint, with independent physical-row proof.

Original `/tmp/review_atc_retry.py` now performs only one generation-0/ask-0 evaluator call and one durable decision; its fresh-stepper restart typed-refuses because the durable trial intent remains unresolved. `/tmp/review_atc_write_faults.py` independently injects refusal before and after actual intent/terminal writes: before-intent retry succeeds without duplicate evaluation; after-intent retry refuses with no evaluator calls; before-terminal retry refuses with one completed evaluator; after-terminal retry reads the completed artifact and succeeds with no duplicate first-trial call. All four controls use actual filesystem append bytes and actual Study execution. Completed-generation/cancellation resume positive remains covered by the real focused fixture.

`/tmp/review_atc_ack.py` independently corrupts real append acknowledgments: Ok(None), bool logical sequence, foreign correlation, nonempty edge receipts, absent StoreReceipt and bool format version each typed-refuse without AttributeError. Focused ATC suite **17 passed**. These scripts and source inspection corroborate the correction; no product edits or Git mutations.

Remaining explicit limitation: an unresolved durable evaluator intent safely blocks a restart even if no action occurred, and a completed CT13 action without terminal is not reconstructed here. Root requested checked reconciliation separately. The registered interpreter is a local fixture; full CLI/QMA/node/provider execution and financial-example policy grammar remain outside this approval.

## f68d7f7b checked reconstruction review

Candidate `f68d7f7ba64a4a0b235843e449f63b9a5d7249b1`: genuine complete CT13 trial reconstruction works without a second interpreter call, but **CHANGES REQUIRED** for same-label ambiguity.

Adapted original `/tmp/review_atc_retry_v2.py` to the explicit initial-state/writer and seven-argument callback API: after terminal failure, restart reconstructs trial 0 and executes only new ask 1; calls remain [(0,0),(0,1)]. This positive does not approve ambiguous recovery.

`/tmp/review_atc_extra.py` adds an actual durable second decision for the same writer and trial label, changing composition fingerprint and frontier input. Restart still reconstructs/tells trial 0 and evaluates ask 1, despite the extra conflicting trial evidence (three total durable decisions). `alternative.py:1282` filters labeled-event completeness by expected composition, hiding the same-label foreign event before checking extras. Census every decision owned by the pinned writer/trial label before filtering config/frontier; reject conflicting or extra lineage. Exact actual-store repro sent data/root; product untouched. Further fault/readback approval remains pending this correction.

Reviewer focused ATC/Study-driver/resume suite: **37 passed**. The independent conflicting-label recovery failure above remains blocking despite these green tests.

## 0fac48d6 independent reconciliation approval

Candidate `0fac48d6a361b558f40dd59ea11a210f9aefa28d`: **bounded PASS for complete checked-trial recovery and ambiguity refusal**, atop f68d7f7b. Original extra same-label foreign-config/frontier repro now refuses with calls [(0,0)] and two durable decisions; no recovered tell/new ask occurs. Source census includes all same-label checked DECISION rows before expected config/writer/frontier filtering.

Independent actual-filesystem controls:

- Original boot positive passes both writers; retry-v2 reconstructs missing terminal with no second trial-0 interpreter call.
- Cross-boot retry reconstructs terminal under original boot-1 writer; only new ask uses boot-2 writer, independently verified in both persisted terminal bodies.
- Before/after actual intent and terminal writes: pre-intent failure has no evaluator effect and safe retry; uncertain written intent with no decision refuses; completed chain before missing/uncertain terminal reconstructs; written terminal readback resumes. No duplicate first-trial evaluation.
- Before/after actual CT07 edge persistence: retry completes terminal/occurrence and evaluates only the new ask, with calls [(0,0),(0,1)].
- Eight actual malformed durable-chain controls alter before/after-state fp, output fp, source fp, split fp, interpreter registration, command epoch or frontier input. Initial execution and recovery each typed-refuse with exactly one first-trial call.
- Actual raw CT13 composition-body tamper under unchanged event fingerprint and torn terminal/intent JSONL tail both refuse recovery without reevaluation.
- Six real hostile append-ACK controls (None, bool sequence, foreign correlation, edges, missing StoreReceipt, bool format) still typed-refuse.

Scripts: `/tmp/review_atc_retry_boot_v2.py`, `/tmp/review_atc_write_faults_v2.py`, `/tmp/review_atc_edge_faults.py`, `/tmp/review_atc_bad_chain.py`, `/tmp/review_atc_raw_tamper.py`, plus original ambiguity/boot/ACK scripts. Reviewer ATC/Study-driver/resume suites **38 passed**. Existing actual cancellation/resume/objective-policy variation controls remain green. Fixtures are local registered policy interpreters with actual QMF persistence; no financial grammar/provider or complete QMA/CLI/node claim. No product writes or Git mutations.
