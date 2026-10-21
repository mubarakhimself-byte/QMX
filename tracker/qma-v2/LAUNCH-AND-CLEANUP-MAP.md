# Launch and clean-up map (2026-10-21)

Read-only survey for the planning lead. Nothing was merged, pushed, deleted, checked out or moved. Git facts come from `git ls-remote`, `rev-list`, `cherry` and `merge-tree --write-tree` against the live remote on 2026-10-21. Code facts come from the merged code at `origin/engine/base` `6b16e461` (read in the detached check copy `D:/Temp/tpl3-check`, whose tree is identical).

## In plain words

- All the new agent-system code is merged. It sits on one branch, `engine/base`. Your `main` holds no code at all, only documents.
- There are six long-lived branches and about 150 short ones. 135 of the short ones are fully merged. They are safe to delete once you say go.
- One branch is dangerous: the UI rebuild. It has 117 saved changes that exist only on this PC. Push it to GitHub first.
- The risk-and-sizing work is also only on this PC. Git ignores its folder, so no branch holds it.
- The merged code starts. I booted the new host on a throwaway home, it answered, and I stopped it.
- You cannot use QMX yet for one main reason: no screen talks to the new host. Both UI versions show demo data only.
- Second reason: about a dozen small wires were left loose between the merged pieces. Example: mini-app tools never reach a chat.
- Your two-part picture is right, and the folders already follow it. But the bridge between the parts is mostly empty today. The agent tools for data, backtests, strategies and the trading node exist by name and refuse every call. An agent that wants real work done today would run raw Python.
- Best branch model for you: one trunk (`main`), short branches that live for one change, and a tag when a version is good. No integration branch, no staging branch.
- Getting there takes one merge that brings the code and the documents together. It has 17 conflicts, all in documents.
- A test still writes junk into your real Library on every full test run. There are 16 junk items now. The fix already exists on a branch that is not merged yet.
- Clutter: 191 git worktrees, about 312 private Python environments inside them, a 699 MB test database on C:, and 8 GB of throwaway test homes on D:. Nothing was deleted.
- Both drives are nearly full (C: 13 GB free, D: 15 GB free). Clearing merged worktrees and test homes is part of getting ready, not an extra.

## 1. Inventory

### 1.1 Long-lived branches

