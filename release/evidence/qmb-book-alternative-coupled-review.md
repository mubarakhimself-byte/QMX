# QMB Book/Alternative coupled independent review

2026-10-01. Independent GPT 6.1 Sol review, attended local release lane. **FAIL: two P2 exact-type defects remain in the frozen Book adapter.** The 24 existing tests passed; shared-context refusal, real local Book producer/readback, missing-witness refusal, and invocation-to-terminal attribution checks passed within this bounded slice.

This review covers ordinary identity and persistence contracts in the 13 files below. It used registered local recorded fixtures and explicit local execution doubles. No product/test files were edited; no commits, network/provider calls, credentials, push, deployment, or security testing were performed. The governing attended repository instructions were retained. Prior nominal-context failures are superseded only for the exact corrected hashes reviewed here; unavailable prior security review remains pending.

## Frozen source binding

All 13 SHA-256 values matched `/workspace/qmx-qmb13-held-review-manifest.json` at entry and at completion. Repairs after completion require a new freeze and re-review.

| File | SHA-256 |
| --- | --- |
| `qmb/src/qmb/doors/cli/__init__.py` | `31e366fbfd03629864e8420911fc159ef00819449d782ac1babaa59753989e65` |
| `qmb/src/qmb/host/qma_cli.py` | `db7c7b1b754bcfd7078224b03eebc3971bc3c598ab16ee1181270cc4fe608121` |
| `qmb/src/qmb/host/operator_replay.py` | `601b7bd3cb49d5c17b47a42419430c340c9d1cdd4999dd670725e6c84b5d2c04` |
| `qmb/src/qmb/host/operator_alternative.py` | `09a7e06141d77bf41ce4b49fe28883c08e8da1144d7b58b8a73e9a08c7e9ba7f` |
| `qmb/src/qmb/host/operator_alternative_replay.py` | `6c32d2e3bff0e25c3799c31461ffa56c25959471e8bea34e6aea85f020125588` |
| `qmb/src/qmb/host/operator_occurrence.py` | `46ef1b4d81440a2752bb1ad0d0e37b6c8fb5ad2180aac97108b56692db8f1df8` |
| `qmb/tests/test_qma_cli.py` | `ad309e68730a2bfdf8e84da139b0c4fb316a8a2ab5397f251cfd28124728a659` |
| `qmb/tests/test_operator_replay.py` | `fedee09506b68f1579dd4b00389847fa088f34ba11e9f1a8c907ac13bcce7bd2` |
| `qmb/tests/test_operator_replay_process.py` | `6da7831723e4f81d63127deb4cf40b1466bdf1d72b567e1233a22d1ac95199fe` |
| `qmb/tests/test_operator_alternative.py` | `c6c632e6f1541d293fd055b5b90a703dd724019aa2c3f0f7de4a9f618b7a6b0a` |
| `qmb/tests/test_operator_alternative_replay.py` | `766fd1983a02d6a0a36b9d55762454db4530ef6af6ce4a38b8677912e8979f15` |
| `qmb/tests/test_operator_alternative_cli_journey.py` | `6b033cc0f5ce92608386d13918ae4533afb88949a522c1a3ac7e4a8ef1c0733f` |
| `qmb/tests/test_operator_occurrence.py` | `f237ed6e22a72e697b906b51f1d2e8966427373fa8cf863d4b64103cfbda1458` |

## Findings

1. **P2 FAIL — Book verification accepts a boolean attempt in a claimed result.** At `operator_replay.py:282`, ordinary Python dictionary equality compares the claim with the trusted result. `True == 1`, so replacing only `attempt_id: 1` with `attempt_id: true` in an otherwise genuine persisted Book result is accepted. Both the direct verifier and the actual `.venv/bin/qmb backtest run` child with `QMA_QMB_VERIFY=1` and the boolean JSON claim succeeded; child exit status was 0 and it returned canonical integer attempt 1. The genuine context and producer witness still belonged to attempt 1, and journal/ledger file hashes did not change, so this finding concerns false approval of an exact transport claim, not reassignment of a terminal. Require exact field types as well as values, or canonical identity comparison, before approving the claim. Alternative result validation already requires the attempt's exact integer type.

2. **P2 FAIL — Book descriptor decoding accepts a boolean format version.** At `operator_replay.py:384`, checking `format_version != 1` accepts `True`. A local genuine persisted descriptor changed to JSON `format_version: true`, with its content fingerprint correctly recomputed and the context pin updated to that fingerprint, was accepted by `read_operator_replay_binding`. This is a supported-format contract defect even though the descriptor remains operator selected and content addressed. Require `type(format_version) is int` and value 1 before accepting the descriptor. Alternative descriptor decoding already enforces the integer type.

