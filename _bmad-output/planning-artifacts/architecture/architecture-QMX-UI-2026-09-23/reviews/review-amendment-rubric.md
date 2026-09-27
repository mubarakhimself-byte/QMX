---
lens: amendment-rubric
target: ARCHITECTURE-SPINE.md (local AD-1..AD-24) + CLOSURE-MAP.md
against: workroom/qmx-ui-review-2026-09-23/REVIEW.md R1–R9
sitting: architecture-QMX-UI-2026-09-23
inspect: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20
date: 2026-09-24
status: independent closure review — not operator-accepted
---

# Amendment rubric — Codex R1–R9

Verdict: **remaining holes**.

The amendment actually closed the original Codex blockers: Authoring is back on the rail; Home is not Copilot; chat is not invoke; QMB owns v1 bootstrap; ActionContext is host-minted and immutable; draft Run is refused; bits-ui 1.x is gone; `[ADOPTED]` is gone. `CLOSURE-MAP.md` over-closes. Two identity contracts still admit two conforming hosts, and provenance still has leftover proposal language. Do not rewrite the spine. Do not send this sitting to Documentation Factory on the map’s “closed” column.

This walk judges the spine plus the companions the spine names as law. Research is evidence. `reviews/gate-summary.md` is pre-Codex (it still says Home is the main-copilot family) and is not this amendment.

## R1–R9 vs CLOSURE-MAP

| ID | Codex required | Independent | Why |
| --- | --- | --- | --- |
| R1 | Home ≠ Copilot; Authoring on the rail with zero apps | **closed** | AD-3 `[USER]` + EXPERIENCE §1 mermaid. Geometry unfrozen is allowed. |
| R2 | One v1 bootstrap owner; sequence; no browser spawn | **closed as candidate** | AD-19 + `BOOTSTRAP-AND-AUTH.md`. Owner is COMP-QMB `qmb host *`. Absent at inspect. |
| R3 | Split chat from invoke; history owner; traces; no synthetic instance | **remaining hole** | Split is real. Unique chat issuer is not. |
| R4 | Versioned DTO; immutable ActionContext; MCP profile + declines | **closed as candidate** | AD-20 + `VIEW-AND-PACK-CONTRACT.md` §5–8 + `EXAMPLES.md` A/B/C and I1–I5. |
| R5 | Draft ≠ template ≠ instance ≠ JobHandle; draft Run explicit | **closed as candidate** | AD-21 + `AUTHORING-AND-ML.md` §2.1 `draft_not_runnable`. |
| R6 | Ingest owner; closed refs; Library verb matrix | **closed as candidate** | AD-22 + `LIBRARY-AND-ATTACHMENTS.md`. Fork/hypothesis listing deferred with revisit. |
| R7 | Traces; unique cancel; producer/command identity; J-UI-13/14 | **remaining hole** | Cancel and journeys landed. `producer_id` cardinality contradicts itself. |
| R8 | USER / INHERITED / CANDIDATE; no proposal stamped accepted | **remaining hole** | Tags exist. AD-4 mix + stale “tagged P” still mislead Factory. |
| R9 | One bits-ui major; Node + package manager | **closed as candidate** | bits-ui **2.19.3** everywhere. Node **22 LTS** + pnpm named. Vite `>=22.12` floor not restated. |

Backend adds (`qmb host`, live CT-40 server, `list_mailbox`, `cancel_job`, `stage_artifact`, `caller_kind`) stay honest absences. Those are not holes in the architecture choice. The holes below are uniqueness forks **inside** the candidate.

## Requested checks

### Home vs Copilot vs Authoring — closed

AD-3 Prevents collapsing Home into Copilot and dropping Authoring. Rule: above the divider, with zero opened apps: **Home**, **Copilot**, **Library**, **Authoring**. Home = work / attention / resume. Copilot = conversation workspace (sessions, messages, preview tabs). They may reuse `SessionList` / `ConversationPane`; they are **not** the same destination or purpose. Authoring is independently reachable (graph/code/ML family) with no app open. EXPERIENCE §1 mermaid matches and says “Home is not Copilot.” Settings is chrome, not a fifth product destination.

This is the Codex R1 correction, not the earlier gate autofix that forced Home into the main-copilot interior. Coordinates remain unfrozen, as Codex allowed. Residual: Home has no region table (attention vs composer layout). That is geometry, not a missing destination.

### Chat vs invoke sequence diagram — split landed; issuer did not

Spine sequence now has three paths: Home send → `dispatchChat` → `send_message`; widget Run → `dispatchInvoke` plus ActionContext → InvocationEnvelope; cancel → `dispatchCancel` → `cancel_job`. `CHAT-AND-HISTORY.md` has two diagrams and traces T-CH-01..07. Home send with no instance is legal. Synthetic instance is forbidden. Mailbox keyed by `psess:`; `list_mailbox` is the named add.

