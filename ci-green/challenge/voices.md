# Challenge voices: ci-green

Per item: the steelman, then two voices in attack mode, the methods that fit, and the outcome (`lock` is core, `park` is later, `crack` is contested, `kill` is a drop recommended).

## S1: make the deep run green

Steelman: until the two red jobs pass, the gate refuses every pull request into `engine/base`. The held risk work and everything after it wait on this one program.

- S1 Dr. Quinn (problem solver): the problem is two red jobs, a test file with eight extra blank lines and two qmn files with 107 errors. It is not the 68 baselined rows, which lint printed as "0 blocking". Three files are the vital few; the 57 rows are the trivial many, carried in by a diagnosis the grounding proved wrong.
- S1 the builder with the held risk PRs waiting behind the gate: every extra file in this checkpoint is one more way for the only checkpoint that can reopen merging to go red. Two PRs, prove it, then the rest.

Methods:
- **Pre-mortem.** It shipped and the gate stayed shut. Likeliest causes: the build's deep run goes red on something outside the two blockers (a flaky test that is not in the one-row flaky list, or Skylos, which scans the diff, on the changed credential lines); or a guard added to a Windows-only module changes what the Linux suite can import. Both block the launch, so the green verdict itself and the unchanged Windows tests are core, not the two job names alone.
- **Occam's Razor.** Three files make the core sentence true.
- **Subtraction.** Out of the first path: the 57 rows, and the baseline file as a builder's edit (the prune command drops gone rows, and a gone row never blocks).
- **Reframe the Question.** The real question is "what stops the gate opening?", not "what does T-22 list?". T-22 was wrong about which job is red and why.
- **Assumption Audit.** Weakest assumption: the reds retaken at the tip hold on the next run. Confidence medium, impact high. Only a run settles it, which is why the sketch offers one before the briefs.

Outcome: lock, for the two blockers. The 57 rows inside S1: park, proposed to him, since they are part of his ask.

## P1: second look at PR #1's five edits

Steelman: PR #1 merged product and test edits that nobody read as product code, and a quietly weakened test inside a CI change is how false greens start.

- P1 the PM: none of the five is red and none serves the core sentence. A review with no deliverable is not a slice.
- P1 the maintainer reading this a year from now: one line saying somebody looked is enough. Somebody did, below.

The look, done here:
- `qmn/src/qmn/host/qa_debt_matrix.py:582` and `:591`, and `qmn/tests/test_qmn_deploy_switch.py:321`: path strings that follow the move to one workflow file, `qmx-ci.yml`. The test still asserts the pinned Ubuntu runner, and the new workflow has it.
- `tools/tests/test_mutation_workflow.py`, deleted: it ran the shell steps of `battery.yml`, which no longer exists.
- `tools/tests/test_readiness_gate.py`, rewritten for the new workflow: it now reads the workflow's structure (which jobs the verdict needs, when it runs, what the gate reads), where the old one ran the gate's script. The gate's script has its own tests in the new `tools/tests/test_ci_driver.py` (line 258 on).
- Nothing here needs a PR. One note for the backlog: the readiness test is structural now.

Methods: Subtraction (nothing is left to build); Shark Tank Pitch (no PR to fund).

Outcome: park. The score recommends a drop; the word is `later` because an agent's proposal is parked.

## P2: a blocking Linux type check for the five packages

Steelman: qmn has a lane that blocks by itself. The five packages have only the baseline, so a new Windows-only call shows up as an unnamed "new row".

- P2 Victor (innovation strategist): what does this stop that the ratchet does not already stop? Nothing. A row that is not in the baseline blocks today (`tools/ci/qci.py:842`).
- P2 a finance reviewer counting PRs: a job with no baseline needs all 68 rows gone, and 11 of them are out of scope. This program could not switch it on even if it built it.

Methods:
- **Occam's Razor.** One ratchet does the job.
- **Assumption Audit.** It assumes the row count reaches zero. That is false while the 11 ordinary rows in qmx-host stay.
- **Subtraction.** The only gain is a clearer label on a failure that already blocks.

Outcome: park. The score recommends a drop; the word is `later` because an agent's proposal is parked.
