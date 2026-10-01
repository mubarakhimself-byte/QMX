# Frozen retry5 independent review — FAIL

2026-10-01. Independent Sol bounded ordinary public-ingress, retry, and durable accepted-work review. Execution confirmed the five hashes below were frozen; the diagnostic checked all five at entry and exit. No product/test edits, commits, provider calls, credentials, or security testing. Owner repair after these findings is a new slice and does not change this verdict.

## Findings

**P1 — accepted continuation is not bound to the accepted input/context.** `sessions/product_session.py:2108-2140` accepts work by logical invocation and grant only; the accepted event adds an attempt but no input hash or approved envelope/context. `sessions/grant_binding.py:273-277` persists only `(logical_invocation_id, grant_id)` and hydration at `product_session.py:1884-1893` restores only that pair. The ledger's revoked-grant continuation exception consequently recognizes different work as the old accepted invocation.

The actual authenticated public CT-40 route first accepted `run_fp1=fp1:sha256:aaa…` with full hash `fp1:sha256:2572decfc2c7e51a0391bd3001ead31902981675e6a78e562fa83169b8b5d4b4`. A second public request kept the same logical invocation, attempt 1, idempotency key, session and grant, but changed run to `ccc…` and correctly recomputed hash `fp1:sha256:303f461ba47d6149d7bb484cac9a2b4168cc3766a179ff5e816117028a7bdd7e`. Both returned success and invoked the local read executor, and journal acceptance attempts were `[1,1]`. This is not a bad supplied hash: each request independently passed the full input hash check, while the accepted identity lacked a durable original hash to compare.

A separate physical substrate close/reopen with a revoked grant provided the continuation boundary control. The exact original `run-1`/hash was allowed, as required. A different `run-different`/different correct hash was also dispatched to the callback using the same accepted invocation and revoked grant. The actual reopened accepted row was only `['inv:1','grant:1']`. Thus persistence preserves the grant exception but loses the exact accepted work it was meant to protect. This is a local correctness regression; it is not security testing or a claim about a real provider/domain result.

**Required correction:** persist and revalidate the complete accepted invocation binding, including original full validated input/hash, operation/version/effect, contribution/version, instance/config revision, caller/session/principal context, grant snapshot/context revision, idempotency/logical identity and authoritative attempt progression. Same accepted work may finish after revoke/expiry; changed work must not inherit that exception. Do not overwrite an existing accepted identity with a new request. Preserve physical reopen behavior and refusal before executor/acceptance effects. Existing old projection rows without sufficient proof need an explicit migration/refusal rule, not invented missing context.

**P2 — supplied attempt 2 is treated as initial accepted work without predecessor authority.** `process.py:2849-2867` calls `accept_work` whenever the current attempt equals the caller's supplied initial attempt, including 2. `accept_work` permits every positive integer. The existing loop ceiling constrains the number, but supplies no durable predecessor identity. A fresh public invocation with registered ceiling 2 and envelope attempt 2 executed successfully, journaled its first and only acceptance at 2, and had no attempt 1. The identical positive control at attempt 1 succeeded with journal `[1]`.

Main SCN-0021 requires monotonic attempt ids; SCN-0026:35 and ADR-0025 DEC-0457 place incrementing retry on the host and same logical invocation. CT-40 does not by itself explicitly decree that every client envelope must start at 1. A lawful resumed higher attempt may exist, but it must be backed by authoritative prior accepted work/progression. This implementation accepts the caller's number as that authority. Even `record_retry_attempt` checks only the caller-provided arithmetic pair `previous+1`, not a persisted last accepted attempt. The observed `[1,1]` reset in P1 is another concrete monotonicity failure.

**Required correction:** distinguish first admission from validated continuation. Refuse a fresh higher attempt or require actual authoritative predecessor state; let the host increment from that state exactly once. Reject reset, duplicate progression, skip, regression, changed context/hash and foreign predecessor before effects. Do not blanket-reject legitimate resumed higher attempts if the contract supports them. Use the real stored attempt, not `supplied_attempt-1`, for a continuation claim.

## Passed controls and practical limits

