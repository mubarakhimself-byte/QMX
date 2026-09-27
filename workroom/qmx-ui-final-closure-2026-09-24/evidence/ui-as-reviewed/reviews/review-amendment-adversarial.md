---
review: amendment-adversarial
target: architecture-QMX-UI-2026-09-23 after Codex R1–R9
attack_surface:
  - ARCHITECTURE-SPINE.md (local AD-1..AD-24)
  - BOOTSTRAP-AND-AUTH.md
  - CHAT-AND-HISTORY.md
  - VIEW-AND-PACK-CONTRACT.md
  - AUTHORING-AND-ML.md
  - TRACE-MATRIX.md
date: 2026-09-24
inspect: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20
lens: 'Two units, every local AD, still incompatible on bootstrap / chat send / ActionContext / draft run / cancel. Credit companions that closed the original Codex pair. Flag remaining holes only. No spine or companion rewrite.'
---

# Adversarial review — amended UI spine (post R1–R9)

## Method

Build **two factory units** one level down from the amended spine. Both obey every local AD (AD-1..AD-24) as written, plus inherited parent/kit law the spine already binds. They still cannot assemble on the five nouns Codex named: bootstrap, chat send, ActionContext, draft run, cancel.

A pair is a hole only when **both readings are literal**. Original Codex pairs that a companion actually closed are credited and not reopened. Companion sentences that contradict a local AD are not a second legal unit; they are flagged as residue. This file does not edit the spine or companions.

`COMPONENT-CONTRACTS.md` and `EXAMPLES.md` are cited only where they close, or re-open, a hole on the attack surface.

## Verdict

**Return remaining holes. Do not reopen the closed Codex pairs.**

The amendment did the job it was asked to do at the slogan layer. Team-B chat-as-`InvocationEnvelope`, launcher-vs-service-vs-Tauri as v1 owner, renderer-selected session grant bag, temporary runnable draft version, and cancel-as-second-`dispatchInvoke` / seed `stop_run` are **not** still legal.

What remains is that each closed noun still has an **unbound joint** the vertical slice must pick: how the browser holds the pairing session, which identity `send_message` dedups on, which process mints `ActionContext` and what callers without a pack mount do, which transition after publish is the first legal Graph Run, and who may call `dispatchCancel` for a JobHandle the pane can see.

`CLOSURE-MAP.md` “closed as candidate” is true for the original pairs. It is false as “factory-unambiguous.” Tests remain unexecuted. Inspect SHA is unchanged.

| Axis | Original Codex pair | Companion close? | Remaining hole |
| --- | --- | --- | --- |
| Bootstrap | launcher vs service vs external daemon vs Tauri spawn | **Yes** — AD-19 + `BOOTSTRAP-AND-AUTH.md` | Pairing session: cookie vs header; HTTP GET vs WS session object; `producer_id` persist vs re-hint; probe `starting` has no UI door |
| Chat send | mailbox `send_message` vs envelope invoke; synthetic Home instance | **Yes** — AD-18 + `CHAT-AND-HISTORY.md` | `dispatchChat` vs pane-direct wire; product-session `command_id` vs wire `(producer_id, id)` only; who starts the reply |
| ActionContext | intercept against any GrantRecord in the `psess:` bag | **Yes** — AD-20 + `VIEW-AND-PACK-CONTRACT.md` | Svelte-minted JSON vs daemon token; composer/palette/platform Authoring have no mount |
| Draft run | temp registered version / overwrite enabled bytes | **Yes** — AD-21 + `AUTHORING-AND-ML.md` §2.1 | Publish = enable-path register vs export→install→enable; template pin in untrusted `input` |
| Cancel | `dispatchInvoke` of descriptor `cancel` vs `JobHandle` client vs `stop_run` | **Yes** — AD-23 + `TRACE-MATRIX.md` cancel contract | Observer vs starter; `expected_state` hashed vs advisory; unique caller vs unique issuer |

## Closures that hold (do not reopen)

