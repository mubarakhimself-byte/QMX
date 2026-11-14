# Funnel skill plan (12 November 2026)

> Superseded on 12 November by `PLANNING-FUNNEL.md` and the installed `funnel-*` skills (see `FUNNEL-CHANGES.md`). Kept as history.

Status: proposal, revised 12 November after his answers. Nothing is installed yet, and no existing skill has been edited. He has given permission to rewrite or combine skills; every change is listed in the last section so he is alerted to each one.

**The frame (his, 12 November): planning is context engineering.** A question means context is missing, and a stress test adds context; it is not a filter. Every skill below is judged by whether it removes ambiguity and hands richer context to the next stage.

It goes with `PLANNING-FUNNEL-PROPOSAL.md`. The stages are the same: expand, ground, self-annealing, technical lens, technical self-annealing, handoff.

## 1. What exists

**pstack.**

- The original is Cursor's: `github.com/cursor/plugins/tree/main/pstack`. Its defaults send code work to Grok and judgment to Opus.
- The installed copy is a mirror, `backnotprop/pstack` as of 7 October, with harness-neutral rewrites.
- The original has 7 skills the mirror lacks. `sharpen`, `in-your-own-words`, `statechart` and `ketchup` fit the funnel.

**Self-annealing.** No skill in pstack, BMad or Matt Pocock's set does it agent-driven. The pieces exist, but each is human-driven or runs once:

| Skill | What it does | Why it doesn't fit as is |
|---|---|---|
| `grilling` (Pocock) | Rounds of questions until the *frontier* is empty, which is the stop rule we want | The user answers every round |
| `bmad-forge-idea` | Pressure-tests an idea "until it hardens, proves out, or dies" | One question at a time, to the user |
| `architect` (pstack) | Grounds the problem, has `arena` produce competing designs, re-runs when the human pushes back | The human's pushback drives the loop |
| `correct` (pstack) | Makes each repeated agent mistake impossible | "Repeat this each time the operator corrects you" |
| `interrogate` (pstack) | Several reviewers attack a change | One pass |
| `bmad-review` | Adversarial, edge-case and verification-gap lenses | One pass |
| `hillclimb` playbook (pstack) | Agent-driven loop: one change, measure, keep or revert, stop on a rule | Built for a metric, not for questions. Its loop shape is the one to borrow |

**"Can delete" pieces.** Five pieces exist; none produces a list of candidates with evidence:

- `principle-subtract-before-you-add`: a lens with no procedure.
- `codebase-design`'s *deletion test*: "if complexity vanishes, it was a pass-through".
- `principle-migrate-callers-then-delete-legacy-apis`.
- `no-comments` / Comment Sicko: workaround comments only, and it waits for approval.
- Pocock's `improve-codebase-architecture`: writes a report, then asks the user to pick one candidate.

**Spawning.** `interrogate`, `arena`, `swarm`, `reflect`, `no-comments`, `bmad-review`, Pocock's `code-review` and party mode's `subagent` mode all spawn. Every pstack spawner says what to do without a subagent tool: "run each reviewer yourself, one after another". `bmad-review` has the same fallback. So the house rule is:

- **The lead session** (the planner) fans out.
- **An agent** runs the same skill one step after another.

## 2. Stage by stage

