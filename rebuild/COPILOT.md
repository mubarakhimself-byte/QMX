# QMX Copilot: modes, skills, hooks and artifacts

Status: proposed by Claude on 2026-10-09, from two studies:
- `research/bmad-study.md`: BMAD v6.11 (BMM, the CIS suite, TEA, BMad Builder)
- `research/skills-ecosystem.md`: Wayfinder and the Pocock skills, Anthropic Agent Skills, superpowers, Spec Kit, and the modes in Claude Code, Codex, Cursor, Roo and Amp

It builds on `DESIGN.md` §5 (agent core), §7 (mini apps) and §8 (one API). The decisions in §9 are made with Claude's recommendation; the operator can override any of them.

## 1. The idea in one paragraph

Three layers, each with one job:
- **Modes** set what the Copilot is *allowed* to do right now.
- **Skills** hold *how* to do a task well: steps, checks, examples.
- **Hooks** hold the rules that must *never* be skipped, in code, not in prompts.

Everything the Copilot produces is a typed **artifact** that appears in the UI, never only in chat text. Every piece of work leaves an append-only **session log**, so it can be resumed, audited or re-run.

## 2. Modes

| Mode | For | Can do | Stops for approval | Default model |
|---|---|---|---|---|
| **Ask** | quick questions, status, "where is X" | read only: catalog, docs, data previews, job status, logs, web | nothing (it can't write) | fast |
| **Plan** | turning an idea into an approved Brief; research; mapping a big effort | Ask + research sub-agents + writing Brief and plan artifacts only | ends with a card: "Approve and Build / Approve and Run / Keep planning" | standard (deep for synthesis) |
| **Build** | creating or editing workflows, mini apps and skills; fixing broken ones (debug is a pinned skill here) | Plan + writing drafts, sandbox runs, tests, previews | publish, install, grant, delete, network allow-list changes | standard (deep for diagnosis) |
| **Run** | launching, watching, steering, cancelling and scheduling long jobs | Ask + background tasks, schedules, compute targets | spend over budget, new schedules, targets outside the allow-list, paper-account actions | fast to watch, standard to brief |
| **Review** | judging results, diffs and app health; a sceptical second opinion | read + evaluation tools + an independent reviewer sub-agent | nothing (it doesn't write except verdicts) | deep |

- Modes are a setting inside a session, saved with it.
- **Switching:** a mode picker by the chat box, Shift+Tab, `/ask` `/plan` `/build` `/run` `/review`, or a suggestion chip from the Copilot.
- **The Copilot can always lower its own mode, but raising it always needs the operator's click.**
- Live trading has no tool in any mode. Orders are proposed and signed in Portfolio (DESIGN §5.7).
- **Stance** (from BMad Builder). Per task the operator can choose:
  - *do it for me*: minimal questions
  - *pair with me*: confirms each step
  - *coach me*: explains as it goes

  The default is *do it for me*.

## 3. The day-to-day stories (what the operator actually does)

| Story | Mode path | Skills | Produces (shows in UI as) |
|---|---|---|---|
| "Make a workflow that…" | Plan → Build → Run | shape-idea → build-workflow → launch-long-run | Brief card → graph in the Lab editor → run in Activity |
| "Build me an app that…" | Plan → Build | shape-idea → build-mini-app | Brief → app preview tab → road-to-live track on Apps |
| "Change this app" (from inside the app) | Build (that app only) | build-mini-app (change branch) | diff card → new version on the road |
| "Run this overnight and tell me in the morning" | Run → Review | launch-long-run → brief-results | job in Activity (where it runs, cost) → morning brief in Library |
| "Is this strategy idea any good?" | Plan → Review | research-strategy (uses the idea-technique catalog) | research brief + quick backtest → verdict card |
| "What happened with last night's runs?" | Review | brief-results | decision-ready brief with links |
| "This app stopped / is broken" | Build | fix-broken-app | diagnosis card → fix as a new version |
| "Connect my IC Markets account / a data source" | Build | connect-source | secure form (Credential Manager) → probe result card |
| "Do this every Monday" | Run | schedule-routine | schedule card (approval) → entry on Home |
| Quick question | Ask | none, or explain-plainly | answer |
| "This is huge, where do we start?" | Plan | wayfind-effort | decision map in Library; one card resolved per session |
| "Remember how we just did that" | Build | capture-skill | skill draft with tests → approval |

## 4. Skill catalogue (13 to start)

Each skill is an Agent Skills folder: `SKILL.md`, optional data and scripts, and a `customize.toml` with UI-editable knobs (borrowed from BMAD). Skills only *expose* tools the session is already allowed to use (hook H2).

| Skill | Trigger | Borrows from |
|---|---|---|
| `copilot-guide` | "which mode or skill fits this?" Reads the skill registry and existing artifacts, then names **one** next step | BMAD `bmad-help` + Pocock router |
| `shape-idea` | any build or change request without an approved Brief. Classifies Spike / Bounded / Architectural; short question rounds, each with a recommended answer; writes the Brief with success checks and **Always / Ask first / Never** limits; the goal is locked after approval | superpowers, grilling, BMAD spec locking |
| `wayfind-effort` | big efforts: a decision map of cards, one resolved per session | Wayfinder |
| `build-workflow` | from Brief to graph draft → validate → dry run → publish request | Spec Kit build path |
| `build-mini-app` | from Brief to app scaffold → sandbox run → contract tests → preview → install request; also the change-request branch | BMad Builder (six phases + lint gate) |
| `fix-broken-app` | something broken: read logs, evidence and breaker reason, reproduce, fix as a new version, prove with a test | Spec Kit bug path, superpowers debugging |
| `research-strategy` | assess a trading idea. Separates generating ideas from narrowing them down, and uses technique catalogs kept as data files (design thinking, problem solving, first principles) | BMAD CIS |
| `launch-long-run` | start, place and budget a background job, then hand control back | Deep Agents background-task guidance |
| `brief-results` | decision-ready summary of runs, backtests and routines: verdict first, evidence linked | Spec Kit verdicts |
| `connect-source` | brokers and data sources through the secure form; demo first; never order-capable access | wizard |
| `schedule-routine` | turn a repeated task into a schedule (needs approval) | loop-me |
| `explain-plainly` | re-explain in plain words with QMX terms | wait-what |
| `capture-skill` | turn a repeated procedure into a new skill draft with trigger tests | BMad Builder + Anthropic skill guidance |

Writing these skills is Claude's job with the operator (P20), one at a time, with intent.

## 5. Hooks (LangChain middleware; in code, never optional)

| Hook | Rule |
|---|---|
| ModeGate | tools outside the current mode are invisible and refused; raising the mode needs approval |
| GrantIntersection | a skill's tools = its listed tools ∩ the session's grants ∩ the mode. A skill never grants anything |
| MoneyPathFence | order, sizing and live-binding tools are refused with no override (DESIGN §12 item 3) |
| SecretsGuard | keys, tokens and account numbers are redacted in chat, tool results and the journal; points to the secure form |
| ApprovalGate | approval cards for publish, install, grant, delete, schedule, spend, off-list compute, paper actions |
| BudgetGuard | per-turn and per-job caps on model calls, tool calls and money; editable in Settings |
| PlanGate | Build tools that write drafts need an approved Brief (spikes write only to scratch) |
| EvidenceBeforeClaims | "done / fixed / passing" without a verification artifact is sent back once, then labelled unverified |
| ArtifactEmitter | every Brief, plan, graph, preview, job, report and verdict is registered and streamed to the UI |
| ReviewLoopCap | review/fix loops stop after 5 rounds and go to the operator (from BMAD) |
| ReturnAfterLaunch | after starting a background job, hand control back; progress comes as events |
| SkillCheck | a build-like request with no Brief pins `shape-idea` (default on, can be turned off in Settings) |
| PhaseBoundary | compaction or handoff only at phase boundaries, never mid-step |
| Resilience | retries and provider fallback; errors come back as messages |
| Audit | mode switches, approvals, tool calls (redacted) and verdicts go to the journal |
| SkillWriteControl | curated skills are read-only; new or edited skills need approval |

Several are already built in P08/P20 (journal, money path, admission, budgets, app hooks). The rest are P24.

## 6. Session log, resume and headless runs (from BMAD)

- **Append-only session log per task** (BMAD's "memlog"): decisions, questions and answers, artifacts, approvals. Rule: *nothing exists until it is a file*. Final documents are rebuilt from the log, so a crash loses nothing.
- **Resume on start:** if an unfinished task with the same run id exists, offer "continue where we left off". Two runs never merge.
- **Headless mode** for overnight or scheduled work: no questions. It ends with a JSON status listing every assumption it made, shown as an "assumptions to confirm" card in the morning.
- **Reviewer findings are triaged by the main agent:** back to the operator, fix the Brief, auto-fix, log for later, or drop. Reviewers' own severity labels are ignored.

## 7. How users build their own things (from BMad Builder)

When the operator says "build me…", Build mode follows six phases:
1. intent
2. classify (utility, simple workflow, complex workflow, mini app)
3. requirements: the Brief
4. draft
5. **lint gate:** automatic checks before saving. Examples:
   - no money-path tool
   - declared capabilities match what the code uses
   - tests exist
   - the manifest is valid
6. quality pass by an independent reviewer

Then it's published to the road to live (DESIGN §7.2).

- **Import and convert:** paste a notebook, script or someone else's strategy, and the Copilot rebuilds it from its intent as a workflow or app.
- Everything a user builds is versioned, hash-addressed and shareable as a bundle.

## 8. What we deliberately don't copy

- Theatrical personas and multi-persona chat as the normal way of talking. Independent parallel reviewers are kept.
- Step files for everything. They're only used for money-path flows.
- A menu after every section, long question rounds before any work, and chains of planning documents nobody reads.

## 9. Decisions (Claude's calls; the operator may override)

1. **Five modes**, keeping Review separate. Its sceptical, deep-model second opinion earns its place on overfitting calls.
2. **Debug is a pinned skill inside Build**, not a sixth mode. Fewer modes for a non-technical operator.
3. **SkillCheck is on by default:** build-like requests start with `shape-idea`. It can be turned off in Settings.
4. **Paper-account actions are allowed in Run behind an approval.** Live trading stays absent.
5. **Models stick per mode** and are editable in Settings, with defaults per tier (DESIGN §5.3 chain).
