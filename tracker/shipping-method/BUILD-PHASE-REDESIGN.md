# Build phase redesign (12 November 2026, proposal)

Status: proposal, applied on 12 November (evening) with his rulings, which override it where they differ. It redesigns build, landing, checkpoint review and merge so they use what the planning funnel now hands over. Written by one Fable agent, on his explicit ask.

## Applied (12 November, evening)

His rulings on applying it: no AI reviewer per slice (question 1: yes); Skylos, Vulture and mutmut as a ratchet where only new findings block and baseline findings become backlog rows; Windows runs the whole suite at every checkpoint, locally while GitLab CI is paused (question 4: yes, local gate); pre-build one checkpoint ahead on files nothing held or in review touches (question 2: yes); the review collects all findings, then sends one fix batch; the power watcher covers review and merge; builders write their PR body with a `TRACE:` line and no credit line; and merging is the last step of the checkpoint review session, not its own phase (`MERGE.md` is a manual entry only). Questions 3 (Fable for the fault walk) and 5 (self-recovery without a test stops the merge) were not ruled on: the files use Opus, and treat a missing self-recovery test as Important.

| Item | State | Where |
|---|---|---|
| 1. `land` without a slice verdict | Done. Setting `slice_verdict_required`, off. A changed rebase sends the slice back to `slice_checks` (`RECHECK`) | `ship/kit`: `land.py`, `settings.py` |
| 2. Rules card | Done. Reviewer rows gone; pre-build; checkpoint hand-off; no teardown at a checkpoint | `standing/RULES-CARD.md` |
| 3. Arm without a grounding agent when the facts are fresh | Done | `prompts/COORDINATOR.md` |
| 4. Builder prompt | Done. `how.md` and the END lines stay (the ready script needs them); `pr.md` with `TRACE:` added | `prompts/BUILDER.md`, `PROJECT-RULES.md` |
| 5. Checkpoint review | Done, with merge as its last step, power heartbeat, reader notes ending `DONE` | `prompts/STOP-REVIEW.md`, `skills/slice-review/SKILL.md` |
| 6. `REVIEW.md` | Done | `standing/REVIEW.md` |
| 7. Merge | Done, inside `STOP-REVIEW.md`; `MERGE.md` is the manual entry | `prompts/STOP-REVIEW.md`, `prompts/MERGE.md` |
| 8. Plan review runs `check_chain.py --stage handoff` | Done by the funnel session | `prompts/PLAN-REVIEW.md` |
| 9. Chain packets | Done by the funnel session (`chain_packet.py`) | `standing/funnel/` |
| 10. `ship facts --tip` | Remains | |
| 11. `ship trace` | Remains. The review builds `MAP.md` by hand meanwhile | |
| 12. `verify_ready` | Partly. `TRACE:` and the no-credit check are done; dropping END lines and `how.md` remains | `verify_ready.py` |
| 13. `slice_checks` | Partly. SAFETY at the head, Vulture and Skylos are done; the scenario ledger and removal guards remain | `slice_checks.py`, `quality.py` |
| 14. `land` adds neighbours' packages, prints Linux NOTRUN | Remains | |
| 15. Quality tools at the checkpoint | Done as `ship quality --from` plus `ship baseline [--part K/N]`, next to `nightly`. The baseline is not taken yet | `quality.py` |
| 16. `run_report` by ask, four numbers | Remains | |
| 17. `check_plan.py` fact blocks | Not mine; check the funnel session's state | |
| 18. Watcher through review and merge | Done as `ship power` and the review's own heartbeat. `phase_state.py` reporting an interrupted review remains | `power_watch.py`, `STOP-REVIEW.md` |
| 19. Pre-build one checkpoint ahead | Done: `dispatch`, `status` (`PREBUILD`), `land` (`HELD`), `ship merged` | `state.py`, `dispatch.py`, `status.py`, `land.py` |
| 20. GitLab backend behind `suite.run_packages` | Another agent, branch `ci/gitlab` | |
| 21 to 24. Funnel and templates | The funnel session's (checkpoints, lanes, section 11, chain packets) | |
| 25. Commit `tracker/REMOVED.md` after merges | Remains | |
| 26. `SHIPPING-METHOD.md` | Done, rewritten (draft 4) | |
| 27. `REVIEWER.md`, `slice-review`, `GROUNDING.md` | Partly. `slice-review` is the checkpoint reader's method; `REVIEWER.md` is listed as retired; `GROUNDING.md` wording remains | |