- No sixth COMP. No UI-owned grant store. No Qt. No layout JSON on `psess:`.
- v1 privileged owner is COMP-QMB `qmb host start|status|stop`. Browser JavaScript does not spawn Python. “Start local” until that verb exists is setup copy. Tauri is not the v1 bootstrap owner. Close tab = `wire.detach`; it does not stop the daemon and does not cancel JobHandles.
- `ConversationPane.send` is CT-40 `send_message`. It does not build `InvocationEnvelope`, does not call `dispatchInvoke`, does not require `instance_id`, does not mint a synthetic instance. Durable history is the QMA mailbox keyed by `psess:`. `list_mailbox` missing is `query_unavailable`, not empty-success. Granted tool calls remain `dispatchInvoke`.
- Unique invoke issuer is `apps/qmx-ui/src/lib/host/dispatchInvoke`. No `caller_kind=widget`. Until the daemon accepts `caller_kind`, pack invoke is `caller_kind_unsupported`. Renderers may supply only `{action, input}`. Host must not pick “any grant in this session whose `op_id` matches.” Unmount drops `ActionContext` and does not cancel work.
- Mutable `editor_draft_id` / `editor_revision` is not runnable. No throwaway template version. Preview/validate ≠ Run. Graph Run is `dispatchInvoke` of a registered template `start` op, not seed `start_mission`, not in-process `MissionCompiler`.
- Unique cancel issuer is `apps/qmx-ui/src/lib/host/dispatchCancel`. Command is addable `cancel_job`, not `stop_run`, not a second invoke. Repeat uses the same product-session `command_id`. First durable terminal wins. `unknown` is not cancellable. `ConversationPane.cancel_display` is chrome stop of presentation, not `JobHandle.cancel`.
- AD-4 + AD-24: each browser surface mints its own `producer_id`. Sharing one `producer_id` across browser tabs is forbidden. (`CHAT-AND-HISTORY.md` §6’s “must not mint a second `producer_id` per tab if they are one UI process” cannot be a second unit; it loses to the local ADs. Residue only.)

`COMPONENT-CONTRACTS.md` names `dispatchChat` / `dispatchInvoke` / `dispatchCancel` as the three host issuers that never import the wire client. That **narrows** chat send and cancel, but it is not a local AD, and `CHAT-AND-HISTORY.md` never names `dispatchChat`. A unit that reads only AD-18 + CHAT still compiles.

---

## Two units (both AD-legal)

Shared, both units:

- SvelteKit static SPA, not served from `:8765`. Probe `127.0.0.1:8765` or a recorded remote. Never retarget remote → local.
- Daemon already running, or operator runs `qmb host start` / the interim `QMA_DAEMON_ROOT` recipe. Lock `.daemon_writer`. Pairing challenge → `qmb host pair` → origin + `credential_ref` + `operator` before protocol bytes. Arbitrary `cred://` is not login.
- Home authoring `psess:` may `send_message` with `app_instance_id` absent. Invoke and Graph Run require exactly one `selected_refs` kind `instance_id`.
- Widgets bind and paint. `dispatchInvoke` builds the envelope from host context, then daemon `compare_envelope_to_grant`.
- Draft Run control on unsaved buffer / `editor_draft_id` / `editor_revision` → `draft_not_runnable`.
- Cancel goes through `dispatchCancel` → `cancel_job`. Adapters do not import the wire client for invoke or cancel.

They still ship different products.

### Unit A — header-ref, command-id chat, Svelte-minted context, enable-path Run, observer cancel

**Bootstrap.** Unpaired browser opens WS to `:8765` with no family bytes; daemon returns the pairing challenge on that socket. After QMB confirm, the same socket pushes the pairing-issued `credential_ref`. The SPA stores the ref in `localStorage` and sends it as an `Authorization` header on **every** later HTTP GET. There is no cookie and no shared `AuthenticatedWireSession` object across transports: WS authenticates once per connection; HTTP re-proves the pairing table per request. `producer_id` is **not** persisted across SPA reload (TRACE-MATRIX J-UI-14 “otherwise re-hint”). Probe chrome is `none` | `loopback-live` | `remote-recorded` | `refused`. It never paints `starting` (the browser has no QMB door).

**Chat send.** `ConversationPane.send` calls `dispatchChat` (spine seed + TRACE). Payload is CHAT’s `{product_session_id, body, kind}` **plus** a product-session `command_id` (UUIDv7) because TRACE’s Home-send row and J-UI-07 require it. Lost ack: reuse `(producer_id, wire id)` **and** the same `command_id`. After ack, the host issues nothing else; a daemon mailbox subscriber may wake a copilot. `steer_agent` is not on this path.

**ActionContext.** The **Svelte** host is “the host.” At mount it builds the AD-20 JSON blob from snapshot queries (GrantRecords, `ViewPresentation`, instance, cursor) and freezes it in memory. Revocation → remint (new object, drop the old). Composer op-submit and command palette have no pack mount: Unit A **synthesizes** an ActionContext from the single selected `instance_id` plus the GrantRecord that matches that instance + chosen `op_id`. Platform Authoring Graph Run uses that synthetic context; `view_id` is a host token `view:host-authoring` that never appeared in `PackUiRequest`.

