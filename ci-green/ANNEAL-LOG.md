# Anneal log: ci-green

## Round 1 (plan mode, 2026-11-14)

Light depth: lenses 1 to 4 and 7 only.

| Q | Lens | The gap | Kind | Filled by | Context added | Source |
|---|---|---|---|---|---|---|
| Q1 | linking logic | What does "green" mean for this program: two jobs passing, or the verdict? | vague | agent, by reference | The deep-verdict job succeeds; it runs only when every deep job succeeded, and only that opens the gate. Written into S1's Done when and stop A. | CHALLENGE.md words; GROUND.md G3 |
| Q2 | attack the premise | Are the format check and the qmn lane really the only blockers once the fix is in? | fact | agent | No: the deep run mutates every touched function on Linux and counts "no tests" as a survivor; `read` and `delete` have no Linux test. Became S1.a and E6. | GROUND.md G24, G25, G26, G27, G28 |
| Q3 | attack the premise | Can the qmn typing fix avoid touching functions at all? | fact | agent | Measured: the deployment reader's module guard and the class-level annotations touch none; only the two last-error lines must change, in `read` and `delete`. | GROUND.md, Found after the challenge, point 2 |
| Q4 | attack the premise | New Linux tests of unchanged behaviour pass at the parent, which feature-kind fail-at-parent refuses. | fact | agent, by reference | Slice kinds pulled forward: cg-01 is a `pin` (passes at parent and head), cg-02 a `refactor` that depends on it. Recorded by the lead, not a question for him. | tracker/shipping-method/BUILD-LOG-2026-11-13.md D-L27 |
| Q5 | contradictions in his words | Does "after CI is green" conflict with fixing all of T-22 now? | fact | agent | No: his H8 yes asked for the real fix, and his cut answer orders it: blockers first, the 57 rows later. | decisions/D1-rest-of-the-type-clean-up-after-ci-is-green.md |
| Q6 | edge cases | What must the pins assert so they are real, and what keeps keys safe? | edge | agent | E1 to E4: exact results, exact messages, the call arguments and the free; a fake that keeps the Windows contract; throwaway targets only. | GROUND.md G16, Fixed lines touched |
| Q7 | edge cases | Does the deployment reader's import guard change anything a Linux node runs? | edge | agent | E5: nothing imports it off Windows. | GROUND.md G8 |
| Q8 | edge cases | Could the fix pass by turning a check down? | edge | agent | E7. | GROUND.md G15 |
| Q9 | subtract | Do the two seen-but-later items (P1, P2) or the 7 guarded rows belong in stop A? | fact | agent | No: P1 and P2 are parked; the 7 guarded rows stay in the baseline; S2 is later by his answer. | CHALLENGE.md verdicts; SCOPE.md Decisions so far |

New questions this round: 9. Stop: no.

## Round 2 (plan mode, 2026-11-14)

Light depth: lenses 1 to 4 and 7 over the rewritten plan. Every line reads clearly; the pins, the fix and the proof each have a home, and no lens raised a gap.

New questions this round: 0. Stop: yes.

Stopped after 2 rounds (plan mode): round 2 raised no new question.
