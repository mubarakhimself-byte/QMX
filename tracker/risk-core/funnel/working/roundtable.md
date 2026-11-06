# Roundtable on the hardest decision points (party mode, session mode, non-interactive)

Run once by the funnel judge, every voice played by me, on the draft picks before `FUNNEL.md` was finalised. Five voices. 🛡️ **Marguerite**, pod-shop risk manager. ⚡ **Dez**, retail scalper, forty trades a day. 🏗️ **Ada**, platform engineer who has read G12. 🧮 **Yara**, the numbers-lens quant who will run the harness. 🎙️ **The operator's voice**, his own words only, from SEEDS. Topics: DP9 and DP10 (the baseline amount and the edge), DP17 and DP20 (the brake and what clears by rule), DP26 (the cut), DP4 (the shape), Q1.

**Round 1: the baseline (DP9) and the edge (DP10)**

🎙️ **The operator's voice:** "we are doing risk management position sizing. Let's give a range for the edge, okay?"

🧮 **Yara:** Then the size cannot come from the range. It comes from the cushion, the spread of results, how many units move together, and how rare he wants the floor. Zero edge in, a size out. The edge only says in or out, and which level.

⚡ **Dez:** So a unit that is twice as good as mine gets my size.

🧮 **Yara:** At your level. It climbs levels faster. And its ceiling is higher because the cost-and-gap Kelly relaxes with evidence. That is the whole lean it gets.

🛡️ **Marguerite:** I will take that. In my shop nobody got size for a story. They got size for a drawdown they had already survived at a smaller size.

🏗️ **Ada:** One thing. Two sizers are on the table, the horizon one and the day-sigma one, and the brake reads the day-sigma. If they ever disagree, the brake and the sizer drift apart.

🧮 **Yara:** They are one formula if the horizon is the trade rate times the days. I checked it. Write it that way or it breaks.

🏗️ **Ada:** Written. And the sizer needs a usable cushion, a correlation and a cost cell. The node reads equity once at sign-in. There is no marked equity. No PR plans it.

🛡️ **Marguerite:** Then the receipt says `basis:unmarked` until there is, and the cushion is balance minus the open risk at the stops. Nobody sizes on a number they pretend to have.

**Round 2: the brake (DP17) and what clears by rule (DP20)**

🎙️ **The operator's voice:** "at three losses, or if we can sort of figure out a pattern in between."

⚡ **Dez:** Three in a row benches me on nine days in ten at my rate. Yara's table says so. I keep the money line.

🧮 **Yara:** Your own first-percentile window, in trades. Ten or more trades per window. ORB gets a five-day window with the same rule, so one shape for everyone.

🛡️ **Marguerite:** And his three?

🧮 **Yara:** Shipped in shadow as the unit's own 99th-percentile run length, halve not bench. It goes live only where the persistence test says runs cluster. In the sim that is where it earned twenty R of timing. Everywhere else it is a tax.

🏗️ **Ada:** Day one. There is no record. The card has a cone and no per-brake fire band.

🧮 **Yara:** A ladder. Own live record, then the card's bootstrap, then the family's pooled cards, then the class default from the dry chassis, then refuse live and allow paper. And the first weeks read high because protection closes leave no trade row. The sentinel's yellow is read first as "the card was optimistic".

🎙️ **The operator's voice:** "You're meant to size down, I think, but not quickly."

🛡️ **Marguerite:** The money brake is quick. It must be. Drift is slow. Two different things with two different clocks, and the thing that waits for him is HALTED, not a bench. A bench that waits for a click at three in the morning is a dark book. I have run a dark book. It is worse than a bad one.

⚡ **Dez:** So a bench clears by itself?

🛡️ **Marguerite:** After its rest, with a probe at the smallest size, and the third bench in a window locks until he looks. Retry, then lockout. That is not automation. That is a recloser.

🏗️ **Ada:** It is against the unit build's rule. Every risk stop waits for his click.

