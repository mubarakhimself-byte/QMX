# X2 roundtable (bmad-party-mode, session mode, non-interactive)

Run 2026-11-03 for Stage B, layer X2. One mind voices every persona; the operator's lines are built only from his recorded words (`seeds/SEEDS.md`, `seeds/operator-words-2026-11-03.md`), quoted where exact. The other five are invented roles, not real people. The hybrids under fire are in `expansion/X2-sizing-accelerators.md`: H01 (horizon floor-odds sizer), H10 (one-ledger cushion pair), H24 (raise permission gate), H39 (cost triple), H44 (asymmetric equity basis), H50 (deployment carries share, costs and level), H28 and H29 (split against full size), H13 and H18 (levels below baseline, tiers above).

**In the room**
- 🏦 **Dana**, pod-shop risk manager. Ran drawdown ladders at a multi-manager. Distrusts anything that sizes up by itself.
- ⚡ **Kofi**, retail FX and gold scalper on a small account. Lives in spreads, minimum lots and broker quirks.
- 🛠️ **Priya**, platform engineer (Kubernetes, SRE). Thinks in seams, appliers, guards and what fails at 3 a.m.
- 🎲 **Hal**, betting-syndicate quant. Kelly is his native language. Hates wasted edge.
- 🧾 **Ruth**, reinsurance actuary. Accumulation, event clauses, reinstatement premiums.
- 🎙️ **The operator's voice**, from his words.

---

## Round 1: the horizon floor-odds sizer (H01)

🎲 **Hal:** Let me get this straight. You size every trade as if the edge were zero? Cushion over s times z times root H. At the believed edge that's what, a third of half Kelly? You're leaving money on the table and calling it discipline.

🏦 **Dana:** He's leaving money on the table *on purpose*, Hal. I watched desks run at half Kelly on a backtest edge. The backtest edge was the first thing to die.

🎙️ **Operator:** "I don't want just safety. I want something that can like perform." And: "it shouldn't really depend on the edge a lot... Let's give a range for the edge."

🎲 **Hal:** Then give me the range and size on the low end. Not on zero.

⚡ **Kofi:** Hang on, the sim already did that. `horizon_half` sizes on half the believed edge. Ten units, rho 0.3, believed edge: median $5,854 against $2,213 for zero edge, both with no floor touch in a thousand paths. Zero edge is the start line, not the finish.

🎲 **Hal:** Fine. Then the dial is the whole game. Who moves it from zero to low to mid?

🎙️ **Operator:** "What if I want to change the way it is derived?"

🛠️ **Priya:** Then the dial is a field on the profile, the derivation is a block, and moving the dial is a version or a calibration row, never a hidden code change. And please, not a bisection solver inside `decide()`. Compute the multiplier at each anchor, cache it, and let the sizer read one number. If the cache is stale past its anchor, fall back to the zero-edge number. That one needs no edge input and cannot be wrong in the dangerous direction.

🏦 **Dana:** Now my real problem. Recomputed every morning off the cushion, this is CPPI. Portfolio insurance. 1987. The maths is lovely until the market gaps through your rebalance.

🧾 **Ruth:** Which is why I like the N-1 reserve in H07, and I'd go further. We don't size for the largest single risk. We size for the probable maximum loss on a named event, one in two hundred. Take your exposure zones, the USD zone, the crypto-weekend zone, and size the reserve for the worst credible event in each, not just the biggest position.

⚡ **Kofi:** And the sim's gap days: 2 % of days, every unit gapping 3R at once. Still no floor touch for the horizon sizers. Fixed 1 % touched 30.7 % of paths at half edge with ten units.

🏦 **Dana:** A model gap. I'll believe it when the scenario layer feeds it real worst moves per class.

**What changed:** H01 now computes its multiplier at anchors and caches it, with the zero-edge number as the fallback (Priya). H07's reserve widens from N-1 to a probable maximum loss per exposure zone, with N-1 as its floor (Ruth). Worst-step moves must come from X4's scenario table, not from history (Dana; collision X2-C16).

---

