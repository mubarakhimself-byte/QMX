# How the factory ships (draft 5, 14 November 2026)

Status: draft, not ratified. It replaces draft 4 of 12 November. It is written from `FACTORY-DESIGN-2026-11-13.md` (Revision 1), its pictures in `FACTORY-DIAGRAMS-2026-11-13.md`, his answers in `FACTORY-CALLS-2026-11-13.md`, and the lead's decisions D-L1 to D-L18 in `BUILD-LOG-2026-11-13.md`, which win where they differ from the design. How a plan is made is in `PLANNING-FUNNEL.md`.

Where this file and the built tools differ, the tools win: `D:/factory/INDEX.toml`, the skills under `D:/factory/skills/`, and the ship kit's `README.md` (`D:/QMX-worktrees/ship-kit/tools/ship/README.md`). Lines marked **Built today:** say where the build has not caught up with the design yet. The section "What is built today" lists every such gap in one place.

## In short

1. **The factory is its own thing.** It is a set of skills, scripts and one index that take his words to merged code. QMX is its first project. It lives in `D:/factory`, and every session and agent reads `D:/factory/INDEX.toml` first.
2. **He talks to one session, the front desk.** It is the only place he is ever asked anything.
3. **Two branches feed the same build.** Planning adds a feature. Auditing improves or removes what exists. A bug goes through one of three doors, by how far it reaches.
4. **Planning has a challenge stage.** A Fable agent writes in one sentence what he really asks for, sketches the simplest path that proves it, sets a PR budget, and sorts every idea into CORE, LATER or DROP. It may say no.
5. **Auditing starts with what the code is meant to do.** Only after he confirms that does it judge the code against it.
6. **He is asked at a few fixed points:** in planning, at the cut and at plan v1; in an audit, at the intent check and the verdicts; then "go". Each time in plain words, at most four questions, each with a recommendation. "Go" can be given in advance.
7. **After "go", nothing needs him.** One script, the conveyor, starts every agent as a headless Claude Code run, runs every check, and recovers from crashes by reading files, never from an agent's memory.
8. **A checkpoint merges itself** when its review is clean and CI is green for that exact code. GitHub's branch protection enforces the gate, so no script and no agent can merge on red. `main` still moves only by his click.
9. **Everything found and not fixed goes to one backlog.** Nothing leaves it without his yes.
10. **Docs catch up after every merge.** A release is a tag. There is no staging branch.
11. **Several things can run at once.** Reading is free, writing takes a claim, and merging takes turns.

## Words used here

| Word | Meaning |
|---|---|
| Factory | The skills, scripts and index in `D:/factory`, plus the ship kit and CI they drive |
| Project | A codebase the factory ships. QMX is the first. What is true only for QMX lives in `D:/factory/projects/qmx/` |
| Program | One folder holding one piece of work, from his words to merged code |
| Front desk | The one session he starts and talks to |
| Conveyor | `ship chain`, the script that runs every step after his "go" |
| Worker | One headless Claude Code run (`claude -p`) the conveyor starts for one job |
| Slice | One PR's worth of work, built by one builder from one brief |
| Checkpoint | 5 to 8 slices that are reviewed and merged together (the old "stop point") |
| PR budget | A rough PR count agreed before detailed planning, read off a simple sketch of the logic. Scope bends to fit the budget, not the other way round |
| Gate | The required `gate` check on GitHub. A PR into `engine/base` merges only when it is green |

## The factory and where it lives

The factory is independent of QMX (his answer on 13 November). QMX is the first project it ships. A second project would get a second folder under `D:/factory/projects/`, and nothing more is built for one until it exists.

**The index comes first.** `D:/factory/INDEX.toml` is the file every session and every worker reads before anything else. It holds:

- `[where]`: where the truth lives (the project profile, his rulings and memory, the project rules, the code standards, the records, the contract, this method);
- `[[principles]]`: one line each, with the paragraph that explains it;
- `[[phases]]`: one row per phase or stage, with its plain-word triggers, its skill or script, what it reads and writes, its gate and what comes next;
- `[[loops]]`: every place the factory can go round, with its exit and the number of rounds after which it stops and asks him.

Each skill and worker prompt opens with "Read `D:/factory/INDEX.toml`; your row is `<phase>`". `check_index.py` fails when a row names a skill, script or file that does not exist, when a `next` points nowhere, when a loop has no exit or no round count, or when a phase id is not a word `ship phase --words` prints.

