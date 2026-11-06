# Pre-mortem and red team on the final set (advanced elicitation, non-interactive)

Run by the funnel judge on the finished `FUNNEL.md` set; both methods played by me, no menu served. Target: the 34 picks and the three shapes. Each finding names the pick that answers it or the gap it opens; the changes it forced are listed at the end.

## Pre-mortem: it is six months on and the template failed. Why?

1. **The first live unit never traded.** The admission gate's lower bound was undefined on a thin record, every cost cell was synthetic, and level 1 waited for N measured fills that only live could produce. *Answer:* DP11's order by world: paper on the stressed default, the paper twin's fills calibrate the cell, level 1 live needs N fills from twin or demo. The gate opens per world. *Residual:* if demo fills are too kind, the first live week recalibrates; the receipt says `cost:uncalibrated` and the sentinel reads the first weeks as "card optimistic".
2. **The guard was never built, so every brake above the position stayed a document.** *Answer:* shape C puts the guard, the sizer, the money brake, the exit stack and RiskState in the first increment and nothing else; the harness's light ledger-driven engine proves the brakes before the guard exists, with a conformance test. *Residual:* the guard is the biggest build item in the set (X1-H57). The architects must size it first.
3. **The applier moved forty units together on one gold move and the book de-risked as a herd.** *Answer:* DP3's share cap per cluster per window, visible on the card. *Residual:* the cap's value is the numbers lens's.
4. **A scalper bled for a month under every daily brake.** *Answer:* the slow-window burn tier (X4-07, DP21) and the input-first check (cost per trade against the card, DP27) see it in days. *Residual:* needs the cost cell and the trade row v2 to exist.
5. **He muted the isolation because it fired on a holiday afternoon.** *Answer:* two tells, calendar-aware baselines, shadow first, the precision record, the trip-tax budget as the bar (DP23, F23). *Residual:* intraday thresholds untested; the numbers lens must score them on calm history before any isolation enforces.
6. **The book went dark for a week while he was away.** *Answer:* Q1's default (retry-then-lockout) and the absence policy (Q6). *Residual:* if he rules no on Q1, the set must say so on every card: "waiting for you since Tuesday".
7. **A unit went live with a demo-sized position.** *Answer:* the deployment carries the share and never reads the demo balance; any world switch resets to level 1 (DP15, X2-H50). *Residual:* promote's one-market refusal wording is gone (G12) but the market list and canary subset (X5-H46) are not built.
8. **A bug sized 2x under the per-trade cap and the accelerators compounded it.** *Answer:* version slow start with accelerators locked, the size sanity band against the unit's usual lots, the twin showing "live 2x twin" on trade one (X4-86, DP22, DP15).
9. **The horizon sizer touched the floor on an intraday gap it never modelled.** *Answer:* the N-1 or PML reserve (X2-H07) and the per-driver cap sized to a tail gap (X4-92). *Residual:* F12; the sim's zero is partly structural and the intraday harness has not run.
10. **Deletion-4 swept the news calendar and the SQS producer before the socket claimed them.** *Answer:* DP24 and DP25 name the files this session claims; this must reach the repair coordinator before C-20 is scheduled. *Residual:* a hand-off, not a design.
11. **Two state tables (kill levels and trading states) confused him and he resumed `all` after a BMS breaker.** *Answer:* DP5 keeps both tables and X6-09 shows requested, enforced, observed; X4-75's second confirmation on `resume all` after a breaker and the 30-second undo. *Residual:* UI work.
12. **The scalper he pictures lost after costs and nobody knew why.** *Answer:* F1, the break-even arithmetic, the cut on the critical path. *Residual:* the cut size per unit has no literature and must come from its own winners' MAE (numbers lens).

## Red team: attack the set

- **Attack: "the never-self-tune list is a lock; he said nothing is set in stone."** The list is his to edit and it locks learners and agents, not him (X5 collision 18). An agent cannot propose a floor change; that is the point. *Held.*
- **Attack: "smallest-wins across caps and strictest-wins across tags will size everything to one lot."** F8: no tag brake live before shadow precision; the binding clamp is named and counted; a cap binding on more than 90 % of trades is a defect; the cost-of-conservatism meter puts it on screen. *Held, with a meter not a proof.*
- **Attack: "the percentile brake is only as honest as the holdout; an optimistic card sets a loose brake."** The dollar clamp from his budget on every level (Dana's rule, X3-H01) and the sentinel's zones. *Held.*
- **Attack: "ten units at level 1 is ten tiny bets that cannot clear a lot step; the breadth thesis is dead at the first cushion."** F5; feasibility-first binds before the split; the class map tells him what the seed can trade; cushion lending. *Held; the numbers lens must show which classes clear.*
- **Attack: "an agent's cut-only evidence is a one-way ratchet; growth waits on clicks."** Expiry, the restore state, the pre-authorised restore ladder (Q1), the sitting-duck advocate with money both ways on every card. *Held if Q1 is yes; a known ratchet if no.*
- **Attack: "the bound click approves a hash; he will click without reading."** X4-75's effect card with "what this costs if wrong", X5-H11's two vetoes, the card budget, the challenge note on the packet. *Held, with the honest note that approval without reading is not measured (A5-056).*
- **Attack: "the kill switch can still be lowered by a bug in the guard."** No path from any brake, agent or applier to a kill level; the lifecycle test proves a fired stop cancels working orders and keeps exits; the one-tap escalation card only raises. *Held.*
- **Attack: "a behaviour check with no orders passes and a move reads it" (hand-off 37).** DP7: no orders is `inconclusive`. *Held.*
- **Attack: "the stack says u2's rules hold on a real run; they cannot be shown to."** DP27: never claimed; the preflight and the replay match are the only evidence. *Held.*
- **Attack: "agents hold cTrader's order tools on the node's own demo account; your numbers ignore their positions."** F16, DP33: a `foreign` scope in the account numbers; a separate demo account for agents recommended to the build. *Held as a flag.*
- **Attack: "three fail modes on one unit is three meanings of missing."** F9: declared per feed on the registry row and shown together on the preflight. *Held.*
- **Attack: "R gross with `net_r` beside it is two P&Ls on one screen; he will confuse them."** Marguerite's line: the money one is his P&L; the R one says whether the idea works. Both shown, labelled, one drift vocabulary. *Held; a UI need.*
- **Attack: "the harness proves a different system than live until the guard exists."** X4 P5: the conformance test on one tape; if they never agree, the simulation proved a different system and says so. *Held.*
- **Attack: "a quarterly red team of the information path is a chore nobody schedules."** X5-H33 picked with a schedule row (`ev_red_team_schedule`); the first run before any news agent is wired (X4-58). *Held as a row; a chore remains a chore.*

## What the two passes changed

- F16 and DP33 added (agent positions on the bound demo account).
- F21 added (the deletion sweep claims), with the files named in DP24 and DP25.
- Hand-offs 36 and 37 answered explicitly in DP27 and DP7.
- X5-H33's quarterly red team picked rather than left plausible.
- The `resume all` second confirmation and undo window carried from X4-75 into DP5's text.
- Section 7 of `FUNNEL.md` ("what this set leans on that is not proved") written from the residuals above.