The original invoke-only Send path is gone. What remains is **who** may talk to the wire for chat (Finding H-2).

### Bootstrap owner — closed as candidate

One owner: **COMP-QMB** via `qmb host start|status|stop` (and `pair`). Browser JavaScript must not spawn Python. Until the group exists, UI “Start local” is a setup instruction (`python -m qma.daemon` + `QMA_DAEMON_ROOT`), not a spawn. Tauri is not the v1 owner. Pairing binds origin + `credential_ref` + `operator` before protocol bytes; a `cred://` string is not operator proof. End-to-end sequence and failure table are in `BOOTSTRAP-AND-AUTH.md`. Inspect: no `host` CLI group; listener still discards bytes.

### ActionContext — closed as candidate

AD-20: each mount gets an immutable host `ActionContext` (`psess`, `view_id`, contribution tuple, `instance_id`, `config_revision`, `grant_id`, `allowed_op_ids`, account scope, snapshot cursor). Renderer/pack may not mint it. Untrusted specs supply only `action` + schema-valid `input`. `dispatchInvoke` intersects that context with the matching GrantRecord; two instances with the same `op_id` do not cross-invoke (`EXAMPLES.md` I1, I5). MCP pin is `specification/2026-01-26`; QMX declines app-provided extra tools. DTO is specified, not in code.

### Draft run refuse — closed as candidate

AD-21 + `AUTHORING-AND-ML.md` §2.1: Run on unsaved buffer, `editor_draft_id`, or `editor_revision` is typed `draft_not_runnable`. Preview/validate stay legal. Run requires a registered immutable Graph Template `(qualified_id, version)` then `dispatchInvoke` of that template’s `start`. Temporary runnable “dev versions” and in-place overwrite of enabled bytes are unsupported. T-R5-02: V1 JobHandle stays pinned while editing V2.

### bits-ui 2.19.3 vs Node 22 — closed as candidate, floor under-specified

The R9 contradiction is gone: AD-2, Stack table, and `COMPONENT-CONTRACTS.md` all pin **bits-ui 2.19.3**. Toolchain: **Node.js 22 LTS** and **pnpm** with `apps/qmx-ui/pnpm-lock.yaml`. Isolated-scaffold lockfile remains unexecuted, as Codex allowed.

Residual (not the original 1.x/2.x fork): the sitting’s own currency review recorded Vite 8.3.0 engines `^20.19.0 \|\| >=22.12.0` and `@sveltejs/vite-plugin-svelte` `^20.19 \|\| ^22.12 \|\| >=24`. “Node 22 LTS” does not name **22.12**. A 22.0–22.11 toolchain can claim the seed and fail install. TypeScript **5.9** (Kit 2 peer; refuse npm 7) is an explicit candidate, not an R9 miss.

### CANDIDATE vs USER tags — remaining hole

`[ADOPTED]` is gone. Spine provenance defines USER / INHERITED / CANDIDATE / OBSERVED. AD-1 `[INHERITED]`, AD-3 `[USER]`, AD-18..AD-24 `[CANDIDATE]` are the right shape. `[CANDIDATE]` is not user approval.

Still wrong:

- AD-4 is tagged `[INHERITED]` while its Rule also freezes sitting-owned Home chat, no synthetic instance, and per-tab `producer_id`.
- `DECISIONS-AND-OPEN.md` last line still says “Remaining defaults are tagged P” after the P-rows were replaced by a C-table.
- AD-10 is `[CANDIDATE]` while the Library-as-rail destination is user dictation (also in AD-3). DECISIONS marks C-LIBRARY as `U+C`.

Factory can still ingest a candidate default as inherited law, or go looking for P-rows that no longer exist.

## Top findings

### High

#### H-1 — `producer_id` cardinality is not one rule (R7, bleeds R3)

**Where:** AD-4 (“each tab has its own `producer_id`”); AD-24 Prevents “sharing producer_id across tabs” / Rule “Each UI process/tab”; `BOOTSTRAP-AND-AUTH.md` §9 (“New per UI process (browser tab / window)”); `TRACE-MATRIX.md` identity table (“One per UI **process/tab**” and “Not shared across tabs”); `CHAT-AND-HISTORY.md` §6 (“They must not mint a second `producer_id` per tab if they are one UI process”).

**Two conforming units**

- **Unit A — one producer per browser tab / window.** One JS realm, one wire connection, one `producer_id`. Work-area chrome tabs of the same SPA share it. A second OS/browser tab mints a new producer. Matches BOOTSTRAP and the sensible CT-40 reading.
- **Unit B — one producer per chrome tab, including work-area tabs.** Reads AD-4/AD-24 literally. Two `WorkAreaTabs` of one `psess:` are two producers on one socket, or two sockets.
- **Unit C — one producer per UI process across browser tabs.** Reads CHAT §6. Two OS tabs share `(producer_id, id)` dedup and can collide or drop commands.

