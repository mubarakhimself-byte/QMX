# Rationale: what I considered and rejected

Candidate 2. Fork sides F-A (b) and F-B (a). **[judgment]** throughout.

| Considered | Rejected because | Taken instead |
|---|---|---|
| Learner and applier now (F-A a) | Three more variables, modes to explain, and in the model no gain at 10 trades a day. Its edge is half a day of cost lag at 40 a day | Refresh, with `Resolved.low`, `high`, `Sheet.rev` and `authority` ready, so it can grow in |
| Strict reading of "applied at the next": one more full period of delay | Half-cushion runs on the bleeding book rise from 27 % to 34 % at N = 10. It buys only a preview, which the plan card already gives | Evidence up to an anchor is in force from that anchor |
| Refresh with no way to move mid-period | X4-39 waits a full day for no reason | A closed trigger list, including `cost_alarm` |
| Halts compiled into the unit (F-B b) | Needs the compiler to feed account and trade ports, and leaves two places for a brake | One guard. `halts_not_built` stays |
| Call site in `Runtime` and a separate one in QMB | Two seams, and it sits where the repair is busiest | `UnitSliceHandler.mint_intents`, which both hosts already run |
| Guard inside `qml` | `qml` imports `qmf.risk` today; the guard would pull hosts toward the compiler | `qmf.risk.guard`, pure, with blocks passed in by factory |
| Sizer base as a new block with a wider socket each time | Every base would change the socket | A base is a derivation producing `baseline_risk_usd`. The sizer block only converts dollars to lots |
| Level and taper applied inside the sizer | A new sizer could forget them | The guard applies every factor after the sizer, once |
| Sizer reading the day's realised loss live | A second reading of one loss. In the model it costs about a point of size and saves about a point of half-cushion runs | Only open risk is live. The taper reads the loss |
| DP9's level-weighted B as written | The level cancels itself at N = 1 and whenever all units share a level | Freed swing only to units at level 1.00; flat for slow units until the harness says otherwise |
| A cut that changes no lots goes straight to paper | Tested; no material difference | Dropped. I did not add a part that does nothing |
| Day stop at k 2.5 on the sized sigma | Still almost never fires, 0.00 to 0.06 per 100 days | k derives from the group's own p1 day; 1.7 as the preset rung |
| Exits inside the profile | Exits move R, so a profile change would cost the record | `exit_set` stays on the unit. The profile holds only exit numbers, and changing one is a counted try |
| Targets stay closed by the node (DP26) | Breaks the hard line: backtest and live disagree on a wick, and QMB may not change | Rest at the venue where it holds them. Needs R24's fact |
| Book or portfolio as schema words | Forces Q8 | `group`, with `display_name` and a reserved `parent` |
| A guard file for its status | One more file to keep atomic on Windows, and a second source of truth | Journal rows and broker deals; `recover` is a fold |
| One `Kind` per brake in `stand_down.py` | A code change per brake | One `Kind.RISK_RULE` |

**What I am least sure of.** The bet key on an FX book: it is the one binding factor the sim does not hold, and many pairs share USD. Next, whether the bleeding-book gap at N = 5 and 10 is acceptable until a pooled CUSUM binds. Then the 40-a-day median gap between raises-at-anchor and raises-at-once, which I would re-run with more paths before believing either way.

**What I did not do.** No test suite ran. No code was changed outside this folder. The reviewer gate's subagents were barred by the brief, so I walked its checklist myself and the lint script passed. The two Q8 readings, the numbers lens and every R24 fact stay open.
