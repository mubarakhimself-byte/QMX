# QMX amended UI architecture — focused closure verdict

**Ready after listed corrections. This revision is not ready for Documentation Factory.**

Review date: 2026-09-24. Scope: Grok's amended candidate against the previous REVIEW.md R1–R9 and its new CLOSURE-MAP.md. This is an architecture-readiness review, not an implementation or whole-backend audit. Severity describes the risk of incompatible downstream implementations, not a demonstrated production incident.

The amendments make real progress: independent Authoring and Home are restored; chat is separated from tool invocation; view requests and immutable action context are documented; graph/code authoring, Library verbs and recovery traces are much more concrete. Missing backend implementation is honestly acknowledged and is **not, by itself, a closure failure**. The remaining failures are conflicting contracts or missing bindings needed to implement those contracts consistently.

## R1–R9 disposition

| Finding | Disposition | What is settled | What remains |
| --- | --- | --- | --- |
| R1 — platform navigation | **Closed in architecture** | Home work/attention/resume, Copilot conversation, independent Library and Authoring; zero opened apps legal | Runtime fidelity awaits implementation; exact geometry remains provisional |
| R2 — bootstrap/authentication | **Partially closed · High** | COMP-QMB owns the proposed local host command; browser does not spawn the daemon | One browser-realizable authentication and pairing contract |
| R3 — chat/history | **Partially closed · High** | Home chat needs no instance or InvocationEnvelope; mailbox is the named history owner | Durable session-to-message routing and lost-ack reconciliation |
| R4 — view/pack contracts | **Partially closed · High** | Request DTO, host ingestion, immutable ActionContext and adapter interception | Existing manifest field compatibility, navigation binding and unambiguous grant selection |
| R5 — authoring/ML lifecycle | **Partially closed · High** | Draft/revision/template/instance/run identities; graph/code ML; no runnable mutable draft | First-run registration/enable order and concurrent saved-draft behavior |
| R6 — attachments/Library | **Partially closed · High** | Typed references, Knowledge provenance, explicit Library verb/defer matrix | Staging placement and transfer/recovery contract |
| R7 — run-control traces | **Partially closed · High** | Separate cancel door, distinct identities, client/core compatibility and installed-client tests | Consistent cancel authority and state-race behavior |
| R8 — decision provenance | **Closed for this gate** | Candidate defaults are distinguished from accepted/inherited inputs | Candidate status remains; closure is not operator acceptance of every default |
| R9 — reproducible build seed | **Partially closed · Medium** | bits-ui 2.19.3 reconciled; pnpm/lockfile owner and scaffold gate named | Explicit compatible Node 22 minimum |

## Remaining corrections

### R2 — Reconcile authentication before handing it to a builder

The spine's AD-19 (`ARCHITECTURE-SPINE.md:211`) requires an in-memory `pairing_session_id` bearer on HTTP **and WebSocket** and refuses cookie-only authentication. `BOOTSTRAP-AND-AUTH.md:143–178` instead describes an origin-bound `credential_ref`, a reference header **or** cookie, and reconnect using that ref. It also opens the wire for a pairing challenge before the parent pre-protocol authentication boundary is satisfied.