Read for it: `PLANNING-FUNNEL.md`, `standing/funnel/CHAIN.md`, the six `funnel-*` skills, `FUNNEL-CHANGES.md`, `SHIPPING-METHOD.md`, everything in `standing/`, `EDGE-CASES-2026-11-12.md`, the ship kit's `README.md`, `SPEED-REVIEW.md`, the four stacked audits, the scope audit, and his own turns in today's sessions (found with `his_words.py`; sources are `<session>:L<line>`).

The five phase skills (`plan-feature`, `plan-review`, `ship-build`, `stop-review`, `ship-merge`, plus `ship-next`) and `prompts/NEXT-PHASE.md` already exist. This proposal changes what the prompts say, not how the sessions chain.

"Checkpoint" below means a stop point: the place where the review session runs and the work merges.

## The shape

| Phase | Who | What happens | Gate |
|---|---|---|---|
| **Build** | Coordinator and builders only | Builders turn briefs into code. No AI reviewer per slice | Scripts: files inside the brief, the trace line, facts, the safety fact, fast checks, fail-at-parent. A red result gets a fresh fixer |
| **Landing** | Script | Touched tests on the merged batch | No new red |
| **Checkpoint review** | Its own session, every 5 to 8 slices | The deep check run starts first. In parallel, Opus reviewers read the batch against the chain, the architecture and the edge cases. Findings become one fix batch | Review clean, and the deep run green |
| **Merge** | Its own session | No new checks. It lands without him | The two results above |

**Checks today and later.** CI is paused, so every level runs on the laptop through the ship scripts for now. When GitLab is switched on, the same levels move there behind one function (`suite.run_packages`), and nothing else changes.

| Level | Today, on the laptop | Later, on GitLab |
|---|---|---|
| Per slice | `slice_checks`: lint, types, touched tests, fail-at-parent, on Windows | The same on Linux, about 15 to 25 minutes |
| Landing | `land`: touched tests on the merged batch, on Windows | Linux and Windows |
| Checkpoint | `nightly`: the whole repo once, plus Skylos, Vulture and incremental mutmut | The same, sharded, on both systems |

Until then, Linux prints as "not run" in every report. It is never hidden.

## His words this answers

| He said | Where | What this proposal does with it |
|---|---|---|
| "the build and coordinator, its whole point is literally just turn the PRs into code. That's it." | dd8f4ab2:L2543 | The build holds coders and scripts only. No reviewer, no grounding agent when the facts pass |
| "So coordination does only building" and "I was suggesting we do an independent review session." | dd8f4ab2:L2516 | All AI review moves to the checkpoint session |
| "review is ... against the intended designs, architecture, and PRs" | dd8f4ab2:L2543 | The checkpoint review's walks are those three, along the chain |
| "By the time the review agents have given a thumbs up, I don't think that you really need me to merge." | dd8f4ab2:L2543 | Merge does not ask him. With CI paused, see question 4 |
| "the coordinator can maybe first ground the PRs" and "it's like a singular back and forth ... then the coordinator begins autonomy" | dd8f4ab2:L1769 | Still stands, but it shrinks. See "Plan review and step 0" |
| "It's not about the plan, it's about the PRs." and "is the plan solid enough before it gets to the coordinator?" | dd8f4ab2:L2516 | The PR-against-code read belongs before the coordinator. It sits in plan review |
| "Did we actually remove it?" (plan review) | dd8f4ab2:L4076 | No. It is still its own session. Stated plainly below |
| "by the time we reach plan review, there is really not much of questions" | dd8f4ab2:L2705 | Plan review is mostly a technical check now. He is asked little there |
| "the funnel really changes a lot of things here" | dd8f4ab2:L4076 | Every role reads its part of the chain. See the role tables |
| "Speed ... it may be the main thing" and "rerunning an entire repo test, well, you have 40 plus PRs going. Doesn't make sense." | dd8f4ab2:L1482 | Cheap checks per slice, the whole repo once per checkpoint. See Speed |
| "Claude Cache for sub-agents ... I think it expires, and I don't think it lasts 30 minutes." | dd8f4ab2:L3951 | Builders never wait on a check. Scripts wait. Fixers are fresh agents |
| "a workflow, that I can leave overnight" and "when power goes off, internet goes off, which means I have to sort of babysit" | 66d0c236:L214, L229 | The power watcher, battery rule and restart rules stay as built. One gap found: the review and merge sessions. See "The morning's failure list" |
| "agents getting stuck at ... the dumb issues while reviewing" | dd8f4ab2:L2795 | No reviewer sits in the build loop any more. At the checkpoint, proof-or-drop stays |
| "almost everything in QMX has to have a DevOps layer ... Whether I mention it or not" and "a system sort of can get itself back online without them" | dd8f4ab2:L3099, L3132 | Each slice proves its operations point with a test. The checkpoint makes parts fail and watches them recover |
| "the agents may build something that is very similar to what was again deleted" | dd8f4ab2:L2973 | Removed rows reach every builder, and a script reruns removal guards |
| "a stop rule that isn't a cap" | dd8f4ab2:L2795 | No new caps. "5 to 8 slices" is a guide the planner aims for, with a warning past it, never a refusal |
| "Let me first pause the GitLab pipeline. I think it's unnecessary for now." | dd8f4ab2:L4076 | Everything here runs on local checks first |
| "Windows and Linux, I think, first." | dd8f4ab2:L1769 | Windows is checked at every landing today. Linux arrives with CI |
| "that deep opus reviewer ... only on money and exits and breaks may not make sense" | 66d0c236:L229 | Every checkpoint gets the full review. Question 3 only asks about a stronger model for one walk |

