---
name: Decisions and open issues
sitting: architecture-QMX-UI-2026-09-23
---

# Decisions and open issues

Legend: **U** user direction (do not reopen). **I** inherited parent/kit. **C** sitting **candidate** default — not operator-accepted. **E** observed at inspect SHA. **Conflict** vs a parent or a rejected study.

Spine tags: `[USER]` / `[INHERITED]` / `[CANDIDATE]`. `[CANDIDATE]` is not user approval.

## Accepted inputs (do not reopen)

- U: Svelte + TypeScript + shadcn-svelte + Svelte Flow. Qt out. Zero spend on the React dashboard kit.
- U: Neutral dark working baseline. Original Excalidraw layouts. Study 03 withdrawn. Study 02 picker/colors rejected.
- U: Headless/visual/mixed are independent. Paper trading is not universal. LSE ML Studio UI rejected.
- U: Shared copilot capability, independently scoped sessions, optional in-app panel.
- U: No application code on `main`. Parallel backend and UI integration. Documentation Factory in a later fresh session.
- Parent/kit law: grants, envelopes, JobHandles, four composition modes, native panes first, adapters not authority.

## Candidate defaults after Codex R1–R9 (not user-accepted)

| ID | Default | Local AD | Status |
| --- | --- | --- | --- |
| C-SPA | SvelteKit 2.70.3 + adapter-static + `ssr=false`; Node.js >=22.12.0 <23.0.0; pnpm | AD-2 | C |
| C-BOOTSTRAP | Externally running daemon; QMB `qmb host *` owner; browser does not spawn; Origin never issues a pairing session | AD-19 | C |
| C-CHAT | `send_message` mailbox; no envelope; `list_mailbox` add | AD-18 | C |
| C-INVOKE | `dispatchInvoke` + ActionContext | AD-8, AD-20 | C |
| C-CANCEL | `dispatchCancel` / `cancel_job` | AD-23 | C |
| C-DRAFT | Draft run refused until immutable template version | AD-21 | C |
| C-INGEST | `stage_artifact` then fp1 | AD-22 | C |
| C-DTO | No `ui_view` contribution point | AD-15 | C |
| C-LIBRARY | Platform rail destination | AD-10 | U+C |
| C-STYLE | Rhea compact dark | DESIGN.md | U working baseline |
| C-CHART | LayerChart vs lightweight-charts | AD-17 | C |
| C-CODE | CodeMirror 6 first | COMPONENT | C until fidelity spike |
| C-TAURI | Later desktop; not v1 bootstrap | AD-12 | C |

## Rejected (with reason)

| Item | Reason |
| --- | --- |
| One three-column shell | Study 03; OpenBB/VS Code interiors differ |
| Permanent mini-app left sidebar | Fidelity reset |
| Prose cards as canvas | User rejected unusable text surfaces |
| json-render / MCP as identity | parent AD-17, kit AD-8 |
| n8n as runtime | Mental model only |
| SvelteKit 3 RC / Tauri 3 alpha | Unstable pins |
| Old `ui` branch as app base | `af66288` is BMad epics |
| Universal paper gate | U + parent AD-11 |
| Widget `caller_kind` | kit AD-4 closed enum |

## Conflicts resolved in this sitting

| Clash | Winner |
| --- | --- |
| VS Code as main-copilot vs authoring family | Authoring/ML family (`research/09`) |
| Home forced into Copilot interior | USER: Home is work state; Copilot is conversation (R1) |
| Host-supervised browser spawn | CANDIDATE: external daemon + QMB CLI (R2) |
| Send through dispatchInvoke | CANDIDATE: dispatchChat vs dispatchInvoke (R3) |
| Library as mini-app tab vs rail jump | Rail destination (dictation self-correct + AD-10) |
| Codex session “not architecture” vs this packet | This packet is the architecture stage the user later ordered |
| stack.md “QMA SDK” vs pack-and-grant “SDK” | Python `qma.*` packages vs host contract for packs — both phrases; UI is a client of the former |
| `ProductSession.app_instance_id` required in code vs kit optional authoring | Kit law for design; code amend is backend FEAT |

## Open issues (non-blocking if defaults hold)

1. Exact `sv create` lockfile — scaffold after review.
2. Whether Tauri ships in the first installer — default no.
3. Monaco vs CodeMirror after a fidelity spike.
4. When to mint `ui_view` — default later.
5. GAP-DESK-ENVELOPE-CRYPTO — backend.
6. Live wire server on `DaemonProcess` — backend prerequisite named in CHANGE-IMPACT.
7. Workload numbers — after a shell exists.

No consequential operator question is required to review this candidate. Remaining defaults are tagged **CANDIDATE**, not user-accepted.
