# QMX build program

This program rebuilds QMX on the final design. It follows `architecture/workflow-engine/`, `architecture/library-and-data/` and `architecture/lab-and-pods/` as amended by `research/methodology/39`, `43`, `47` (with "Review 48 applied") and `48`, the re-triage in `40`, and rulings 1 to 119 in `26`.
The operator gets one host program where his copilot and his workflows run at once, agent steps that do real work, one tool catalog and one chat builder, one Library with memory on Hindsight, an in-house router and account pool with no QMX caps, remote runs covered end to end, and about 122,600 lines of old runtime deleted.
The rule it enforces is that every probe runs before the work it gates, every PR proves its point with a check that ran green at its head, and nothing is deleted before its replacement passes.
There are 58 PRs in 15 phases, in the order of the table under "Spawn owners". Forty-seven need neither his server nor his merge click. Nine need his server reachable for the builders. RUN1b, DEL1 and DEL4 also wait for his merge click. No PR waits for a paid machine.
The stack roots on `engine/base` at `132169c71c3bb372c67ab330066f938e5dc6a56d`. After his merge click of `engine/base` into `rebuild/base`, it roots on `rebuild/base`.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a short preamble. It names the triage rows (B-n, L-n and AL-n of `40-retriage.md` section 2) where there are any, the AD ids (engine unless marked Lib or Lab), the probe or check that proves it, its gate, the scenarios of `46-domain-expansion.md` section 5 it serves (K-n, or a section 5.0 row), and the done line. Then come the nine blocks `check-plan.mjs` requires.

Path shorthands, used in every Files block.

- `E/` is `qmx-agents/packages/qmx-engine/src/qmx_engine/` and `ET/` is `qmx-agents/packages/qmx-engine/tests/`. `T/` is `E/templates/`.
- `H/` is `qmx-agents/packages/qma-harness/src/qma/harness/` and `HT/` is `qmx-agents/packages/qma-harness/tests/`. `G/` is `qmx-agents/packages/qma-harness/src/qma/gpt/`.
- `QX/` is `qmx-agents/packages/qmx-control/src/qmx_control/`, `AP/` is `qmx-agents/packages/qmx-apps/src/qmx_apps/` and `RM/` is `qmx-agents/packages/qmx-remote/src/qmx_remote/`.
- New packages. `HO/` is `qmx-agents/packages/qmx-host/src/qmx_host/`, `R/` is `qmx-agents/packages/qmx-router/src/qmx_router/`, `LB/` is `qmx-agents/packages/qmx-library/src/qmx_library/`, `MM/` is `qmx-agents/packages/qmx-memory/src/qmx_memory/` and `HB/` is `qmx-agents/packages/qmx-hub/src/qmx_hub/`. Each has a `tests/` folder beside `src/`.
- `SL/` is `scripts/live/` and `SP/` is `scripts/probes/`. `CP/` is the core plugin `qmx-agents/plugin/`.
- The store is `D:/QMX-worktrees/qma-ship/build/`. The ship home with the plan login is `D:/QMX-worktrees/qma-ship/home`.

The program runs `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md`. Its selection rule picks it, because the work is sequenced and the operator reviews before anything lands. Nothing merges in this program. The coordinator appends each verified PR to one linear stack, and the operator lands it himself.

The plan makes nine overrides of that playbook and of poteto-mode. Each is named again where it applies.

- Override 1 replaces the owner of autopilot-stack step 1. One `poteto-agent` builder on `opus` per PR runs on the operator's PC in its own worktree, not a Cursor cloud agent. `/deslop` is not installed, so the builder rereads its full diff instead. No Bugbot runs on this repo.
- Override 2 replaces the verdict of step 4 with the operator's light rule. One build and one check per PR. The coordinator runs the check itself and spawns no checker agent. Only blockers and anything touching his logins, keys or stores block. Low findings go to `lows.md` and never block. One fix round per PR.
- Override 3 is the lane count. `check-plan.mjs` demands ten lanes per PR. Here the ten lanes are a menu, not a quota. Lanes 1 to 4 are the proving set the coordinator runs, plus at most one menu lane it judges likeliest to break the PR's point. A lane box outside the run set is checked with a `ledger.tsv` row that says `menu, not run`.
- Override 4 is the perf block. No speed gate runs unless speed is the PR's point. Every perf block records a number and fails nothing, except where its Rule box names a fail line.
- Override 5 is the rebase cadence. A PR's one fix round finishes before a PR that shares a file with it is built on top. The stack is rebased once per fix, never per round.
- Override 6 is one planned rebase at his merge click. When `rebuild/base` first holds `engine/base`, the root rebases the chain onto `rebuild/base` once and retargets the root PR. The six files `rebuild/base` adds touch no PR before RUN1b, so patch-ids stay the same.
- Override 7 is the gated-PR rule. A PR whose gate is closed (his server step or his merge click) is skipped, never waited on. When the gate opens, the PR is built on the stack tip of that moment and appended there. It never goes into the middle of the verified stack.
- Override 8 replaces poteto-mode's "fresh subagents by default" for fix rounds. The same builder is resumed for its one fix round, because a fresh agent rereads the design, the plan and the code (`WORKFLOW-SHIP-PREP.md` lesson 10). Every other new task gets a fresh agent.
- Override 9 is pipelining. While the coordinator checks PR N, the builder of a later PR may start on N's code-ready head only when the two Files blocks share no file (Appendix F). It rebases once onto N's verified head.

Opus checking Opus is weaker than a review across model families. Every verdict says so in its first lines. No Fable runs in this program.

Defaults are marked. Every value this plan sets that the operator did not choose says "Claude's default" where it appears, and Appendix H lists them all.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Check the bases. Run `git -C D:/QMX-worktrees/agent-system fetch origin`, then `git rev-parse origin/engine/base`, which must print `132169c71c3bb372c67ab330066f938e5dc6a56d`. Then run `git merge-base --is-ancestor origin/engine/base origin/rebuild/base`. Exit 0 means his merge click has landed and the stack roots on `rebuild/base`. Exit 1 means it has not, and the chain roots on `engine/base` until the gate (Override 6). Then run `git merge-tree --write-tree origin/rebuild/base origin/engine/base` and log whether it is clean. It was clean on 2026-10-18. Log all three results in `decisions.tsv`.
- [ ] Read the plan from its branch with `git -C D:/QMX-worktrees/agent-system show plan/agent-system:tracker/qma-v2/HARDENING-PLAN.md`. If the file is not committed there, stop and ask the operator to have it committed, because every tick re-reads it from the branch.
- [ ] State the protocol and this plan to the operator in plain words, then stop. Start only on his explicit go.
- [ ] In the same message, list what only he can do, with a time for each. Log his answers in `decisions.tsv`.
  - [ ] Say go. About one minute.
  - [ ] Click the merge of `engine/base` into `rebuild/base` when he chooses. About two minutes. RUN1b, DEL1, DEL4 and the landing wait for it. Nothing else does.
  - [ ] Make his Contabo server reachable for the builders when the server phase comes (the server step). That means SSH over Tailscale from the PC, plus `/login` once in a plan home there if he wants plan turns on the server. About 20 minutes, once. Nine PRs wait for it and are skipped until then (Override 7).
  - [ ] Type `/login` once in the ship home only if a lane reports that the plan login in `D:/QMX-worktrees/qma-ship/home/claude` expired. Two minutes, at most once.
  - [ ] Optional. Sign in to his GPT account once in the ship home, so the GPT halves of PRB-R, RTR4 and RTR6 run. Five minutes. Without it those rows record `not run, no GPT sign-in`.
  - [ ] Optional. Add direct provider keys to the keyring as `qmx/<provider>` if he wants direct Kimi, GLM, DeepSeek, Qwen or MiniMax rows proven. Without them the OpenRouter rows stand in, in provider-proof lanes only.
  - [ ] Keep the PC awake and plugged in. Do not start `qma.serve` or `qmx_host` on the ship home while the run is live. The coordinator also requests keep-awake through `mcp__ccd_host__request_keep_awake`.
- [ ] Read these at program start and at every tick. Log each read in `decisions.tsv`.
  - [ ] `git show origin/main:CLAUDE.md` for the project rules on trunk, then Read `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`, whose QMA v2 section is newer.
  - [ ] This plan, from `plan/agent-system` as above.
  - [ ] `research/methodology/26-operator-rulings-and-alignment.md`, all sections. Its latest ruling wins over every other file.
  - [ ] `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md`, `shipping.md` and `opening-a-pr.md`, then `C:/Users/Mubarak/.claude/skills/no-comments/SKILL.md` and `show-me-your-work/SKILL.md`.
- [ ] Confirm the shell before any command. The PC runs Windows 11 with PowerShell 7 and Git Bash. Log which one each brief uses.
- [ ] Create the store with `decisions.tsv`, `ledger.tsv`, `lows.md`, `BACKLOG.md`, `RESUME.md`, `evidence/`, `review/` and `homes/`. Write these standing orders into `decisions.tsv` as its first rows.
  - [ ] Builders are `poteto-agent` on `opus`. Never `bulk-worker`. No Fable. Every brief names its model and says "do not spawn sub-agents".
  - [ ] At most two builders at once, and never two that share a file (Appendix F). The coordinator checks every PR itself.
  - [ ] The whole app is unlocked (ruling 118). A PR may refactor, delete and rebuild anything its Files block names, and touches nothing else.
  - [ ] No step reads, prints or copies a plan token, a provider key or a ChatGPT token. Secrets are named by keyring reference only. No step spends on any Anthropic or OpenAI API. Plan turns go through the CLI login in the ship home.
  - [ ] Agents have no path to money, and no PR builds money machinery (rulings 116, 118). No PR touches a broker credential or a money act. `propose_order` keeps asking.
  - [ ] Tests run on `claude/haiku` through the plan login. OpenRouter runs only in a lane that exists to prove another provider works. There is no spend cap.
  - [ ] No QMX usage cap is added anywhere (ruling 106). A probe bound, such as P2's 20 turns, is a probe bound and says so.
  - [ ] Scripts and agents run locally by default (ruling 117). No PR forces a container or a server.
  - [ ] Every probe runs before the work it gates. A failed probe triggers the fallback this plan names for it, never improvisation.
  - [ ] Nothing is deleted before its replacement passes. No remote compute is deleted before the remote worker passes E57 on a real machine.
  - [ ] No unplanned work. A gap, bug or idea outside a PR's section goes to the store's `BACKLOG.md` as one line, and the reply mentions it.
  - [ ] Every test gate and lane runs with every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA` unset, and with `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`.
- [ ] Write the standing brief `BRIEF-BUILDER.md` in the store. Copy `D:/QMX-worktrees/qma-ship/engine/BRIEF-BUILDER.md`. Change the plan name, the file boundary (the PR's Files block), the branch prefix `build/`, the store path, the base, and the harness rule (the harness is an ordinary module now). Keep its "Tests", "Done means", "Reply with" and "Unplanned work" sections. Drop its "Program facts so far", which belong to the last program. Add one line. Lane 1 never reruns the full `SL/qma/run_all.py` or `SL/engine/run_all.py` unless its box says so.
- [ ] On the operator's go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a stuck agent and the action taken, a gate opened, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the stacked list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every builder a zero-writes order at once.
- [ ] Keep the coordinator's context under 40 %. Before it crosses 40 %, run poteto-mode's `playbooks/pause-safely.md`, write `RESUME.md`, and ask the operator to open a fresh coordinator session with the same prompt.

### Spawn owners

The table is the build order. "After" names the PRs whose code a PR needs, and the probe PRs whose result it reads. Gates are his server step (SRV), his merge click (GATE-M), or a probe result named in the preamble. Phases are 1 hygiene, 2 probes, 3 caps, 4 fixes to kept engine code, 5 host, turn call, agent steps, guard, catalog and chat builder, 6 run list, scheduler and heartbeat, 7 Library and references, 8 mini apps as plugins, 9 memory and evals, 10 router and pool, 11 delegate, 12 templates and the copilot workflow builder, 13 local deletions, 14 the server phase, 15 the last deletions.

| # | Id | Ph | PR | Gate | After | Proving check |
|---|---|---|---|---|---|---|
| 1 | HYG0 | 1 | CI test, haiku first, no Fable, no live CLI flag, key-first roles | none | none | E38, role tests, qma-core suite |
| 2 | PRB-H | 2 | Harness probes P-SET, P-SYS, P-PERM, P-PK, P-PL, P-NM | none | none | rows in `SP/harness/FINDINGS.md` |
| 3 | PRB-R | 2 | Router probes P0, P1, P1k | none | none | rows in `SP/router/FINDINGS.md` |
| 4 | PRB-L | 2 | Local probes P-TAINT, P-MEM (PC), P-SRCH, P-NEST, P-OPS (PC) | none | none | rows in `SP/library/FINDINGS.md` |
| 5 | CAPE | 3 | Engine caps out, stuck detector in | none | HYG0 | E41, E43 engine half |
| 6 | CAPH | 3 | Harness budgets out, sends wait for a slot | none | HYG0 | E43 harness half |
| 7 | CAPX | 3 | Capacity per resource class | none | CAPE, CAPH | E58 |
| 8 | SEC1A | 4 | One redaction seam, tool key refs, published-only reads | none | CAPE | E37 |
| 9 | SEC2A | 4 | Attempt overlays, script lifetime, run context | none | SEC1A | E14, E50 |
| 10 | BUG1 | 4 | Run state and resume | none | SEC2A, CAPX | E40, B-69 lane |
| 11 | BUG2 | 4 | Spec-gap code and validation | none | BUG1 | validation and event-key lanes |
| 12 | BUG3 | 4 | Gate answers, ledger-derived state, partition ladder, one event writer | none | BUG2 | gate fold and runs-list lanes |
| 13 | HOST | 5 | One host program `qmx_host` | none | CAPH | E54 |
| 14 | TURN-H | 5 | The turn call and persisted chat options | none | HOST, PRB-H | H1 and H19 lanes, P-SET cache case |
| 15 | TURN-E | 5 | The engine drives chats through the turn call | none | TURN-H, BUG3 | x10, x11 lanes on `run_turn` |
| 16 | GUARD | 5 | The guard replaces the money gate | none | TURN-H | E56 |
| 17 | AGW | 5 | Agent steps write in their overlay | none | TURN-E, SEC2A, PRB-H | E55 |
| 18 | CAT | 5 | One operation catalog, one `qmx` server per chat | none | GUARD, AGW, PRB-H | E61 name half, P-PK path |
| 19 | SURF | 5 | The Surface builds every chat | none | CAT, PRB-H | E60 |
| 20 | RUN1a | 6 | One run list, app schedules as triggers | none | CAT, BUG3 | E57 trigger half |
| 21 | TRG2a | 6 | Trigger kinds, priority, ready-by, pause flag, failure contracts | none | RUN1a | trigger lanes, E64 local half |
| 22 | OPS1 | 6 | Heartbeat and incidents on one host | none | TRG2a, PRB-L | heartbeat lanes |
| 23 | LIB1 | 7 | The Library store, kinds, port and landing rule | none | BUG3, HOST | E10 on the real store |
| 24 | LIBM | 7 | Import the three old Libraries, dual write | none | LIB1 | migration counts |
| 25 | SES | 7 | Sessions are Library items | none | LIBM, TURN-H | session lanes |
| 26 | LIB2 | 7 | Marks, hypotheses, locators, as-of reads | none | LIB1, PRB-L | E66 |
| 27 | LIB3 | 7 | Search and ranking | none | LIB2, PRB-L | P-SRCH pass line |
| 28 | REF1 | 7 | Context references for Library kinds, runs, apps, sessions | none | SURF, SES | E62 Library half |
| 29 | PACK | 8 | Packs load as Claude plugins | none | SURF, LIB1, PRB-H | P-PL path, pack lanes |
| 30 | APP2a | 8 | Two channels, app artifacts in the Library, contracts, profiles | none | PACK, RUN1a, LIBM | E61 |
| 31 | MEM | 9 | Memory on Hindsight with the built-in search as backup | none | SES, REF1, LIB2, PRB-L | E65 |
| 32 | EVAL | 9 | The copilot eval battery | none | SURF, LIB1 | battery lanes |
| 33 | RTR0 | 10 | Move router code into `qmx_router` | none | GUARD, CAT | relay suite unchanged |
| 34 | RTR1 | 10 | Model registry and data profiles | none | RTR0 | one-token Test per row |
| 35 | RTR2 | 10 | Route by model id, normaliser, own thread | none | RTR1 | P3 key half, E43 router half |
| 36 | RTR3 | 10 | Chat-completions lane | none | RTR2 | P3 chat half |
| 37 | RTR4 | 10 | Account pool, one error classifier, `complete` | none | RTR3 | P7, E8 |
| 38 | RTR5 | 10 | The engine reads the registry and calls `complete` | none | RTR4, CAPX, SURF | E9, E29, E30 |
| 39 | RTR6 | 10 | Registry-generated sub-agents | P1k, P1 | RTR5, PRB-R | P1k on the real router |
| 40 | RTR7 | 10 | Plan lane built dark, proved, then turned on by him | P0 and P1 pass | RTR6 | P4, P2, E49 router half |
| 41 | DLG | 11 | `delegate` v2 | none | RTR4, SURF | P5, E52 |
| 42 | TPL1 | 12 | Plain template names, intake, number evidence | none | RTR5, BUG2 | E48, E51 |
| 43 | TPL2 | 12 | The copilot builds a workflow from one line | none | TPL1 | E42 |
| 44 | TPL3 | 12 | Revolution loop, panel, clippings, digest, crystallise | none | TPL2, EVAL, PRB-L | template test runs |
| 45 | QMBH | 13 | The QMB host starts `qmx_host` | none | HOST | QMB host lanes |
| 46 | DEL2 | 13 | Delete `qma-daemon` and the host forwarders | none | QMBH, RUN1a | E59 daemon scan |
| 47 | DEL3 | 13 | Delete `qma-core` and `qma-wire` | none | GUARD, DEL2 | E59 core scan |
| 48 | PRB-S | 14 | Server probes P-OPS and P-MEM on Contabo | SRV | none | rows in `SP/server/FINDINGS.md` |
| 49 | LIB4 | 14 | The Hub, claims, server primary, purge | SRV | LIB3, PRB-S | E67, P-LAT measured |
| 50 | RTRP | 14 | Run passes, vault, router on the tailnet, two hosts | SRV | RTR4 | E25, E26, E53 |
| 51 | REM | 14 | The remote worker with the sidecar | SRV | RTRP, LIB4 | E57 on Contabo |
| 52 | TRG2b | 14 | Event triggers on the Library ref log | SRV, P-EV | LIB4, APP2a, TRG2a | E63 |
| 53 | APP2b | 14 | App homes and state across machines | SRV, P-APP | APP2a, REM | P-APP path |
| 54 | OPS2 | 14 | Server runs seen and answered on the PC | SRV | OPS1, REM, PRB-S | E68, E64 |
| 55 | ADOPT | 14 | A run adopted on another machine | SRV | OPS2 | E69 |
| 56 | RUN1b | 14 | Delete the old remote runs and jobs | SRV, GATE-M | REM | E57 passed, E59 scan |
| 57 | DEL1 | 15 | Delete the `qmx_agents` runtime | GATE-M | RUN1b | E59 agents scan |
| 58 | DEL4 | 15 | Delete the LangChain family | GATE-M | DEL1 | E59 lock scan |

Changes to the order the operator gave (hygiene, caps, then one host, turn call, agent steps, tool catalog and sets, chat builder, references, heartbeat, run list and scheduler, Library, mini apps, memory, evals, router and pool, delegate, templates and the builder), each with its reason.

- The probes run second, as their own scripts-only PRs, so every probe result exists before the PR it gates. Probes that need code from a later PR run as the first Build box of that PR (P-EV in TRG2b, P-APP in APP2b, P3 in RTR2 and RTR3, P4 and P2 in RTR7, P5 in DLG, P7 in RTR4). PRB-S waits for his server.
- Phase 4 holds the triage fixes to engine code the rebuild keeps (40 section 3). AGW needs SEC2A's overlays, and the rebuild sits on the fixed ledger and run state. The door rows (B-68, L-68) and the lock rows (L-64, L-70) move into HOST, and the adapter rows into TURN-E, because those files are rebuilt there.
- The guard (GUARD) sits after the turn call. The catalog needs it first (47 section 7, CAT after HRMH).
- The run list comes before the heartbeat. Review 48 orders the heartbeat after RUN1a (47 "Review 48 applied", OPS row).
- References come after the Library store and sessions. A reference pins a Library object (AD-63), and 47 section 7 puts REF1 after SES. The `@memory` resolver lands with MEM.
- The Hub (LIB4) moves into the server phase, because it needs his server. No other Library PR waits on it.
- Remote work (RTRP, REM, TRG2b, APP2b, OPS2, ADOPT) is one server phase after the templates, because it all needs his server and nothing before it needs remote code.
- DEL1 moves after RUN1b. `RM/worker.py` imports `qmx_agents.router` and `langgraph`, so deleting `qmx_agents` before the remote worker is replaced would break the only working remote compute. 47's "DEL1 to DEL3 after RUN1a" missed that import.
- The UI is a separate session (`UI-HANDOFF.md`). No PR here builds a screen.

- [ ] Spawn one builder per PR with the Agent tool, `subagent_type: "poteto-agent"`, `model: "opus"` and `run_in_background: true`. The brief names the PR id, its plan section, the parent branch and head, and points at `BRIEF-BUILDER.md`. Briefs point at files and never paste them. Every brief says "do not spawn sub-agents".
- [ ] Follow the "After" column. Stacked work branches from the parent PR's branch at its verified head.
  - [ ] Pipelining is allowed (Override 9). Two builders may run at once only when their Files blocks share no file (Appendix F).
  - [ ] Two tracks fit that rule early. The engine track (SEC1A, SEC2A, BUG1, BUG2, BUG3) and the host track (HOST, TURN-H, GUARD) share no file, so one builder from each may run at once.
  - [ ] A gated PR is skipped (Override 7). A PR whose "After" names a skipped PR takes the last verified PR before it as its parent, unless its preamble says it needs the skipped one.
  - [ ] Apply Override 6 once, at his merge click, and log it. RUN1b and DEL1 never start before it.
- [ ] Hold the file boundaries.
  - [ ] Each PR touches only the files its Files block names, plus the store's `evidence/` and `review/` folders.
  - [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, or the ship home's `settings.toml`. QMB, QMN and QML files change only in QMBH and DEL3, where their Files blocks name them. LIBM reads QMB's registry through its as-of port and edits nothing there.
- [ ] Hold the review gates. QMBH, RTR7, TPL1 and TPL2 change his tool, his copilot's path or the templates he sees. Each posts screenshots and a video to him in chat. QMBH waits for his review before it is appended, so DEL2 and DEL3 wait with it. RTR7 ships with the plan lane off until he turns it on. TPL1 and TPL2 are appended on their clean verdict, and changes he asks for go to `BACKLOG.md`.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Run `command -v origin`. If it is missing, use `gh` and record that in `decisions.tsv`. Never require `gt`.
- [ ] Branch `build/<id>` (lowercase) from the parent branch at its verified head, in the worktree `D:/QMX-worktrees/bld-<id>`. Never use `git stash`, which is shared across worktrees. Open the PR ready, never draft, per **Opening a PR**, with `gh pr create --base <parent-branch> --head build/<id> --repo MubarakHimself/QMX`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Put `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`.
- [ ] Run `uv run --no-sync python -m poethepoet fmt-check`, `lint` and `types` once in each package the PR touches, and `uv run --no-sync python tools/secret_scan.py`, before the PR-facing push. Push with hooks on.
- [ ] Reread the full diff before each commit in place of `/deslop` (Override 1). Run `/no-comments` before the check.
- [ ] Add only the tests that prove the PR's point, at the module's public interface, with literal expected values. Typically a handful, rarely more than about 20. No test per private function, no snapshot or getter tests, no mirror-the-implementation tests.
- [ ] No full `just ci` per PR. The coordinator runs it under the CI lock `mkdir D:/QMX-worktrees/.ci-lock` five times in the program, in the checks of BUG3, SURF, TPL3, DEL3 and DEL4.
- [ ] A new package joins the `qmx-agents/pyproject.toml` workspace members, the qma-core member-set test and `tools/ci.py` in the PR that creates it.
- [ ] End each commit message with the attribution lines from the session's system reminder. End each PR body with the line the reminder names.

### Verdict and merge, for every PR (append to the stack, never merge)

- [ ] At the code-ready head SHA, the coordinator runs one check (Override 2). It reads the PR body and the diff (the full diff for files under 400 changed lines, else the files the section's Build block names), runs the PR's unit tests with `-n 2`, the gates above, lanes 1 to 4 and at most one menu lane (Override 3), and reads only the tails of the logs. It writes `review/<id>-check-<head8>.md`, whose first line is CLEAN or NOT CLEAN and whose second line is "Opus reviewed Opus. A cross-family review was not run."
- [ ] Blockers and findings on logins, keys or stores go back to the same builder, resumed for one fix round (Override 8). Low findings go to `lows.md` with the PR id and never block.
- [ ] After the fix round, the coordinator reads the fix diff, reruns the failing lane, and records the verdict in `ledger.tsv` with head SHA, parent SHA and `git patch-id --stable`. No second round runs. What is still open goes to `BACKLOG.md`.
- [ ] Append the PR to the stack on a clean verdict, per autopilot-stack steps 5 and 6. No builder merges, arms auto-merge or closes. The operator lands the stack bottom-up into `rebuild/base` with his own clicks. `main` moves only by his squash-merge click.

### Boot recipe, for every live lane

- [ ] `git -C D:/QMX-worktrees/agent-system fetch origin build/<id>`, then `git -C D:/QMX-worktrees/agent-system worktree add --detach D:/Temp/<id>-check <head>`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Put `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`. Run `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] A lane that needs no model runs on a throwaway home under the store's `homes/<id>-<lane>`. A lane that needs a model opens the harness or the host on the ship home only while it holds the lane lock `mkdir D:/QMX-worktrees/.engine-lane-lock`, because opening a harness kills the CLI trees it finds for its home.
- [ ] Model turns run on `claude/haiku` through the ship home's plan login. A provider-proof lane adds the OpenRouter row from `SL/qma/switch_lane.py` (`OPENROUTER_ROW`) to a throwaway home, credential ref `qmx/openrouter`, and never reads the value. A lane that only needs a model to answer uses the fake model `SL/qma/fake_model.py` or the engine's fake provider.
- [ ] No lane edits the ship home's `settings.toml`, not even with a restore. A lane that needs other settings uses a throwaway home. Hash the ship home's `settings.toml` before and after each lane that opens it.
- [ ] A server lane (phase 14) runs the PR head on Contabo from a detached checkout under `/srv/qmx/check/<id>` over SSH on the tailnet, with its own throwaway home there, and removes both after.
- [ ] Save a text capture as `<slug>.log`, which is the CLI's screenshot, and a screen as `<slug>.png` with `ffmpeg -f gdigrab -i title=<window title> -frames:v 1` where a window exists. Put both in the store's `evidence/<id>/`, prefixed `owner-` or `check-`, and never overwrite another PR's files.
- [ ] Remove the lane lock, then confirm with `Get-Process` that no `claude`, `qma-cli-launcher` or `qmx_host` process from the lane is left. Remove `D:/Temp/<id>-check` with `git worktree remove`.

## Remove the red CI test, Fable and the live CLI mode, and make defaults key-first (HYG0)

Rows B-75, B-95, B-98, B-44, and the role rows of engine `DOC-CHANGES.md` row 35. ADs AD-11, AD-13. Check E38 plus the role tests. Gate none. Scenarios K-11 (a panel across model families needs key-first roles) and the test footing of every scenario. Done when `just ci` passes the qma-core member test, no default role list names Fable, test mode resolves `claude/haiku` first, a live strong role tries a Chinese key row first, and `python -m qmx_engine run --mode live` is a usage error.

**Depends on.** None. It branches from the stack base.

**Files.**

- [ ] Edit `qmx-agents/packages/qma-core/tests/test_extensibility.py` (the member set at line 136).
- [ ] Edit `E/settings.py` (lines 20 to 22 and 70 to 72), `E/roles.py` (lines 85 and 86, and the module docstring), and `E/__main__.py` (the `run --mode` option at line 56).
- [ ] Edit `ET/test_settings.py`, `ET/test_roles.py` and `ET/test_admission.py`.
- [ ] Edit `SL/engine/e09_roles.py` and `SL/engine/llm_lanes.py` only where they assume OpenRouter first in test mode.

**Build.**