## Does the evidence support review outside the build?

Yes, with small checkpoints. Here is the test.

**What the per-slice reviewer was worth.** In the old build it caught about 10 real faults in 21 slices, and "every real money-path catch was its" (`SPEED-REVIEW.md`). That is the cost of removing it: on those numbers, about one slice in two lands on the build branch with a fault inside it.

**Why that cost is acceptable now.** Each kind of fault it caught has a new owner:

| What the slice reviewer caught | Who catches it now |
|---|---|
| A test that cannot fail (the old "money-door test") | Fail-at-parent on every slice, by script. Mutmut at the checkpoint |
| A broken fixed line (the old "warning that released a brake") | The safety fact, rerun by script at every slice head. The fault walk at the checkpoint |
| Files or code outside the brief | The ready script, on every slice |
| The brief not met, a scenario not handled | The scenario tests, written first and run on every slice. The element reader at the checkpoint |
| Stale numbers in tests (9 of 26 old fix rounds) | The touched tests, on every slice |

**What it could never catch.** The six high bugs. All six sat between slices or on fault paths. Only a review of the batch as a whole finds those, and that is where all the review effort now goes.

**What it cost.** Ready-to-verdict was 0.65 hours at the median, and the repair loop 0.93 hours, on 16 of 21 slices. About 6 of 26 fix rounds were paperwork. That is the "stuck on small issues" cost he named.

**The risk: problems pile up before review.** On the old numbers, a checkpoint of 6 slices would carry about 3 faults inside slices and 1 or 2 across them. That is a fix batch of about 4 or 5 items, which one round can clear. At 28 slices it was 6 highs, 3 slices to rework and a scope audit, found too late.

**Is 5 to 8 the right size?** The evidence supports it, three ways:

- The audits that found the six highs split 28 slices into groups of 6 to 8 per reviewer (G1: 8, G2: 6, G3: 7, G4: 7). That is the size at which one reviewer demonstrably held the work in its head and found cross-slice bugs.
- The speed review's own advice was a whole-repo check "after every eighth row".
- With 3 seats, 6 slices is about two layers of dependency. So a fault is built on by at most one or two later slices before review sees it.

Below 5, the fixed cost of a checkpoint (one whole-repo run, one review session) is paid too often. Above 8, there is no evidence a reviewer still sees the whole batch.

**One rule that keeps the pile small.** Unreviewed work is never more than one checkpoint deep. Builders may start the next checkpoint's slices during a review (question 2), but none of those lands until the checkpoint under review has merged.

**How to check this claim.** The run report prints, per checkpoint: findings inside a slice, findings across slices, and how many later slices had been built on each. If in-slice findings stay above about one slice in two with Opus builders, the cheap fix is a smaller checkpoint, not a reviewer back in the loop.

## Plan review and step 0: what stands now

**Plan review was not removed.** It is still session 2, with its own skill. The funnel changed its job. The funnel now handles his asks, the ambiguity and the scope, so plan review is mostly the technical check he described: are the PRs right against the code, and do they collide. It still holds the scope gate (his go) and asks him the few open questions left.

**His grounding idea still stands. It moves one session earlier and gets cheaper.**

| The job he described | Where it lives now |
|---|---|
| Read every PR against the real code | Plan review (its grounding agent). Once, by a session that did not write the plan |
| Find collisions: with code that exists, between slices, with branches in flight | Funnel stage 2 lists branches in flight. Plan review's grounding agent checks the other two |
| Send flaws back to the planner, one round trip | Plan review, step 4. Already written that way |
| Then run on its own | The coordinator |

**What remains for the coordinator.** At arm time the build branch sits on the exact commit plan review just checked. An agent re-reading every brief there repeats work minutes old. A script reruns every brief's facts instead, at the build tip and at the target branch's tip (in case `engine/base` moved since planning).

