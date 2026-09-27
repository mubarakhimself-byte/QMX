# Runtime, chat, authentication, and cancel closure review

Scope: the amended UI architecture against prior `REVIEW.md` R2, R3, and R7, with parent-law and narrow `integration@34c148b` checks. This is an architecture closure review. The named backend work being absent is not itself a defect where the candidate labels it honestly.

## Verdicts

| Review item | Verdict | Basis |
| --- | --- | --- |
| R2 — bootstrap and authentication owner | **Not closed as architecture** | COMP-QMB / `qmb host` is now a clear owner and the implementation gap is stated honestly. The browser authentication bridge still has mutually incompatible credential and transport rules, and the binding spine requires a WebSocket header the browser API cannot set. |
| R3 — chat, invocation, and durable history | **Not closed as architecture** | `dispatchChat` / `send_message` is correctly separated from `dispatchInvoke`, with no synthetic instance. The proposed mailbox history lacks a specified durable `psess:` routing field, and lost-ack reconciliation has no stable identifier the client can know before the lost acknowledgement. |
| R7 — run control, identities, and cancel | **Not closed as architecture** | The trace matrix usefully separates wire ids, session command ids, and invocation idempotency, and it preserves first-terminal-wins. Cancel authority contradicts itself, the existing handle has no originating-`psess:` authorization binding, and `expected_state` is incompatible with the documented race/retry path. |

`CLOSURE-MAP.md:17-18,22,51` therefore overstates closure. These are design contradictions or missing bindings, not merely the already-declared implementation work (`qmb host`, live CT-40, `list_mailbox`, and `cancel_job`).

## Findings and closure fixes

### F1 — R2 has two incompatible browser authentication contracts, and the binding one is not implementable with the standard browser WebSocket API

`ARCHITECTURE-SPINE.md:211` requires an in-memory `pairing_session_id`, `Authorization: Bearer pairing:<id>` on every HTTP query **and WebSocket**, and refuses cookie-only auth. `BOOTSTRAP-AND-AUTH.md:148-153` instead issues a `credential_ref` plus an origin-bound session handle, `BOOTSTRAP-AND-AUTH.md:163-172` allows the query credential as a header **or cookie**, and `BOOTSTRAP-AND-AUTH.md:178` reconnects with `credential_ref`. The existing shape gate also accepts only a CredentialRef plus principal (`.worktrees/integration-inspect/qmx-agents/packages/qma-wire/src/qma/wire/auth.py:92-115`). These are different credentials, storage rules, and server lookups.

The standard browser [`WebSocket()` constructor](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/WebSocket) accepts a URL and optional subprotocols; it provides no application API for an `Authorization` header. The [WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/) likewise constructs the browser handshake from the URL and subprotocol list. Thus the binding AD-19 path cannot be implemented by the selected browser SPA as written.

**Closure fix:** choose one browser-realizable proof and make AD-19 and the companion identical. A concrete v1 choice is: pairing completes over a named pre-auth bootstrap endpoint; confirmation issues an origin-bound, HttpOnly `SameSite=Strict` host session cookie (also `Secure` remotely); the daemon validates cookie + exact `Origin` on HTTP queries and the WebSocket upgrade before accepting CT-40 family bytes; the server maps that session to the stored CredentialRef and operator principal. If a different proof is chosen, specify the exact browser API that sends it on both transports. Define persistence, expiry, revocation, second-tab behavior, and browser-restart behavior for that one credential. Remove the other token names and the header/cookie fork.

### F2 — R2 sends a pairing challenge on the wire before the required pre-protocol authentication

`BOOTSTRAP-AND-AUTH.md:143-153` says an unpaired browser opens “the wire,” receives a pairing challenge, then authenticates. The sequence repeats that ordering at `BOOTSTRAP-AND-AUTH.md:202-211`. Yet `BOOTSTRAP-AND-AUTH.md:30,119-124` and parent CT-40 require authentication before protocol bytes. Calling the challenge “not an unauthenticated protocol bind” does not identify a separate transport or endpoint.

**Closure fix:** define pairing as a small bootstrap exchange outside the CT-40 family channel, including request/response shape, origin checks, expiry, rate limit/refusal, and the transition that permits the authenticated WebSocket upgrade. The CT-40 connection must begin only after that proof succeeds.

### F3 — R3 names the mailbox as history owner but never makes `psess:` or thread identity durable in that mailbox

`CHAT-AND-HISTORY.md:152-174` says the existing QMA mailbox is the sole writer and that the projection is indexed/filtered by `psess:`. `CHAT-AND-HISTORY.md:178-194` then makes `list_mailbox(product_session_id)` authoritative. But the restated CT-48 record at `CHAT-AND-HISTORY.md:170` contains no `product_session_id` or `conversation_thread_id`. The inspected `Envelope` fields likewise contain neither (`.worktrees/integration-inspect/qmx-agents/packages/qma-core/src/qma/core/ports/mailbox.py:76-95,269-289`), and the current mailbox projection is keyed by Quant `ActorId`, not product session (`.worktrees/integration-inspect/qmx-agents/packages/qma-daemon/src/qma/daemon/bus/mailbox.py:185-230`). An “index by `psess:`” cannot be rebuilt from the specified durable record after restart.

