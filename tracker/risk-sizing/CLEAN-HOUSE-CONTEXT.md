# Context for the clean-house session, from the planner

Written 2026-11-05 by the session that planned the unit system ("QMX backend implementation", log `ed09cf0c`, running since 29 October). The operator asked for it so the replan has both halves: you hold what the build did, and this file holds why the plan looks as it does.

Read sections 1 to 4 before anything else. The rest is a map, so open it when you need it.

Labels: **CHECKED** means I read it in a file or ran it this morning. **MEASURED BY** names who measured it. **PLANNER'S VIEW** is my opinion, and his word beats it. Short paths: `P` = `D:/QMX-worktrees/unit-plan/tracker/risk-sizing`, `A` = `D:/QMX-worktrees/audit-ship`.

## 1. What this plan was for, in ten lines

1. QMX had a "bot" model. He replaced it with the **unit**: one complete trading algorithm with no separations, holding entry, exits, its own self-calibrating risk and sizing, its condition needs, session profile, baseline and journal, tested as one (`P/STATE.md:21`).
2. **There is no complete unit today.** Risk and sizing were taken out of this plan on purpose and given to a separate design session. The plan built a socket with labelled placeholders in it (section 3).
3. **He has no strategies to test yet.** "I don't have layer strategies" (`P/STATE.md:186`). So the plan used a **dummy unit**, picked by the lead. Its only job is to prove the system works: can agents build a unit, and can they backtest it (`P/STATE.md:70,186`). It says nothing about trading edge.
4. His ruled order of care is QML first, the node second, the MIS third (`STATE:79`). The build order is QML, the MIS and the contracts first, then assembled into the node, which comes late (`STATE:110`). The plan's phases follow that: 0 dummy end to end, 1 QML and dictionary, 2 QMB, 3 journals and agents, 4 MIS, 5 node, 6 workflows.
5. His method: foundation first, the smallest complete core that everything grows on, like mini apps and pods. Never say "minimal viable" (`STATE:75`). Design for complexity, never a complex system (`STATE:20`).
6. Two things are his "babies": the workflow engine and the mini-app core. Understand their intent before touching them (`STATE:128,133`). The Library's core is also not to be ruined (`STATE:131`).
7. Much was already built before this plan: QMA v2, the copilot, workflows, mini apps, the Library, the local-first stack. Legacy code is surgical, not frozen (`STATE:96,105`).
8. The plan is 73 PRs written on 1 November (`eb93a70b`). It grew to 91 sections, all through my commits (section 6).
9. The build started on Sunday 1 November on his laptop. He froze it on Wednesday 4 November and you audited it that night.
10. His newest word beats everything in this file. See section 2.

## 2. What changed this morning (his 5 November message to you)

These replace what the plan and the 4 November triage say:

- **Foundation before demo.** The two-PR path to a first real start was his accepted shape on 4 November (`P/build/TRIAGE-2026-11-03.md:5,16`), so your demo-first order had a real source. His newer word replaces it: fix the foundation, then the walls, and there is no rush.
- **The dummy question is closed.** Do not bring it back (section 3 explains why it arose).
- **Plan and build are split.** You plan from the findings, and a fresh session builds. He leans this way and you agreed.
- **Blast radius comes first**, because this code sits on a legacy code base with much that already works.
- **Code from October onward is the truth. `docs/` is stale**, last updated around June to early September. The plan never used `docs/` as code truth either.

## 3. The unit, the dummy, the "exam" and risk

**Where "exam" came from.** It is an old word. Early funnel research used "exam baseline" (`P/STATE.md:348`, `P/research/07-funnel.md`). The glossary then retired it: use "baseline card", avoid "exam" (`P/architecture/funnel/versions/GLOSSARY.md:135-137`), and Level 0 bans the word in QMB source (`P/architecture/level-0/ARCHITECTURE-SPINE.md:609`). What exists now is **the judge**, in `qmx-agents/packages/qmx-judge` (plan section B13). He is right that "the exam" is not a current thing. You are right that the judge is in the code.