## Round 2: ten units, the split and the minimum lot (H28, H29, H45)

🎙️ **Operator:** "if you're telling me 1 unit will get $20 and then 10 different units each will get, you know, $2, does that make sense to you?"

🎲 **Hal:** Under H28 it's neither. Ten units at rho 0.3 have an N_eff of 2.7. Each gets one over root 2.7 times ten... you know what, each gets about a sixth of the solo size, and the book's swing is root N_eff times one unit's.

🏦 **Dana:** And H29 says each keeps full size under a parent cap set from how often they lose together. That's how we ran pods. The children don't know about each other; the book does.

⚡ **Kofi:** You're both arguing about a world where sizes are continuous. They aren't. Gold, 0.01 lot, a three-dollar stop costs three dollars. At $500 with ten units, a sixth of a $6 trade is a dollar. Gold can't trade at a dollar. Neither can a micro index future. Euro-dollar can, at a ten-pip stop. Crypto spot can. So at $500 your breadth runs into the lot table before it runs into correlation.

🛠️ **Priya:** So admission is a function of the derived size, not of the instrument. H45. The MIS can route a unit only to instruments where the minimum lot fits under the derived size times a tolerance.

🎙️ **Operator:** "We need to be able to have this unit be able to adjust technically" across pips, points and the rest.

⚡ **Kofi:** And the dither idea, H46, is cute but I've seen brokers... no, actually it's fine if the cap is hard. Trade 0.01 most of the time, 0.02 now and then, average comes out right. Just never let one trade blow through one and a half times target.

🏦 **Dana:** Cute is not a risk policy. A dithered lot is a trade risking 54 % more than plan. Fine on EUR/USD; on gold before a US number, no.

**What changed:** a new collision, breadth against the minimum lot at small equity (X2-C02). H46 gets a news-window exclusion and stays wild (Dana). H45 orders admission by feasibility first, so at $500 the first units go to FX micro lots and crypto spot (Kofi).

---

## Round 3: house money, reverse house money and the anchor (H10, H11)

🎙️ **Operator:** "I don't think I want to lose the house of money and the accelerators analogy." And "reverse House of Money was my idea."

🧾 **Ruth:** One ledger, one anchor, and the anchor decides. I like it. But your units win together. A USD release pays five units in an hour. If each one presses on its own ledger you have written the same risk five times. In my world that's accumulation, and the hours clause is how we stop it: everything inside 72 hours is one event.

🎲 **Hal:** And on independent trades it adds nothing. R9's own script: 0.600 growth per unit of risk against 0.603 for a constant. House money is a size increase in a costume.

🏦 **Dana:** Unless results persist. The 500-trade regime: 0.855 against 0.604. Nobody here has measured persistence on an intraday unit after costs. Nobody.

🎙️ **Operator:** "brakes first, accelerator second." And "aggressive and nuclear are two things."

🛠️ **Priya:** Then the accelerator half is disabled by default and turns on per unit after the proof card (H20) passes, while the brake half (reverse house money in money, FI cuts counted by their size) is on from day one. Same block, two switches.

🧾 **Ruth:** And put the accelerator half at the book, not the unit, with the event window. Profit from one event funds extra risk once.

**What changed:** H10 ships with the brake half on and the accelerator half off until H20 passes (Priya, Dana). H11 becomes the default home for house money, with the event window counting one event once (Ruth). The scope question stays his (Q3).

---

## Round 4: pairing, so the accelerator never drives into a trip (H24, H26)

🏦 **Dana:** My nightmare is a restore that overshoots. The brake lets go, the accelerator sees a green day and presses, and you're straight back at the size that tripped.

🛠️ **Priya:** H24 checks headroom: before any raise, m full losses at the new size must still fit before the nearest trip. And no raise while the last change is settling. TCP has done this for forty years. Remember where you broke, come back fast to half of it, slow near it.

🎲 **Hal:** And the AIMD day pair is the only thing in R9's table that kept growth per unit of risk and halved the deep drawdowns. 0.5 % against 1.3 % for a constant at the same average risk.

🏦 **Dana:** At 79 % of base risk. So it's mostly a brake.