- All pass: it starts building. No agent, no round trip.
- A fact fails: only those slices go to a grounding agent. Its findings get the one round trip with the planner he described. Design calls still park.

Before each later checkpoint the code has really moved, because slices landed. The same script runs first, and again only the failing briefs go to an agent.

**One duplicate to remove on the funnel side.** The handoff (stage 6, step 9) also has a fresh reader check every brief against the code. Plan review's grounding agent does the same from an independent session. One is enough. I would keep plan review's.

## What the six high bugs have in common

| Bug | What went wrong | Why per-slice review missed it |
|---|---|---|
| rc-10 | The host fails after the unit creates an exit. The exit is lost for good | The fault is in another package. The slice's tests never drive it |
| rc-11 | One exit block raises. Every exit of the position is blocked, every bar | Filed as "low 6". It breaks "exits are never blocked" |
| rc-13 | A brake block raises. The brake is gone after one step, so it fails open | The tests only drive a working brake |
| rc-21 | A size modifier returns an extreme but allowed number. A held exit is dropped | The earlier sizer fix (rc-28) did not cover this path |
| rc-16 | A `flatten` brake never refuses entries, while the fold says HALTED | Filed as "low 6". Two slices use one word for two things |
| rc-30 | A live 15-minute bar is dropped when one minute is quiet | An Opus re-review found it and wrote NOT CLEAN. The ledger kept saying CLEAN |

Four of the six are one shape: **a part on a fixed line's path fails, and the fixed line quietly breaks.** One is two slices disagreeing on a word. One is a record that lied.

## The chain packet: one generated file per slice

Today a builder reads the brief, the house rules and one ask in `SCOPE.md`. The plan lines, the element, the scenarios and the removed rows sit in six other files it never opens.

**Proposal:** at handoff, a script writes `slices/<id>/CHAIN.md` for every slice. Nobody edits it by hand. It holds only what that slice's `Chain:` line cites:

- the ask, in his words, with its source;
- the plan lines, including any marked "my reading";
- the architecture elements, and the operations points they carry;
- the edge cases, in full;
- the can-change rows it carries out;
- the removed rows for its files: "never rebuild these";
- the ground facts and fixed lines that name its files;
- its neighbours: other slices that share an element or an edge case with it.

The builder reads the brief, this packet and `PROJECT-RULES.md`. The checkpoint reviewers read the packets of the batch.

## What changes for each role

### Coordinator

| | |
|---|---|
| **Now reads** | `PROGRAM.yaml` with its `chains:` rows, `SLICES.md`, the rules card. Not the architecture or the plan; its context stays small |
| **Stops doing** | Spawning a grounding agent at arm time when the facts pass |
| **Stops doing** | Spawning reviewers, reading verdicts, routing disputes and range reviews. A slice goes ready check, slice checks, landing |
| **Newly does** | Sends a red check to a fresh fixer with the summary file. A second red parks the slice |
| **Newly does** | Routes `BLOCKED chain <id>` (a builder says a plan line, element or edge case is wrong) to the planner's change route, not to him |
| **Newly does** | Reports by ask, not by slice: "S2: 3 of 4 slices landed, pd-07 parked." He can read that |
| **Newly does** | At the checkpoint, runs the trace script and starts the review session |

### Builder

| | |
|---|---|
| **Now reads** | The brief, the chain packet, `PROJECT-RULES.md`, and `facts.log` from dispatch |
| **Stops doing** | Rerunning every fact, and running the safety fact at the parent. Dispatch just did both in the same worktree |
| **Stops doing** | Writing `how.md` from zero. `GROUND.md` and the element already say how the area works. Two short sections in `report.md` replace it: "what I found that the plan did not say" and "values I moved, and where I searched for them" |
| **Stops doing** | Hand-writing `END <sha> <id>` lines on evidence files. Evidence sits in a folder per attempt, and the READY line proves the builder finished. A typo there costs a whole fix round today |
| **Stops doing** | Writing the trace into the PR. The ready script adds `TRACE: <slice> -> <plan lines> -> <ask>` from the chain |
| **Still never does** | Wait on a long check. Scripts run them after it replies |
| **Newly does** | Writes the tests for its scenarios and its operations point first, each driving the failure, not the working path. With no reviewer behind it, these tests are the slice's proof |
| **Newly does** | Refuses to rebuild a removed row. If the brief seems to require it: `BLOCKED chain R-<id>` |
| **Newly does** | Reports up the chain. `BLOCKED chain <id> <why>` when the plan itself is wrong. A `DECISION <chain id>: chose X because Y` line in `report.md` for every reading it picked. Findings it did not build carry a chain id, or "no ask" |