| What | Where |
|---|---|
| The index, the skills, their prompts, templates and scripts | `D:/factory/` (its own git repo). Each skill is linked into the project's `.claude/skills/` by `install.py` |
| What is true only for QMX | `D:/factory/projects/qmx/`: `project.toml` (repo, target branch, worktree folder, CI workflow, generated files, transcript folders, worker pool, model per seat), `PROJECT-RULES.md`, `REVIEW.md` |
| Shared funnel scripts | `D:/factory/skills/factory-core/scripts/` (`check_chain.py`, `check_plan.py`, `chain_packet.py`, `his_words.py`, `check_index.py`, `resume.py`) |
| The conveyor and the gates | the ship kit, branch `ship/kit`, `D:/QMX-worktrees/ship-kit/tools/ship/` |
| CI code and baselines | the QMX repo: `.github/workflows/qmx-ci.yml`, `tools/ci/`, `ci/baselines/` |
| Program folders | `D:/QMX-worktrees/plans/<slug>/`, a worktree of branch `plans`, committed and pushed at every phase end |
| The shared records | `D:/QMX-worktrees/plans/_records/`: `BACKLOG.tsv`, `REMOVED.md`, `PREFIXES.md`, `CLAIMS.tsv` |
| Machine-wide locks | `D:/factory/run/` (not in git) |
| Code standards | the QMX repo, `conventions/standards/`, written after the first audit derives them |
| The UI contract | the QMX repo, `contracts/`, generated from the code and checked by CI |
| His research and these method notes | `tracker/` on `main` |

Skills name no QMX path. They read `{PROJECT.*}` values from `project.toml`. Planning writes nothing in the main checkout.

Rule of thumb for a new script: it runs in CI, so it goes in `tools/ci`; it drives a run, so it goes in the ship kit; it belongs to one phase's thinking, so it goes in that skill's `scripts/` folder.

## The front desk

The front desk is the one session he starts. It turns his words, or a backlog row, into the right start: a plan, an audit or a bug door.

- **Routing.** It matches his words against the index's trigger phrases, then runs `ship phase` for the program he means. A new feature goes to planning (`plan-feature`). "Improve, remove, clean up, audit" goes to auditing (`audit-area`). "This is broken" or a backlog row goes to a door. "Continue" or "where are we" reads `ship phase` and the waiting files and says the state in plain words, by ask.
- **Asking.** It alone asks him questions, with AskUserQuestion, at most four a batch, each with a recommendation. It writes his answers in his quoted words with their source.
- **Starting the conveyor.** At his "go" it starts `ship chain` detached, and runs `ship chain --follow` in the background so it wakes when something waits on him.
- **"Continue".** It fires only on a program word or a pipeline phrase, never on a bare "continue" in an unrelated session. It answers what waits on him, restarts a dead conveyor with `ship chain --resume`, or says the conveyor is running and starts nothing.
- **He sees** one line at the start: what it understood, which branch, which folder.

**Built today:** the `factory` skill is the front desk, and `route.py` routes his words by the index. Until `ship backlog` exists, the mechanical bug door goes to `plan-feature` at light depth. Triage of backlog rows arrives with U34.

## Two branches: planning and auditing

Both branches end in a program folder that the same review, build, checkpoint review and merge consume. Both are run by the front desk as the lead. Stage agents are Opus 5.5 at high effort, except the Fable seats named below.

### Planning adds a feature

Planning is the funnel in `PLANNING-FUNNEL.md`: expand, ground, challenge and the cut, self-annealing, technical lens, technical self-annealing, handoff. It removes ambiguity until any model could build the work. `check_chain.py --stage <stage>` must pass after each stage, and `check_plan.py` at handoff. The output is a program folder with `PROGRAM.yaml` (version 2), `SCOPE.md`, `CHALLENGE.md`, `PLAN.md`, `arch/ARCH.md` with `## Operations` and `## Interfaces`, `SLICES.md`, the briefs and their chain packets.

### Auditing improves or removes what exists

His model: "You can't just audit without knowing what something is meant to be doing." So an audit first recovers and confirms what an area is **meant** to do, then judges what is **there** against it. It judges as a senior engineer leading engineers would, and never deletes without knowing why and what replaces it.

The unit is one area (a package or app plus its seams) or a cluster of areas. His main areas: QMB, QML, QMA, QMF, the Library, the mini apps and workflows, and the DevOps layer of each.

| # | Stage | Who | What comes out |
|---|---|---|---|
| 1 | Census | script, `census.py` | `CENSUS.md`: size, largest files, tests, quality rows, routes, registries, the parts (one reader each), and the intent sources: merged PRs with their descriptions, plans and decisions, docs (as claims), his own turns, journeys |
| 2 | Intent | Opus, role `audit-intent` | `INTENT.md`: "it should ..." lines (`N1`, `N2`...) each with sources, and the ambiguities with plain-word choices and a recommendation. It reads the intent sources only, never the code |
| 3 | Intent check | him, at the front desk | A short explainer page and at most four plain questions a batch, none about code. His answers settle the `N` lines. `ship gate intent` records his yes |
| 4 | Quality | a probe script, then one Opus reader per part | `readers/`, then `FINDINGS.tsv`. Six lenses: does it deliver the intent, tests that cannot fail, architecture, maintainability and standards, operations, the UI surface. "This is fine" is a welcome answer. There is no quota |
| 5 | Judgement | one Fable agent, then an Opus screen | `AUDIT.md`: the area on one page with two diagrams, a verdict per part (keep, improve, remove, ask him, wait), what replaces each removal, the cut against a PR budget, the standards found |
| 6 | Verdicts | him, at the front desk | The verdicts page, and only the questions he can answer. `ship gate verdicts` records his yes |
| 7 | Handoff by door | script or light funnel | Briefs, or a hand-off row for planning |