🎲 **Hal:** It's a brake that costs nothing. I'll take that over an accelerator that costs something.

🎙️ **Operator:** "while we lose, we don't lose stupidly."

**What changed:** H24 adds a rule that a restore never goes above baseline: crossing baseline needs an accelerator's own permission (Dana; matches R9's restore definition). H26 thresholds are in the unit's own day percentiles, not in percent of equity (Hal, from R9 §4.2).

---

## Round 5: costs (H39, H40, H42)

⚡ **Kofi:** Finally. A scalper's edge is a cost question. EUR/USD at 0.8 pips round trip on a 6-pip stop is 0.13R before you start. Halve the stop, double the cost in R. And at 21:00 to 22:00 GMT the spread is the trade.

🎲 **Hal:** H39's Kelly with costs: p = 0.45, b = 2 gives 17.5 % at no cost and about 12 % at 0.1R. As a ceiling. Good.

🛠️ **Priya:** And costs uncalibrated on day one? The QMB port refuses rather than invent a zero. If the sizer refuses too, nothing trades. Sitting duck.

⚡ **Kofi:** Use a stressed class default, twice the broker's posted typical spread, and decay toward measured as fills come in.

🎙️ **Operator:** "if you are trading, let's say, in a given market for a given instrument at a given time frame, we need to know what are the fees, what are the costs, so that the unit can know."

⚡ **Kofi:** And kill the session multiplier. If London is cheaper, the cost term already gives London more size. A 1.2x "premium window" on top is paying twice.

🏦 **Dana:** Agreed. Windows lower cost; they don't hand out edge.

**What changed:** H39's uncalibrated-cost fallback is a stressed class default that decays toward measured (Kofi, Priya). H40 removes the session multiplier outright (collision X2-C07 with the old premium-window lift and his D8).

---

## Round 6: realised or marked, and demo against live (H44, H50)

🏦 **Dana:** Which equity does the sizer read? Every firm I worked at had a fight about this.

🧾 **Ruth:** Accountants settled it centuries ago. Lower of cost or market. Recognise losses when they're likely, gains when they're realised.

🛠️ **Priya:** So: size from committed cushion (the lower of balance and marked equity, minus the floor, minus open risk at the stops); brakes on marked equity; accelerators only on realised profit. Three rows, each declaring its series. And the shipped stack reads cTrader equity once at sign-in, so marked equity isn't even available yet.

🎙️ **Operator:** "Split QMX into demo and live so a unit trades the same way on both and only the account differs." Did I get that right?

🛠️ **Priya:** Close. Today a paper unit on a $10,000 demo sizes from $10,000. H50 says the budget share travels with the deployment, so demo sizes from the live share. The cost model travels too, and on a world switch the level drops to its first rung and house money goes to zero.

⚡ **Kofi:** Demo fills are flattering. Keep a paper twin beside the live unit and charge the gap.

**What changed:** H44 names a fourth row for the floor clip (worst case at the stops, gap factor included) (Priya). H50 adds the paper twin gap as the source of the live slippage term (Kofi).

---

## Round 7: the operator's last word

🎙️ **Operator:** "Is the sweep cap coming back?" And "I can't be seated like a duck the entire day without trading the 300."

🏦 **Dana:** The ratchet answers both. H56 locks part of every new high into the floor at the BMS. The unit keeps compounding on its cushion. Nothing sits idle, and nothing gets swept out from under a unit's brakes.

🎲 **Hal:** And the cushion is the thing being sized, so a lower floor really is "risk more, lose more". That's his own words back at him.

🎙️ **Operator:** "This is where the leveling comes in."

🛠️ **Priya:** Levels in the UI: he picks a floor level, the derivation does the rest, the receipt shows dollars and percent.

**Takeaways nobody resolved:** Hal still thinks zero-edge is too timid as a default; Dana still thinks any auto-raise above baseline is a mistake; Kofi still thinks $500 cannot carry ten units across classes. Those disagreements are recorded as collisions X2-C01, X2-C12 and X2-C02 in the expansion file.