**Closure fix:** name the durable routing datum and its journal source. For example, make the daemon-owned message projection persist `product_session_id` and derived `conversation_thread_id` alongside each delivery record, populated from the admitted `send_message` command and inherited by replies/questions. Specify how existing Quant mailbox ownership and the product-session index coexist, how replies inherit the binding, and how a rebuild deterministically recreates `list_mailbox(psess)` without parsing free-form bodies or adding a parallel conversation store.

### F4 — R3 cannot reconcile a lost send acknowledgement with the identifiers it defines

`CHAT-AND-HISTORY.md:204-209` says recovery queries the snapshot and checks whether `msg_id` is present. But `CHAT-AND-HISTORY.md:234` says an unsent draft has no `message_id` until acknowledgement, and `CHAT-AND-HISTORY.md:310` merely says “If M is present” after the acknowledgement was lost. The wire pair `(producer_id, id)` is explicitly distinct from mailbox `msg_id` (`CHAT-AND-HISTORY.md:127-135`) and is only deduplicated for a bounded window. `TRACE-MATRIX.md:41,44` additionally introduces a product-session `command_id` that the chat companion does not place in the mailbox record. The inspected command schema leaves `args` unconstrained and supplies no mapping (`.worktrees/integration-inspect/qmx-agents/packages/qma-wire/schemas/command.v1.schema.json:8-30`).

**Closure fix:** select one durable correlation. Either the client mints `msg_id` before send and retries/query by that id, or the daemon persists `(product_session_id, principal, command_id)` and the original wire pair on the mailbox record and makes `list_mailbox` queryable by it. State the retention and collision rule. Then make `CHAT-AND-HISTORY.md` and `TRACE-MATRIX.md` agree on whether chat uses only the wire pair or also the parent AD-29 session `command_id`. Lost-ack recovery must terminate as landed or absent without guessing message content.

### F5 — R7 gives observers cancel authority in one binding artifact and denies it in another, without a durable origin binding

The binding local AD-23 permits only “the operator of the `psess:` that started the job” (`ARCHITECTURE-SPINE.md:231-235`). `TRACE-MATRIX.md:28-35` instead permits that operator **or anyone who can observe it**. Observation is not authority in the parent design, and the existing `JobHandle` stores `owner: ActorId`, `logical_run_id`, and `attempt_id`, but no originating `psess:` or initiating principal (`.worktrees/integration-inspect/qmx-agents/packages/qma-core/src/qma/core/ports/jobs.py:263-285`). An implementation cannot enforce the spine rule from the handle it receives.

**Closure fix:** retain the spine’s starter-only rule unless a separately reviewed authority expansion is intended; remove “or can observe it” from the trace matrix. Persist an immutable cancel-authority binding at job admission from authenticated principal + originating `psess:` to `(job_id, logical_run_id, attempt_id)`, and require `cancel_job` to resolve that binding before entering the existing `JobHandle.cancel` authority. Observers remain read-only.

### F6 — R7’s `expected_state` precondition conflicts with cancel-vs-complete and lost-ack recovery

AD-23 requires `expected_state` in the command (`ARCHITECTURE-SPINE.md:231-235`); the trace defines it as the last queried state (`TRACE-MATRIX.md:30-34,43`). If a handle naturally moves `queued → running` between query and cancel, strict equality makes the cancel stale before the documented cancel-vs-complete arbitration runs. Retrying with the same `command_id` repeats the stale payload; changing `expected_state` under that id is a payload collision; minting a new id contradicts `TRACE-MATRIX.md:34,43-44`. Parent law already fences the attempt and makes the first durable terminal win (`architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md:240-244`; `CONTRACTS.md:332-352`).

**Closure fix:** remove state equality as a cancel precondition. Fence on immutable handle identity + `logical_run_id` + `attempt_id`; atomically apply cancel against the current handle, returning the existing terminal as a recorded no-op when completion already won. If `expected_state` is retained as advisory context, say explicitly that a non-terminal state advance does not refuse cancellation, and define the durable result returned for same-`command_id` replay.

## What is resolved but unimplemented

The owner choice itself is coherent with parent AD-21: COMP-QMB is the only operator CLI, while the daemon remains the runtime. The candidate also honestly labels `qmb host *`, loopback pairing, live CT-40 serving, `list_mailbox`, and `cancel_job` as absent. Likewise, the chat/invoke split, close-versus-stop-versus-cancel separation, distinct identity namespaces, snapshot-over-event rule, and first-durable-terminal rule are adequate architecture directions. They should remain; closure requires the six contract repairs above, not implementation evidence or new epics.
