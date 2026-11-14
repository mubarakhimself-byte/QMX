# Audit branch: grounding (13 November 2026)

Grounding only. Nothing was built, installed or run from a downloaded repo. Agent OS was cloned read-only into the scratchpad (`.../scratchpad/agent-os`, tip `e892e61`, 7 Oct 2026). Line counts and test counts were measured on `origin/engine/base` at `3ae41ffcb` (8 Nov 2026) by two small scripts that read git blobs (scratchpad `loc.py` and `asserts.py`). Evidence levels follow the house scale: 2 = read the line, 3 = walked it, 4 = ran it.

## 0. His ask, in one paragraph

From `HIS-WORDS-2026-11-13.md:45-53` (18:40 and 18:49 UTC). The factory gets **two branches that feed implementation**: planning (new features) and auditing (improving or removing what exists). Auditing is its own phase, not a planning mode, and is "an auditing only plan or auditing only session" that first takes in the code, the architecture and the PRs, then decides. It is judged the way a senior engineer leading several engineers would: does the code serve the intended features as each feature is meant to work; how many tests are false positives ("we are going to discover that most of them are like this"); is the high- and low-level architecture solid and explainable very simply; is it maintainable; are there coding standards (Agent OS by Builder Methods); and the DevOps layer (logging, monitoring, self-recovery, backend operations, database). "Deleting without actually knowing ... what is going to be replaced is also not paramount." Coding and review must say how they interact with audit programs, and every phase must say what connects to the UI. Docs appending belongs somewhere (18:40). He is not technical, so the audit must explain itself simply. At 18:06 he also said the planning-phase skills belong on his machine, not inside QMX (`HIS-WORDS:25-27`).

## 1. Agent OS (Builder Methods)

### What it is today (v3.0, 20 Jan 2026; last commit 7 Oct 2026)

Sources: the repo README and `CHANGELOG.md:13-49`; https://buildermethods.com/agent-os and https://buildermethods.com/agent-os/standards (fetched 13 Nov). The main site (https://buildermethods.com/) is now a coaching and community business and does not mention Agent OS.

- **v3 cut most of the framework.** The changelog says spec writing, task breakdown and orchestration are now "best handled using Plan mode" and frontier models, so "Implementation/orchestration phases retired" (`CHANGELOG.md:21-25`, `:38-41`). The v3 release commit `1be88b0` deleted 6,197 lines, including every default standard (`profiles/default/standards/**`) and every workflow (`implement-tasks`, `orchestrate-tasks`, `verify-spec`, the implementation verifier).
- **What is left is five markdown commands** in `commands/agent-os/` plus three bash scripts:
  - `discover-standards.md` (261 lines): pick an area, read 5 to 10 representative files, find patterns that are "Unusual", "Opinionated", "Tribal" or "Consistent" (`:44-48`), ask the user *why* for each one (`:70-86`), write one short file per standard under `agent-os/standards/<folder>/`, then index it.
  - `index-standards.md` (124): keeps `agent-os/standards/index.yml`, one short description per standard, so an agent reads the index and loads only matching files.
  - `inject-standards.md` (291): pulls matching standards into a conversation, a skill (as `@` references or copied text) or a plan.
  - `shape-spec.md` (267): plan-mode helper that writes `shape.md`, `standards.md` and `references.md` into a spec folder.
  - `plan-product.md` (204): mission, roadmap, tech stack.
  - `scripts/project-install.sh` copies a profile's standards and the commands into a project (`.claude/commands/agent-os`, `:388-389`); `sync-to-profile.sh` copies project standards back to a reusable profile. Profiles inherit through `config.yml`.
- **The shipped profile is nearly empty.** `profiles/default/global/tech-stack.md` (React, Express, Postgres) is the only file. Standards are meant to come from your own code.
- **No audit, review or verification workflow exists in v3.** The site says nothing about one either. The closest is discovering patterns in a legacy codebase.
- **Writing rules for standards** (`discover-standards.md:166-196`, and the standards page): "Every word costs tokens"; lead with the rule; code examples over prose; one concept per file; skip what the code already makes clear.

### What fits QMX

1. **The format: one rule per small file, plus an index an agent reads first.** QMX already has the content but not the shape. `standing/PROJECT-RULES.md` (65 lines) mixes product rules ("Configuration, never caps", `:11`), build rules (`:28-36`) and code traps (`:40-50`: dependency direction AD-21, exits, `make` and `evidence`, money arithmetic, censuses). `conventions/failure-register.md` on `engine/base` is a second source. Splitting these into indexed standards would let a builder, an auditor and a reviewer each load only what touches their files.
2. **discover-standards as an audit step.** Its four tests (unusual, opinionated, tribal, consistent) are a good lens for "are there coding standards?" An audit agent can run it headless over each package and report both the patterns it found and where packages disagree. Disagreement is itself a finding for a 500k-line codebase built by many agents.
3. **The "why" loop.** Asking why before writing a standard matches his "never delete without knowing why". For QMX the why comes from the docs ledger (DEC ids), rulings and the transcripts, and only the residue goes to him (the corpus-first ruling in memory `qmx-qa-phase-design`).
4. **inject-standards into briefs.** The brief template already names skills and principles (`templates/BRIEF.md:113`). An index makes "which standards apply to these files" a lookup the planner (or a script) can do.

### What does not fit

- **Interactive by design.** Every step uses AskUserQuestion and confirms each standard one at a time (`discover-standards.md:7`, `:72-86`). He is non-technical and dictates; a headless version must answer the why from the corpus and batch only real product questions.
- **No content to borrow.** v3 ships no standards. The v2 defaults, recoverable from history, are generic and in places wrong for QMX: v2 `testing/test-writing.md` said "Write Minimal Tests", "Defer Edge Case Testing" and "Mock External Dependencies" (git `7423543^`), which contradicts PROJECT-RULES:33-34 ("Scenario tests first", "A fake is never kinder than the real neighbour").
- **Bash install scripts.** They need Git Bash or WSL on Windows (`project-install.sh` is `#!/bin/bash`, `set -e`). Nothing in them is needed: the commands are plain markdown and can be rewritten as a local skill.
- **Its spec and plan commands overlap the funnel** and add nothing the funnel lacks.