### The slice gate (scripts, no agent)

| Check | Script |
|---|---|
| Changed files are inside the brief; the PR carries its trace line | `verify_ready` |
| Lint, types, touched tests; each new test fails at the parent on an assertion | `slice_checks` |
| Every scenario in the brief names a test, and that test ran and passed | `slice_checks` (new) |
| The safety fact gives the same output at the head | `slice_checks` (new) |
| The removal guards still hold | `slice_checks` (new) |

### Landing

| | |
|---|---|
| **Stops doing** | Requiring a CLEAN verdict, and calling for a range review after a rebase. A changed patch after a rebase means the slice checks run again on the rebased head |
| **Stays** | Tests on the merged batch. Local on Windows today; both systems with CI |
| **Newly does** | Adds the packages of every landed neighbour (a slice sharing an element or an edge case) to those tests. Today it tests only the packages the batch touched, so a slice that changes what a neighbour relies on can land green |

### Checkpoint review

See the next section.

### Merge

| | |
|---|---|
| **Now reads** | The review verdict, the deep run's result, the trace file, the program's `REMOVED.md` |
| **Stops doing** | Running or waiting on checks of its own. Review clean plus the deep run green means it lands |
| **Stops doing** | Grounding the next checkpoint's briefs with an agent. The facts script runs first; only failing briefs go to an agent |
| **Newly does** | Refuses while any BLOCKED verdict in the program folder has no later CLEAN for the same code. A script checks it. This is the rc-30 failure |
| **Newly does** | Moves this checkpoint's planned removal rows to `tracker/REMOVED.md` with the merge sha |
| **Newly does** | Tells him what merged per ask, in his words: "You asked for X. Now true: ... Parked: ... For the next plan: ..." |
| **Still does** | Asks him only for a problem that cannot be fixed and touches money, his sign-ins or the fixed lines |

## The checkpoint review: how it uses the chain and the architecture

Today's prompt says: read every landed diff and every verdict, then judge through three lenses. That gives the reviewer no map. The audits worked because they took his words, walked to the code, and ran probes at the tip.

**First, two things start at once.**

- **The deep run:** the whole repo, Skylos, Vulture and incremental mutmut, as a background command. Nobody waits for it; the session reads the result when its reviewers are done.
- **`ship trace`,** which writes the map for the checkpoint:
  - per ask: its plan lines, elements and slices, each slice's state and landed commit;
  - commits with no chain (any is a blocker);
  - seams: every element, edge case or file that two or more slices touched;
  - the scenario ledger: every edge case, its test, and that test's result at the tip;
  - `GROUND.md` facts that moved; removal guards; every builder `DECISION` line.

**Then the reviewers, in parallel.** Fresh Opus agents, split by architecture element, not by slice order. Each element reader gets every slice of its element, so both sides of a seam sit in one head. Every Important needs a run at the tip as proof. A candidate with no proof is dropped.

1. **Each element, read whole.** For each slice of the element: is the brief met, can each test fail, does each scenario test drive the failure. Then the seams: do the slices agree on every value, word, contract and registry they share, and does any test pass only because the neighbour is faked. This is the in-slice read the build no longer does, done once, with the neighbours in view.

2. **Down the chain: is each plan line true?** For each ask, take each plan line ("what is true when done") and each of his rulings the checkpoint touches. Prove it at the tip with a command or a test. This catches rc-16: "a brake stops new entries" is false for `flatten`, and one run shows it.

3. **Up from the code: does everything serve an ask?** The trace lists unchained commits. The reader checks the hunks too. This is the scope audit, done every 5 to 8 slices, not after 28.

4. **The fixed-line fault walk.** Aimed at four of the six highs. For each fixed line and ruling under "Fixed lines touched" in `GROUND.md`:
   - List every part on its path at the tip, from the element index and the diagrams, plus the older modules the ground facts name.
   - For each part, ask each fault kind: it raises; it returns an extreme but allowed value; it is missing or quiet; the host fails between two of its steps; it restarts halfway.
   - Each cell ends one of three ways: a named test in the scenario ledger passes; a probe run now shows the line holds; or it is an Important finding.

   rc-10, rc-11, rc-13 and rc-21 are each one cell of that table for the old build. The fault-kind list lives in `REVIEW.md` and grows when a new kind is found.

5. **The operations layer.** Each line under `## Operations` in the architecture is a claim. Self-recovery matters most: "it falls back safely" is what failed in rc-13. Prove each self-recovery line by making the part fail and watching it come back. Check the alarm fires only when recovery fails.

**Then the session itself:**

