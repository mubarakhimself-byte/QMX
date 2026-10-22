# 33 — State of play (latest update 2026-10-22 morning; the 2026-10-18 evening text follows below as history)

## 0. Update 2026-10-22: the build program milestone

**Code (checked on GitHub).** The QMX build program built and verified 51 of its 58 PRs.
- PRs 112-154 (42 PRs) are merged into `engine/base`. PR 122 (QMB start-up on `qmx_host`) is merged. PR 155 merged `rebuild/base`'s 25 fixes into `engine/base` (tip `788b1926` at that point). `integration` and `rebuild/base` are now fully inside `engine/base`; only `main`'s document commits sit outside it.
- The eight server PRs 156-163 (PRB-S, LIB4, RTRP, REM, TRG2b, APP2b, OPS2, ADOPT) are built, checked and stacked on `engine/base`; his review agent merges them bottom-up (156 first).
- Left: the five deletions, DEL2 then DEL3, and RUN1b then DEL1 then DEL4, done by one Claude Code coordinator session with Opus builders after 156-163 land. Two PRs were skipped by their probes (AGW, RTR7).
- Builders: Claude Opus until 2026-10-20, then DeepSeek-V4.1-Flash (operator's choice) for the rest.

**Server.** `qmx-server` (Contabo, reset 2026-10-21, Ubuntu 24.04) is on his Gmail tailnet (`100.105.172.63`); key-only SSH with `~/.ssh/qmx_server`; no PHP or web server; automatic security updates on. Hindsight does not fit it (about 2.7 GB), so memory runs on the PC and server recall uses the built-in search. Tailscale SSH asks for browser checks; builders use the public IP with the key.

**Findings that shape the next rounds.**
- `LAUNCH-AND-CLEANUP-MAP.md`: proposed one-trunk branching (`main` plus short branches), the must-for-usable list, clutter (191 worktrees, about 8 GB of test homes, junk Library items), stale docs. The UI rebuild branch exists only on his PC by his choice.
- `research/methodology/49-compute-and-storage-options.md`: one Linux home server, Cloudflare R2 for storage and backups, Cloudflare containers for bursts; Windows (cTrader) stays on the PC; a T3 Code-style "connect a machine" flow.
- `research/methodology/50-backend-packages-and-data-today.md`: what QMF, QMB, QML and QMN do today and every data path. The agent tools for data, backtests and the node return nothing in the running host (empty starting setup); five Libraries exist in code; history data is orphaned.

**His order from here (2026-10-21/22).** Merges (his review agent) -> deletions (Claude Code) -> cleanup -> backend finished (data journeys with the Library taking in all data, agent doors into QMB and QMF, loose wires) -> UI last, as pure wiring. The copilot methodology is designed in this lead session (CIS over BMad). The unit, QML revision, MIS router and a simplified trading node ("a server where trusted bots live") come after, in their own sessions. ML training runs on his PC first (Quadro T1000, 4 GB).

**Planning workflow for the new rounds:** see the operator memory "planning workflow that worked" (audit, research, three-ledger alignment, on-the-ground inventory, studies, party-mode and CIS funnel, BMad fold, review and fix, re-centralize, check-plan).

---

## History: state of play, 2026-10-18 evening

Read this file first, then `26-operator-rulings-and-alignment.md` (rulings 1-114; the latest ruling wins and outranks every other file). This file replaces the 2026-10-16 night version; that version's history lives in git.

## 1. Where things stand, in five lines

1. **Code.** The engine stack is merged into `engine/base`. Nothing new was built today; today was alignment and architecture.
2. **Design.** The architecture rerun (`39`) is done, reviewed (`41`), re-triaged (`40`) and fix-checked (`42`), and both fix rounds are applied inside 39.
3. **Next.** Plan the next coding program from 40's packet order (HANDOFF step 8), then put his parked calls to him and write the coding prompt (step 9).
4. **His click first.** Merge `engine/base` into `rebuild/base` before any harness packet starts.
5. **Still owed with him:** the data study (ruling 91), the methodology and system prompts (B26-B29), and the fifth quant lens.

## 2. Code: what is merged (checked with `git` on 2026-10-18)

| Branch | Commit | Holds |
|---|---|---|
| `origin/engine/base` | `132169c7` | EP0-EP14, HG1 (grants H0, H15, H16, H17), HG2, TP1-TP4 (31 templates), and HP0-HP17 **except HP2** (ruling 103) |
| `origin/rebuild/base` | `4345eafa` | The HP stack including **HP2 (#72)** and two test fixes (#76, #80) that `engine/base` lacks. The two share merge base `ed704c92` (#74) |

What this means:
- "The HP stack is merged at `ed704c92`" was never fully true: HP2 landed in `rebuild/base` after that point.
- **Merging `engine/base` into `rebuild/base` is his click.** It should come before any harness packet (CAP-H, HG3, the router), because those packets edit `launch.py` and `harness.py`, where HP2 and the test fixes live. Conflicts are possible; frame them for him with the red CI test.
- `just ci` is red on one line: `qma-core/tests/test_extensibility.py:136` pins the package set and `packages/qmx-engine` is new. The fix is one line in P0 pre-land hygiene (40 §3.1 row 0).
- Merged code still breaks four rulings. Each is a P0 or caps item, not a doc edit: `claude/fable` in the strong ladder (ruling 87); `openrouter/moonshotai/kimi-k2.5` as the first test model and `roles.live_order ("plan", "key")` (rulings 105, 107); the harness `background_cap 0.5` and `max_budget_usd 5.0`, plus every engine runaway number (ruling 106).
- `main` moves only by his own squash-merge click. `integration` is not ready.

## 3. Design: where the architecture stands

**The rerun, `39-architecture-rerun.md`**, with its two applied sections at the end ("Review applied (41 + 40 gaps)" and "Fix-check applied (42)"):
- **Routing: A + B + D.** One model router per host fronts every CLI the harness launches, with four lanes: plan (Claude bytes forwarded unchanged), GPT, key and chat (an in-house chat-completions translator). `delegate` v2 gives full helper chats on any provider. A Kimi or GLM main gets native mixed sub-agents for free. Engine AD-38, AD-39, AD-41, AD-50.
- **No QMX caps.** The $5 budget, the 0.5 share, `max_turns`, the runaway guard, and turn, tool-call and wall-time limits all go. Stuck, loop and no-convergence detection stays, because it needs no usage number. Engine AD-40, AD-16.
- **Hermes:** all 142 rows of 37d validated: 119 ADOPT, 18 ADAPT, 4 DEFER, 1 REJECT. No top-N cut.
- **MT5 and cTrader on demo:** a five-layer demo proof. cTrader click-through needs a Windows desktop placement; MT5 runs on the PC (AD-33).
- **Every alignment mismatch** of parts A, B and C has an outcome (39 §5).

**Decision ids now in use:**
- Workflow engine spine: **AD-1 to AD-51**. AD-38 to AD-49 came from the rerun; AD-50 (request normaliser) and AD-51 (per-attempt write zones) came from the review.
- Library spine: AD-1 to AD-20 (AD-20, a working copy per writer with checkpoints before destructive edits, is new).
- Lab and Pods spine: AD-1 to AD-18 (AD-18, the board cuts iterations, is new).
- Harness requests: HG3 (narrowed per 36) and HG4. HG4 includes **H38**: registry-generated sub-agent definitions on `NewChat.agents`, the only route to native third-party sub-agents in his copilot.

**Probes that gate the build** (pass and fail lines in SOLUTION-DESIGN §26.14). None has run yet:

| Probe | Gates | If it fails |
|---|---|---|
| **P0** parity | the plan lane | no plan lane; plan launches stay as built |
| **P1** sub-agent definitions under his real `/login` | the plan lane and H38 for plan mains | no plan lane; his Opus copilot uses `delegate` v2 helpers |
| **P1k** H38 under Kimi and GPT mains | H38 for those mains | native helpers wait; `delegate` v2 still works |
| **P2** live billing | the plan lane | no plan lane |
| **P4** normaliser under a plan main | each provider's native sub-agent use | that provider is `delegate` only |

Order: P0, P1, then build dark, then P4, P2, then turn on. Also gating: P3 (chat lane), P5, P7, P-PK, P-FK, P-BR and E33. The probes run on haiku through his plan login (ruling 105), so he must start them himself.

**Re-triage, `40-retriage.md`:** 189 distinct issues from the engine run, mapped to the rerun. 158 still need code. Packet order: P0 hygiene → CAP-E and CAP-H (caps removal with the stuck detector) → SEC-1, SEC-2 → HG3 → BUG-1, BUG-2 → L1 → later engine packets → ROUTER → DLG → HERMES → HG4 non-pool → TPL → MM → BRW → MEM → LIB → DESK, with HYG in parallel (40 §3.1).

## 4. Built, designed, new (said plainly)

He said "the backend is almost done". It is not. The engine core and the harness are built. Most of what he asked for since Friday is designed but **not built**.

| Built and merged | Designed, not built | New in the rerun, not built |
|---|---|---|
| Engine core: definitions, validation, ledger, memo, replay basics, script/rule/loop/join/wait/llm/agent/grader/monitor/subworkflow/trigger/doctor nodes | **Account pool** (AD-12): the code logs "skipped: no pool" | **Router lanes**: plan, chat, normaliser (AD-38, AD-50) |
| Triggers: cron, interval, manual, after, catch-up, quota hold, preflight | **Vault**, run passes, central relay (AD-28) | **Model registry** and data profiles (AD-39) |
| Inbox, explain, drafts, versions, tests, local worker | **Library** and its **Hub**: the engine runs on a fake Library port | **`delegate` v2** (AD-41) |
| 31 templates (9 tested and installed disabled, 22 drafts) | **Contabo node**, placements beyond the PC (AD-30) | **Multimodal layer** (AD-42) |
| Harness: chats, permissions, money gate, relay key lane, GPT lane, blocking `delegate`, plan usage meter | **Script isolation**: zones, AppContainer, manifest tiers, money-scan predicate (AD-24, AD-36, AD-37) | **Permission floor and rules** (AD-43) |
| HG1 grants (H0, H15, H16, H17) | **Memory** (AD-18): one docstring today | **Browser pack, take-over, HUD** (AD-44); **Cua** desktops |
| Idle watchdog | No-caps settings (AD-40); the code still holds every cap | **Output directives and previews** (AD-45) |
| | Trigger kinds `event`, `webhook`, `session` | **Skills lifecycle and curator** (AD-46); **copilot loops** (AD-47) |
| | Copilot builder skill (placeholder file only); mini-app archive (stub) | **Desktop app host** (AD-48); **worktrees** (AD-49); write zones (AD-51) |

## 5. Parked operator calls (only these)

Framed in engine `OPEN-DECISIONS.md`, recommendations first:

| Call | What | Recommend |
|---|---|---|
| **D** | Grant HG3, narrowed (H2 first: engine agent chats get the SDK `tools` list) | Yes |
| **E** | Edited and model-written scripts never run bare on the PC: Docker started by QMX, then Contabo, then wait | Yes |
| **F** | A money scan that fails closed with no allow-list | Yes |
| **G** | Grant the HG4 rows outside the pool exception: H26, H30, H31, H32, H34, H35, H37, H38, H3 | Yes |
| **Burst and paid machines** | Which burst provider to pay for and when, including whether to pay for a **Windows desktop placement** so cTrader demo click-through exists (MT5 demo needs none) | Decide only when Contabo's four sessions overflow too often |
| **Fifth quant lens** | Four are confirmed (researcher, trader, developer, portfolio manager); the fifth is unnamed | Nothing is built on it; settle it in the methodology session |

**Steps only he can do** before gated pieces: run the build-gate probes under his own `/login`; create a demo-only cTrader ID if he wants cTrader demo work; write his demo account list in Settings; tick the sites a `logged_in` browser profile may carry.

**Also open, not calls:**
- The data deeper study (ruling 91). Data stays held. His 10 GB tick history still has no backup.
- Methodology, system prompts, persona text and explainer screens (B26-B29, ruling 82), with him.
- The old-code deletion D1-D4 and the B1 SQLite one-writer fix have not run. `DELETION-PLAN.md` must be rewritten first: its one-plan and 50 % premises are stale.
- Unanswered from 10-18 (RECOLLECTION §3): whether he reviewed or waived the EP14/TP4 screenshot and video gate; whether he still routes his own plan through opencodex (`ocx claude`).
- Disk and branch clutter: `AUDIT-2026-10-18.md` lists about 2.7 GB in `D:\QMX-worktrees\qma-ship\` and about 90 merged remote branches. Each deletion needs his go.

## 6. File index: what to read first

All paths are under `tracker/qma-v2/`.

| Order | File | Why |
|---|---|---|
| 1 | `research/methodology/26-operator-rulings-and-alignment.md` | Binding rulings 1-114 |
| 2 | this file | State |
| 3 | `HANDOFF-2026-10-18.md` | How the planning lead works; the rerun steps (1-7 done, 8-9 next) |
| 4 | `research/methodology/39-architecture-rerun.md` | The current design record; read §1, §9, §10, then "Review applied" and "Fix-check applied" |
| 5 | `research/methodology/40-retriage.md` §3 | Packet order and file overlaps for the next plan |
| 6 | `architecture/workflow-engine/` | Spine AD-1 to AD-51, `SOLUTION-DESIGN.md` (§26 holds the rerun), `HARNESS-REQUESTS.md`, `OPEN-DECISIONS.md`, `PLAIN-WORDS.md` |
| 7 | `architecture/library-and-data/`, `architecture/lab-and-pods/` | The other two spines (approved; amended by the rerun) |
| 8 | `UI-HANDOFF.md` | Everything the UI session needs, §0-§13 |
| 9 | `wayfinder/MAP.md` and `python -I wayfinder/frontier.py` | Open questions as tickets |
| 10 | `AUDIT-2026-10-18.md`, `alignment/A`, `B`, `C`, `RECOLLECTION-2026-10-18.md` | Disk audit and the transcript alignment behind rulings 105-114 |

**Inputs and records** (read when a detail is needed): studies `01`-`38` (`27-rubric-walk.md` grades 01-22; `34` engine-run triage; `35` and `36` the first amendment and its review; `37a`-`37d` Hermes; `38` provider routing, stale where its banner says); `41` and `42` (review and fix-check, applied in 39); `research/sources/hermes-docs/` (Hermes docs mirror); `research/one-engine/` (the 10-14 harness design; `architect/DESIGN.md` is its contract); `BACKLOG.md` (his backlog in his words); `UI-NOTES.md` (harness event details for the UI); `WORKFLOW-SHIP-PREP.md` (the shipping mistakes list); `DELETION-PLAN.md` (rewrite before use). The engine run record is `D:\QMX-worktrees\qma-ship\engine\`.

**Archived** (evidence only, never the plan; each folder has a `SUPERSEDED.md`):
- `archive/2026-10-18-harness-program/`: the HP0-HP17 plan, prompt, arena candidates, type sketch and review.
- `archive/2026-10-18-engine-program/`: `ENGINE-PLAN.md`, `PROMPT-ENGINE.md`, `RERUN-WORKFLOW.md`. ENGINE-PLAN's Appendix G (later packets L1-L19) and Appendix H (defaults) are still cited by 34, 39 and SOLUTION-DESIGN.
- `archive/2026-10-18-methodology-studies/`: 05, 10, 15-17, 27b-27d.
- `archive/2026-10-18-wayfinder-superseded/`: 16 superseded tickets.
- Older: `archive/2026-10-16-methodology-drafts/`, `archive/2026-10-13-*`.