**How a unit moves (A9, B13, C-23).** `draft` to `tested` is the judge's verdict. `tested` to `paper` is his click. `draft` to `live` answers `illegal_move`. The judge may label tested or parked by itself because neither state trades (`STATE:46`).

**The hole that produced the question, and it is the plan's fault.** Nothing in the plan says how the dummy becomes `tested`. B13's lane 4 uses "a passing verdict on the dummy's draft" as a fixture (`P/build/UNIT-PLAN.md:2003`). C-23's lane starts from an already tested dummy (`:3219`). C-14 says his node "trades the dummy" (`:3765` onward). I never joined those up, so C-14's rehearsal passed only by planting rows, as you found. It was a gap in my plan, not a decision of his.

**PLANNER'S VIEW.** A judge verdict on a unit whose sizing and exits are placeholders measures plumbing. That is another reason the replan should not make passing the judge a goal for the dummy. Its goal is the proof of (3) in section 1.

**The proof list is still owed.** He said the tests "are not defined properly yet" and that I owed a proof-test list (`STATE:186`). INFERRED from a search of `STATE.md`, Level 0 and the plan: no separate list was ever written. B9's lanes, C-14 and C-15 stood in for it. The replan should define what "the foundation works" means.

**Risk and sizing belongs to another session.** "QMX risk management and position sizing" (app session `local_90bdf1b0-517c-49a5-923e-d8e59418d2ee`), branch `plan/risk-core`, worktree `D:/QMX-worktrees/risk-plan`. Read `tracker/risk-core/STATE.md`, "RESUME HERE", items 41 to 43. CHECKED: it stopped on 3 November at Stage B of its expansion, on his stop line, with the funnel next. It has no architecture yet. He wants it resumed as soon as this clean-up allows.

- Every placeholder, where it sits and what replaces it: `P/build/RISK-SIZING-PLACEHOLDERS.md` (31 rows: sizer, stop, target, time exit, halts, cross-unit hook, kill effects, lot rounding and more). Values such as 0.5% and 2R carry no weight (`A/RULINGS-NOW.md:189`).
- The socket's four slot contracts: section "What the slots accept" of the same file, and part A `CONTRACTS.md` §4.3.
- His own words on risk: `P/RISK-SIZING-PACK.md`.
- Your list "For the risk session" (`A/REPAIR-SCOPE.md:130-132`) is the right hand-off. Anything that changes a sizing or exit rule goes there.
- **PLANNER'S VIEW:** a defect in plumbing around a placeholder is yours, for example "flatten says done and does nothing". The value or rule the placeholder stands for is theirs. In cluster 5, refusing at compile needs nothing from them. Making exits really run touches their socket, so agree it with them first. You already said this.

## 4. What the plan got wrong, and my part in it

You should not treat the plan as above question. These are mine:

1. **Nobody independently reviewed the plan.** R0, R1 and FC1 reviewed the architecture. P2 then wrote the plan, and I only ran `check-plan.mjs`, which checks structure, not content (`STATE:50`, commit `eb93a70b`). My own workflow says a builder brief points at a reviewed plan section. Your plan check on 4 November was the first content review it ever had. **Do not repeat this: review the replan before any builder starts.**
2. **Skills were on paper with nothing enforcing them.** `P/build/BRIEF-BUILDER.md:57-72` lists a stack: Feature playbook, `how`, `architect`, `tdd`, `blast-radius` and more. The builder template in `P/build/PROMPT-ORCHESTRATOR.md:66` only orders poteto-mode's `SKILL.md`, and it also says "Open the PR ready within about 15 minutes" (`:83`). That line pushes against `how` and `architect`. Nothing ever checked a transcript. MEASURED BY the build coordinator on 4 November: every one of 249 agents loaded poteto-mode, the Feature playbook was opened by 35% of builders in the first 73 PRs and 25% after, and none opened `how`, `architect` or `tdd`. Check lanes ran for 54 of the first 74 stack rows and 6 of the last 19. Your `tools/audit.py check` is the fix I should have written.
3. **The same gap existed in planning.** See the table in section 7. The full architecture review (R1) opened only poteto-mode by my measure, although its brief names `bmad-review` and `blast-radius`.
4. **C-14's "landed means `origin/main`" came through my validation pass** (`P/build/VALIDATION-2026-11-03.md`), against his "never `main`" (`STATE:282`). That is your plan-check-1.
5. **Growth: I said yes one item at a time and never showed the total** (section 6).
6. **Rulings lost between architecture and plan** (`A/reports/plan-check.md`): SQS appears nowhere in the plan, nothing writes the market journal, one-click server setup was softened, `lifecycle.auto_paper` contradicts "his click", and the wording "verified only when unit, live and perf boxes are checked" sits badly with "no hundreds of tests".
7. **Stale line numbers.** Every Files block was read at `c93407ca` in `D:/QMX-worktrees/engine-base-read`. The stack is 390 commits above that. Treat the plan's file:line references as starting points.
8. **Compaction.** This session was compacted several times. What survived reliably is on disk, so trust `STATE.md` and the verbatim transcripts over any summary of mine.

