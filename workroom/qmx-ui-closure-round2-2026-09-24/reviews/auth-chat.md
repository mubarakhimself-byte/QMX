# Round 2 closure review — R2 authentication and R3 chat/history

Review date: 2026-09-24. Scope: the frozen candidate under `evidence/candidate-as-reviewed/`, limited to local AD-18, AD-19, AD-24, `BOOTSTRAP-AND-AUTH.md`, `CHAT-AND-HISTORY.md`, the relevant `TRACE-MATRIX.md` rows, `EXAMPLES.md`, and `BACKEND-DEPENDENCIES.md`. This is an architecture-binding review. Named backend amendments may proceed to the fresh backend sitting; absent implementation is not a failure here.

## Verdict

| Finding | Disposition | Gate effect |
| --- | --- | --- |
| R2 — bootstrap/authentication | **Partially closed** | **One residual blocker:** second-tab auto-approval can issue a new operator-bound `pairing_session_id` from unauthenticated `/pair/*` using Origin alone. The HTTP Bearer and WebSocket subprotocol contract is otherwise aligned. |
| R3 — chat/history | **Closed in architecture** | The durable `psess:` binding, pre-ack wire identity, collision rule, lookup, rebuild, and no-resend recovery now form one implementable contract. One restart phrase needs precision but does not reopen the data model. |

Overall: **not fully closed because R2 still permits two materially different pairing implementations.** Resolve that finite issuance rule in the fresh backend sitting before handing authentication to builders. R3 can pass to that sitting as a named mailbox amendment.

## R2 — one residual blocker; transport proof itself is coherent

The intended proof is now consistent across the load-bearing artifacts:

- Local AD-19 makes unauthenticated `/pair/start` and `/pair/confirm` the only bootstrap paths, then uses the same `pairing_session_id` as HTTP Bearer proof and as `qmx.pair.<id>` in the browser WebSocket subprotocol list (`ARCHITECTURE-SPINE.md:207-211`).
- The companion repeats that ruling up front (`BOOTSTRAP-AND-AUTH.md:16-18`), defines exact HTTP and WebSocket presentation (`:191-212`), and refuses protocol bytes before Origin + session-table match (`:208-212`).
- Reconnect and the vertical slice use that same proof rather than a browser-supplied `credential_ref` (`TRACE-MATRIX.md:52,78-81`).
- The missing server work is honestly named as a backend amendment (`BACKEND-DEPENDENCIES.md:24-30`).

That closes the former HTTP-versus-WebSocket and `credential_ref` forks. A browser builder has one proof and one way to present it on each transport.

### Blocking edge: Origin-only second-tab auto-approval

The companion also says a second tab, which has no inherited session proof, may call `/pair/start` and receive a new operator-bound session without another QMB confirmation when the Origin is already paired (`BOOTSTRAP-AND-AUTH.md:39,226-230`). Both pairing endpoints are explicitly unauthenticated and use `credentials: 'omit'` (`:174-181`). The same rule is repeated as expected behavior in the failure matrix, second-tab table, QMB contract, and test intent (`:316,:343,:409,:436`).