🛡️ **Marguerite:** Then it goes up as his question, with that default. He said the technical part does not need him. The book cannot go dark on every routine bench while he travels.

**Round 3: the cut (DP26)**

⚡ **Dez:** Nobody has asked the only question that matters. At a five-pip stop my round trip is a sixth of my R. At 55 percent and one to one, do I make money?

🧮 **Yara:** No. Break-even is 58 percent. You lose.

⚡ **Dez:** So the whole frequency thing is dead.

🧮 **Yara:** Not if half your losers are cut at a third of R. Then break-even is 50 percent and 55 clears. The cut is the edge after costs. Not the win rate.

🎙️ **The operator's voice:** "fast invalidation really is yeah, especially for scalpers."

🛡️ **Marguerite:** Then the cut rule, its two-arm proof and a trade row that can tell a cut from a time exit are on the critical path, before the sizer. Put that in the flaws list in those words.

🏗️ **Ada:** The trade row cannot tell them apart today. Exits after entry do not run. That is step 2 of the exit socket and it is sixty lines. It ships first.

**Round 4: the shape (DP4)**

🎙️ **The operator's voice:** "the book is the right skeleton. I say that, but again, I don't know. It's just cleaner."

🛡️ **Marguerite:** My losses never came from a folder. Tag by driver and cap the tag.

🏗️ **Ada:** Tags are drop-ins; I can build them. But two new Library kinds and a lander sit on the path to the first live unit. If "must go live" means anything, the first increment is flat: the profile, the guard, the sizer, the money brake, the exit stack, RiskState, one portfolio config. No cluster level until there are enough units to need one.

🧮 **Yara:** With two or three units the parent limit and the bet keys do the co-loss job. The family tag only pools proof.

🛡️ **Marguerite:** Then flat first, and tags against Books as the competing versions. He picks the words.

🎙️ **The operator's voice:** "Design for complexity. Don't design a complex system."

**Round 5: what the picks cost (F11)**

⚡ **Dez:** Add it up. Bench, halve, isolation, news windows, probation. How much of my year do your brakes eat?

🧮 **Yara:** Steady state, about a tenth of healthy R, mostly news minutes and the halve step. Inside the choke budget. The ramp is the real cost: about sixty baseline trades per unit start. Days for you. Fifty days for a two-a-day ORB.

🛡️ **Marguerite:** Then the ORB climbs on the family's cohorts, pooled across its opens, not its own. That is his own "brilliant".

🧮 **Yara:** And one more honest line. The horizon sizer's zero floor touches are partly structural. It resizes from the cushion every morning. Only an intraday hole bigger than the cushion can touch the floor. The harness runs intraday paths at forty trades a day with size held, gaps mid-day, correlated results, before anyone trusts that zero.

🏗️ **Ada:** And the demo account. Agents hold cTrader's order tools on it. A position an agent opens reads "not ours". No rule sees it. It still moves the balance.

🛡️ **Marguerite:** A `foreign` line in the account numbers. Margin and open risk counted at the account, never in a unit. And a separate demo account for agents, if the build will give one.

**Close.** The room did not agree on everything; it changed the draft in these places, all folded into `FUNNEL.md`:
1. H defined as trade rate times days so X2-H01 and X2-H02 are one formula (F2).
2. `basis:unmarked` on the receipt until marked equity exists (DP12, F3).
3. The fast-invalidation cut named as the critical path for the scalper profile, with the arithmetic (F1).
4. The day-one fallback ladder for the percentile brake (DP17, F4).
5. Retry-then-lockout as the default under Q1, with HALTED, the kill switch, promotion and lockouts his.
6. Shape C (flat first) as the first increment of both A and B (section 5).
7. The ramp cost and pooled cohorts for slow units (F11).
8. The structural "0 % touches" caveat (F12).
9. The `foreign` scope for agent positions on the bound demo account (DP33, F16).
