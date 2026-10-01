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