If he is away at stage 3, stage 4 starts on the `N` lines that no ambiguity blocks.

**The probe.** `probe_tests.py` runs once per package root. It swaps every package name a test calls, first with `None`, then with a distinct sentinel. A test that passes under both swaps is `cannot-fail`. Each test has its own time limit, and the checkout must be clean afterwards (D-L18).

**Who decides a removal.** He often cannot tell what code does, so he is never asked to judge code (his H10 answer).

| The removal | Who decides | What he gets |
|---|---|---|
| Changes nothing he can see or use: dead code, duplicates, old paths nothing calls, tests that cannot fail, code nobody asked for and nobody uses | Fable, logged as "Fable decided X because Y" | One plain line each: what it was, why it goes, what replaces it, "you will notice nothing" |
| Takes away something he can see, use or was promised | Him | A plain question with a recommendation |
| Touches a fixed line (money, exits, the kill switch, keys, promotion to live) or data he owns on disk | Him | The same, with what could go wrong |

A fresh Opus screen then reads Fable's list and writes only `AUDIT-SCREEN.md`, one line per call. The lead runs `apply_screen.py`, which moves any hidden product call to him. A row marked `one_way: yes` can never be decided by Fable, and is never a mechanical door.

**The challenge runs inside the judgement.** A restructure or a decoupling (for example, moving the mini apps and workflows out of QMX) is CORE only when it names a measure: which number improves, from what to what, and the evidence. "It would be cleaner" is not a measure.

**Code standards** are derived, then confirmed. The first audit writes down what the code already does consistently and where packages disagree. Fable picks one way for each disagreement. He confirms only the ones that are product rules. They are then written into the repo as one rule per file, and a rule that a machine can check becomes a lint or a script.

**One removal mechanism for both branches.** Planning removes code with `funnel-subtract` on the area a plan touches. An audit uses the same skill on a whole area (`--scope area`). Both use the same `X` row (with `Replaced by:` and a plain-words line), the same `REMOVED.md` ledger, the same `remove` slice kind, the same proof that nothing still calls the thing (`callers.py`, which fails closed and lists what it cannot see), and the same decider rule.

### How the branches hand work to each other

Either branch can leave a row in the backlog for the other. He says yes before it is picked up. The row points at the folder that holds the context, so nothing is retold from memory.

| Crossing | When | How |
|---|---|---|
| Audit to plan | A finding is design-level, or a feature is missing | A backlog row of source `handoff`, door `design`. Planning starts with `inputs.audit` set; expand reads `INTENT.md`, `AUDIT.md` and his approval, and ground starts from the audit's facts and reruns them |
| Plan to audit | Grounding shows the area is not fit to build on | The planner proposes "audit this area first" at the cut. A scoped audit runs stages 1 to 5 on just those paths, and its results join the plan's ground |
| LATER to later checkpoints | The last CORE checkpoint has merged | The LATER briefs are written then, on the new tip, inside the LATER budget |
| Review to planner | A builder or reader says the plan itself is wrong (`BLOCKED chain`) | `notes/CHAIN-ISSUES.md`, shown in the checkpoint's map. A mechanical one goes into the fix batch; a product call waits on him |

A row that has crossed once and wants to cross back goes to him, so the branches cannot bounce work between them.

## Bugs: the three doors

| Door | The test | The path |
|---|---|---|
| Mechanical | One obvious fix, nothing he can see changes, no fixed line | A sweep program: briefs from `sweep_briefs.py`, plan review by scripts plus one grounding reader, build, a light checkpoint review, merge |
| Contained | One area, behaviour changes, the blast radius is known | A light funnel: ground, annealing lenses 1 to 4 and 7, an element index, handoff. The challenge is one paragraph |
| Design | Crosses areas, touches a fixed line, or needs a product call | The full funnel, challenge included |

When the door is unclear, one Opus agent proposes it with the `blast-radius` lens. He says yes before any row is pulled.

## The one backlog

Everything the factory finds and does not fix becomes a row in `D:/QMX-worktrees/plans/_records/BACKLOG.tsv`, rendered to `BACKLOG.md` for him.