## 5. Read these, in this order

**Must read, about 30 minutes:**

| # | File | Why |
| --- | --- | --- |
| 1 | `P/STATE.md` lines 18-192 | Binding corrections, midday rulings 1 to 55, then the morning round with "the proof run uses a placeholder": the intent behind the whole plan |
| 2 | `P/STATE.md` lines 193-284 | His earlier rounds, including "code first, broaden before defining" |
| 3 | `P/architecture/funnel/versions/GLOSSARY.md` (9 KB) | The words. Wrong words have cost him the most |
| 4 | `P/build/plan-parts/00-head.md` and `90-tail.md` | How the program was meant to run, its gates, and Appendix B "Not in this program" |
| 5 | `P/build/TRIAGE-2026-11-03.md`, `P/build/VALIDATION-2026-11-03.md` | The additions and his 4 November rulings |
| 6 | `P/build/RISK-SIZING-PLACEHOLDERS.md` | What is deliberately not built |
| 7 | `P/architecture/00-how-the-best-session-worked.md` | The working method he called "a perfect session". He asked that planning copy it |
| 8 | `P/operator/transcript-2026-10-31-to-11-05.md`, the parts from 31 October midday and from 3 November on | His words and mine, newly extracted for you. Search it instead of reading all 193 KB |

**Design, by repair cluster.** Read only your cluster's row. Your order may differ, and the numbers are yours from `A/REPAIR-SCOPE.md`:

| Cluster | Architecture under `P/architecture/` | Plan phase |
| --- | --- | --- |
| 5. What a unit says is what it runs | `parts/A-qml-dictionary-unit/` 1-qml-door-compiler-runtime, 2-unit-template-numbers-lifecycle, 3-checker-and-authoring-doors, 4-dictionary, CONTRACTS | 0, 1 |
| 4. Backtests on his data and facts | `parts/B-qmb-journals-workflows/` qmb, library-data, judge | 0, 2 |
| 3. Recorded and reaches him | `parts/B-.../journals`, `parts/C-node-mis-external/` RECORDS, MIS, DEVOPS-CLOCKS | 3, 4, 5, 6 |
| 2. Node keeps a true picture | `parts/C-.../` NODE, EXTERNAL, NETWORKING | 5 |
| 1. First start runs to its end | `parts/C-.../` NODE (OP-02), Level 0 AD-37, plan C-14 and C-15 | 5 |
| 6. Workflow verdicts are true | `parts/B-.../` workflows, mini-app-core; `grounding/G4b-qma-v2-session-agents-workflows.md` | 6 |

Over all of them: `P/architecture/level-0/ARCHITECTURE-SPINE.md` (118 KB, AD-1 to AD-47) and `P/architecture/01-connections.md`, which says who connects to whom. Each part also has `ARCHITECTURE-SPINE.md`, `BUILD-SLICES.md`, `LEAD-CALLS.md` and `RISK-SIZING-POINTS.md`. The lead's calls are where I decided things he did not.