Both findings were sent to the coordinator and Execution owner. No current full PASS is implied by the positive results below.

## Commands and results

Working directory: `/workspace/QMX-release`. Existing-suite command:

```sh
PATH=/workspace/QMX-release/.venv/bin:$PATH uv run --no-sync pytest -q -p no:cacheprovider qmb/tests/test_qma_cli.py qmb/tests/test_operator_replay.py qmb/tests/test_operator_replay_process.py qmb/tests/test_operator_alternative.py qmb/tests/test_operator_alternative_replay.py qmb/tests/test_operator_alternative_cli_journey.py qmb/tests/test_operator_occurrence.py
```

**PASS: 24 passed in 15.08s.** This includes actual local child preflight, execution and claimed verification for Book, and actual Alternative CLI execution followed by claimed and claimless durable verification. These use editable checkout entrypoints and local doubles, rather than a final installed release or provider-backed QMA worker.

Preserved ordinary local review programs were run with:

```sh
PATH=/workspace/QMX-release/.venv/bin:$PATH PYTHONPATH=/workspace/QMX-release/qmb/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_qmb_context_nominal.py
PATH=/workspace/QMX-release/.venv/bin:$PATH PYTHONPATH=/workspace/QMX-release/qmb/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_qmb13_context_boundaries.py
PATH=/workspace/QMX-release/.venv/bin:$PATH PYTHONPATH=/workspace/QMX-release/qmb/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_qmb13_book_witness.py
```

An initial nominal-program invocation without the test-support `PYTHONPATH` failed to import `replay_fixture_support` before fixture execution. The corrected command above passed. The new programs assert the full frozen source manifest before and after their work.

| Check | Result and evidence |
| --- | --- |
| Genuine persisted descriptor | PASS; the archived prior nominal-context program reads the genuine descriptor successfully, then rejects all six prior malformed-field cases without an exception. |
| Shared context before adapters/builders | PASS; 133 controls across Book read/execute/verify and Alternative presence/read/execute/verify reject malformed spec/evidence/split fingerprints, non-boolean mode, boolean/zero/string attempts, empty/non-string job/environment/occupancy, and malformed descriptor pins. Builder seams would raise if reached; there were zero builder calls and the complete fixture file census/hashes remained unchanged. |
| Genuine Book producer and terminal readback | PASS; the actual production replay service on the local recorded fixture produced CT-32 and its unique confirmation LedgerLine, reopened them, wrote the private CT-13 occurrence, then both claimed and claimless public verification succeeded. Verification left journal/ledger file hashes unchanged. |
| Existing Book terminal cannot be reassigned | PASS; changed job, integer attempt, environment, or occupancy is refused in both claimed and claimless verification (eight controls). For job/attempt, the claimed response was correspondingly relabeled, rather than relying on a trivial unchanged-claim mismatch. Journal/ledger census and hashes remained unchanged. |
| Missing producer witness after real Book CT-32 | PASS; a local refusal injection at `record_operator_occurrence` let the actual replay service produce and reopen one real CT-32/confirmation row but prevented the producer witness. Execution returned refusal. Both otherwise correct claimed and claimless public verification refused the terminal, with journal/ledger file hashes unchanged. This is an explicit local persistence refusal injection, not normal producer success. |
| Book claimed attempt exact type | FAIL; boolean claim accepted by direct verifier and actual CLI. |
| Book descriptor format exact type | FAIL; boolean version accepted with an internally consistent content hash and pin. |
| Alternative identity/readback | PASS within existing tests and static review; foreign split/descriptor are refused before CT-13 decisions, a foreign source claim is refused, and genuine claimed/claimless verification reproduces the persisted terminal while retaining identical journal bytes. Attempt and format fields use exact integer guards. |
| Private occurrence invariants | PASS within existing tests and static review; malformed nominal occurrence identities refuse before append, a legitimate occurrence is idempotent and physically reopened, foreign job and conflicting terminal witnesses refuse. |

## Static persistence joins and scope

Book public adapters first call the shared exact nominal-context validator, before fingerprint dereference, descriptor selection, builder materialization, or verification. The descriptor ties spec/evidence/split, roots, registered CT-06 records, policy identity and builder bytes to its content fingerprint and context pin. Runtime checking ties the resolved config to the descriptor, canonical CT-22/CT-27 fragments, registered bot/Book/BMS references and resolved persisted request/split. The normal producer executes the shared replay service and compares the reopened CT-32, terminal-line fingerprint and run identity with that execution before writing its occurrence.