**Draft run.** Publish of a valid `editor_revision` **is** the pack/plugin enable-path register (AUTHORING §2 publish row: “first runnable identity,” “enabled bytes immutable”). No export/install cycle. Graph Run lights when `(qualified_id, version)` exists on the roster **and** exactly one `instance_id` is selected. Untrusted input may name `template` + `node_ids` as in EXAMPLES.md; the host trusts schema-valid `input.template` if `parameter_ceiling.allow_keys` includes it, filling envelope contribution from ActionContext only when those keys are absent.

**Cancel.** Unique issuer `dispatchCancel`. Callers: `RunInspector` **and** Home attention cards (TRACE: operator of the `psess:` that started the job **or can observe it**). `expected_state` is last queried JobHandle state and **is** part of the hashed `command_id` payload (parent AD-29 collision rule). Repeat delivery must byte-match the original payload, including `expected_state`. If the handle moved, Unit A keeps the original payload and lets first durable terminal win.

### Unit B — cookie session, pane-wire chat, daemon token, export-cycle Run, starter-only cancel

**Bootstrap.** Same unpaired WS challenge and QMB confirm. On confirm the daemon sets a `SameSite=Strict` cookie that **is** the origin-bound session handle; the `credential_ref` is that cookie’s value, not `localStorage`. Subsequent HTTP GET snapshots send the cookie and resume the **same** `AuthenticatedWireSession` as the WS. Header-only clients without the cookie are refused even with a pasted ref (possession is not proof; the session handle is). `producer_id` is stored per browser tab and reused on reload and reconnect. Probe still cannot see QMB; Unit B also never paints `starting`.

**Chat send.** AD-18 literal: `ConversationPane.send` issues `send_message` itself. Payload is exactly CHAT §1.1 (`product_session_id`, `body`, `kind`). No product-session `command_id` — mailbox append is not `product_session.mutate`, and parent AD-8 forbids storing transcript on the session row. Dedup is only wire `(producer_id, id)`. After ack, the pane starts the assistant turn with seed `steer_agent` (CHAT: “`steer_agent` is not Send,” so it is a **second** command, legal because it is not `dispatchInvoke` and not `send_message`). If `steer_agent` needs an instance, Home chat-without-instance produces a user row and no assistant.

**ActionContext.** The **daemon** is “the host.” `ProductSessionChrome.mount_view` returns an opaque capability token. Svelte stores the token; it cannot mint or edit fields. Dispose invalidates the token. Composer, palette, and platform Authoring **refuse** `dispatchInvoke` unless a pack view is focused and the token is live. Platform Authoring with zero opened apps can edit/validate/publish; it cannot Run. Grant revocation without remount: token still presented; daemon `GRANT_MISMATCH`.

**Draft run.** Publish creates the Graph Template identity only. AUTHORING flowchart is law: `T → pack export → install → enable → grant → P → dispatchInvoke`. The Authoring-destination Run control stays `draft_not_runnable` until that cycle has produced an enabled, granted instance and the operator opens the ML app’s `view:train-graph`. Template `(qualified_id, version)` is **not** taken from untrusted `input`; the host overwrites `input.template` from the mount contribution / selected `selected_refs` kind `template`. EXAMPLES’ payload is treated as documentation, not wire.

**Cancel.** Unique issuer `dispatchCancel`. Sole caller: `RunInspector.cancel` (TRACE callers sentence). Home attention is AD-14 observation and must not emit cancel. Principal: the `psess:` that **started** the job, not any observer. `expected_state` is advisory, omitted from the payload hash, so a repeat with a newer last-queried state still reuses `command_id`. `machine` refused. `unknown` not cancellable.

### Where they cannot assemble