- [ ] Add `packages/qmx-engine` to the expected member set in `test_qma_ui_contract_placeholder_is_not_shipped`. Nothing else in qma-core changes.
- [ ] Rewrite `_CHEAP`, `_MID` and `_STRONG` in the order `key, gpt, plan`, with the Chinese rows first in every tier, the strong tier included, using the example ids of SOLUTION-DESIGN section 9. No list names `claude/fable`. These lists are Claude's default, stay UI-editable, and are generated from the registry in RTR5. A provider with no profile is skipped at resolution, as today.
- [ ] Set `roles.live_order` to `("key", "gpt", "plan")` (Claude's default, ruling 107). Make test mode resolve each role's cheap end through the plan login first, so `claude/haiku` is the first test candidate (ruling 105). `test_only` rows are admitted only in a lane that names them as provider proof. Make the sort at `roles.py:85-86` match.
- [ ] Remove `live` from `run --mode` in `__main__.py`, so the CLI runs test mode only (AD-11). Live runs start only through the service.

**You see.**

- [ ] `python -m qmx_engine run <folder> --mode live` exits 2 with a usage error, and the qma-core suite passes.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_settings.py` asserts no default list contains `claude/fable`, that every tier's first row is a Chinese key row, and `roles.live_order`. `test_roles.py` asserts that test mode resolves `claude/haiku` first and that a live strong role tries a Chinese key row first when its profile exists. Run `uv run --no-sync python -m pytest tests -q -n 2` in `qmx-engine` and `qma-core`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` and `qma-core` suites with `-n 2` at the parent and at head. Save `hyg0-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E38 first line. Run `python -m qmx_engine run <fixture> --mode live`, then `--mode test --fake`. Save `hyg0-e38.log`. Pass when the first exits 2 with a usage error and the second runs and reads `mode: test`.
- [ ] Lane 3. Run `SL/engine/e09_roles.py` in test mode on the ship home under the lane lock. Save `hyg0-roles-test.log`. Pass when the first resolved candidate of every role is `claude/haiku` on the plan profile and one haiku turn answers.
- [ ] Lane 4. Run the qma-core suite alone. Save `hyg0-qma-core.log`. Pass when `test_qma_ui_contract_placeholder_is_not_shipped` passes and no other test changed state.
- [ ] Lane 5. Print the live candidate order of `planner` on a throwaway home with a Kimi profile row and no key. Save `hyg0-roles-live.log`. Pass when Kimi is first and resolution skips it without a key.
- [ ] Lane 6. Grep the engine source and templates for `fable`. Save `hyg0-fable.log`. Pass when no default names it.
- [ ] Lane 7. Run `python -m qmx_engine --help` and `run --help`. Save `hyg0-cli.log`. Pass when `--mode` offers `test` only.
- [ ] Lane 8. Run the `llm_lanes.py` provider-proof lane on the OpenRouter row. Save `hyg0-provider-proof.log`. Pass when it names the row as provider proof and one call answers.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `hyg0-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `hyg0-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Role resolution time in ms for all roles.
- [ ] Probe. Lane 3's resolution step, three times.
- [ ] Baseline. The parent head, same probe.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. HYG0 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends HYG0 as the root of the stack.

## Settle what the Claude Code program does before the harness is rebuilt (PRB-H)

ADs AD-53, AD-55, AD-60, AD-61, AD-62. Probes P-SET, P-SYS, P-PERM, P-PK (with P-TG only if P-PK fails both ways), P-PL and P-NM, exactly as `HARNESS-REQUESTS.md` "Probes named above" and SOLUTION-DESIGN section 28.8 write them. P-FK is not run, because the session fork is backlog (Appendix G). Gate none. Scenarios K-02, K-21 and 46 section 5.0 "Agentic vs non-agentic workflows". Done when `SP/harness/FINDINGS.md` holds one PASS or FAIL row per probe with its evidence and the fallback it triggers, and the coordinator has told the operator in plain words what changed.

**Depends on.** None. It branches from the stack base and shares no file with any PR.

**Files.**

- [ ] Create `SP/harness/common.py`, `test_probes.py`, `p_set.py`, `p_sys.py`, `p_perm.py`, `p_pk.py`, `p_tg.py`, `p_pl.py`, `p_nm.py` and `FINDINGS.md`, and the fixture folder `SP/harness/fixtures/` with two small pack plugin views.
- [ ] Reuse `SP/engine/raw_client.py` and `SP/engine/common.py` by path. Do not edit them.

**Build.**

- [ ] Drive the pinned `claude-agent-sdk` 0.2.166 and its bundled CLI 2.1.299 directly, with haiku under the ship home's plan login, `setting_sources=[]` and `strict_mcp_config=True`. No probe imports the harness, so the results describe the CLI, not QMX code.
- [ ] Write each probe's pass and fail lines into its script as literal checks, then record the result and the fallback it triggers in `FINDINGS.md`.
  - [ ] P-SET pass means TURN-H passes Claude settings by file path. Its fail means settings stay on the command line and the append text goes through `--append-system-prompt-file`, which passed in HP0 S20. If its cache case fails (no cache read across two folders), the fallback is Claude's default. An agent chat's working folder stays the workflow's shared workspace, as built, and AGW passes the overlay as an added folder with write rules scoped to it.
  - [ ] P-SYS size, cache and resume cases. A resume-case fail means a slot change starts a fresh chat seeded with the session recap (SURF reads this row). A size fail means slots keep within the command-line check and spill to skills.
  - [ ] P-PERM, the declared `Bash` writing outside the overlay included (review 48 H3). A fail means AGW is not built, agent steps stay read-only as built, and the coordinator tells the operator.
  - [ ] P-PK with both paths, `tools/list_changed` and `reconnect_mcp_server("qmx")`. A pass on either picks CAT's path. If both fail, run P-TG with the review 48 cases. P-TG pass means CAT serves one server per toolset with toggling. P-TG fail means pack tools join at the next turn by resume.
  - [ ] P-PL with the review 48 cases (a pack joining by relaunch-by-resume, no agents or commands from an enabled pack outside the set). A fail means PACK materialises one combined plugin view per pack set.
  - [ ] P-NM with names of 64, 65 and 80 characters and one with a dot. The result sets the length CAT's wire-name check enforces.

**You see.**

- [ ] `FINDINGS.md` has a PASS or FAIL row for each of the six probes, with the fallback each one triggers and the log it came from.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_probes.py` runs each probe's verdict function on two recorded fixtures, one passing and one failing, and asserts the literal verdict. Run `uv run --no-sync python -m pytest scripts/probes/harness -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run `git diff --stat <parent> HEAD`. Save `prb-h-regression.log`. Pass when only `SP/harness/` changed.
- [ ] Lane 2. Run `p_set.py` and `p_sys.py` under the lane lock. Save `prb-h-set-sys.log`. Pass when each case ends in PASS or FAIL with `cache_read_input_tokens` recorded for the cache cases.
- [ ] Lane 3. Run `p_perm.py` under the lane lock. Save `prb-h-perm.log`. Pass when the log shows, for every call, which of the hook, the CLI rules, `can_use_tool` and the policy saw it, and ends in PASS or FAIL.
- [ ] Lane 4. Run `p_pk.py` and `p_pl.py` under the lane lock, then `p_tg.py` only if `p_pk.py` failed both paths. Save `prb-h-pk-pl.log`. Pass when each ends in PASS or FAIL per its lines.
- [ ] Lane 5. Run `p_nm.py` under the lane lock. Save `prb-h-nm.log`. Pass when each name length has a recorded load result.
- [ ] Lane 6. Run `p_pk.py` a second time. Save `prb-h-pk-repeat.log`. Pass when it gives the same verdict as lane 4.
- [ ] Lane 7. Hash the ship home's `settings.toml` and list `~/.claude` before and after lanes 2 to 5. Save `prb-h-home.log`. Pass when both are unchanged.
- [ ] Lane 8. Count the haiku plan turns from the probe logs. Save `prb-h-turns.log`. Pass when the count is recorded for Appendix E.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `prb-h-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `prb-h-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Launch time in ms of a chat with the core plugin and two pack views.
- [ ] Probe. P-PL's launch, three times.
- [ ] Baseline. A launch with the core plugin only.
- [ ] Rule. No fail rule. Recorded for PACK.

**Review gate.** None. The coordinator reports each probe's result and fallback to the operator in plain words.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends PRB-H on HYG0.

## Settle native sub-agents under the plan login before router code (PRB-R)

Rows AL-6 (the probe part). ADs AD-38, AD-29, AD-50. Probes P0, P1 and P1k of SOLUTION-DESIGN section 26.14, exactly as written there. Gate none. Scenarios K-11 and 46 section 5.0 "Provider limit mid fan-out; mixed providers per sub-agent". Done when `SP/router/FINDINGS.md` holds one PASS or FAIL row per probe with its evidence, and the coordinator has told the operator in plain words what P1 means for his copilot.

**Depends on.** None. It branches from the stack base and shares no file with any PR.

**Files.**

- [ ] Create `SP/router/common.py`, `test_router.py`, `router.py`, `p0_parity.py`, `p1_definitions.py`, `p1k_key_mains.py` and `FINDINGS.md`.
- [ ] Reuse `SP/engine/raw_client.py` and `SP/engine/common.py` by path. Do not edit them.

**Build.**

- [ ] In `router.py`, write a loopback test router for probes only. It forwards `claude-*` requests to `api.anthropic.com` with the body and the raw header list unchanged. It answers third-party ids from an echo upstream. It records every method and path. It never writes an `authorization`, `x-api-key` or `cookie` value. It compares those values between two runs in memory only and writes `same` or `different`.
- [ ] In `p0_parity.py`, run the same haiku turn with one `qmx` MCP tool call twice under the ship home's plan login, through a raw SDK client. Once with no base URL, once through `router.py` in record mode. Compare every header and body field, excluding only the fields P0 names. If a difference appears, retry with `ENABLE_TOOL_SEARCH=true` and any env value that restores it, and record which one did.
- [ ] In `p1_definitions.py`, launch a haiku main under the plan login with `agents={"kimi-reviewer": AgentDefinition(model="kimi/k3", ...)}` through `router.py` with a Kimi echo upstream. Record whether the sub-agent spawned, the request's `model` and agent-id header, the echo's answer as the sub-agent's result, and every method and path. Keep the raw incoming sub-agent request for RTR7's P4.
- [ ] In `p1k_key_mains.py`, launch a Kimi main on the OpenRouter Kimi row and, if his GPT sign-in exists, a GPT main, each with definitions naming a DeepSeek and a Qwen sub-agent through `router.py` with echo upstreams. Record whether each sub-agent spawned with its model id unchanged.
- [ ] Write `FINDINGS.md` with one row per probe, the observed values, PASS or FAIL per the section 26.14 lines, and the fallback each triggers. P0 or P1 FAIL means RTR7 is not built and plan mains get no third-party definitions in RTR6. P1k FAIL means key and GPT mains reach third parties only through DLG.

**You see.**

- [ ] `FINDINGS.md` has a PASS or FAIL row for P0, P1 and P1k, with the env values P0 found and the method and path list P1 recorded.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_router.py` sends a fixture request with an `authorization` header through `router.py` and asserts the recorded file holds no header value and the forwarded bytes equal the input. Run `uv run --no-sync python -m pytest scripts/probes/router -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run `git diff --stat <parent> HEAD`. Save `prb-r-regression.log`. Pass when only `SP/router/` changed.
- [ ] Lane 2. Run `p0_parity.py` under the lane lock. Save `prb-r-p0.log`. Pass when the log ends in PASS or FAIL per the P0 line, with every differing field named.
- [ ] Lane 3. Run `p1_definitions.py` under the lane lock. Save `prb-r-p1.log`. Pass when the log ends in PASS or FAIL per the P1 line and lists every method and path.
- [ ] Lane 4. Run `p1k_key_mains.py` on the OpenRouter rows. Save `prb-r-p1k.log`. Pass when the log ends in PASS or FAIL for the Kimi main, and the GPT main reads PASS, FAIL or `not run, no GPT sign-in`.
- [ ] Lane 5. Run P1's echo form twice in a row. Save `prb-r-canary.log`. Pass when both runs give the same verdict, so it can serve as RTR7's boot canary.
- [ ] Lane 6. Grep every log and recording for `sk-ant-`, `Bearer ` and `x-api-key` values. Save `prb-r-leak.log`. Pass when none is found.
- [ ] Lane 7. Hash the ship home's `settings.toml` and list `~/.claude` before and after lanes 2 to 4. Save `prb-r-home.log`. Pass when both are unchanged.
- [ ] Lane 8. Count the haiku plan turns from the run journals. Save `prb-r-turns.log`. Pass when the count is recorded for Appendix E.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `prb-r-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `prb-r-processes.log`. Pass when no `claude`, `qma-cli-launcher` or probe router process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Added latency in ms of the pass-through router per plan request.
- [ ] Probe. P0's two runs, five requests each.
- [ ] Baseline. The run with no base URL.
- [ ] Rule. No fail rule. A median above 50 ms goes into `FINDINGS.md` as a risk for RTR7.

**Review gate.** None. The coordinator reports P1's result to the operator in plain words.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends PRB-R on PRB-H.

## Settle the Library, memory and heartbeat numbers on the PC (PRB-L)

ADs AD-18, AD-5, AD-65; Lib AD-8, AD-22. Probes P-TAINT, P-MEM (PC half), P-SRCH, P-NEST and P-OPS (PC half), exactly as SOLUTION-DESIGN section 28.8 writes them with the review 48 pass lines. Gate none. Scenarios K-03, K-07, K-15, K-19, K-25 and K-26. Done when `SP/library/FINDINGS.md` holds one PASS or FAIL row per probe with its number and the fallback it triggers.

**Depends on.** None. It branches from the stack base and shares no file with any PR.

**Files.**

- [ ] Create `SP/library/common.py`, `test_probes.py`, `p_taint.py`, `p_mem.py`, `p_srch.py`, `p_nest.py`, `p_ops.py`, `questions.json` and `FINDINGS.md`.

**Build.**

- [ ] `p_taint.py` builds a synthetic 100,000-item edge table in SQLite with memory rows included (review 48 M6) and times `marks()` for an item with a 20-deep, 500-node ancestry. Pass is p95 at most 50 ms. Fail means LIB2 adds a derived closure index rebuilt from the edges.
- [ ] `p_mem.py` installs Hindsight (embedded) into a probe venv on `D:` and compares it with an FTS5 index over the same rows, built from read-only copies of his session transcripts and his `library.db` items. It asks the four question types ("already built", a dead end, a Lab-to-hub follow-up, "what did we decide about X"), measures RSS, and times one session-digest retain with a DeepSeek extractor on the OpenRouter row (provider proof). Pass is Hindsight's top 5 matching or beating FTS5's on each type, at most 2,048 MB RSS, and a retain within 30 s. Fail on RAM means Hindsight stays on the PC and server runs recall through FTS5. Fail on quality is recorded and tuned, and the choice stands (ruling 119).
- [ ] `questions.json` holds 40 questions over his real `library.db` items with the expected item ids. The builder writes them (Claude's default, because no labelled set exists), and the operator may replace them. `p_srch.py` measures the grounder's precision and coverage, the truncation constants, and ranking under fan-out noise. Pass is precision at least 0.85 at coverage at least 0.70, with no truncation dropping a top-5 hit. Fail means LIB3 tunes the constants and reruns before it is appended.
- [ ] `p_nest.py` runs the built validator on a loop whose body calls a subworkflow that holds its own loop. Fail means TPL3 adds that one exception to the validator.
- [ ] `p_ops.py` writes synthetic heartbeat rows for 20 agents at a 30 s interval on the PC for 30 minutes. Pass is a row of at most 4 KB and heartbeat work at most 1 % of one core. Fail means OPS1 sends deltas from idle hosts at a longer interval. The Contabo half runs in PRB-S.

**You see.**

- [ ] `FINDINGS.md` has a PASS or FAIL row with a number for each of the five probes.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_probes.py` checks each verdict function on a passing and a failing recorded fixture with literal verdicts. Run `uv run --no-sync python -m pytest scripts/probes/library -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run `git diff --stat <parent> HEAD`. Save `prb-l-regression.log`. Pass when only `SP/library/` changed.
- [ ] Lane 2. Run `p_taint.py` and `p_nest.py`. Save `prb-l-taint-nest.log`. Pass when both end in PASS or FAIL with the p95 recorded.
- [ ] Lane 3. Run `p_mem.py`. Save `prb-l-mem.log`. Pass when it ends in PASS, FAIL on RAM or FAIL on quality, with RSS and retain time recorded.
- [ ] Lane 4. Run `p_srch.py` and `p_ops.py`. Save `prb-l-srch-ops.log`. Pass when both end in PASS or FAIL with their numbers.
- [ ] Lane 5. Run `p_taint.py` a second time. Save `prb-l-taint-repeat.log`. Pass when its p95 is within 20 % of lane 2's.
- [ ] Lane 6. Confirm the probe read only copies of his files. Save `prb-l-readonly.log`. Pass when the hashes of his `library.db` and transcripts are unchanged.
- [ ] Lane 7. Grep the probe outputs for key-shaped strings. Save `prb-l-leak.log`. Pass when none is found.
- [ ] Lane 8. Record disk used by the probe venv and indexes. Save `prb-l-disk.log`. Pass when the number is recorded and the folder is on `D:`.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `prb-l-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `prb-l-processes.log`. Pass when no Hindsight or probe process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. The probe numbers themselves (P-TAINT p95, P-MEM RSS and retain time, P-OPS CPU share).
- [ ] Probe. Lanes 2 to 4.
- [ ] Baseline. The pass lines of SOLUTION-DESIGN section 28.8.
- [ ] Rule. Each probe's own pass line decides its row. The PR fails nothing else.

**Review gate.** None. The coordinator reports the P-MEM result to the operator in plain words.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends PRB-L on PRB-R.

## Remove the engine's usage caps and ship the stuck detector in the same PR (CAPE)

Rows AL-2, AL-3 (the strategy default), B-16, B-33, B-36, B-38, B-49, B-55, L-21, L-45, L-46, L-48, L-60, L-61, L-66, and 39 R.6 L5 (the engine half). ADs AD-40 (2), AD-16, AD-9, AD-4. Checks E41 and the engine half of E43. Gate none. Scenarios 46 section 5.0 "300-video playlist; Firecrawl pipeline" and "Provider limit mid fan-out", and K-23. Done when `settings.DEFAULTS` holds no runaway, turn, tool-call or run-time entry, no shipped template carries a `runaway` block, `timeout.run_seconds` or agent `max_turns`, and the stuck detector stops a looping or flailing agent while a converging fixer, a pager and a slow prefill run on.

**Depends on.** HYG0 (`E/settings.py`, `E/roles.py`).

**Files.**

- [ ] Edit `E/settings.py`, `E/admission.py`, `E/roles.py` (the degrade path at lines 95 to 110), `E/watchdog.py`, `E/runner.py`, `E/core/ladder.py`, `E/core/commands.py`, `E/core/fold.py`, `E/core/ready.py`, `E/core/simulate.py` and `E/core/state.py`.
- [ ] Edit `E/definition/model.py`, `E/definition/lint.py` and `E/definition/schema/qmx.workflow.1.json`.
- [ ] Edit `E/nodes/base.py`, `E/nodes/llm.py`, `E/nodes/agent.py`, `E/ports/inbox.py` and `E/ports/settings.py`.
- [ ] Create `H/stuck.py` for the pure chat rules of the stuck detector (no progress, loop signature, no convergence) and export its names from `H/__init__.py`. Create `HT/test_stuck.py`.
- [ ] Edit every `T/*/definition.json`, the three `T/_shared` folders that carry `max_turns`, and `T/rv-weekly-review/scripts/lint_edits.py`.
- [ ] Edit `ET/test_ladder.py`, `test_agent.py`, `test_lint.py`, `test_settings.py`, `test_definition.py`, `test_watchdog.py`, `test_admission.py`, `test_templates.py`, `planted.py`, and the fixture `ET/fixtures/workflows/bad-agent-no-max-turns/`.
- [ ] Edit `SL/engine/x08_watchdog.py`, `SL/engine/x11_agent_chunks.py` and `SP/engine/p_limits.py`. Create `SL/engine/e41_stuck.py` and `SL/engine/e43_no_caps.py`.

**Build.**

- [ ] Delete `runaway.*`, `on_runaway`, `agent.max_turns`, `agent.max_tool_calls`, `timeout.agent.run`, `timeout.script.run`, `pool.accounts.*.background_share` and `budgets.max_live_chats` from `DEFAULTS`. Read `max_live_chats` from the harness slot table through `SettingsPort` instead. Set `pool.strategy` to `least_used` (Claude's default). Keep `limits.interactive_reserve` 2.
- [ ] Delete the runaway guard and the degrade path from the ladder, the runner, the fold, the commands and `roles.py`. An old document's `runaway` folds to nothing with one `info` line.
- [ ] Delete every template's `runaway` block, node `timeout.run_seconds` and agent `max_turns` and `max_tool_calls`, and the schema defaults. Lint refuses only a value below 1 that he wrote. Every template's content hash changes, which TPL1's E48 re-tags.
- [ ] Honour a `limits` block he wrote (`tokens`, `turns`, `tool_calls`, `wall_seconds`) as a pause with one `info` line, checked at each turn end and every tick. `wall_seconds` counts active time only. No template ships one.
- [ ] Move the warm-first gate from inside the agent attempt to dispatch, so a held chunk writes no `node_started` (AD-9, L-60).
- [ ] Build the stuck detector of AD-16. The pure chat rules live in `H/stuck.py`, so copilot helpers use the same judgement later (H45). The engine's watchdog imports them from `qma.harness`. No progress on a sleep-aware clock gives a warning at 80 % through the inject path, then an interrupt, `timeout.grace`, and `stalled`. A model request in flight counts as progress, read from the run journal's `model_call` rows. The worker heartbeat never counts. Recorded waits are skipped. `timeout.in_tool` counts only time with no CPU and no IO on a process the engine owns. Then the loop signature on the narrow stuck digest, no convergence on error results, zero-token runs, and the crash-loop counter. The values are in Appendix H.

**You see.**

- [ ] `python -m qmx_engine check` on every shipped template prints no `runaway`, and a looping-agent fixture ends `stalled(loop)` with its summary as output.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `HT/test_stuck.py` covers a loop (5 identical calls and digests), a flailing fixer (same failing set and count), a converging fixer (5, then 3, then 1 failed), a pager over new rows, a request in flight, and a recorded wait, each with its literal verdict. `test_settings.py` asserts none of the deleted keys exists. `test_lint.py` asserts a template with no limits validates. Run `-n 2` in `qmx-engine` and `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` and `qma-harness` suites with `-n 2` at the parent and at head. Save `cape-regression.log`. Pass when head fails nothing the parent passes except tests that asserted a deleted cap, each named.
- [ ] Lane 2. E41. Run `e41_stuck.py` on the fake provider. Save `cape-e41.log`. Pass when the loop ends `stalled(loop)`, the flailing fixer ends `stalled(no_convergence)` and walks the ladder, and the converging fixer, the pager, a 400 s first-token wait and a CPU-busy script all end `passed`.
- [ ] Lane 3. E43 engine half. Run `e43_no_caps.py` with a fake row declaring a 1M window, two chunks reporting 600k tokens in all, and a run whose fake clock moves six hours. Save `cape-e43.log`. Pass when both end `passed` with no pause and no `needs_you`.
- [ ] Lane 4. Run one agent template on haiku under the lane lock. Save `cape-haiku.log`. Pass when it ends `passed` and its span shows no limit check.
- [ ] Lane 5. Write a `limits` block with `turns: 2` into a fixture and run it. Save `cape-limits.log`. Pass when it pauses with one `info` line and resumes from `runs.resume`.
- [ ] Lane 6. Run a three-chunk agent node on the fake provider with the warm-first gate. Save `cape-warm.log`. Pass when chunks 2 and 3 write no `node_started` while held and none stalls.
- [ ] Lane 7. Grep `settings.py`, the schema and every template for `runaway`, `max_turns`, `max_tool_calls` and `run_seconds`. Save `cape-grep.log`. Pass when no default or template value is found.
- [ ] Lane 8. Kill the engine three times during one run. Save `cape-crashloop.log`. Pass when the run parks with one inbox item.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `cape-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `cape-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Watchdog tick time in ms with 50 open attempts.
- [ ] Probe. A unit benchmark over 50 fixture attempts, ten ticks.
- [ ] Baseline. The parent's watchdog tick on the same fixture.
- [ ] Rule. Fail when the median tick exceeds 200 ms, because the detector runs every tick.

**Review gate.** None. CAPE changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends CAPE on PRB-L.

## Remove the harness budgets and let sends wait for a slot (CAPH)

Rows AL-1, B-7, B-9, and 39 R.6 L5 (the harness half). ADs AD-40 (1) and (5), AD-30. Change H28. Check the harness half of E43. Gate none. Scenarios 46 section 5.0 "Capacity queues, interactive reserve" and "Provider limit mid fan-out". Done when `[budgets]` unset reaches the SDK as no budget and no turn cap, no `needs_you` appears for usage, a Background send past capacity waits, a parent that delegates under `max_live_chats = 1` finishes, and `hard_stop` is untouched.

**Depends on.** HYG0 for CI. It may build beside CAPE, because their files are disjoint.

**Files.**

- [ ] Edit `H/launch.py` (`Budgets` and `parse_budgets` at lines 221 to 261, the options at 518 and 519), `H/harness.py` (`BackgroundCap`, `needs_you` and `ChatTableFull` at lines 362 to 433, the usage page at 624) and `H/usage.py` (`BackgroundCap` and `cap_note` at lines 250 to 280; `hard_stop` and `overage_rule` kept).
- [ ] Edit `qmx-agents/packages/qma-harness/src/qma/console.py` where it shows budget rows.
- [ ] Edit `HT/test_launch.py`, `test_table.py`, `test_usage.py`, `test_delegate.py`, `test_console.py` and `test_change.py`.
- [ ] Edit `SL/qma/s10_usage.py` and `SL/qma/s31_chat_cap.py`. Create `SL/qma/e43_harness.py`.

**Build.**

- [ ] `[budgets] max_budget_usd`, `background_cap` and the Background and Child `max_turns` accept unset and default to unset. An unset value reaches the SDK as no `max_budget_usd` and no `max_turns`.
- [ ] Delete `BackgroundCap`, `cap_note` and the usage page's cap rows. Write no `needs_you` block for usage on an unattended chat.
- [ ] A Background or Child send with no free chat slot waits for one instead of failing with `ChatTableFull`.
- [ ] A child started by a parent that is blocked on it borrows the parent's slot (42 N5).
- [ ] Derive `max_live_chats` from the machine's RAM, with `session_mb` 1,536 and `overhead_mb` 4,096 on the PC (Claude's default, AD-30). This replaces the fixed 4 and 6 of 39 R.6 L5. Keep `limits.interactive_reserve`.

**You see.**

- [ ] With `[budgets]` empty, the usage page shows readings only, and a Background chat's launch options carry no budget and no turn cap.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_launch.py` asserts unset budgets reach the options as `None`. `test_table.py` asserts a send past capacity waits and then runs when a slot frees, and that a borrowed slot finishes under `max_live_chats = 1`. `test_usage.py` asserts `hard_stop` still stops. Run `-n 2` in `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` suite with `-n 2` at the parent and at head. Save `caph-regression.log`. Pass when head fails nothing the parent passes except tests that asserted a deleted cap, each named.
- [ ] Lane 2. E43 harness half. Run `e43_harness.py` on haiku under the lane lock. Save `caph-e43.log`. Pass when the launch options hold no budget or turn cap and no `needs_you` block appears.
- [ ] Lane 3. Start three Background chats with `max_live_chats = 2` on a throwaway home with the fake model. Save `caph-wait.log`. Pass when the third waits and then runs, and none fails.
- [ ] Lane 4. A parent delegates under `max_live_chats = 1` with the fake model. Save `caph-borrow.log`. Pass when parent and child both finish.
- [ ] Lane 5. Rerun `s10_usage.py`. Save `caph-s10.log`. Pass when readings show and no cap row exists.
- [ ] Lane 6. Feed a paid-overage reading to `hard_stop`. Save `caph-hardstop.log`. Pass when it still stops.
- [ ] Lane 7. Print the derived `max_live_chats` on the PC. Save `caph-ram.log`. Pass when it matches the RAM formula.
- [ ] Lane 8. Open the console's usage view. Save `caph-console.png`. Pass when no budget row shows.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `caph-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `caph-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Time in ms from a freed slot to the waiting send starting.
- [ ] Probe. Lane 3, three times.
- [ ] Baseline. None, the wait is new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The visible change is the usage page losing its cap rows, and the UI session owns that screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends CAPH on CAPE.

## Give each kind of work its own capacity, with one chat-slot counter (CAPX)

ADs AD-58, AD-9, AD-10 (priority). Check E58. Gate none. Scenarios K-16 and 46 section 5.0 "Capacity queues, interactive reserve". Done when rule, join and loop nodes never wait for a slot, scripts take CPU slots, chats take slots only from the harness slot table, and waiting work is ordered by priority then age.

**Depends on.** CAPE and CAPH.

**Files.**

- [ ] Edit `E/workers/local.py` (the single semaphore at line 47), `E/admission.py` (`engine_cap`), `E/settings.py` (`cpu_slots`, `container_slots`, `gpu_slots`) and `E/runner.py` (the admission call).
- [ ] Edit `H/harness.py` (`_take_slot`, exposed as the one chat-slot reading the engine reads).
- [ ] Edit `ET/test_admission.py`, `ET/test_drain.py` and `HT/test_table.py`. Create `SL/engine/e58_capacity.py`.

**Build.**

- [ ] Pure kinds (`trigger`, `rule`, `loop`, `join`, `wait`, `subworkflow`, a deterministic `grader`, `library` reads) take no slot.
- [ ] `script`, `monitor` and a local `rlm` kernel take a CPU slot. `cpu_slots` defaults to the logical core count minus one (Claude's default).
- [ ] A chat-backed node takes a slot from the harness slot table, the only chat-slot counter. Delete `admission.engine_cap`.
- [ ] A container attempt also takes a container slot (`container_slots` 3 on the PC, Claude's default). A GPU attempt takes a `gpu_slots` slot where a placement has GPUs (unset on the PC).
- [ ] Order waiting work by trigger `priority`, then age. A low-priority fan-out yields between chunks.

**You see.**

- [ ] A run with 40 rule nodes and 12 agent chunks shows no rule waiting and his Interactive chat starting while the chunks run.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_admission.py` asserts each kind takes its class and nothing else, that priority beats age, and that no `engine_cap` exists. Run `-n 2` in `qmx-engine` and `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` and `qma-harness` suites with `-n 2` at the parent and at head. Save `capx-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E58. Run `e58_capacity.py` with 40 rule nodes and 12 agent chunks on the fake provider. Save `capx-e58.log`. Pass when no rule waits, scripts run at `cpu_slots` at once, and chats never exceed the slot table minus the reserve.
- [ ] Lane 3. Start an Interactive chat on haiku while lane 2's chunks hold every other slot, under the lane lock. Save `capx-reserve.log`. Pass when the chat starts at once.
- [ ] Lane 4. Queue a priority 1 and a priority 5 run behind full capacity. Save `capx-priority.log`. Pass when the priority 5 run starts first.
- [ ] Lane 5. Run a backtest-shaped script beside 10 rule nodes. Save `capx-script.log`. Pass when the rules finish before the script.
- [ ] Lane 6. Grep for `engine_cap` and the old semaphore. Save `capx-grep.log`. Pass when neither is found.
- [ ] Lane 7. Print the derived slot table on the PC. Save `capx-table.log`. Pass when it matches the machine.
- [ ] Lane 8. A low-priority fan-out of 6 chunks beside a high-priority run. Save `capx-yield.log`. Pass when the fan-out yields between chunks.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `capx-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `capx-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of lane 2's run.
- [ ] Probe. Lane 2 at head, three times.
- [ ] Baseline. The same run at the parent.
- [ ] Rule. Fail when head is slower than the parent, because removing one shared semaphore is this PR's point.

**Review gate.** None. CAPX changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends CAPX on CAPH.

## Redact every stored and served secret through one seam, and keep tool keys by reference (SEC1A)

Rows B-17, B-39, L-50, L-51, L-52, L-58, the rows of 40's SEC-1 that survive the retirement pass (39 RP.4). ADs AD-37, AD-23, AD-24 (run context). Check E37. Gate none. Scenarios K-27 and 46 section 5.0 "Credentials on a new machine; provider onboarding". Done when a provider error echoing a key, a script printing a resolved tool key and the inbox item built from that failure all read `[redacted…]` in the ledger, the inbox, `explain`, REST and the run summary, a node names only a declared `qmx/tool/<name>` key, and a run reads only published versions as published.

**Depends on.** CAPE (`E/definition/lint.py`, templates).

**Files.**

- [ ] Create `E/ledger/redact.py`. Edit `E/ledger/store.py`, `E/ledger/inbox_table.py`, `E/ledger/memo.py`, `E/trace_export.py`, `E/service/explain.py`, `E/service/rest.py` and `E/service/runs.py` (lines 208 to 212).
- [ ] Edit `E/definition/lint.py` (the `qmx/tool/<name>` rule), `E/ports/library_fake.py` (redaction on writes) and `E/nodes/script.py` (stderr capture).
- [ ] Edit `ET/test_ledger.py`, `ET/test_inbox.py`, `ET/test_explain.py`, `ET/test_lint.py` and `ET/test_runs.py`. Create `SL/engine/e37_redaction.py`.

**Build.**

- [ ] `redact` is the one redaction function. The ledger writer applies it to every string in every event's `data` before commit, the inbox table passes through it, the `LibraryPort` adapter applies it to run summaries, trace exports and artifact metadata, and the REST serializer applies it to every answer. Each span counts its redactions.
- [ ] Lint refuses a credential reference that is not a declared `qmx/tool/<name>` key. A token-shaped literal stays refused (AD-23, built).
- [ ] `service/runs.py` reads a ref as published only when it is on `main` (L-51).

**You see.**

- [ ] A failing fixture whose provider error echoes `key_sk-or-v1-…` shows `[redacted…]` in `explain` and in the inbox item.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert `redact` on the key shapes of every bundled provider, that a ledger event with a key commits redacted, that `explain` and REST answers carry no key, and that a draft ref is not read as published. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head. Save `sec1a-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E37. Run `e37_redaction.py` on the fake provider. Save `sec1a-e37.log`. Pass when the ledger, the inbox title and cause, `explain`, REST and the run summary all show `[redacted…]`.
- [ ] Lane 3. Validate a definition naming a non-tool credential ref. Save `sec1a-refs.log`. Pass when lint refuses it with the file and line.
- [ ] Lane 4. Start a run on a draft ref through the service. Save `sec1a-published.log`. Pass when it is refused as not published.
- [ ] Lane 5. Grep the lane's ledger file and exports for the planted key. Save `sec1a-grep.log`. Pass when it is not found.
- [ ] Lane 6. Print a key from a script's stdout and stderr. Save `sec1a-script.log`. Pass when both captures are redacted.
- [ ] Lane 7. Read the run's spans. Save `sec1a-spans.log`. Pass when the redaction count is above zero.
- [ ] Lane 8. Run one template on haiku under the lane lock. Save `sec1a-haiku.log`. Pass when it ends `passed`.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `sec1a-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `sec1a-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Ledger append time in microseconds with redaction on.
- [ ] Probe. 10,000 appends of a 2 KB event.
- [ ] Baseline. The parent, same probe.
- [ ] Rule. Fail when the median append is more than twice the parent's, because the ledger writer is one thread.

**Review gate.** None. SEC1A changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends SEC1A on CAPX.

## Give each attempt its own overlay and tie scripts to the engine's life (SEC2A)

Rows B-26, B-29, B-31, B-78, B-80 (the env half), L-39, L-40, L-43. ADs AD-51, AD-24 (zones, Job object, orphan sweep, run context, kept by 39 RP.2), AD-8. Checks E14 and E50. Gate none. Scenarios 46 section 5.0 "300-video playlist; Firecrawl pipeline" (chunks writing files) and K-12. Done when two concurrent attempts of one run write different files and a retry keeps the sibling's committed files, only declared outputs commit, a crash between the renames and `zone_committed` rolls forward, and a script killed with the engine dies with it.

**Depends on.** SEC1A (`E/nodes/script.py`, `E/ledger/store.py`).

**Files.**

- [ ] Edit `E/workers/effects.py` (the `.snap` snapshot goes), `E/workers/local.py` (the script env and the Job object), `E/nodes/script.py`, `E/definition/validate.py` (concurrent writers of one declared path) and `E/definition/model.py` (`outputs.files`, merge kinds).
- [ ] Create `E/workers/zones.py` for overlays, staged commits and roll-forward.
- [ ] Edit `T/db-desk-brief/scripts/gather.py` (line 135) and `T/rv-weekly-review/scripts/week.py` (lines 30 and 31), which derive the QMX home from the cwd.
- [ ] Edit `ET/test_effects.py` and `ET/test_validate.py`. Create `ET/test_zones.py`, `SL/engine/e50_overlays.py`, and edit `SL/engine/e14_script_env.py`.

**Build.**

- [ ] Every attempt that may write files gets `<zones_root>/<run_id>/attempts/<node>.<iteration>.<partition>.<attempt>/` as its cwd and only writable place. `work/` is read-only to it (`QMX_WORK_SHARED`), and `code/` is a read-only, hash-checked copy.
- [ ] At `ok`, stage the declared `outputs.files` under `work/.staging/<attempt>/`, rename each into place under the ledger writer, apply declared tombstones, and write `zone_committed{paths, sha256}`. Undeclared files die with the overlay. Resume rolls a staged commit forward.
- [ ] Validation refuses two possibly-concurrent writers of one declared path unless it is partition-templated or a merge (`append` or `keyed`). A `zone_conflict` at commit is a definition bug, non-retryable, sent to the doctor.
- [ ] `failed`, `cancelled` and `unknown` delete the overlay. A parked run's zone is kept until its inbox item closes (AD-49).
- [ ] Scripts run in the engine's Job object, so they die with it, and the start-up sweep folds orphans. The script env holds the run context (`QMX_RUN_ID`, `QMX_MODE`, `QMX_FAKE`, `QMX_NOW`, `QMX_WORK`, `QMX_WORK_SHARED`, `QMX_CODE`) and no provider key, `CLAUDE_CONFIG_DIR`, plan path or home path.

**You see.**

- [ ] After a three-chunk run, `work/` holds only the declared outputs, and no attempt folder is left.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_zones.py` asserts a commit of declared outputs only, a roll-forward after a crash between renames, a refused second writer at validation, and an overlay deleted on `failed`. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head. Save `sec2a-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E50. Run `e50_overlays.py`. Save `sec2a-e50.log`. Pass when the sibling's files survive a retry, scratch files never collide, the second writer is refused at validation, and a staged commit rolls forward.
- [ ] Lane 3. E14. Run `e14_script_env.py`. Save `sec2a-e14.log`. Pass when the env shows the run context and none of the forbidden names.
- [ ] Lane 4. Kill the engine with `taskkill /F` during a 60 s script. Save `sec2a-lifetime.log`. Pass when the script process is gone within 2 s.
- [ ] Lane 5. Run `db-desk-brief` and `rv-weekly-review` in test mode on the fake provider. Save `sec2a-templates.log`. Pass when both end `passed` from the new cwd.
- [ ] Lane 6. Start the engine after a planted orphan. Save `sec2a-sweep.log`. Pass when the sweep folds it.
- [ ] Lane 7. Park a run and list zones. Save `sec2a-parked.log`. Pass when the parked run's zone is kept.
- [ ] Lane 8. Grep for `.snap`. Save `sec2a-grep.log`. Pass when no snapshot code is left.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `sec2a-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `sec2a-processes.log`. Pass when no script, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Commit time in ms for 100 declared files.
- [ ] Probe. A fixture node with 100 outputs, five runs.
- [ ] Baseline. None, the commit is new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. SEC2A changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends SEC2A on SEC1A.

## Fix run state, waits and resume (BUG1)

Rows B-25, B-37, B-42, B-54, B-57, B-60, B-63, B-66, B-72, L-28, L-31, L-32, L-33, L-37, L-38, L-47, L-57, L-65, L-69, L-80 of 40's BUG-1. B-69 and the H2 engine side move to TURN-E, B-73 to BUG3, and L-64 and L-70 to HOST, because those files are rebuilt there. ADs AD-7, AD-8, AD-9, AD-10, AD-16. Check E40 plus the resume lanes. Gate none. Scenarios 46 section 5.0 "Catch-up after downtime" and "Provider limit mid fan-out", and K-16. Done when a held run writes a wake row and resumes on its own, a model node declaring `irreversible` follows AD-8's rule, and every row above has its named test.

**Depends on.** SEC2A (`E/workers/effects.py`) and CAPX (`E/workers/local.py`).

**Files.**

- [ ] Edit `E/runner.py`, `E/core/fold.py`, `E/core/ladder.py`, `E/watchdog.py`, `E/triggers/ticker.py`, `E/triggers/claims.py`, `E/ledger/store.py`, `E/ledger/inbox_table.py`, `E/service/runs.py`, `E/workers/effects.py` and `E/workers/local.py`, each only for the rows above.
- [ ] Edit the matching tests in `ET/`. Create `SL/engine/e40_wakes.py`.

**Build.**

- [ ] Fix each row as 40 section 2 states it, with one behavioural test per row named after the row id. B-57 follows AD-8 (40 section 5 item 5). L-47 and B-37 follow the ladder of AD-16 as CAPE left it.
- [ ] Wakes. A run held on `wait` or a retry backoff writes a wake row, reads `waiting`, and the ticker resumes it with no human action (AD-10).

**You see.**

- [ ] A run held on `wait seconds: 90` reads `waiting` in `runs list` and resumes on its own after 90 s.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] One test per row above with literal end states. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head. Save `bug1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E40. Run `e40_wakes.py`. Save `bug1-e40.log`. Pass when the held run and the backoff both resume on their own.
- [ ] Lane 3. Rerun `SL/engine/e02_replay.py` and `e04_unknown_outcome.py`. Save `bug1-replay.log`. Pass when both pass.
- [ ] Lane 4. Rerun `SL/engine/x12_scheduler.py` and `e06_catchup.py`. Save `bug1-scheduler.log`. Pass when both pass.
- [ ] Lane 5. Rerun `e05_pause.py`. Save `bug1-pause.log`. Pass when it passes.
- [ ] Lane 6. Rerun `e11_ladder.py`. Save `bug1-ladder.log`. Pass when it passes.
- [ ] Lane 7. Kill the engine mid-run twice and restart. Save `bug1-kill.log`. Pass when the run resumes once each time with no duplicate fire.
- [ ] Lane 8. Run one agent template on haiku under the lane lock. Save `bug1-haiku.log`. Pass when it ends `passed`.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `bug1-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `bug1-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Ticker tick time in ms with 200 trigger rows.
- [ ] Probe. A unit benchmark, ten ticks.
- [ ] Baseline. The parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. BUG1 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends BUG1 on SEC2A.

## Write the spec-gap code and close the validation holes (BUG2)

Rows B-18, B-19, B-20 (refusal), B-22, B-23, B-24, B-27, B-43, B-46 (refusal), B-61, B-71, B-76, B-77, B-85, B-87, B-90, B-92, L-20, L-22, L-26, L-29, L-34, L-54, L-55, L-56, L-75, L-89 of 40's BUG-2. B-68 moves to HOST, because the door is rebuilt there. ADs AD-7, AD-11, AD-4, AD-5, AD-20. Check the validation and event-key lanes. Gate none. Scenarios K-12 and K-34. Done when `required` edges, enable derived from triggers, event keys, the `WorkerPort.run(job, emit)` shape and the refusals of nested fan-out and `llm`-mode graders exist with one test per row.

**Depends on.** BUG1 (`E/runner.py`, `E/service/runs.py`).

**Files.**

- [ ] Edit `E/definition/validate.py`, `E/definition/registry.py`, `E/definition/folder.py`, `E/core/ready.py`, `E/core/joins.py`, `E/runner.py`, `E/nodes/subworkflow.py`, `E/service/versions.py`, `E/service/drafts.py`, `E/service/tests.py`, `E/service/runs.py`, `E/service/explain.py`, `E/ledger/store.py` and `E/workers/local.py`, each only for the rows above.
- [ ] Edit `T/catalog.py` (B-76, so `SHARED_COPIES` can go in TPL1) and the matching tests in `ET/`.

**Build.**

- [ ] Fix each row as 40 section 2 states it, with one behavioural test per row named after the row id. B-19 settles memo truth per AD-7. B-20 and B-46 add only the refusals, since nested fan-out and the grader's `llm` mode are backlog (Appendix G).
- [ ] `WorkerPort.run(job, emit) -> NodeResult` takes the event sink, and no executor crosses the port (AD-20, L-42).

**You see.**

- [ ] `python -m qmx_engine check` refuses a definition with a nested fan-out and names the node.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] One test per row above with literal results. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head. Save `bug2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Rerun `SL/engine/x03_validate.py` with the new refusal fixtures. Save `bug2-validate.log`. Pass when each fixture is refused with its node named.
- [ ] Lane 3. Rerun `x04_ledger.py` and check event keys on a two-node run. Save `bug2-events.log`. Pass when every event carries its key.
- [ ] Lane 4. Rerun `e07_lifecycle.py`. Save `bug2-lifecycle.log`. Pass when enable follows from triggers and publish refuses non-user callers.
- [ ] Lane 5. Rerun `x06_joins_loops.py`. Save `bug2-joins.log`. Pass when it passes.
- [ ] Lane 6. Rerun `x09_explain.py`. Save `bug2-explain.log`. Pass when it passes.
- [ ] Lane 7. Rerun `x07_nodes.py`. Save `bug2-nodes.log`. Pass when it passes.
- [ ] Lane 8. Run the template tests in `ET/test_templates.py`. Save `bug2-templates.log`. Pass when they pass.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `bug2-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `bug2-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Validation time in ms for the largest shipped template.
- [ ] Probe. `check` on that template, ten times.
- [ ] Baseline. The parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. BUG2 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends BUG2 on BUG1.

## Fold gate answers, derive run state from the ledger, let a partition walk its own ladder, and keep one event writer (BUG3)

Rows B-28, B-32 (GATE), B-40, B-73 (LDR), B-35 (CHUNK), and the 43 section 5 row that deletes `core/simulate.py`. L-68 moves to HOST. ADs AD-7, AD-8, AD-16, AD-17, AD-1. Checks the gate-fold and runs-list lanes, plus the first full `just ci`. Gate none. Scenarios K-22 and 46 section 5.0 "Provider limit mid fan-out". Done when an inbox answer folds as `gate_resolved` and moves the run, `runs list` reads a pure fold over events, a failed partition walks retry, account, model and doctor while its siblings' memos stand, and `simulate.py` is gone with its tests moved onto `Engine`.

**Depends on.** BUG2 (`E/core/joins.py`, `E/service/runs.py`).

**Files.**

- [ ] Edit `E/core/fold.py`, `E/core/joins.py`, `E/core/ladder.py`, `E/ports/inbox.py`, `E/ledger/inbox_table.py` and `E/service/runs.py`.
- [ ] Delete `E/core/simulate.py`. Move `ET/test_fold.py`, `test_joins.py`, `test_loops.py`, `test_replay.py` and `test_rule.py` onto `Engine` with injected executors (the `executors=` seam), and repoint `SL/engine/e01_determinism.py`, `e02_replay.py`, `e03_chunks.py` and `x06_joins_loops.py`.
- [ ] Create `SL/engine/bug3_gates.py`.

**Build.**

- [ ] `InboxPort.resolve` appends `gate_resolved{answer, principal}` through the ledger writer and wakes the run. The core folds `retry`, `skip_node`, `stop`, `resume` (lifting a pause at a limit he wrote) and `stronger_model`. An `unknown` outcome on an `irreversible_external` step waits on its gate.
- [ ] `status_of(run_id)` is a pure fold over the run's events plus the worker's live-attempt set. At engine start every open attempt is `interrupted` until folded. `workflow_runs_list` reads the fold, never a cache.
- [ ] A failed partition walks the ladder on its own. The join's watermark waits while any partition has ladder steps left.
- [ ] Delete `core/simulate.py`, so one event writer remains.

**You see.**

- [ ] `runs list` shows an in-flight run as `running` and a held one as `waiting`, and answering a gate item moves the run on.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert each gate answer's fold, the run status from a fixture event log, and a partition walking its ladder while siblings stand. The moved tests pass on `Engine`. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run `just ci` under the CI lock at head, and the `qmx-engine` suite at the parent. Save `bug3-ci.log`. Pass when `just ci` passes and head fails nothing the parent passes.
- [ ] Lane 2. Run `bug3_gates.py`. Save `bug3-gates.log`. Pass when each of the five answers folds and moves the run as AD-17 says.
- [ ] Lane 3. List runs during a three-node run and while one waits. Save `bug3-runs.log`. Pass when the states match the ledger.
- [ ] Lane 4. Fail one of four partitions twice on the fake provider. Save `bug3-partition.log`. Pass when it walks its own ladder and the other memos stand.
- [ ] Lane 5. Rerun `e01_determinism.py`, `e02_replay.py` and `e03_chunks.py` on `Engine`. Save `bug3-moved.log`. Pass when all pass.
- [ ] Lane 6. Grep for `simulate`. Save `bug3-grep.log`. Pass when no import is left.
- [ ] Lane 7. Restart the engine with an open attempt. Save `bug3-restart.log`. Pass when it reads `interrupted` and then folds.
- [ ] Lane 8. Answer a gate on an `irreversible_external` unknown. Save `bug3-irreversible.log`. Pass when the step runs only on `retry`.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `bug3-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `bug3-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. `runs list` time in ms with 1,000 runs in the ledger.
- [ ] Probe. A seeded ledger, ten calls.
- [ ] Baseline. The parent's cached list.
- [ ] Rule. Fail when the median exceeds 500 ms, because the list now folds every time.

**Review gate.** None. BUG3 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends BUG3 on BUG2.

## Run the copilot and the workflows in one host program (HOST)

Rows B-11, B-64, B-68, L-64, L-68, L-70. ADs AD-52, AD-3, AD-23, Lib AD-5. Change H24 (the principal at the one door). Check E54. Gate none. Scenarios K-02, K-28 and 46 section 5.0 "Catch-up after downtime". Done when `python -m qmx_host serve` serves chat, engine and control routes on one home, a copilot turn and a workflow agent node run at once, a second host on the same home refuses with one line, and `qma.serve`, `python -m qmx_control serve` and `qmx_engine.host` forward to it.

**Depends on.** CAPH (`H/harness.py`). It may build beside the engine track (SEC1A to BUG3), whose files it does not share. The root appends it on BUG3.

**Files.**

- [ ] Create the package `qmx-agents/packages/qmx-host/` with `pyproject.toml`, `HO/__init__.py`, `HO/__main__.py`, `HO/host.py` (the composition) and `HO/door.py` (the principal), plus `tests/test_host.py`.
- [ ] Edit `qmx-agents/packages/qma-harness/src/qma/serve.py` and `QX/__main__.py` into one-line forwarders. Edit `H/routes.py` so `_serve` becomes a function that mounts the chat routes and starts nothing.
- [ ] Edit `E/host.py` into a forwarder and move the single-instance `engine.lock` into `HO/host.py` (L-64, L-70). Rebuild `E/control_door.py` to about 350 lines. Delete the Library-watcher fallback (`CURSOR`, `library-watch`, `nonce`), take the principal from the door, and fix B-68 and L-68 there.
- [ ] Edit `qmx-agents/packages/qmx-broker/src/qmx_broker/service.py` (lines 117 to 121) to read settings through `ControlService`.
- [ ] Edit `qmx-agents/pyproject.toml` (members), `qmx-agents/packages/qma-core/tests/test_extensibility.py` (the member set) and `tools/ci.py`.
- [ ] Edit `SL/engine/lane_host.py`, `x13_doors.py` and `x14_hello.py` to start `qmx_host`. Create `SL/host/e54_one_host.py`.

**Build.**

- [ ] `python -m qmx_host serve --home <home> --port <port> [--role pc | node] [--ui-origin <origin>]` runs SOLUTION-DESIGN section 27.1 steps 1 to 10, with the parts that exist today. It scrubs the environment first, takes the lock, builds `ControlService`, starts the relay on its own thread, opens the `Harness`, builds the engine and the apps supervisor, and mounts chat, engine and control routes behind one bearer.
- [ ] The door sets the principal of every call. The UI bearer is `user`, an in-process `qmx` tool call is `agent:<session_id>`, and a run pass is `workflow:<run_id>`. Publish, enable and live start refuse anything but `user`.
- [ ] No other package starts a server. The three old entry points forward for one release and go in DEL2.
- [ ] On stop, the host drains the engine, closes the harness and stops the relay.

**You see.**

- [ ] One `qmx_host` process answers `GET /api/health`, lists chats and lists workflow runs on the same port.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_host.py` asserts a second host on the same home refuses, the door's principal for each credential kind, and that publish over an agent principal returns a card. Run `-n 2` in `qmx-host`, `qmx-engine` and `qmx-control`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness`, `qmx-engine` and `qmx-control` suites with `-n 2` at the parent and at head. Save `host-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E54. Run `e54_one_host.py` on the ship home under the lane lock, with a haiku copilot turn and a workflow agent node at once. Kill the host mid-turn and restart. Save `host-e54.log`. Pass when both ran at once, the chat shows its turn as unknown, the run resumes from its ledger, and a second host refuses with one line.
- [ ] Lane 3. Rerun `x13_doors.py` against `qmx_host`. Save `host-x13.log`. Pass when every door answers with the right principal.
- [ ] Lane 4. Start each old entry point. Save `host-forwarders.log`. Pass when each starts `qmx_host` and serves the same routes.
- [ ] Lane 5. Rerun `x14_hello.py`. Save `host-x14.log`. Pass when it passes.
- [ ] Lane 6. Call publish with an agent principal and with the UI bearer. Save `host-principal.log`. Pass when the first returns a card and the second publishes.
- [ ] Lane 7. Read broker settings through `ControlService`. Save `host-broker.log`. Pass when the broker service reads no file directly.
- [ ] Lane 8. Grep for `CURSOR`, `library-watch` and `nonce` in `control_door.py`. Save `host-grep.log`. Pass when none is found.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `host-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `host-processes.log`. Pass when no `claude`, `qma-cli-launcher` or `qmx_host` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time from `qmx_host serve` to the first 200 on `/api/health`.
- [ ] Probe. Five starts.
- [ ] Baseline. Five starts of `qma.serve` at the parent.
- [ ] Rule. No fail rule. Recorded for the desktop host later.

**Review gate.** None. HOST changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends HOST on BUG3.

## Give programs a turn call and keep every chat option across restarts (TURN-H)

Rows B-6, B-8, B-10, B-50, B-65, L-7, L-8, L-9, L-16, L-17. ADs AD-53, AD-16, AD-35, AD-62 (preset options). Changes H1, H2, H8, H18, H19, H20, H21, H22, H39 (the registry), H40, H41, H45, H51, H53, H54 and section I. Checks the H1 and H19 lanes and P-SET's cache case on a real launch. Gate none, after PRB-H's P-SET row. Scenarios K-02, K-28 and 46 section 5.0 "300-video playlist" (the cached brief). Done when `run_turn` returns a handle whose `result()` equals the turn's blocks, every `NewChat` option survives a host restart, a finished Background chat leaves no CLI process, and a draft save asks nothing.

**Depends on.** HOST (`HO/host.py`) and PRB-H (P-SET). If P-SET failed, settings stay on the command line and the append text goes through `--append-system-prompt-file` (its named fallback).

**Files.**

- [ ] Create `H/turns.py` (`TurnHandle`, turn events) and `qmx-agents/packages/qma-harness/src/qma/harness/py.typed`.
- [ ] Edit `H/harness.py` (`start_chat`, `run_turn`, `interrupt`, `close_chat`, `set_packs` storing the set, `register_policy`, `register_sink`), `H/chat.py` (turn end through `Chat.next_end`, policies answered in-process from `can_use_tool`), `H/launch.py` (`NewChat` fields, the per-chat settings file, the preset with `exclude_dynamic_sections` and `snapshot: false`, `autoMemoryEnabled: false` for Background and Child, `claude_hooks`, allow rules from the Effect table), `H/home.py` (the chat record) and `H/__init__.py` (exports).
- [ ] Edit `H/usage.py` (the `meter()` cooldown and cleanup, L-16 and L-17).
- [ ] Edit `HT/test_chat.py`, `test_chat_options.py`, `test_launch.py`, `test_home.py` and `test_table.py`. Create `HT/test_turns.py`. Create `SL/qma/turn_lanes.py` and edit `SL/qma/s13_compact.py` and `s14_resume.py`.

**Build.**

- [ ] `run_turn(sid, prompt) -> TurnHandle`. `events()` yields the projected blocks plus `queued`, `started`, tool, compaction and `waiting_on_model` facts. `result()` resolves once with `ok`, `failed`, `interrupted` or `unknown`, the final text, usage with cache and thinking tokens, the tool calls, the compactions, the context read and the terminal reason.
- [ ] `NewChat` carries `home` (with kind `agent`, H51), `packs`, `tools` (`[]` for none), `agents`, `mcp_servers`, `append_system_prompt`, `compact_at`, `hook_sink`, `permissions`, `policy_args` and `claude_hooks`. Every field is persisted on the chat record. Sinks and policies are resolved by name after a restart, never stored as callables.
- [ ] The order on a tool call is the money gate as built (GUARD replaces it), then the CLI rules, then `can_use_tool`, which an Interactive chat answers through him and a Background or Child chat through its named policy in-process.
- [ ] Claude settings go to a per-chat file passed by path, and the command-line check stays the only bound (H21). Every chat's preset carries `exclude_dynamic_sections: true` and `snapshot: false` (H53). Background and Child chats run with auto memory off (H54).
- [ ] `DOMAIN_WRITE` rows never ask while `[agents] domain_write` is `allow` (H20). `close_chat` ends the CLI process and deletes nothing (H18).
- [ ] Copilot helper chats feed `run_turn` events into the stuck rules in `H/stuck.py` (H45).
- [ ] Fix section I. `meter()` gets a cooldown and cleans up before awaiting `chat.close()`, `Harness._options` is pruned when a chat ends, and `_observer` also catches `CancelledError`.

**You see.**

- [ ] A Background chat started with `tools: []`, a hook sink and `compact_at: 0.4` keeps all three after the host restarts, and its turn ends with no polling.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_turns.py` asserts a turn's `result()` equals its blocks, `queued` while waiting for a slot, and `unknown` after a restart mid-turn. `test_chat_options.py` asserts every `NewChat` field round-trips through the chat record. Run `-n 2` in `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` suite with `-n 2` at the parent and at head. Save `turn-h-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. H1. Run a 40-tool-call haiku turn through `turn_lanes.py` under the lane lock. Save `turn-h-h1.log`. Pass when it ends through `result()` and no poll loop ran.
- [ ] Lane 3. H19. Kill the host mid-turn on a Background chat with `compact_at: 0.4` and a hook sink, then resume. Save `turn-h-h19.log`. Pass when the resumed chat compacts at 0.40 and its PostToolUse events still arrive.
- [ ] Lane 4. P-SET's cache case on the real launch. Two Background chats in two folders. Save `turn-h-cache.log`. Pass when the second reads the system prefix from cache.
- [ ] Lane 5. Resume a `tools: []` chat and ask it to use a tool. Save `turn-h-h2.log`. Pass when no tool runs.
- [ ] Lane 6. Save a draft through the copilot on haiku. Save `turn-h-h20.log`. Pass when no ask appears.
- [ ] Lane 7. Close a finished Background chat. Save `turn-h-h18.log`. Pass when no CLI process of it is left.
- [ ] Lane 8. A workflow's PostToolUse command hook in `claude_hooks`. Save `turn-h-h41.log`. Pass when it runs in that workflow's chats and not in a copilot chat.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `turn-h-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `turn-h-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time in ms from the CLI's turn end to `result()` resolving.
- [ ] Probe. Lane 2's turn, three times.
- [ ] Baseline. The parent engine adapter's 50 ms poll on the same turn.
- [ ] Rule. Fail when the median exceeds 50 ms, because ending the polling is the point.

**Review gate.** None. TURN-H changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends TURN-H on HOST.

## Drive engine chats through the turn call and delete the polling (TURN-E)

Rows B-51, B-69, B-70, and the engine side of H2 from 40's BUG-1. ADs AD-53, AD-60 (the read-only policy first), AD-34, AD-13. Checks `x10_llm.py`, `x11_agent_chunks.py` and `e04b_agent_unknown.py` on `run_turn`. Gate none. Scenarios 46 section 5.0 "300-video playlist; Firecrawl pipeline" and K-34. Done when the engine's `HarnessPort` waits on `result()`, about 200 lines of polling are gone, a node gets exactly the tools it declares, a plan-row `llm` node gets none, and a resumed chunk that never got its task is re-sent in full.

**Depends on.** TURN-H and BUG3 (`E/nodes/agent.py`, `E/runner.py`).

**Files.**

- [ ] Rebuild `E/ports/harness_adapter.py` to about 150 lines on `run_turn`. Rebuild `E/nodes/agent.py` to about 250 lines. Edit `E/nodes/llm.py`, `E/watchdog.py` and `E/runner.py` (the harness is injected by the host).
- [ ] Create `E/policy.py` with the `engine` policy in its read-only form (every write and undeclared tool denied with a reason) and `E/sink.py` with the `engine` hook sink. Edit `HO/host.py` to register both.
- [ ] Edit `ET/test_harness_port.py`, `test_agent.py` and `test_llm.py`. Edit `SL/engine/x10_llm.py`, `x11_agent_chunks.py` and `e04b_agent_unknown.py`.

**Build.**

- [ ] `wait_turn` becomes `await handle.result()`. Delete `_turn`, `_blocks`, `_last_event`, the 50 ms loop and the poll-and-reject of asks. Keep the `Turn` record shape, so the nodes change little.
- [ ] Tool spans come from the sink live and are reconciled with the session blocks at turn end.
- [ ] Delete the context-watch restart at `compact_at + 0.05` and the "every request to write is rejected" rule text. `compact_at` now survives restarts (H19).
- [ ] A node passes exactly its declared built-ins as `tools`, and a plan-row `llm` node passes `[]` (H2, B-51, B-70).
- [ ] Keep the B-69 re-seed. A resumed attempt whose chat never got its task is re-sent in full. Keep the JSON validation with one repair turn.
- [ ] The watchdog reads chat progress from turn events through the rules in `qma.harness`.

**You see.**

- [ ] `git diff --stat` shows `harness_adapter.py` near 150 lines, and a two-chunk agent run on haiku ends `passed`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_harness_port.py` asserts a turn result maps to the `Turn` record, and the read-only policy denies a write with its reason. `test_agent.py` asserts the declared tool list reaches `NewChat.tools` and the B-69 re-seed. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head. Save `turn-e-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Rerun `x10_llm.py` on haiku under the lane lock. Save `turn-e-x10.log`. Pass when the plan-row `llm` node calls no tool and validates its JSON.
- [ ] Lane 3. Rerun `x11_agent_chunks.py` on haiku under the lane lock. Save `turn-e-x11.log`. Pass when both chunks end `passed` with tool spans.
- [ ] Lane 4. Rerun `e04b_agent_unknown.py`, killing the host before the task reaches the chat. Save `turn-e-b69.log`. Pass when the retry re-sends the full task and ends `passed`.
- [ ] Lane 5. Ask an agent node to write a file. Save `turn-e-readonly.log`. Pass when the policy denies it with its reason and the attempt goes on.
- [ ] Lane 6. Grep `harness_adapter.py` for `sleep(` and `_blocks`. Save `turn-e-grep.log`. Pass when neither is found.
- [ ] Lane 7. Push one chunk past its compaction point. Save `turn-e-compact.log`. Pass when the CLI compacts in the same chat and no restart chat is created.
- [ ] Lane 8. Rerun `SL/engine/e21_real_tests.py`. Save `turn-e-e21.log`. Pass when it passes on haiku.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `turn-e-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `turn-e-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Engine CPU seconds during a 40-tool-call agent turn.
- [ ] Probe. One such turn on haiku.
- [ ] Baseline. The parent's polling adapter on the same turn.
- [ ] Rule. Fail when head uses more CPU than the parent.

**Review gate.** None. TURN-E changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends TURN-E on TURN-H.

## Replace the money gate with the guard (GUARD)

Rows AL-22. ADs AD-54, AD-43. Changes H31, H42, H57, and the external-server half of H58. Check E56, which replaces `s06_money.py`. Gate none. Scenarios K-21 and 46 section 5.0 "Demo-broker setup by agents". Done when one PreToolUse guard runs first on every call, refuses sign-ins, keys, store writes, destructive commands outside the chat's folder and his never-list, lets a broker's public docs page through, asks in an Interactive chat before a recursive delete outside its folder, and the harness no longer imports `qma.core`.

**Depends on.** TURN-H (`H/launch.py`, `H/harness.py`, `H/home.py`). It may build beside TURN-E.

**Files.**

- [ ] Create `H/guard.py` from `H/money.py`'s kept functions plus the floor rows. Delete `H/money.py`.
- [ ] Edit `H/tools.py` (the `qma.core` import at line 29 and the surface vocabulary), `H/launch.py` (the hook and the deny rules shrunk to login and secret paths), `H/harness.py` (the doctor drops `probe_exposure`) and `H/routes.py` (`/api/doctor/probe` and the posture on the usage page go).
- [ ] Create `E/definition/money_words.py` with the vendored word list and point `E/definition/lint.py` at it.
- [ ] Edit `QX/service.py` for his always-allow and never-allow lists as Settings data.
- [ ] Rename `HT/test_money.py` to `HT/test_guard.py`, delete `HT/test_posture.py`, and edit `HT/test_tools.py` and `test_launch.py`. Replace `SL/qma/s06_money.py` with `SL/qma/e56_guard.py`, and delete `SL/qma/s26_posture.py` and `s27_broker_scope.py`.

**Build.**

- [ ] The guard denies plan-login and secret files, keyring and credential-store readers and the exact `qmx/*` names, writes into the QMX home outside `workspaces/` and `agent-memory/`, any write into a store or the install tree, recursive deletes outside the run's zones or the chat's working folder or worktree, disk, format and registry tools, NT device and UNC paths to unknown hosts, a secret in an outbound command body, invisible or bidirectional Unicode, `delegate` from a native sub-agent, an external MCP tool in an unattended chat unless listed, and then his never-list. His always-list never lifts a floor row.
- [ ] In an Interactive chat a recursive delete outside its folder asks him instead of refusing (H57).
- [ ] The vendored list also runs over a vetted external server's tool list and refuses an order-shaped tool (H58, external half).
- [ ] Retire `name_money_act`, the broker-host refusals, `MoneyPosture`, `money_posture`, `keyring_inventory`, scope proofs and the exposure probe. Keep the `Effect` enum without a money member, `AGENT_OPERATIONS` as an explicit list with a unit test that no row names an order act, and `propose_order` asking.

**You see.**

- [ ] A copilot WebFetch of a broker's public documentation page succeeds, and a copilot `cat` of the plan login file is refused with the guard's reason.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_guard.py` asserts each floor row on its Windows path forms, that his always-list cannot lift a floor row, the Interactive delete ask, and that no catalog row names an order act. Run `-n 2` in `qma-harness` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` and `qmx-engine` suites with `-n 2` at the parent and at head. Save `guard-regression.log`. Pass when head fails nothing the parent passes except retired money tests, each named.
- [ ] Lane 2. E56. Run `e56_guard.py` on haiku under the lane lock. Save `guard-e56.log`. Pass when every refusal and every allow in E56 holds and `propose_order` still asks.
- [ ] Lane 3. In an Interactive chat, ask for `rm -rf dist` inside its folder and outside it. Save `guard-delete.log`. Pass when the first runs and the second asks.
- [ ] Lane 4. Run `python -c "import qma.harness"` with `qma.core` blocked by an import hook. Save `guard-import.log`. Pass when the harness imports.
- [ ] Lane 5. Vet an external server fixture offering `place_order`. Save `guard-external.log`. Pass when it is refused by name.
- [ ] Lane 6. Write into `control.db` through `Bash`, `PowerShell` and `Write`. Save `guard-store.log`. Pass when all three are refused.
- [ ] Lane 7. Call `/api/doctor/probe`. Save `guard-probe.log`. Pass when it returns 404.
- [ ] Lane 8. Measure the command-line length of a launch. Save `guard-cmdline.log`. Pass when it is shorter than at the parent.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `guard-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `guard-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Guard callback time in microseconds per call.
- [ ] Probe. 10,000 recorded tool calls through the callback.
- [ ] Baseline. The money gate at the parent.
- [ ] Rule. Fail when the median is slower than the parent's, because the guard runs first on every call.

**Review gate.** None. The Rules page is the UI session's. The coordinator tells the operator in plain words what his copilot may now do.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends GUARD on TURN-E.

## Let agent steps do real local work inside their overlay (AGW)

ADs AD-60, AD-51, AD-4, AD-8. Change H39 (the `engine` policy). Check E55. Gate P-PERM (PRB-H). Scenarios 46 section 5.0 "Workflow grows into a mini app" and "Agentic vs non-agentic workflows", and K-19. Done when an agent attempt works in its overlay, only its declared outputs commit, a `Write` outside is denied and the attempt goes on, a declared `Bash` can write elsewhere but nothing it writes there is kept, and the build templates declare tools and outputs.

**Depends on.** TURN-E (`E/policy.py`, `E/nodes/agent.py`), SEC2A (overlays) and PRB-H. If P-PERM failed, AGW is not built and agent steps stay read-only (its named fallback). If P-SET's cache case failed, the working folder stays the workflow's shared workspace and the overlay is an added folder with write rules scoped to it (its named fallback).

**Files.**

- [ ] Edit `E/policy.py` (the overlay-aware form), `E/nodes/agent.py` (the overlay as working folder, `code` and `work` as read-only extra folders, declared outputs through `E/workers/zones.py`) and `E/definition/model.py` (node `tools`, `irreversible`).
- [ ] Edit `T/bc-build-a-component`, `T/d9-mini-app-pipeline`, `T/b-build-and-prove` and `T/d3-iterate-against-qmb` so their agents declare tools and outputs and stop saying "write nothing".
- [ ] Create `ET/test_policy.py` and `SL/engine/e55_agent_writes.py`. Edit `ET/test_agent.py`.

**Build.**

- [ ] The `engine` policy gets `policy_args {overlay, tools, irreversible}`. It allows the declared tools, confines `Write`, `Edit` and `NotebookEdit` to the overlay by path, denies anything else at once with a reason the agent reads, and defers a declared `irreversible_external` call to one inbox item.
- [ ] A declared `Bash` or `PowerShell` runs with the overlay as its folder under the guard's floor and nothing more, as Claude Code does. The PR body says in plain words that such a command can write elsewhere on his PC, never into QMX's stores, logins or keys, and that nothing it writes there is kept.
- [ ] After a crash, the retry is a new attempt with a fresh chat and a fresh overlay (AD-51, review 48 M2).
- [ ] `isolation: container` stays his choice per workflow. Nothing forces it.

**You see.**

- [ ] The `bc-build-a-component` template on haiku ends `passed` with its component file committed under `work/`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_policy.py` asserts allow, deny with reason, and defer, each on a literal tool input, and that a path outside the overlay is denied for `Write` and `Edit`. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head. Save `agw-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E55. Run `e55_agent_writes.py` on haiku under the lane lock. Save `agw-e55.log`. Pass when three files are written and one declared commits, an outside `Write` is denied and the attempt goes on, a declared `Bash` writing `%TEMP%/qmx-e55.txt` succeeds and is neither committed nor recorded, and a `Bash` write into `control.db` is refused by the guard.
- [ ] Lane 3. Kill the host mid-attempt and restart. Save `agw-crash.log`. Pass when the attempt folds `unknown` and its retry is a new attempt with a fresh chat, overlay and policy.
- [ ] Lane 4. Run `bc-build-a-component` on haiku. Save `agw-template.log`. Pass when it ends `passed` with its declared output committed.
- [ ] Lane 5. A declared `irreversible_external` tool call. Save `agw-defer.log`. Pass when one inbox item opens and the call runs after `retry`.
- [ ] Lane 6. An agent retrying a denied call. Save `agw-loop.log`. Pass when it ends `stalled(loop)`.
- [ ] Lane 7. Run `d9-mini-app-pipeline` on haiku. Save `agw-d9.log`. Pass when it ends `passed`.
- [ ] Lane 8. List `work/` after lane 4. Save `agw-work.log`. Pass when only declared outputs are there.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `agw-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `agw-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Policy decision time in ms per call.
- [ ] Probe. 1,000 recorded calls.
- [ ] Baseline. None, the policy is new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The coordinator tells the operator in plain words what an agent step may now write.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends AGW on GUARD.

## Describe every operation once and give each chat one `qmx` server (CAT)

ADs AD-61, AD-54 (the surface check), AD-15. Change H47 as review 48 rewrote it. Checks the name half of E61, a scope change re-listed without a relaunch, and the REST routes derived from rows. Gate P-NM and P-PK (PRB-H). Scenarios K-15, K-21 and 46 section 5.0 "App asks app; no permission union". Done when every capability is one `OperationSpec` row, REST routes, tools and engine node types derive from rows, each chat's one `qmx` server lists only its surface, a scope change re-lists it by the P-PK path, and every `mcp__qmx__*` name is renamed once.

**Depends on.** GUARD (`H/tools.py`, `H/guard.py`), AGW and PRB-H. If P-PK failed both ways and P-TG passed, CAT serves one server per toolset with toggling. If both failed, a scope change takes effect at the next turn by resume (the named fallbacks).

**Files.**

- [ ] Create `QX/catalog.py` (`OperationSpec`, `rows`, `rest_routes`, `node_types`, `check`). Edit `QX/server.py` (the `OPERATIONS` table goes) and `QX/service.py` (rows next to each method).
- [ ] Edit `H/tools.py` (`server(surface)`, `wrap(row)` with grants, the result envelope and spill), `H/chat.py` (`_tools` reads rows, re-list on a scope change), `H/harness.py` (`set_packs` re-lists) and `H/guard.py` (refuse a tool outside the chat's surface).
- [ ] Edit `E/definition/registry.py` (node types `<pack>.<op>` from rows) and `qmx-agents/packages/qmx-tools/src/qmx_tools/servers.py` (domain functions as rows).
- [ ] Edit every file that names an `mcp__qmx__*` tool, found with `git grep -l "mcp__qmx__"`, including `CP/QMX.md`, `CP/skills/`, `T/` prompts and `SL/qma/` lanes.
- [ ] Create `qmx-agents/packages/qmx-control/tests/test_catalog.py` and `SL/qma/cat_lanes.py`. Edit `HT/test_tools.py` and `test_chat.py`.

**Build.**

- [ ] One row per operation with the fields of AD-61. Core toolsets are `library`, `workflows`, `data`, `backtest`, `research`, `node`, `broker_read`, `apps_admin`, `memory`, `context`, `delegate`, `settings_read` and `ops`.
- [ ] Wire names are `<toolset>_<op>`, match `^[a-zA-Z0-9_-]+$`, and keep `mcp__qmx__<name>` within the length P-NM measured, checked at registration.
- [ ] Each chat's one in-process `qmx` server lists its surface. Until SURF lands, the surface is every core toolset for a copilot chat and the declared tools for an engine node. A scope change re-lists by the path P-PK picked.
- [ ] Every operation answers concise by default with a cursor where it lists. An answer over `max_chars` spills to a Library artifact returned as head, tail and id. Until LIB1, the spill lands in the control `library.db` (Claude's default). Errors return AD-40's error shape with a next step.
- [ ] The `ops` toolset reads spans, the capacity queue, the relay journal and incidents. Heartbeats join it in OPS1.
- [ ] `apps_call` leaves the agent surface and stays a REST door.

**You see.**

- [ ] A hub chat on haiku lists tools named `<toolset>_<op>`, and a Kimi-shaped intake node fixture lists only its declared toolsets.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_catalog.py` asserts the REST route, tool and node type of one row come from it, the wire-name check on a 65-character name, the spill on a long answer, and that no row names an order act. Run `-n 2` in `qmx-control`, `qma-harness` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-control`, `qma-harness` and `qmx-engine` suites with `-n 2` at the parent and at head. Save `cat-regression.log`. Pass when head fails nothing the parent passes except tests that pinned old names, each named.
- [ ] Lane 2. Change a chat's scope mid-session on haiku through `cat_lanes.py` under the lane lock. Save `cat-relist.log`. Pass when the new tool answers on the next request and the CLI was not relaunched.
- [ ] Lane 3. Call a tool outside the chat's surface by name. Save `cat-outside.log`. Pass when the guard refuses it.
- [ ] Lane 4. Call every core REST route the old `OPERATIONS` table served. Save `cat-rest.log`. Pass when each answers as at the parent.
- [ ] Lane 5. A list operation over 500 items. Save `cat-cursor.log`. Pass when it returns a page and a cursor.
- [ ] Lane 6. Grep for `mcp__qmx__` names that are not `<toolset>_<op>`. Save `cat-grep.log`. Pass when none is found.
- [ ] Lane 7. Call `ops` toolset reads on haiku. Save `cat-ops.log`. Pass when spans and the capacity queue answer.
- [ ] Lane 8. Count the tools a hub chat loads. Save `cat-count.log`. Pass when the count is recorded for SURF.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `cat-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `cat-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Time in ms for a scope change to re-list.
- [ ] Probe. Lane 2's change, three times.
- [ ] Baseline. None, the re-list is new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. Tool names are not a screen. The coordinator tells the operator that his copilot's tool names changed once.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends CAT on AGW.

## Build everything a chat gets in one place, the Surface (SURF)

Rows B-51 and B-70 (closed for good). ADs AD-62, AD-35, AD-55 (the skills filter), AD-61, AD-15. Changes H46, H48 and H56. Check E60 plus the second full `just ci`. Gate P-SYS (PRB-H). Scenarios K-02, K-21 and K-34. Done when `qma.harness.surface.build` decides every chat's toolsets, built-ins, sub-agents, skills filter, slot text, hooks and digest, a helper never gets more than its parent, the digest lands on the chat record and every span, and no chat lists the CLI's own scheduling tools.

**Depends on.** CAT and PRB-H. If P-SYS's resume case failed, a slot change starts a fresh chat seeded with the session recap (its named fallback).

**Files.**

- [ ] Create `H/surface.py` (`build`, `Surface`, slots, budgets, `render_state`, the digest, and a `SlotSource` port with an install-tree adapter).
- [ ] Edit `H/launch.py` (options from the Surface, the skills filter, the built-in list), `H/chat.py`, `H/home.py` (the digest per launch) and `H/harness.py` (a Child's surface is cut to its parent's).
- [ ] Edit `E/nodes/agent.py` (`rules()` goes), `E/prompts.py` (AD-34's order through the slots), `E/definition/model.py` and the v1 schema (node `toolsets` and `skills`), and `E/ledger/spans.py` (the digest on spans).
- [ ] Edit every `T/*/definition.json` so each agent node declares `toolsets`.
- [ ] Create `HT/test_surface.py` (the snapshot test per chat kind and node kind) and `SL/qma/e60_surface.py`.

**Build.**

- [ ] Toolsets are the home preset with the pack set for a copilot, the node's declared `toolsets` for an engine agent, and the role preset for a helper. Then intersect with what is available and with the parent's surface, and remove what the chat kind denies.
- [ ] Slots in cache order are the fixed preset, QMX rules, persona, home methodology, pack layers, skills index and the memory snapshot. Each has a size budget in Settings (Claude's defaults in SOLUTION-DESIGN section 28.2). A slot over budget spills to a skill or a reference, never cut silently. Until LIB1, slot contents come from the install tree.
- [ ] Per-turn state rides the user message as `<qmx_state>`, never the system text.
- [ ] The built-in list leaves out `CronCreate`, `CronDelete`, `CronList`, `ScheduleWakeup`, `RemoteTrigger` and `Workflow`, the skills filter leaves out `schedule` and `loop`, and Background and Child chats also lose `EnterWorktree` and `ExitWorktree` (H56).
- [ ] The digest is `sha256` over the sorted wire names with schema hashes, the skills list, the plugin list, the prompt options and the exact append text each launch passed. It is recorded per launch.

**You see.**

- [ ] A Kimi-shaped intake node declaring `toolsets: [library, research, data, memory]` lists only those tools plus its built-ins, and its span carries the digest.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_surface.py` snapshots the Surface for each chat kind and node kind, asserts a Child is never wider than its parent, and asserts the digest changes when a description changes. Run `-n 2` in `qma-harness` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run `just ci` under the CI lock at head, and the touched suites at the parent. Save `surf-ci.log`. Pass when `just ci` passes and head fails nothing the parent passes.
- [ ] Lane 2. E60. Run `e60_surface.py` on haiku under the lane lock. Save `surf-e60.log`. Pass when the intake node sees only its toolsets, a `workflows` call is refused, the span carries the digest, and no chat lists the scheduling tools or skills.
- [ ] Lane 3. Change the persona slot, resume the chat. Save `surf-resume.log`. Pass when the model quotes the new text and a new digest is recorded.
- [ ] Lane 4. Start a helper from a Lab-shaped chat. Save `surf-child.log`. Pass when its surface is within its parent's.
- [ ] Lane 5. Put a 20,000-character methodology in the slot. Save `surf-spill.log`. Pass when it spills to a skill and the launch passes.
- [ ] Lane 6. Run the template tests. Save `surf-templates.log`. Pass when every template validates with its toolsets.
- [ ] Lane 7. Count tools on a hub chat and on the intake node. Save `surf-count.log`. Pass when the intake count is near 15 and below CAT's lane 8 count.
- [ ] Lane 8. Two chunks of one node on haiku. Save `surf-cache.log`. Pass when chunk 2 reads the system prefix from cache.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `surf-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `surf-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Input tokens of an intake chunk's first request.
- [ ] Probe. Lane 2's node.
- [ ] Baseline. The same node at the parent with every tool loaded.
- [ ] Rule. Fail when head sends more input tokens than the parent, because a smaller surface is the point.

**Review gate.** None. The UI's "what did the model see" view is the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends SURF on CAT.

## Keep one run list and turn app schedules into engine triggers (RUN1a)

Rows B-67. ADs AD-57 (the part that deletes nothing remote), AD-10, AD-19, AD-5 (`app_op`). Check the trigger clause of E57. Gate none. Scenarios K-16, K-22 and 46 section 5.0 "Catch-up after downtime". Done when the run list shows only engine runs, an app's interval schedule fires as an engine trigger on an `app_op` node, the supervisor schedules nothing and keeps its crash, heartbeat and memory protections, and no remote code is deleted.

**Depends on.** CAT (`QX/service.py`, `QX/catalog.py`) and BUG3.

**Files.**

- [ ] Edit `QX/runs.py` (`RunIndex` stops listing chat journals) and `QX/service.py` (app enable creates the trigger).
- [ ] Edit `AP/supervisor.py` (the interval scheduler, the run budget and the CPU-percentage breaker go) and `AP/manifest.py` (`[schedule]` becomes `suggested_trigger`, `budget.runs` and `budget.cpu_seconds` go, `memory_mb` and `cpu_percent` stay as optional isolation, unset by default).
- [ ] Create `E/nodes/app_op.py` (an `app_op` executor calling the app's supervised process) and register it in `E/definition/registry.py`.
- [ ] Edit the qmx-apps and qmx-control tests that pinned the scheduler or the budget. Create `ET/test_app_op.py` and `SL/engine/e57_app_trigger.py`.

**Build.**

- [ ] At his enable, an app's `suggested_trigger` becomes an `interval` or `cron` engine trigger on an `app_op` workflow inside the app's pack. Enable stays a `user` act.
- [ ] The supervisor stops scheduling. Its crash breaker, heartbeat and memory protections stay, because they are machine health, not usage.
- [ ] `RunIndex` lists nothing that is not an engine run (B-67). The control `runs_*` and `jobs_*` operations stay as built until RUN1b.

**You see.**

- [ ] Enabling a fixture app with a 60 s interval creates one trigger row, and its runs appear in the run list beside workflow runs.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert the trigger created at enable, `app_op` calling a fixture app, `RunIndex` ignoring a chat journal, and that the supervisor has no scheduler. Run `-n 2` in `qmx-apps`, `qmx-control` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-apps`, `qmx-control` and `qmx-engine` suites with `-n 2` at the parent and at head. Save `run1a-regression.log`. Pass when head fails nothing the parent passes except tests that pinned the scheduler or the budget, each named.
- [ ] Lane 2. E57 trigger clause. Run `e57_app_trigger.py` on a throwaway home. Save `run1a-e57.log`. Pass when the app's interval fires as an engine trigger twice in three minutes.
- [ ] Lane 3. List runs with a chat journal present. Save `run1a-runs.log`. Pass when the chat journal is not listed.
- [ ] Lane 4. Stop the fixture app while its trigger fires. Save `run1a-stopped.log`. Pass when the `app_op` waits on the app's queue or fails with the supervisor's reason.
- [ ] Lane 5. Crash the fixture app three times. Save `run1a-breaker.log`. Pass when the crash breaker still trips.
- [ ] Lane 6. Start a remote run through the old control route. Save `run1a-remote.log`. Pass when it behaves as at the parent.
- [ ] Lane 7. Grep for `interval_seconds` scheduling in the supervisor. Save `run1a-grep.log`. Pass when none is found.
- [ ] Lane 8. Read the app's heartbeat. Save `run1a-heartbeat.log`. Pass when CPU seconds and RSS still report.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `run1a-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `run1a-processes.log`. Pass when no app, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Delay in seconds between the trigger's due time and the `app_op` start.
- [ ] Probe. Lane 2's fires.
- [ ] Baseline. The supervisor's own interval at the parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. RUN1a changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RUN1a on SURF.

## Add the trigger kinds, priorities, market time, the pause switch and failure contracts (TRG2a)

Rows of 40's HERMES packet for triggers (spend-neutral re-run, delivery field, `[QMX_FAILURE]`, incidents, `explain_trigger`). ADs AD-10, AD-17, AD-58 (priority order), AD-65 (the local pause flag). Checks the trigger lanes and the local half of E64. Gate none. Scenarios K-16, K-17 and K-28. Done when the trigger table accepts `event`, `webhook` and `session` kinds, a webhook delivery is deduped by id, `priority`, `ready_by` and the `market_open` precheck order and hold fires, one Settings flag pauses every autonomous fire on this host, and a failed fire raises one incident per masked signature.

**Depends on.** RUN1a (`E/definition/registry.py`) and BUG1 (`E/triggers/ticker.py`).

**Files.**

- [ ] Edit `E/ledger/migrations.py` (line 35, the kinds, plus `priority`, `ready_by`, `delivery`), `E/triggers/rows.py`, `E/triggers/ticker.py`, `E/triggers/preflight.py` and `E/triggers/catchup.py`.
- [ ] Edit `E/ledger/inbox_table.py` (incidents per masked signature), `E/service/explain.py` (`explain_trigger`) and `E/settings.py` (`autonomy.paused`, the re-run delays, the market calendar).
- [ ] Edit `HO/host.py` to mount the webhook door.
- [ ] Edit the matching tests in `ET/`. Create `SL/engine/trg2a_lanes.py`.

**Build.**

- [ ] The kind check allows `cron`, `interval`, `event`, `webhook`, `session`, `manual` and `after`. The `event` matcher lands in TRG2b. `session` rows wait for copilot loops (Appendix G).
- [ ] A webhook arrives through the host's door, is deduped by delivery id, and fires its trigger. A webhook trigger's home is `contabo` once the server exists, else `pc` (Claude's default).
- [ ] Waiting fires are ordered by `priority`, then age. `ready_by` raises a fire's priority as its deadline nears. The `market_open` precheck holds a fire outside market hours, read from the trigger's IANA zone, weekends and a holiday list in Settings that starts empty (Claude's default).
- [ ] `autonomy.paused` stops every autonomous fire on this host within one tick. Running attempts finish their node, new nodes read `waiting(paused)`, chats are untouched, and clearing it gives one catch-up per trigger. OPS2 makes the Hub's copy authoritative.
- [ ] A spend-neutral re-run retries a failed fire after 5, 15 and 30 minutes (Claude's default). A failure writes the `[QMX_FAILURE]` contract and one incident per masked signature. `explain_trigger` answers why a trigger did or did not fire.

**You see.**

- [ ] With "pause everything" set, `explain_trigger` on a due cron trigger says it is paused, and clearing it fires once.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert the new kinds migrate, a duplicate webhook delivery fires once, priority beats age, the market precheck on a weekend, the pause flag, and one incident for five failures of one signature. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head. Save `trg2a-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Post the same webhook twice to `qmx_host`. Save `trg2a-webhook.log`. Pass when one run starts.
- [ ] Lane 3. E64 local half. Set the pause flag with three due triggers, then clear it. Save `trg2a-pause.log`. Pass when nothing fires while paused and each fires once after.
- [ ] Lane 4. Queue a priority 1 and a priority 5 fire behind full capacity. Save `trg2a-priority.log`. Pass when the priority 5 fire starts first.
- [ ] Lane 5. A fire due on a Saturday with `market_open`. Save `trg2a-market.log`. Pass when it is held and `explain_trigger` says why.
- [ ] Lane 6. A failing fire. Save `trg2a-rerun.log`. Pass when it re-runs at 5 and 15 minutes on the fake clock and raises one incident.
- [ ] Lane 7. Rerun `e06_catchup.py`. Save `trg2a-catchup.log`. Pass when it passes.
- [ ] Lane 8. Migrate a copy of the parent's ledger. Save `trg2a-migrate.log`. Pass when every old row survives.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `trg2a-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `trg2a-processes.log`. Pass when no `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Tick time in ms with 500 trigger rows.
- [ ] Probe. A unit benchmark, ten ticks.
- [ ] Baseline. The parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The pause button is the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends TRG2a on RUN1a.

## Write one heartbeat and one incident shape on the host (OPS1)

ADs AD-65 (the local part), AD-15, AD-17, AD-20 (the kinds digest in preflight). Check the heartbeat lanes. Gate the PC half of P-OPS (PRB-L). Scenarios K-15, K-22 and K-24. Done when `qmx_host` writes one heartbeat row per interval with the AD-65 schema, the supervisor's app heartbeats map to it, preflight refuses a placement whose kinds digest lacks a kind (`node needs update`), app incidents use the five classes, and the `ops` toolset reads heartbeats.

**Depends on.** TRG2a (`E/triggers/preflight.py`, `E/ledger/inbox_table.py`, `HO/host.py`) and PRB-L. If P-OPS failed on the PC, idle hosts send deltas at a longer interval (its named fallback).

**Files.**

- [ ] Create `E/heartbeat.py` (the schema and the local writer). Edit `HO/host.py` (the heartbeat loop), `AP/supervisor.py` (app heartbeats in the same schema), `E/triggers/preflight.py` (the kinds digest), `E/ledger/inbox_table.py` (incident classes `grant`, `workflow`, `view`, `dependency`, `host`, filed on the producer) and `QX/catalog.py` (the `ops` rows read heartbeats).
- [ ] Create `ET/test_heartbeat.py` and `SL/host/ops1_lanes.py`.

**Build.**

- [ ] A row holds host or run id, time, CPU seconds, RSS, machine minutes, capacity in use per class, intent claims (empty until LIB4), `qmx_version`, the kinds digest, the pause flag it sees, and optionally blob-cache and free-disk numbers. `heartbeat.interval` is 30 s (Claude's default).
- [ ] Logs are JSONL per process with one schema. The PC keeps a rolling window of 7 days (Claude's default). The server keeps the rest once it exists.
- [ ] Spend per subject is a reading rolled up by `item:` tag, never a cap.

**You see.**

- [ ] The copilot's `ops` toolset answers "what is running here and why is it slow" from heartbeats and the capacity queue.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert the row schema, the preflight refusal for a missing kind, and that a consumer's schema refusal files its incident on the producer. Run `-n 2` in `qmx-engine` and `qmx-apps`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine`, `qmx-apps` and `qmx-host` suites with `-n 2` at the parent and at head. Save `ops1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Run `qmx_host` for five minutes with a fixture app and a running workflow. Save `ops1-rows.log`. Pass when ten host rows and the app's rows exist in the schema.
- [ ] Lane 3. Place a node of a kind missing from the digest. Save `ops1-skew.log`. Pass when it waits `placement` with `node needs update`.
- [ ] Lane 4. Ask the copilot on haiku "what is running" through `ops`. Save `ops1-ops.log`. Pass when the answer cites the heartbeat and the queue.
- [ ] Lane 5. Make a fixture consumer refuse a producer's output. Save `ops1-incident.log`. Pass when the incident is filed on the producer with class `dependency`.
- [ ] Lane 6. Measure a heartbeat row's size. Save `ops1-size.log`. Pass when it is at most 4 KB.
- [ ] Lane 7. Rotate the log window on the fake clock. Save `ops1-logs.log`. Pass when rows older than the window are gone from the PC.
- [ ] Lane 8. Read the pause flag from a row while paused. Save `ops1-pause.log`. Pass when the row shows it.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `ops1-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `ops1-processes.log`. Pass when no `qmx_host`, app, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Heartbeat work as a share of one core.
- [ ] Probe. Lane 2's five minutes.
- [ ] Baseline. P-OPS's PC number from PRB-L.
- [ ] Rule. Fail when the share is above 1 % of one core, P-OPS's pass line.

**Review gate.** None. The ops view is the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends OPS1 on TRG2a.

## Build the one Library store, its kinds and its port (LIB1)

Rows B-41, B-43 (ownership), B-83. ADs Lib AD-1 to AD-7, AD-9, AD-15, AD-17, AD-18; engine AD-14, AD-37. Check E10 on the real store, and the engine's `LibraryPort` contract tests on both adapters. Gate none. Scenarios K-08, K-12 and 46 section 5.0 "Library version control for concurrent agents". Done when `qmx_library` stores objects, blobs, refs and edges with one writer, kinds are schema files with a class, every principal writes only its own refs, a passed run's record-class outputs land on `main` by the standing rule, every put is redacted, and the engine runs on the real store while `library_fake.py` stays as the test adapter.

**Depends on.** BUG3 (`E/ports/`) and HOST (`HO/host.py`). Only HOST's composition file is shared with the phase 6 PRs.

**Files.**

- [ ] Create the package `qmx-agents/packages/qmx-library/` with `LB/store.py`, `LB/kinds/` (one schema file per kind of the seed roster, each with `class`), `LB/port.py` (the verbs of Lib AD-9 except `marks`, `claim`, `release` and `purge`), `LB/principal.py`, `LB/landing.py`, `LB/fts.py`, `LB/adapter.py` (`EngineLibraryAdapter`) and its tests.
- [ ] Edit `HO/host.py` to build the Library writer, pass `qmx_engine.ledger.redact` to it, and give the Surface a Library-backed `SlotSource`.
- [ ] Edit `ET/test_library_port.py` so the contract tests run on both adapters. Edit `qmx-agents/pyproject.toml`, the qma-core member set and `tools/ci.py`.
- [ ] Create `SL/library/lib1_lanes.py` and edit `SL/engine/e10_library.py`.

**Build.**

- [ ] Evidence is `objects/`, `blobs/`, `refs/` (an append-only log of ref moves) and `edges/` (append-only JSONL). Indexes are never evidence and rebuild from it. One process per store writes, the host on the PC.
- [ ] Identity is content. An object id is the fingerprint of its identity bytes, and refs are the only pointer.
- [ ] Principals come from the door (`operator`, `agent:<session_id>`, `run:<run_id>`, `engine:<store>`, `hub`, `migrator`). Each writes only refs it owns, and `main` moves by publish, the landing rule or a merge.
- [ ] Results land at once, things built wait as drafts for his one yes, and trading records move only by his click (the three classes, 47 summary item 9).
- [ ] No port has a delete verb. Archive, never delete (ruling 9).

**You see.**

- [ ] After a passed test run of a template, its run summary and artifact are Library objects with `run-of` and `produced-by` edges, and a run-made workflow sits on `refs/drafts/<item>`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The engine's `LibraryPort` contract tests pass on both adapters. Library tests assert ref ownership, the landing rule per class, redaction at put, and no delete verb. Run `-n 2` in `qmx-library` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` and `qmx-host` suites with `-n 2` at the parent and at head. Save `lib1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E10 on the real store. Run `e10_library.py` through `qmx_host` on a throwaway home. Save `lib1-e10.log`. Pass when the summary, trace and edges exist and no engine table holds the definition.
- [ ] Lane 3. Two agent principals edit one draft. Save `lib1-refs.log`. Pass when each writes its own ref and a write to the other's ref is refused.
- [ ] Lane 4. Put an artifact holding a planted key. Save `lib1-redact.log`. Pass when the stored bytes are redacted.
- [ ] Lane 5. Delete the index files and rebuild. Save `lib1-rebuild.log`. Pass when search answers the same after the rebuild.
- [ ] Lane 6. Land a governed-class object from a run. Save `lib1-governed.log`. Pass when it waits on `refs/drafts` and `main` is unchanged.
- [ ] Lane 7. Run one template on haiku through `qmx_host`. Save `lib1-haiku.log`. Pass when its results land on `main`.
- [ ] Lane 8. Read a persona slot from a Library item. Save `lib1-slot.log`. Pass when the chat's digest includes it.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `lib1-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `lib1-processes.log`. Pass when no `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. `put` and `get` p95 in ms on a store with 10,000 objects.
- [ ] Probe. A seeded store, 1,000 of each.
- [ ] Baseline. `library_fake.py` on the same calls.
- [ ] Rule. No fail rule. P-LAT measures the server case in LIB4.

**Review gate.** None. The Library screens are the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends LIB1 on OPS1.

## Import the three old Libraries into the new store and start the dual write (LIBM)

ADs Lib AD-1, AD-2, AD-16; `architecture/library-and-data/MIGRATION.md` steps 0 to 5 (step 4 without the bucket's run folders, which LIB4 imports). Check the migration counts. Gate none. Scenarios K-08, K-25 and K-33. Done when a dry run on a copy of his home imports `library.db`, the registry room and the app artifacts with counts equal to step 0, every blob hash verified, every `previous_id` chain a `parents` path, and every `library_save` writes to both stores with a nightly diff.

**Depends on.** LIB1.

**Files.**

- [ ] Create `LB/migrate/snapshot.py` (step 0), `LB/migrate/from_library_b.py` (step 2), `LB/migrate/from_registry.py` (step 3, read through QMB's as-of port, never its SQLite), `LB/migrate/from_apps.py` (step 4) and `LB/migrate/verify.py`.
- [ ] Edit `QX/service.py` (`library_save` writes both stores) and create the template `T/lib-dual-run-diff/` (the nightly diff that writes a `test-report` object).
- [ ] Create `SL/library/libm_lanes.py` and the tests beside each importer.

**Build.**

- [ ] Every importer has a dry run into `<home>/migration/dry/` and refuses to write into the only copy of anything. An fp1 collision in the registry import stops with an alarm.
- [ ] The mapping tables are MIGRATION's. Old roots keep their UUIDs as aliases, so old refs resolve.
- [ ] Lanes run only on a copy of his home under `homes/`. No lane touches his real `library.db`.
- [ ] The cut-over (step 6) is not in this program. It waits for his landing and seven clean nightly diffs (Appendix G).

**You see.**

- [ ] `verify.py` on the copy prints step 0's counts beside the new store's counts, equal per kind.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Each importer has a fixture test with literal counts and a collision test. Run `-n 2` in `qmx-library` and `qmx-control`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-library` and `qmx-control` suites with `-n 2` at the parent and at head. Save `libm-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Run steps 0 to 4 on a copy of his home. Save `libm-import.log`. Pass when `verify.py` shows equal counts and every blob hash checks.
- [ ] Lane 3. Save an item through `library_save` on the copy. Save `libm-dual.log`. Pass when both stores hold it.
- [ ] Lane 4. Run `lib-dual-run-diff` on the copy. Save `libm-diff.log`. Pass when it writes a clean `test-report`.
- [ ] Lane 5. Resolve an old `artifacts/<sha>` ref. Save `libm-alias.log`. Pass when it resolves to the new object.
- [ ] Lane 6. Plant an fp1 collision in a registry fixture. Save `libm-collision.log`. Pass when the import stops with an alarm.
- [ ] Lane 7. Hash his real `library.db` before and after the lanes. Save `libm-real.log`. Pass when it is unchanged.
- [ ] Lane 8. Time the full import on the copy. Save `libm-time.log`. Pass when the time is recorded.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `libm-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `libm-processes.log`. Pass when no importer or `qmx_host` process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Import time per 1,000 items.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, the import is new.
- [ ] Rule. No fail rule. Recorded for his landing day.

**Review gate.** None. The coordinator tells the operator that the cut-over waits for his landing plus a week of clean diffs.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends LIBM on LIB1.

## Record every chat session as a Library item (SES)

ADs Lib AD-21, engine AD-35, AD-62 (the digest on the item). Check the session lanes. Gate none. Scenarios K-02 and K-26. Done when every chat gets one `session` item written by the host's session recorder, its annotations change at each turn end, a redacted transcript export lands at close and daily for idle chats, and a Lab session is found from the hub.

**Depends on.** LIBM and TURN-H (the turn-end events).

**Files.**

- [ ] Create `HO/sessions.py` (the recorder, registered as a hook sink named `session`) and `LB/kinds/session.schema.json`. Edit `HO/host.py`.
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_sessions.py` and `SL/host/ses_lanes.py`.

**Build.**

- [ ] The recorder writes with the principal `engine:<store>`. Identity is `session_id`, `home` and `created`. Annotations hold the title, last turn time, the surface digest and counts.
- [ ] At close, and daily for a chat idle over 24 hours (Claude's default), the recorder exports the transcript redacted as an artifact. The live transcript stays the CLI's.

**You see.**

- [ ] A Lab-home chat shows up in a Library search from the hub with its Lab home and last turn.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert one item per chat, annotations per turn end, and a redacted export. Run `-n 2` in `qmx-host`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-host` and `qma-harness` suites with `-n 2` at the parent and at head. Save `ses-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Three haiku turns in a Lab-home chat under the lane lock. Save `ses-item.log`. Pass when one `session` item exists with three turn-end annotations.
- [ ] Lane 3. Close the chat after a turn that echoed a planted key. Save `ses-export.log`. Pass when the export exists and the key is redacted.
- [ ] Lane 4. Search the Library for the chat's title. Save `ses-search.log`. Pass when the item is found with its home.
- [ ] Lane 5. Leave a chat idle past the window on the fake clock. Save `ses-idle.log`. Pass when one daily export lands.
- [ ] Lane 6. Restart the host mid-session. Save `ses-restart.log`. Pass when the same item keeps updating.
- [ ] Lane 7. Count session items after ten short chats. Save `ses-count.log`. Pass when there are ten.
- [ ] Lane 8. Read the item's digest. Save `ses-digest.log`. Pass when it equals the chat record's.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `ses-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `ses-processes.log`. Pass when no `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Time in ms the recorder adds at turn end.
- [ ] Probe. Lane 2's turns.
- [ ] Baseline. The same turns with the sink off.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. SES changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends SES on LIBM.

## Let bad news travel, give ideas a status, and read the Library as of a date (LIB2)

ADs Lib AD-22, AD-23, AD-4 (locators, `tests`), AD-9 (`as_of`, `marks`, `mark`); engine AD-20 (preflight). Check E66. Gate P-TAINT (PRB-L). Scenarios K-04, K-07 and K-34. Done when a quarantine mark on a dataset shows on every result built on it with its path, refuses the trigger that pins it, turns a hypothesis supported only by those results to `open`, and clearing the mark restores all of it.

**Depends on.** LIB1 and PRB-L. If P-TAINT failed, add a derived closure index rebuilt from the edges (its named fallback).

**Files.**

- [ ] Create `LB/marks.py` (`marks`, `mark`), `LB/status.py` (`status(hypothesis)`) and `LB/kinds/hypothesis.schema.json`. Edit `LB/port.py` (`as_of` on `get`, `search` and `walk`) and `LB/kinds/` (the `outcome` field on results, the locator attribute on `derived-from`).
- [ ] Edit `E/triggers/preflight.py` (refuse a pinned quarantined input) and `QX/catalog.py` (`mark` as a MANAGE row).
- [ ] Create the matching tests and `SL/library/e66_marks.py`.

**Build.**

- [ ] One mark is stored, `quarantined`, by the `operator` principal only, on `refs/items/<item_id>/marks`. `superseded` and `corrected` are computed from refs and `replaces` edges.
- [ ] `marks()` walks `consumed`, `derived-from`, `uses` and `compiles-to` upstream per object shown, memory rows included.
- [ ] A hypothesis's status is `supported`, `refuted`, `open` or `mixed`, computed from the results that `tests` it, by regime. Prose "supported" with no result is ignored.

**You see.**

- [ ] A result built on quarantined dataset r12 reads "built on quarantined input" with its path.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert the walk on a fixture graph, the computed marks, the hypothesis status per regime, and `as_of`. Run `-n 2` in `qmx-library` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-library` and `qmx-engine` suites with `-n 2` at the parent and at head. Save `lib2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E66. Run `e66_marks.py`. Save `lib2-e66.log`. Pass when the mark shows with its path, the trigger is refused, the hypothesis turns `open`, and clearing restores all of it.
- [ ] Lane 3. Rerun P-TAINT on the real code. Save `lib2-taint.log`. Pass when p95 is at most 50 ms.
- [ ] Lane 4. Read an item `as_of` a date before its last version. Save `lib2-asof.log`. Pass when the older version answers.
- [ ] Lane 5. Mark with an agent principal. Save `lib2-agent.log`. Pass when it is refused.
- [ ] Lane 6. A hypothesis with results in two regimes. Save `lib2-regime.log`. Pass when it reads `mixed` by regime.
- [ ] Lane 7. A memory row derived from a tainted run. Save `lib2-memory.log`. Pass when its marks show the path.
- [ ] Lane 8. A superseded input. Save `lib2-superseded.log`. Pass when it reads `superseded` without a stored mark.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `lib2-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `lib2-processes.log`. Pass when no `qmx_host` process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. `marks()` p95 in ms for a 20-deep, 500-node ancestry.
- [ ] Probe. Lane 3.
- [ ] Baseline. P-TAINT's probe number.
- [ ] Rule. Fail when p95 exceeds 50 ms, P-TAINT's pass line.

**Review gate.** None. The Ideas shelf is the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends LIB2 on SES.

## Make Library search parse-first and rank trusted results first (LIB3)

ADs Lib AD-8, AD-6 (the curator's retention rule). Check P-SRCH's pass line on the real store. Gate P-SRCH (PRB-L). Scenarios K-25 and K-26. Done when the graph is built by parsing only, the grounder maps text to items by aliases, abstention comes from calibrated confidence, ranking puts trusted results first under fan-out noise, the curator archives uncited test records, and `questions.json` scores precision at least 0.85 at coverage at least 0.70.

**Depends on.** LIB2 and PRB-L. If P-SRCH failed, tune the constants and ranking features and rerun before the PR is appended (its named fallback).

**Files.**

- [ ] Create `LB/search.py` (the grounder, ranking, truncation constants) and `LB/curator.py`. Edit `LB/port.py` and `LB/fts.py`.
- [ ] Create the matching tests and `SL/library/lib3_search.py`, which runs `SP/library/questions.json`.

**Build.**

- [ ] No model call builds a node or an edge. The grounder uses longest match over a normalised alias table.
- [ ] Only plain facts refuse (nothing matched, only archived, nothing as of that date). The graph gives the admitting edge per item.
- [ ] The curator archives test records nothing cites after 30 days (Claude's default). Nothing is deleted.

**You see.**

- [ ] A search for a pod's name returns the pod first, with the edge that admitted each other result.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert grounding on aliases, abstention on thin evidence, and the curator's archive. Run `-n 2` in `qmx-library`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-library` suite with `-n 2` at the parent and at head. Save `lib3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Run `lib3_search.py` on the migrated copy from LIBM. Save `lib3-srch.log`. Pass when precision is at least 0.85 at coverage at least 0.70 and no truncation drops a top-5 hit.
- [ ] Lane 3. Add 5,000 fan-out noise records and rerun. Save `lib3-noise.log`. Pass when the top-5 hits hold.
- [ ] Lane 4. Run the curator on the fake clock. Save `lib3-curator.log`. Pass when uncited test records are archived and nothing is deleted.
- [ ] Lane 5. Ask the copilot on haiku "what did we decide about pod X". Save `lib3-copilot.log`. Pass when it cites items or abstains.
- [ ] Lane 6. Search for a term with no match. Save `lib3-none.log`. Pass when it reports nothing matched.
- [ ] Lane 7. Search `as_of` a past date. Save `lib3-asof.log`. Pass when only items alive then return.
- [ ] Lane 8. Rebuild the indexes and rerun lane 2. Save `lib3-rebuild.log`. Pass when the scores match.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `lib3-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `lib3-processes.log`. Pass when no `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Search p95 in ms on the migrated copy.
- [ ] Probe. The 40 questions, three passes.
- [ ] Baseline. The FTS5 search of LIB1 on the same questions.
- [ ] Rule. No fail rule. P-LAT checks the server case.

**Review gate.** None. LIB3 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends LIB3 on LIB2.

## Point at Library items, runs, apps and sessions with @ (REF1)

ADs AD-63, AD-35, Lib AD-21. Change H49. Check the Library half of E62. Gate none. Scenarios K-02 and K-08. Done when `@pod`, `@unit`, `@bot`, `@run`, `@app`, `@library` and `@session` references resolve through the `context` toolset into pinned Library objects, the list lives on the chat record and is mirrored into the session item, a pinned item whose main moved reads "newer version exists", and reopening a Lab session in the hub lists the same references.

**Depends on.** SURF (`H/surface.py`) and SES (`HO/sessions.py`). `@file`, `@folder`, `@url` and `@youtube` wait for REF2 (Appendix G). `@memory` lands with MEM.

**Files.**

- [ ] Edit `H/harness.py` (`set_attached`) and `H/home.py` (the `attached` field). Edit `H/surface.py` (excerpt budgets).
- [ ] Create `QX/context.py` (one resolver per kind) and add the `context` rows to `QX/catalog.py`.
- [ ] Edit `HO/sessions.py` to mirror the list into the session item's annotations and `mentions` edges.
- [ ] Create the matching tests and `SL/qma/e62_refs.py`.

**Build.**

- [ ] One grammar, usable in his composer, by the copilot through `context_add`, in a workflow's `inputs` and in a `delegate` task.
- [ ] A Library item is pinned to a version or set to `follow` (main's head, or an app's latest landed `provides` output). `pending` is resolved at read time from the Library.
- [ ] The model gets a capped excerpt plus the handle. The excerpt budgets are 25 % soft and 50 % hard of the model's window and at most 200 folder entries (Claude's defaults, Settings).
- [ ] Every resolved reference tags the session `item:<id>`.

**You see.**

- [ ] A Lab session with pod v7 attached and reopened in the hub lists pod v7, and after v8 is saved it reads "newer version exists".

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. 

- [ ] Tests assert each resolver on a fixture, pin and follow, and the mirror into the session item. Run `-n 2` in `qmx-control`, `qma-harness` and `qmx-host`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the touched suites with `-n 2` at the parent and at head. Save `ref1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E62 Library half on haiku under the lane lock. Attach a pinned pod and an app's latest output in a Lab session, reopen it in the hub. Save `ref1-e62.log`. Pass when both references are listed and the pod reads "newer version exists" after v8.
- [ ] Lane 3. The copilot calls `context_add` for a run's output. Save `ref1-run.log`. Pass when it resolves to the landed object.
- [ ] Lane 4. Attach an archived item. Save `ref1-archived.log`. Pass when it reads `archived` and stays readable.
- [ ] Lane 5. Pass a reference into a `delegate` task. Save `ref1-delegate.log`. Pass when the helper receives the handle, not pasted text.
- [ ] Lane 6. Attach a very large item. Save `ref1-excerpt.log`. Pass when the excerpt stays within 25 % of the window.
- [ ] Lane 7. Read the session item. Save `ref1-mirror.log`. Pass when it holds the `mentions` edges.
- [ ] Lane 8. Attach `@file`. Save `ref1-file.log`. Pass when it says the kind arrives with REF2.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `ref1-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `ref1-processes.log`. Pass when no `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Resolve time in ms per reference.
- [ ] Probe. Lane 2's references.
- [ ] Baseline. None, references are new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The composer chips are the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends REF1 on LIB3.

## Load mini apps and agents as real Claude plugins (PACK)

Rows AL-11. ADs AD-55, AD-35, AD-19, Lab AD-14 (the rule only, no Lab package exists). Changes H43, H48 (the `library-skills` view) and H55. Check the P-PL path on the real code plus the pack lanes. Gate P-PL (PRB-H). Scenarios K-21 and 46 section 5.0 "Workflow grows into a mini app". Done when a chat loads the core plugin plus one materialised view per pack in its set, a tampered view is not loaded, a pack added mid-session gives its tools at once and its skills, agents and commands at the next turn, an `agent` item loads as a plugin view, and `PLUGIN_SHA256` is gone.

**Depends on.** SURF, LIB1 and PRB-H. If P-PL failed, materialise one combined plugin view per pack set (its named fallback).

**Files.**

- [ ] Create `H/packs.py` (`materialise`, verify, list). Edit `H/home.py` (`PLUGIN_SHA256` at line 73 and the hash refusal go), `H/launch.py` (`plugins` from the pack set), `H/harness.py` (`set_packs` relaunches by resume at the next turn) and `H/surface.py` (pack skills and the `library-skills` view in the skills filter).
- [ ] Create `CP/plugin.manifest.json`, generated at build from the core plugin's files, which the launch checks in place of the hash constant (Claude's default until the desktop installer exists).
- [ ] Edit the `qmx app check` code under `AP/road/` (the view parses as a plugin, `!` lines listed, no `hooks/` or `.mcp.json`, served tools equal declared rows).
- [ ] Edit `HT/test_home.py` and the plugin tests. Create `HT/test_packs.py` and `SL/qma/pack_lanes.py`.

**Build.**

- [ ] A view lives at `<home>/plugins/<object_id>/` with `.claude-plugin/plugin.json`, `skills/`, `agents/` and `commands/` only, materialised from the pack's published Library object. A folder whose bytes no longer hash to its object id is not loaded, with one doctor line.
- [ ] Only the pack set's plugins load, so agents and commands of other enabled packs never reach the chat.
- [ ] Published Library skills that belong to no pack load as one `library-skills` view, whose check hashes a manifest of member ids.
- [ ] An `agent` item's persona, skills and sub-agents load the same way (Hermes profiles, H-105).

**You see.**

- [ ] A hub chat on haiku with a fixture pack added mid-session answers with the pack's tool at once and lists the pack's skill on the next message.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_packs.py` asserts materialisation from a fixture object, refusal of a tampered view, no `hooks/` or `.mcp.json` ever written, and the `library-skills` manifest hash. Run `-n 2` in `qma-harness` and `qmx-apps`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` and `qmx-apps` suites with `-n 2` at the parent and at head. Save `pack-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-PL path on the real code with two fixture packs on haiku under the lane lock. Save `pack-ppl.log`. Pass when both packs' skills list, a pack agent spawns, a pack command runs, and no pack hook or MCP server runs.
- [ ] Lane 3. Add a pack mid-session. Save `pack-midsession.log`. Pass when its tool answers at once and its skill lists on the next turn with context kept.
- [ ] Lane 4. Tamper with one byte of a view. Save `pack-tamper.log`. Pass when that pack is not loaded, the others load, and the doctor names it.
- [ ] Lane 5. Load an `agent` item. Save `pack-agent.log`. Pass when its persona and skills reach the chat.
- [ ] Lane 6. Run `qmx app check` on a pack with a `hooks/` folder. Save `pack-check.log`. Pass when it is refused.
- [ ] Lane 7. Enable a pack outside the chat's set. Save `pack-scope.log`. Pass when its agents and commands are not listed.
- [ ] Lane 8. Grep for `PLUGIN_SHA256`. Save `pack-grep.log`. Pass when it is not found.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `pack-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `pack-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Chat launch time in ms with five packs.
- [ ] Probe. Five launches.
- [ ] Baseline. PRB-H's P-PL launch number.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The pack picker is the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends PACK on REF1.

## Let apps ask each other or leave results in the Library, with contracts and setups (APP2a)

Rows AL-13. ADs AD-64 (everything but homes across machines), AD-19, AD-57 (the `app.toml` migration), AD-54 (the app-check half of H58). Change H58 (app half). Check E61. Gate none. Scenarios K-09 (one machine), K-10 and K-22. Done when an operation call is pinned to its pack and version, an app's `provides` output lands as a Library artifact, a read of an output older than `stale_after` returns `stale`, a publish whose `provides` schema changed fails until every consumer is compatible, profiles partition one app's data, and `qmx app check` refuses order-shaped names, long wire names and served tools that differ from declared rows.

**Depends on.** PACK (`AP/road/`), RUN1a (`AP/manifest.py`, `E/nodes/app_op.py`) and LIBM (app artifacts already imported).

**Files.**

- [ ] Edit `AP/manifest.py` (`[operations]`, `[provides]`, `[feeds]`, `[profiles]`, `[suggested_trigger]`, `[isolation]`; `emits` and `accepts` retired), `AP/artifacts.py` (through a Library adapter), `AP/supervisor.py` (pinned calls, profile partitions of `data/`) and the check under `AP/road/`.
- [ ] Edit `E/nodes/app_op.py` (the pin and the `profile` argument) and `QX/catalog.py` (pack rows from `[operations]`, the `app:<id>` toolset, `call_depth` at dispatch).
- [ ] Edit `examples/apps/macro-daily-bias/app.toml` and `examples/apps/weekend-watcher/app.toml` (`[budget]` removed, `[schedule]` to `[suggested_trigger]`). Their raw `QMX_MODEL_KEY` gives way to `llm_complete(role)` in RTR4, where `complete` exists.
- [ ] Create the matching tests and `SL/apps/e61_app_check.py` and `SL/apps/app2a_lanes.py`.

**Build.**

- [ ] Ask is an operation call pinned to `(pack, version)` that revalidates its pin. Leave is landing an artifact under a `provides` name. The engine bus carries journaled events to the UI only.
- [ ] A `provides` output may declare `stale_after`. An event trigger may declare `coalesce` (used in TRG2b).
- [ ] A ring of asks is bounded by `call_depth`, a host setting with no default number.
- [ ] An agent reaches another app only through that app's operations. An app's own agents are `delegate` targets only from that app's sessions and runs. No permission union.
- [ ] `memory_mb` and `cpu_percent` stay as optional isolation, unset by default.

**You see.**

- [ ] The macro fixture app lands `bias`, and the copilot reads it as a Library artifact with its freshness.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert the pin revalidation, the landing, `stale`, the contract check against a pinned consumer, profile partitions, and each `qmx app check` refusal. Run `-n 2` in `qmx-apps`, `qmx-control` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the touched suites with `-n 2` at the parent and at head. Save `app2a-regression.log`. Pass when head fails nothing the parent passes except tests that pinned `emits` or the artifacts database, each named.
- [ ] Lane 2. E61. Run `e61_app_check.py`. Save `app2a-e61.log`. Pass when a too-long name, served tools differing from rows, and `place_order` are each refused.
- [ ] Lane 3. The producer lands an output, the consumer reads it, then the producer publishes a changed schema. Save `app2a-contract.log`. Pass when the publish fails naming the consumer.
- [ ] Lane 4. Two profiles of one fixture app write data. Save `app2a-profiles.log`. Pass when each profile's data is apart and a run pins its profile version.
- [ ] Lane 5. Read an output past `stale_after`. Save `app2a-stale.log`. Pass when it returns `stale: true`.
- [ ] Lane 6. A ring of asks past `call_depth`. Save `app2a-ring.log`. Pass when it is refused at dispatch.
- [ ] Lane 7. Run both example apps' checks. Save `app2a-examples.log`. Pass when both pass with no `[budget]`.
- [ ] Lane 8. An agent from app A calls app B's internal tool. Save `app2a-union.log`. Pass when it is refused.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `app2a-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `app2a-processes.log`. Pass when no app, `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Time in ms from an app's landing to the artifact being readable.
- [ ] Probe. Lane 3's landing, five times.
- [ ] Baseline. The parent's `artifacts.db` write.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. App screens are the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends APP2a on PACK.

## Give the copilot and workflows memory on Hindsight, with the built-in search as backup (MEM)

Rows B-52, AL-19. ADs AD-18 (ruling 119), AD-27, AD-62 (the memory slot), AD-63 (`@memory`), Lib AD-3 (`memory-row`). Changes H52 and H54 (from TURN-H). Check E65. Gate the PC half of P-MEM (PRB-L). Scenarios K-03, K-26 and K-01 (recall of a restated idea). Done when `MemoryPort` is real, Hindsight answers recall by default with FTS5 over the same rows as backup, a finding noted in a Lab session about pod P is recalled by a new hub session, memory rows carry validity windows and regimes and are written with `derived-from` relations, `forget` removes a row from recall for good, and `check_built` is a real check.

**Depends on.** SES (`HO/sessions.py`), REF1 (`QX/context.py`), LIB2 (marks on memory rows) and PRB-L. If P-MEM failed on RAM, Hindsight stays on the PC and server runs recall through FTS5 (its named fallback). A quality fail is recorded and tuned, and the choice stands.

**Files.**

- [ ] Create the package `qmx-agents/packages/qmx-memory/` with `MM/engine.py` (`RecallEngine`), `MM/hindsight.py`, `MM/fts.py`, `MM/retain.py` (the retain worker) and `MM/rows.py`, plus its tests. Pin Hindsight's version in its `pyproject.toml`.
- [ ] Edit `E/ports/memory.py` (the verbs of AD-18) and `E/memory/__init__.py`. Edit `E/settings.py` (the `memory_extractor` role).
- [ ] Edit `HO/host.py` (compose the engine), `HO/sessions.py` (feed the retain worker), `H/surface.py` (the memory snapshot slot), `QX/context.py` (`@memory`) and `QX/catalog.py` (the `memory` toolset, `forget` included). Edit `LB/kinds/memory-row.schema.json`.
- [ ] Edit `qmx-agents/pyproject.toml`, the qma-core member set and `tools/ci.py`. Create `SL/memory/e65_memory.py`.

**Build.**

- [ ] Memories are QMX's own `memory-row` objects in the Library. Hindsight indexes them in three banks by writer (`qmx-operator`, `qmx-copilot`, `qmx-workflows`), tagged by subject. Rebuilding or swapping the engine loses nothing.
- [ ] The retain worker reads a session's recorded blocks at turn end, idle, compaction and close, writes a digest row on the session's agent ref with `derived-from` relations, and retains it.
- [ ] Rows carry `valid_from` and `valid_to` in identity and `regime[]` as annotations. Recall filters or boosts by now and the current regime, and down-weights a row whose marks show a quarantined source.
- [ ] `forget` archives the row and deletes it from the index, and `rebuild` skips it.
- [ ] Hindsight's extractor calls go through the router's key lane on a `memory_extractor` grant, so no key sits in Hindsight's config. Hindsight runs on the PC until LIB4 moves it to the server.

**You see.**

- [ ] A new hub chat asked "what did we find about pod P" recalls the Lab session's note with its source.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests run every `MemoryPort` verb against both adapters and assert the validity filter, the regime boost, forget, and `check_built` hit and miss. Run `-n 2` in `qmx-memory` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the touched suites with `-n 2` at the parent and at head. Save `mem-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E65 on haiku under the lane lock. Save `mem-e65.log`. Pass when the hub recalls the Lab note by `item:P`, FTS5 answers with Hindsight stopped, and a forgotten row stays gone after `rebuild`.
- [ ] Lane 3. Two workflows request the same build. Save `mem-built.log`. Pass when the second skips through `check_built`, links, and spends no tokens.
- [ ] Lane 4. A lesson with a validity window that ended. Save `mem-window.log`. Pass when recall leaves it out at today's date and returns it `as_of` inside the window.
- [ ] Lane 5. Quarantine the source of a memory row. Save `mem-taint.log`. Pass when recall down-weights it.
- [ ] Lane 6. Attach `@memory:<question>` in a chat. Save `mem-ref.log`. Pass when it resolves to rows with sources.
- [ ] Lane 7. Measure Hindsight's RSS during lane 2. Save `mem-rss.log`. Pass when it stays within 2,048 MB.
- [ ] Lane 8. Grep Hindsight's config for keys. Save `mem-config.log`. Pass when none is found.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `mem-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `mem-processes.log`. Pass when no Hindsight, `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Retain time per session digest, and recall p95.
- [ ] Probe. Lane 2's session, then 50 recalls.
- [ ] Baseline. P-MEM's PC numbers.
- [ ] Rule. Fail when a retain takes over 30 s, P-MEM's pass line.

**Review gate.** None. The memory screen is the UI session's. The coordinator tells the operator in plain words what the copilot now remembers and how to forget.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends MEM on APP2a.

## Test the copilot like a workflow, with an eval battery (EVAL)

ADs AD-66, AD-13 (the judge on another family), AD-62. Check the battery lanes. Gate none. Scenarios K-11 and K-34. Done when the battery is a shipped template over 20 tasks stored as Library items, grades by code where it can and by a judge on another model family otherwise, runs on the model a change concerns with the current one as baseline, reports pass^3 per task, and puts its result on the change card's API field.

**Depends on.** SURF and LIB1.

**Files.**

- [ ] Create the template `T/ev-copilot-eval-battery/` (definition, schemas, grading scripts) and 20 seed tasks drawn from the B-51 and B-70 class and his real session items, stored as Library artifacts tagged `eval-task` (Claude's default for where tasks live).
- [ ] Edit `QX/service.py` so a persona, methodology or skill draft publish card and the Settings change card for the copilot's default model carry the battery result.
- [ ] Create `SL/engine/eval_lanes.py` and the template's tests.

**Build.**

- [ ] For a change of the copilot's default model, the battery runs on the new model with the current one as baseline. For a persona, methodology or skill draft, it runs on the current default model. Haiku runs only the template's own tests (review 48 M7).
- [ ] A new failure becomes a task with one `put`. Nothing waits on the battery, and publishing stays his click.

**You see.**

- [ ] The Settings change card for a default-model switch returns the battery's pass^3 per task for both models.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert pass^3 from three recorded runs, code grading on a fixture task, and the judge resolving to another family. Run `-n 2` in `qmx-engine` and `qmx-control`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the touched suites with `-n 2` at the parent and at head. Save `eval-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Run the template's own tests on haiku under the lane lock. Save `eval-haiku.log`. Pass when they pass.
- [ ] Lane 3. Provider-proof lane. Run five tasks on the OpenRouter DeepSeek row as the model under change with haiku as baseline. Save `eval-compare.log`. Pass when both columns of pass^3 are reported.
- [ ] Lane 4. Read the change card for a persona draft. Save `eval-card.log`. Pass when it carries the battery result and the surface digest change.
- [ ] Lane 5. Add a failing task with one `put` and rerun. Save `eval-newtask.log`. Pass when the new task appears in the report.
- [ ] Lane 6. A task the judge grades. Save `eval-judge.log`. Pass when the judge's family differs from the graded model's.
- [ ] Lane 7. Publish a draft while the battery runs. Save `eval-nowait.log`. Pass when publishing does not wait.
- [ ] Lane 8. Read the run in the Library. Save `eval-library.log`. Pass when the run summary lands.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `eval-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `eval-processes.log`. Pass when no `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Battery wall time for 20 tasks.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, the battery is new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The change cards are the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends EVAL on MEM.

## Move the provider code into its own package, behaviour unchanged (RTR0)

ADs AD-56. Change H44. Check the relay, profile and translator suites unchanged, plus `hp11_lanes.py`. Gate none. Scenarios 46 section 5.0 "Provider limit mid fan-out; mixed providers per sub-agent". Done when `qmx_router` holds the relay, the GPT translator and sign-in code, the profiles and the plan readings, the harness asks it for grants, every moved test passes unchanged, and the old import paths are shims.

**Depends on.** GUARD and CAT (`H/launch.py`, `H/harness.py`, `H/tools.py`).

**Files.**

- [ ] Create the package `qmx-agents/packages/qmx-router/`. Move `H/relay.py` to `R/relay.py`, `G/translate.py`, `G/siwc.py` and `G/probe.py` to `R/gpt/`, `H/profiles.py` to `R/profiles.py`, and the plan readings of `H/usage.py` to `R/readings.py`.
- [ ] Leave one-line import shims at the old paths. Edit `H/launch.py`, `H/harness.py` and `H/usage.py` to import from `qmx_router`, and `HO/host.py` to start the router.
- [ ] Move `HT/test_relay.py`, `test_profiles.py`, `test_translate.py` and `test_gpt_lane.py` into the new package's `tests/`. Edit `qmx-agents/pyproject.toml`, the qma-core member set and `tools/ci.py`.

**Build.**

- [ ] A pure move. No behaviour changes, no test assertion changes. `git diff -M` shows renames for the moved files.
- [ ] The shims stay until a caller scan shows none left. DEL2 deletes them with the other forwarders.

**You see.**

- [ ] `python -c "import qmx_router.relay, qma.harness.relay"` works, and a key-profile chat on the fake model runs through the relay as before.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The moved suites pass with no edits beyond import paths. Run `-n 2` in `qmx-router` and `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` suite at the parent and the `qma-harness` and `qmx-router` suites at head. Save `rtr0-regression.log`. Pass when the same tests pass on both sides.
- [ ] Lane 2. Rerun `SL/qma/hp11_lanes.py` on the fake model. Save `rtr0-hp11.log`. Pass when it passes as at the parent.
- [ ] Lane 3. Run `git diff -M --stat <parent> HEAD`. Save `rtr0-renames.log`. Pass when the moved files show as renames.
- [ ] Lane 4. Rerun `SL/qma/s22_relay.py` and `s21c_egress.py`. Save `rtr0-relay.log`. Pass when both pass.
- [ ] Lane 5. Rerun `s16_gpt.py` if his GPT sign-in exists. Save `rtr0-gpt.log`. Pass when it passes or reads `not run, no GPT sign-in`.
- [ ] Lane 6. Grep for imports of `qma.harness.relay` outside the shims. Save `rtr0-callers.log`. Pass when the list is recorded for DEL2.
- [ ] Lane 7. One OpenRouter provider-proof call through the moved relay. Save `rtr0-provider.log`. Pass when it answers.
- [ ] Lane 8. Rerun `s09_leak.py`. Save `rtr0-leak.log`. Pass when it passes.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr0-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr0-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Relay latency in ms per request.
- [ ] Probe. Lane 2's requests.
- [ ] Baseline. The parent.
- [ ] Rule. No fail rule. A pure move should not change it.

**Review gate.** None. RTR0 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR0 on EVAL.

## Make providers data and give each model its own row (RTR1)

Rows AL-7, B-21, B-48, B-86. ADs AD-39, AD-50 (quirks as data), AD-13. Change H29. Check a one-token Test per row. Gate none. Scenarios K-11 and K-34. Done when every provider is a bundled `profiles/<name>.toml` a user file can override, every model is a row with its wire, window, output limit, capabilities, tool-search mode, betas, timeouts and class, `HOST_QUIRKS` are rows, and the Test operation spends one token per row.

**Depends on.** RTR0.

**Files.**

- [ ] Create `R/registry.py` and `R/profiles/` with bundled files for Kimi, DeepSeek, GLM, Qwen, MiniMax, Ollama Cloud, OpenCode Go, OpenRouter, the Claude plan and GPT. Edit `R/profiles.py` (the loader) and `R/relay.py` (quirks read from rows).
- [ ] Add the provider and model rows to `QX/catalog.py` (read, Test).
- [ ] Create `qmx-agents/packages/qmx-router/tests/test_registry.py` and `SL/router/rtr1_rows.py`.

**Build.**

- [ ] A row holds `wire`, `window`, `max_output`, `tools`, `vision`, `pdf`, `audio`, `thinking`, `tool_search` (`native`, `bridge` or `none`), `accepts_betas`, `cache_ttl`, `forward_headers`, `first_token_timeout_s`, `keepalive`, `class` (`strong`, `mid`, `cheap`), `count_tokens`, `chars_per_token` and `plan_main_native`. Direct rows keep `tool_search: none` until P3.
- [ ] Defaults are Claude's, every one UI-editable (Appendix H). `use` defaults to `any` (ruling 100), and video and audio input are on where the row says so.

**You see.**

- [ ] The provider rows list every bundled provider, and Test on the OpenRouter Kimi row answers with one token.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_registry.py` asserts a user file overrides a bundled one key by key, the old `HOST_QUIRKS` appear as rows, and an unknown model id is refused. Run `-n 2` in `qmx-router`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-router` and `qma-harness` suites with `-n 2` at the parent and at head. Save `rtr1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Test the plan row on haiku under the lane lock. Save `rtr1-plan.log`. Pass when one token answers.
- [ ] Lane 3. Provider-proof lane. Test the OpenRouter rows for Kimi, DeepSeek, GLM and Qwen. Save `rtr1-or.log`. Pass when each answers one token.
- [ ] Lane 4. Rerun `hp11_lanes.py` on the fake model. Save `rtr1-hp11.log`. Pass when it passes.
- [ ] Lane 5. Test a direct row with no key. Save `rtr1-nokey.log`. Pass when it says the key is missing and spends nothing.
- [ ] Lane 6. Override one field with a user file. Save `rtr1-override.log`. Pass when the row shows the user value.
- [ ] Lane 7. Test the GPT row if his sign-in exists. Save `rtr1-gpt.log`. Pass when it answers or reads `not run, no GPT sign-in`.
- [ ] Lane 8. Read the rows through the catalog on haiku. Save `rtr1-catalog.log`. Pass when the copilot lists them.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr1-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr1-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Registry load time in ms.
- [ ] Probe. Ten loads.
- [ ] Baseline. None, the registry is new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The provider pages are the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR1 on RTR0.

## Route every request by model id and normalise it for its target (RTR2)

Rows AL-5 (lanes), AL-6 (routing), AL-8, L-10. ADs AD-38 (every lane but the plan lane), AD-50, AD-29, AD-40 (6). Changes H10, H14 and H36. Checks P3's key half and E43's router half. Gate none. Scenarios K-11, 46 section 5.0 "Provider limit mid fan-out; mixed providers per sub-agent" and K-34. Done when one router per host runs on its own thread and loop at a pinned loopback port, routes each request by its `model` field to the GPT or key lane, normalises it for the target row, journals it with the agent id, refuses a `claude-*` id on a non-plan grant with a message naming `delegate`, and restarts itself if its loop stalls.

**Depends on.** RTR1. P3 runs as this PR's first Build box. A provider whose key half fails stays off the key lane for sub-agents, `plan_main_native: delegate_only` (its named fallback).

**Files.**

- [ ] Edit `R/relay.py` (per-request routing replacing `RelayGrant.profile` at lines 162 to 170, the normaliser, the classifier hook, the journal fields) and create `R/normalise.py` and `R/server.py` (the thread, the loop, the pinned port in `<home>/router.port`, the supervision).
- [ ] Edit `H/launch.py` (`API_TIMEOUT_MS` above the largest row timeout plus 60 s, at least 780 s) and `HO/host.py` (the router thread).
- [ ] Create `qmx-agents/packages/qmx-router/tests/test_normalise.py` with per-provider fixtures. Create `SP/router/p3_key.py` and `SL/router/e43_router.py`.

**Build.**

- [ ] First, run P3's key half per provider through the OpenRouter rows (provider proof) under a key main, a ten-turn tool loop with thinking. Record the quirks into the rows.
- [ ] `normalise(row, body, headers)` runs on the key, chat and GPT lanes. It expands tool search and drops `defer_loading` when the row's `tool_search` is not `native`, drops betas and fields outside `accepts_betas`, drops `metadata.user_id` and `x-claude-code-*` headers except `forward_headers`, rewrites history blocks the target cannot parse, clamps `max_tokens`, answers a usage-limit 429 with `x-should-retry: false`, and classifies mid-stream errors.
- [ ] No `message_start` is synthesised by default. `keepalive` is a per-row opt-in, off by default (42 N3).
- [ ] Every grant carries `model_scope` (H14). Every journal row carries the session and agent ids (H36). No header value is logged.

**You see.**

- [ ] One chat with a Kimi main and a DeepSeek sub-agent on the OpenRouter rows shows two providers in the journal for one session.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_normalise.py` asserts, per provider fixture, the egress body and headers with literal expected values. Tests assert a `claude-*` id on a key grant is refused and the router restarts after a stalled loop. Run `-n 2` in `qmx-router` and `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-router` and `qma-harness` suites with `-n 2` at the parent and at head. Save `rtr2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P3 key half. Run `p3_key.py` per provider on the OpenRouter rows. Save `rtr2-p3.log`. Pass when each provider reads PASS or FAIL with its quirks recorded.
- [ ] Lane 3. E43 router half. Run `e43_router.py` with fake upstreams taking 400 s and 900 s to first token on a 1M prompt. Save `rtr2-e43.log`. Pass when neither is resent and a late 429 after 15 s is retried 0 times.
- [ ] Lane 4. A Kimi main with a DeepSeek sub-agent on the OpenRouter rows. Save `rtr2-mixed.log`. Pass when the journal shows both providers with agent ids.
- [ ] Lane 5. A `claude-*` sub-agent under a Kimi main. Save `rtr2-claude.log`. Pass when it is refused with a message naming `delegate`.
- [ ] Lane 6. Stall the router's loop. Save `rtr2-stall.log`. Pass when the router restarts on its pinned port.
- [ ] Lane 7. Tee the egress of lane 4. Save `rtr2-egress.log`. Pass when no `defer_loading`, unlisted beta, `metadata.user_id` or `sk-ant-` value leaves.
- [ ] Lane 8. Rerun `hp11_lanes.py`. Save `rtr2-hp11.log`. Pass when it passes.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr2-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr2-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Router overhead in ms per request.
- [ ] Probe. 100 fake-upstream requests.
- [ ] Baseline. RTR0's relay.
- [ ] Rule. Fail when the median overhead exceeds 20 ms.

**Review gate.** None. RTR2 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR2 on RTR1.

## Add the in-house chat-completions lane (RTR3)

Rows AL-5. ADs AD-38 (the chat lane), AD-50. Change H12. Check P3's chat half. Gate none. Scenarios K-11. Done when a CLI request for a chat-completions row such as OpenCode Go is translated both ways, thinking round-trips through `reasoning_content` with translator-owned signatures, and `tool_use` ids map to `tool_calls` ids and back over a ten-turn loop.

**Depends on.** RTR2. P3's chat half runs as its first Build box. A row that fails stays off the chat lane (its named fallback).

**Files.**

- [ ] Create `R/chat_lane.py`, shaped like `R/gpt/translate.py`. Edit `R/relay.py` to route `wire: chat` rows to it.
- [ ] Create `qmx-agents/packages/qmx-router/tests/test_chat_lane.py` and `SP/router/p3_chat.py`.

**Build.**

- [ ] First, run P3's chat half on the OpenRouter rows that speak chat completions (provider proof), a ten-turn tool loop with thinking.
- [ ] Translate Anthropic Messages to chat completions and back, with the normaliser first. The translator owns thinking signatures, so a thinking block from another provider never reaches a chat-lane model.

**You see.**

- [ ] A sub-agent on an OpenCode Go row (or the OpenRouter row standing in) finishes a three-tool task under a Kimi main.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_chat_lane.py` asserts round trips of text, tool calls, tool results and thinking on recorded fixtures with literal bodies. Run `-n 2` in `qmx-router`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-router` suite with `-n 2` at the parent and at head. Save `rtr3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P3 chat half. Run `p3_chat.py`. Save `rtr3-p3.log`. Pass when each row reads PASS or FAIL after ten turns.
- [ ] Lane 3. The three-tool task from **You see.** Save `rtr3-task.log`. Pass when it ends with all three tool results used.
- [ ] Lane 4. A thinking sub-agent on the chat lane under a thinking Kimi main. Save `rtr3-thinking.log`. Pass when no foreign signature reaches either model.
- [ ] Lane 5. A mid-stream error from the fake chat upstream. Save `rtr3-error.log`. Pass when it is classified once and the parent continues.
- [ ] Lane 6. A sub-agent that needs vision on a text-only chat row. Save `rtr3-vision.log`. Pass when the router refuses it naming the capability.
- [ ] Lane 7. Tee the egress. Save `rtr3-egress.log`. Pass when no Anthropic-only field leaves.
- [ ] Lane 8. Rerun lane 3 of RTR2. Save `rtr3-e43.log`. Pass when it still passes.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr3-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr3-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Translation time in ms per streamed request.
- [ ] Probe. 100 fixture requests.
- [ ] Baseline. The GPT translator on the same sizes.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. RTR3 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR3 on RTR2.

## Build the account pool, the one error classifier and `complete` (RTR4)

Rows AL-3 (the pool), AL-4, L-63. ADs AD-12, AD-40 (the classifier), AD-56 (`complete`), AD-19 (`llm_complete`). Changes H3, H6 and H33 (one machine). Checks P7 and E8. Gate none. Scenarios 46 section 5.0 "Provider limit mid fan-out; mixed providers per sub-agent", K-16 and K-22. Done when accounts per provider rotate by his strategy with no QMX cap, a 429 cools one account and the next request takes another, a plan 401 benches an account only on the CLI's "needs `/login`" signal or three 401s in five minutes, every error is classified once, and `router.complete` serves key and GPT rows with a recorded-transport unit suite and one provider-proof lane.

**Depends on.** RTR3. P7 runs as this PR's first Build box.

**Files.**

- [ ] Create `R/pool.py`, `R/classify.py` and `R/complete.py`. Edit `R/relay.py` (leases and the classifier), `R/readings.py` (per-account readings) and `R/gpt/siwc.py` (several GPT sign-ins, one owner machine each).
- [ ] Add the pool rows and `llm_complete(role)` to `QX/catalog.py`. Edit the two example apps' `app.toml` so their raw `QMX_MODEL_KEY` gives way to `llm_complete(role)`.
- [ ] Create `qmx-agents/packages/qmx-router/tests/test_pool.py`, `test_classify.py` and `test_complete.py` with a recorded transport. Create `SP/router/p7_pool.py` and `SL/router/e08_pool.py`.

**Build.**

- [ ] Strategies are `fill_first`, `round_robin` and `least_used`, with `least_used` as Claude's default. Each account carries a priority, a share, ceilings and cooldowns he sets, all unset by default. His copilot account has `background_priority: last` (Claude's default).
- [ ] Affinity keys on `run_id:node_id`, so chunks hold one lease. Cooldowns are per `(account, model)`. A 429 with no or a past reset on a probing request is a generic 429, never straight back to `probing` (42 N13).
- [ ] The classifier maps every provider error once to `rate_limit`, `billing`, `auth`, `model_entitlement`, `content`, `transient` or `fatal`. A 402 cools an account one hour. One inbox item only when every allowed account for a role is closed past `alert_after`.
- [ ] `complete(role_or_model, messages, schema?, session?)` runs on the key and GPT lanes through the same normaliser, lease, classifier and journal. A plan row is refused with a message naming the one-turn chat.

**You see.**

- [ ] With two OpenRouter keys under one provider row (or two fake keys), a forced 429 on the first moves the next request to the second, and the readings show both.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_pool.py` asserts each strategy's pick order, affinity and cooldowns. `test_classify.py` maps recorded errors of each provider to literal classes. `test_complete.py` replays recorded responses. Run `-n 2` in `qmx-router`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-router` suite with `-n 2` at the parent and at head. Save `rtr4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P7. Run `p7_pool.py` with two fake Kimi keys and a 429 with `retry-after: 30` on key 1. Save `rtr4-p7.log`. Pass when key 1 cools 30 s, the next request takes key 2, it switches back after the cooldown, and the class is `rate_limit`.
- [ ] Lane 3. E8. Run `e08_pool.py` with eight fake chats across two accounts. Save `rtr4-e8.log`. Pass when leases spread by `least_used`, a 429 moves the next chat, and a running chat keeps its account.
- [ ] Lane 4. Provider-proof lane for `complete` (review 48 M8). Call `complete` on the OpenRouter DeepSeek row with a JSON schema. Save `rtr4-complete.log`. Pass when it returns valid JSON and journals one row.
- [ ] Lane 5. `complete` on a plan row. Save `rtr4-plan.log`. Pass when it is refused naming the one-turn chat.
- [ ] Lane 6. A 402 on a fake key. Save `rtr4-402.log`. Pass when the account cools one hour and the next takes over.
- [ ] Lane 7. Run an example app's `llm_complete(role)`. Save `rtr4-app.log`. Pass when it answers with no key in the app's environment.
- [ ] Lane 8. Three fake plan 401s in five minutes, then one CLI refresh race. Save `rtr4-401.log`. Pass when only the three 401s bench the account.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr4-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr4-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Lease time in ms with 50 accounts.
- [ ] Probe. 1,000 leases.
- [ ] Baseline. None, the pool is new.
- [ ] Rule. Fail when the median exceeds 5 ms, because every request takes a lease.

**Review gate.** None. The Accounts page is the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR4 on RTR3.

## Make the engine read the registry and call `complete` (RTR5)

Rows B-21, B-48, B-86, L-10, L-63. ADs AD-13, AD-34, AD-39, AD-9 (the pool lease), AD-56. Checks E9, E29 and E30. Gate none. Scenarios 46 section 5.0 "300-video playlist; Firecrawl pipeline" and K-11. Done when role lists are generated from the registry in `key, gpt, plan` order, chunks are sized from the resolved model's window, the compaction point comes from the row, admission takes a pool lease, and an `llm` node on a key or GPT row calls `complete` with no CLI process while a plan row keeps the one-turn chat.

**Depends on.** RTR4, CAPX (`E/admission.py`) and SURF (`E/nodes/agent.py`).

**Files.**

- [ ] Create `E/ports/router.py` (`RouterPort`). Edit `E/roles.py` (lists from the registry), `E/settings.py` (the generated defaults replace HYG0's literals), `E/core/partitions.py` (the window from the row), `E/nodes/agent.py` (the compaction point), `E/nodes/llm.py` (the `complete` path), `E/admission.py` (the pool lease) and `HO/host.py` (inject the router).
- [ ] Edit `ET/test_roles.py`, `test_partitions.py`, `test_llm.py` and `test_admission.py`. Edit `SL/engine/e09_roles.py`, `e03_chunks.py` and `x10_llm.py`.

**Build.**

- [ ] Until he edits a list, each role's candidates are generated from the providers he configured, by class, key rows first with the Chinese rows first, then GPT, then the plan (Claude's default, ruling 107). Test mode still resolves `claude/haiku` first.
- [ ] `chunk.fill` is 0.30 of the resolved model's window. The compaction point is 0.40 at 512k and above, 0.75 below. `chars_per_token` is 3 with 10 % headroom when a row has no `count_tokens` (Claude's defaults).
- [ ] A fallback to a smaller model re-plans the unstarted chunks for the new window. Finished chunk memos stand.

**You see.**

- [ ] A 50-abstract list into an agent node gives 2 chunks on a 1M model and 7 on a 200k model.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert the generated order for a registry fixture, the chunk counts of E29, the compaction points, and the `llm` executor picking `complete` for a key row and the chat for a plan row. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head. Save `rtr5-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E9. A node names `writer`, Settings lists Kimi first, then Kimi is disabled. Save `rtr5-e9.log`. Pass when the span records Kimi and then the second candidate.
- [ ] Lane 3. E29 on the fake provider. Save `rtr5-e29.log`. Pass when the chunk plans are 2 and 7 and a failed chunk 2 reruns alone.
- [ ] Lane 4. Provider-proof lane. An `llm` node on the OpenRouter DeepSeek row. Save `rtr5-complete.log`. Pass when no CLI process starts and the span carries the router journal id.
- [ ] Lane 5. E30 on the fake provider. Save `rtr5-e30.log`. Pass when chunks 2 to 7 hold chunk 1's lease and a forced rotation marks only that span `uncached_resend`.
- [ ] Lane 6. A plan-row `llm` node on haiku. Save `rtr5-plan.log`. Pass when it runs as a one-turn chat with no tools.
- [ ] Lane 7. A chunk falls back from a 1M to a 128k model. Save `rtr5-replan.log`. Pass when unstarted chunks re-plan and finished memos stand.
- [ ] Lane 8. Rerun `e21_real_tests.py`. Save `rtr5-e21.log`. Pass when it passes on haiku.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr5-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr5-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Peak RSS of a 20-call `llm` fan-out on a key row.
- [ ] Probe. 20 `llm` calls on the fake key row.
- [ ] Baseline. The same fan-out at the parent, one CLI per call.
- [ ] Rule. Fail when head's peak RSS is not below the parent's, because no CLI per call is the point.

**Review gate.** None. RTR5 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR5 on RTR4.

## Give every chat registry-generated sub-agents (RTR6)

Rows AL-6 (sub-agents). ADs AD-38, AD-4, AD-29. Change H38. Check P1k on the real router, plus E18. Gate P1k for key and GPT mains, and P1 for plan mains (PRB-R). Scenarios K-11 and 46 section 5.0 "Provider limit mid fan-out; mixed providers per sub-agent". Done when a Kimi or GPT main lists one sub-agent definition per role (plus one per model he pins), filtered by the lanes the chat can reach and regenerated on relaunch, its DeepSeek and Qwen sub-agents run through the router, and plan mains get third-party definitions only when P1 passed and the plan lane is on.

**Depends on.** RTR5 and PRB-R. If P1k failed, key and GPT mains reach third parties only through DLG, and this PR ships only the generator for Claude ids (its named fallback). If P1 failed, plan mains never get third-party definitions.

**Files.**

- [ ] Create `R/agents.py` (the generator). Edit `H/surface.py` (sub-agent definitions from the generator) and `H/launch.py` (`NewChat.agents` into the SDK options).
- [ ] Create `qmx-agents/packages/qmx-router/tests/test_agents.py` and `SL/router/rtr6_subagents.py`.

**Build.**

- [ ] Definitions are per role by default and per model only for models he pins, so the cache prefix stays stable (42 N21). Tools are inherited and never widened.
- [ ] A row with `plan_main_native: delegate_only` gets no native definition under a plan main.

**You see.**

- [ ] A Kimi-main chat on the OpenRouter row lists `deepseek-reviewer` and `qwen-reviewer`, and asking for both reviews runs both through the router.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_agents.py` asserts the definitions for three registry fixtures and lane states, and that a pinned model adds one. Run `-n 2` in `qmx-router` and `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-router` and `qma-harness` suites with `-n 2` at the parent and at head. Save `rtr6-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P1k on the real router with a Kimi main on the OpenRouter row. Save `rtr6-p1k.log`. Pass when both sub-agents spawn with model ids unchanged and return.
- [ ] Lane 3. E18. An agent node with `subagents.max_concurrent: 3` spawns 5 on the fake provider. Save `rtr6-e18.log`. Pass when 3 run at once, depth 1 holds, spans are children of the node, and a Kimi-named sub-agent routes to Kimi.
- [ ] Lane 4. A plan main on haiku. Save `rtr6-plan.log`. Pass when it lists third-party definitions only if P1 passed and the lane is on, else none.
- [ ] Lane 5. A GPT main, if his sign-in exists. Save `rtr6-gpt.log`. Pass when its sub-agents spawn or it reads `not run, no GPT sign-in`.
- [ ] Lane 6. Disable a provider and relaunch. Save `rtr6-regen.log`. Pass when its definition is gone.
- [ ] Lane 7. Two chats with the same roles. Save `rtr6-cache.log`. Pass when their definition lists are identical.
- [ ] Lane 8. A sub-agent naming an unknown id. Save `rtr6-unknown.log`. Pass when it fails and the parent continues.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr6-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr6-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Launch time in ms with 12 definitions.
- [ ] Probe. Five launches.
- [ ] Baseline. Launches with none.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The live dock is the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR6 on RTR5.

## Build the plan lane dark, prove it, then let him turn it on (RTR7)

Rows AL-6 (the plan lane). ADs AD-38, AD-50, AD-48 (the health check), AD-29. Change H27. Checks P4, P2 and the router half of E49. Gate P0 and P1 must both have passed in PRB-R. Scenarios K-11 and SOLUTION-DESIGN S1 (his Opus copilot with Kimi and Qwen reviewers). Done when a plan launch goes through the router only while `router.plan_lane` is on for that Claude account, bytes pass unchanged except the router's own grant header, the boot canary and the 5 s health check turn the lane off on failure, P4 and P2 pass against the dark build, and the operator has turned the lane on himself after reading the results.

**Depends on.** RTR6. If P0 or P1 failed, RTR7 is not built. Plan launches stay as built and his copilot's other-provider helpers run on DLG (its named fallback). The coordinator logs the skip and appends DLG on RTR6.

**Files.**

- [ ] Create `R/plan_lane.py`. Edit `R/relay.py` (the plan path for any method and path with raw headers), `R/server.py` (the canary at boot, the health check), `H/launch.py` (the plan launch env when the lane is on), `H/home.py` (one plan home per Claude account) and `QX/catalog.py` (the per-account switch, MANAGE).
- [ ] Create `qmx-agents/packages/qmx-router/tests/test_plan_lane.py`, `SP/router/p4_normaliser.py`, `SP/router/p2_billing.py` and `SL/router/e49_router.py`.

**Build.**

- [ ] Plan lane only for Claude ids on a grant minted for a plan home launch on the same host, loopback only. The body and every header pass unchanged except `x-qmx-grant`, which is removed. The router reads `model` and the streamed usage, logs no header value and keeps nothing past the hop. It never swaps a token between accounts.
- [ ] Every non-plan lane drops the incoming bearer and runs the egress stop, so a Claude token there fails closed.
- [ ] P1's echo form runs at every boot. A failure keeps the lane off with one `black` item. The health check turns the lane off within 5 s of a stall, and it returns after three healthy checks plus a canary.
- [ ] Build it dark with `router.plan_lane: off` on every account (Claude's default). Then run P4 per provider, then P2. A provider that fails P4 stays `plan_main_native: delegate_only`. A P2 fail means the lane does not ship, and the coordinator removes the switch from this PR.

**You see.**

- [ ] With the lane on for his account, his Opus copilot on the plan asks a Kimi reviewer and a Qwen reviewer, and the journal shows the plan requests and both reviewers in one session.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_plan_lane.py` asserts byte equality except the grant header, that a plan grant never reaches the key lane's bearer handling, and the canary's off switch. Run `-n 2` in `qmx-router` and `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-router` and `qma-harness` suites with `-n 2` at the parent and at head. Save `rtr7-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P4 against the dark lane, a haiku main under his `/login` with sub-agents on the OpenRouter rows. Save `rtr7-p4.log`. Pass when each provider reads PASS or FAIL per the P4 line.
- [ ] Lane 3. P2. Save `rtr7-p2.log`. Pass when it reads PASS or FAIL per the P2 line within 20 turns (a probe bound).
- [ ] Lane 4. E49 router half. Stall the router's loop with the lane on. Save `rtr7-e49.log`. Pass when within 10 s the lane is off and the plan chat continues with no base URL on the same session id.
- [ ] Lane 5. Fail the boot canary. Save `rtr7-canary.log`. Pass when the lane stays off with one `black` item.
- [ ] Lane 6. Leak check on every recording. Save `rtr7-leak.log`. Pass when no `sk-ant-`, `Bearer ` or grant value is found at any upstream.
- [ ] Lane 7. Turn the lane off mid-session. Save `rtr7-off.log`. Pass when new plan chats launch without a base URL and running ones keep their launch.
- [ ] Lane 8. Hash the ship home's `settings.toml` and list `~/.claude` before and after. Save `rtr7-home.log`. Pass when both are unchanged.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr7-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr7-processes.log`. Pass when no `claude`, `qma-cli-launcher` or router process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Added latency in ms per plan request through the lane.
- [ ] Probe. P2's turns.
- [ ] Baseline. PRB-R's P0 number with no base URL.
- [ ] Rule. Fail when the median added latency exceeds 50 ms.

**Review gate.** The lane changes his copilot's path, so he reviews before he turns it on.

- [ ] Write P4 and P2's results in plain words to `review/rtr7-plain.md`, with what turning the lane on changes for his plan window.
- [ ] Save a screenshot of the journal from **You see.** as `review/rtr7-journal.png`, and record a 30 to 60 second video of the S1 run with `ffmpeg -f gdigrab` as `review/rtr7.mp4`.
- [ ] Post the file, the screenshot and the video to the operator in chat. The lane stays off until he turns it on for his account himself.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR7 on RTR6.

## Rebuild `delegate` so helpers return a handle at once and report back between turns (DLG)

Rows AL-21. ADs AD-41, AD-16 (the stall monitor), AD-62 (a helper never wider than its parent), AD-64 (no permission union). Change H26. Checks P5 and E52. Gate none. Scenarios K-11, K-21 and SOLUTION-DESIGN S1 when native sub-agents are not available. Done when `delegate` returns a handle at once, helpers on any profile run in parallel, the parent can list, steer and stop them, each completion is stored before it is announced and delivered once between turns even across a restart, a stuck helper is stopped by the stuck rules, and a `cli` helper runs as a local process owned by its handle.

**Depends on.** RTR4 (one runtime resolver and leases) and SURF. Images to helpers wait for the multimodal layer (Appendix G).

**Files.**

- [ ] Create `H/delegate.py`. Edit `H/harness.py` (`_delegate` at line 425 rebuilt), `H/tools.py` (`delegate_def` at line 388 goes), `H/surface.py` (the helper's surface) and `QX/catalog.py` (the `delegate` toolset rows `delegate`, `delegate_list`, `delegate_steer`, `delegate_stop`).
- [ ] Edit `QX/service.py` and `QX/models.py` for the completions table in `control.db`.
- [ ] Edit `HT/test_delegate.py`. Create `SL/qma/p5_delegate.py` and `SL/qma/e52_cli.py`.

**Build.**

- [ ] `delegate(task, role? | model? | profile?, effort?, output_schema?, worktree?, group?)` resolves one child bundle (profile, lease, model, wire, effort, fallback chain) in one function and returns a handle at once. Children run in batches of 10 by default with no ceiling, and host capacity queues the rest (Claude's default).
- [ ] Completions are stored before announce and handed to the parent between its turns. A restart mid-run delivers each completion exactly once.
- [ ] The stall monitor uses the rules in `H/stuck.py`. `delegate` depth is 1 (Claude's default).
- [ ] A `cli` target is a local process owned by its handle that dies with it, its model calls go through the router on a grant, and the first spawn of each binary version asks in a copilot chat. Day-one targets are CLIs that take an Anthropic base URL from env. RTRP turns the grant into a run pass.

**You see.**

- [ ] His copilot on haiku starts three helpers on the OpenRouter Kimi, DeepSeek and Qwen rows, keeps talking to him, and receives three results between turns.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_delegate.py` asserts the handle at once, once-only delivery across a simulated restart, steer and stop, and a helper surface within its parent's. Run `-n 2` in `qma-harness` and `qmx-control`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` and `qmx-control` suites with `-n 2` at the parent and at head. Save `dlg-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P5. Run `p5_delegate.py`, a haiku copilot under the lane lock with three helpers on the OpenRouter rows (provider proof), and restart the host mid-run. Save `dlg-p5.log`. Pass when handles return at once, results arrive between turns, and each completion is delivered exactly once.
- [ ] Lane 3. E52. Run `e52_cli.py`. Save `dlg-e52.log`. Pass when it records which CLIs take a base URL from env, a `cli` helper dies with its handle, and its calls appear in the router journal under its grant.
- [ ] Lane 4. A looping helper on the fake model. Save `dlg-stall.log`. Pass when the stall monitor stops it and the parent continues.
- [ ] Lane 5. Steer a running helper, then stop another. Save `dlg-steer.log`. Pass when the steer reaches it and the stop ends it.
- [ ] Lane 6. A helper asks for a tool its parent lacks. Save `dlg-scope.log`. Pass when it is not offered.
- [ ] Lane 7. Fifteen helpers at once. Save `dlg-batch.log`. Pass when ten start and five queue with no refusal.
- [ ] Lane 8. A helper with `output_schema`. Save `dlg-schema.log`. Pass when its completion validates.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `dlg-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `dlg-processes.log`. Pass when no helper, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time in ms from `delegate` to the handle.
- [ ] Probe. Lane 2's three calls.
- [ ] Baseline. Today's blocking `delegate` at the parent.
- [ ] Rule. Fail when the median exceeds 1,000 ms, because a handle at once is the point.

**Review gate.** None. The live dock is the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DLG on RTR7, or on RTR6 when RTR7 was skipped.

## Give every template a plain name, let the intake take a playlist without asking, and ground numbers in evidence (TPL1)

Rows AL-14, B-79, B-84, B-88, B-91, L-76, L-77, L-81 to L-88, L-93. ADs AD-46, AD-45 (the evidence rule), AD-11. Checks E48 and E51. Gate none. Scenarios K-01, K-05 and 46 section 5.0 "300-video playlist; Firecrawl pipeline". Done when all 31 templates carry the plain titles of SOLUTION-DESIGN section 26.9, old ids resolve, template A expands a playlist fixture with no ask, a number found only in a model's intermediate output fails the grader, and all 31 pass a haiku test run.

**Depends on.** RTR5 (role defaults) and BUG2 (B-76 lets `SHARED_COPIES` go).

**Files.**

- [ ] Edit `T/catalog.py` (titles, aliases for old ids, `SHARED_COPIES` gone, `test_cost` strings), `T/install.py` (B-91), every template folder's `definition.json` and README, `T/a-fill-the-library/scripts/intake.py`, and the shared `render_and_grade` block under `T/_shared/`.
- [ ] Edit `docs/TEMPLATES.md`, `ET/test_templates.py` and `SL/engine/t_templates.py`. Create `SL/engine/e48_templates.py` and `SL/engine/e51_evidence.py`.

**Build.**

- [ ] Titles say plainly what each template does (ruling 35). The proposals of SOLUTION-DESIGN section 26.9 are Claude's default, and he may rename any of them. Old ids stay as aliases.
- [ ] Template A expands a playlist or a site into chunked items without asking.
- [ ] The grader builds an evidence set from pinned inputs, fetched and read artifacts and the results of declared scripts no model wrote. Output of model-written code, `llm` and `agent` outputs and the run's own prompt are never evidence. Timestamps, dates, run ids, hashes and version strings are removed from both sides.
- [ ] Each template passes one real test run on haiku before it is listed on the shelf (E32, E48).

**You see.**

- [ ] The template list shows 31 plain titles, and each reads `tested`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert old ids resolve, the evidence set on planted-number fixtures per E51, and one planted-number case per runnable template. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` and `ET/test_templates.py` at the parent and at head. Save `tpl1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E48. Run `e48_templates.py`, all 31 templates on haiku under the lane lock. Save `tpl1-e48.log`. Pass when all 31 pass and renamed ids resolve.
- [ ] Lane 3. E51. Run `e51_evidence.py`. Save `tpl1-e51.log`. Pass when the intermediate-only number fails, the fetched-source number passes, a timestamp year does not count, and a number printed by the agent's own code fails.
- [ ] Lane 4. Template A on a 20-video playlist fixture. Save `tpl1-intake.log`. Pass when it expands without an ask and chunks the list.
- [ ] Lane 5. Install a template by its old id. Save `tpl1-alias.log`. Pass when it installs the renamed one.
- [ ] Lane 6. Read the `test_cost` strings. Save `tpl1-cost.log`. Pass when they show cache tokens and no "0k in".
- [ ] Lane 7. Grep for `SHARED_COPIES`. Save `tpl1-grep.log`. Pass when it is gone.
- [ ] Lane 8. Count haiku turns for lane 2. Save `tpl1-turns.log`. Pass when the count is recorded for Appendix E.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `tpl1-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `tpl1-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Haiku turns and wall time for all 31 test runs.
- [ ] Probe. Lane 2.
- [ ] Baseline. The engine program's TP lanes.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** The template titles are what the operator sees on the shelf.

- [ ] Save a screenshot of the template list as `review/tpl1-titles.png`.
- [ ] Record a 30 to 60 second video of template A expanding the playlist fixture with `ffmpeg -f gdigrab` as `review/tpl1.mp4`.
- [ ] Post the screenshot, the video and the old-to-new title table to the operator in chat. Renames he asks for go to `BACKLOG.md` as one line each, and nothing waits on them.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends TPL1 on DLG.

## Let the copilot build, validate and test a workflow from one line (TPL2)

Rows AL-16. ADs AD-22, AD-11, AD-46. Check E42. Gate none. Scenarios 46 section 5.0 "Agentic vs non-agentic workflows" and K-01. Done when the builder is a real skill in the core plugin, and the copilot builds, validates and test-runs a three-node workflow from a one-line request with no ask, landing the draft on its agent ref, while publish returns a card for his click.

**Depends on.** TPL1.

**Files.**

- [ ] Create `CP/skills/build-workflow/SKILL.md` and its references. The old placeholder under `qmx_agents/skills/build-workflow/` goes in DEL1.
- [ ] Edit `CP/QMX.md` to point the copilot at the skill.
- [ ] Create `SL/qma/e42_builder.py`.

**Build.**

- [ ] The skill runs the loop-me interview (trigger, checkpoints pushed as late as possible, brief) inside BMad's six phases (discover intent, classify, gather requirements, draft, build with a lint gate, optimise), as AD-22 says.
- [ ] It writes drafts only through `service.drafts.put` onto its agent ref, then validates, then test-runs on cheap candidates. Publish returns a card.
- [ ] A workflow may be script-only, mixed or fully agentic (ruling 52), and a single agent is still a workflow (ruling 44).

**You see.**

- [ ] He types "every weekday at 7, pull the ECB calendar, summarise it, and save it to the Library", and a tested draft appears with a publish card.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A test parses the skill's frontmatter and asserts it names only catalog tools that exist. Run the `qma-harness` plugin tests with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` suite with `-n 2` at the parent and at head. Save `tpl2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E42. Run `e42_builder.py` on haiku under the lane lock with the one-line request. Save `tpl2-e42.log`. Pass when a three-node draft is built, validated and test-run with no ask and lands on the agent ref.
- [ ] Lane 3. Ask the copilot to publish it. Save `tpl2-publish.log`. Pass when a card returns and nothing is published.
- [ ] Lane 4. A script-only request. Save `tpl2-script.log`. Pass when the draft has no model node and the test run spends no tokens.
- [ ] Lane 5. A request that needs an unknown tool. Save `tpl2-unknown.log`. Pass when the builder says so instead of inventing one.
- [ ] Lane 6. Edit the built draft by one line. Save `tpl2-edit.log`. Pass when the edit lands on the same agent ref.
- [ ] Lane 7. Read the draft in the Library. Save `tpl2-library.log`. Pass when it is on `refs/drafts` or the agent ref, never `main`.
- [ ] Lane 8. Count haiku turns. Save `tpl2-turns.log`. Pass when the count is recorded.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `tpl2-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `tpl2-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Wall time from the request to a tested draft.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, the builder is new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** The builder is a new path in his copilot.

- [ ] Save a screenshot of the tested draft and its publish card as `review/tpl2-card.png`.
- [ ] Record a 30 to 60 second video of lane 2 with `ffmpeg -f gdigrab` as `review/tpl2.mp4`.
- [ ] Post the screenshot and the video to the operator in chat. The root appends TPL2 on its clean verdict, and changes he asks for go to `BACKLOG.md`.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends TPL2 on TPL1.

## Ship the revolution loop, the panel, clippings intake, the morning digest and the crystallise pattern (TPL3)

ADs AD-46, AD-26, AD-45, AD-5 (sanctioned nesting), AD-27. Checks a haiku test run of each new template plus the third full `just ci`. Gate P-NEST (PRB-L). Scenarios K-11, K-19, K-31 and K-32. Done when five new templates pass a test run, the panel shows its spread, clippings are deduped by hash and intent key, the digest reads "since last look" from one operator cursor row, and crystallise passes equivalence on 20 replays. Loop-to-server (K-18) waits for copilot loops (Appendix G).

**Depends on.** TPL2, EVAL and PRB-L. If P-NEST failed, add that one exception to the validator in this PR (its named fallback).

**Files.**

- [ ] Create `T/revolution-loop/`, `T/ask-the-panel/`, `T/clippings-into-research/`, `T/morning-digest/` and `T/crystallise-a-workflow/` (plain names, Claude's default). Edit `T/catalog.py`.
- [ ] Edit `QX/service.py` for the operator's "last look" cursor row. Edit `E/definition/validate.py` only if P-NEST failed.
- [ ] Create `SL/engine/tpl3_templates.py`.

**Build.**

- [ ] The revolution loop is a loop that calls a subworkflow holding its own loop (DC-11).
- [ ] The panel asks several model families the same question, shows the spread, marks an absent member, and labels a judge of the same family as a member.
- [ ] Clippings intake dedupes by content hash and intent key, so the same clipping twice runs once.
- [ ] The morning digest reads the Library ref log since his last look.
- [ ] Crystallise replaces an agent step with a script once 20 replays agree, and samples one item in N back to the agent.

**You see.**

- [ ] The five templates appear on the shelf with plain titles and read `tested`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] One planted-input case per template, and the cursor row's read and write. Run `-n 2` in `qmx-engine` and `qmx-control`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run `just ci` under the CI lock at head. Save `tpl3-ci.log`. Pass when it passes.
- [ ] Lane 2. Run the five templates on haiku under the lane lock. Save `tpl3-runs.log`. Pass when all five pass.
- [ ] Lane 3. Provider-proof lane. Run the panel with haiku and the OpenRouter DeepSeek and Kimi rows. Save `tpl3-panel.log`. Pass when the spread shows three members.
- [ ] Lane 4. Feed the same clipping twice. Save `tpl3-dedupe.log`. Pass when it runs once and the second links.
- [ ] Lane 5. Run crystallise on a fixture with 20 recorded replays. Save `tpl3-crystallise.log`. Pass when the equivalence check passes and sampling is set.
- [ ] Lane 6. Run the digest twice. Save `tpl3-digest.log`. Pass when the second shows only what landed since the first.
- [ ] Lane 7. Validate the revolution loop. Save `tpl3-nest.log`. Pass when it validates.
- [ ] Lane 8. Count haiku turns. Save `tpl3-turns.log`. Pass when the count is recorded.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `tpl3-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `tpl3-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Haiku turns per template.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, the templates are new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. TPL1's review covers how templates show. The coordinator lists the five new titles to the operator.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends TPL3 on TPL2.

## Point the QMB host at `qmx_host` (QMBH)

ADs AD-52, AD-59 (step 2's precondition). DELETION-PLAN D2 as review 48 L2 retargeted it. Check the QMB host lanes. Gate none. Scenarios K-01 and K-34 (QMB backtests keep starting). Done when `qmb host start`, `status` and `stop` run against `qmx_host`, and `git grep -n "qma.daemon" qmb/` prints nothing. Built in this program as Claude's default, because ruling 118 unlocks QMB. If he prefers the QMB session to own it, the coordinator hands this section over as its brief and DEL2 waits for that session.

**Depends on.** HOST.

**Files.**

- [ ] Edit `qmb/src/qmb/doors/cli/host.py`. Delete `DAEMON_SPAWN_MODULE` at line 104 and its export at 43, the daemon branches of `_spawn_argv` at 692 and 693, their callers near 938 and 1746, and the daemon-only `invoke_host_*` helpers. Change the spawn module at 1799 to `qmx_host`.
- [ ] Edit `qmb/tests/test_cli_host.py`, and delete or rewrite `qmb/tests/test_operator_study_cli.py`, which imports `qma.daemon` and `qma.core`.
- [ ] Edit the comment at root `pyproject.toml:341`.

**Build.**

- [ ] The spawn argv names `python -m qmx_host serve`. `recover-control` works through `qmx_host` or exits with a message naming the removed daemon path.
- [ ] QMB's backtest code does not change.

**You see.**

- [ ] `uv run qmb host start`, `status` and `stop` exit 0 and the running process is `qmx_host`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_cli_host.py` asserts the spawn argv names `qmx_host`. Run the `qmb` suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmb` suite with `-n 2` at the parent and at head. Save `qmbh-regression.log`. Pass when head fails nothing the parent passes except `test_operator_study_cli.py`, rewritten or deleted.
- [ ] Lane 2. Run `uv run qmb host start`, `status` and `stop` on a throwaway home. Save `qmbh-host.log`. Pass when each exits 0 and the process is `qmx_host`.
- [ ] Lane 3. Run `git grep -n "qma.daemon" qmb/`. Save `qmbh-grep.log`. Pass when it prints nothing.
- [ ] Lane 4. Run the QMB backtest suite at the parent and at head. Save `qmbh-backtest.log`. Pass when the pass and fail counts match.
- [ ] Lane 5. Call `GET /api/health` on the QMB-started host. Save `qmbh-health.log`. Pass when it answers.
- [ ] Lane 6. Run `uv run qmb host recover-control`. Save `qmbh-recover.log`. Pass when it works or names the removed daemon path.
- [ ] Lane 7. Read `qmb/src/qmb/analysis/variants.py:66`. Save `qmbh-schema.log`. Pass when the `qma.wire.money_path_field_diff.v1` name is a plain string.
- [ ] Lane 8. Read `status` while the host runs. Save `qmbh-status.log`. Pass when it names the PID and the port.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `qmbh-secrets.log`. Pass when it is clean.
- [ ] Lane 10. Stop the host and list processes. Save `qmbh-processes.log`. Pass when no `qmx_host`, `claude` or `qma-cli-launcher` process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time from `qmb host start` to the first 200 on `/api/health`.
- [ ] Probe. Five starts at the parent and five at head, interleaved.
- [ ] Baseline. The parent's median.
- [ ] Rule. Fail when head's median exceeds the parent's by more than 1 s.

**Review gate.** QMB is his tool, so he reviews before the root appends.

- [ ] Save a screenshot of lane 2's output as `review/qmbh-host.png`.
- [ ] Record a 30 to 60 second video of `qmb host start`, `status` and `stop` with `ffmpeg -f gdigrab` as `review/qmbh.mp4`.
- [ ] Post the screenshot, the video and the `qmb/` diff to the operator in chat and in `QUESTIONS-FOR-OPERATOR.md`. While his review is pending, build the next unblocked PR (prompt rule 18); never idle on it.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends QMBH on TPL3.

## Delete `qma-daemon` and the old host entry points (DEL2)

ADs AD-59 (step 2), AD-52 (the forwarders go). Check E59's daemon scan. Gate none. Scenarios 46 section 5.0 "Agentic vs non-agentic workflows" (one runtime serves every workflow). Done when `git grep -n -E "qma\.daemon|qma-daemon" -- . ':!*.md' ':!archive/**'` prints nothing, the three forwarders and RTR0's shims are gone, the caller scan is attached to the PR, and `qmx_host` still starts.

**Depends on.** QMBH and RUN1a. The replacement, `qmx_host`, passed E54 in HOST.

**Files.**

- [ ] Delete `qmx-agents/packages/qma-daemon/`, `qmx-agents/examples/native_*`, `qa/integration/test_qma_authenticated_study.py` and `qa/integration/test_qma_registered_replay.py`.
- [ ] Delete the forwarders in `qmx-agents/packages/qma-harness/src/qma/serve.py` (the `serve` path), `QX/__main__.py` (`serve`) and `E/host.py`, and RTR0's import shims, once the caller scan shows no caller.
- [ ] Edit `qmx-agents/pyproject.toml` (members, the `qma-runtime` extra, pytest `pythonpath`, pyright paths, poe coverage targets), root `pyproject.toml:228-230` and `:360-362`, and both `uv.lock` files.
- [ ] Edit `tools/nested_coverage_report.py`, `tools/release_gate.py`, `tools/build_release.py`, `tools/backend-source-provenance.py`, `tools/secret_scan.py:65`, `tools/tests/test_release_install.py` and `tools/tests/test_runtime_wheel_closure.py`.

**Build.**

- [ ] Before any deletion, run `git grep -n -E "qma\.daemon|qma-daemon|qma\.serve|qmx_engine\.host" -- . ':!*.md' ':!archive/**' ':!**/uv.lock'` and attach the output to the PR body.
- [ ] Commit in this order. The callers, then the forwarders and shims, then the package and its config edits.
- [ ] The 34 docs pages that describe the daemon are a documentation row (DOC-CHANGES row 44), not part of this PR.

**You see.**

- [ ] The scan prints nothing, and `python -m qmx_host serve` starts.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `tools/tests` and every remaining `qmx-agents` package suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run every remaining package suite with `-n 2` at head and the same suites at the parent. Save `del2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E59 daemon scan. Run the scan from **Build.** Save `del2-scan.log`. Pass when it prints nothing.
- [ ] Lane 3. Run `uv lock --check` at the root and in `qmx-agents/`. Save `del2-lock.log`. Pass when both pass.
- [ ] Lane 4. Start `qmx_host`, run one haiku chat turn and one workflow on the fake provider. Save `del2-host.log`. Pass when both work.
- [ ] Lane 5. Run `uv run qmb host start`, `status` and `stop`. Save `del2-qmb.log`. Pass when each exits 0.
- [ ] Lane 6. Run `python -c "import qma.daemon"`. Save `del2-import.log`. Pass when it fails with `ModuleNotFoundError`.
- [ ] Lane 7. Run `tools/build_release.py`. Save `del2-release.log`. Pass when the wheels build.
- [ ] Lane 8. Count deleted lines with `git diff --shortstat`. Save `del2-lines.log`. Pass when the count is recorded.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `del2-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `del2-processes.log`. Pass when no `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `uv sync --frozen --all-packages --all-groups` in `qmx-agents/` with an empty cache on `D:`.
- [ ] Probe. Two cold syncs at the parent and two at head, interleaved.
- [ ] Baseline. The parent's mean.
- [ ] Rule. Fail when head's mean is slower than the parent's.

**Review gate.** None. DEL2 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DEL2 on QMBH.

## Delete `qma-core` and `qma-wire` (DEL3)

ADs AD-59 (step 3), AD-54. Review 48 L1's callers. Check E59's core scan plus the fourth full `just ci`. Gate none. Scenarios 46 section 5.0 "Agentic vs non-agentic workflows". Done when no file outside the deletion set imports `qma.core` or `qma.wire`, the apps supervisor checks manifests instead of descriptors, QMN's example and two path lists are fixed, the two QML tests that would pass vacuously are repointed or deleted, and `just ci` passes.

**Depends on.** GUARD (the harness import is gone, the word list is vendored) and DEL2.

**Files.**

- [ ] Delete `qmx-agents/packages/qma-core/` and `qmx-agents/packages/qma-wire/`, `qmx-agents/tests/test_workspace_scaffold.py`, `qmx-agents/examples/scoped_tool_request.py`, `qmx-agents/examples/scaffold_overview.py`, `qmx-agents/plugins/` (the five daemon packs), `scripts/probes/qma/name_barrier_diff.py` and `scripts/dev/qma_callers.py`.
- [ ] Edit `AP/supervisor.py` (line 29, `check_descriptor` becomes a manifest check).
- [ ] Delete `qmn/examples/spot_paper_journey.py`, and edit `qmn/tests/test_qmn_fx_paper.py` (lines 682 to 684) and `qmn/tests/test_qmn_paper_trinity.py` so their path lists drop the three folders.
- [ ] Repoint or delete `qml/tests/test_generation_gaps_unfilled.py:62` and `qml/tests/test_generation_ownership.py:274`.
- [ ] Edit `qmx-agents/pyproject.toml`, root `pyproject.toml`, both `uv.lock` files, `tools/ci.py` and any tool the caller scan names.

**Build.**

- [ ] Before any deletion, run `git grep -n -E "qma\.core|qma\.wire|qma-core|qma-wire" -- . ':!*.md' ':!archive/**' ':!**/uv.lock'` and attach the output to the PR body. Every hit is in the deletion set or edited here.
- [ ] QMB keeps `qma.wire.money_path_field_diff.v1` as a plain string.
- [ ] The QMN and QML edits are listed in the PR body for those sessions (Claude's default under ruling 118, as in QMBH).

**You see.**

- [ ] The scan prints nothing, and `just ci` passes.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run the `qmn`, `qml`, `qmb` and `qmx-apps` suites with `-n 2`, then `just ci` in lane 1.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run `just ci` under the CI lock at head. Save `del3-ci.log`. Pass when it passes.
- [ ] Lane 2. E59 core scan. Run the scan from **Build.** Save `del3-scan.log`. Pass when it prints nothing.
- [ ] Lane 3. Install and start a fixture app through the supervisor. Save `del3-app.log`. Pass when the manifest check accepts it and a broken manifest is refused.
- [ ] Lane 4. Run the two repointed QML tests with a planted gap. Save `del3-qml.log`. Pass when each fails on the planted gap.
- [ ] Lane 5. Run `uv lock --check` at the root and in `qmx-agents/`. Save `del3-lock.log`. Pass when both pass.
- [ ] Lane 6. Run the `qmn` suite. Save `del3-qmn.log`. Pass when it passes.
- [ ] Lane 7. Run E56 again. Save `del3-guard.log`. Pass when the guard still refuses and allows as in GUARD.
- [ ] Lane 8. Count deleted lines. Save `del3-lines.log`. Pass when the count is recorded.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `del3-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `del3-processes.log`. Pass when no app, `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `just ci`.
- [ ] Probe. Lane 1.
- [ ] Baseline. SURF's `just ci` time.
- [ ] Rule. No fail rule. The saving is recorded for the operator.

**Review gate.** None. DEL3 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DEL3 on DEL2.

## Settle the heartbeat and memory numbers on his server (PRB-S)

ADs AD-65, AD-18, AD-30. Probes P-OPS (Contabo half) and P-MEM (Contabo half), exactly as SOLUTION-DESIGN section 28.8 writes them. Gate SRV, his server step. Scenarios K-03 and K-15. Done when `SP/server/FINDINGS.md` holds a PASS or FAIL row with its number for each probe and the fallback it triggers, and Contabo's `overhead_mb` figure counts Hindsight.

**Depends on.** None in code. It needs his server reachable over Tailscale (Override 7 until then). It shares no file with any PR.

**Files.**

- [ ] Create `SP/server/common.py`, `test_probes.py`, `p_ops.py`, `p_mem.py` and `FINDINGS.md`. Reuse `SP/library/p_ops.py` and `p_mem.py` by path.

**Build.**

- [ ] `p_ops.py` writes synthetic heartbeat rows for 20 agents at a 30 s interval on Contabo for 30 minutes. Pass is a row of at most 4 KB and at most 1 % of one core. Fail means idle hosts send deltas at a longer interval in OPS2.
- [ ] `p_mem.py` runs Hindsight with its embedding model on Contabo against the same rows as PRB-L. Pass is at most 2,048 MB RSS with the PC's quality numbers held. Fail on RAM means Hindsight stays on the PC and server runs recall through FTS5 over the same rows until the server grows.
- [ ] Record Contabo's free RAM with Hindsight running, and write the `overhead_mb` that leaves 2 agent sessions with Hindsight and 4 without (review 48 M11).

**You see.**

- [ ] `FINDINGS.md` has both rows with numbers and the derived `overhead_mb`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_probes.py` checks each verdict function on recorded fixtures. Run `uv run --no-sync python -m pytest scripts/probes/server -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run `git diff --stat <parent> HEAD`. Save `prb-s-regression.log`. Pass when only `SP/server/` changed.
- [ ] Lane 2. Run `p_ops.py` on Contabo. Save `prb-s-ops.log`. Pass when it ends in PASS or FAIL with row size and CPU share.
- [ ] Lane 3. Run `p_mem.py` on Contabo. Save `prb-s-mem.log`. Pass when it ends in PASS or FAIL with RSS.
- [ ] Lane 4. Record free RAM with and without Hindsight. Save `prb-s-ram.log`. Pass when both numbers and the derived `overhead_mb` are recorded.
- [ ] Lane 5. Run `p_ops.py` again. Save `prb-s-ops-repeat.log`. Pass when its CPU share is within 20 % of lane 2's.
- [ ] Lane 6. List what the probes left on Contabo. Save `prb-s-leftovers.log`. Pass when only `/srv/qmx/check/prb-s` remains, then is removed.
- [ ] Lane 7. Grep the probe logs for key-shaped strings. Save `prb-s-leak.log`. Pass when none is found.
- [ ] Lane 8. Record Contabo's disk use for the Hindsight index. Save `prb-s-disk.log`. Pass when it is recorded.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `prb-s-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes on Contabo after the lanes. Save `prb-s-processes.log`. Pass when no probe or Hindsight process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. The probe numbers themselves.
- [ ] Probe. Lanes 2 and 3.
- [ ] Baseline. The pass lines of SOLUTION-DESIGN section 28.8.
- [ ] Rule. Each probe's own pass line decides its row.

**Review gate.** None. The coordinator reports the result to the operator in plain words.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends PRB-S at the stack tip when his server step is done (Override 7).

## Put the Library Hub on his server, hold claims there, and make the server primary at setup (LIB4)

ADs Lib AD-10, AD-11, AD-14, AD-16, AD-19, AD-24, AD-6 (`purge`); engine AD-27, AD-30. MIGRATION steps 7 and 8, with step 4's bucket run folders. Checks E67 and the purge drill, with P-LAT measured. Gate SRV. Scenarios K-13, K-14, K-27 and K-33. Done when `qmx_hub` on Contabo serves the `LibraryPort` over the tailnet as the server store's one writer, the PC pushes and pulls by parent hashes, claims are compare-and-swap refs on the Hub, `qmx node setup` makes the server primary unconditionally, an operator purge tombstones a secret on every copy, and Hindsight moves to the server if PRB-S passed.

**Depends on.** LIB3 and PRB-S, and his server step. P-LAT is measured here and gates nothing (review 48 H5).

**Files.**

- [ ] Create the package `qmx-agents/packages/qmx-hub/` with `HB/server.py`, `HB/replicate.py`, `HB/claims.py` and `HB/purge.py`, plus its tests.
- [ ] Create `LB/client.py` (the Hub client). Edit `LB/port.py` (`claim`, `release` and `purge`) and `LB/store.py` (replica and cache roles).
- [ ] Edit `QX/node.py` and `QX/node-bootstrap.sh` so `qmx node setup` installs the Hub, Hindsight (when PRB-S passed) and the node service, imports the bucket's run folders, and flips `[library] primary = server`.
- [ ] Create `LB/migrate/from_bucket.py`, `SL/server/e67_claims.py`, `SL/server/p_lat.py` and `SL/server/purge_drill.py`. Edit `qmx-agents/pyproject.toml` and `tools/ci.py`.

**Build.**

- [ ] The Hub owns `refs/runs/<run_id>` for runs it minted and the workflow memory and champion refs. Once primary, it also owns `main`, `refs/drafts/*` and the other primary refs.
- [ ] The PC pulls refs and missing objects on wake and pushes its own, ordered by parent hashes, never by wall clock.
- [ ] `claim(intent_key, run_id, ttl)` is a compare-and-swap on `refs/claims/<intent_key>` of the Hub, renewed in batches. A host that cannot reach the Hub claims locally and accepts a rare duplicate deduped by the key.
- [ ] `purge(blob_id, reason)` is operator only and secrets only. It is the one exception to archive-never-delete.
- [ ] The flip runs MIGRATION step 8 at setup, on his command after he lands the stack. Lanes run it only on throwaway homes.

**You see.**

- [ ] On a throwaway PC home paired with Contabo, a save lands on the Hub and mirrors back, and the doctor shows `primary: server`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert replication order by parents, claim compare-and-swap with expiry, purge tombstones, and the primary owner table read from the setting. Run `-n 2` in `qmx-hub` and `qmx-library`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-library` and `qmx-control` suites with `-n 2` at the parent and at head. Save `lib4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E67. Run `e67_claims.py` with one run on the PC and one on Contabo starting the same build within a second. Save `lib4-e67.log`. Pass when one builds and the other waits and links, and killing the first lets the second take the claim after one `ttl`.
- [ ] Lane 3. Run `qmx node setup` against a throwaway pair and save from the PC. Save `lib4-setup.log`. Pass when the save lands on the Hub, mirrors back, and the doctor reads `primary: server`.
- [ ] Lane 4. Purge drill. Run `purge_drill.py` with a planted secret. Save `lib4-purge.log`. Pass when the blob is tombstoned on the PC, the Hub and the bucket.
- [ ] Lane 5. P-LAT. Run `p_lat.py`. Save `lib4-plat.log`. Pass when read and write p95 are recorded against 300 ms and 1,500 ms. A miss is a latency bug for `BACKLOG.md`, not a block.
- [ ] Lane 6. Put the PC to sleep (stop its host) while Contabo writes, then wake it. Save `lib4-offline.log`. Pass when the PC pulls every new object.
- [ ] Lane 7. Import the bucket's run folders on the pair. Save `lib4-bucket.log`. Pass when each folder becomes one `workflow-run` with its artifacts.
- [ ] Lane 8. Recall from a server run with Hindsight on Contabo, or FTS5 if PRB-S failed on RAM. Save `lib4-memory.log`. Pass when it answers.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `lib4-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes on both machines after the lanes. Save `lib4-processes.log`. Pass when no check process is left and `/srv/qmx/check/lib4` is removed.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Library read and write p95 in ms over the tailnet.
- [ ] Probe. Lane 5.
- [ ] Baseline. LIB1's local numbers.
- [ ] Rule. No fail rule (review 48 H5). A miss goes to `BACKLOG.md`.

**Review gate.** None. The coordinator tells the operator in plain words that the flip runs when he does the Contabo setup after landing.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends LIB4 on PRB-S.

## Serve credentials once everywhere, with run passes and the router on the tailnet (RTRP)

ADs AD-28, AD-12 (two hosts), AD-38 (the central router), AD-41 (`cli` helpers on passes). Changes H11, H13 and H33 (owner machines). Checks E25, E26 and E53. Gate SRV. Scenarios 46 section 5.0 "Credentials on a new machine; provider onboarding", K-14 and K-21. Done when keys entered once on the PC replicate encrypted to `qmx-vault` on Contabo, every remote attempt gets a run pass scoped to its run, branch, models and placement that expires with its owner, Contabo's router is the central router other placements reach over the tailnet, `qmx node login` gives Contabo its own plan home, and the two pools share cooldowns within one sync.

**Depends on.** RTR4 and his server step.

**Files.**

- [ ] Create `R/vault.py`, `R/passes.py` and `R/facts.py`. Edit `R/server.py` (the tailnet bind for the `node` role, pass bearers), `R/pool.py` (fact exchange, GPT owner machines) and `R/gpt/siwc.py`.
- [ ] Edit `QX/node.py` (`qmx node login`, vault install), `HO/host.py` (the `node` role) and `H/delegate.py` (a `cli` helper's grant becomes a pass naming its handle).
- [ ] Create `qmx-agents/packages/qmx-router/tests/test_passes.py` and `test_facts.py`. Create `SL/server/e25_passes.py`, `e26_vault.py` and `e53_two_hosts.py`.

**Build.**

- [ ] Keys live in Windows Credential Manager as `qmx/*`, as today. Replicable entries are encrypted under the vault's public key and pushed as ciphertext. Broker credentials are never replicable.
- [ ] A pass carries run, attempt, placement, read scope, write prefix, `key_scope` and `model_scope`, and expires when its owner ends. Revocation is a list the routers read.
- [ ] The pools exchange `(account, model, state, until, reading, observed_at)` over the tailnet on every change, and the newest fact wins. A key's concurrency is shared by live leases. Each GPT account has one owner machine, and a second machine's sign-in of it is refused.
- [ ] Contabo's router has a plan lane only for Contabo's own plan homes, signed in there by him. Plan bytes never cross the tailnet.

**You see.**

- [ ] A key rotated in Settings on the PC is used by the next relayed request on Contabo within one sync.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_passes.py` asserts every refusal of E25 on fixtures. `test_facts.py` asserts newest-fact-wins and the shared concurrency. Run `-n 2` in `qmx-router`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-router` and `qma-harness` suites with `-n 2` at the parent and at head. Save `rtrp-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E25. Run `e25_passes.py` across the pair. Save `rtrp-e25.log`. Pass when every misuse is refused and a pass whose owner ended is expired.
- [ ] Lane 3. E26. Run `e26_vault.py`. Save `rtrp-e26.log`. Pass when a rotation reaches Contabo within one sync, a deletion is refused within one sync, and with the vault and Hub stopped in-flight runs keep calling on cached keys.
- [ ] Lane 4. E53. Run `e53_two_hosts.py`. Save `rtrp-e53.log`. Pass when a 429 cooldown on the PC applies on Contabo within one sync and a second GPT sign-in is refused or reads `not run, no GPT sign-in`.
- [ ] Lane 5. A `cli` helper on Contabo. Save `rtrp-cli.log`. Pass when its pass names its handle and its calls journal under it.
- [ ] Lane 6. Grep Contabo's environment and disk for plaintext keys. Save `rtrp-plain.log`. Pass when none is found.
- [ ] Lane 7. A plan request routed to Contabo's router from the PC. Save `rtrp-plan.log`. Pass when it is refused.
- [ ] Lane 8. `qmx node login` on Contabo, if he did the server sign-in. Save `rtrp-login.log`. Pass when a haiku turn runs on Contabo's plan home or it reads `not run, no server sign-in`.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtrp-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes on both machines after the lanes. Save `rtrp-processes.log`. Pass when no check process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Pass verify time in ms, and the fact sync delay in seconds.
- [ ] Probe. 1,000 verifies, and lane 4's sync.
- [ ] Baseline. None, both are new.
- [ ] Rule. Fail when a verify exceeds 5 ms at the median, because every remote request carries one.

**Review gate.** None. The Settings key pages are the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RTRP on LIB4.

## Run workflow steps on his server through the remote worker and its sidecar (REM)

ADs AD-20, AD-25, AD-30, AD-57 (the replacement), Lib AD-12, AD-13. Change H8 (the sandbox tool server). Checks E57 on Contabo, E13 and E27. Gate SRV. Scenarios K-14, K-23 and 46 section 5.0 "Remote workflows reach the Library". Done when a `script` or `agent` node with `runs_on: contabo` runs there through `WorkerPort`, the sidecar ships heartbeats, logs and checkpoints to the Hub and redacts the pass, outputs return by hash, a one-node CPU job lands as a `workflow-run`, and Contabo's sessions derive from its RAM.

**Depends on.** RTRP and LIB4. E57's GPU case waits for a paid GPU placement and records `not run, no paid GPU placement`.

**Files.**

- [ ] Create `E/workers/remote.py` (the remote `WorkerPort` adapter on `RM/providers.py`) and `RM/sidecar.py`. Keep `RM/code.py` for remote build attempts.
- [ ] Edit `E/settings.py` (the `contabo` placement row with `ram_budget_mb` and `overhead_mb` from PRB-S), `E/triggers/preflight.py` (placement states), `HO/host.py` (the `node` role runs remote attempts) and `H/launch.py` (the sandbox tool server through `mcp_servers` for `runner_outside`).
- [ ] Create the template `T/run-on-a-machine/` (a one-node workflow for a placed job). Create `ET/test_remote_worker.py`, `SL/server/e57_remote.py`, `e13_remote.py` and `e27_placement.py`.

**Build.**

- [ ] A remote attempt receives a run pass, never a key. Its model calls go through Contabo's router.
- [ ] The sidecar heartbeats to the Hub, ships JSONL logs and traces to `runs/<run_id>/`, flushes checkpoints every 5 s and at every node boundary, and redacts the pass and every declared secret.
- [ ] A machine lost mid-attempt folds `unknown` after the heartbeat stops and retries by effect class (AD-8).
- [ ] Nothing remote is deleted here. RUN1b deletes the old path after this PR passes E57.

**You see.**

- [ ] A one-node CPU job on `contabo` lands as a `workflow-run` the PC's run list shows.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_remote_worker.py` asserts the job and result shapes over a fake provider, the `unknown` fold on a lost heartbeat, and that no key enters the job. Run `-n 2` in `qmx-engine` and `qmx-remote`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` and `qmx-remote` suites with `-n 2` at the parent and at head. Save `rem-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E57 on Contabo. Run `e57_remote.py` with a one-node CPU job. Save `rem-e57.log`. Pass when it lands as a `workflow-run` with its outputs by hash. The GPU case reads `not run, no paid GPU placement`.
- [ ] Lane 3. E13. Run `e13_remote.py`. Save `rem-e13.log`. Pass when outputs return by hash and events land in the home ledger.
- [ ] Lane 4. E27. Run `e27_placement.py` with six agent nodes on `contabo`. Save `rem-e27.log`. Pass when the derived sessions run and the rest wait `placement`, and a plan account asked on a provider VM is refused at preflight.
- [ ] Lane 5. Cut Contabo's network mid-attempt. Save `rem-lost.log`. Pass when the attempt folds `unknown` and retries by effect class.
- [ ] Lane 6. Grep the sidecar logs for the pass. Save `rem-redact.log`. Pass when it is redacted.
- [ ] Lane 7. A remote build attempt through `code.py`. Save `rem-code.log`. Pass when it pushes only its one refspec.
- [ ] Lane 8. An agent node on Contabo on a key row. Save `rem-agent.log`. Pass when it ends `passed` through Contabo's router.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rem-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes on both machines after the lanes. Save `rem-processes.log`. Pass when no check, sidecar or `claude` process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Dispatch-to-start delay in seconds for a remote attempt.
- [ ] Probe. Lane 2, five jobs.
- [ ] Baseline. A local attempt.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The Machines view is the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id, with E57's Contabo result named, because RUN1b reads it.
- [ ] The root appends REM on RTRP.

## Fire event triggers from the Library ref log across machines (TRG2b)

ADs AD-64, AD-10, Lib AD-11, AD-14. Check E63. Gate SRV, and P-EV run as this PR's first Build box. Scenarios K-09 and K-17. Done when an `event` trigger keeps a cursor into the Library ref log, fires on new rows matching kind, output name and producer, dedupes per trigger and object, honours `coalesce`, and a Contabo app's landing fires the next Contabo app with the PC asleep.

**Depends on.** LIB4, APP2a and TRG2a. If P-EV failed, the Hub pushes ref-log rows on the engine event stream instead of the tick reading them (its named fallback).

**Files.**

- [ ] Create `E/triggers/event.py` and `SP/server/p_ev.py`. Edit `E/triggers/ticker.py` and `HB/server.py` (a ref-log read, and the push stream only for the fallback).
- [ ] Create `ET/test_event_trigger.py` and `SL/server/e63_chain.py`.

**Build.**

- [ ] First, run P-EV. Pass is a fire within two ticks (120 s at the default 60 s tick) of the object reaching the Hub and a claim round trip under 1 s at p95. The result sets `scheduler.tick` for event triggers.
- [ ] `coalesce: latest` drops a queued fire that a newer object superseded. The default is `each` (Claude's default from AD-64).

**You see.**

- [ ] With the PC's host stopped, the macro fixture app on Contabo lands `bias`, and the signal fixture app on Contabo runs on it.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert matching, the cursor, dedupe of a re-delivery and `coalesce: latest`. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head. Save `trg2b-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-EV. Run `p_ev.py`. Save `trg2b-pev.log`. Pass when it ends in PASS or FAIL with both numbers.
- [ ] Lane 3. E63 with the PC asleep. Run `e63_chain.py`. Save `trg2b-e63.log`. Pass when the chain completes on Contabo.
- [ ] Lane 4. A PC landing fires a Contabo trigger. Save `trg2b-cross.log`. Pass when it fires once within one tick after replication.
- [ ] Lane 5. Two re-deliveries of one object. Save `trg2b-dedupe.log`. Pass when nothing extra fires.
- [ ] Lane 6. Three landings while a fire is queued with `coalesce: latest`. Save `trg2b-coalesce.log`. Pass when one fire runs on the newest.
- [ ] Lane 7. Restart the engine mid-cursor. Save `trg2b-cursor.log`. Pass when no row is skipped or fired twice.
- [ ] Lane 8. A self-feeding app. Save `trg2b-ring.log`. Pass when the intent key ends the loop.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `trg2b-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes on both machines after the lanes. Save `trg2b-processes.log`. Pass when no check or app process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from an object reaching the Hub to the fire.
- [ ] Probe. Lane 4, ten landings.
- [ ] Baseline. P-EV's number.
- [ ] Rule. Fail when the p95 exceeds two ticks, P-EV's pass line.

**Review gate.** None. TRG2b changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends TRG2b on REM.

## Give each app instance one home and move it between machines (APP2b)

ADs AD-64 (homes and state), AD-19, Lib AD-3 (`mini-app-instance`). Check the P-APP path. Gate SRV, and P-APP run as this PR's first Build box. Scenarios K-09, K-10 and K-21. Done when every app instance has one home, a `state: none` operation starts the app lazily on the caller's machine from the pinned bundle fetched by hash, a `state: instance` operation routes to the home and waits `placement` when it is away, and moving an instance is a snapshot, a restore elsewhere and a flip of `home` with the volume lease handed over.

**Depends on.** APP2a and REM. If P-APP failed, stateful operations stay on their PC home, remote callers wait `placement`, and no lazy remote start ships (Claude's default fallback, since SOLUTION-DESIGN names none).

**Files.**

- [ ] Create `AP/bundle.py` (fetch by hash, lazy start) and `SP/server/p_app.py`. Edit `AP/supervisor.py`, `AP/volume.py` (the lease handover), `E/nodes/app_op.py` (routing by `state`) and `QX/catalog.py` (the move operation, MANAGE).
- [ ] Create the matching tests and `SL/server/app2b_lanes.py`.

**Build.**

- [ ] First, run P-APP. Pass is an app server started on Contabo from a Library bundle by hash, and a lease handed from the PC to Contabo with a snapshot and restore.
- [ ] Reading another app's latest output never needs a call. It is a Library read that works offline and remotely.

**You see.**

- [ ] The macro fixture app moves from the PC to Contabo, and its next scheduled run happens there with its state intact.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert routing by `state`, the `placement` wait, and the snapshot and restore round trip. Run `-n 2` in `qmx-apps` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-apps` and `qmx-engine` suites with `-n 2` at the parent and at head. Save `app2b-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-APP. Run `p_app.py`. Save `app2b-papp.log`. Pass when it ends in PASS or FAIL per its line.
- [ ] Lane 3. Move the fixture instance to Contabo. Save `app2b-move.log`. Pass when state survives and the next run happens there.
- [ ] Lane 4. Call a `state: instance` operation with the home unreachable. Save `app2b-away.log`. Pass when the node waits `placement` and resumes when the home returns.
- [ ] Lane 5. Call a `state: none` operation from Contabo. Save `app2b-lazy.log`. Pass when the app starts there from the bundle by hash.
- [ ] Lane 6. Read the app's latest output offline. Save `app2b-read.log`. Pass when the Library answers.
- [ ] Lane 7. Two machines try to hold one lease. Save `app2b-lease.log`. Pass when the second is refused.
- [ ] Lane 8. A profile moves with its instance. Save `app2b-profile.log`. Pass when its partition is intact.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `app2b-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes on both machines after the lanes. Save `app2b-processes.log`. Pass when no app or check process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Move time in seconds for a 100 MB volume.
- [ ] Probe. Lane 3.
- [ ] Baseline. None, moves are new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. App screens are the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends APP2b on TRG2b.

## See and answer server runs on the PC, with one pause switch everywhere (OPS2)

ADs AD-65 (remote homes, the Hub reply), AD-21, AD-10, AD-30 (draining). Checks E68 and E64. Gate SRV, and the Contabo half of P-OPS (PRB-S). Scenarios K-15, K-22, K-24 and K-28. Done when every host and sidecar pushes its heartbeat to the Hub, the Hub's reply carries the authoritative pause flag, the PC forwards reads and inbox answers for Contabo-homed runs over the tailnet with a host pass, one event stream per reachable node brings its items to the PC inbox, an unreachable node's rows read "server unreachable since", and `qmx node update` drains the node first.

**Depends on.** OPS1, REM and PRB-S. If P-OPS failed on Contabo, idle hosts send deltas at a longer interval (its named fallback).

**Files.**

- [ ] Edit `E/heartbeat.py` (the push and the reply), `HB/server.py` (receive, reply with `autonomy_paused` and `claims_renewed`), `E/service/runs.py`, `E/service/inbox.py` and `E/service/api.py` (merge by `home_engine`).
- [ ] Create `E/service/forward.py` (reads and answers forwarded with a host pass) and `HO/streams.py` (one event stream per reachable owned node). Edit `HO/host.py` and `QX/node.py` (`qmx node update` drains first).
- [ ] Create the matching tests, `SL/server/e68_remote_inbox.py` and `SL/server/e64_pause.py`.

**Build.**

- [ ] The PC's engine service reads runs, cards, spans, inbox items, incidents and `explain_trigger` of a Contabo-homed run by forwarding. An inbox answer is forwarded, and only the run's home folds it.
- [ ] A host that cannot reach the Hub for 5 minutes (Claude's default) honours the last flag it knew and shows "pause state unknown".
- [ ] Nothing replicates. Each ledger stays its home's.
- [ ] `runs.fetch_home` waits for the replay fork (Appendix G).

**You see.**

- [ ] A 401 on a Contabo-homed run shows in the PC's inbox, and pressing `retry` on the PC resumes it on Contabo.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert the merged list by `home_engine`, a forwarded answer folding only at home, and the "pause state unknown" timer. Run `-n 2` in `qmx-engine` and `qmx-hub`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` and `qmx-hub` suites with `-n 2` at the parent and at head. Save `ops2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E68. Run `e68_remote_inbox.py` with a fake 401 on a Contabo-homed run. Save `ops2-e68.log`. Pass when the item reaches the PC inbox and the copilot's `ops` answer within one stream round, and `retry` from the PC resumes it.
- [ ] Lane 3. E64 across both hosts. Run `e64_pause.py`. Save `ops2-e64.log`. Pass when no fire is claimed on either host within one tick of pausing, and clearing gives one catch-up per trigger.
- [ ] Lane 4. Unplug Contabo from the tailnet. Save `ops2-unreachable.log`. Pass when its rows read "server unreachable since" with the last values.
- [ ] Lane 5. Run `qmx node update` with a running attempt. Save `ops2-drain.log`. Pass when the attempt finishes its node before the restart.
- [ ] Lane 6. Lose the Hub for 6 minutes on the fake clock. Save `ops2-unknown.log`. Pass when the host shows "pause state unknown".
- [ ] Lane 7. A Contabo node without a kind the definition uses. Save `ops2-skew.log`. Pass when the node waits with `node needs update`.
- [ ] Lane 8. Measure a pushed row's size on Contabo. Save `ops2-size.log`. Pass when it is at most 4 KB.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `ops2-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes on both machines after the lanes. Save `ops2-processes.log`. Pass when no check process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from a Contabo inbox item to the PC inbox.
- [ ] Probe. Lane 2, five items.
- [ ] Baseline. None, forwarding is new.
- [ ] Rule. Fail when the p95 exceeds 10 s, because provider failures are what must reach him (ruling 77).

**Review gate.** None. The inbox and ops screens are the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends OPS2 on APP2b.

## Let another machine adopt a run whose home died (ADOPT)

ADs AD-7, AD-3, Lib AD-24. Check E69. Gate SRV. Scenarios K-33 and K-14. Done when a run's journal is mirrored to the Hub at each node end, `runs.adopt` is refused while the home's heartbeat is fresh and succeeds after, finished chunks are not paid again, nodes that committed `work/` files run again, and the old home marks its copy moved and never resumes it.

**Depends on.** OPS2.

**Files.**

- [ ] Create `E/ledger/mirror.py`. Edit `E/service/runs.py` (`adopt`), `E/runner.py` (the start-up check for an adopted run) and `HB/server.py` (the mirrored journals).
- [ ] Create the matching tests and `SL/server/e69_adopt.py`.

**Build.**

- [ ] `adopt` takes a Hub claim on `adopt:<run_id>`, seeds a ledger from the mirrored events, writes `run_adopted{from, to}`, folds open attempts `unknown`, voids memos of nodes that committed `work/` files, and resumes.
- [ ] Zone files do not travel. Nodes that wrote `work/` run again.

**You see.**

- [ ] A PC-homed fan-out cut mid-run resumes on Contabo after `adopt`, and the PC, restarted, shows its copy as moved.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Tests assert the refusal while fresh, the seeded fold, the voided memos and the moved mark. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head. Save `adopt-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E69. Run `e69_adopt.py`, removing the PC's ledger file mid-run. Save `adopt-e69.log`. Pass when adoption is refused while fresh, then succeeds, finished chunks are not paid again, and the PC marks its copy moved.
- [ ] Lane 3. Two machines adopt at once. Save `adopt-race.log`. Pass when one wins the claim.
- [ ] Lane 4. Adopt a run with a node that committed `work/` files. Save `adopt-work.log`. Pass when that node runs again.
- [ ] Lane 5. Read the mirrored journal on the Hub. Save `adopt-mirror.log`. Pass when it holds every node end.
- [ ] Lane 6. Restart the old home after adoption. Save `adopt-oldhome.log`. Pass when it never resumes the run.
- [ ] Lane 7. Adopt with the Hub unreachable. Save `adopt-nohub.log`. Pass when it is refused with the reason.
- [ ] Lane 8. Grep the mirrored journal for the planted key. Save `adopt-redact.log`. Pass when it is redacted.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `adopt-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes on both machines after the lanes. Save `adopt-processes.log`. Pass when no check process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Mirror time in ms per node end.
- [ ] Probe. Lane 2's nodes.
- [ ] Baseline. None, mirroring is new.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. ADOPT changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends ADOPT on OPS2.

## Delete the control plane's old remote runs and jobs (RUN1b)

ADs AD-57 (the deletion), AD-59. Checks E57's removed routes and E59's scan. Gate SRV and GATE-M, and REM's E57 pass on Contabo recorded in `ledger.tsv`. Scenarios 46 section 5.0 "Remote workflows reach the Library". Done when the control `runs_*`, `run_job`, `job_*` and `jobs_*` operations, their catalog rows and their `work` table kinds are gone, `RM/worker.py`, `RM/runs.py` and `RM/store.py` are deleted, `providers.py`, `models.py` and `code.py` stay, and the removed routes return 404.

**Depends on.** REM, with its E57 Contabo result in `ledger.tsv`. It edits `qmx-remote` tests, whose `conftest.py` `rebuild/base` changed, so it waits for his merge click (Override 6).

**Files.**

- [ ] Edit `QX/service.py`, `QX/catalog.py`, `QX/runs.py` and `QX/models.py` (the operations, rows and `work` kinds go).
- [ ] Delete `RM/worker.py`, `RM/runs.py` and `RM/store.py`. Edit `RM/__init__.py` and `qmx-agents/packages/qmx-remote/pyproject.toml` (drop `qmx-agents` and `langgraph`).
- [ ] Edit `qmx-agents/packages/qmx-control/tests/test_remote.py` and the `qmx-remote` tests. Edit `SL/smoke_remote.py` to start a one-node engine run instead.

**Build.**

- [ ] Before any deletion, run `git grep -n -E "runs_start_remote|run_job|jobs_list|qmx_remote\.(worker|runs|store)" -- . ':!*.md' ':!archive/**'` and attach it. Every hit is in the deletion set or edited here.
- [ ] A placed job is the `run-on-a-machine` template from REM.

**You see.**

- [ ] `POST` to the old remote-run route returns 404, and `SL/smoke_remote.py` runs its job as an engine run on Contabo.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run the `qmx-control` and `qmx-remote` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-control`, `qmx-remote` and `qmx-engine` suites with `-n 2` at the parent and at head. Save `run1b-regression.log`. Pass when head fails nothing the parent passes except deleted tests, each named.
- [ ] Lane 2. Call each removed route. Save `run1b-routes.log`. Pass when each returns 404.
- [ ] Lane 3. Run the scan from **Build.** Save `run1b-scan.log`. Pass when it prints nothing outside the deletion set.
- [ ] Lane 4. Run `SL/smoke_remote.py` against Contabo. Save `run1b-smoke.log`. Pass when its job lands as a `workflow-run`.
- [ ] Lane 5. Import `qmx_remote.providers` with `langgraph` uninstalled. Save `run1b-import.log`. Pass when it imports.
- [ ] Lane 6. List the copilot's tools on haiku. Save `run1b-tools.log`. Pass when no old run or job tool is listed.
- [ ] Lane 7. Run `uv lock --check` in `qmx-agents/`. Save `run1b-lock.log`. Pass when it passes.
- [ ] Lane 8. A remote build attempt through `code.py`. Save `run1b-code.log`. Pass when it still works.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `run1b-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes on both machines after the lanes. Save `run1b-processes.log`. Pass when no check process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Lines deleted.
- [ ] Probe. `git diff --shortstat`.
- [ ] Baseline. None.
- [ ] Rule. No fail rule. Recorded for the operator.

**Review gate.** None. RUN1b changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RUN1b on ADOPT.

## Delete the `qmx_agents` runtime after porting its agents and skills (DEL1)

ADs AD-59 (step 1), AD-55, AD-22. DELETION-PLAN D1, retargeted. Check E59's agents scan. Gate GATE-M. Scenarios K-21 (the ported agents load as plugin agents). Done when the four agent definitions and the `build-mini-app` and `debug-app` skills live in the core plugin, the copilot rules of `copilot.md` and `copilot.yaml` are in `CP/QMX.md`, `qmx-agents/packages/qmx-agents/` is deleted, and the scan prints only the two example apps' git pins.

**Depends on.** RUN1b, because `RM/worker.py` imported `qmx_agents.router` until then, and his merge click, because `rebuild/base` changed `qmx-agents/packages/qmx-agents/tests/conftest.py` (Override 6).

**Files.**

- [ ] Create `CP/agents/app-builder.md`, `data-analyst.md`, `researcher.md` and `overnight-builder.md`, ported from `qmx_agents/agents/`. No `tools` list names the `delegate` tool.
- [ ] Create `CP/skills/build-mini-app/` and `CP/skills/debug-app/`, ported. `build-workflow` already lives there from TPL2.
- [ ] Edit `CP/QMX.md`. Edit `QX/service.py` (`apps_publish`) to run the app-publish test gate if the caller scan shows it lives only in `AppHooksMiddleware`.
- [ ] Delete `qmx-agents/packages/qmx-agents/`, `SL/copilot_build_app.py`, `SL/smoke_agent.py` and `SL/smoke_firecrawl.py`, and `default_tool_registry` in `qmx-agents/packages/qmx-tools/src/qmx_tools/registry.py`.
- [ ] Edit `qmx-agents/pyproject.toml`, the pyright paths in root `pyproject.toml`, `tools/ci.py`, `tools/test_all.py` and both `uv.lock` files.

**Build.**

- [ ] Before any deletion, run `git grep -n "qmx_agents" -- . ':!*.md' ':!archive/**' ':!**/uv.lock'` and attach it.
- [ ] Commit in this order. The ports, the publish gate, the script deletions, then the package deletion.
- [ ] The example apps keep their pinned copy until they are rebuilt as packs (Appendix G).

**You see.**

- [ ] The scan prints only the two example apps' git pins, and a hub chat lists the ported agents and skills.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A plugin test asserts every file under `CP/agents/` parses and none lists the `delegate` tool. Run the touched suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run every remaining package suite with `-n 2` at the parent and at head. Save `del1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. E59 agents scan. Run the scan from **Build.** Save `del1-scan.log`. Pass when it prints only the two pins.
- [ ] Lane 3. A hub chat on haiku under the lane lock asks the ported researcher agent a question. Save `del1-agent.log`. Pass when it answers from the ported definition.
- [ ] Lane 4. Run `uv lock --check` at the root and in `qmx-agents/`. Save `del1-lock.log`. Pass when both pass and `qmx-agents` is not installed.
- [ ] Lane 5. Publish a fixture app whose tests fail. Save `del1-publish.log`. Pass when the publish is refused.
- [ ] Lane 6. List the core plugin's skills in a chat. Save `del1-skills.log`. Pass when the three ported skills list and none of his personal skills do.
- [ ] Lane 7. Import `qmx_control`, `qmx_apps`, `qmx_remote` and `qma.harness` with `langchain*` uninstalled. Save `del1-import.log`. Pass when all four import.
- [ ] Lane 8. Count deleted lines. Save `del1-lines.log`. Pass when the count is recorded.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `del1-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `del1-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Lines deleted.
- [ ] Probe. `git diff --shortstat`.
- [ ] Baseline. None.
- [ ] Rule. No fail rule. Recorded for the operator.

**Review gate.** None. DEL1 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DEL1 on RUN1b.

## Delete the LangChain family from every lockfile (DEL4)

ADs AD-59 (step 4), AD-61 (the LangChain wrapper subtracted). DELETION-PLAN D4. Check E59's lock scan plus the last full `just ci`. Gate GATE-M (through DEL1). Scenarios 46 section 5.0 "Agentic vs non-agentic workflows" (one engine, no second runtime). Done when no `pyproject.toml` names `langchain`, `langchain-core`, `langgraph`, `deepagents`, `langchain-anthropic`, `langchain-openai`, `langchain[mcp]`, `langgraph-checkpoint-sqlite` or `openai-codex`, a fresh venv lists none of them, and `just ci` passes.

**Depends on.** DEL1.

**Files.**

- [ ] Edit every `pyproject.toml` that names one of the nine, `qmx-agents/packages/qmx-tools/pyproject.toml` (`langchain-core==1.6.7`) included. Delete the LangChain wrapper in `qmx_tools/registry.py`.
- [ ] Regenerate both `uv.lock` files.

**Build.**

- [ ] Remove each dependency only after `git grep` shows no import of it outside locks, `archive/` and the two example apps.

**You see.**

- [ ] In a fresh venv after `uv sync --frozen --all-packages --all-groups`, `uv pip list` shows none of the nine.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `just ci` under the CI lock in the fresh venv in lane 1.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run `just ci` under the CI lock at head in a fresh venv. Save `del4-ci.log`. Pass when it passes.
- [ ] Lane 2. Run `uv pip list` in the fresh venv. Save `del4-pip.log`. Pass when none of the nine is listed.
- [ ] Lane 3. Run `git grep -n -i -E "langchain|langgraph|deepagents"` outside locks, `archive/` and the example apps. Save `del4-grep.log`. Pass when it prints nothing.
- [ ] Lane 4. Start `qmx_host` and run one haiku chat turn and one template on the fake provider. Save `del4-host.log`. Pass when both work.
- [ ] Lane 5. Import every package with `python -X importtime`. Save `del4-import.log`. Pass when no LangChain module appears.
- [ ] Lane 6. Start `qmx-mcp-data` over stdio and list its tools. Save `del4-mcp.log`. Pass when it lists the same names as the parent.
- [ ] Lane 7. Run `tools/build_release.py`. Save `del4-release.log`. Pass when the wheels build.
- [ ] Lane 8. Run `tools/tests/test_release_install.py`. Save `del4-release-install.log`. Pass when it passes.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `del4-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `del4-processes.log`. Pass when no `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of a cold `uv sync --frozen --all-packages --all-groups` in `qmx-agents/` on `D:`.
- [ ] Probe. Two cold syncs at the parent and two at head, interleaved.
- [ ] Baseline. The parent's mean.
- [ ] Rule. Fail when head's mean is slower than the parent's.

**Review gate.** None. DEL4 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DEL4 as the tip of the stack.

## Close the program

- [ ] Every box above is checked with its evidence, every lane outside a run set has its `menu, not run` row, and every skipped or gated PR has a `decisions.tsv` row naming its gate.
- [ ] Reply to the operator with the report autopilot-stack names. Give links to the stack's root and tip, a one-line verdict per PR, what was skipped or gated and why, every probe result with its fallback, and the trail at the store's `decisions.tsv`.
- [ ] Write the store's `RESUME.md` with the stack state for his landing session and for any PR a later gate opens.
- [ ] List every `build/*` branch and worktree for his go. Delete none without it.

## Appendix A. Prototype evidence

No prototype ran in this planning pass. The probe PRs run first and settle what the design cannot know without running the CLI, the SDK, Hindsight or his server. The planner read these facts from `origin/engine/base` at `132169c7` and `origin/rebuild/base` at `4345eafa` with `git show`, `git grep`, `git ls-tree` and `git merge-tree` on 2026-10-18, and each one shaped a PR.

| Fact read from the code | Where | Shapes |
|---|---|---|
| `_STRONG` names `claude/fable`, `roles.test_order` tries test-only rows first, `roles.live_order` is `plan, key` | `E/settings.py:22`, `:71`, `:72` | HYG0 |
| `run --mode` offers `live` | `E/__main__.py:56` | HYG0 |
| The qma-core member-set test lacks `packages/qmx-engine` | `qma-core/tests/test_extensibility.py:136` | HYG0 |
| `Budgets` holds `background_cap` 0.5, `max_turns` 50 and `max_budget_usd` 5.0 | `H/launch.py:229-232`, `:518` | CAPH |
| The engine polls the chat file in `wait_turn` and answers asks with `Reject` | `E/ports/harness_adapter.py:135`, `:221`, `:237` | TURN-E |
| `money.py` is 1,198 lines and `relay.py` 1,147 | `git grep -c` | GUARD, RTR0 |
| `PLUGIN_SHA256` locks one plugin | `H/home.py:73` | PACK |
| The trigger kind check allows only `cron, interval, manual, after` | `E/ledger/migrations.py:35` | TRG2a |
| The apps supervisor schedules by interval and counts a run budget | `AP/supervisor.py:86`, `:430` | RUN1a |
| `RM/worker.py` imports `qmx_agents.router`, `qmx_agents.spec`, `qmx_agents.workflows` and `langgraph` | `RM/worker.py:28-31` | DEL1 after RUN1b |
| The builder skill is a placeholder in the old runtime | `qmx_agents/skills/build-workflow/SKILL.md` | TPL2, DEL1 |
| `qmx_engine.host` serves the engine without the chat routes | `E/host.py:2-5` | HOST |
| `rebuild/base` adds six files since the merge base, two `conftest.py` files and four HP2 probe files | `git diff --name-only` | Override 6, RUN1b, DEL1 |
| Merging `engine/base` into `rebuild/base` has no conflict | `git merge-tree --write-tree`, rechecked 2026-10-18 | GATE-M |

Unproven by design until their probe runs. P-SET, P-SYS, P-PERM, P-PK, P-TG, P-PL and P-NM in PRB-H. P0, P1 and P1k in PRB-R. P-TAINT, P-MEM, P-SRCH, P-NEST and P-OPS in PRB-L and PRB-S. P3 in RTR2 and RTR3. P7 in RTR4. P4 and P2 in RTR7. P5 in DLG. P-EV in TRG2b. P-APP in APP2b. P-LAT is measured in LIB4 and gates nothing.

## Appendix B. Alternatives rejected

- **Autopilot-full.** The operator reviews before landing and withholds merge authority, so the selection rule picks autopilot-stack.
- **A checker agent per PR.** The operator's brief says the coordinator verifies each PR itself. That leaves both agent slots for builders, and the coordinator's context is managed by handing off at 40 %.
- **Waiting for the merge click before any work.** Forty-seven PRs need neither the click nor the server. The six files `rebuild/base` adds touch nothing before RUN1b.
- **Deleting `qmx_agents` right after the run list (47's order).** `RM/worker.py` imports it, so the deletion would break the only working remote compute. DEL1 waits for RUN1b.
- **Per-toolset MCP servers with toggling as the first design.** Review 48 H6 showed the CLI keeps switch-offs per workspace. One server per chat, re-listed, is first. Toggling is only P-TG's fallback.
- **Building REF2 (files, folders, URLs, videos) now.** It needs the multimodal layer, which this program does not build.
- **Building the Lab, the browser, the desktop host and copilot loops here.** They are not in the operator's rebuild list. Appendix G holds them with what each waits for.
- **Ten live lanes per PR.** The light rule replaced them. They stay as a menu because `check-plan.mjs` requires them.

## Appendix C. Risks

- **Haiku test turns draw on his copilot's plan window (every model lane).** Appendix E guesses about 830 turns over the program, about 150 of them in TPL1.
- **Probes forward his plan login through a loopback probe process (PRB-R, RTR7).** The probe router writes no header value and keeps nothing past the hop. A lane in each greps for leaks.
- **OpenRouter stands in for direct provider rows.** Direct Kimi, DeepSeek, GLM, Qwen and MiniMax rows stay unproven until he adds keys.
- **A declared `Bash` in an agent step can write elsewhere on his PC (AGW).** The guard keeps it out of QMX's stores, logins and keys, and nothing it writes elsewhere is kept. A workflow that must not touch the rest of the PC picks a container.
- **The tool names change once (CAT).** Any personal note or skill of his that names an old `mcp__qmx__*` tool stops matching.
- **The server phase waits on his server step.** Until then remote work stays on the old path, which keeps working.
- **The Library cut-over waits on his landing plus a week (Appendix G).** Until then both stores are written.
- **Opus reviews Opus (every PR).** A cross-family review is not run.
- **No macOS or Linux test machine.** Out of scope for this program.

## Appendix D. Links and reading list

- The contract is `architecture/workflow-engine/` (`ARCHITECTURE-SPINE.md`, `SOLUTION-DESIGN.md` sections 17, 18, 26 to 29, `HARNESS-REQUESTS.md` as a plain change list with its probe lines), `architecture/library-and-data/` (`ARCHITECTURE-SPINE.md`, `MIGRATION.md`) and `architecture/lab-and-pods/ARCHITECTURE-SPINE.md` for the rules PACK and AGW cite.
- The design record is `research/methodology/39-architecture-rerun.md` with "Review applied", "Fix-check applied" and "Retirement pass", `43-whole-app-unlocked.md`, `47-studies-folded.md` with "Review 48 applied", and `48-review-unlocked-and-folded.md`. Row ids are in `40-retriage.md` section 2. Scenario ids are in `46-domain-expansion.md` section 5.
- Rulings live in `research/methodology/26-operator-rulings-and-alignment.md`. Its latest ruling wins.
- `UI-HANDOFF.md` lists what the UI session builds. No PR here builds a screen.
- The last run's store `D:/QMX-worktrees/qma-ship/engine/` holds the old briefs, `BACKLOG.md`, `lows.md` and `review/`. Builders read a line there only when their section cites it.
- `WORKFLOW-SHIP-PREP.md` "Mistakes made last time" shaped Overrides 2, 3, 4, 5 and 8.
- Never read `tracker/qma-v2/archive/` as the plan.

## Appendix E. Sizing (an estimate)

Every number is the planner's guess, not a measurement. Effort is focused builder hours. The coordinator's check adds about 30 minutes per PR. Haiku turns are plan turns through the ship home's login. OpenRouter calls are provider-proof calls only.

| PR | Effort (h) | Haiku turns | OpenRouter calls | Gate |
|---|---|---|---|---|
| HYG0 | 2 | 5 | 2 | none |
| PRB-H | 5 | 40 | 0 | none |
| PRB-R | 4 | 25 | 20 | none |
| PRB-L | 5 | 0 | 10 | none |
| CAPE | 8 | 10 | 0 | none |
| CAPH | 4 | 5 | 0 | none |
| CAPX | 5 | 5 | 0 | none |
| SEC1A | 4 | 5 | 0 | none |
| SEC2A | 6 | 0 | 0 | none |
| BUG1 | 8 | 10 | 0 | none |
| BUG2 | 8 | 0 | 0 | none |
| BUG3 | 6 | 0 | 0 | none |
| HOST | 8 | 10 | 0 | none |
| TURN-H | 10 | 30 | 0 | none |
| TURN-E | 8 | 20 | 0 | none |
| GUARD | 8 | 20 | 0 | none |
| AGW | 6 | 25 | 0 | P-PERM |
| CAT | 10 | 20 | 0 | P-NM, P-PK |
| SURF | 10 | 30 | 0 | P-SYS |
| RUN1a | 6 | 0 | 0 | none |
| TRG2a | 6 | 0 | 0 | none |
| OPS1 | 5 | 5 | 0 | P-OPS |
| LIB1 | 14 | 10 | 0 | none |
| LIBM | 8 | 0 | 0 | none |
| SES | 4 | 10 | 0 | none |
| LIB2 | 6 | 0 | 0 | P-TAINT |
| LIB3 | 6 | 10 | 0 | P-SRCH |
| REF1 | 6 | 15 | 0 | none |
| PACK | 8 | 20 | 0 | P-PL |
| APP2a | 8 | 0 | 0 | none |
| MEM | 10 | 20 | 10 | P-MEM |
| EVAL | 6 | 30 | 30 | none |
| RTR0 | 4 | 0 | 5 | none |
| RTR1 | 6 | 5 | 20 | none |
| RTR2 | 10 | 5 | 80 | P3 |
| RTR3 | 6 | 0 | 40 | P3 |
| RTR4 | 10 | 5 | 20 | P7 |
| RTR5 | 6 | 15 | 10 | none |
| RTR6 | 5 | 10 | 30 | P1k, P1 |
| RTR7 | 8 | 60 | 60 | P0, P1, then P4, P2 |
| DLG | 8 | 25 | 30 | none |
| TPL1 | 8 | 150 | 0 | none |
| TPL2 | 4 | 40 | 0 | none |
| TPL3 | 6 | 60 | 20 | P-NEST |
| QMBH | 3 | 0 | 0 | none |
| DEL2 | 4 | 5 | 0 | none |
| DEL3 | 5 | 10 | 0 | none |
| PRB-S | 3 | 0 | 0 | SRV |
| LIB4 | 12 | 5 | 0 | SRV |
| RTRP | 10 | 5 | 20 | SRV |
| REM | 12 | 10 | 10 | SRV |
| TRG2b | 6 | 0 | 0 | SRV, P-EV |
| APP2b | 8 | 0 | 0 | SRV, P-APP |
| OPS2 | 8 | 5 | 5 | SRV |
| ADOPT | 6 | 0 | 0 | SRV |
| RUN1b | 4 | 5 | 0 | SRV, GATE-M |
| DEL1 | 5 | 10 | 0 | GATE-M |
| DEL4 | 3 | 0 | 0 | GATE-M |
| Total | 388 | 830 | 422 | |

- **Number of PRs.** Fifty-eight. Forty-seven need neither his server nor his merge click, nine need his server step (one of them also his merge click), and two more need his merge click.
- **Wall time.** Two builders at once where files allow, and the coordinator's check beside them. Roughly 20 to 25 working days for the first 47 PRs, and another 8 to 10 for the server phase and the last deletions. A guess.
- **Full suite.** `just ci` runs five times, in the checks of BUG3, SURF, TPL3, DEL3 and DEL4.

## Appendix F. Files two PRs share

Never give these to two builders at once. Two PRs on one row run one after the other, and the later one waits for the earlier one's verdict.

| File | PRs |
|---|---|
| `E/settings.py` | HYG0, CAPE, CAPX, TRG2a, MEM, RTR5, REM |
| `E/roles.py` | HYG0, CAPE, RTR5 |
| `E/nodes/agent.py` | CAPE, TURN-E, AGW, SURF, RTR5 |
| `E/nodes/llm.py` | CAPE, TURN-E, RTR5 |
| `E/runner.py` | CAPE, CAPX, BUG1, BUG2, TURN-E, ADOPT |
| `E/core/fold.py`, `E/core/ladder.py` | CAPE, BUG1, BUG3 |
| `E/core/joins.py` | BUG2, BUG3 |
| `E/admission.py` | CAPE, CAPX, RTR5 |
| `E/workers/local.py` | CAPX, SEC2A, BUG1, BUG2 |
| `E/workers/effects.py` | SEC2A, BUG1 |
| `E/ledger/store.py` | SEC1A, BUG1, BUG2 |
| `E/ledger/inbox_table.py` | SEC1A, BUG1, BUG3, TRG2a, OPS1 |
| `E/service/runs.py` | SEC1A, BUG1, BUG2, BUG3, OPS2, ADOPT |
| `E/service/explain.py` | SEC1A, BUG2, TRG2a |
| `E/triggers/ticker.py` | BUG1, TRG2a, TRG2b |
| `E/triggers/preflight.py` | TRG2a, OPS1, LIB2, REM |
| `E/definition/model.py`, the v1 schema | CAPE, SEC2A, AGW, SURF |
| `E/definition/lint.py` | CAPE, SEC1A, GUARD |
| `E/definition/validate.py` | SEC2A, BUG2, TPL3 |
| `E/definition/registry.py` | BUG2, CAT, RUN1a |
| `E/nodes/app_op.py` | RUN1a, APP2a, APP2b |
| `E/heartbeat.py` | OPS1, OPS2 |
| `E/policy.py` | TURN-E, AGW |
| `T/**` | CAPE, SEC2A, AGW, CAT, SURF, LIBM, EVAL, TPL1, TPL3, REM |
| `H/launch.py` | CAPH, TURN-H, GUARD, PACK, SURF, RTR0, RTR2, RTR6, RTR7, REM |
| `H/harness.py` | CAPH, CAPX, TURN-H, GUARD, CAT, SURF, PACK, REF1, RTR0, DLG |
| `H/chat.py` | TURN-H, CAT, SURF |
| `H/home.py` | TURN-H, PACK, SURF, REF1, RTR7 |
| `H/tools.py` | GUARD, CAT, DLG |
| `H/guard.py` | GUARD, CAT |
| `H/surface.py` | SURF, REF1, PACK, MEM, RTR6, DLG |
| `H/__init__.py` | CAPE, TURN-H |
| `H/usage.py` | CAPH, TURN-H, RTR0 |
| `H/delegate.py` | DLG, RTRP |
| `HO/host.py` | HOST, TURN-E, LIB1, SES, TRG2a, OPS1, MEM, RTR0, RTR2, RTR5, RTRP, REM, OPS2 |
| `HO/sessions.py` | SES, REF1, MEM |
| `QX/service.py` | GUARD, CAT, RUN1a, LIBM, EVAL, TPL3, DLG, DEL1, RUN1b |
| `QX/catalog.py` | CAT, OPS1, LIB2, REF1, APP2a, MEM, RTR1, RTR4, RTR7, DLG, APP2b, RUN1b |
| `QX/context.py` | REF1, MEM |
| `QX/node.py` | LIB4, RTRP, OPS2 |
| `AP/supervisor.py` | RUN1a, OPS1, APP2a, APP2b, DEL3 |
| `AP/manifest.py` | RUN1a, APP2a |
| `R/relay.py` | RTR0, RTR1, RTR2, RTR3, RTR4, RTR7 |
| `R/server.py` | RTR2, RTR7, RTRP |
| `R/pool.py` | RTR4, RTRP |
| `LB/port.py` | LIB1, LIB2, LIB3, LIB4 |
| `HB/server.py` | LIB4, TRG2b, OPS2, ADOPT |
| `examples/apps/*/app.toml` | APP2a, RTR4 |
| `qmx-agents/pyproject.toml`, `tools/ci.py`, both `uv.lock` files | HOST, LIB1, MEM, RTR0, LIB4, DEL2, DEL3, DEL1, DEL4 |

Safe pairs to run at once. Any probe PR beside any build PR. CAPE beside CAPH. The engine track (SEC1A, SEC2A, BUG1, BUG2, BUG3) beside the host track (HOST, TURN-H). GUARD beside TURN-E. AGW beside GUARD. QMBH beside any PR that does not touch `qmb/`.

## Appendix G. Named backlog, not scheduled in this program

Each item names why it waits and what it needs. None is built here.

| Item | Rows | Waits for |
|---|---|---|
| The multimodal layer and attachments (AD-42, H30, E44) | AL-18 | its own PR after RTR5 |
| REF2, references to files, folders, URLs and videos (AD-63) | none | the multimodal layer |
| The browser pack, take-over and HUD (AD-44, H35, E45, P-BR) | AL-10 | ruling 30's journeys explained to him first |
| Cua and MT5 demo click-through (AD-33, E46) | AL-9 | the browser pack, and his demo accounts in Settings |
| cTrader demo click-through | AL-9 | paid machines (a Windows desktop placement) and a demo-only cTrader ID |
| The desktop host and output directives (AD-48, AD-45, E47, E49 desktop half) | AL-17, AL-12 | the shell probe, and the UI session |
| Copilot standing loops and loop-to-server (AD-47, H34, K-18) | none | a loops PR after SURF |
| Session fork, run fork, replay and `runs.fetch_home` (AD-35, AD-7, H50, P-FK, K-20, K-30) | B-82 | the replay packet |
| The background review fork (H37, P-FK) | none | the replay packet |
| Engine later packets for pinned test data, nested fan-out, the grader's `llm` mode and `engine_view` reads | B-20, B-46, B-47, B-80, B-81, L-26, L-84 | BUG2's refusals are in place |
| Doctor verdicts, champion and challenger (AD-26) | B-34 | MEM and the improve workflow |
| The skills curator and `/learn` (AD-46 part) | AL-16 part | LIB1's lifecycle kinds |
| Worktrees, reconcile and checkpoints (AD-49) | H-89, H-108, H-109 | LIB1 |
| The Lab program (Lab AD-1 to AD-18, P-CELL, K-29) | none | his Lab session, on the seams this program builds |
| The Library cut-over (MIGRATION step 6) | none | his landing of LIB1 and LIBM, then seven clean nightly diffs |
| E57's GPU case and the preemption drill (K-23) | none | paid machines (a GPU provider) |
| Data, the market-data service, the tick backup, the locality score and the restore order (K-14, K-33) | none | rulings 91 and 111, a data study first |
| The example apps rebuilt as packs | none | PACK and APP2a, then his go |
| The documentation pass over 34 pages naming the daemon | DOC-CHANGES row 44 | DEL2 |
| One uv workspace, `adws/`, `queue/` and 2.7 GB of test homes (43 section 7) | none | his go, because deletions need it |
| Lane-script hygiene | L-3, L-5, L-11, L-13, L-15, L-41, L-59, L-62, L-67, L-72, L-73, L-74, L-78, L-79, B-62, B-74, L-27 | any free slot |
| Methodology, system prompt text, persona and methodology slot content (B26 to B29) | none | his methodology session (ruling 82) |
| Voice inside QMX | B15 | much later (ruling 85) |

## Appendix H. Defaults

Every value here is Claude's default, not the operator's. Each is UI-editable, and each was checked against rulings 105 to 119.

| Setting | Default | Where it lands |
|---|---|---|
| Role lists | `key, gpt, plan`, Chinese rows first in every tier, no Fable | HYG0, then generated in RTR5 |
| Test-mode first candidate | `claude/haiku` through the plan login | HYG0 |
| `pool.strategy` | `least_used` | CAPE, RTR4 |
| His copilot account's `background_priority` | `last` | RTR4 |
| Account share, ceiling, cooldown | unset | RTR4 |
| `[budgets] max_budget_usd`, `background_cap`, Background and Child `max_turns` | unset | CAPH |
| `max_live_chats` | derived from RAM, `session_mb` 1,536, `overhead_mb` 4,096 on the PC | CAPH |
| `limits.interactive_reserve` | 2 | kept |
| `cpu_slots`, `container_slots`, `gpu_slots` | cores minus one, 3, unset | CAPX |
| `timeout.idle` | 300 s agent, 600 s script | CAPE |
| `timeout.in_tool` | 1,200 s of no CPU and no IO | CAPE |
| `timeout.grace` and the warning | 120 s, warning at 80 % | CAPE |
| `loop.repeat`, `loop.window`, `loop.no_convergence` | 5, 8, 6 of 8 | CAPE |
| Crash loop | 3 engine restarts, then park | CAPE |
| The cache-case fallback folder | the workflow's shared workspace with the overlay added | AGW, if P-SET's cache case failed |
| Slot budgets | rules 2,000, persona 4,000, methodology 8,000, pack layers 600 per pack, skills index 120 per skill (characters) | SURF |
| Spill target before LIB1 | the control `library.db` | CAT |
| Webhook trigger home | `contabo` once the server exists, else `pc` | TRG2a |
| Market calendar | the trigger's IANA zone, weekends, an empty holiday list | TRG2a |
| Spend-neutral re-run | 5, 15, 30 minutes | TRG2a |
| `heartbeat.interval` | 30 s | OPS1 |
| PC log window | 7 days | OPS1 |
| Pause state unknown after | 5 minutes without the Hub | OPS2 |
| Idle chat export | daily after 24 hours idle | SES |
| Curator archive of uncited test records | after 30 days | LIB3 |
| P-SRCH question set | 40 questions the builder writes over his `library.db` | PRB-L |
| Reference excerpt budgets | 25 % soft, 50 % hard of the window, 200 folder entries | REF1 |
| Eval tasks | Library artifacts tagged `eval-task` | EVAL |
| `chunk.fill` | 0.30 of the model's window | RTR5 |
| Compaction point | 0.40 at 512k and above, 0.75 below | RTR5 |
| `chars_per_token` | 3, with 10 % headroom | RTR1, RTR5 |
| `first_token_timeout_s` | 120 s plus 60 s per 100k prompt tokens | RTR1, RTR2 |
| `API_TIMEOUT_MS` | above the largest row timeout plus 60 s, at least 780 s | RTR2 |
| `keepalive` per row | off | RTR2 |
| `router.plan_lane` | off until P4 and P2 pass and he turns it on | RTR7 |
| `delegate` batch and depth | 10 per batch with no ceiling, depth 1 | DLG |
| Template titles and the five new template names | SOLUTION-DESIGN section 26.9's proposals and TPL3's names | TPL1, TPL3 |
| The core plugin's integrity check | a manifest file built from the plugin's files | PACK |
| The APP2b fallback | stateful operations stay on the PC home | APP2b, if P-APP failed |
| QMB, QMN and QML edits done in this program | yes, under ruling 118, listed in each PR body | QMBH, DEL3 |

## Appendix I. Gates and calls

| Gate | What it is | PRs that wait | If it never comes |
|---|---|---|---|
| GATE-M | His merge click of `engine/base` into `rebuild/base` | RUN1b, DEL1, DEL4, and his landing of the stack | 55 PRs still build and stack on `engine/base` |
| SRV | His server reachable over Tailscale for the builders (an operator step, not a paid machine) | PRB-S, LIB4, RTRP, REM, TRG2b, APP2b, OPS2, ADOPT, RUN1b | remote work stays on today's path, which keeps working |
| Paid machines | Which rented provider to pay for, and when, including a Windows machine for cTrader demo work | no PR, only E57's GPU case and Appendix G rows | nothing in this program changes |
| QMBH review | His review of the QMB host change, because QMB is his tool | QMBH's append, then DEL2 and DEL3 | the daemon stays until he reviews |
| Probe gates | P-PERM, P-PK, P-PL, P-SYS, P-NM, P0, P1, P1k, P-TAINT, P-SRCH, P-MEM, P-NEST, P-OPS, P3, P7, P4, P2, P-EV, P-APP | the PR the preamble names | that PR takes the fallback its preamble names |
| W1, W2 | His two word questions ("strategy", one folder shape with two names) | nothing | the recommended words stand |

The plan lane is a review, not a gate. RTR7 ships with the lane off, and he turns it on himself after reading P4 and P2.

## Appendix J. Attention, for the operator

The operator's Attention list is in `PROMPT-HARDENING.md`, beside the paste prompt. It names his merge click, his server step, the paid-machine call, the optional sign-ins and keys, the defaults to check, and the risks of Appendix C in plain words.