- **Screens the builder decisions.** Is each one a product call in technical clothes, or does it touch a fixed line? A cleared one is logged as "the builder decided X because Y". A product call that touches a fixed line, a ruling or a one-way door is Important. Any other is listed for him at merge with a recommendation, and does not hold the merge.
- **Reads the deep run through the chain.** A red test is a finding. Dead code a can-change row planned to delete and that is still there is a finding; new dead code is scope creep. A surviving mutant under a fixed-line scenario test is a finding; other survivors are logged.
- **Writes one verdict** with one severity rule: a proved finding on exits, brakes, the kill switch, money or keys is Important, never a Nit. Two of the six highs were filed as lows.

**Findings become one fix batch.** Each fix brief cites the chain ids it repairs. Each finding becomes a scenario with a test that fails first. The batch runs through the build. Then only what changed is rerun: the touched tests, mutmut on the changed lines, and a round-2 read of the fix diff. Clean means merge.

**What this would have caught**

| Bug | Caught by |
|---|---|
| rc-10, rc-11, rc-13, rc-21 | Walk 4, and the severity rule for rc-11 |
| rc-16 | Walk 2 (the ruling proved by a run), walk 1 (the word HALTED across two slices) |
| rc-30 | The unanswered-BLOCKED check at merge, for certain. The scenario ledger, if planning wrote "the live feed has a quiet minute" |
| 13 slices with no ask, 5 against his rulings | The funnel's chain check at plan time. In the build, the trace line and walk 3 keep it that way |

One honest limit: the chain alone would not have caught the four fault bugs. The funnel asks for one edge case per fixed line, and those four are four different faults on one line. Walk 4 finds them. Each one it finds goes back to planning as a new edge case.

## The morning's failure list, checked against this design

| Item | Status here |
|---|---|
| Power cuts and the battery rule | Unchanged for the build: `power_watch`, `HOLD`, `recover`, restarts not counted as attempts. **Gap found:** the review and merge sessions have no watcher. A power cut during a review kills its agents and nothing restarts them. Smallest fix: each reader writes its notes to a file when done, so a rerun skips finished work; `phase_state.py` reports the review as interrupted; the power watcher keeps running through review and merge, and starts `ship-next` when power and internet are back |
| Unattended autonomy | Stronger. Arm time waits on no agent when the facts pass. The build loop has no verdicts or disputes to get stuck on. A wrong plan line goes to the planner, not to him |
| Speed | See the next section |
| Builders never waiting | Kept. Fixers are fresh agents |
| Review as its own session | Now the only place AI review happens |
| Merge without him | Kept. With CI paused, see question 4 |
| Windows at landing | Kept, locally. Linux is printed as "not run" until CI |
| Reviewers stuck on small issues | Gone from the build loop. At the checkpoint: proof-or-drop, and Nits never block |
| DevOps and self-recovery in every feature | Each brief's operations point needs a test. Walk 5 proves self-recovery by breaking the part |
| No hard caps | None added. 5 to 8 is a planning guide with a warning |
| The "removed, and why" list | In every chain packet. Guards rerun at each slice and at the checkpoint. Merge moves the rows |

## Speed

Measured numbers are from the old risk build (`SPEED-REVIEW.md`): 21 slices in 46.2 hours, 2.2 hours a slice overall and 2.45 after the speed orders. That is about 10 slices a day, round the clock. Everything below is an estimate built from those measured parts. Nothing here has been run.

**One slice**

| Step | Old build (measured, median) | This shape (estimate) |
|---|---|---|
| Build | 0.96 h (0.77 h before builders ran long suites) | About 0.8 h |
| Wait for a reviewer, and the review | 0.65 h | 0 |
| Checks | 0.4 h (24 minutes) | 0.3 to 0.4 h, in the background |
| Repair loop | 0.93 h, on 16 of 21 slices | A fixer for a red check on perhaps 1 slice in 3: about 0.5 h plus the recheck |
| Seat time per slice | About 1.7 h | About 1 h |

**One checkpoint of 6 slices**

| Step | With GitLab | Laptop only (today) |
|---|---|---|
| Build 6 slices, 3 seats, two layers of dependency | 3 to 4 h | 4 to 5 h (checks share the laptop) |
| Deep run | 0.5 to 1 h, sharded | 1.5 to 3 h (the whole repo took 2.3 to 3 h with 2 workers; 4 workers were advised) |
| Reviewers, in parallel with the deep run | 1 to 1.5 h | 1 to 1.5 h |
| Fix batch of 4 or 5 items, and its checks | 1 to 1.5 h | 1.5 h |
| Rerun what changed, round-2 read, merge | 0.5 h | 0.5 to 1 h |
| **Review, start to merge** | **about 3 h** | **about 4 to 5 h** |
| **Whole cycle** | **6 to 7 h** | **8 to 10 h** |