| Joint | Unit A | Unit B | Shared-data clash |
| --- | --- | --- | --- |
| HTTP GET after pair | `Authorization: cred-ref` per request | cookie = session handle | CORS/cookie vs header; XSS vs CSRF; second tab finds the ref in `localStorage` vs cookie |
| SPA reload | new `producer_id`; T-CH-06 cannot reuse `(P, C1)` | same `producer_id`; lost-ack reuse possible | wire dedup window identity |
| Send identity | `(producer_id, id)` + `command_id` in `(psess, principal)` | `(producer_id, id)` only | two tabs, two payloads, same or different uniqueness domain |
| Who talks on Send | `dispatchChat` only | pane owns the wire client for mailbox | COMPONENT-CONTRACTS “never import the wire” vs AD-18 “pane issues” |
| Assistant turn | daemon subscriber, or silence | `steer_agent` follow-up | Home-without-instance either gets a reply or does not |
| ActionContext bytes | client JSON, Svelte-minted | daemon token | grant_id freshness; who can forge fields (daemon compare still runs) |
| Palette / Authoring Run | synthetic context | refuse, no mount | first Graph Run surface |
| First legal Run after publish | enable-path register + selected instance | export/install/enable/grant + opened view | whether Authoring destination is an invoke surface |
| Template pin | schema-valid `input.template` may choose version | host overwrites from mount / selected_ref | V1 pin vs V2 draft at press |
| Who cancels | Home observer + inspector | inspector + starting `psess:` only | Home attention is a command surface or not |
| Cancel repeat | hashed `expected_state` must not change | advisory `expected_state` may change | parent AD-29 collision vs TRACE “repeat same `command_id`” |

Neither unit mints `COMP-UI`, spawns Python from JS, routes Send through `dispatchInvoke`, lets an iframe pick `grant:B`, registers a throwaway draft version, or maps Cancel to `stop_run`. That is the point: the closed pairs stay closed, and the slice still forks.

---

## Remaining holes (only)

### H-BOOT — Pairing session is named twice and bound nowhere

`BOOTSTRAP-AND-AUTH.md` §5.3.7 issues a `credential_ref` **and** an “origin-bound session handle.” §5.4 then says HTTP GET uses “header **or** cookie that is the ref.” AD-12 requires HTTP GET snapshots and WS commands to be the same CT-40 client, and BOOTSTRAP requires the **same** `AuthenticatedWireSession`. Those three sentences do not pick one object.

WS `AuthenticatedWireSession` is connection-scoped. HTTP GET is another TCP connection. Unit A (per-request pairing-table check) and Unit B (cookie session) both satisfy AD-11/AD-12/AD-19.

Also unbound, still inside the ADs:

- Probe state `starting (QMB reported)` (`BOOTSTRAP-AND-AUTH.md` §4.2). The UI has no legal door to QMB. Both units must skip the state. The table still lists it.
- TRACE-MATRIX J-UI-14: `producer_id` “persists across client restart of the same surface **if stored; otherwise** re-hint.” Explicit OR. T-CH-06 requires the same `P` after crash. Those two traces disagree on reload.
- Pairing challenge is not one of AD-12’s three families. Both units keep it as a pre-protocol WS frame (BOOTSTRAP sequence). An HTTP pairing resource on `:8765` would be a fourth family and is **not** AD-legal. Not a unit split; a trap for a third reading.

Original R2 owner fork: **closed.**

### H-CHAT — Send identity and issuer are split across AD-18, CHAT, and TRACE

AD-18: the pane issues `send_message`; not `dispatchInvoke`; no instance. **Closed** for the envelope fork.

Unbound:

1. **Issuer.** Spine seed + sequence + TRACE + `COMPONENT-CONTRACTS.md`: `dispatchChat` is the unique mailbox issuer; components never import the wire client. AD-18 + CHAT §1.1: `ConversationPane.send` issues the command. CHAT never writes `dispatchChat`. Unit A and Unit B both obey every local AD.
2. **Dedup namespace.** CHAT §1.1 payload has no `command_id`. CHAT §5 / T-CH-06: identity is `(producer_id, wire id)`. TRACE Home-send and J-UI-07: product-session `command_id` unique per `psess:`; lost ack must not mint a new `command_id`; duplicate Send coalesces on `command_id`. Parent AD-29’s `command_id` namespace is `product_session.mutate`. Mailbox append is not that mutate, and parent AD-8 forbids transcript on the session row. Unit A overloads the namespace. Unit B stays on the wire pair and cannot coalesce two browser tabs of the same `psess:` (AD-24: they have different `producer_id`s).
3. **Reply trigger.** CHAT: a message may request work; it is never the work; `steer_agent` is not Send. Nothing names the command that starts the assistant after Home send. Vertical slice item 2 is only the user mailbox send, so the slice can go green while Copilot is mute.

Residue (not a legal unit): CHAT §6 vs local AD-4/AD-24 on `producer_id` for two chrome surfaces of one `psess:`.

