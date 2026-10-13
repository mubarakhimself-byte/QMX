---
label: qma-v2:research:H2-skills-method
created: 2026-10-13
question: How do pstack and Matt Pocock's skills get used the way their creators intend, in our orchestrator, builder and UI sessions on Claude Code?
sources: creators' GitHub pages and guide (read in the built-in browser), Claude Code docs, local installs under C:/Users/Mubarak/.claude/
---

# H2. Using pstack and Matt Pocock's skills as their creators intend

## Three facts that change the recipe

1. **Nesting is on.** Claude Code docs say "By default, a subagent can spawn subagents of its own, up to three layers" (code.claude.com/docs/en/sub-agents). The installed build is 2.1.296 and no settings file sets `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`. So "sub-agents cannot spawn sub-agents" is false here. It was our own prompt that forbade it (ORCHESTRATOR-PROMPT.md:116 "Do not spawn sub-agents"). That is a fine cost rule. Make it structural: set the env var to `1` in the project settings, and write the skill fallbacks into the builder brief.
2. **A subagent can call the Skill tool on a pstack skill.** This run is a subagent. It called `Skill("unslop")` (`disable-model-invocation: true`), the call loaded the skill, and the transcript shows `"name":"Skill","input":{"skill":"unslop"}`. That was measured once. The docs say such skills are "not on its own" for Claude and cannot be preloaded into subagents. So the rule is to try the Skill tool first and, if it is refused, Read the full SKILL.md. Either way, log which one happened.
3. **The local copies trail upstream.** The pstack playbooks we use (orchestrate, autopilot-stack, autopilot-full, multi-phase-plan, feature, shipping, pause-safely) match `cursor/plugins` main byte for byte. `poteto-mode/SKILL.md` and `agents/poteto-agent.md` miss one rule upstream added: "Never spawn a `poteto-agent` to run the playbook itself." Upstream also dropped the Harness section, so the local copy, close to the backnotprop mirror, is the better one for Claude Code. Matt's local skills predate v1.3 (2026-10-05). They lack `implement-spec`, `pr` and `retro`, and use `CONTEXT.md` where upstream now uses `GLOSSARY.md`.

## (a) The recipe on one screen

**Planning session (now).** pstack's **Multi-phase plan** playbook. Write the plan in its skeleton, name `orchestrate.md` as the execution playbook, run `node ~/.claude/skills/poteto-mode/scripts/check-plan.mjs <plan>`, hand back, stop. Settle open questions by prototype, not by asking.

**Orchestrator session.** One fresh session. Operator pastes a prompt that begins with `/poteto-mode`.
1. The skill loads because `/poteto-mode` leads the message. Read `~/.agents/pstack-models.md`.
2. Match the **Orchestrate** playbook. Open the todo list with its seven steps verbatim (Frame, Install the runtime, Pilot, Scale, Drain, Land, Close).
3. Install the runtime. Write `preferences.md` (numbered standing orders), `LEDGER.md` (one row per packet), and `decisions.tsv` per **show-me-your-work**. `orch.ts` is optional. bun is installed.
4. Pilot. Run the first packet through the whole path (brief, builder, verify, ledger row, merge) before any second builder starts.
5. Scale. Keep a rolling window of up to 3 `poteto-agent` builders on `opus`, refilled as each one finishes.
6. Verify each PR yourself, using **Shipping** steps 1 to 3 (independent verdict, patch-id) and the Orchestrate Verification section. Run gates and live lanes inline. Spawn a verifier (`sonnet`) only for expensive or judgment-heavy units.
7. Land. Merge only the contiguous verified run into `rebuild/base`. Recompute after each merge.
8. Pause with **Pause safely** and resume with **Session pickup**. Close with the predicate count, the ledger, and the show-me-your-work audit.

**Each builder (`poteto-agent`, `opus`, background, own worktree).**
1. Read the poteto-mode SKILL.md at its absolute path, then `pstack-models.md`, `playbooks/feature.md` and `playbooks/opening-a-pr.md`.
2. Open a todo list with the Feature steps verbatim. A skipped step keeps a line `skip: <reason>`.
3. Step 1 `how`: one inline pass over the files in the brief. Step 2 `architect`: `skip: shape fixed by ARCHITECTURE section 8` unless the brief says otherwise.
4. Step 3 is the throughput checkpoint. Step 4: own the diff directly, as feature.md:12 allows, and call `Skill("tdd")` at the seams the brief names.
5. Step 5: verify on the real surface with the project verify skill. Step 6: small ordered commits. Step 7 `interrogate`: skip, because the orchestrator owns review.
6. Step 8, Opening a PR. Reread the diff to stand in for deslop. Run the Comment Sicko prompt yourself over the diff for `/no-comments`. Write the PR body with `technical-writing` then `unslop`. Open the PR ready, report, and stop. No babysitting.

