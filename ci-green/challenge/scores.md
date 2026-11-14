# Challenge scores: ci-green

The rubric of `funnel-challenge/references/rubric.md`: Clean, Low, Med or High on five dimensions. Any High recommends a drop; two Med make a row contested; otherwise his two tests decide.

| Item | Necessity now | Abstraction | Extensibility speculation | Premature optimisation | Drift from the core sentence | Result |
|---|---|---|---|---|---|---|
| S1, the two blockers (format check, qmn Linux lane) | Clean | Clean | Clean | Clean | Clean | core: the core sentence is false until both pass |
| S1, the 57 baselined rows the plan folded into it | Med | Clean | Low | Low | Low | one Med, so his two tests decide: left out now, nothing in the core is reworked, and it is not configuration. Later, and it is his ask, so it is proposed to him (question 1) |
| P1, second look at PR #1's five edits | High | Clean | Clean | Clean | High | drop recommended; the word is `later` because an agent's proposal is parked. The look is done in `voices.md` |
| P2, a blocking Linux type check for the five packages | High | Med | High | Low | Med | drop recommended; the word is `later` because an agent's proposal is parked |

Why each score that is not Clean:
- **The 57 rows, necessity Med.** The core sentence does not need them: the lint job printed "0 blocking" for all 68 rows in those packages (GROUND.md, the job table). They are still real debt that issue T-22 names, so not a High.
- **P1, necessity and drift High.** None of the five edits is red at the tip and `SCOPE.md` says it would serve no ask. It reviews merged work; it builds nothing toward a green run.
- **P2, necessity High.** A row that is not in the baseline already blocks (`tools/ci/qci.py:842`), so the core sentence holds without it.
- **P2, abstraction Med.** A second checker over the same files as the ratchet, with one user.
- **P2, speculation High.** It exists for a future slip that the ratchet already stops; its own "Why" in `SCOPE.md` names only a clearer label as the gain.
- **P2, drift Med.** It adds a blocking job to a program whose goal is fewer red jobs, and it cannot be switched on while the 11 out-of-scope rows in qmx-host remain.

The scoping test, "would it ship on its own merits without the core?":
- The 57 rows: yes. They touch other files than the two blockers and stay on the known list meanwhile. So they are their own later item and never ride inside a core slice.
- P1: yes, as a review note. It needs no PR.
- P2: yes, and only after every row is gone.