**For your blast-radius point.** The audit did not judge older working code. These files map the shipped seams at `c93407ca`: `P/architecture/level-0/blast-radius.md`, `parts/A-.../blast-radius.md`, `parts/C-.../BLAST-RADIUS.md`. Part B has no file of its own, so that is a gap. For what the legacy parts do and why: `P/architecture/grounding/` (G1 algo side, G2 agents and platform, G3 node and external, G4a wrap-up session with node and Library, G4b QMA v2 with agents and workflows). Check them against code before relying on them.

**The hard cases.** `P/architecture/funnel/edge-cases/catalogue.md` (119 KB) maps each case to a part and a check. It was the yardstick for the architecture and is a ready source for "what must the foundation survive".

**Reference, only when a question points there:**

| What | Where |
| --- | --- |
| Why each design choice won | `P/architecture/funnel/solutions/` (one file per part), `funnel/versions/versions.md`, `P/research/43-convergence.md` |
| Every decision with its source, 279 quotes checked | `P/architecture/00-ledger.md` |
| Reviews and fixes | `P/architecture/review/` (R0, R1, FC1, R1-FIXES) |
| What the plan was before and after | `A/plan-original.md`, `A/plan-current.md`; sources in `P/build/plan-parts/` |
| Screen notes for the UI session | `P/build/UI-NOTES-UNITS.md`. No UI code in this work (`STATE:123`) |
| The prompts the build ran from | `P/build/PROMPT-ORCHESTRATOR.md`, `P/build/BRIEF-BUILDER.md` |
| Each agent's brief | `P/architecture/briefs/` |
| Research, one file per question | `P/research/` (48 files), table in `STATE.md` from line 337 |
| His raw sessions | `P/operator/`: `transcript-2026-10-20-to-28.md`, `-10-29-to-30.md`, `-10-30-to-31.md`, `-10-31-to-11-05.md`, `session-wrapup-coordination-…`, `session-qma-v2-workflow-design-2-…` |
| The earlier decision map | `P/wayfinder/MAP.md`, `P/wayfinder/tickets/` |
| Earlier build plans that shipped well | `tracker/qma-v2/DATA-PLAN.md`, `LOCAL-FIRST-PLAN.md`, `PROMPT-DATA.md` on `plan/unit-system` |
| The build's store | `D:/QMX-worktrees/unit-ship/` (`RESUME.md`, `decisions.tsv`, `dispatch/`, `review/`). You sorted its loose-end lists, so they need no second read |

Read old Hermes logs only through the extracts. The raw logs hold credentials.

## 6. How 73 became 91

CHECKED with `git log -S` on `UNIT-PLAN.md`. All 18 added sections came through planner commits:

| Commit | Date | Sections | Trigger |
| --- | --- | --- | --- |
| `6ecbd5c1` | 3 Nov | C-12d, C-25, C-26, C-27, C-28, C-29, C-30 | The validity check of C-14, C-17, C-20 and C-21 the coordinator asked me for, which found these gaps against the built stack |
| `a205ddc1` | 3 Nov | C-27a | C-27 contradicted its own done line |
| `e5253804` | 3 Nov | C-12e, C-26b, C-31, C-32, C-33, C-34, C-35, C-36 | The 102-item loose-ends pass, and his MCP ask for C-36 |
| `231c324c` | 3 Nov | C-37 | C-12d's review |
| `87173a4b` | 4 Nov | C-38 | His rulings on the five items |

The 9 fix PRs were outside the plan. The coordinator raised them for red checks.

He gave permission, expecting two or three PRs. Your plan check found each addition justified, and I still agree with that item by item. What I got wrong: each section became its own PR until his clustering ruling of 4 November, and I never told him the running total or asked why a plan needed this many corrections. **PLANNER'S VIEW:** the growth was a symptom. Parts were being built and tested alone, against fakes kinder than the real neighbour. That is the same cause you found behind the 30 must rows.

## 7. Skills: what planning used, by measurement