**Slices a day, round the clock**

| | Slices a day | Hours a slice |
|---|---|---|
| Old build (measured) | about 10 | 2.2 to 2.45 |
| This shape, laptop only | 14 to 18 | 1.3 to 1.7 |
| This shape, with GitLab | 20 to 24 | 1.0 to 1.2 |
| With the next checkpoint pre-built during review (question 2), laptop only | 20 to 25 | about 1 |
| The same, with GitLab | 30 to 36 | 0.7 to 0.8 |

These are merged slices, already reviewed as a batch. The old 2.2 hours bought a slice that still needed the audits.

**Where the gain comes from, in order:**

1. No review wait and far fewer repair rounds in the build loop. The old repair loop alone was about 20 hours over 21 slices.
2. Seats that do not sit empty. Empty seats were the old build's largest cost, about 22 hours; 5.5 of them at one stop.
3. The whole repo once per checkpoint. His words: rerunning it per PR "doesn't make sense".
4. No grounding agent at arm time when the facts pass: an estimated 30 to 60 minutes per start.
5. Scope held by the chain. The scope audit cut 69 slices to 47; at 2.2 hours each that is about 48 hours not spent. The funnel earns this; the build keeps it.

**What could make these numbers wrong.** The rate of in-slice faults with Opus builders is not measured; a larger fix batch stretches the checkpoint. The laptop's whole-repo run is the longest single step until CI returns. The run report should print four numbers per checkpoint so the next review is measured: red checks per slice, hours with an empty seat, findings in and across slices, and review start to merge.

## The smallest set of edits

Applied as the table under "Applied" at the top says. Split in two, because he wants to build again today. The first run is the repair slice for the six bugs. Items marked (known) come from `FUNNEL-CHANGES.md`, "Not done".

### Before today's run: about one to two hours

One small script change, then prompt edits.

1. `land` and `settings.py`: a setting `slice_verdict_required`, default off. With it off, `land` takes every slice whose checks are green, and after a rebase that changes the patch it asks for the slice checks again in place of a range review.
2. `RULES-CARD.md`: remove the reviewer rows. Green slice checks go to `ship land`. Red goes to a fresh fixer with the summary. `BLOCKED chain` goes to the planner.
3. `prompts/COORDINATOR.md`, Arm steps 2 and 3: skip the grounding agent when plan review's grounding report ends with the build tip's sha. Dispatch already reruns each slice's facts. Otherwise run it as now, with the one planner round trip.
4. `prompts/BUILDER.md`:
   - read `facts.log`; do not rerun the facts or the safety fact at the parent;
   - write the scenario and operations tests first, each driving the failure;
   - never rebuild a removed row;
   - reply `BLOCKED chain <id> <why>` when the plan itself is wrong;
   - write a `DECISION` line in `report.md` for each reading picked.

   `how.md` and the END lines stay for now, because the ready script still requires them.
5. `prompts/STOP-REVIEW.md`: replace round 1 steps 1 and 2 with the section above: start the deep run (`ship nightly` and the quality tools, in the background), then the five walks with readers split by element, the decision screen, and one fix batch. Until `ship trace` exists, the session builds the seam list itself from `PROGRAM.yaml` chains and `git log --name-only`. Each reader writes its notes when done.
6. `REVIEW.md`: the severity rule; blocker 6 covers removed rows; the fault-kind list; say that slice-level blockers are now judged at the checkpoint.
7. `prompts/MERGE.md`:
   - no checks of its own: review clean and the deep run green;
   - refuse while any BLOCKED verdict has no later CLEAN (by a search, until the script exists);
   - move the planned removal rows to `tracker/REMOVED.md` (known);
   - the per-ask note to him;
   - the local gate, if he says yes to question 4.
8. `prompts/PLAN-REVIEW.md`: also run `check_chain.py --stage handoff` (known).

**For the repair slice itself.** Each of the six bugs becomes a scenario in its brief, with a test that fails first. The four fault bugs are four cells of the fault walk, so its checkpoint review is the first real trial of walk 4. It is one small checkpoint, so it also gives the first measured numbers.

### After the first run

**Scripts**