Book occurrence identity binds the full context, descriptor/binding fingerprint, exact CT-32 and terminal-line fingerprints, binding epoch, writer/stream and roots. Its timestamp uses the resolved recorded source's final observation frontier. Thus source/config joins are carried through the pinned request, config, descriptor and cited terminal rather than unrelated response labels. The private CT-13 readback checks the canonical expected occurrence payload, correlation key, instant/world/writer, event fingerprint and exactly one matching physical journal row. Public claimed and claimless verification both require this witness; the producer's private staging readback precedes witness creation and is not exposed by the CLI.

Alternative resolves its exact registered source/config/interpreter/owner epoch and operator roots before execution, reopens the domain terminal, writes the same private occurrence class and requires its readback during result validation. Verify-only rebuilding reads matching durable terminal material and checks its decision references and occurrence without invoking the policy evaluator. The previously separately approved actual Alternative CLI one-evaluation counter is not a new normal QMA execution proof in this review; this run did not repeat that separate counter diagnostic.

The two exact-type findings prevent approval of this complete frozen slice. Full coupled QMA persistence, normal automatic worker/pump execution, provider behavior, final installed entrypoints and final same-commit release builds/installs remain separate pending work. Security review remains separate and unapproved; this ordinary local review does not replace the previously unavailable security lane.

## Preserved diagnostics

Archive: `/workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics`. Temporary local fixture trees were removed at the programs' normal completion; reproducible programs, exact argv/source bindings, results and prior diagnostics remain in the archive.

| Artifact | SHA-256 |
| --- | --- |
| `review_qmb13_book_witness.py` | `559105e4bb6a985f831cce427817d541d4263d3e7c0f44a0468690b8dd0aeb0d` |
| `qmb13-book-witness-results.json` | `2340a254aff5d6b54467ab884cc4d7334ecf1f476a5145ce0e5a4af7da02cd8c` |
| `review_qmb13_context_boundaries.py` | `a8d5c91e62c36a566b0d8d38eb7f9a5eb72b7e59e23460cc421affe854d5f75f` |
| `qmb13-context-boundaries-results.json` | `f43f70d10905c239b3f316c26b552f6bda5f76e79f7b60f40012221c3b4e18b3` |
| `QMB13_REVIEW_ARGV_SOURCE_NOTES.json` | `65f635cdd661dffb7ac950d863588843b899b8460ef407e107095a3217a61942` |
| `SHA256.json` at completion | `98aeebd5c8600b39c3aec830c51047e25e0301a143f27093a184bc4a86a8ad9e` |

## Corrected Book13 re-review — 2026-10-01

**PASS within the corrected frozen 13-file slice; both prior P2 findings are resolved at these hashes.** The historical FAIL and its original diagnostics above remain unchanged. This append supplies no complete candidate, normal registered QMA, provider, installed release or security approval.

The exact manifest `/workspace/qmx-qmb13-book-corrected-review-manifest.json`, SHA-256 `edfe133c2cdc421d913a8b16c0a4d5f0a0405c5c75e991908a4ea37b53ce10e6`, matched all 13 files at entry and completion. Only the three hashes below changed from the earlier table; the other ten match that original frozen table exactly.

| Corrected file | SHA-256 |
| --- | --- |
| `qmb/src/qmb/host/operator_replay.py` | `a92ab0c1c1cb20e932ef281d7f3de73e030b661800c1bc030d23d64e46fb2650` |
| `qmb/tests/test_operator_replay_process.py` | `2d118fed357e40158eb9b29deb30f54ea88d3c844657d0b55340d7c31d32a1c4` |
| `qmb/tests/test_operator_alternative_cli_journey.py` | `fdc2f880f1ca65aae1d728e9ef772db4489d04b7e6ebb37d1486c4f30dc43e42` |

Source review confirms `_matches_terminal_claim` now requires the complete exact key set and exact runtime type plus value for every field in the flat Book claim. It cannot conflate boolean/float attempts with integers. Descriptor decoding requires exact integer format version equal to `OPERATOR_BINDING_FORMAT_VERSION` before identity parsing or builder execution. The shared-context validation and producer/readback/occurrence ordering are preserved.

Exact existing-suite command, working directory `/workspace/QMX-release`:

