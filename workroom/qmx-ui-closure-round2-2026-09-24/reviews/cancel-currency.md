# R7/R9 round-two closure review — cancellation and build floor

**Verdict: pass for this UI architecture gate.** No blocking or corrective finding remains in the reviewed R7 cancellation contract or R9 build-floor contract. R1 and R8 remain preserved in the bounded regression check.

## R7 — closed as candidate

The authoritative spine and binding trace now describe one cancellation model:

- `ARCHITECTURE-SPINE.md:235` makes `dispatchCancel` the unique issuer, fences the request with `handle_id`, `logical_run_id`, `attempt_id`, `command_id`, and `expected_state`, and grants authority only to the operator of the immutable `originating_psess` recorded when the job is admitted. It explicitly denies authority from observation.
- `TRACE-MATRIX.md:22-24,28-36` uses the same product-session command namespace and the same starter-only authority. It also states that `queued`→`running` does not invalidate the same cancel command, an already-terminal handle records a no-op, replay with the same command is idempotent, and first durable terminal wins.
- `TRACE-MATRIX.md:44-46,53` carries those rules through cancel-vs-complete, lost-ack, two-tab, and duplicate-submit paths: cancellation stays requested until an authoritative snapshot is terminal; a lost acknowledgement is reconciled by query; retries reuse the command identity; and a terminal result is never repainted as cancelled.
- `BACKEND-DEPENDENCIES.md:32` names `cancel_job` plus `originating_psess` at admission as the QMA wire/daemon JobHandle amendment, including the nested-child dependency. `CHANGE-IMPACT.md:18,39`, `DELIVERY-AND-QA.md:12`, and `CLOSURE-MAP.md:22,49` consistently present this as named backend work rather than implemented behavior.

The prior contradiction between starter-only authority and observer authority is gone. The requested race boundaries are handled: starter versus observer, `queued`→`running`, already terminal, cancel versus completion, lost acknowledgement/duplicate delivery, and nested child handles. The starter/observer, state-advance, and nested-child cases remain contract statements rather than separate worked trace rows; that is thin future test evidence, but it does not create a second rule or block this architecture gate. `TRACE-MATRIX.md:10` accurately labels all tests unexecuted.

## R9 — closed as candidate

The selected runtime is consistently **Node.js >=22.12.0 <23.0.0** in the binding artifacts:

- `ARCHITECTURE-SPINE.md:109,273` states the exact floor and ceiling next to Vite 8.3.0, pnpm, and the stack seed.
- `DECISIONS-AND-OPEN.md:25`, `CHANGE-IMPACT.md:44`, and `CLOSURE-MAP.md:24` repeat the same range.
- bits-ui remains 2.19.3 in `ARCHITECTURE-SPINE.md:109,265` and `COMPONENT-CONTRACTS.md:20`; pnpm remains 10.x with `apps/qmx-ui/pnpm-lock.yaml` owned by the isolated-scaffold gate at `ARCHITECTURE-SPINE.md:274`.

This closes the earlier Vite-engine mismatch identified in `workroom/qmx-ui-closure-review-2026-09-24/reviews/currency.md:23-27`. The earlier `.memlog.md:34` entry saying “Node 22 LTS” is append-only history and is superseded in the same log by the exact range at `.memlog.md:43`; it is not a live build instruction. Exact dependency resolution, lockfile generation, `svelte-check`, and production build remain honestly unexecuted at the isolated-scaffold gate (`ARCHITECTURE-SPINE.md:109`, `CLOSURE-MAP.md:24`). No fresh web lookup was needed because the pinned Vite/plugin facts and the correction under review are unchanged from the prior primary-metadata check.

## Bounded regression and evidence checks

- R1 is intact: the rail still exposes Home, Copilot, Library, and Authoring above the divider with distinct purposes (`ARCHITECTURE-SPINE.md:23,111-115`; `CLOSURE-MAP.md:16`).
- R8 is intact: USER / INHERITED / CANDIDATE provenance remains explicit, and candidate defaults are still identified as not operator-accepted (`ARCHITECTURE-SPINE.md:25`; `DECISIONS-AND-OPEN.md:8-10,21`; `CLOSURE-MAP.md:23`).
- SHA-256 comparison of the current candidate tree with `workroom/qmx-ui-closure-round2-2026-09-24/evidence/candidate-as-reviewed/` found **0 differing files**. This report therefore applies to the supplied immutable snapshot.
- Existing epics are planned requirements, not implementation evidence. The absent `cancel_job` implementation and proposed `originating_psess` amendment are accurately disclosed and are not blockers for this UI architecture closure gate.

No corrective finding is raised for the requested R7/R9 scope.
