# Challenge: ci-green

Core sentence: "With the fix in, a deep CI run on engine/base ends green on Linux and Windows, with no check switched off or silenced." (built from: "Go with the recommendation if you see fit" and "What's the point of CI if we are merging locally?" dd8f4ab2:L7041)
Premise: every ask assumes the qmx-apps format check and the qmn Linux lane are the only two things between `engine/base` and a green deep run. Holds because: in the last full deep run the only other red jobs were Skylos, raised on PR #1's own diff, and suite shards whose reds were retaken into the known-reds list at the tip (GROUND.md G2, G3 and its job table). One leg is not proven: no deep run has run at the tip yet (the only CI run on `bef6e808` is the nightly walk, run 43555617142). That is a fact a run settles, not a call for him.

What the words mean, once:
- **deep CI run**: a run of `qmx-ci.yml` at the deep level, which runs lint, Vulture, Skylos, the Linux and Windows suites, mutmut, the docker node and the qmn lane.
- **ends green**: its `deep-verdict` job succeeds. GitHub runs that job only when every deep job succeeded (GROUND.md G3), and the gate lets a pull request into `engine/base` only on a green deep run of its exact head (`tools/tests/test_ci_driver.py:258`). A listed known red or listed flaky test does not block; that is today's rule, not this program's change.
- **the fix**: the two blockers this program owns, the format check and the qmn Linux lane.
- **switched off or silenced**: no new ignore marker, no rule turned down, no file excluded, no change of the platform the checker types for (GROUND.md G15; `SCOPE.md` Out of scope).

## Simple sketch

1. No PR: one deep run at the tip before a brief is written, so every red job is known up front. It is optional; without it the build's own deep run is the first proof.
2. PR 1: run the formatter on the one qmx-apps test file that ends in eight extra blank lines (GROUND.md G5). The `lint` job goes green.
3. PR 2: the two qmn files the Linux lane fails on (GROUND.md G6, G7). Declare the credential store's attributes where the checker sees them on every platform, reach the Windows calls only under a platform check it can read, and mark the deployment reader as Windows-only. The lane goes from 107 errors to 0.
4. Windows behaviour does not change: the two Windows test files that drive this code still pass in the Windows suite (GROUND.md G16, G17, G18).
5. Checkpoint: the build branch's deep run ends green and the gate lets the pull request into `engine/base`. That run is the proof of the core sentence.
6. After the proof, in later PRs: the 57 baselined rows from Windows-only code in the five qmx-agents packages. They block nothing today.

Not in the first path: the 57 baselined rows (lint printed "0 blocking" for them), the 11 ordinary type rows in qmx-host, P1, P2, the known reds and flaky tests, the Skylos time limit, coverage floors, and any way of switching Linux typing off.

PR budget: core 2, later 3, checkpoints 1

How the budget was counted: core is PR 1 and PR 2 above, one checkpoint. Later is the 57 rows as three PRs by package group: qmx-home (31 rows), qma-harness (12 rows), and the test-only rows in qmx-host, qmx-apps and qmx-engine (7 rows). The 7 rows inside his guarded parts (the workflow engine and the mini-app core) are not counted; see the call-outs. P1 needs no PR and P2 gets no budget unless he picks it.

## Verdicts

| Item | Verdict | Left out now, is the core reworked later? | Is it configuration? | Would it ship on its own? | Why, in one line | Evidence | Decider |
|---|---|---|---|---|---|---|---|
| S1 | core | yes | no | - | The two blockers are why the gate refuses every pull request, so nothing ships until they go; the 57 baselined rows the plan folded into S1 block nothing and are proposed for later PRs (question 1). | GROUND.md G3, GROUND.md G5, GROUND.md G6, GROUND.md G7 | him (his ask) |
| S2 | later | no | no | yes | He chose this at the cut: the 57 rows block nothing (lint printed 0 blocking), so they follow in up to 3 later PRs once a green deep run proves S1; the 7 rows in his guarded parts stay in the baseline. | GROUND.md G9, GROUND.md G10 | him (D1) |
| P1 | later | no | no | yes | The second look is done in this challenge and found nothing that needs a PR: two path strings follow the workflow rename, the deleted test drove a workflow that no longer exists, and the gate's script has its own tests. | qmn/src/qmn/host/qa_debt_matrix.py:582, qmn/tests/test_qmn_deploy_switch.py:321, tools/tests/test_ci_driver.py:258 | agent |
| P2 | later | no | no | yes | The ratchet already blocks any type row that is not in the baseline, so a second blocking check adds a job for a clearer label only; it also cannot be switched on while the 11 out-of-scope rows remain. | tools/ci/qci.py:842, GROUND.md G9 | agent |