| Stage | Skills that fit | Human-driven today | Agent-driven in one session |
|---|---|---|---|
| Expand (depth per feature: light, medium or deep) | `research`, `bmad-domain-research`, `bmad-technical-research`, alphaXiv, browser, `grilling`, `domain-modeling`, `bro`, `in-your-own-words`* | `grilling`, `in-your-own-words` (by design: this is his stage) | Light: restate and confirm. Medium and deep: the lead fans out research agents. Grilling stays with him, because he is the source here |
| Ground | `how`, `why`, `blast-radius`, `codebase-design`, the `session-pickup` and `investigation` playbooks | None, but nothing reads an area's PR history | New **`ground-area`**, run by one agent per area |
| Self-annealing | `grilling`, `bmad-forge-idea`, `bmad-party-mode`, `bmad-cis-*`, `bmad-review` (edge-case lens), `principle-attack-the-premise`, `sharpen`* | Grilling, forge, party mode and CIS are all conversations with the user | New **`self-anneal`** (plan mode) and new **`can-change-scan`** |
| Technical lens | `bmad-architecture`, `architect`, `improve-codebase-architecture`, `codebase-design`, `blast-radius`, pstack principles | `improve-codebase-architecture` (the user picks a candidate); `architect` checkpoint (only if asked) | `bmad-architecture` has a headless mode (`references/headless.md`). The agent reads the improve report and picks by a rubric: serves a plan line, smallest blast radius. The lead runs `arena` if wanted |
| Technical self-annealing | `bmad-review` (adversarial, verification gap), `interrogate`, `blast-radius` | None | **`self-anneal`** (technical mode), with the Fable answer-linker |
| Handoff | `to-tickets`, the `multi-phase-plan` playbook with `check-plan.mjs`, `writing-for-agents`, `technical-writing`, `unslop` | `to-tickets` ("Quiz the user... until the user approves") | The approval is replaced by the scope-trace script plus a fresh reader per brief |

\* Upstream pstack only. Install approved on 12 November; not installed yet.

## 3. New skills

Each is written to `writing-for-agents`:

- the description front-loads its leading word;
- each step ends on a completion criterion that can be checked;
- the target is stated as what to do;
- reference material sits behind pointers.

### `self-anneal`

**Spec.** It removes ambiguity from a subject file, round by round, by finding what is still unclear and adding the missing context. It stops when a round produces no new question.

- **The subject:** the core things and plan in plan mode, or the architecture in technical mode.
- **Each question is a gap in context.** The round fills it from one of three sources:
  - the ground truth, for facts;
  - a linking-logic step;
  - him or the Fable answer-linker, for decisions.
- **Linking logic is a named technique.** It grounds a vague idea in something concrete:
  - **by analogy:** "self-configuring like Kubernetes";
  - **by reference:** a module in the code, a paper, a ruling, another product.
- **Each round** runs these lenses in turn:
  - attack the premise;
  - the edge-case lens;
  - a party-mode debate in session mode;
  - CIS problem solving;
  - forge-idea's attack mode;
  - linking logic, for whatever is still vague.
- **Contradictions and ambiguity in his words go to him with a recommendation.** Each carries the agent's best proposal and its reason. No agent settles one silently.
- **Technical mode:** technical questions go to the Fable answer-linker. A fresh Opus agent checks its answers for hidden product calls before they are logged as "Fable decided X because Y".
- **The record is the product.** `ANNEAL-LOG.md` keeps each round's questions, the context that answered each one, and who answered it, so the next stage reads how ambiguity was removed, not only the result. State is on disk, so a round resumes after a crash.
- **Output:** the subject's new version, `ANNEAL-LOG.md`, `EDGE-CASES.md`, candidates for `can-change-scan`, and the number of rounds.

```markdown
---
name: self-anneal
description: Anneal a plan or architecture: find what is still ambiguous, add the missing context, round after round, until a round raises no new question. Use for planning stage 3 (plan mode) or stage 5 (technical mode).
---
Inputs: subject file, GROUND.md, MAP.md, REMOVED.md, mode (plan | technical).
1. Load ANNEAL-LOG.md (create it if absent). Done when every past question is held by meaning.
2. Run the round's lenses in order; inside a subagent, one after another (lens list and the
   linking-logic technique: references/lenses.md). Done when each lens returned findings or "none".
3. Sort each finding: fact gap, vague idea, decision for him, technical decision, edge case,
   can-change candidate. Done when every finding has one kind and a source line.
4. Keep only findings new by meaning; log each as a question.
5. Fill context: look up fact gaps in the ground truth; ground vague ideas by analogy or
   reference; write edge cases to EDGE-CASES.md; pass candidates to can-change-scan.
   Done when every question but the decisions has its answer and source in the log.
6. Decisions: his go to the lead (max 5, numbered, each with a recommendation and its reason),
   then wait. Technical mode: technical decisions go to the answer-linker
   (references/answer-linker.md); a fresh check pulls out hidden product calls for him; the rest
   are logged as "Fable decided X because Y".
7. Rewrite the subject with the new context. Stop rule: the round raised no new question.
   Report: rounds run, questions per kind, the new subject version.
```