### H-CTX — Mount context is closed; non-mount callers are not

AD-20 + VIEW §5–§6 + EXAMPLES I1/I5 **close** the session-bag attack: ignored foreign authority fields; `instance_id`+`grant_id` on the mint context; no “any grant with this `op_id`.”

Unbound:

1. **Which host mints.** AD-20 “host-minted.” VIEW: renderer and pack do not mint; remount mints a new context. Kit “host” is the daemon. This sitting’s “host” is `apps/qmx-ui`. Unit A (Svelte JSON) and Unit B (daemon token) both fit. Daemon compare still runs; isolation at press is not the same as isolation at mint.
2. **Callers with no mount.** AD-8 lists composer op-submit, command palette, and graph Run as `dispatchInvoke` callers that use **the mount** ActionContext. AD-20 only binds **mounted** views. Platform Authoring with zero opened apps is legal (AD-3, AUTHORING create-draft). Palette from Home is legal chrome. VIEW `view_id` is a pack view id (`view:…`). There is no pack view on empty Authoring. Unit A synthesizes. Unit B refuses. AD-20’s required `instance_id` field also does not say `null` is legal on an authoring preview mount; `grant_id` explicitly may be null.
3. **Freshness.** Immutable context vs “`dispatchInvoke` intersects that context with the matching GrantRecord.” Unit A remints on snapshot. Unit B presents the dead token and waits for daemon `GRANT_MISMATCH`. Both are intersection.

### H-DRAFT — Draft is not runnable; “registered” is not one transition

AD-21 + AUTHORING §2.1 **close** Team-B: no draft test-run, no hidden version, no in-place overwrite of enabled `(qualified_id, version)`.

Unbound: the path from that refusal to the first legal Graph Run.

AUTHORING §2 publish row: publish **is** enable-path register; “first runnable identity.” AUTHORING flowchart: template then **pack export → install → enable → grant → instance → dispatchInvoke**. Run row: enabled ∩ GrantRecord ∩ health ∩ envelope `instance_id`. AD-9/AD-21: Run refuses until a new immutable template version is **registered**. Three different predicates.

Unit A lights Run after publish + selected instance (register/enable-path). Unit B keeps Authoring Run dark until export/install/enable/grant and an opened pack view. Both refuse the mutable draft.

Second joint: EXAMPLES.md legal Graph Run payload puts `{template: {qualified_id, version}, node_ids}` in **untrusted** `input`. AD-20 allows schema-valid input. If `parameter_ceiling.allow_keys` contains `template`, the renderer chooses the runnable pin. AUTHORING wants expand/return to retain typed template refs and to refuse running V2 draft bytes. Unit A honors EXAMPLES. Unit B overwrites from host refs. That is the draft/run pin, back in the input schema.

### H-CANCEL — Unique function is closed; authority, hash, and callers are not

AD-23 + TRACE cancel contract **close** cancel-as-invoke and `stop_run`. `cancel_display` is not cancel.

Unbound:

1. **Starter vs observer.** TRACE: operator of the `psess:` that started the job **or** can observe it. AD-14: Home attention consumes queries; it does not authorize live/hot-swap (cancel is not named). AD-23 is silent. Unit A Home-cancels observed jobs. Unit B does not. J-UI-08 can be implemented twice.
2. **`expected_state` vs parent AD-29.** AD-23 and TRACE require `expected_state` and “repeat uses the same `command_id`.” Parent AD-29: `(psess, principal, command_id)` collision with a **different payload hash** refuses. If `expected_state` is in the hashed payload, a honest re-query before repeat is a collision (Unit A must freeze the original state). If it is not hashed, TRACE’s field is advisory (Unit B). The race J-UI-08 exists to test is exactly this.
3. **Unique issuer ≠ unique caller.** AD-23 names the function. TRACE names `RunInspector.cancel` only. AUTHORING says ML JobHandle cancel is `dispatchCancel` (surface unspecified). Home job cards are unspecified. Unit A and Unit B both have one function.

`attempt_id` and `logical_run_id` are both required fields. Cancel-this-attempt vs cancel-the-run is not chosen. Smaller than (1)–(3); still a wire-shape fork.

---

## What this pass did not do

Did not edit `ARCHITECTURE-SPINE.md` or any companion. Did not reopen closed pairs (QMB owner, mailbox send, session-bag intercept, draft test-run, cancel-as-invoke). Did not treat research notes as law. Did not execute tests. Did not start Documentation Factory or epics.