**UI session (later, separate).** Start with `/poteto-mode`, Feature playbook, one screen at a time. Make the verify lever first: `/install-and-verify` (Reticle) in the SvelteKit app. Then use `agentic-tdd` for each user flow and `verify-ui-change` after each change. Answer layout questions with the Prototype playbook or Matt's `prototype` (options behind a switcher, screenshots). Run `audit-my-app` before handover. The built-in browser takes the screenshots.

## (b1) Paste-ready "Method" section for the orchestrator prompt

```text
## Method
/poteto-mode is loaded by this message. Work under it for the whole session.
1. Read ~/.agents/pstack-models.md now. Models: builders opus, verifiers and swarm workers sonnet. Never Fable without Mubarak's explicit OK. Never the bulk-worker agent type.
2. Playbook: Orchestrate (~/.claude/skills/poteto-mode/playbooks/orchestrate.md). Copy its seven steps verbatim as the first todos. A step you skip stays with "skip: <reason>".
   Also read shipping.md, pause-safely.md and session-pickup.md in the same folder. Use Shipping steps 1-3 for every verdict.
3. Never spawn a poteto-agent to run the playbook. This chat runs it. Builders are delegates.
4. Standing orders: write D:\QMX-worktrees\qma2-ship\preferences.md before the first spawn, one numbered constraint per line.
   Paste it verbatim into every builder brief and every fix-round brief. When you restate an instruction, add a line instead.
5. Trail: keep decisions.tsv per show-me-your-work (one row per decision, with evidence). Every skill you use is a row.
   Each row says "Skill tool" or "Read <path>". Never write "followed in spirit".
6. Pilot first. The first packet goes through brief, build, verify, ledger and merge before a second builder starts.
   Fix the brief template from what the pilot shows.
7. Window: at most 3 builders in flight, subagent_type "poteto-agent", model "opus", run_in_background true. Refill as each finishes.
   Completions are queue events. Record the report, then verify. Never deep-review inside a drain.
8. The brief is the product. Every brief has GOAL, SCOPE (worktree, branch, files), CONTEXT (pointers plus upstream reports pasted in full),
   ACCEPTANCE, VERIFY (exact commands), TIMEBOX, FORBIDDEN, REPORT and STANDING. A field you cannot fill means the packet is not ready.
9. Verification is yours, at the exact head SHA. CI green and a builder's word are inputs, not verdicts.
   Run the gates and the live lanes yourself. Lanes are coverage boxes, not agents.
   Spawn a sonnet verifier (or a /swarm of at most 3 lanes, each with its own port and data dir) only when a unit's
   verification is expensive, judgment-heavy or high blast radius. Write the reason in decisions.tsv.
10. Record each verdict with head SHA, base SHA and git patch-id --stable. A new head voids the verdict unless the patch-id is unchanged.
11. Land only the contiguous verified run into rebuild/base, one PR at a time, then recompute. Never main or integration.
12. Contested design in a PR: run interrogate (reviewers per pstack-models: opus plus sonnet). Otherwise skip it with the reason.
13. Wake: background-agent completions are the main wake. On Mubarak's go, arm /loop 1h with the multi-phase-plan tick prompt.
    That prompt re-reads orchestrate.md, judges progress only by side effects (commits, pushes, PR deltas), and replaces a stuck builder.
14. After any context compaction, Read poteto-mode SKILL.md and orchestrate.md again before the next action.
15. Audit each builder before its verdict. grep its transcript (~/.claude/projects/<slug>/<session>/subagents/agent-*.jsonl)
    for the Read of poteto-mode/SKILL.md and a Skill call for tdd. Missing either means a fresh fix-round builder, not a pass.
16. Write to Mubarak per poteto-mode "Writing the reply": short sentences, evidence or a label on every claim, PR links.
```

## (b2) Paste-ready "Method" section for the builder template