The standard browser WebSocket API exposes URL and subprotocol arguments, not an arbitrary Authorization-header argument. The AD-19 instruction therefore cannot be implemented literally by the selected browser SPA. See the [WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/#the-websocket-interface).

**Close by:** specifying one proof, its issuance/storage/expiry/revocation, and exactly how the browser sends it on both HTTP and WebSocket. Separate the permitted unauthenticated bootstrap exchange from authenticated CT-40 traffic. State the static-client/daemon origin and site topology, including remote use and second-tab/restart behavior. Origin checks and credential reference shape do not alone prove operator identity. Reconcile spine, companion, examples and traces. A cookie suggestion in the independent review is an option to validate against the chosen topology, not a ratified solution.

### R3 — Make the proposed mailbox projection rebuildable and a lost send identifiable

`CHAT-AND-HISTORY.md:154–174` correctly names the mailbox fold and a new `psess:` index. However, the unchanged CT-48 message shape it lists has no persisted product-session routing datum, and the existing mailbox is Quant/ActorId based. Saying the fold is indexed by `psess:` does not yet say which durable source record supplies that value for messages, replies and questions after restart/rebuild.

At `CHAT-AND-HISTORY.md:204–218`, a lost send acknowledgement is reconciled by looking for `msg_id`, while a client gets no `message_id` until acknowledgement (`:239`). The client therefore lacks the identifier that this recovery requires. The trace matrix adds a durable session `command_id`, but the chat payload and dedup table specify only the wire pair. These cannot remain separate interpretations.

**Close by:** naming the persisted session-routing field/envelope metadata and journal source, with reply/question inheritance and a rebuild example. Choose a message/correlation identifier known before acknowledgement, or a durable command-to-message lookup. Specify its collision/retention rule and use it consistently in payload, query and trace. Show lost ack followed by browser restart restoring the right conversation without guessing content or sending a second intent. No new conversation store is required merely to fix this.

### R4 — Preserve the manifest contract already going into the backend factory

`VIEW-AND-PACK-CONTRACT.md:35–36` moves `copilot_profile` inside `pack_ui_request` and forbids the sibling manifest field. The inherited kit `architecture-QMX-2026-09-23/CONTRACTS.md:10–19` and Pack-and-Grant Epic 60 already specify an optional `PluginManifest.copilot_profile` (epics `:290`, `:304`, `:324–325`). These are mutually exclusive schemas for parallel builders. This is a concrete example of why the new backend work needs dependency scoping.

Two smaller but real bindings remain: nav items contain only `{id,title,slot}` and do not identify their view/mount set (`VIEW-AND-PACK-CONTRACT.md:43–69`); ActionContext assumes one matching grant/account scope without selecting or refusing multiple valid matches (`:154–156`). The inherited GrantRecord contract does not supply that uniqueness invariant.

**Close by:** retaining the existing manifest field and referencing it from UI requests, or declaring an explicit parent amendment with impacted Epic 60 work and compatibility/migration rules. Define nav-to-view binding, invalid references and selection behavior. Derive the action context from one unambiguous host-authorized grant, with a defined ambiguity refusal or explicit host selection; never merge grants or pick by ordering. Update the worked native/json-render/MCP examples. Do not silently rewrite active factory inputs.

### R5 — Explain how a first authored template becomes runnable

The transition table publishes/registers a Graph Template through the enable path **before** pack export, install and enable (`AUTHORING-AND-ML.md:94–99`). The parent defines compile identity from a plugin manifest **at enable** (`architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md:110`). The new companion also forbids registration outside that law. These may be reconciled by distinguishing a local authoring package from later distributable export, but the candidate currently does not establish that bridge.

Saved drafts are daemon-owned mutable working copies with immutable revisions (`AUTHORING-AND-ML.md:39–40`, `:90–93`, `:122–132`), yet there is no saved-head/base revision comparison or explicit single-writer/refusal rule. Two restored clients can otherwise overwrite the draft's head while both believe they saved the current revision.

**Close by:** documenting one complete empty-Authoring → save/validate → actual package/enable registration → grant → first Run path, then edit/new version/run/rollback. Distinguish local enable from later export if that is the chosen design. Preserve immutable enabled bytes and no direct draft execution. Define stale save/publish handling using the existing CAS approach or an explicit single-writer contract; exact UI geometry can remain deferred.

### R6 — Separate attachment possession from eventual execution placement

`LIBRARY-AND-ATTACHMENTS.md:75–85` allows staging without an instance but requires staging onto the placement that will run. Its Home example stages first and chooses an instance only later (`:220–223`), so that execution placement need not yet be known. The document promises streamed bytes and resumable/refused transfer but leaves the streaming wire path, staging identity and resume/refusal choice undefined. Naming a CT-40 command alone does not define its byte-transfer path.

**Close by:** selecting either target-bound staging before upload, or initial possession at the authenticated daemon followed by an explicit transfer/verification before placement. Preserve Home attachments before invocation and refuse silent local fallback. Define the transport, size/partial-upload bounds, completion proof and cleanup owner. If resumable, name the staging identity and retry semantics; if v1 refuses interrupted uploads, say so consistently. Trace local attachment followed by remote execution and an interrupted upload without minting a runnable partial reference. Keep the useful Library and Knowledge distinctions already written.

### R7 — Cancel authority and cancel races must agree

AD-23 (`ARCHITECTURE-SPINE.md:235`) limits cancel to the initiating session's operator and denies observers. `TRACE-MATRIX.md:33` permits the starter **or anyone who can observe**. The existing handle has no durable originating-product-session binding to enforce the new rule. The command also carries `expected_state` without defining whether a normal queued→running transition should invalidate cancellation, or how to reconcile that with same-command replay and terminal completion winning a race.

**Close by:** using one authorization rule across all files, backed by an immutable admitted-job-to-principal/session binding or another explicit inherited authority. Observation alone must not silently become cancel authority. Fence the intended handle/run/attempt; define a normal non-terminal state advance and already-terminal result. If `expected_state` stays, label its exact effect, including conflicts and same-command replay. Provide starter/observer, queued→running, cancel-vs-complete, duplicate/lost-ack and nested-child examples through the existing JobHandle owner.

### R9 — Make the Node floor explicit

`Node 22 LTS` still admits versions below the pinned Vite engine minimum. Use **`Node.js >=22.12 <23`**, or another explicitly compatible selected range, consistently in spine AD-2/stack, decision ledger, memlog and closure map. Vite 8.3.0 declares `^20.19.0 || >=22.12.0`; the checked Svelte Vite plugin also requires the appropriate minor floor. Sources: [Vite 8.3.0 package metadata](https://registry.npmjs.org/vite/8.3.0), [Svelte Vite plugin 7.3.1 metadata](https://registry.npmjs.org/@sveltejs/vite-plugin-svelte/7.3.1).

Keep exact lockfile generation, resolved adapter/plugin pins, `svelte-check` and production build at the already-named scaffold gate. No dependency install is demanded by this document review.

## Backend scope and parallel work

See [BACKEND-SCOPE.md](BACKEND-SCOPE.md). It is viable to extract a bounded backend-delta architecture session now, while independent existing epics proceed. Do not wait for finished UI code to settle the interface contracts above. Equally, do not treat every missing runtime connection as a new UI feature: some belongs to previously specified QMA work or Pack-and-Grant Epics 60–65.

The follow-up should classify reuse / already planned / implementation-adoption gap / new amendment, identify exact affected contracts and epics, and decide which dependencies must settle before those affected stories run. Separate branches alone do not prevent contract conflicts. This review does not certify the current running factory queue or guarantee all its work is independent.

## Evidence and limits

- Three independent gpt-5.6-sol reviews: [runtime](reviews/runtime.md), [experience](reviews/experience.md), [currency](reviews/currency.md). Root checked primary text, inherited contracts and relevant existing epic definitions, and consolidated rather than adopting every suggested implementation.
- Mechanical spine lint passes with zero findings. Structural lint cannot detect the contradictions above.
- All 53 reviewed input files are preserved with SHA-256 hashes. The amended candidate was not edited. Original September 23 review/snapshot remain intact. Final integrity results are in [evidence/verification.json](evidence/verification.json).
- Inspected main and integration refs remain `92279dfe43922d60fabe38e29284ca52956ab75c` and `34c148be404a375cbfd79fd4ce6997452e4f1d20`. Working-tree work by others is not evaluated merely by those commit ids.
- No implementation, Documentation Factory, epic generation/execution, runtime tests, Reticle verdict, packaging trial, branch switch or factory intervention. No inference that passing static checks proves a working installed product.

**Next gate:** correct R2–R7/R9 and amend CLOSURE-MAP.md so each closure points to mutually consistent contracts and traces. Retain R1/R8 closure and useful research. Review that finite delta before downstream generation; do not reopen the design baseline or demand backend implementation as a condition of architecture closure.