P1 and P2 each score a High in `challenge/scores.md`, which recommends a drop. The word stays `later` because an agent's proposal is parked until he picks it. Recommendation at plan review: pick neither.

No row is contested, and the depth is light, so no party round ran.

## Call-outs

- The plan was sized on a wrong diagnosis. The brief and issue T-22 say lint is red on type errors in five packages; lint is red on the format check alone, and all 68 rows in those packages are in the baseline and block nothing. Why it is bloat: 57 rows across ten files in five packages would ride on the one checkpoint that opens the gate for every held PR, and change nothing in the verdict. Evidence: GROUND.md G9. Recommended: later (question 1).
- The scope's "Done when" stops one step short of the ask. Passing `lint` and `qmn-lane` "so the verdict can run" is not a green verdict, and only a green deep run of the head opens the gate. Why it matters: a red on the build's deep run from outside the two blockers (a flaky test that is not in the one-row flaky list, or Skylos on the changed credential lines, since it scans the diff) would leave the program "done" with the gate still shut. Evidence: GROUND.md G3. Recommended: core. The checkpoint's proof is the green verdict; a red from outside the two blockers gets one rerun, then goes to him as a budget call.
- Seven of the 57 rows sit in parts he guards: three in the workflow engine's script node and four in the mini-app core's supervisor. His rule allows an engine change as a new template only, and a mini-app core fix only for a real block; a baselined row blocks nothing. Why it is bloat: it spends a guarded-part edit on a typing nicety. Evidence: GROUND.md G12. Recommended: drop from the fix and leave those seven rows in the baseline, unless he says otherwise when the later PRs are briefed.
- The baseline file is not a builder's deliverable. `ci/baselines/pyright.txt` is in the program's area and in the second "Done when" bullet, but it is a shared generated file in the project profile, a row that is gone never blocks, and the prune command drops gone rows. Why it is noise: no builder needs to touch it for the run to be green. Evidence: tools/ci/qci.py:841. Recommended: drop it from the builders' files; who runs the prune, and when, is a fact for the handoff to pin.
- P1 has nothing left to build. Its five edits follow PR #1's move to one workflow file. One note for the backlog, not for this program: the rewritten readiness test now reads the workflow's structure where the old one ran the gate's script. Evidence: tools/tests/test_readiness_gate.py:15. Recommended: drop (parked).
- P2 rebuilds what the ratchet does. Evidence: tools/ci/qci.py:842. Recommended: drop (parked).

## Questions for him

One question, now settled as `decisions/D1-rest-of-the-type-clean-up-after-ci-is-green.md` (his answer: later): do the 57 non-blocking rows come in later PRs after CI is green (recommended), or in the same batch?

For the lead: he said twice in the source turn that CI is not his cup of tea, and on 13 November that the first PRs "should first prove that thing works" and that "the nice to haves can come in later PRs" (dd8f4ab2:L6423). Those words point the same way as the recommendation. Whether they settle the question without a fresh ask is the lead's call at the cut. If he says later, the 57 rows become their own later ask in `SCOPE.md`, quoting his answer; if he says the same batch, the core budget rises from 2 to 5 and `budget.raised` names that decision.

Waiting for the next batch, because it matters only once question 1 is answered: may a typing-only edit touch the workflow engine and the mini-app core (the seven rows above)? Recommendation: no, leave them in the baseline. If he answers question 1 with "the same batch", this one is asked next.