MEASURED BY me this morning from 66 agent transcripts: an agent counts as using a skill when a Read, Bash, Grep, Glob or Skill call names it. Skill text pasted into a brief would not show. A few relaunched agents are counted twice. Paths: `~` skills are in `C:/Users/Mubarak/.claude/skills/`, BMad skills in `C:/Users/Mubarak/Desktop/QMX/.claude/skills/`.

| Step | Output | Skills the brief asked for | Opened by the agents |
| --- | --- | --- | --- |
| Grounding (30-31 Oct) | `research/17-19, 34, 42`, `architecture/grounding/` | poteto-mode Investigation, `how` | poteto-mode, sometimes `how` |
| Map | `wayfinder/` | `wayfinder` | `wayfinder` |
| Solutions | `funnel/solutions/` | `bmad-party-mode`, `bmad-brainstorming` | Both |
| His day | `funnel/experience/` | `bmad-cis-design-thinking`, `bmad-cis-problem-solving` | Both |
| Edge cases | `funnel/edge-cases/catalogue.md` | `bmad-review` edge-case lens, `bmad-advanced-elicitation` | Both, though the edge-case lens file itself was not named |
| Versions and Level 0 | `funnel/versions/`, `level-0/` | `bmad-party-mode`, `principle-exhaust-the-design-space`, `codebase-design`, `domain-modeling`, `bmad-architecture`, `blast-radius` | All |
| R0 review | `review/R0-level-0.md` | `bmad-review`, `blast-radius` | `bmad-review` only |
| Part A | `parts/A-…` | `bmad-architecture`, `codebase-design`, `principle-exhaust-the-design-space`, `blast-radius` | All |
| Parts B and C | `parts/B-…`, `parts/C-…` | The same | `bmad-architecture` and `lint_spine` only |
| R1 full review | `review/R1-findings.md` | `bmad-review`, `blast-radius` | **poteto-mode only** |
| R1 fixes and fix-check | `R1-FIXES-*`, `FC1` | `bmad-architecture`, `blast-radius` | As asked |
| Plan and prompts | `build/` | poteto-mode `multi-phase-plan`, `autopilot-stack`, `check-plan`, `technical-writing`, `unslop` | All of those |

Files holding the method: `P/architecture/00-workflow-and-skills.md` (his ruled workflow, which skills stack at each step, and how live-conversation skills run inside a sub-agent), `P/STANDING-ORDERS.md` (pasted into every planning brief), and my memory `C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/memory/planning-workflow-that-worked.md` (the 12-step workflow, "scale it, never skip it").

**Facts that will bite if you run these skills** (detail in `00-workflow-and-skills.md` §3): QMX's BMad overrides in `_bmad/custom/` still route to the retired factory, so tell agents to ignore those endings. BMad writes to the main checkout by default, so pass an absolute `doc_workspace`. Live-only skills do not run inside a sub-agent. CIS needs YOLO at its first checkpoint. `wayfinder` and `improve-codebase-architecture` cannot be invoked by the Skill tool, only read and followed.

**PLANNER'S VIEW on the stack for the replan.** This is medium work on built code, so use his cut-down set from the memory file above. He asked for a cluster of skills, and this is my suggestion. You choose after reading them:

| Stage | Skill | Use |
| --- | --- | --- |
| Understand | `how`, poteto-mode `playbooks/investigation.md` | Each legacy subsystem a repair touches, read at the code |
| Blast radius | `blast-radius` | Prove the one safety fact per seam by running real code |
| Shape | `codebase-design`, `principle-subtract-before-you-add`, `principle-migrate-callers-then-delete-legacy-apis` | Deep modules, delete before adding, and the deletion plan |
| Order | `principle-sequence-verifiable-units` | Each repair ends in a checkable state, foundation first |
| Real proof | `principle-prove-it-works`, `principle-test-behavior-not-implementation`, `bmad-review` verification-gap lens | Tests across real connections, not kinder fakes |
| Hard cases | `bmad-review` edge-case lens, against `catalogue.md` | Failure paths, as he asked on 22 October |
| Write the plan | poteto-mode `playbooks/multi-phase-plan.md`, `check-plan.mjs`, `technical-writing`, `unslop` | The plan itself, checked to 0 problems |
| Review the plan | A fresh Opus agent with `code-review` (Spec axis) and `bmad-review` | The step I skipped |
| Build | poteto-mode `playbooks/feature.md`, `playbooks/autopilot-stack.md`, `tdd`, `show-me-your-work` | The builder's stack |