- Frozen focused tests: from `qmx-agents/packages/qma-daemon`, `uv run --no-sync python -m pytest -q -p no:cacheprovider tests/test_product_session_host_retry.py tests/test_product_session_grants.py tests/test_j_kit_06_host_retry.py` — **17 passed in 0.60s**.
- Relevant existing host loop controls: same working directory, `uv run --no-sync python -m pytest -q -p no:cacheprovider tests/test_host_retry.py` — **18 passed in 0.56s**. These cover registered ceiling, none/read retries, retryability NO, zero pack retries, reconcile policy, CAS conflict, unknown-blocked and external egress. They exercise existing loop/fixtures, not new actual operation owners.
- Existing core effect matrix: from `qmx-agents/packages/qma-core`, `uv run --no-sync python -m pytest -q -p no:cacheprovider tests/test_effect_outcomes.py` — **13 passed in 0.13s**.
- The new frozen public-route test genuinely invokes the normal paired CT-40 dispatcher, uses live roster/session/grant creation, persists `[1,2]`, and allows the in-process accepted read to retry after grant revocation; missing ceiling has zero executor calls, nonretryable read takes one call, PLACE_RUN transient refusal takes one call. Its operation executors are explicit local doubles: this is not normal registered QMA-to-QMB publisher proof.
- The finite diagnostic's healthy attempt-1 positive and same-input reopened revoked continuation positive both pass, so each failure reaches the intended boundary. No broad quota-filling tests were added. Whole coupled QMA producer/persistence, normal installed end-to-end behavior, arbitrary concurrent/restart retry recovery and complete security approval remain pending.

## Frozen source binding

Paths are relative to `qmx-agents/packages/qma-daemon`:

```text
add57144f49d49679354d13db4c99c463415f645b354eb44be6c9ab19537bc2f src/qma/daemon/process.py
37cca45c857200d840b5d140f1e8ff17626855e4e3f44d170ee4d1653e76fdbd src/qma/daemon/sessions/product_session.py
439a9cb28e98a014e1903f793038eff8aba93de58aa311b9f15388e701c79564 tests/test_product_session_host_retry.py
306a9cb17bcf09600298663e4ef391f09abd1a6d3716a1b5e261fd218dd312a2 tests/test_product_session_grants.py
8ce5663194b3b4173ac34330c14bb668967322db29ddc3711f80d5d140c96ba6 examples/product_session_grants_usage.py
```

All diagnostics are retained under `/workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics`. Exact command, from the daemon package directory: `uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_retry5_public_identity.py` — exit 0, produced the factual failing outcomes above. The script reuses the existing frozen public test's genuine setup and injects only local healthy operation callbacks; its paired connection is the fixture's initialized WireConnection, not a real external authenticated network principal.

```text
d4c033bb8234110910543e998772ca8739c5d6e843f7225574fa150916b40083 review_retry5_public_identity.py
ef5c0ef8989ea6b580c50a5887713756b65f93903e32e60f942ec7cfe3c00eb9 review_retry5_public_identity.results.json
```

Execution and the coordinator were notified before corrective editing. These are FAIL findings on the original held bytes; later repairs require a new exact hash review.

## Corrected retry5 re-review — FAIL, 2026-10-01

This is a separate bounded review of Execution's explicit latest hold. The earlier corrective session/grants hashes `34e146…`/`376ae6…` were superseded before this active diagnostic; this review uses hydration-first `f843b2…`/`92da64…`. All five hashes below matched diagnostic entry/exit and the final report census. No source/test edits or commits.

**P1 remains at the shared public continuation boundary.** The normal process now refuses a changed-input duplicate start and a fresh attempt 2 before executor/acceptance effects. Its accepted journal event retains a canonical `binding_fp1`. However, `product_session.py:1262`, `1876-1989`, `2198-2356` retain/hydrate only grant, fingerprint and attempt, rather than a reconstructable complete accepted authority binding. `dispatch_public_call` at `2470-2585` evaluates the accepted logical/grant exception and dispatches the newly validated request without comparing that request with the original accepted binding or requiring authorized persisted progression.

The finite control first obtains a genuine validated BoundInvocation using the shared dispatcher and official stores, computes the same descriptor/envelope/validated-payload fingerprint body as `process.py:2867`, accepts attempt 1, revokes the grant, physically closes journal/SQLite, then reopens both. Direct `record_retry_attempt` for 1→2 with the original fingerprint succeeds. Duplicate 1→2, skip 2→4, reset 1→2 and wrong-fingerprint 2→3 refuse. The same-input shared dispatch positive then executes `run-1` with input hash `fp1:sha256:29ccb612dd33e32a291b4542c3b52fc7eacc516e93d4197a3053e53b77aea31b`. A changed-input dispatch also executes `run-different` with its correctly recomputed hash `fp1:sha256:f16400f2d421f8caa5d8cb7e80ad64fbdb2fe46cea5c6cb710d155b4787ecefc`, on the same accepted logical/grant. Both supplied attempt 3 without an accepted attempt-3 event. Each reaches its callback; this is not an invalid supplied hash.