### `can-change-scan`

**Spec.** It is pstack's subtract-before-you-add turned from a principle into a procedure, with two additions he asked for: every deletion or change is justified, and agreed ones go into a durable "removed, and why" list.

- **It applies four tests:**
  - the deletion test;
  - subtract-before-you-add;
  - migrate-callers-then-delete, for old APIs that still have callers;
  - Comment Sicko's view of workaround comments.
- It also uses the project's dead-code tools: Skylos and Vulture in QMX.
- **Each candidate carries a justification:**
  - which core thing or plan line it serves;
  - its callers, as a command and its expected output;
  - its blast radius;
  - what it frees.
  - A candidate without a justification is not listed.
- **Who decides:** agents, when nothing in the app he sees changes. Otherwise he does, given a recommendation.
- **`REMOVED.md`:** each agreed deletion or change, with its reason and the decider.
- **The YAGNI guard:** before anything is added, it is checked against `REMOVED.md`. A plan line or slice that would rebuild a removed thing is flagged as a decision for him, with the old reason attached.

```markdown
---
name: can-change-scan
description: Subtract before you add: justified candidates for deletion or change in one area, and the durable REMOVED.md list that stops later loops rebuilding them. Use in planning stage 3 and before architecture.
---
Inputs: area paths, core things, plan, GROUND.md, REMOVED.md.
1. Run the dead-code tools on the area. Done when each tool's output is saved.
2. Apply the deletion test to each module, and subtract-before-you-add to each guard,
   wrapper and stand-in (tests: references/tests.md). Done when every module has a verdict.
3. Justify each candidate: the core thing or plan line it serves, callers (command + expected
   output), blast radius, what it frees. Done when every listed candidate has all four.
4. Mark the decider: "agents" when nothing visible in the app changes; "him" otherwise,
   with a recommendation and its reason.
5. Check the plan against REMOVED.md; flag any line that would rebuild a removed thing.
6. Write CAN-CHANGE.md. Append each agreed item to REMOVED.md with its reason and decider.
   The code itself changes only later, through a slice.
```

### `ground-area`

**Spec.** It writes the ground truth for one area from the code itself, without waiting on docs.

- **It reads:**
  - the code, through `how`;
  - the area's merged PRs: titles, plain-words lines, `OPEN:` lines, review notes;
  - `why`, where ownership is in question;
  - the area's docs, as claims to check.
- **It writes `GROUND.md`:**
  - facts, each as a command and its expected output;
  - open items from `OPEN:` lines;
  - a doc-drift list (the doc says X, the code says Y), which feeds the docs step;
  - a census of callers.

```markdown
---
name: ground-area
description: Ground truth for one code area from its code, PR history and docs, as facts that rerun. Use in planning stage 2, before any stress test.
---
Inputs: area name or paths, core things.
1. Resolve the paths (docs/architecture/dependencies.yaml, then git grep). Done when every path is listed.
2. Read the code through `how`. Done when every path has at least one fact or a "not relevant" note.
3. List the merged PRs touching the paths since the area's docs were last verified; read titles,
   plain-words, OPEN: and review lines. Done when every OPEN: line is listed.
4. Read the area's docs as claims; check each against the code. Done when each is "matches" or "drift".
5. Read every REMOVED.md row for the area. Done when each is listed as a standing constraint.
6. Write GROUND.md: facts (command + expected output), open items, removed items, doc drift,
   callers census.
```