```text
## Method
You are a poteto-mode delegate. The orchestrator owns the playbook for the program. You own this packet's Feature run.
1. Read in full before any work: <ABS>/.claude/skills/poteto-mode/SKILL.md (Principles index included),
   ~/.agents/pstack-models.md, poteto-mode/playbooks/feature.md and poteto-mode/playbooks/opening-a-pr.md.
   Bundled skills live at ../<name>/SKILL.md from poteto-mode/SKILL.md. Read a leaf principle-* skill before you cite it.
2. To use any other skill, call the Skill tool with its name. If the call is refused, Read its SKILL.md in full. Say which in your report.
3. Open a todo list whose first items are the eight Feature steps, verbatim. Then mark them this way:
   - Step 1 (how): one inline pass over the files in SCOPE. You do not spawn. how allows "run each role yourself".
   - Step 2 (architect): "skip: shape fixed by ARCHITECTURE section 8", unless this brief asks for a sketch.
   - Step 4: own the diff directly. feature.md allows this for "A subagent forbidden to spawn".
     Call Skill("tdd"). Its pre-agreed seams are <acceptance file and public entry points>. Do not ask the user to confirm them.
   - Step 7 (interrogate): "skip: orchestrator reviews".
   - Step 8 (Opening a PR): reread the full diff and cut slop (stands in for deslop).
     Run ~/.claude/skills/no-comments/references/comment-sicko.md yourself over the diff (stands in for /no-comments).
     Write the PR body with technical-writing then unslop. Open it ready. Do not babysit.
4. Do not spawn agents. Where a skill wants a fan-out, use the fallback that skill names. Record it as "skip: <reason>" or "inline: <reason>".
5. Verify on the real surface with the project verify skill (verify-qmx-agents) before you report.
   "Inconclusive" or a check on the wrong surface is not a pass.
6. Report: PR URL, head SHA, base SHA, the done-when output, the just ci result, the todo list with every skip line,
   every principle you applied with the choice it changed, and every skill you used with "Skill tool" or "Read".
```

## (c) Cursor names and what to use in Claude Code here