Skip party mode and CIS unless a repair really needs new design, since generating ideas is not the problem here. Use `bmad-architecture` only if a repair changes a spine decision, and amend the spine in that case. Whatever the list, carry your transcript check into the build, because a list alone failed.

## 8. Your 13 set-aside questions, against the record

He says most agent questions are already answered in the plans. Here is what the record says, so fewer reach him (`A/FOR-HIM.md` numbering):

| # | Question | What the record says | Still for him? |
| --- | --- | --- | --- |
| 1 | Where does the stack land? | "The merge target is decided later; never `main`" (`STATE:282`). 5 Nov: "most of the code will be merged back to engine/base or something", and the repair must not work on that branch. See section 9 | Only the final target, and only when landing nears |
| 2 | Dummy skips the judge? | Closed by him on 5 Nov | No |
| 3 | SQS before the demo? | "Kill switch and SQS stay" (risk STATE:320). Where it sits is the risk session's. C-20 must not delete the only gate first | No. Hand to risk, hold C-20 |
| 4 | Old QMB door goes? | "Build on, enhance or scrap" (`STATE:113`). Large deletions need his word | Later, with evidence |
| 5 | `qmf-indicators`, `qmf-structure` | The architecture names them as built: catalogue code in `qmf-indicators` (Level 0:57) and TA-Lib wrappers plus swing points as dictionary inputs (part A `4-dictionary.md:20`). A4's lane 6 runs `qmf-indicators`' tests. Check whether the dictionary port really dropped them before calling them unused | Only after that check |
| 6, 7 | Flatten, and RED on unheld positions | Kill effects are placeholder 18: RED closes positions at the scope, and the numbers are the risk session's. The button doing what it claims is yours | No |
| 8 | Does R include costs? | Open with the risk session (risk STATE:322, 342) | Risk session |
| 9 | "Live logins never in QMX" | R:29 and C-21 come later. Nothing to build now | Later |
| 10 | MIS widens or narrows a unit? | Narrow. Widening is a new version plus his click (risk STATE:22(c)). The MIS reads and publishes, and units pick (`STATE:190`). Only he promotes | No |
| 11 | Market board feed | Safe unstarted today because units fall back to every admitted market (TRIAGE:49). Keep it unwired or finish it, your call | No |
| 12 | Futures and other data kinds | "Design for futures… placeholders, or what works" (`STATE:101,115`). See below | Later |
| 13 | Engine change batch | Ask once, batched (TRIAGE:55). The trigger was "after G-DEMO", so it needs a new trigger in the new order | Yes, once |

**On futures and order flow.** On 3 November he concluded that QMX only needs a broker it can send orders to and a data feed. He does not need a charting platform. Free order flow applies to crypto only, and exchange-grade futures order flow needs a paid feed. He wants data providers added in Settings with a click or an API key, and order flow available to units. He may start with crypto, and an order-flow unit may be among his first. **That track is not planned.** I offered and he has not said go. IBKR research was stopped by him. Do not widen into it, but note its seams: `qml/src/qml/compile/compiler.py:496` refuses `reads`, the unit runtime gets bars only, and QMB cannot replay trades or books. Your cluster 5 touches those same lines. Discussion in `P/operator/transcript-2026-10-31-to-11-05.md`, 3 November 13:42 onward.

## 9. Branches and plan mechanics

CHECKED this morning:

