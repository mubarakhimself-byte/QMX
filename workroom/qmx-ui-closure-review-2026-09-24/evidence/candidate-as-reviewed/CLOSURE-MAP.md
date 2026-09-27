---
name: Codex R1–R9 closure map
sitting: architecture-QMX-UI-2026-09-23
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
status: candidate — not operator-accepted
---

# Closure map

Amendment in place after `workroom/qmx-ui-review-2026-09-23/REVIEW.md`. AD-1..AD-17 ids kept. AD-18..AD-24 added. Tests unexecuted. Inspect SHA unchanged.

## R1–R9

| ID | Decision | Changed files | Evidence | Remaining risk | Status |
| --- | --- | --- | --- | --- | --- |
| R1 | Home = work/attention/resume; Copilot = conversation; Authoring restored on the rail | `ARCHITECTURE-SPINE.md` AD-3; `EXPERIENCE-AND-LAYOUT.md` §1 | User dictation Home / main agent / Library / Authoring; `research/04` D-015 | Geometry still unfrozen | **closed** |
| R2 | v1 requires running daemon; owner COMP-QMB `qmb host *`; browser does not spawn; pairing before CT-40 bytes | AD-11, AD-12, AD-19; `BOOTSTRAP-AND-AUTH.md` | parent AD-21; `auth.py`; Codex R2 | `qmb host` absent at inspect; live server still required | **closed as candidate** |
| R3 | `dispatchChat` / `send_message` vs `dispatchInvoke`; mailbox keyed by `psess:` | AD-4, AD-7, AD-8, AD-18; sequence diagram; `CHAT-AND-HISTORY.md`; `COMPONENT-CONTRACTS.md` | `WireCommand.SEND_MESSAGE`; parent AD-8 fields | `list_mailbox` is a backend add | **closed as candidate** |
| R4 | PackUiRequest v1; immutable ActionContext; MCP 2026-01-26 host policy declines extra tools | AD-6, AD-15, AD-20; `VIEW-AND-PACK-CONTRACT.md`; `EXAMPLES.md` | parent AD-17; currency MCP spec | DTO not in code | **closed as candidate** |
| R5 | Draft/revision vs template vs instance vs JobHandle; draft Run refused | AD-9, AD-21; `AUTHORING-AND-ML.md` | parent template immutability | Editor persistence implementation later | **closed as candidate** |
| R6 | `stage_artifact`; Knowledge cite as artifact fp1; Library verb matrix | AD-7, AD-22; `LIBRARY-AND-ATTACHMENTS.md` | research/13 matrix | fork/hypothesis listing deferred with revisit | **closed as candidate** |
| R7 | Trace matrix; `dispatchCancel`; J-UI-13/14; workloads named | AD-13, AD-23, AD-24; `TRACE-MATRIX.md`; `JOURNEYS.md`; `DELIVERY-AND-QA.md` | parent JobHandle; seed `stop_run` forbidden | `cancel_job` absent; tests unexecuted | **closed as candidate** |
| R8 | `[USER]` / `[INHERITED]` / `[CANDIDATE]`; decisions ledger no longer stamps P as Adopted | spine frontmatter; every local AD tag; `DECISIONS-AND-OPEN.md` | Codex R8 | Factory must not treat CANDIDATE as user law | **closed** |
| R9 | bits-ui 2.19.3 everywhere; Node 22 LTS; pnpm lockfile at scaffold gate | AD-2; stack table; `COMPONENT-CONTRACTS.md` | currency review; Vite 8 floor | lockfile unexecuted | **closed as candidate** |

## Whole-session rubric

| Area | After amendment |
| --- | --- |
| UX-01 Startup | Candidate contract in BOOTSTRAP-AND-AUTH; native install still later |
| UX-02 Home / platform | Corrected (R1) |
| UX-03 Copilot | Chat contract closed; references via AD-22 |
| UX-04 App / widgets | ActionContext + PackUiRequest |
| UX-05 Library | Verb matrix promoted |
| UX-06 App building | AD-21 transitions |
| UX-07 Graph / code | Draft not runnable |
| UX-08 Charts | AD-17 plus TRACE-MATRIX |
| UX-09 ML | AUTHORING-AND-ML journey |
| UX-10 Trading | Paper scoped; ticket chrome deferred to trading-app sitting |
| UX-11 Operations | dispatchCancel; Home attention |
| UX-12 Settings / previews | Pairing, stage_artifact, xterm preview |
| Headless / mixed | Pass at policy |
| Original layouts | Pass with R1 |
| Parent authority | Preserved; named backend adds, no local override of grants |
| Honesty | CANDIDATE tags; inspect SHA unchanged |

## Backend adds (not this sitting)

`DaemonProcess` CT-40 server; `caller_kind`; `list_mailbox`; `cancel_job`; `stage_artifact`; `qmb host start|status|stop`; loopback pairing; optional authoring `app_instance_id`.

Post-amendment independent review applied. Remaining risk is implementation of those backend adds, not a second unnamed owner.