## 4. Docs

**His doubt is right.** `documentation-factory` change mode suits design docs, not brownfield code:

- It starts from the ledger: a decision entry and an ADR for every change.
- Its components (`docs/architecture/dependencies.yaml`, 21 components) list no code paths, so a PR cannot be matched to the doc it affects.
- `docs/` was last changed on 27 September. GitHub shows 334 merged PRs since then (261 into `engine/base`, 65 into `rebuild/base`, 8 into `integration`); his ~700 likely also counts stacked and unmerged work.
- No merged PR carries a `DOC:` line yet, because PR body v2 is new today.

**Going forward: a `doc-sync` step after each merge.**

1. A script reads the merged PR's `DOC:` lines (`DOC: <doc> | <what changed>`) and appends each to `docs/_pending.tsv`.
2. It also flags a PR that changed an area's code paths but says `DOC: none`. This needs a one-time `code_paths:` field on each component in `dependencies.yaml`.
3. A docs agent takes the pending rows. For each doc, it reads the PR diff, the current code and the doc, and edits only what the line names, with the code as truth. It then bumps `verified` and adds a changelog line.
4. It reuses only the parts of `documentation-factory` that fit: its style rules, `lint_docs.py`, `check_citations.py` and the changelog. ADRs are written only when a decision changed.

**Backfill of past PRs** (no `DOC:` lines exist, so it works by area, not by PR):

1. One-time: add `code_paths:` to the 21 components.
2. A script lists the merged PRs since each doc's `verified` date and maps their changed files to components. It ranks components by PR count.
3. Per component, one agent reads the current code as truth and the PR titles and bodies for intent. It rewrites the doc to match, marks each claim as verified at a commit, and flags what it cannot verify.
4. Run it when a program first touches an area, using `ground-area`'s doc-drift list as the to-do list. A background sweep works through the rest in rank order. Planning never waits on it.

## 5. Changes to alert him to

None of these is made yet. He has given permission to rewrite and combine skills; this list is the alert.

| # | Change | Kind | Status |
|---|---|---|---|
| 1 | `self-anneal` | New skill, combining grilling's stop rule, the hillclimb loop, forge's attack mode, party-mode session mode, the bmad-review edge-case lens and linking logic as a named technique | Allowed; not built |
| 2 | `can-change-scan` | New skill, built on subtract-before-you-add and enhanced with a justification per candidate, `REMOVED.md` and the YAGNI guard | Asked for by him; not built |
| 3 | `ground-area` | New skill, combining `how`, `why`, PR-history reading and the `REMOVED.md` rows | Allowed; not built |
| 4 | `doc-sync` | New step: a script plus a docs agent, using parts of `documentation-factory` | Proposal |
| 5 | `code_paths:` in `docs/architecture/dependencies.yaml` | Docs data edit | Proposal |
| 6 | `to-tickets` | QMX copy: replace "quiz the user" with the chain-check script and a fresh reader | Allowed; not built |
| 7 | `improve-codebase-architecture` | QMX copy: the agent picks by rubric instead of asking the user | Allowed; not built |
| 8 | Install `sharpen`, `in-your-own-words`, `statechart`, `ketchup` from upstream pstack | Install | Approved; not installed |
| 9 | House rule for spawning skills: the lead fans out, an agent runs them one after another | Rule in `PROJECT-RULES.md` | Proposal |
| 10 | `REMOVED.md` per program, or project-wide | New file | His choice pending (question 2 of the funnel proposal) |
| 11 | `TRACE:` line in PR body v2, naming the slice and core thing | Template edit | Proposal (question 3 of the funnel proposal) |
| 12 | Per-feature chain rows in `PROGRAM.yaml` (his words through to the PR) | Index format | Proposal |