| pstack says | Use here |
|---|---|
| `Task` tool, `generalPurpose` | `Agent` tool. Use `poteto-agent` for delegates (registered in `~/.claude/agents/`) and `general-purpose` where a routed skill prescribes it. |
| `environment: "cloud"` workers, Cursor Projects | Local worktrees under `D:\QMX-worktrees\`, one writer each. One standing orchestrator session plus `RESUME.md`. |
| `grok-4.7-xhigh-fast` (code), `claude-opus-5-5-xhigh` (judgment) | `opus` for code and judgment, `sonnet` for swarm workers and how/why explorers, per `~/.agents/pstack-models.md`. No Fable without the operator's OK. Never `bulk-worker`. |
| `~/.cursor/rules/pstack-models.mdc` | `~/.agents/pstack-models.md` (exists, budget medium). |
| "verifier on a different model family" | Opus and Sonnet are one family. State that limit, or ask the operator for a one-time Fable OK on a high-stakes verdict. |
| `control-ui` | Now: the built-in Browser pane for `/console`. Later, for SvelteKit: Reticle via `install-and-verify` or `verify-unattended`, then `verify-ui-change`, `agentic-tdd` and `audit-my-app`. |
| `control-cli` | A project skill `.claude/skills/verify-qmx-agents/` made by `/create-verification-skill`. It holds Launch (`qmx-control start`), Doctor, Drive (API through a small Python drive script, plus the console), Evidence and Cleanup. |
| `deslop` (cursor-team-kit) | Reread the diff and cut slop by hand (Harness line). `/simplify` is optional. |
| `/no-comments` Comment Sicko subagent | The orchestrator spawns it. A builder runs `references/comment-sicko.md` itself. |
| Bugbot, agentic security review | None on this repo. Use the orchestrator's diff audit, `interrogate` for contested PRs, and optionally Matt's `code-review` once on the final `rebuild/base`. |
| Origin, Graphite `gt` | `gh` only, never `gt`. |
| `scripts/watch-pr`, Babysit `drive` | Only useful once GitHub Actions runs exist. Until then the CI evidence is the local `just ci` log. |
| `/loop` (Cursor) | Claude Code's bundled `/loop`, plus `ScheduleWakeup` and `Monitor` for event waits. Background-agent completions are the main wake. |
| `agent-transcripts/` | `~/.claude/projects/<slug>/<session>.jsonl` and `.../subagents/agent-*.jsonl`. |
| `AskQuestion` / `create-skill` | `AskUserQuestion` / `skill-creator` or `writing-for-agents`. |
| custom mode (alt+enter) | None in Claude Code. A skill stays in context after load, but compaction keeps only its first 5,000 tokens. Re-Read after compaction. |

## Answers to the six questions

**1. How each creator sequences the work.**
- **poteto.** The order is understand, design, build and clean, verify, ship. You name the goal and the check, and the playbook does the ordering. "use /poteto-mode at the start of a task" (README). "Enumerating skills in the prompt" is a pitfall because it "reorders steps the playbook already sequences" (guide 10). Plans are optional: "i don't believe in planning. the best spec is code" (README). For queues the guide offers Autopilot-full, Autopilot-stack and Orchestrate (guide 07). Verification needs a scripted lever, and `/create-verification-skill` is how you make one (guide 06).
- **Matt.** The order is grill, spec, tickets, implement (tdd, then code-review), retro. "Each one's output is the next one's input" (aihero.dev/skills). Implementation runs per ticket, "`/clear`ing context between each one" (ask-matt). implement-spec runs "implementer subagents" over the ready frontier on one "integration branch". Rule: "A user-invoked skill may invoke model-invoked skills, but never another user-invoked one" (README).

**2. Which playbook fits the orchestrator.** Orchestrate, with Shipping's verify-and-land rules inside it. The reasons, in the playbooks' own words:
- Orchestrate is the one where the coordinator "never authors or edits code". "Mechanically landing a verified unit" is bookkeeping it may do itself (orchestrate.md:15).
- Autopilot-full has each owner merge its own PR (autopilot-full.md:3, :9). Our builders never merge.
- Autopilot-stack hands the operator "one linear base-branch stack to review and land" (autopilot-stack.md:3). Our orchestrator merges into `rebuild/base` itself.
- The selection rule (autopilot-stack.md:14) would pick Autopilot-stack, because our work "is sequenced or coupled". But that playbook's landing step contradicts our merge authority.
- Multi-phase-plan is the planning session's playbook. It says "A standing program takes `playbooks/orchestrate.md`" (multi-phase-plan.md:8).
- About 10 PRs over 3 days does not fit "one agent could finish inside that budget" (orchestrate.md:60). So the program stays Orchestrate, collapsed as "Ceremony must scale with the program" (:5): no sub-coordinators, no cloud, the first packet is the pilot (:62), and verification scales to the unit (:87).

**3. What makes poteto-mode work in Claude Code.**
- **Invocation.** The operator's pasted prompt must begin with `/poteto-mode`. Docs: at the start of a message "Claude Code runs the skill directly". After plain text a slash name only counts "as your permission for that message".
- **Builders.** `poteto-agent` already tells the builder to Read SKILL.md, which is the creator's own route for delegates (Harness, SKILL.md:106). Upstream adds that the parent should "put this file's absolute path in every `poteto-agent` prompt". For every other skill, try the Skill tool first (fact 2 above).
- **Models.** `/setup-pstack` is done. `~/.agents/pstack-models.md` maps every role to `opus` or `sonnet`. Skills read it when they pick a model (setup-pstack:11, SKILL.md:107).
- **Swarm lanes.** The multi-phase-plan default is "Ten lanes" on cloud VMs (multi-phase-plan.md:13), and check-plan.mjs:141 enforces exactly 10. Keep 10 lanes in the plan as coverage boxes, but run them in one boot by the orchestrator, which is top level and may spawn. Use `/swarm` with at most 3 sonnet workers only where orchestrate.md:87 says a dedicated verifier earns its place. Ten agents per PR times 10 PRs is about 100 runs, and that is not justified on Max 5x.

**4. Where Matt's skills fit now.**
- `tdd`: yes. It is model-invocable, so builders call it as a real Skill tool call, as upstream `implement` now says ("Call the Skill tool with tdd"). Name the seams in the brief, because tdd otherwise asks the user to confirm them (tdd:22). The local `tdd` is Matt's. pstack's own `tdd` (bug-fix only) is not installed.
- `implement-spec` (not installed): our orchestrator already follows its rules (frontier, background implementers, own worktree, "context pointers"). Borrow its rule that an implementer merges the integration tip before it reports. Do not install it mid-program.
- `to-tickets` adds nothing now. The plan is already in multi-phase-plan form. to-tickets bans file paths, and its approval step needs the operator. Use its vertical-slice and blocking-edge rules only as a checklist.
- `wayfinder` is only for fog, and there is none: decisions are made. It produces "decisions, not deliverables" and must "never resolve more than one ticket per session". It is user-invoked only.
- `code-review` is optional, run once by the orchestrator on the final `rebuild/base` (implement-spec step 7). It spawns two reviewers.
- `diagnosing-bugs` is for a fix round on a hard bug. `handoff` is for starting the UI session. `grill-me`, `grilling` and `to-spec` are not used: the operator's rulings are settled.

**5. Verification approach.** Backend plus console now: run `/create-verification-skill` once, from the orchestrator or a dedicated packet, after 1b gives a runnable host. It writes `.claude/skills/verify-qmx-agents/` with a feature map, and it must prove itself end to end before use (create-verification-skill:40). Then build the lever the guide asks for: a small JSON-output drive CLI the skill calls, not throwaway scripts (guide 06). Before 1b, builders verify with the done-when command plus `just ci`. UI session later: Reticle (`install-and-verify` once, then `verify-ui-change` and `agentic-tdd`), `audit-my-app` before handover, and the Browser pane for screenshots.

**6. Rules that stop "in spirit" runs.**
- Every skill use is either a Skill tool call or a full Read, and it is logged with its path. The words "in spirit" never appear in a prompt.
- Copy the playbook steps verbatim into the todo list. Removing a fan-out is a written `skip:` or `inline:` line that cites the skill's own fallback (how:22, swarm:34, feature.md:12), never a silent change.
- Say "done" only with an evidence pointer. "Grilling done" with no grilling call is a false claim.
- The orchestrator greps builder transcripts for the Read and Skill calls (rule 15 above). A miss fails the unit.
- Enforce no nesting in settings (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`), not only in prompt text (principle-encode-lessons-in-structure).
- User-invoked skills such as `wayfinder` run only when the operator types them. "Ran its method by hand" is not a run. If the work has no fog, say so and stop (wayfinder step 2).
- Re-Read the skill files after compaction, and at every `/loop` tick.