- **Columns:** `id` (`B-<n>`, never reused), `source`, `what`, `where`, `first_seen`, `program`, `touches` (a fixed line or none), `door` (`mechanical`, `contained`, `design` or `triage`), `status`, `hops`.
- **Sources:** CI findings by tool (`ci-vulture`, `ci-skylos`, `ci-mutmut`, `ci-types`), `known-red`, `flaky`, `review` (Pre-existing or Nit findings), `builder` (a builder's `findings.md` line), `parked` (a slice parked when its checkpoint merged), `audit`, `later` (a LATER item), `ui-ask`, `handoff`, `his-ask`.
- **A row ends only two ways:** closed with the commit that fixed it, or dropped in his quoted words.
- **Builders never read the backlog,** so no old finding ever blocks new work. Only the front desk pulls from it, through the three doors, with his yes.
- **One writer at a time.** Every write to the records is one commit on branch `plans`, made under `records.lock`.

**Built today:** the records folder and `BACKLOG.tsv` exist (`ship records init`). The `ship backlog` command and the harvest after each merge (U33) and the CI rows (U32) are not built.

## The challenge

The challenge is stage 2b of planning and runs again inside every audit's judgement. He asked for it on 13 November: an agent that calls him out when he is not clear, filters the noise, and stops a 3-PR idea from becoming 70 PRs. The details are in `PLANNING-FUNNEL.md`. In short:

- **Core sentence:** one checkable sentence of at most 25 words, built from his quoted words, true exactly when the feature works.
- **Simple sketch:** 5 to 10 plain lines for the thinnest path that makes the core sentence true.
- **PR budget:** `core <n>, later <m>, checkpoints <k>`, set first, from the sketch.
- **Verdicts:** every ask and idea is **CORE** (built first; the core is reworked later if it is left out), **LATER** (built after the core is proven, never thrown away) or **DROP** (only with his yes when the item is his).
- **The cut:** he sees the sentence, the sketch and the budget, and answers at most four questions. Growth past the budget later needs his yes, and the challenger is asked why it grew.
- **In the build:** every CORE checkpoint comes before any LATER one. The last CORE checkpoint's done line is the core sentence, and its review must say whether that sentence is true on the real thing. LATER checkpoints start only after that.

## Plan review and his "go"

A fresh pair of eyes checks the plan, or the audit's approved verdicts, before anything is built. Planning and review are close: review judges against his words, `CHALLENGE.md` and the plan.

- **Who.** A `plan-review` worker (Opus, high). It is the one worker allowed subagents, one level deep: four readers (scope, logic, PRs, grounding), started in the foreground in one turn. The scope reader checks that LATER stayed LATER and that the slices fit the budget. The PRs reader checks every brief's `API:` line against the architecture's Interfaces rows. The grounding reader reads every brief against the code at the tip. A sweep program gets the scripts and the grounding reader only.
- **Gate.** `check_chain.py --stage handoff` and `check_plan.py` pass, and `FIXES.md` is empty after one round trip. A short `planner-fix` worker applies the mechanical fixes.
- **Go.** If he gave "go" in advance and the review is clean, within budget and has no question, the conveyor records `gates.go` itself, with his advance quote as the source. Otherwise the front desk asks him the open questions and "go?".

**Built today:** plan review runs as the `plan-review` worker on the conveyor. `plan-feature` hands the program to `ship chain` at the end of planning.

## The conveyor

After "go", one script drives every step. No session starts another session, and no agent coordinates other agents.

```
front desk (his session)
  starts, detached:  ship chain --program <P>
    loop: read files, run the next step, wait for its done-file
      script steps: dispatch, verify_ready, slice_checks, land, trace, merge, docs
      CI steps:     gh workflow run, gh run watch, gh pr checks
      agent steps:  claude -p "<prompt>" --model <role model> --effort high ...
```

- **`ship chain`** is one poll loop (every 20 seconds by default). Each tick it runs `ship phase`, starts at most one thing per activity, and never blocks. It also refreshes `chain.lock`, reads power, network and GitHub, sets or clears `HOLD`, and sleeps until a usage limit resets. Exit codes: 0 finished, 10 waits on him, 11 held by a lock, 1 an error it wrote to WAITS.
- **`ship run`** is the build loop inside it: the old coordinator's rules card as a script.
- **`ship phase`** says what comes next, from files alone: the first matching rule in design section 11.7. Its words are the kit's `WORDS` list, and the index's phase ids match them.
- **`ship chain --follow`** prints one line per change and exits when the conveyor finishes, waits on him or dies. **`--resume-all`** restarts every program whose conveyor died. **`--stop-after X`** stops after a checkpoint merges. **`--install-task`** prints, and with `--install` registers, a Windows task that runs `--resume-all` at logon and every 15 minutes.

### Workers

Every agent is a headless Claude Code run started by `launch.py`, the only place the command line is built.

- **Model and effort are named on every start,** so nothing inherits his session's default. A Fable seat is `--model fable` with `--fallback-model claude-opus-5-5`.
- **Plan login, no API spend.** Never `--bare`, and never `bypassPermissions`.
- **No prompt can hang a run:** `--permission-mode dontAsk --permission-prompts none`.
- **No nesting:** `--disallowedTools Agent` for every role except plan review.
- **Boxed in** (D-L9 to D-L11):
  - `--setting-sources project,local` and `--strict-mcp-config` with no servers, so none of his user settings, hooks, plugins or CLAUDE.md load;
  - an environment allow-list (PATH, the Windows basics, `GIT_*`, `UV_*`, `SHIP_*`), so API keys never reach a worker;
  - a narrow command allow-list per role: test, lint and type commands through `uv run --no-sync`, and the kit's `timed` wrapper, with no bare `python` or `git`;
  - the kit's write-guard hook on Write, Edit and Bash. It refuses writes outside the worker's own worktree and evidence folder, any git that writes elsewhere, any force push or push to another branch, and any command naming the main checkout, `~/.claude` or the Windows credential store. It fails closed: any error refuses.
- **Each run has a session id and a name** (`<role>: <program> <id>`), recorded in `workers/<id>/`, so any transcript can be opened with `claude --resume`.
- **The reply contract.** The last non-blank line of the reply is `READY <sha>`, `BLOCKED <reason>`, `DONE <path>` or `WAITS <path>`. Anything else is `nocontract`.

| Role | Model | Job |
|---|---|---|
| `builder`, `fixer` | Opus, high | Build one slice, or fix it after a red check |
| `reader`, `grounding` | Opus, high | Read one part of a checkpoint, or the briefs against the code |
| `fault-reader` | Fable, high | The fault walk on a checkpoint that touches exits, brakes, the kill switch or money |
| `verdict` | Opus, high | Write the checkpoint's one verdict |
| `plan-review` | Opus, high | Review the plan, with four readers one level deep |
| `planner-fix`, `later-handoff`, `sweep-handoff` | Opus, high | Apply review fixes; write LATER briefs; write a sweep's briefs |
| `challenger`, `answer-linker`, `audit-judge` | Fable, high | The challenge; technical decisions; the audit's judgement |
| `audit-intent`, `audit-reader`, `audit-screen` | Opus, high | The audit's intent, quality readers and screen |
| `docs` | Opus, high | Edit the docs a merge named |

### Recovery is a script

Every step writes a file when it finishes, so the conveyor picks up at the first step with no file. Nothing depends on an agent remembering.

| Event | What the conveyor does |
|---|---|
| It is killed or the laptop restarts | `--resume`: the dead `chain.lock` is taken over, `ship recover` saves leftovers as a patch, resets to the last pushed commit and marks seats dead, and it carries on |
| A second conveyor starts on the same program | Refused while `chain.lock` holds a live process |
| A worker returns no contract line, crashes or times out | Restart. Its third death parks the slice for him (D-L12) |
| A usage limit | A restart, never an attempt. It records the reset time and sleeps until then. A limit needs an error ending as well as the words (D-L12) |
| A worker runs past its time limit with no push and no heartbeat | Only that worker is stopped, recovered and restarted |
| Power on battery, or no internet, or no GitHub | `HOLD`: nothing new starts and nothing counts as a failed attempt. Commands that cannot reach GitHub exit 3, which means "try again" |
| A CI run sits queued | It waits up to 12 hours, once more, then writes a WAITS line with the run's link |
| Something truly needs him | A line in `notes/WAITS-ON-YOU.md`. Everything that does not depend on it goes on |
| Every step is done | `run_report`, `teardown`, claims released, the final note |

Kills are exact: the conveyor records each child's process id and creation time and kills only on an exact match. A lock older than the last boot is stale (D-L14).

## Build: the flow of one slice

There is no AI reviewer per slice. Machine checks gate each slice; all AI review happens at checkpoints.

1. **Arm** (once per program). `init`, `preflight`, `ship facts --tip` (every brief's facts rerun at today's tip), and `ship claims claim` (the program's files). Arming without `gates.go` is refused.
2. **Dispatch.** It refuses a slice whose files overlap a held slice, a slice two checkpoints ahead, or a pre-build slice whose files overlap the open checkpoint. It reruns the brief's facts and the SAFETY fact on the first attempt and creates the worktree.
3. **Build.** An Opus builder reads its brief, chain packet, `PROJECT-RULES.md` and `facts.log`. It writes the tests first, builds in small pushed commits, runs the fast checks, writes its evidence and its PR body (`pr.md`), and replies `READY <sha>` or `BLOCKED <reason>`. It never waits on a long check.
4. **Verify ready.** The remote equals the sha, the sha descends from the parent, the diff is not empty, every evidence file ends with its `END` line, `pr.md` holds its `TRACE:` line and no credit line, and the changed files stay inside the brief. Then it opens the PR.
5. **Slice checks.** Lint, types, the touched tests, the parent rule for the slice's kind, Vulture and Skylos with no new finding in the slice's files, the SAFETY fact at the head, and the Linux slice run on GitHub.
6. **Red** goes to a fresh fixer once. A second red parks the slice.
7. **Land.** Each green slice is squashed onto the build branch in dependency order, one landing at a time. A rebase that changes the slice sends it back to its checks.

**Slice kinds** (the `kind` column in `SLICES.md`) set the parent rule:

| Kind | What it is | Parent rule |
|---|---|---|
| `feature` | New behaviour | Each new test fails at the parent on an assertion and passes at the head |
| `pin` | A photo of today's behaviour before a change | Each new test passes at the parent and the head, and fails when its subject returns nothing |
| `refactor` | Same behaviour, better shape | The pin tests it depends on stay green |
| `remove` | Delete code | No callers are left, and `Replaced by:` is filled |
| `docs` | Docs only | Docs lint |

**Built today:** the template's `kind` column exists. The parent rule by kind in `slice_checks` is U29 and is not built, so every slice follows the `feature` rule for now.

**What every brief carries:** the goal, the files it may touch, facts about the code (each a command plus its expected output), the code to read first, what it must do with real values, the tests with exact expected values, what it must not do (including removed rows on its files), its edge cases, the SAFETY fact, the done line with its `Operations:` line, its kind, and the whole merge request: title, plain words, `TRACE: <slice> -> <plan ids> -> <ask>`, the door and blast radius, `DOC:` lines, and `API:` (the Interfaces rows it implements, or `none`).

## Checkpoints and review

When a checkpoint is built, `ship run` writes `notes/stop-<X>.json` and the conveyor starts its review while builders pre-build the next checkpoint on files the review cannot touch.

1. **The deep run** on GitHub for the exact tip: the whole suite on Linux and Windows, lint, types, Vulture, Skylos, mutmut on changed functions. A summary job always writes `summary.json`. A run on the laptop stands in only when GitHub cannot run it.
2. **The map.** `ship trace --stop X` writes `stop-review/X/MAP.md`: per ask, its plan lines, elements and slices; commits with no chain; seams; builder `DECISION` lines; chain issues.
3. **Readers**, as parallel workers: one per architecture element, plus the walks: down the chain (each plan line proven at the tip), up from the code (everything serves an ask), the fixed-line fault walk (Fable on checkpoints that touch exits, brakes, the kill switch or money), and the operations walk. A reader that does not finish is restarted once, then its part is "not read", which blocks.
4. **One verdict.** When the readers and the deep run are done, one `verdict` worker screens the builder decisions, reads `summary.json` and writes `VERDICT: CLEAN` or `BLOCKED`. Every finding is tagged Important, Nit or Pre-existing, with a file, a line and a run as proof. A proved finding on exits, brakes, the kill switch, money or keys is Important.
5. **Blocked: one fix batch.** Every Important becomes a slice of a fix program (`kind: fix`) with a test that fails first. The conveyor builds it, then round 2 judges only whether each finding is fixed and whether the fix adds one, with a full deep run on the fix tip. There is no third round: round 2 still blocked waits on him.
6. **Leftovers.** Pre-existing and Nit findings, and every builder `findings.md` line, become backlog rows.

## Merge, behind the gate

`ship merge X` is a script. No agent runs `gh pr merge`.

1. Take the project's merge lock. One merge into `engine/base` at a time, across every program; the oldest waiter goes next.
2. Check that every BLOCKED verdict has a later CLEAN, and that the build branch tip is the reviewed tip.
3. If `engine/base` moved, merge it into the build branch, regenerate the generated files by script (`uv.lock`, the baselines, the contract dump), and run the deep run on that commit. A real conflict becomes a one-slice fix program.
4. Open or reuse the PR with the body the verdict worker wrote, and wait for the required `gate` check.
5. Merge with a merge commit (one commit per slice, so a bad slice reverts in one step), then prove the reviewed tip is in `engine/base`.
6. Record the merge, move the checkpoint's removal rows to `_records/REMOVED.md`, release the claims, release the merge lock, and start the docs step.

**The gate is GitHub's, not the script's.** `engine/base` is the default branch. Its protection requires the `gate` check, requires the branch to be up to date, allows no force push and no deletion, and binds admins too. A direct push was proved rejected (U18). So nothing can merge on red, whoever tries.

**He sees**, per ask, in his words: "You asked for X. Now true: ... Parked: ... For the next plan: ...". For an audit: lines out, what replaces them, and the proof that nothing changed for him.

## CI levels and the ratchet

One workflow, `.github/workflows/qmx-ci.yml`, on free GitHub runners, and one driver, `tools/ci/qci.py`.

| Level | Starts on | Runs | Who waits |
|---|---|---|---|
| Slice | Push to `slice/**` | Linux: format, lint, types, touched tests, Vulture and Skylos on changed files. Windows slice checks run on the laptop | `ship run`, with a time limit |
| Land | Push to `build/**` | Touched tests on the merged batch, Linux and Windows. Only new reds block | Evidence only; the deep run decides |
| Deep | The conveyor, for an exact commit | The whole suite on both systems, lint, types, Vulture, Skylos against the checkpoint's start, mutmut on changed functions, the node tests. A summary job always runs | The verdict worker reads `summary.json` |
| Gate | A PR into `engine/base` | Passes only when a green deep run exists for the PR's exact head (or the same tree). It reruns nothing. A docs-only PR passes on docs lint | `ship merge` |
| Walk | Nightly schedule | mutmut over one part of the repo at a time. Never a gate; survivors become backlog rows | Nobody |
| Baseline | Push to `baseline/**` | Retakes a baseline | By hand, rarely |
| Release | A `v*` tag | See "Release" below | He reads the verdict |

**The ratchet** is a set of baselines that may only shrink. They live in one place, `ci/baselines/` in the repo: `vulture.txt`, `skylos.txt`, `mutmut.txt`, `pyright.txt`, `known-reds.txt` and `flaky.txt`. Only a new finding blocks. A baseline finding is a backlog row for a later fixer and never blocks, so no agent loops on old findings.

The guard (`tools/ci/guard.py`, D-L17) makes the ratchet hold:

- Rows are compared as counted sets per file. A PR that adds a row outside a `baseline/**` branch fails.
- New suppressions count as growth: `# type: ignore`, `# pyright: ignore`, `# noqa`, `# skylos:` markers, rule downgrades, new excludes and whitelist entries.
- The gate runs trusted code: the gate job checks out the PR's base for `tools/ci` and the growth check, never the PR's own copy.
- At merge, `ship merge` prunes fixed rows in a script commit under the merge lock.

**Flaky tests.** A red test is rerun once in the same shard. It is non-blocking only when it is listed in `ci/baselines/flaky.txt`; a newly flaky test blocks. Each test has a 300-second limit in CI, so a hang becomes a named red. At release, flaky tests block too.

**The mutation rule:** no new survivors in changed code, and the baseline only shrinks. This replaces the old "kill rate never below 68%" floor (his H16, confirmed).

**Built today:** the ship kit still reads its own second set of quality baselines (`quality_dir`) until U17b moves it onto `ci/baselines/`. The kit's CI setting is `local` by default; a program sets `ci = "github"` in its `ship.toml`.

## Docs after merge

Docs catch up after every merge, for both branches, and never hold up code.

- The docs step collects the merged checkpoint's `DOC:` lines, and flags a slice that changed a documented area's code but said `DOC: none`.
- One `docs` worker edits only the docs those lines name, with the code as the truth, stamps each changed claim `verified: <commit>`, and marks a decision record superseded when its code went.
- The result is a small docs-only PR into `engine/base`, which passes the gate on docs lint and merges itself. A docs failure becomes a backlog row.
- An audited area's one-page explanation becomes its component doc. There is no separate sweep of old PRs: areas are documented as they are audited or first touched.

**Built today:** the docs step is U36 and is not built. The conveyor records `skipped` for each checkpoint's docs and moves on.

## Release: a tag

There is no staging branch. A staging branch is a second place where code waits, so every change would be merged and tested twice, and the two would drift. A tag freezes one commit just as well.

- **A release candidate** is a tag `v0.x.y-rc.N` on an `engine/base` commit that passed the gate. CI runs the release level. Then the candidate runs on his demo account on his PC for as long as he sets. Then the real tag, `v0.x.y`.
- **A `release/vN` branch** is cut from its tag only on the day a released version needs a fix while `engine/base` has moved on. The fix lands on `engine/base` first, then is copied across. The branch gets the same protection and gate.
- **The release level, in steps as the pieces exist.** R0 now: the deep run on both systems, a start with no data, the node on a fresh server, every red blocks (the known-reds list does not apply), a release verdict, and a draft GitHub Release with notes built from the merge records. R1 when an installer exists: build and install it once. R2 when the UI is wired: a browser smoke test.
- **The UI** merges into `engine/base` as its own folder, `apps/qmx-desk`, at the design rounds he approves, through the same gate. It is committed on `ui-redesign` today (U41).
- **Deploy** in the factory means only this release and install path. Hosting waits by his word.
- **He makes the tag,** or says "tag it".

**Built today:** the workflow already runs on `v*` tags, and a dry run has passed. The full R0 level (U37) is not built; Skylos at release still times out.

## Several things at once

His answer to H15: building, auditing, planning and reviewing can run at the same time, and the factory must make that safe. **Reading is free, writing takes a claim, and merging takes turns.**

- **Reads run together with no limit:** planning sessions, the audit's census, intent and quality stages, plan and audit reviews, checkpoint readers (each in its own frozen copy of one commit), CI runs and docs PRs.
- **Builds run together when their files differ.** At arm time a program claims its files in `_records/CLAIMS.tsv`. If another live program's claim overlaps, only the slices that touch those files wait, as `blocked-by claim`, which is not a failure. They start after the other program's checkpoint merges, and their facts are rerun on the new code first. Files written by scripts are never claimed; they are regenerated at merge.
- **Plans and audits leave a notice, not a lock.** The front desk tells him when a plan and an audit look at the same area. Every fact is rerun at the current tip before a handoff, so nobody trusts an old read.
- **What takes turns:**

| One at a time | Held by |
|---|---|
| Merging into `engine/base`: the second merger takes the first's code and is deep-tested again | `D:/factory/run/merge-<project>.lock`, oldest waiter first |
| Two programs writing the same file | the claims list |
| Landings on one program's build branch, and one conveyor per program | `<program>/chain.lock` |
| Writes to the shared records | `_records/records.lock` |
| The Fable seat | `D:/factory/run/fable.lock` |
| Headless runs on the laptop | the worker pool, `[pool].workers` in `project.toml` (3 today) |

The quiet clash, where two programs touch different files and still break each other, is caught by the deep run on the merge result.

## Fable seats

Fable stays scarce (his H3 answer: it is costly, the promotion will end, he may downgrade). There are four seats:

| Seat | Role | Where |
|---|---|---|
| The challenger | `challenger` | Planning stage 2b |
| The answer-linker | `answer-linker` | Planning stage 5, one per batch of technical decisions |
| The audit judge | `audit-judge` | The audit's judgement, one per area or cluster |
| The fault walk | `fault-reader` | A checkpoint that touches exits, brakes, the kill switch or money |

- Only one Fable agent runs at a time across the whole machine (`fable.lock`).
- Each seat is one line of settings (`roles/roles.toml` in the kit, which a project profile may override), so turning a seat down to Opus is a one-word change.
- When Fable cannot be started, Opus stands in (`--fallback-model`) and the log says so.
- Every other seat is Opus 5.5 at high effort. Never Sonnet for substance.
- Other models may come later through a proxy inside Claude Code. Such a model is one more `--model` name; the factory stays Claude Code only.

## The loops and where each stops

Every place the factory can go round has an exit and a number of rounds after which it stops and tells him what is still open. The number is a safety valve, never a limit on thinking. The rows live in the index (`[[loops]]`).

| Loop | Exit | Stops after |
|---|---|---|
| Questions to him | Nothing is left that only he can answer | 3 batches of 4; the rest go to `WAITING.md` with what can go on without them |
| Self-annealing rounds | A round raises nothing new and no answer arrived during it | 5 rounds |
| Plan review and the planner | Both checks pass and `FIXES.md` is empty | 1 round trip |
| A slice's fix round | Green | 1 fix round; a second red parks the slice |
| A worker dying | It replies | 3 restarts, then parked |
| Checkpoint fix batch | Round 2 is clean | 2 rounds; no third |
| A reader that does not finish | Its notes end `DONE` | 1 restart, then "not read", which blocks |
| Waiting on CI | The run finishes | 2 long waits |
| Merge when `engine/base` moved | The gate is green on an up-to-date branch | 2 tries, then he is told who keeps merging first |
| Budget growth | He says yes, or scope is cut | Every raise is his |
| CORE then LATER | The LATER budget is used | Bounded by the budget |
| Audit and plan crossing | The row is closed | 1 crossing; a second goes to him |
| The backlog | Fixed, or dropped in his words | Nothing leaves without his yes |
| He changes his mind | The checks pass again from the earliest stage his words touch | His call each time |

## Rules that carry over from draft 4

- Quality comes from the brief and the tests. Scripts run every check and enforce every gate. Agents think and write.
- Every slice names the ask it serves. A slice that serves no ask is a proposal and is built only after his yes. The checkpoint review walks up from the code: a commit with no chain is a blocker.
- Removed means removed. Planned removals reach every builder through its brief and chain packet. A builder that thinks it needs one back replies `BLOCKED chain R-<id>`.
- Agents get lenses and required reply fields, never caps on length or size. "5 to 8 slices" is a guide that warns, never a refusal.
- PRs use body v2 with a `TRACE:` line, signed "Shipped by Mubarak." or not signed. PRs and commits carry no model credit line; the ready check refuses one.
- From the Claude Code team's review flow: `REVIEW.md` is written once per project; every finding is Important, Nit or Pre-existing; Nits never block; a finding that recurs becomes a lint, a script check or a line in `PROJECT-RULES.md`; speed comes from fast recovery (one squashable commit per slice), not from extra gates.

## What is built today

As of 14 November, from the build log and the code.

| Part | State |
|---|---|
| `D:/factory`: home, QMX profile, index, templates v2, the challenge and what follows it, Interfaces in planning, the audit branch (census, intent, readers, probe, callers, judgement, screen, handoff) | Built (S1, S3, S4 and their fix rounds) |
| Ship kit: records, `ship phase`, `ship gate`, launcher and spike, `ship run`, arm checks, `ship trace` and `ship review`, `ship merge`, claims, locks and the worker pool | Built and committed on `ship/kit` |
| `ship chain` with `--follow`, `--resume-all` and the logon task (U11) | In the ship-kit worktree, not yet committed |
| CI: types baseline, Skylos by diff, flaky rerun, summary, guard, gate trims, release dry run; PR #1 merged; branch protection on `engine/base` | Built (C1, its fix round, U18) |
| The front-desk `factory` skill and the headless worker prompts (U13) | Built; the old session skills are retired |
| Chaos suite (U12), one ratchet in the kit (U17b), first real program `ci-green` (U19) | Not built |
| Contract dump (U23), contract diff in the run (U25), UI checks in CI (U39) | Not built; `contracts/` is not on `engine/base` yet |
| Slice kinds in the checks (U29), backlog (U32, U33), triage (U34), nightly walk times (U35), docs step (U36), release R0 (U37) | Not built |
| First audit (U31) and code standards (U30) | Wait on H9 |

Where the build and the design disagree, in one line each:

- `plan-feature` no longer records `notes/SESSIONS.md` or a `planner_session` field (U13).
- The index's `where.removed` points at `tracker/REMOVED.md` in the repo, while `ship merge` moves removal rows to `_records/REMOVED.md`, as the design says.
- The kit's default list of protected branches still names a retired branch; the QMX profile overrides it with `main` and `engine/base`.
- The kit README's section "How the coordinator uses them" describes the old coordinator session; `ship run` and `ship chain` replace it.
- `D:/factory` is a local git repo with no remote until he answers H11b.

## Open for him

1. **H9: how the auditing runs.** Recommendation C: recover intent for every area in one go, so he confirms his picture of the whole of QMX once, then judge and build one cluster at a time. He holds this until morning.
2. **H6: tags only, and a release branch only when needed;** the UI merges into `engine/base` as its own folder at the rounds he approves. Waiting on his yes.
3. **H11b: back up `D:/factory`** to a private GitHub repo on the new account. Recommendation: yes. It holds no keys, and a disk fault would otherwise lose every skill and prompt.