```sh
PATH=/workspace/QMX-release/.venv/bin:$PATH uv run --no-sync pytest -q -p no:cacheprovider qmb/tests/test_qma_cli.py qmb/tests/test_operator_replay.py qmb/tests/test_operator_replay_process.py qmb/tests/test_operator_alternative.py qmb/tests/test_operator_alternative_replay.py qmb/tests/test_operator_alternative_cli_journey.py qmb/tests/test_operator_occurrence.py
```

**PASS: 25 passed in 17.78s.** The actual Book CLI test retains genuine attempt 1 execution and matching claim verification, refuses a boolean attempt claim, and the new actual CLI preflight test refuses a correctly rehashed boolean descriptor version with no terminal ledger row.

The archived original review programs and results were retained. Corrected copies change only the source-manifest binding and separate result filename; the Book copy additionally asserts the expected repaired refusals and nonzero actual CLI exit. This repeats the same bounded ordinary identity/persistence controls, without product/test edits or new provider/security activity:

```sh
PATH=/workspace/QMX-release/.venv/bin:$PATH PYTHONPATH=/workspace/QMX-release/qmb/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_qmb13_book_witness_corrected.py
PATH=/workspace/QMX-release/.venv/bin:$PATH PYTHONPATH=/workspace/QMX-release/qmb/tests uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_qmb13_context_boundaries_corrected.py
```

| Repeated control | Result |
| --- | --- |
| Genuine Book producer, claimed and claimless readback | PASS; the real production replay service on the recorded local fixture persisted CT-32, unique confirmation LedgerLine and its producer occurrence. Both verification modes accepted; verification kept journal/ledger hashes unchanged. |
| Prior boolean attempt claim | PASS refusal; direct verifier refuses `True` for integer attempt 1. Actual `.venv/bin/qmb backtest run` verification exits 1 with `terminal_result` policy rejection. Journal/ledger hashes remain unchanged. |
| Prior boolean descriptor version | PASS refusal; the descriptor's hash and context pin were correctly recomputed for JSON `true`, so refusal cannot be explained by stale identity. |
| Other invocation attribution | PASS; all eight claimed/claimless job/attempt/environment/occupancy changes refuse with unchanged journal/ledger hashes. Relabeled job/attempt claims do not turn a foreign invocation into success. |
| Real CT-32 without producer witness | PASS; the same explicit local persistence-refusal injection omits the occurrence after real CT-32/terminal creation. Both claimed and claimless public verification refuse, without further journal/ledger changes. |
| Nominal shared contexts | PASS; 133 malformed cases across all seven Book/Alternative adapters refuse before builder calls. Complete fixture file census and hashes remain unchanged. |
| Existing Alternative CLI and occurrence controls | PASS within the 25-test suite; actual local recorded execution and matching claimed/claimless durable verification retain the earlier identity/readback behavior, and malformed/foreign/conflicting occurrence controls pass. |

The separately reported actual Alternative CLI one-evaluation counter remains evidence from a fixture QMA context, not a normal registered QMA operation/worker proof; this re-review did not repeat that separate counter diagnostic. Full coupled QMA persistence, normal card/graph publication and execution, pending Study integration, final installed release checks and provider/security lanes remain separate. Factory checks and coverage floors are unchanged. No source/test edits or commits were made by this reviewer.

Corrected diagnostics remain in the same archive, with exact argv and all 13 source hashes in `QMB13_BOOK_CORRECTED_REVIEW_ARGV_SOURCE_NOTES.json`:

| Artifact | SHA-256 |
| --- | --- |
| `review_qmb13_book_witness_corrected.py` | `17ddb61b36751ecb81ea731f3ae3891bb4c42cb9794d5b88d2aea5aceb8f68f5` |
| `qmb13-book-witness-corrected-results.json` | `b6fd80d202918abc9947dcea74d8b778c2d64cae712fafaf7ca1bf6424c6ab3c` |
| `review_qmb13_context_boundaries_corrected.py` | `40f79aeadb357465e10bbb1355b9de27a830ca7ea91f47ac27baa726e97ecee8` |
| `qmb13-context-boundaries-corrected-results.json` | `1f4eb22694dcda0ef4b18fbd8b2ab679d9b2468f2934ee820c6610f48d085d85` |
| `QMB13_BOOK_CORRECTED_REVIEW_ARGV_SOURCE_NOTES.json` | `2ed2c2bdcff7f5e3ec0f13b6f3cf71d778cba75619ba9a7db84fd5cefc0c0e27` |
| `SHA256.json` at corrected completion | `31a1b5a207a6f1730f01e08c9edc42813ba1c5de1b7432977ae5edfbc253b7dc` |