## (d) Evidence

Creator pages (read in the browser, 2026-10-13):
- github.com/cursor/plugins/tree/main/pstack README: "do not spawn poteto-agent to run the playbook itself"; "the best spec is code".
- raw.githubusercontent.com/cursor/plugins/main/pstack/docs/guide/06-verify-and-ship.md: "Create a project verification skill"; build a control CLI.
- .../07-overnight.md: Autopilot-full, Autopilot-stack, Orchestrate for queues; "a duration is not a finish condition".
- .../10-recipes-and-pitfalls.md: "Enumerating skills in the prompt"; "Parallel agents in one worktree".
- github.com/backnotprop/pstack README and MIRROR.md: the harness-neutral mirror of cursor/plugins.
- github.com/mattpocock/skills README: "A user-invoked skill may invoke model-invoked skills". aihero.dev/skills: main flow, changelog v1.3.
- raw .../mattpocock/skills/main/skills/engineering/implement-spec/SKILL.md and implement/SKILL.md ("Call the Skill tool with tdd").
- code.claude.com/docs/en/skills: disable-model-invocation, slash name placement, the compaction 5,000-token rule. code.claude.com/docs/en/sub-agents: nesting default of 3 and the spawn-depth variable.

Local files (C:/Users/Mubarak/.claude/):
- skills/poteto-mode/SKILL.md:15 (cite only principles you read), :93 (poteto-agent for delegates), :95 (Task defaults), :99 (fresh subagents), :101-111 (Harness), :133 (verbatim todo list with skip lines), :135 (figure-it-out versus Orchestrate), :152-154.
- skills/poteto-mode/playbooks/orchestrate.md:3, :5, :15, :52, :60, :62, :87. autopilot-stack.md:3, :14. autopilot-full.md:3, :9. multi-phase-plan.md:8, :13, :15. feature.md:12. shipping.md:7-9. opening-a-pr.md:36.
- skills/how/SKILL.md:22, skills/swarm/SKILL.md:34, skills/no-comments/SKILL.md:18, skills/create-verification-skill/SKILL.md:9, :40, skills/setup-pstack/SKILL.md:11, skills/tdd/SKILL.md:22, skills/implement/SKILL.md:9, skills/ask-matt/SKILL.md:23, skills/poteto-mode/scripts/check-plan.mjs:141.
- agents/poteto-agent.md:9. ~/.agents/pstack-models.md (budget medium, opus and sonnet only).
- Version drift: `diff` against upstream main gives 0 lines for orchestrate, autopilot-stack, autopilot-full, multi-phase-plan, feature, shipping and pause-safely. It gives 126 lines for poteto-mode/SKILL.md (cursor) and 106 (mirror). Matt: 6 to 75 lines per skill, implement-spec absent.
- QMX: tracker/qma-v2/ORCHESTRATOR-PROMPT.md:76, :116. reviews/2026-10-13-planning-phase-audit.md:21-22, :98-99 (the "in spirit" runs, zero Skill calls, Wayfinder never re-run).
- Measured: this subagent's transcript `.../subagents/agent-a9c0263d855ebc71a.jsonl` contains `"name":"Skill","input":{"skill":"unslop"}`.