The accepted journal contains exactly attempt-1 accept and attempt-2 retry payloads with fingerprint, grant, logical id and moment. The full body in the diagnostic result is independently reconstructed diagnostic data, not persisted product evidence. In a second service using the reopened SQLite projection without journal proof, direct retry correctly refuses, but shared dispatch of `run-legacy-different` still executes under the same revoked grant. Thus the missing-proof refusal is not enforced at every continuation entrypoint.

**Correction required:** persist the complete accepted authority binding (including approved session/context/grant and original validated full input) and reconstruct/revalidate it on physical readback. Gate every public continuation/helper before executor effects on exact accepted-work equality and persisted next-attempt authority. Legacy insufficient-proof state must receive a scoped typed refusal at dispatch too. The process-only duplicate-start fix and matching caller-supplied fingerprint do not establish that shared contract. The original P2 fresh higher-attempt/unchecked direct progression is corrected in the exercised controls; that does not resolve this P1.

**Validation:** from `qmx-agents/packages/qma-daemon`, `uv run --no-sync python -m pytest -q -p no:cacheprovider tests/test_product_session_host_retry.py tests/test_product_session_grants.py tests/test_j_kit_06_host_retry.py` — **17 passed in 0.73s**. Diagnostic command: `uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_retry5_public_identity_corrected.py` — exit 0, observed outcomes retained. Healthy normal attempt-1 executes once; fresh normal attempt-2 produces invalid-input with zero executor/accepted events; changed normal duplicate start refuses with only the original call/event. These meaningful positives/refusers distinguish the fixed process path from the residual shared continuation failure.

Latest source binding, paths relative to the daemon package:

```text
5e4fb10a04bf644122130e75c50dd5f13dac527d70719c55494747e489bb08c4 examples/product_session_grants_usage.py
e21661f28b850d095e4135fab7814f6951b9a55c5338ce1ca3b0a588daedc58f src/qma/daemon/process.py
f843b2f2d228e4e7134085c54ef826441dbd6b236109a154df6d173b068eaab7 src/qma/daemon/sessions/product_session.py
92da644d05f7c72fcca9f3f872f660b64f64a292fed6e47cf82ff7c4d467e93b tests/test_product_session_grants.py
0b85491a0290ca040d9ebcdf79d759b5ef5f22249b3059f60b815e5740636480 tests/test_product_session_host_retry.py
```

Archived program/results/argv/source notes:

```text
1c07ec9a8f149cecc331142bcb6852ba2a51965daee9420b7ad2c7f75dbc214c review_retry5_public_identity_corrected.py
2f83b2a0012f232a7ff661fcbcc4e75af8d216068f77336cde99282a96288241 review_retry5_public_identity_corrected.results.json
4861db3e07e89f22dbb39ac4395bab5ff705651f784881969a6715d4822defe6 review_retry5_public_identity_corrected.notes.json
```

Execution and the coordinator received the residual finding before any repair. No complete coupled QMA persistence/normal publisher, provider, restart concurrency, security or release acceptance is implied. Any corrective source changes require release of this hold and a new exact frozen re-review; earlier FAIL evidence remains intact.

## Corrected retry6 re-review — shared continuation FAIL, 2026-10-01

Execution's six-path hold matched at diagnostic entry, exit and report census. This review preserves the earlier failures and distinguishes the corrected normal process from the shared execute-callback API. No product/test edits, commits, provider calls, credentials or security testing.

**Corrected controls PASS:** `accepted_invocation_binding` now retains a complete canonical body: approved session/context, descriptor, contribution, instance/config, original grant snapshot, envelope identity and validated full input. Its fingerprint is recomputed on journal hydration; actual persisted bodies, not diagnostic reconstructions, survive physical journal/SQLite close and fresh reopen. Matching revoked accepted work may continue. A correctly rehashed different input refuses before the shared callback; SQLite-only accepted projection without journal binding proof refuses both direct retry and shared dispatch. Fresh normal attempt 2, changed normal duplicate start, direct duplicate/reset/skip and wrong-body-fingerprint progression refuse. The new existing test also supplies a correctly recomputed changed whole-body fingerprint and verifies direct retry refusal, so this does not rely only on rejecting an internally inconsistent supplied fingerprint.

