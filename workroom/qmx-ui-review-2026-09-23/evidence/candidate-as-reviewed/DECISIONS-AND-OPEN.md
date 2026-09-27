---
name: Decisions and open issues
sitting: architecture-QMX-UI-2026-09-23
---

# Decisions and open issues

Legend: **U** user direction. **P** proposal default (this sitting). **E** observed. **Conflict** vs a parent or a rejected study.

## Accepted inputs (do not reopen)

- U: Svelte + TypeScript + shadcn-svelte + Svelte Flow. Qt out. Zero spend on the React dashboard kit.
- U: Neutral dark working baseline. Original Excalidraw layouts. Study 03 withdrawn. Study 02 picker/colors rejected.
- U: Headless/visual/mixed are independent. Paper trading is not universal. LSE ML Studio UI rejected.
- U: Shared copilot capability, independently scoped sessions, optional in-app panel.
- U: No application code on `main`. Parallel backend and UI integration. Documentation Factory in a later fresh session.
- Parent/kit law: grants, envelopes, JobHandles, four composition modes, native panes first, adapters not authority.

## New recommendations (P, for Codex)

| ID | Default | Consequence if accepted |
| --- | --- | --- |
| P-SPA | SvelteKit 2.70.3 + adapter-static + `ssr=false` | Adopted in local AD-2 |
| P-PROCESS | Browser + host-supervised daemon is v1; Tauri 2 later | Adopted in local AD-12 |
| P-DTO | Do not mint `ui_view` this sitting | Adopted in local AD-15 |
| P-ATTACH | Uploads become artifact fp1; live ids stale-badge | Adopted in local AD-7 |
| P-LIBRARY | Library is a platform rail destination | Adopted in local AD-10 |
| P-STYLE | Rhea compact dark | Adopted in DESIGN.md |
| P-CHART | LayerChart for analytics; dedicated host for tape | Adopted in local AD-17 |
| P-CODE | CodeMirror 6 first | Still a proposal until a fidelity spike |

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

No consequential operator question is required to review this candidate. Remaining defaults are tagged P.