9. `check_chain.py --packets`: write `slices/<id>/CHAIN.md` for every slice. Until then, the brief's `Chain:` line and section 7a carry the context.
10. `ship facts --tip <sha>`: every brief's facts, `GROUND.md`'s facts and the removal guards at one commit. It replaces item 3's rule and the next-checkpoint grounding agent.
11. `ship trace --stop <X>`: the checkpoint's map. Exit 1 on an unchained commit, an edge case with no passing test, a failed guard, or an unanswered BLOCKED verdict.
12. `verify_ready`: require only `red.log` and `report.md`; no END lines on builder evidence; add the `TRACE:` line (slice id and ask) to the PR body (known).
13. `slice_checks`: the scenario ledger for the slice, the `SAFETY` fact at the head, and the removal guards, each as a pass or fail line.
14. `land`: add neighbours' packages to the merged-batch tests; print Linux as NOTRUN.
15. `nightly`: run Skylos, Vulture and incremental mutmut with the whole-repo run, and write one result file the review and merge read.
16. `run_report`: group by ask; print the four numbers named under Speed.
17. `check_plan.py`: strip fact blocks before the placeholder scan. Real fact output with `<...>`, such as Svelte markup, fails it today (known). Do this first if the next program has a UI slice. Also warn, never refuse, when a stop point holds more than 8 slices.
18. `power_watch` and `phase_state.py`: keep the watcher alive through review and merge, and start `ship-next` when power and internet are back.
19. Only if question 2 is yes: `dispatch` may start the next checkpoint's slices during a review, and `land` holds them until the merge is recorded.
20. When GitLab is switched on: the CI backend behind `suite.run_packages`. The slice pipeline starts once, at the ready check, not on every push, because builders push after every small unit.

**Funnel and templates**

21. `funnel-handoff` step 3: aim for stop points of 5 to 8 slices, each still ending in something he can see. A larger one is split (A1, A2).
22. `funnel/CHAIN.md`, `funnel-subtract`: a removed row may carry a guard fact that proves the code is gone.
23. `funnel-handoff`, `templates/BRIEF.md`: section 7a lines start with the `E` id and name a test; the done line reads `Operations: <what> (test: <name>)`; section 7 lists removed rows; the template gains the `Chain:` line. Drop the handoff's own fresh reader, which plan review's grounding agent duplicates.
24. `templates/PROGRAM.yaml`: list the funnel's files and the new run files.
25. `tracker/REMOVED.md` lives outside git on his laptop. Commit it with the docs step after each merge, so it cannot be lost.

**Text and leftovers**

26. `SHIPPING-METHOD.md`: replace "Step 0", "The flow of one slice" and the stop-point paragraph with this shape; say plainly that plan review exists and what it does. Fix what is wrong: "Every slice gets a deep, fresh Opus review" under Settled; it names `PROGRAM.md`, `index.yaml`, `PROPOSALS.md` and `arch/final/SPINE.md` (known); it says nothing reaches `engine/base` without his click and also that a stop lands without him; its CI section describes GitHub Actions as running.
27. `prompts/REVIEWER.md` and `skills/slice-review/`: the skill's four passes and proof pass become the element reader's method at the checkpoint. The per-slice prompt is retired. `prompts/GROUNDING.md`: say it runs in full at plan review, and only on failed facts in the build.

## Questions for him

1. **Confirm: no AI reviewer per slice. All review happens in its own session, every 5 to 8 slices.** In the build, scripts and tests are the gate. **My recommendation: yes.** The honest cost: about one slice in two may reach the build branch with a fault inside it (old numbers), found at the checkpoint a few hours later instead of at once. Small checkpoints keep that cheap, and nothing reaches `engine/base` unreviewed. The repair run will give the first real numbers.

2. **While one checkpoint is being reviewed and merged, may builders already start the next one?** They would build and pass checks, but nothing lands until the merge is done. Seats stay busy (5.5 hours sat empty at one stop last time), and it is worth roughly a third more slices a day. The cost: a fix nearby means a pre-built slice is checked again. **My recommendation: yes,** never more than one checkpoint ahead.

3. **May the checkpoint review use one Fable agent for the fault walk?** Every checkpoint gets the same full review either way. This only asks whether the hardest walk, the one that would have caught four of the six high bugs, gets the stronger model. **My recommendation: yes, one Fable agent,** on checkpoints that touch exits, brakes, the kill switch or money. All else stays Opus.

4. **With GitLab paused, may a checkpoint merge without you on local checks alone?** Today's rule says a merge waits for your word until CI exists. The local gate would be: the whole repo green on your laptop (Windows), the quality tools, and the review clean. Linux would not be checked until CI returns. **My recommendation: yes,** with "Linux not run" written in every merge note, because nothing trades live money yet and a bad slice reverts in one step.

5. **If a feature's "it recovers by itself" promise has no test proving it, should that stop the merge?** **My recommendation: yes for self-recovery,** because a part failing quietly caused four of the six high bugs. Missing logging or monitoring is listed as open and does not stop the merge.