| Ref | At | What |
| --- | --- | --- |
| `origin/engine/base`, `build/unit-system` | `c93407ca` | The root. His good code, where PRs 207 to 234 landed. Nobody moves it but him |
| `build/us-<id>` | One per PR, worktree `D:/QMX-worktrees/bld-us-<id>` | The stack |
| `build/us-c28` | `db948daa` | Last row actually stacked |
| `build/us-c35` | `f9607cd4` | PR 327, on top of c28 |
| `build/us-c14` | `50c83a4e` | PR 328, on top of c35, 390 commits above the root. Its worktree holds an uncommitted edit to how the script finds his login |
| `origin/main` | `c3e8ec5e`, 27 Sep | Only his click moves it |
| `origin/integration` | `a0e87697`, 30 Sep | Not ready for code (`CLAUDE.md`) |
| `plan/unit-system` | `6d0a550e` | This plan. Worktree `D:/QMX-worktrees/unit-plan` |

**PLANNER'S VIEW on his branch question.** Plan on `plan/unit-system` beside this file, in something like `P/build/REPAIR-PLAN.md`. Build on fresh `build/repair-<n>` branches stacked from `build/us-c14` once that uncommitted edit is settled, since you decided PRs 327 and 328 stay. Nothing commits to `engine/base`. He should confirm this; he said he wanted to ask about the branch himself.

**Plan mechanics, if you amend `UNIT-PLAN.md`.** Edit `P/build/plan-parts/`, then from `P/build` run `node plan-parts/assemble.mjs`, then `node C:/Users/Mubarak/.claude/skills/poteto-mode/scripts/check-plan.mjs UNIT-PLAN.md`. The assembler reads every slice id on a `**Depends on.**` line and refuses forward references, so keep notes off that line. Each section needs the nine blocks and ten lanes. `build/` is git-ignored but tracked, so use `git add -f`. A new plan file needs the same checker run on it.

## 10. Standing rules a new agent trips on

- He is non-technical and dictates. "Potato mode" is poteto-mode, "KMX" is QMX, "Febble" or "Fibble" is Fable. Plain short replies, no codenames, no PR ids without their plain name. Decisions go through the question tool, explained first, only when truly his: money, his values, words on his screens, irreversible scope.
- Nothing merges without his word. Never push `main`. Permanent deletion is his click.
- Agents never touch money or reach a live account. His live logins stay in his browser. Agents' cTrader MCP tools work on demo accounts only. Only he promotes.
- Never read, print or copy keys or tokens. Broker credentials live in Windows Credential Manager under `qmx/*`. Never open `auth.json` or `.env`.
- Never touch `C:/Users/Mubarak/Desktop/DATA_NARL` or `Documents` contents.
- Sub-agents: Opus 5.5, model named on every spawn, told not to spawn. No Fable unless he asks. Never `bulk-worker`. They never wait on long commands, because their cache expires, so the orchestrator runs long tests in the background with time limits. One agent per job. When new information changes a running agent's job, stop it and start fresh.
- Cluster: six to nine bugs is one to three PRs. A finding must be justified as a real bug before planning. Windows is first class, disk `D:` for temp and caches, since `C:` runs full. No caps inside QMX. Never mention Firecrawl.
- His timelines are plans, not orders to cut queued work. He wants the risk session back soon, and the build's weekly usage has been a sore point. Be efficient.

## 11. What I did not do

- I did not re-read every file listed here this morning. I read `STATE.md` lines 1-147, the prompts, the brief's skills table, the placeholders file, the triage and your reports, then took the rest from file listings, searches and the record. Treat the "why" rows as pointers.
- I did not re-verify the audit's findings or read your per-part reports other than `plan-check.md`.
- The coordinator's measurements in section 4 come from my memory note of its report (`memory/orchestrator-audit-2026-11-04.md`), not from a rerun.
- The new transcript extract was scanned for key-shaped strings by pattern and nothing matched. That is a pattern check, not a guarantee.
- This session's full log is `C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/ed09cf0c-69f1-44ab-8c6b-76992918774a.jsonl` (31 MB), with agent transcripts in the folder of the same name. Search it, don't read it.

If something here conflicts with the code, the code wins for what is. If it conflicts with his newest word, his word wins for what should be. If you need a judgement about why the plan says something, ask me through him.