Codex R7 required producer cardinality, per-producer wire-id uniqueness, and `command_id` uniqueness across tabs as distinct from invoke `idempotency_key`. `command_id` per `psess:` is unique. `producer_id` is not. Lost-ack reuse of `(producer_id, id)` forks with the cardinality.

**Action:** one sentence, same meaning, in AD-24, BOOTSTRAP §9, TRACE identity table, and CHAT §6. Candidate that matches CT-40: **one `producer_id` per browser tab/window (one JS realm / one `initialize`)**; work-area tabs share it; do not share it across OS tabs. Do not say “process/tab.”

#### H-2 — Chat unique issuer is `dispatchChat` in the spine and `ConversationPane.send` in the chat companion (R3)

**Where:** AD-18 Rule (`ConversationPane.send` issues `send_message`; does not call `dispatchInvoke`); spine sequence + structural seed (`dispatchChat` next to `dispatchInvoke` / `dispatchCancel`); `COMPONENT-CONTRACTS.md` (ConversationPane `send` via `dispatchChat`; Composer `submit_chat` or `submit_invoke`); `CHAT-AND-HISTORY.md` (controlling R3 contract never names `dispatchChat`; sequence is `ConversationPane` → wire).

**Two conforming units**

- **Unit A — unique host function.** `ConversationPane` and Composer Send call `apps/qmx-ui/src/lib/host/dispatchChat` only. They never import the wire client. Matches AD-8’s invoke pattern and the spine sequence.
- **Unit B — pane is the host.** `ConversationPane.send` builds the CT-40 frame itself. Composer `submit_chat` is a second send path. Matches AD-18 + CHAT §0/§1.

Send vs invoke **is** split (`send_message` vs InvocationEnvelope). Codex’s remaining R3 consequence still holds: two implementations can disagree on the Send method and on whether the pane may import the wire client.

**Action:** AD-18 names `dispatchChat` as the unique chat issuer, same posture as AD-8/AD-23. CHAT §0 Host column becomes `dispatchChat`. Composer Send is an event into that function, not a second client.

### Medium

#### M-1 — Provenance leftovers can still stamp candidate as law (R8)

**Where:** AD-4 `[INHERITED]` mixed with sitting chat/producer rules; `DECISIONS-AND-OPEN.md:76` “Remaining defaults are tagged P”; CLOSURE-MAP marks R8 **closed** (not candidate).

**Action:** retag AD-4 so inherited surface≠session≠engine stays `[INHERITED]` and Home-chat / producer sentences sit on AD-18 / AD-24 (`[CANDIDATE]`). Delete the P leftover. Do not treat CANDIDATE ADs as user-accepted because they have Binds/Prevents/Rule.

### Low (do not reopen the closed rows)

- **L-1 — Node 22 LTS vs Vite 8.3 `>=22.12`.** Restate the floor on the Stack row at the next spine touch. Exact lockfile stays the isolated-scaffold gate.
- **L-2 — TRACE identity table cites “Mailbox Envelope (AD-20 record)”.** Local AD-20 is ActionContext, not CT-48 `Envelope`. A builder can fuse mailbox and mount context. Fix the citation only.
- **L-3 — Home interior regions.** Purpose is unique; layout of attention vs composer is not. Codex left geometry unfrozen. Do not freeze pixels in this review.

## What actually closed (do not reopen)

- **R1** Authoring restored; Home work/attention/resume; Copilot conversation; component reuse allowed.
- **R2** External daemon; QMB supervisor; static origin ≠ :8765; `QMA_DAEMON_ROOT`; lock; pairing before protocol bytes.
- **R3 (partial)** No Home invoke-for-chat; no synthetic instance; mailbox + `list_mailbox`; T-CH-01..07.
- **R4** `PackUiRequest` v1; host ActionContext; three examples; invalid cases with a named refuser; MCP 2026-01-26 + explicit declines.
- **R5** Five identities; draft Run refused; ML journey in graph/code; change-request does not mutate running v1.
- **R6** `stage_artifact`; Knowledge cite = artifact fp1 + provenance; verb matrix with deferred fork/listing.
- **R7 (partial)** `dispatchCancel` / `cancel_job`; J-UI-13/14; workloads named; tests labelled unexecuted.
- **R8 (partial)** `[ADOPTED]` removed; CANDIDATE defined as not user approval.
- **R9** bits-ui 2.19.3 in AD-2, Stack, and COMPONENT; Node 22 + pnpm named.

## Gate

Do **not** fold this sitting in Documentation Factory on `CLOSURE-MAP.md` as written.

1. Apply **H-1** and **H-2** (uniqueness only; no new ADs, no research restart).
2. Apply **M-1** in the same pass.
3. L-1/L-2 if the Stack or TRACE rows are touched.

Status remains **draft / candidate**. Unexecuted tests, absent `qmb host`, and the live CT-40 server are named prerequisites, not remaining architecture holes of the R1–R9 class.
)