| Branch | Head, date | What it holds | Relative to `engine/base` |
|---|---|---|---|
| `engine/base` | `6b16e461`, 10-21 | The real code tip. The rebuild (P01-P24), the harness (HP0-HP17 minus HP2), the workflow engine (EP0-EP14, HG1-2, TP1-4) and all 42 build PRs (#112-#154, merged as merge commits on 10-21). | itself |
| `rebuild/base` | `4345eafa`, 10-18 | The older code trunk. | 21 commits not in `engine/base` (HP2's GPT-on-plan probe, the plants-lock flake fix, and the test guard that stops tests writing into your real `~/.qmx`). 286 behind. Merges clean both ways. |
| `main` | `c3e8ec5e`, 09-27 | Documents only. Its top folders are `docs`, `_bmad-output`, `_docwork`, `workroom`, `tracker`, `adws`, `queue`, `archive`, `recorder`, `.serena`, `.worktrees`. No `packages`, `qmx-agents`, `qmb`, `qml`, `qmn` or `apps`. It also carries a stray gitlink `.worktrees/ui`. | 11 commits not in `engine/base` (all documents: workbench and CONNECT absorption, QML research epics, the 09-19 "main apps" research dump of 1,858 files, two 09-23..09-27 workroom checkpoints). 1,831 behind. Not branch-protected on GitHub. |
| `integration` | `a0e87697`, 09-30 | The retired factory trunk. | Fully inside `engine/base`. Nothing unique. |
| `plan/agent-system` | `feb35b8b`, 10-18 | The plan: `tracker/qma-v2/` (HARDENING-PLAN, the three architecture spines, UI-HANDOFF, rulings, research, wayfinder). | 101 doc commits not in `engine/base`. Merges clean into `engine/base` and `rebuild/base`. |
| `ui-review/repair` | `eea09941`, 10-14, **local only** | The UI rebuild (the design you click through): 339 files under `apps/qmx-ui`, plus `tools/ui_factory`, `.grok/` and two CI workflow edits. | **117 commits on no remote.** Based on `7b65732f` (09-27). Merging into `engine/base` gives 25 conflicts: 23 in `apps/qmx-ui`, plus `.github/workflows/battery.yml` and `skylos.yml`. |
| `staging` | does not exist | | |

Other named lines: `ui-integration` and `ui-epic/066-shell` (the Grok UI you scrapped on 10-01; 4 and 19 unique commits), `codex/factory-enforcement-*` (retired factory; heads also tagged `factory-candidate/*`), `factory-recovery/007/*` (08-23), two `qmx-*-checkpoint-2026-10-01` branches. Open PRs: #122 (start-up change, approved, mergeable into `engine/base`) and #25 (a draft marked "do not merge", `rebuild/base` into `integration`).

### 1.2 Short branches

- Remote: 148 branches and 26 tags. 128 branches are contained in `engine/base`. 7 more are patch-equivalent (same changes, different commits). The 13 with unique work are the ones in 1.1, plus `build/qmbh` (PR #122), `fix/qma-plants-flake`, `fix/qmx-remote-test-home` and `qma/hp2` (all three already inside `rebuild/base`), and `rebuild/p08-guards` (squash-merged as #35, so its 10 commits are history only).
- Local: 162 branches. 23 `build/*` branches show commits "not on any remote". `git cherry` shows every one of them is patch-equivalent to `engine/base`: they are the pre-rebase copies left behind when the coordinator force-pushed rebased heads. Nothing is lost if they go.
- Truly local work: `ui-review/repair` (117 commits) and `epic/049-skylos-qml-quality-3` (2 commits, old factory QML lint). One stash from 08-23 (`factory-recovery epic-007`).

**Safe to delete later, on your go:** all 47 `build/*` (local and remote) once #122 lands, the 21 `engine/*`, the 18 `qma/hp*` once `rebuild/base` is merged, the ~45 `rebuild/p*`, all `epic/*`, `integration`, `restore/*`, `deployment/*`, `research/mql5-article-library` (its one commit is on `main`), `plan/risk-sizing` (it equals `main`; no commits), `ui` (08-21, merged). Keep as tags rather than branches: `ui-integration`, `ui-epic/066-shell`, `codex/factory-enforcement-*` (already tagged), `factory-recovery/*`.

**Holds unique work, do not delete:** `ui-review/repair` (push first), `plan/agent-system` until merged, `rebuild/base` until merged, `build/qmbh` until #122 merges, `main`.

### 1.3 Worktrees

`git worktree list` shows 192 entries (the main checkout plus 191). There is also a second clone at `D:/QMX-worktrees/p16a-repository` with one worktree, `p16a-deletion-plan`, whose head is merged.

| Group | Count | State |
|---|---|---|
| `D:/QMX-worktrees/bld-*` (builders) | 47 | Clean. Merged. `bld-run1a-fix2` shows one modified test file with an empty diff (line endings only). `bld-qmbh` holds PR #122's head (pushed). |
| `D:/QMX-worktrees-archive/*` | 34 | Old factory and P01-P18 worktrees. Clean except two: `epic-072-pack-ui-action-context` (5 modified, 4 new files in `qma-wire`/`qma-daemon`, code due for deletion) and `epic-071-editor-drafts` (1 modified, 1 new, same). |
| `D:/Temp/*-check` and `hp*-verify` | 32 | Detached check copies. Clean. |
| `D:/QMX-worktrees/eng-*` | 21 | Clean, merged. |
| `D:/QMX-worktrees/qma-hp*`, `qma-verify*` | 20 | Clean. `qma-hp2` is merged only into `rebuild/base`. |
| `D:/QMX-worktrees/p15`-`p23`, `p16b`, `p16c`, `p17-docker-ci`, `p22-base-check`, `harness-survey` | 12 | Clean, except `p23-linux`: 3 modified files and 1 new test in `qmx-apps` and `qma-daemon`, never committed (10-08). Small; probably superseded by later `qmx-apps` work, but unread. |
| `D:/QMX-worktrees/chk-*` | 8 | Detached, clean. |
| `C:/Users/Mubarak/.codex/worktrees/*` | 5 | Codex factory worktrees. Clean. |
| `C:/Users/Mubarak/Desktop/QMX/.worktrees/*` | 4 | `integration-inspect`, `mql5-library`, `risk-sizing` (equals `main`, empty), `ui` (08-21). One untracked file in `mql5-library`. |
| `C:/Users/Mubarak/Desktop/QMX-worktrees/*` | 3 | `p14-road-to-live` (clean), `rebuild` (local `rebuild/base` 242 commits behind origin; untracked `.reticle/` and `research/`), **`ui-review-repair` (clean, but its branch is local only)**. |
| `D:/QMX-p14-*`, `qma-plants-flake`, `qmx-test-home`, `agent-system` | 5 | Clean. |
| Main checkout `C:/Users/Mubarak/Desktop/QMX` | 1 | On `main`. Modified `CLAUDE.md` (the QMA v2 section exists only here, uncommitted) and `.serena/project.yml`. Untracked `.svelte-kit/`, `.vite/`, `_bmad-output/implementation-artifacts/`, two workroom folders. **`workroom/risk-lab-2026-10-05/` is git-ignored by its own `.gitignore` (`*`)**, so the risk work shows as neither tracked nor untracked. |

Only the main checkout, `ui-review-repair`, `p23-linux` and the two archive epics hold anything git does not already have.

## 2. Target branching model

### 2.1 What I recommend

One trunk, `main`. Every change lives on a short branch named for the change, opens a PR into `main`, and is deleted when it merges. Stacked PRs are fine; GitHub retargets each one as its parent merges, which is what you just did 42 times on `engine/base`. When a version is good enough to use, tag it (`usable-2026-10-24`). The tag is your "staging": a name for a known-good point, with nothing to keep in sync.

Why not integration, then staging, then main: with one operator and agents that never merge, the middle branches only add merges and drift. Today proves it. `integration` died on 09-30, `rebuild/base` and `engine/base` split and need a merge, `staging` was never made, and `main` never received code.

Rules that make it stable:

- Turn on branch protection for `main`: PRs only, no force-push, no deletion. Agents keep pushing only their own short branches.
- Land each PR with a merge commit or a squash, your choice per PR. But never squash-merge a long-lived branch into another long-lived branch. A squash drops the ancestry, so the next merge between the same two branches conflicts on every line touched twice. If you ever keep a second long-lived line again, land it with a merge commit.
- One worktree per active builder, removed when its PR merges. The coordinator's brief should say so; this run left all 47 behind.
- Remove the `.worktrees/ui` gitlink and add `.worktrees/` to `.gitignore`.

If you want a buffer anyway: keep exactly two lines, `dev` (agents land here) and `main` (your click, merge commit only, never squash). That is the smallest version of the old model that does not drift.

### 2.2 Getting there from today

Every step below is your click or your go. Conflict counts are from `git merge-tree --write-tree` on 10-21.

1. **Push `ui-review/repair` to GitHub** as it is. No merge, just a backup of 117 commits that exist only on `C:`.
2. **Merge PR #122** (start-up change) into `engine/base`. Approved, mergeable, 0 conflicts. This unblocks the two local deletion PRs.
3. **Close PR #25** (the "do not merge" draft).
4. **Merge `rebuild/base` into `engine/base`.** 0 conflicts. Brings the test guard (stops the junk Library items), HP2, and the plants flake fix. This also satisfies the "merge click" gate the plan waits on, because one branch now holds both.
5. **Merge `plan/agent-system` into `engine/base`.** 0 conflicts. The plan and architecture then live beside the code.
6. **Converge with `main`.** A builder makes `land/main` from `engine/base`, merges `origin/main` into it, resolves the 17 conflicts, and opens one PR into `main`. You land it with a **merge commit**. The 17 conflicts, all documents or config:
   - `.gitignore` (content)
   - `_bmad-output/.../architecture-QMX-2026-09-16/research/query_hermes_sessions.py` (add/add)
   - six `_docwork/*.yaml` files (deleted on the code line, edited on `main`)
   - `docs/AGENTS.md`, `docs/index.md`, `docs/components/qma-core.md`, `qma-daemon.md`, `qma-wire.md`, `qml.md`, `trading-node.md`, `docs/contracts/ct-40-qma-wire-envelope.yaml`, `docs/lenses/security/security-model.md`
   - Resolution rule: code-line side for `.gitignore`; `main`'s side for the QMF/QML/node documents (they carry the newer workbench and CONNECT text); delete `_docwork` (the code line already did); the three `qma-*` pages get `main`'s text plus a "replaced, see tracker/qma-v2" banner until the deletion PRs remove them.
7. **Retire the old lines** after the converge PR lands and one boot works: delete `engine/base`, `rebuild/base`, `integration`, `plan/agent-system` and the merged short branches, keeping tags where listed in 1.2. Then `git worktree prune` and remove the merged worktrees with `git worktree remove`.

Steps 2-5 can each be a GitHub PR with your click, or one PR that carries all four; they do not conflict with each other (checked pairwise: `rebuild/base` with `build/qmbh`, with `plan/agent-system`, and `build/qmbh` with `plan/agent-system` are all 0).

### 2.3 The remaining PRs

The plan's 58 rows: 43 done (42 merged plus #122 approved), 2 skipped by a probe result and not owed (agent steps writing files, and the Claude-plan router lane), 13 waiting. Your seed says 15; the difference is that RUN1b is one of the nine server PRs, and #122 is already built.

| PR | What | Waits on | Targets after step 6 |
|---|---|---|---|
| #122 QMBH | `qmb host start` starts the new host | your merge (approved) | `engine/base` now, as in step 2 |
| DEL2 | delete the old daemon and host forwarders | #122 merged | `main` |
| DEL3 | delete `qma-core` and `qma-wire` | DEL2 | `main`. Watch four live imports of old code in new packages: `qmx_control/catalog.py` (money-path barrier), `qma/harness/money_words.py`, `qmx_apps/supervisor.py`, `qmx_apps/road/check.py` |
| PRB-S, LIB4, RTRP, REM, TRG2b, APP2b, OPS2, ADOPT, RUN1b | server phase | your Contabo step | `main`, built on the tip at that time |
| DEL1 | delete the `qmx_agents` runtime | RUN1b | `main` |
| DEL4 | remove the LangChain family from the lockfiles | DEL1 | `main` |

The plan's "Override 6" (rebase the chain onto `rebuild/base` at your click) becomes "build on `main`". Its "merge click" gate is met by step 4.

### 2.4 How the UI session and the risk work join without collisions

- **UI.** After step 6, the UI session branches from `main`, takes `ui-review/repair`'s `apps/qmx-ui` as a whole (it replaces the 86-file 10-01 placeholder on the code line), and leaves `tools/ui_factory`, `.grok/` and the two CI workflow edits behind (factory leftovers). After that, UI PRs touch only `apps/qmx-ui/`. Backend PRs never touch it (the build plan already forbids it). The only shared surface is the REST and SSE door, so the rule is: a gap the UI finds becomes a one-line backend PR, never a UI-side workaround.
- **Risk, sizing, units, QML.** This is design only so far: `decisions.md`, `seeds.md`, `grounding/01-09`, `HANDOFF.md` in `workroom/risk-lab-2026-10-05/` (agreed items, a baseline "not agreed", and a 10-20 lean the same day reversed in `seeds.md`). No code, no branch, no commits. It joins as a docs PR that copies the markdown into `tracker/risk-sizing/` (leave the 252 MB of CSV price data out). Its future code (rebuilt QML, QMB doors, the unit) lives in the root workspace (`qml/`, `qmb/`, `qmn/`, `packages/`), which no QMA v2 PR touches except QMBH and DEL3. The one shared file to schedule carefully is `qmx-agents/packages/qmx-tools/` (the agent door to those libraries, section 4).
- **Order between them:** converge first (step 6), then UI and the wiring sweep in parallel (they share no files), then the domain doors, then deletions.

## 3. Launch readiness: a usable QMX on this PC

### 3.1 What exists, end to end

| Journey | Built and merged | Gaps (source) |
|---|---|---|
| **Start the app** | `python -m qmx_host start --home ~/.qmx --port 8766` (or `qmb host start` after #122). One process runs chats and workflows. **Proven today:** booted on a throwaway home at port 18766, it wrote its home layout (library, memory, engine, chats, router port), answered with the bearer check (401 without the token), reported running, and stopped cleanly. The doctor route was not read, because the token is in your Windows vault (`qmx/control-token`) and I do not read secrets. Side effect to know: the host creates that vault entry if it is missing; it most likely already existed from the build lanes. | Your real `~/.qmx` has no `settings.toml` and no `claude/` login folder yet. First boot needs `/login` once in `~/.qmx/claude` and your provider keys as `qmx/<provider>` in the vault. Never booted on your real home. |
| **Copilot chats, mixed providers** | Harness, turn call, Surface, router registry, chat-completions lane, account pool, `complete`, registry-generated sub-agents, `delegate` v2 (handles, steer, stop). | Role resolution does not skip a provider whose key is missing (BACKLOG HYG0/RTR4). The provider Test answers "not run" for every chat-completions row (RTR3/RTR4/RTR5). `ops_providers` and `ops_provider_test` are in the catalog but no host read serves them, marked HIGH (RTR1). A disabled provider's sub-agent survives in a chat (RTR6). A Claude-plan copilot reaches Kimi or Qwen only through `delegate`, because the plan router lane was skipped (QUESTIONS). |
| **Run a workflow or template** | 32 templates on the shelf. 10 run and are marked tested on haiku. 22 are drafts that refuse by name. The biggest groups: 8 wait for the trading node and 7 for QMB's agent door; the rest wait for a sandbox, app operations, a risk session, a broker read token, a real Library or the big-table reader (`templates/catalog.py`). The copilot builds a workflow from one line. | Publishing costs two clicks, a permission prompt then the card (TPL2). `templates install` has no `--template <id>` flag (TPL1). A core-plugin skill cannot read files beside its own SKILL.md (TPL2). The run-list change means an app schedule only runs after `POST /api/apps/{id}/enable`, and no screen has that button (RUN1a). |
| **Library** | One store with kinds, marks, as-of reads, sessions as items, parse-first search, `@` references. The host dual-writes into the new store. | The old store is still primary until seven clean nightly diffs (plan Appendix G). The nightly diff trigger is not installed (LIBM). `library_mark` is not served (LIB2). Your real Library holds 16 test items titled remote-flow, and the count grows by one per full test run (section 6). |
| **Mini apps** | Packs load as Claude plugins. Two channels, app artifacts, contracts, profiles. | App tool rows never reach a chat: `qma/harness/tools.py` binds no `app:<id>` rows (APP2a). `packs.materialise` is never called when a pack is published (PACK). App outputs land in `artifacts.db`, not the Library, and a pinned app step fails (APP2a). No Enable button (RUN1a). |
| **Memory** | Hindsight on the PC with built-in search as backup, `@memory`, the memory toolset, summary saved in the background. | First start downloads the embedder and reranker. Peak about 2.2 GB of RAM. A summary save took 42 s in the probe. The "skip what is already built" check is not wired into build steps (MEM). qmx-memory's tests are not in `tools/test_all.py` (MEM). |
| **A screen** | None that talks to the host. The code line's `apps/qmx-ui` (86 files, 10-01) has no backend calls. The UI rebuild (`ui-review/repair`, 339 files) is a design with demo data; it fetches only article files. | The whole wiring: UI-HANDOFF sections 1-3 and 12-16. |

The stack was built and checked by DeepSeek V4.1 Flash, not Opus as the plan says. Each verdict's second line records "DeepSeek V4.1 Flash checked DeepSeek V4.1 Flash. A cross-family review was not run." Treat the first real-home boot as the first independent check.

### 3.2 Must for usable this week

1. **Land the code (section 2.2 steps 1-6).** Without the `rebuild/base` merge, every full test run keeps writing into your real Library.
2. **One wiring-sweep PR** that closes the loose one-liners the build left "outside its Files block". Each is named in BACKLOG with file and owner: serve `app:<id>` rows in `tool_defs`; give `ControlService.app_runtime()` the Library sink and pin/profile; call `packs.materialise` on publish; serve `ops_providers`, `ops_provider_test` and `library_mark`; make the publish card the only ask; let a plugin skill read its own folder; add `--template <id>`; make the row Test run chat-completions rows; skip a provider with a missing key in role resolution; pass the settings registry to sub-agent generation; add qmx-memory to `tools/test_all.py`. About a day for one builder, and a smoke lane per item.
3. **The UI session wires five screens to the door, with demo mode off:** the copilot chat (create with home, send, live stream, approvals, stop), Settings for providers and keys (shows the vault reference and the row Test), the Workflows shelf (templates, install, test run, publish card, enable, runs), the Library (list, search, open), and Apps (list, Enable). Everything else stays "Not connected".
4. **First boot on your real home, about 30 minutes of your time:** `/login` once in `~/.qmx/claude`, add one or two provider keys, then five journeys: a plan chat, a key-provider chat, a `delegate` to a third provider, one runnable template run whose result lands in the Library and is found by search, and a second chat that recalls the first through memory.
5. **Your go to remove the 16 remote-flow items**, after step 1 so they stop coming back.

### 3.3 Later (not needed to start using it)

- The agent door to QMB, QML, the data store and the node (section 4). This is what turns the 22 draft templates on. The smallest useful slice, the host loading your recorded datasets so the four data tools return bars, could join the wiring sweep if you want research on real data this week.
- DEL2 and DEL3 (about 114,000 lines of old code). Safe after #122. Better done after the first real boot, so a regression shows against a known-good start.
- The server phase (nine PRs) and DEL1/DEL4 after it.
- Plan Appendix G items: the desktop shell, multimodal and file references, the browser pack, the Lab program, the Library cut-over, standing copilot loops, session fork and replay.
- One uv workspace (section 6).

## 4. The two-part architecture, checked against the code

**Your picture:** a human-facing half (agents, copilots, workflows, mini apps, the UI, the Library) and a non-human half (QMF, QMN, QMB, QML) that does the real work, with agents as the go-between, using the libraries rather than raw Python.

**What the code shows.**

- The folders already split this way. The root uv workspace holds the algo half: `packages/qmf-*` (7), `extensions/qmf-calendar-forex`, `qml`, `qmb`, `qmn`. The `qmx-agents/` workspace holds the human half: 16 packages. Your 10-20 note in `seeds.md` ("algo-facing: QMB, QML, QMF, QMN; human-facing: agents, copilot, workflows, Lab, pods; agents sit between") matches.
- The bridge is one catalog. `qmx_control/catalog.py` describes every operation once (engine AD-61). REST, the model's tool and the workflow node type all come from the same row. That is the right seam.
- The bridge is thin. In the new packages only two import the algo half: `qmx-tools` (610 lines: `qmb.runloop`, `qmb.results`, `qml.protocol`, `qmn.doors.api`, `qmf.data`) and `qmx-broker` (848 lines: `qmf.venue`, reads only). The catalog has 10 domain rows (`data` 4, `backtest` 4, `research` 1, `node` 1) and 7 broker rows. By contrast the old code being deleted (`qma-core`, `qma-daemon`, `qma-wire`, about 114,000 lines) imports `qmf` 374 times.
- **The bridge is empty in the running host. Proven by running it:** `qma/harness/harness.py:403` builds `DomainContext(root=home.root)` with no data store, no datasets, no registered backtest configs, no QML bots and no node. Calling the real domain functions with exactly that construction gives:

  ```text
  list_instruments: OK, result [] (total 0)
  read_bars:   ValueError: No data store configured; inject a host-owned QMF AppendStore
  run_backtest: ValueError: Unknown config_ref; ask the host to register a recorded QMB run configuration
  qml_run:     ValueError: Unknown bot_ref; ask the host to register a QML HostedBot with recorded surfaces
  node_state:  ValueError: No node configured; inject the host's QMN DoorRuntime
  datasets 0 bots 0 backtests 0 node None store None
  ```

  (Script: `domain_probe.py` in this session's scratchpad, run with the merged code's own venv.)
- The templates agree. The ones that need QMB carry `needs: qmb-door`, and their scripts say QMB's doors for agents (`qmb.spec.register`, `qmb.backtest`, `qmb.walk_forward`, `qmb.robustness`) do not exist yet (`templates/b-build-and-prove/scripts/qmb.py`).
- Meanwhile every copilot chat gets Claude Code's own tools, `Bash`, `Edit`, `Write` and `Read` among them (`qma/harness/surface.py:160`, only scheduling and worktree tools are denied). So today an agent that wants a backtest would write and run Python against the libraries. That is the raw-Python path you want to avoid.

**Verdict.** The split is right, and the seam (the catalog) is in the right place. What is missing is the adapters behind it. Today `DomainContext` fails the deletion test: delete it and nothing would reappear in the callers, because nothing real is wired behind it.

**What would make it clean.**

1. Each algo library publishes one deep door: a few plain functions with typed inputs and results, no agent knowledge. QMB: register a sealed strategy, backtest, walk-forward, robustness, compare. QML: validate and compile a strategy, evaluate it on recorded instants. QMF data: list and read. QMN: read status (exists as `qmn.doors.api.read_status`). Your risk session's ruling already says QMB is "a tool agents call but cannot edit".
2. Each door function becomes one catalog row (`binds="domain_fn"`). No other path into the algo half.
3. The host builds the adapters at boot from your real stores, the way it already builds memory and the Library. Tests use a fake adapter. Two adapters make it a real seam.
4. Agents still write Python where Python is the product: QML strategy code is "a fixed contract plus any code inside" (`decisions.md`). They hand that code to the door, and QMB runs it. Workflows never shell into the algo half.
5. Move the money-path barrier out of `qma-core` (the catalog imports it) when DEL3 runs, so the bridge stops depending on the old package.
6. One uv workspace, so the two halves are two folders of one project, not two projects joined by path links.

## 5. Documentation map

### 5.1 Current

| Where | What | Note |
|---|---|---|
| `tracker/qma-v2/` on `plan/agent-system` | HARDENING-PLAN, `architecture/` (workflow engine, Library and data, Lab and pods), UI-HANDOFF, rulings file `research/methodology/26`, README | The real design of the agent system. Not on the code line or `main`. README's "Code truth" says `engine/base = 132169c7`; it is now `6b16e461` with everything merged. The plan names Opus builders; this run used DeepSeek. |
| `D:/QMX-worktrees/qma-ship/build/` (off repo) | RESUME, QUESTIONS-FOR-OPERATOR, BACKLOG (207 rows), IDEAS (78), lows (218), `decisions.tsv`, `ledger.tsv`, `review/` | Live. RESUME still says "nothing merged"; all 42 merged on 10-21. Your rule is that research lives in the repo; this store is not in it. |
| Template READMEs in `qmx-engine/templates/*/` | 37 files, 10-20 and 10-21 | Current. |
| `workroom/risk-lab-2026-10-05/` (git-ignored) | Risk, sizing, unit and QML decisions; seeds | Current thinking, in no branch. |

### 5.2 Stale or contradictory

| Where | Problem |
|---|---|
| `CLAUDE.md` on the code line (10-01) and on `main` | Says implementation ships only through the factory lanes to `integration`. The QMA v2 section exists only as an uncommitted edit in your main checkout. Your global CLAUDE.md says the factory is retired. |
| `docs/AGENTS.md` (10-05) | "QMF V1 Agent Entry Point". Calls the daemon plus `qma-core`/`qma-wire` the ratified agent system and the factory the only way to build. Contradicts QMA v2 throughout. On `main` it differs again (one of the 17 conflicts). |
| `docs/components/qma-core.md`, `qma-daemon.md`, `qma-wire.md`, `docs/contracts/ct-40-*` | Describe code DEL2 and DEL3 delete. Plan DOC-CHANGES row 44 counts 34 pages that name the daemon. |
| `docs/` as a whole (165 files, last 10-06) | No page for the new host, engine, harness, router, Library, memory or tools. |
| Package READMEs | None in `qma-harness`, `qmx-engine`, `qmx-host`, `qmx-router`, `qmx-library`, `qmx-memory` (all new), nor in `qma-core`, `qma-daemon`, `qma-wire`, `qmx-ledger`. `qmx-agents/packages/qmx-agents/README.md` (10-08) describes the runtime DEL1 deletes. QMF package READMEs date from 08-21 to 09-01. |
| `docs/` QMF, QML, node pages | `main`'s versions (workbench, CONNECT, 09-14 to 09-27) are newer than the code line's. Nine of the 17 conflicts. |
| `_docwork/` | Documentation-factory working state. Deleted on the code line, edited on `main`. |
| `_bmad-output/` (574 files on the code line; more on `main`), `rebuild/` (P01-P24 program, done), `adws/` and `queue/` (factory drivers), `tracker/*.md` outside `qma-v2` (08-30), `workroom/` checkpoints | History. Several still read as instructions (BMad epics 40-52 for QMA through the factory). |
| Two backlogs | `tracker/qma-v2/BACKLOG.md` (your words, 10-18) and the build store's BACKLOG (program bugs). Neither points at the other. |
| Your auto-memory index | Lines such as "QMX project state, 23 epics" and "agent SDK effort" describe the factory era. |

### 5.3 Clean-up order

1. Entry points first, because every agent reads them: rewrite `CLAUDE.md` (commit the QMA v2 rules, drop the factory pipeline) and replace `docs/AGENTS.md` with a one-page map: the two halves, where the plan lives, how to start the host, where the backlog is.
2. Land `tracker/qma-v2/` on the trunk (step 5 of 2.2) and correct its README "Code truth" and RESUME.
3. Put a "replaced" banner on the three `qma-*` component pages and CT-40 now; delete them inside DEL2 and DEL3.
4. One short README per new package, written from the architecture spines.
5. Resolve the nine docs conflicts in the converge PR by taking `main`'s newer QMF, QML and node text.
6. Move the build store's BACKLOG, IDEAS, lows and QUESTIONS into `tracker/qma-v2/build/` so they live in the repo; point the two backlogs at each other.
7. Copy the risk work's markdown into `tracker/risk-sizing/` (not the CSV data).
8. Archive `_docwork/`, the factory-era `_bmad-output/` epics, `rebuild/`, `adws/`, `queue/` and old `workroom/` checkpoints under `archive/<date>/` with a SUPERSEDED note (your go, since it removes paths).
9. After DEL2: the 34-page daemon pass.

## 6. Clutter (nothing deleted)

Sizes are from `robocopy /L` (list only) and `du -sm`, on 2026-10-21. Many venvs hold hard links into the uv cache, so a folder total can overstate the space you would actually free.

**Both drives are nearly full: C: has 13 GB free, D: has 15 GB free.** One more builder run with check copies and test homes could fill D:. That makes the clean-up a launch item, not a nice-to-have: removing merged worktrees and the 8 GB of test homes is the cheapest way to get room back.

| Item | Where | Size | Note |
|---|---|---|---|
| Build-run throwaway homes | `D:/QMX-worktrees/qma-ship/build/homes/` (305 folders) | 5.8 GB, 288,000 files (one home is about 600 MB) | Some hold a `claude/` folder that may contain copies of a login. Delete, do not archive. |
| Engine-run throwaway homes | `D:/QMX-worktrees/qma-ship/engine/homes/` (301 folders) | 2.3 GB, 45,000 files | Same. The 10-18 audit counted 192 folders, 2.3 GB. |
| Probe venv | `D:/QMX-worktrees/qma-ship/probe-venv/` | 305 MB | |
| Ship home with the plan login | `D:/QMX-worktrees/qma-ship/home/` | 353 MB | Holds a plan login and key rows. Keep until no lane needs it, then delete. |
| HP-era scratch | `qma-ship/gates.sh`, `hp10-env.sh`, `hp13-*.sh`, `turns.tsv` | tiny | |
| Backup of your `~/.qmx` (10-14) | `qma-ship/backup-qmx-home-20261014T172356Z/` | under 1 MB | Keep until you confirm. |
| Plan copies | loose `*.md` in `D:/QMX-worktrees/` (about 1.6 MB) and the empty folder `tmp.zXDjyNB4L2` | tiny | Copies of the plan made by builders. |
| Hindsight test database | `C:/Users/Mubarak/.pg0/instances/hindsight` | 699 MB | From the memory probe and lanes. Your own `hindsight-embed-hermes` (72 MB) is separate; keep it. |
| Test items in your real Library | `C:/Users/Mubarak/.qmx/library.db` | 16 items, all "remote-flow" | Written by `qmx-remote` `tests/test_remote.py` on every full test run (BACKLOG HIGH). Grew from 14 to 16 since 10-20. The guard that stops it is on `rebuild/base` (commits `76977668`, `0ec8a692`), not on `engine/base`. |
| Worktrees | 191 linked plus a second clone | about 230 GB apparent (bld-* 65 GB, eng-* 27 GB, qma-hp* 24 GB, p15-p23 22 GB, chk-* 9 GB, the rest smaller). Hard links into the uv cache are counted once per worktree, so the real share is lower: all of D: holds 134 GB in use. | 142 hold a root `.venv`, 170 a `qmx-agents/.venv`, 4 a `node_modules`. Remove with `git worktree remove`, never by deleting folders. |
| Archived worktrees | `D:/QMX-worktrees-archive/` (34) | 29 GB apparent | Two hold uncommitted old-factory edits (1.3). |
| Check copies | `D:/Temp/` (32 detached) | 42 GB apparent | |
| Second clone | `D:/QMX-worktrees/p16a-repository` + `p16a-deletion-plan` | small | Head merged. |
| Scratch folders on D: | `D:/QMX-p13-p14-scratch`, `QMX-p17-p19-scratch`, `QMX-p18-scratch`, `p18-tmp`, `tmp`, `tmp-qma`, loose `tmp-*.md` and `tmp_*.py` at `D:/` | not measured | |
| Factory leftovers in the repo | `adws/` (50 files), `queue/`, `_bmad/` factory skills, `tools/ui_factory` and `.grok/` (on the UI branch), the root `pyproject.toml` still named "sssf-project" | | Plan Appendix G: "One uv workspace, adws/, queue/ and 2.7 GB of test homes", waiting for your go. |
| Two Python workspaces | root `pyproject.toml` + `uv.lock` (QMF, QML, QMB, QMN) and `qmx-agents/pyproject.toml` + `uv.lock` (16 packages, path links into the root) | | Every run syncs twice; every package that crosses the line edits two lockfiles. |
| Old Codex worktrees | `C:/Users/Mubarak/.codex/worktrees/*` (5) | not measured | Retired factory. |
| One old stash | `stash@{0}` (08-23, factory-recovery epic-007) | | |
| Risk-lab price data | `workroom/risk-lab-2026-10-05/data/` | 252 MB | Not clutter, but not in git either. Decide where data lives (plan Appendix G, the data study). |

## Proposed order for the coming shipping session

1. **You, 15 minutes:** push `ui-review/repair` as a backup; merge #122; close #25; say go on the converge. Also say go on removing the merged `bld-*`, `chk-*`, `eng-*` and `D:/Temp` check worktrees and the two test-home folders, because both drives are nearly full and the session needs room to build.
2. **Converge (one builder, half a day):** `rebuild/base` and `plan/agent-system` into `engine/base` (both clean), then one PR into `main` with the 17 document conflicts resolved by the rule in 2.2. You land it with a merge commit. Protect `main`. Tag it.
3. **First boot on a throwaway home from `main`** (the coordinator), then on your real home (you: `/login`, keys). Remove the 16 test items on your go.
4. **In parallel, sharing no files:**
   - the wiring-sweep PR (backend, about a day);
   - the UI session: take the rebuild's `apps/qmx-ui`, wire chat, Settings providers, Workflows shelf, Library, Apps, demo mode off.
5. **Five journeys on your real home** (3.2 item 4). Tag `usable-<date>` when they pass. From here you use it.
6. **Docs entry points** (5.3 steps 1-4), one small PR, any time after step 2.
7. **DEL2, then DEL3**, on `main`, after the usable tag.
8. **The agent door to QMB, QML, data and the node** (section 4), planned with the risk and QML session, since that session owns what the door must carry.
9. **Clean-up on your go:** delete merged branches and worktrees, the test homes, the probe venv, the Hindsight test database; archive the factory folders; one uv workspace.
10. **Later:** your server step, then the nine server PRs, DEL1 and DEL4.