Verdict: borrow the standards format, the index and the discover lens. Rewrite discover as a headless audit step. Skip the rest.

## 2. Skills for an audit

"Headless" means: can it run inside one agent that spawns nothing and asks nobody. All paths are SKILL.md files read today.

### 2.1 Does the code serve the feature (intent against code)

| Skill | Where | What it does | Headless? | What it gives an audit |
|---|---|---|---|---|
| `bmad-testarch-trace` | `QMX/.claude/skills` | Requirements-to-tests matrix and a PASS/CONCERNS/FAIL gate. With no formal requirements it infers "synthetic journeys/requirements" from source (`steps-c/step-01-load-context.md:46`, `:68`, `:86`). | No headless section in its SKILL.md; it is a step-file workflow with a mode menu. Needs a wrapper. | The closest skill to "does the code serve the feature": an oracle (docs, journeys, plan lines) mapped to tests. Its knowledge base is Playwright and Pact heavy. |
| `code-review` (Matt Pocock) | `~/.agents/skills/code-review` | Two parallel axes on a diff since a fixed point: **Standards** (the repo's documented standards plus a Fowler smell baseline, the repo wins) and **Spec** (does the code match the originating spec). | No: spawns two agents and reads an issue tracker. Its two axes run fine inline. | The Standards axis consumes exactly what Agent OS would produce. Built for a diff, not a whole package. |
| `how` | `~/.claude/skills/how` | Senior-engineer onboarding explanation: Overview, Key Concepts, How It Works, Where Things Live, Gotchas. | Spawns explorers and an explainer; the simple path is one pass and runs inline. | The "explain it very simply" deliverable, per area. |
| `why` | `~/.claude/skills/why` | Motivation behind code from git history, PRs and docs, with an epistemics guide. | Spawns investigators. Its code-archaeology source runs inline. | "Know why before deleting": the reason a thing exists. |
| Existing QMX audit templates | `tracker/risk-audit-2026-11-12/SCOPE-AUDIT-*`, `PLAN-INTENT-A/B` | His words against what was built, row by row, with verdicts keep, merge, drop, ask him, wait (`SCOPE-AUDIT:60`). | Yes, already run headless. | A proven house format for intent audits. |

### 2.2 False-positive tests

| Skill | What it does | Headless? | Fit for QMX |
|---|---|---|---|
| `principle-test-behavior-not-implementation` (pstack) | The test: would it still pass if every imported function returned `undefined`? Five shapes: weak assertion, mock-only, self-referential, constant pin, fixture asserts fixture. | Yes (a principle). | Direct fit, but its examples are Jest-style. Needs a Python version. |
| `standing/skills/slice-review` (QMX) | Already turns that test into a runnable Python probe: monkeypatch the subject to return nothing, run the test (`slice-review/SKILL.md:88-89`). | Yes. | The best existing lever. Today it runs on one slice; an audit would run it over a package. |
| mutmut (CI) | Mutation testing: change the code, see whether any test fails. | Script. | Already measured: qmf-core 805 of 2,107 mutants survive (38%), qmf-risk 340 of 605 (56%) (`ci/baselines/mutmut.txt:2-3` on `origin/ci/github`; `tracker/ci/ISSUES-2026-11-12.md:77-78`). qmn not run yet (`:79`). |
| `bmad-testarch-test-review` | Scores test files 0-100 on determinism, isolation, maintainability and performance. Has a real headless mode (`SKILL.md` "Headless mode"; `review_files`, `context_files`). | Yes. | Weak fit. Its checklist assumes Playwright, Jest, Cypress or Vitest (`checklist.md:16-17`) and coverage is out of scope. It does not ask whether a test can fail. |
| `false-green-tests`, `audit-my-app` | Both are **Reticle** skills (`metadata.homepage: https://www.reticle.sh`): they drive a running web app and compare DOM, network and state. | Need the app instrumented with Reticle. | Useful only for the UI, once wired. They do not judge Python backend tests. |
| `bmad-review` verification-gap lens | Would verification fail if the changed behaviour broke where it is used? Three gap shapes: regression, missing adoption, broken verification (`references/lens-verification-gap.md`). | Runs a lens inline when no subagents. | Good second lens on test gaps, but scoped to a change, not a package. |

**A measured fact that shapes this.** A naive "test with no assertion" scan finds almost nothing: of 10,338 test functions on `engine/base`, 59 have no `assert`, `raises` or `assert_*` call (scratchpad `asserts.py`, level 4). So QMX's false greens are not missing assertions. They are tests whose assertions hold whatever the code does, which only mutation testing or the "returns nothing" probe can show. The 27 Aug QA phase found the same: "falsifiability, not red-count, is the quality signal" and "tautological/self-testimony tests" were a systemic defect (memory `qmx-qa-phase-design`).

### 2.3 Architecture: solid, and explainable simply

| Skill | What it does | Headless? | What it gives |
|---|---|---|---|
| `bmad-architecture` | Produces or **validates** an architecture spine of invariants. Brownfield: "investigate before you decide ... ratify the conventions already there" and derive a spine from code. Has `references/headless.md`, a `lint_spine.py` check and a reviewer gate. A whole dimension left silent, including "deployment & environments, infra/provider strategy, operations", is called a failure (Finalize step 1). | Yes (headless reference). The reviewer gate spawns lens agents; it can run sequentially. | The "high-level architecture" deliverable, and a validate mode against the existing spines in `_bmad-output/planning-artifacts/architecture/`. |
| `improve-codebase-architecture` (Matt Pocock) | Scans for **deepening opportunities** (shallow modules, leaky seams, untestable interfaces), weights recent hot spots from `git log`, applies the deletion test, writes an HTML report with before/after diagrams, then grills on one pick. | `disable-model-invocation: true`; an agent cannot call it, and it spawns an explorer and asks the user. Steps 1-2 can be copied into a headless skill. | The "low-level architecture" lens, plus the visual report he prefers (memory `output-as-animated-explainers`). |
| `codebase-design` | Vocabulary: module, interface, depth, seam, adapter, leverage, locality; the deletion test; "one adapter is a hypothetical seam, two is a real one". | Yes. | A shared language so the audit's findings read the same across packages. |
| `domain-modeling` | Keeps `CONTEXT.md` (glossary) and `docs/adr/` current. | Yes when only reading. | "Explain it simply" needs one glossary. QMX's is `docs/glossary.md`, stale (section 4.6). |
| `principle-minimize-reader-load` | Maintainability as reader load: layers to trace and state to hold. "Can a new reader answer 'where does X come from?' ... in under 30 seconds?" | Yes. | A concrete maintainability test per module. |
| `principle-foundational-thinking`, `principle-model-the-domain`, `principle-type-system-discipline` | Data structures first; encode the domain in a structure instead of scattered conditionals; make illegal states unrepresentable. | Yes. | Rubric rows for "is it solid". |
| `engineering:architecture` (plugin) | Writes or evaluates an ADR. | Yes. | Records the keep or replace decision per area. |
| `engineering:tech-debt` (plugin) | Six debt kinds (code, architecture, test, dependency, documentation, infrastructure) and a score `(Impact + Risk) x (6 - Effort)`. | Yes. | A simple ranking he can read. The infrastructure row covers his DevOps ask. |

### 2.4 Removing safely

| Skill | What it does | Headless? | What it gives |
|---|---|---|---|
| `principle-subtract-before-you-add` | Remove first, then build; "Design for observed usage, not speculative edge cases". | Yes. | The audit's default stance. |
| `principle-migrate-callers-then-delete-legacy-apis` | Inventory callers, migrate them, delete the old API in the same wave; "Update tests to assert the new contract, and delete tests that only protect pre-refactor implementation details". | Yes. | The slice shape for replacements. Already in `PROJECT-RULES.md:32`. |
| `blast-radius` | Find what a change breaks beyond the diff; prove the one fact it is safe because of, by running code (evidence levels 1-5). | Yes without step 6 (arena). | The safety proof for each deletion. Already the evidence scale of `qmx-auditor`. |
| `funnel-subtract` (QMX) | Collects can-change candidates (Vulture, Skylos, the deletion test, wrappers, old APIs with callers), justifies each (`Serves`, `Callers`, `Blast radius`, `Frees`, `Decider`), records agreed rows in `REMOVED.md` (`funnel-subtract/SKILL.md` steps 1-5). | Yes. | Already the audit's deletion ledger, but scoped to "the area a plan touches". |
| `bmad-code-review` deletion check | For removed code: "did it carry behavior or a contract that the change neither re-established nor intentionally retired?" (`references/deletion-check.md:5`). | The review spawns layers; the deletion check is one paragraph. | The review-time question for deletion slices. `slice-review/SKILL.md:42` already carries it. |
| poteto-mode Refactoring playbook | "Pin the behavior contract first ... write a characterization test, snapshot, or equivalence harness" (`playbooks/refactoring.md` step 1); prove unchanged behaviour on the real artifact (step 6); "If the diff does not lower reader load somewhere, revert it" (step 7); subtraction commit, then reshape, then cleanup (step 8). | Yes, except the delegated edits. | The exact build shape an "improve" slice needs. See section 6: today's build checks reject it. |
| `simplify` (built-in Claude Code skill) | Reviews changed code for reuse, simplification and efficiency, then applies fixes. | Yes. | A diff tool, not an audit tool. |

### 2.5 DevOps layer

| Skill | What it does | Headless? | What it gives |
|---|---|---|---|
| `bmad-testarch-nfr` | Audits evidence for performance, security, reliability and maintainability; PASS/CONCERNS/FAIL per category (`instructions.md` Overview; steps `04a`-`04d`). Wants evidence: "tests, scans, metrics, logs, monitoring data, CI results". | No headless section; step-file workflow. | The DevOps checklist shape. Its template is web-service flavoured (p95 latency, auth strength). |
| funnel's Operations rule | Every feature gets logging, observability, monitoring, self-recovery and backend operations (`PLANNING-FUNNEL.md:33-40`); the review's operations walk breaks the part and watches it recover (`STOP-REVIEW.md:46`). | Yes. | The audit can reuse the same five questions per area, so audit and planning judge operations alike. |
| `principle-make-operations-idempotent`, `principle-boundary-discipline` | Converge after crashes and retries; guards at system boundaries. | Yes. | Rubric rows for self-recovery and the database layer. |

Nothing read covers the database layer specifically. QMX's stores are append logs, a Library store and journals (for example PR #171 "make the Library store survive torn logs", `release-inventory/MERGED-PRS.md:224`); an audit lens for them would be new.

### 2.6 Docs

| Skill | What it does | Fit |
|---|---|---|
| `documentation-factory` | Builds a decision-ledger knowledge base; modes `transcripts`, `codebase`, `enhance`, `change` (`SKILL.md:41-47`, `:89-100`). `codebase` mode reads the repo and `git log`. Emits a feature inventory. | His own judgement on 12 Nov: "that skill is very different. I don't think it's taking in PRs" (transcript L2795). `FUNNEL-SKILL-PLAN.md` section 4 agrees and reuses only its style rules, `lint_docs.py`, `check_citations.py` and changelog. |
| `bmad-project-context` (and the deprecated `bmad-document-project`, `bmad-generate-project-context`) | A small verified block in `AGENTS.md`: policy, conventions that differ from defaults, pitfalls. Its **audit** intent re-verifies every line and prunes ones whose evidence is gone (`SKILL.md:82`). | Good for the standards block. The deprecation note is a finding in itself: "Generating documentation volume about a codebase made agents worse, not better ... the generated set was stale on arrival" (`bmad-document-project/SKILL.md:9`). |

### 2.7 Interview and judgement (already ground in `CHALLENGER-SKILLS-2026-11-13.md`)

`grilling` (frontier questions with a recommendation each), `bmad-forge-idea`, `bmad-advanced-elicitation`, `bmad-party-mode` and poteto-mode's "No is an acceptable answer" serve the challenger stage. For audits the same rule applies: facts are looked up, only product calls go to him.

### 2.8 Not useful for this audit

- `bmad-deep-recon`: web research for decisions (market, technical, academic). Its research firewall forbids project code as evidence ("Project context ... is inadmissible as evidence", `SKILL.md`, rule 2). Useful only for "what is the standard way to do X" questions.
- `bmad-review` adversarial lens: "requires at least ten concrete findings" (`SKILL.md` line 8). He vetoed quota reviewers on 27 Aug: "agents told to find problems manufacture problems" (memory `qmx-qa-phase-design`, item 3).
- `engineering:code-review` and the official `code-review` plugin: PR-diff reviewers (the plugin posts PR comments through `gh`). Not whole-package audits.

### 2.9 What a headless audit skill set could look like (options, not decisions)

No existing skill audits a whole package against intent, tests, architecture, standards and operations at once. The parts exist. A local audit skill (in `~/.claude/skills`, per his 18:06 word) could compose: `how` (explain) + trace-style oracle mapping (serves the feature?) + the "returns nothing" probe and mutmut survivors (false greens) + `codebase-design` deletion test and `improve-codebase-architecture` steps 1-2 (architecture) + `principle-minimize-reader-load` (maintainability) + an Agent OS style discover pass (standards) + the five operations questions (DevOps) + `blast-radius` and `funnel-subtract` row shape (removals) + `engineering:tech-debt` scoring (ranking). Scripts it could carry: a per-package line and test counter (the two scratchpad scripts), a "returns nothing" probe runner, a callers counter, a docs-drift lister (section 5), and a standards index builder.

## 3. What QMX already has

### 3.1 CI quality tools and baselines (`origin/ci/github` at `9eb140303`, PR #1, not merged)

- `ci/baselines/vulture.txt`: 21 findings at `3ae41ffcb2` (`:1-2`). One is real: `qmn/src/qmn/data/backup_run.py:669` ignores its `remote_root` argument (`ISSUES-2026-11-12.md:74`, T-15).
- `ci/baselines/mutmut.txt`: 1,148 lines; qmf-core 1,302 killed and 805 survived, qmf-risk 265 killed and 340 survived, qmn not run (`:2-3`). `mutmut-modules.txt` names the money, exit and kill-line modules.
- `ci/baselines/skylos.txt`: "NO BASELINE TAKEN YET" (`:1`). The whole-repo scan never finished: 29-minute quota on GitLab, past 40 minutes on Windows, out of memory in WSL (`:2-4`).
- `ci/baselines/known-reds.txt`: 57 lines, Linux only, from GitLab shards 2-8 (`:1-4`).
- `tracker/ci/CI-INTENT-CHECK-2026-11-13.md`: the shape matches what he agreed, but no deep run can be green yet (`:5`); T-22 Linux typing blocks it (`:114`); Skylos at deep times out (`:115`); the nightly mutmut walk never fires because GitHub runs schedules only from `main` (`:48`); two ratchets exist and nobody chose two (`:100`); the backlog loop is not closed (`:71`); the mutmut floor became "no new survivors" (`:107`).
- Coverage floors (80%) ran only in the old nightly battery and `qmx-ci` does not run them (`ISSUES-2026-11-12.md:82`, T-24).

### 3.2 Two earlier audits, and what came of them

**27 August: the QA phase** (memory `qmx-qa-phase-design`). Deterministic battery first (Skylos, Vulture, coverage, mutmut), then 71 agents across 23 epics, one Opus "L6" requirements-fidelity seat per epic. Result: 132 findings (45 confirmed: 4 critical, 18 high), 35 fix cards, 1,379 independent tests written, about 213 of them with wrong expectations. The tests live in `qa/` (43,889 test lines today, section 3.4). Fixes went to Codex on `fix/qa-round-1`. Lessons he ruled or that were measured:
- "No adversarial agent panels ... mutation testing IS the mechanical adversary."
- "Five lanes filed zero findings ... all hollow, L6 caught each; falsifiability, not red-count, is the quality signal."
- Corpus first: dig docs, ledger and spines before asking him; 7 of 12 questions were closed by the corpus.
- Dead code was "effectively clean" by the three-way intersection (Skylos and Vulture and never executed).

**4-5 November: the clean-house audit** (`D:/QMX-worktrees/audit-ship/`, not a git checkout; agent `~/.claude/agents/qmx-auditor.md`; memory `orchestrator-audit-2026-11-04`).
- Shape: a chief-engineer brief, eleven part auditors by plan phase plus seam and whole-repo deletion auditors, read-only, under a hook that blocks git writes, `uv` and credentials (`qmx-auditor.md:6-11`). Findings TSV columns: `id grade kind section location what level proof fix_size removable_lines`; kinds `bug false-green test-delete slop spec-miss scope-creep dead plan-gap`; grades `must should leave`, with `must` allowed only at evidence level 3 or 4.
- The agent's stance is worth keeping verbatim in spirit: "'This is fine' is a correct and welcome answer. There is no quota"; "Before you write any finding, answer one sentence: 'What goes wrong for him, and when?'"
- Result: `FINDINGS.tsv` 290 rows, 30 must from 18 causes; verifiers 34 confirmed, 0 refuted (`STATE.md`). Verdict: "The parts are well built and the connections between them are not finished" (`MORNING-REPORT.md:5`). Every part "Repair", none "Rewrite". Lines that could go, summed from its table: 17,174 (`MORNING-REPORT.md:9-21`).
- What came of it: a 24-PR repair plan, built and merged as R01-R24, PRs #329-#352 on 8 Nov (`release-inventory/MERGED-PRS.md:28`). The plan lives only on the local branch `plan/unit-system`.
- Left open for him (`audit-ship/FOR-HIM.md`): "The old QMB door, about 48,200 lines, and the two old packages `qmf-indicators` and `qmf-structure`, about 14,000 lines. Default: they stay until you say." This is still open and is exactly the kind of question his audit branch is for.
- Its limits, for the design: it audited the *unit build* against its plan, not the whole codebase against what each feature is for, and it did not grade architecture, standards or operations as their own questions.

**A deletion precedent.** The October rebuild ran an inventory PR before any deletion: P16a "inventories the old QMA runtime before any deletion" (#48), then P16b and P16c deletion sets (#49-#70) (`MERGED-PRS.md:47`, `:73`, `:84-90`).

### 3.3 Other inventories

- `tracker/release-inventory/`: `JOURNEYS.md` (every journey checked against code: matches, partly, never built), `SHIPPED.md`, `MERGED-PRS.md` (334 merged PRs, each proved an ancestor of `3ae41ffc`), `PLANS.md` (`README.md:1-10`). This is the "take in the PRs" input already built.
- `tracker/risk-audit-2026-11-12/`: intent audits A and B, a staleness check, four stacked-PR audits and the scope audit (69 sections cut to about 47; mini apps keep 4, merge 19, drop 8, ask 4, wait 7, `SCOPE-AUDIT:50`, `:223`).
- `tracker/ci/ISSUES-2026-11-12.md`: 72 issues, 8 high (`:19`).
- `tracker/BUGS.md` (B-001 confirmed: the node records the stop price as the exit price) and `tracker/REMOVED.md` (empty, header only).

### 3.4 Size on `origin/engine/base` (`3ae41ffcb`, level 4)

Counted: `.py .ts .tsx .js .mjs .svelte .rs .sql .sh .ps1`, lines, test = files under `tests/` or named `test_*`, `*_test.py`, `*.test.*`, `*.spec.*`, `conftest.py`.

| Top level | Code lines | Test lines |
|---|---|---|
| qmx-agents | 139,905 | 87,962 |
| qmb | 109,540 | 49,393 |
| qmn | 105,871 | 48,587 |
| packages (qmf-*) | 86,904 | 49,340 |
| qml | 38,529 | 19,552 |
| qa | 471 | 43,889 |
| scripts | 42,979 | 463 |
| tools | 7,327 | 6,362 |
| apps | 4,374 | 1,462 |
| **All** | **538,541** | **307,642** |

Largest packages by code: qmb 109,540 (218 files), qmn 105,871 (232), qmx-engine 47,563, qml 38,529, qmx-host 22,537, qmf-data 20,837, qmf-risk 18,517, qma-harness 13,253, qmf-readings 13,268, qmf-venue 11,865.

Notes:
- His "QMB 106k" is QMB's code alone at 109,540, plus 49,393 test lines. Its biggest files: `qmb/src/qmb/host/book_handler.py` (126 KB), `data/generate.py` (83 KB), `analysis/project.py` (79 KB), `doors/api/__init__.py` (74 KB), `qmb/__init__.py` (73 KB).
- `scripts/` holds 42,979 code lines with 463 test lines, almost all in `scripts/live/` (166 files, for example `scripts/live/engine/t_templates.py`, 43 KB). These look like one-off live checks from past programs (guess, level 2).
- `qa/` holds 43,889 test lines from the 27 Aug QA phase, sorted by epic (`qa/tests/epic_NN`).
- `apps/qmx-ui` on `engine/base` is 4,374 lines; the UI redesign lives on other branches.
- 10,338 test functions in all (scratchpad `asserts.py`).

### 3.5 Docs against code (level 2-3 samples)

- `docs/` on `engine/base`: 165 files. Last change to `docs/architecture` 1 Oct (`aeccd2fd9`); to components, contracts and decisions 6 Oct. 261 PRs merged into `engine/base` after that (`FUNNEL-SKILL-PLAN.md` section 4).
- `docs/architecture/overview.md` frontmatter: `verified: 2026-09-25`, `stale_after: 90d`. It names `COMP-QMA-CORE`, `COMP-QMA-WIRE` and `COMP-QMA-DAEMON`; PR #169 deleted those packages (`MERGED-PRS.md:32`). It never mentions `qmx-engine`, `qmx-host`, `qmx-home`, `qma-harness` or pods (grep count 0 each).
- The overview says "Nothing imports `qmf-venue` or `qmf-risk`: they are edge modules", and that the node is "the one sanctioned importer and wirer of `qmf-venue`". In code, `qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:13`, `ctrader_transport.py:9-10`, `models.py:7` and `service.py:17-19` import `qmf.venue`, and at least 10 files under `qmb/src` import `qmf.risk` (for example `qmb/src/qmb/execution/cost.py`). Either the rule was amended later without a docs change, or the code broke it. Either way the ratified doc no longer describes the code.
- `docs/components/` has 21 files, including `qma-core.md`, `qma-daemon.md` and `qma-wire.md` for deleted packages, and none for the eleven `qmx-*` packages that now hold 140k lines.
- The 5 Nov audit already ruled "`docs/` is stale" and "October code is the truth" (`audit-ship/STATE.md`).

## 4. Docs appending: what was said, and where it sits

His words, transcript `dd8f4ab2`:
- 12 Nov 08:42 (L214): asks whether PRs can be used "to maybe update documentation" and to find unfixed issues, across "330 something PRs".
- 12 Nov 11:08 (L1769): main holds "only plans and docs mostly ... we shall move the plans because man, we need documentation for QMX"; Greptile "can, I think, update documentation via the PRs ... I'll have a Claude agent monitor that ... documentation is very out of date. It's not even funny."
- 12 Nov 14:02 (L2795): "Updating docs is separate. The separate factory step that runs after each merge ... I don't think it's something very heavy. And I think we may not use ... the documentation factory skill ... it's not taking in PRs ... the whole point was first updating the docs so that the plans can come in properly ... we are working on a very brownfield code base ... documenting is paramount and also catching bugs."
- 13 Nov 18:40 (`HIS-WORDS:47`): "Oh, before I forget, also documentation ... documentation appending ... We just never said which phase."

What was agreed and written down:
- `PLANNING-FUNNEL.md:84`: "Grounding never waits for a docs refresh; the docs catch up after each merge, in a separate factory step." Grounding lists doc drift (`:57`, `:82`).
- PR body v2 carries `DOC: <doc path> | <what changed>` lines (`PR-BODY-AND-SKILLS-2026-11-12.md:35-36`, `:77-78`); the brief's section 11 carries them (`templates/BRIEF.md:110`); the checkpoint merge copies every `DOC:` line into the stop's PR (`STOP-REVIEW.md:77`).
- `FUNNEL-SKILL-PLAN.md` section 4 designs both halves:
  - **Going forward, `doc-sync` after each merge:** a script appends merged `DOC:` lines to `docs/_pending.tsv`; it flags a PR that changed an area's code paths but says `DOC: none`, which needs a `code_paths:` field per component in `dependencies.yaml`; a docs agent edits only what each line names, with the code as truth, bumps `verified` and adds a changelog line.
  - **Backfill:** add `code_paths:` to the components, map merged PRs since each doc's `verified` date to components, rank by PR count, then one agent per component rewrites the doc from current code (PR bodies for intent), marking each claim verified at a commit. Run when a program first touches an area; a background sweep does the rest; "Planning never waits on it."
- `GAP-AUDIT-2026-11-13.md:39` (section 3 item 9): designed, "but not built and not scheduled". Item 10 adds "moving the plans off `main` into docs" and "the code-quality review of about 700 PRs".

Where it could sit (options for the architect, section 6 Q8):
- After merge, as now designed, for both branches. Every merged checkpoint, feature or audit, produces `DOC:` lines.
- Inside the audit branch as its first output: an audit already reads code, PRs and docs for an area, which is the backfill's input. Its "explain simply" deliverable is a rewritten component doc.
- As a background sweep, never on the critical path.

Two facts constrain the choice. The component docs have no code paths today, so nothing can map a PR to a doc until `code_paths:` exists. And BMad's own finding is that generated docs about code go stale on arrival (`bmad-document-project/SKILL.md:9`), so whatever is kept must be small and verified at a commit.

## 5. How build, review and merge would take an audit program

### 5.1 What already fits

- **Subtract first, callers migrated, no compatibility layer** is a house rule (`PROJECT-RULES.md:32`): "A replaced internal API moves every caller and is deleted in the same slice ... Nothing is deleted before its replacement passes."
- **Removed rows** travel end to end: planned in the program's `REMOVED.md` by `funnel-subtract`, carried to builders in brief section 7 and `CHAIN.md`, guarded at review (`REVIEW.md:16`, `:28`), moved to `tracker/REMOVED.md` at merge (`STOP-REVIEW.md:80`).
- **The checkpoint review already asks the deletion question** (`slice-review/SKILL.md:42`) and has the "returns nothing" probe (`:88-89`).
- **The quality ratchet** only blocks new findings, so deletions never trip it.
- **The vertical slice, checkpoint and lane layout** works the same for removals.

### 5.2 Gaps, by phase

**Chain and plan checks (planning side, also the audit's handoff).**
1. Every ask must quote him with a transcript source (`check_chain.py`, `check_expand`, lines 168-185: `ask-<id>-quoted-and-sourced-in-his-words`, `ask-<id>-quote-matches-source`). An audit's work items come from findings, not his words. `CHAIN.md` has ids for asks, plan lines, elements, slices, questions, decisions, proposals, edge cases, can-change and removals, but none for an audit finding or an audit verdict. The chain from "his mandate" to "finding F" to "slice" has no link type.
2. `funnel-subtract` collects candidates only "in the area" a plan touches (`funnel-subtract/SKILL.md` step 1). A whole-package audit needs the same row shape at program scale.
3. `check_plan.py:73-74` needs a SAFETY fact and at least one code fact per brief. That fits. Nothing checks that a deletion brief names its callers fact (for example `git grep -c "<symbol>(" -- <roots>` with expected `0` after) or its replacement.

**Build.**
4. **The fail-at-parent rule rejects behaviour-preserving slices.** `PROJECT-RULES.md:34`: "Each new test fails at the parent on an assertion and passes at the head". `BUILDER.md:25`: "a test that passes or errors at the parent is rewritten." `slice_checks.py:63-104` (ship-kit `51d95409`) fails any new test whose parent outcome is not an assertion failure. A refactor's pin (characterization or equivalence test) must pass at **both** parent and head. So poteto's Refactoring playbook step 1 is impossible under today's checks: a slice that adds a pin goes red; a slice that adds no test gets `NOTRUN` and passes (`:88-89`), so the safe path is to add no pin at all. Level 3.
5. **Test deletion has no proof form.** `PROJECT-RULES.md:34` allows deleting a test that "would still pass if the code returned nothing", but no check records the probe output as evidence, and `verify_ready` checks only that the diff is non-empty and inside the brief (`verify_ready.py:3-9`). A slice that deletes tests to go green looks the same as one that deletes false greens.
6. **Whole-package removal.** `slice_checks` runs lint, types and tests per touched package from `head_copy / package.root` (`slice_checks.py:160-170`). A slice that deletes a package's folder has no root at the head. Guess, level 2: the per-package commands would fail or misreport. `checks.toml` would also need the package removed, and `tools/test_all.py` and `tools/ci.py` hold the suite list (`PROJECT-RULES.md:45`).
7. **Forced files for removal** (pins, censuses, `app.toml` versions, `uv.lock`, workspace members, CI shard lists, `ci/baselines/*.txt` rows) must be in the brief's file list or `verify_ready` refuses the slice (`templates/SLICES.md:31-34`). The planner has no checklist for what a deletion forces.
8. **Baselines after deletion.** A deleted function's mutmut and Vulture rows stay in `ci/baselines/` ("A finding that is fixed stays in the baseline", `CI-INTENT-CHECK:46`). The ratchet cannot tell "gone because deleted" from "gone because fixed", and nothing shrinks the baseline (fix item 6 in `CI-INTENT-CHECK:119`).

**Checkpoint review.**
9. **Proving behaviour kept.** The review walks prove plan lines and edge cases at the tip (`STOP-REVIEW.md:44-46`). An improve slice's claim is "same outputs as before", which needs an equivalence run at `{FROM}` and `{TIP}` with the same inputs. No walk compares parent and tip.
10. **Proving nothing still calls it.** Static callers are a `git grep`. Dynamic callers are not: QMX registers blocks, apps, workflow templates, MCP tools and reason codes by name (censuses in `PROJECT-RULES.md:47`, `qmx-tools/tests/test_tools.py` tool counts, `app.toml` manifests, stdlib blocks in the node's lock, `:43`). A removal can pass `git grep` and break a stored unit document, a shipped app or the UI. No review walk covers stored data, manifests, the UI or the other workspace (`qmx-agents` holds `qmb` and `qmn` too, `:48`).
11. **The four walks are feature-shaped.** "Down the chain" proves plan lines; "up from the code" checks every hunk serves an ask. An audit checkpoint needs "every finding this checkpoint claims is closed is closed at the tip" and "every removed row has its replacement or its no-replacement reason".
12. **`REMOVED.md` rows lack the replacement.** The row shape is `what. Why. Decided by. Status` (`tracker/REMOVED.md:5`; `funnel-subtract` step 5). His 18:49 rule ("knowing ... what is going to be replaced") needs a `Replaced by:` field (a new path, or "nothing, because ...").
13. **Fault and operations walks** read `GROUND.md` fixed lines and `## Operations` in the program's architecture. An audit program may have no `arch/ARCH.md` of its own; the walks need the existing area's operations claims instead.

**Merge and after.**
14. **The merge note speaks in asks.** "You asked for X. Now true: ..." (`STOP-REVIEW.md:81`). An audit merge needs "removed N lines, here is what replaces them, here is the proof nothing changed for you".
15. **One-way doors.** `BUILDER.md:73` lists "a deleted public API" and "a stored data format change" as one-way doors. Most audit removals are one of these. Today a one-way door is a label in the PR body, not a gate. The 5 Nov audit already deferred "may the old node be deleted before any unit has traded on demo?" to him (`FOR-HIM.md` item 2).
16. **Docs.** A removal invalidates docs and ADRs. Nothing today marks a `docs/decisions/ADR-*` as superseded when its code goes.

**Index and phase plumbing.**
17. `PROGRAM.yaml` has no field for the program's kind, and `phase_state.py` routes by files and verdict lines (`SYSTEM-AUDIT:328-353`). The same four phases could carry an audit program if the plan stage is swapped; nothing reads a kind today. `SYSTEM-AUDIT:357-392` lists every place a new stage must register (funnel table, `PLAN.md`, `check_chain.py STAGES`, fixtures, `CHAIN.md`, skills, `CLAUDE.md`, `NEXT-PHASE.md`, `phase_state.py`, `SHIPPING-METHOD.md`). A new phase touches the same list plus `NEXT-PHASE.md`'s table and a new start sentence for him.
18. The 37 system-audit findings still stand (6 blocks), including that phase starts do not chain unattended (F1), the merge ignores CI (F4) and chained sessions inherit Fable (F5) (`SYSTEM-AUDIT:9-36`). An audit branch inherits all of them.

## 6. Open design questions for the factory architect

Each is a real choice. None is decided here.

**Q1. What is the unit of an audit?**
- (a) One package or app at a time (qmb, qmn, qmx-engine...). Simple to scope and to explain; seams between packages are missed.
- (b) One feature or journey end to end (`JOURNEYS.md` rows), crossing packages. Matches "does the code serve the feature"; harder to bound, and two audits may touch one package.
- (c) Whole repo in one pass, sliced by part, like 5 Nov. Finds cross-cutting issues; one large report he cannot read in one sitting.
- Trade-off: (a) is easiest to resume and to hand to build; (b) answers his first question best; (c) costs most and repeats 5 Nov.

**Q2. What does an audit hand to build?**
- (a) A full program folder (`SCOPE`, `SLICES`, briefs) written by the audit session itself. One session, no planning stage; the audit must do the funnel's handoff work and pass its checks.
- (b) A findings report plus a verdict per item (keep, improve, remove, ask him), which then enters the planning funnel as its input (audit then plan). Reuses the funnel; adds a phase.
- (c) Mechanical findings go straight to one batch builder; contained and design findings go through a light or full funnel (the three doors he accepted on 12 Nov, `CI-INTENT-CHECK:17`, `:78`).
- Trade-off: (a) is fastest but builds a second planner; (b) keeps one handoff path but makes every cleanup pay for annealing; (c) fits the doors but needs a triage step whose door calls he trusts.

**Q3. Where do audit asks come from, so the chain holds?**
- (a) His mandate quote ("clear out a lot of the clutter", 18:49) is the single ask S1; findings become plan lines under it.
- (b) A new id kind (finding `F`, or audit verdict) in `CHAIN.md` with its own checks; his yes per batch of verdicts turns them into asks.
- (c) Audit verdicts he approves become asks by quoting his approval turn.
- Trade-off: (a) needs no checker change but every slice traces to one vague quote; (b) is precise but touches `check_chain.py`, fixtures and `chain_packet.py`; (c) costs him the most reading.

**Q4. How are false-green tests judged and removed?**
- (a) Mechanical only: mutmut survivors plus the "returns nothing" probe decide; an agent rewrites or deletes.
- (b) Mechanical first, then one agent per package classifies each weak test (rewrite, delete, keep) with the probe output as evidence, as the 27 Aug L6 seat did.
- (c) Rewrite only, never delete, until the code under it is audited.
- Trade-off: (a) is cheap and cannot manufacture findings, but full-repo mutmut has never finished on this hardware or free CI; (b) costs agents but explains each call; (c) keeps the suite large and slow.
- Linked: the `qa/` folder (43,889 test lines, written by the QA phase about features that have since moved) is itself an audit target. Keep, fold into packages, or retire?

**Q5. How does build prove a behaviour-preserving slice?**
- (a) A second slice kind ("pin" or "refactor") where new tests must pass at both parent and head, and an equivalence script runs old against new.
- (b) Two slices: first a pin slice that adds characterization tests (allowed to pass at the parent), then the change slice that must keep them green.
- (c) No new tests; rely on the existing suite plus mutmut on changed functions.
- Trade-off: (a) changes `slice_checks.py`, `BUILDER.md`, `PROJECT-RULES.md:34` and the brief template; (b) adds slices and a dependency edge but keeps each check simple; (c) is free but trusts a suite with 38-56% mutant survival on money modules.

**Q6. How is "nothing still calls it" proved before a removal merges?**
- (a) Static: `git grep` callers facts in the brief, at zero after.
- (b) Static plus registry scans: censuses, manifests, stored unit documents, app pins, the UI's API calls, the second workspace.
- (c) Static plus a runtime trace: run the app (host, node, QMB) through its journeys and record which modules load.
- Trade-off: (a) misses dynamic lookups; (b) needs a scanner per registry kind; (c) needs a running system and journeys that cover the path.

**Q7. What standard does the audit judge against, and where does it live?**
- (a) Rewrite `PROJECT-RULES.md` and `conventions/failure-register.md` into Agent OS style indexed standards, discovered headless from the code with the why taken from the corpus.
- (b) Keep `PROJECT-RULES.md` as the one standard; the audit only reports where code breaks it.
- (c) Adopt an outside baseline (Matt Pocock's Fowler smell list, `codebase-design` vocabulary) with QMX overrides.
- And where: in the repo (every builder sees it; he said his planning skills stay local, 18:06) or on his machine.
- Trade-off: (a) gives builders, auditors and reviewers one source but is a project of its own; (b) is free but the file mixes product, process and code rules; (c) is quick but generic.

**Q8. Where does docs appending sit?**
- (a) After every merge (the `doc-sync` design), for both branches.
- (b) As the audit's first output per area (the backfill), with (a) after.
- (c) Only a background sweep, never in a phase.
- And: Greptile (his 12 Nov idea), a Claude agent, or a script plus an agent.
- Trade-off: (a) keeps docs current but needs `code_paths:` first; (b) makes the audit's "explain simply" output reusable but slows the first audit; (c) never blocks and may never catch up.

**Q9. Who audits, and with what model?**
- (a) Opus readers per area with one Fable synthesis seat (he floated Fable for this branch at 18:40 and 18:49).
- (b) Fable for the architecture and "explain simply" judgement only; Opus everywhere else.
- (c) All Opus, Fable only on his explicit ask (CLAUDE.md standing rule).
- Trade-off: weekly usage against depth. The 5 Nov audit ran on Opus with `effort: high` and found 30 must rows with 0 refuted.

**Q10. How do the two branches hand to each other?**
- An audit can find a missing feature or a needed redesign (needs planning); a plan can need an audit of its area first (RESUME:11).
- (a) Either branch may write a request file the other picks up; he approves each crossing.
- (b) Planning always runs a scoped audit of its area first (grounding grows into it); auditing never plans features, it only parks them for him.
- (c) One shared "intake" step routes every request to audit or plan.
- Trade-off: (a) is flexible but adds a state the phase router must read; (b) makes every plan slower; (c) adds a phase before both.

**Q11. How is a checkpoint of removals reviewed and merged?**
- (a) The same review, with an added equivalence walk, a callers walk and a "finding closed" walk.
- (b) A lighter review for mechanical removals (scripts only) and the full review for design-level ones.
- (c) Every removal of a public API, a stored format or anything on a fixed line waits for his yes at merge (one-way door gate).
- Trade-off: (a) is consistent; (b) is faster but splits rules; (c) is safest and costs his attention.

**Q12. What does he see?**
- (a) One plain report per area: what it is for, does it do that, what stays, what goes and what replaces it, size before and after, with a visual explainer (memory `output-as-animated-explainers`).
- (b) Only the questions only he can answer, in batches of four, with recommendations.
- (c) Both, with (a) as an artifact and (b) in chat.
- Trade-off: his reading time against trust. His memory notes say long multi-section answers go unread (`short-replies`).

**Q13. What happens to the open 5 Nov question?**
- The old QMB door (about 48,200 lines) and `qmf-indicators` plus `qmf-structure` (about 14,000 lines) wait on him (`FOR-HIM.md` item 3). Is that the first audit program, or does the first audit start from the measured biggest areas (QMB 109,540 and qmn 105,871 code lines), or from `scripts/live` (42,979 lines with almost no tests)?

**Q14. What gate stops the audit branch from growing like the risk build did?**
- (a) The challenger stage applies to audits too: every proposed improvement is CORE, LATER or DROP against a budget.
- (b) A line budget instead: an audit program must remove more than it adds.
- (c) No budget; his yes per batch is the gate.
- Trade-off: (a) reuses one mechanism; (b) is measurable but can reward deleting the wrong things; (c) puts all control on his reading.