**P2 — shared execute dispatch checks but does not consume the next persisted attempt.** `product_session.py:2802-2820` checks that the supplied attempt is `prior.attempt_id + 1`, then directly invokes `execute(invocation)`. It neither calls `record_retry_attempt` nor advances/persists an equivalent authority record. Starting with genuine original accepted attempt 1, revocation, physical reopen and an authorized direct 1→2 retry, the finite diagnostic calls the shared API twice with the exact original payload/hash, same logical identity, grant and attempt 3. Both succeed and each calls its local executor once. The journal still has acceptance attempts `[1,2]`; no attempt-3 event was appended. The second callback therefore repeats the same purported next attempt instead of incrementing from consumed durable authority. A different correctly hashed payload at attempt 3 refuses with zero callback calls, proving that the remaining issue is progression rather than accepted-input equality.

Main `SCN-0026-host-retry.md:35` assigns incrementing attempts on one logical invocation to the host; the shared implementation itself promises a “next host-owned read attempt.” The current shared method documents binding/resolution/refusal and accepts an ordinary `Callable[[BoundInvocation], None]`; it does not state or enforce a callback-owned persistence prerequisite. A binding-only call with `execute=None` can remain a preflight. A call that actually executes needs a supported protocol which durably admits/consumes the exact attempt before effects and makes repeating it refuse. Merely checking the unchanged predecessor each time does not prove progression. Execution was asked to clarify callback ownership before repair; no whole shared retry6 PASS is assigned to an undocumented caller obligation.

**Normal process bounded PASS:** its execute callback independently calls `accept_work` or `record_retry_attempt` before `_execute_bound_product_operation`, so the observed shared callback issue does not demonstrate a remaining duplicate-attempt execution in that actual process route. The meaningful healthy normal attempt-1 control executes once and journals its complete original binding. The existing normal host retry fixture persists `[1,2]` with registered ceiling and accepted read continuation after revoke. Local operation callbacks remain doubles; none of this is normal registered QMA-to-QMB publisher/domain proof.

Validation from `qmx-agents/packages/qma-daemon`:

```text
uv run --no-sync python -m pytest -q -p no:cacheprovider tests/test_product_session_*.py tests/test_host_retry.py
59 passed in 0.80s
uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_retry6_public_identity_corrected.py
exit 0; observed shared same-attempt callback repetition retained in results
```

The test glob expanded in the shell. Actual diagnostic controls include original BoundInvocation/official complete binding, real accept/revoke/journal/SQLite reopen, direct exact progression, same-input callback positive, its same-attempt repetition, different-input refusal and missing legacy proof refusal. Complete binding/input/context fixes are credited; the shared progression boundary remains FAIL. Whole coupled QMA producer/persistence, installed end-to-end execution, concurrent retry arbitration, provider/security and release acceptance remain separate pending work.

Frozen source paths relative to the daemon package:

```text
e86d8ad6219377f88cdb80d862ad255e8724694040e14031a0770f969c4d7103 src/qma/daemon/process.py
68563a573c4ea7d7051b1a69b1f6d8f2b16c633b93bf424c0cd38f99983a6bb4 src/qma/daemon/sessions/product_session.py
de3fd329e6f91ee0b592fd29e1c74e2b0e0c2b4d25e953cb09c765ffdceeefe7 src/qma/daemon/sessions/__init__.py
969d7026bce179e6b3328e45eb424a9aa09c60aa363e24f88c1edf87c0f45699 tests/test_product_session_grants.py
0b85491a0290ca040d9ebcdf79d759b5ef5f22249b3059f60b815e5740636480 tests/test_product_session_host_retry.py
01dfae31c3621c1fb8d2badbe8c4b4da0cd4ae9d0a5b3b17b7e0e78ff87311f2 examples/product_session_grants_usage.py
```

Preserved diagnostic binding in `/workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics`:

```text
6aaf833ab991bec82df479ef5fecf9f1fea8e9745f1f32f10433f4310080b9ef review_retry6_public_identity_corrected.py
004be222ba36a87642d64c3375f68b4e61a6bcfc474fd8255c881bbf201d5229 review_retry6_public_identity_corrected.results.json
139b9b1624735643baed91aacb803747c55fd7fca6eeff64dd36aef66d64166c review_retry6_public_identity_corrected.notes.json
f1c668466938fd99019709a9f46d47faf92cd06bea1b12b8fdaac8ce7c8d023d SHA256.json (archive snapshot at this review)
```

The coordinator and Execution received this finding while the held source was unchanged. Corrective editing requires coordinator release and a new frozen exact review; it cannot retroactively change this outcome.