This is not merely an omitted implementation detail. Origin is part of the browser request context; it is not possession of the prior operator proof. [RFC 6455 §10.1](https://datatracker.ietf.org/doc/html/rfc6455#section-10.1) explicitly warns that non-browser clients can send fake Origin fields, and a new browser tab has no tab-scoped `pairing_session_id` to present. Therefore the auto-approve branch can bind a fresh session to the prior operator without either of the two acts the architecture otherwise recognizes as proof: possession of an unexpired pairing session or a fresh `qmb host pair` confirmation. The word **may** also leaves builders free to ship incompatible issuance behavior.

**Finite closure rule:** every new `pairing_session_id` must require exactly one of:

1. fresh QMB confirmation of that pending pair; or
2. an explicitly authenticated renewal/derivation request that presents an existing unexpired `pairing_session_id` and matches its Origin.

Origin match remains required but is not sufficient by itself. If v1 has no safe cross-tab handoff for the existing proof, require fresh QMB confirmation for the second tab. Remove the optional Origin-only branch and update all repeated occurrences at `BOOTSTRAP-AND-AUTH.md:39,228,316,343,409,436` plus the pairing amendment row at `BACKEND-DEPENDENCIES.md:30`. This does not require a broad authentication redesign.

### Downstream backend bindings, not additional UI blockers

The candidate refers to expiry and revocation but does not yet name the TTL, revocation door, or pairing-table persistence policy (`BOOTSTRAP-AND-AUTH.md:230-238,315,324`). The fresh backend sitting should bind those lifecycle choices and the exact store owner. They do not create a second UI proof: the UI behavior is already “present the current id; on refusal, discard it and pair again.” Treat them as backend contract work after fixing issuance, not as reasons to demand implementation or reopen the UI architecture.

## R3 — closed in architecture

The current candidate repairs both previous R3 gaps with one continuous binding:

1. `dispatchChat` mints `(producer_id, wire_id)` before send, stores the pending correlation, and sends `product_session_id` in the ordinary `send_message` payload (`CHAT-AND-HISTORY.md:35-42,53-67`). Chat carries neither `msg_id` nor product-session `command_id` before acknowledgement.
2. Admission copies `product_session_id`, the originating wire pair, and the payload hash onto the durable existing mailbox/journal record (`:67,160-166`). Replies and questions inherit the session field and refuse retargeting (`:182-184`).
3. The rebuild example demonstrates that a daemon restart reconstructs the conversation by persisted `product_session_id`, including inherited reply/question rows, without parsing bodies or creating a parallel store (`:188-206`).
4. `list_mailbox` has a full-session form and a zero-or-one pre-ack lookup by `{product_session_id, producer_id, wire_id}` (`:210-229`).
5. Duplicate and collision behavior is explicit: same pair + same payload returns the prior result; same pair + different hash refuses; admitted chat correlation is journal-lifetime rather than only the bounded transport dedup window (`:239-248`).
6. Reconnect queries before any replay, paints a landed row, and keeps an absent row `unknown` without minting a second intent (`:296-306,357-366`).
7. The consolidated trace now agrees: Home send and lost-ack use the wire pair only; product-session `command_id` is reserved for other mutation/cancel paths (`TRACE-MATRIX.md:18-24,42,45,53`).
8. The fresh backend amendment is named without demanding a new store (`BACKEND-DEPENDENCIES.md:31`).

This is sufficient architecture input for one compatible mailbox implementation. `EXAMPLES.md` adds no competing chat or authentication dialect; its examples concern view/pack manifests, so no R2/R3 correction is required there.

### Non-blocking precision: reload/restored tab versus cold restart

`BOOTSTRAP-AND-AUTH.md` says `sessionStorage` survives a same-tab reload (`:216-230`) and that closing the browser/tab loses it (`:323,331`). `CHAT-AND-HISTORY.md` T-CH-06 and the Home-send trace instead say “browser restarts” and assume the pending triple is still present (`CHAT-AND-HISTORY.md:357-364`; `TRACE-MATRIX.md:42`). That wording promises more than the selected store guarantees for every cold restart or closed-tab case.

The recovery contract itself remains safe because it already specifies the empty-storage branch: restore the selected `psess:` by full mailbox snapshot and do not replay or mint a send (`CHAT-AND-HISTORY.md:303-306,364`). A landed message still appears under its durable session; only the client’s pending-correlation label is unavailable.

**Precision fix:** rename T-CH-06 and the trace claim to “same-tab reload or restored page session with pending state present.” Add one sentence for cold start/closed tab: “If pending state is absent, restore by `list_mailbox(product_session_id)` and never auto-resend; deterministic pre-ack correlation is unavailable on that client.” This is a wording/test-boundary correction, not an R3 closure blocker.

## Bounded adversarial and edge-case disposition

| Check | Current disposition |
| --- | --- |
| One browser-realizable HTTP proof | Closed — Bearer `pairing:<id>`. |
| One browser-realizable WebSocket proof | Closed — offered `qmx.pair.<id>` with `qmx.ct40.v1`. |
| Pre-protocol authentication boundary | Closed in contract; implementation is named backend work. |
| New-tab session issuance | **Blocker** — Origin-only auto-approval lacks prior proof or fresh confirmation. |
| Pair expiry/revocation/persistence | Backend sitting must bind lifecycle; no second UI proof introduced. |
| Durable chat-to-`psess:` routing | Closed — persisted on the mailbox/journal record. |
| Reply/question session inheritance | Closed — inherit and refuse mismatch. |
| Pre-ack identifier known before send | Closed — `(producer_id, wire_id)`. |
| Lost-ack lookup and collision retention | Closed — journal-backed lookup and lifetime collision rule. |
| Duplicate-send behavior | Closed — same pair coalesces; new id is forbidden. |
| Rebuild after daemon restart | Closed — fold persisted `product_session_id`; no body parsing. |
| Cold browser restart without pending state | Safe no-replay fallback exists; narrow the trace wording. |

## Structural note

The bootstrap companion is a 5,966-word reference/explanation document. Repetition of the second-tab rule across locked defaults, storage, failures, owner tables, QMB verbs, and tests is useful only if every occurrence carries the same invariant. Preserve those checkpoints, but replace the Origin-only auto-approve wording in all six places in one change. No broad condensation or reorganization is needed for this closure gate.
