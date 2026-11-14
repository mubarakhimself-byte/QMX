# Challenge to the shipping method draft, 12 November 2026

Read: the draft, the current orchestrator prompt, the speed review, the stack list, the builder brief, the epic-factory plugin, the 4 November audit note, and the repo's CI files.

## What the evidence says first

- **Skill proof never stopped the drift.** In the audited run all 249 agents loaded the main skill and 30 serious defects still shipped. Those came from fakes kinder than the real neighbour and builders not reading existing code.
- **The drift was the orchestrator's.** It skipped the test lanes on 13 of the last 19 rows, reviewed a PR itself, and let the plan grow from 73 to 91 sections. An LLM running the loop got tired of its own rules.
- **What caught real faults since:** the fresh reviewer (every money-path catch), tests at the exact head, the red-then-green proof, and two cross-row checks (the Opus re-review of rc-07, the exit probe at the tip).
- **Known findings.** Confirmed: the adversarial review lens demands ten findings. Confirmed: a missing skill is a blocker in the live prompt, though the speed review asked for it to be a low. Partly disputed: `how` does say "run each role yourself" when spawning is not possible, so it is usable, just rarely opened.

## Verdict per section

1. **Off the laptop: keep, with a change.** CI already has a Windows runner beside Linux, so Windows is covered. But CI only fires on `main`, `integration` and `rebuild/**`. Build branches never ran it. Fix the trigger and make the Windows job required before any landing. 103 Python files branch on the platform, so a Linux-built slice will sometimes go red on Windows after the push. Broker sign-in lanes stay on the laptop.
2. **Slice and brief: change.** The template lacks "read what is there and list who calls it". That is the cause of the 30 defects. The clarity reader must read the brief and the code it names: rc-07's brief missed three files, and no brief-only read finds that. "Fewer, bigger slices" needs a size limit, or the one reviewer skims and fix rounds grow.
3. **Builder: change.** Dropping proof of skill reading is right. Dropping the three evidence files is not: the caller map, the failing-test log, and the safety fact run before and after. Keep "search for every value you move"; it caused most fix rounds.
4. **Machine checks: keep, and extend.** Add two machines: new tests must fail on the parent commit, and a mutation check on changed lines. Both turn "a test that cannot fail" from an opinion into a result.
5. **Review: keep, with changes.** Add "a fake kinder than the real thing" to the blocker list. The reviewer must still run the safety fact, not only read. Name the lenses, leaving out the ten-finding one. The outside reviewer is fine as advice. Skip the sweep of 330 old PRs.
6. **Landing: change.** Two slices can each be green and be red together. Land one at a time: rebase on the tip, full suite on the result, then merge. Slices depend on each other, so a parked slice must not stop the night. Add a cross-slice check at each stop point.
7. **Script loop: keep. This is the real fix for drift.** A script cannot skip a lane. Run each builder and reviewer as its own headless session (`claude -p`), started by the script. They are then top-level sessions and can use skills that spawn helpers. `/loop` and scheduled tasks live inside a session and are the wrong tool. Do not revive epic-factory: its loop is an LLM session, its review is advisory and once per epic, and it has no agents folder. Reuse only its merge gate.
8. **Standing: keep.** Add a PR description standard: what it does, how it was checked, every departure from the brief.

## Top 5 changes

1. Keep the evidence files and have the script check them. Drop only the skill list.
2. Land through a one-at-a-time queue, with the full suite on the merged result, on Linux and Windows.
3. Let GitHub enforce his click: branch protection so no agent token can push `engine/base`, `integration` or `main`.
4. Add the two test-quality machines: fail-on-parent and mutation on changed lines.
5. Add a circuit breaker and a morning report: stop after three parks in a row or a red build branch, and on a usage limit sleep rather than crash.

## Unsure

- Whether the full suite fits CI's 60-minute limit. It took 2.3 to 3 hours on the laptop with two workers.
- Whether his subscription may run headless on a rented third-party VM, and how its limits behave there.
- Whether boat.dev or Amp offer Windows machines. A plain Windows cloud PC would remove the Linux question.
- Whether Opus builders need fewer fix rounds than DeepSeek did. Not measured, and it sets the real speed.
