# Pod grounding, 12 November 2026

Read-only research. Nothing here is a design or a ruling. It gathers what the owner has said about "pods", what the old Book and BMS did, and what code exists, so a pod-central design can be drafted next.

**Sources and short names**

| Short name | Path |
|---|---|
| NUMBERS | `C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/5534aebf-0aee-489f-850b-f15ac8efdd0a.jsonl` ("QMX numbers and strategy", 9 Nov). All 17 of his turns read; agent replies grepped for "pod". |
| RISK | `.../2928e6ee-7392-4c1c-87c8-23b375749b4f.jsonl` (risk planning, 1 to 10 Nov). His turns grepped. |
| TODAY | `.../dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26.jsonl`, his message of 12 Nov 12:29 UTC. |
| WORDS | `D:/QMX-worktrees/risk-plan/tracker/risk-core/seeds/operator-words-2026-11-0{1,3,6,9}.md` (his words verbatim, line numbers below). |
| OCT27 | `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/operator/2026-10-27-review-dictation.md` |
| G4, G6 | `D:/QMX-worktrees/risk-plan/tracker/risk-core/grounding/G4-current-book-bms.md`, `G6-book-bms-levels-and-paper.md` |
| GB | `C:/Users/Mubarak/Documents/QMX/raw/online/qmx-gitbook/captures/2026-07-18T141659Z/pages/markdown/components/` (GitBook, July) |
| SPINE, SOLUTION | `D:/QMX-worktrees/risk-plan/tracker/risk-core/round-2/arch/final/SPINE.md`, `SOLUTION.md` |
| E2 | `D:/QMX-worktrees/risk-plan/tracker/risk-core/round-2/expand/E2-pods-miniapps.md` |
| INTENT-B | `D:/QMX-worktrees/risk-ship/PLAN-INTENT-B-2026-11-12.md` |
| LAB | `D:/QMX-worktrees/risk-plan/tracker/qma-v2/architecture/lab-and-pods/` (October Lab design, unbuilt) |
| EB | branch `origin/engine/base` at `3ae41ffcb` (8 Nov) |

Quotes are his dictation, cut for length with "...". Typos from dictation are kept.

---

## 1. His words on pods, by theme

### 1.1 What a pod is

- **Pod = Book plus BMS, versioned.** "You see how a book was and how a BMS was. I think a pod is basically the entire thing, the BMS and the book. The only issue is it has different versions, so numbers can change." (TODAY, 12 Nov)
- **Portfolio-like.** "for me, I think a pod, you can think of it like a portfolio... What do you call a pod? Because I envisioned it like a portfolio" (TODAY, 12 Nov)
- **Everything under risk and sizing.** "a pod was meant to be literally everything under risk management, position sizing." He adds: "I don't have an actual answer, a clear one anyway." (TODAY, 12 Nov)
- **Circumstantial.** "a pod is circumstantial. I could want a pod for cash flow. I could want a pod for stability. I could want a pod for a specific instrument or a specific time frame. That is the level of extensibility that QMX is meant to have." (TODAY, 12 Nov)
- **Built from the scalping book idea.** "There is something called the scalping book... It was using the book and the BMS... one version of a book which was for scalpers. Now, what a pod is the combination of what BMS is meant to do for that scalping" (TODAY, 12 Nov)
- **Hedge-fund origin of the word.** "the term book wasn't my idea. The term book came from a session where I was curious on how hedge funds actually handled this. So I think they use pods." (WORDS 11-01:50, 1 Nov). "Hedge funds, I think, have pods, but I think their pods are specific." (TODAY, 12 Nov)
- **Earlier: pod is the BMS alone.** "the pod is literally the BMS in a way... the BMS already catered for everything in the account guard, so we need to standardize these two... maybe let's combine it with the pod." He called the Book "a little bit overkill". (OCT27, 27 Oct)
- **Earlier: BMS as pod manager.** "It sort of controls the capital. Think of it like the pod manager in a hedge fund. I don't know if that's right" (WORDS 11-01:84, 1 Nov)
- **Earlier: pod as a risk template under a unit.** "templatize what now, should I call it a pod under a unit can be?... Sorry, not under a pod, for a unit." (WORDS 11-01:84). "having a pod or the risk management information sizing system as a pod and templatizing it inside the unit" (WORDS 11-01:98, 1 Nov)
- **Earlier: pods as mini apps, more like the book.** "units are not mini apps, obviously, but pods are meant to be mini apps. But if you look at the definition of a pod in a hedge fund setup, it's more like the book... how do we ship pods?" (WORDS 11-03:13, 3 Nov)
- **The game plan is a pod.** "So I think we are designing a pod, if I'm not mistaken... I think this is a pod. This is more like a pod or a mini alpha, but more of a pod." (NUMBERS, 9 Nov 10:55)
- **Hedge-fund department sense.** "a mini app that is optimized for futures... workflows... maybe an FX also mini app... I think in a hedge fund, that's called what? A pod, if I'm not mistaken... agents that are specialized" (WORDS 11-06:66, 7 Nov). Then, pushed back on: "I said, I think... I did not say it is... Okay, so a mini app is different also." (WORDS 11-06:72, 7 Nov)
- **Pods are configuration, not rigid rules.** "question number five [portfolio day stop] is really more of a pod life question... QMX is customizable... I highly doubt you even know what a pod is." (WORDS 11-06:60, 7 Nov)
- **Copilot builds pods.** "That's why we have pods. That's why we have mini-apps... on a random day, I can decide to make a new unit or a specific pod... set different numbers, different configurations" (WORDS 11-06:66, 7 Nov)
- **Open to replacement.** "If the pod thing makes no sense, you can propose something new, but [you'll] talk about everything you've overhauled when we come back." (WORDS 11-06:102, 7 Nov)

### 1.2 What a pod holds

- **Money rules and its own exit rules.** "exit rules may be fixed or may not... for a scalper, we may require first invalidation, which is relating to the money rules or the rules inside the pod... these things are not random; they are thought through, whether through the copilot or whether pre-built" (TODAY, 12 Nov)
- **Its own sizing style.** "we don't have to only rely on one style of sizing... the BMS... could also handle another type of style or another type of trading book" (WORDS 11-01:84, 1 Nov)
- **Self-optimising at portfolio level.** "self-optimizing at a portfolio level in that it can be like, nah, let's reduce the number of scalpers, or let's now open up more slots... At a BMS level, opens up more slots to go to intraday or go to this, if the capital allows... the BMS was doing this... It's just that it wasn't self-configured." (RISK, 3 Nov 10:46)
- **Versions, so numbers can change** (TODAY, above). In NUMBERS the agent framed the stage switch "at $5,000 the math changes" as part of the pod; he did not object.
- **Win-rate targets differ by method inside a cluster.** "this is a cluster. We are not having only one strategy... a win rate is something that a scalper really needs. But when you go to ORB, the math changes." (NUMBERS, 9 Nov 16:40)

### 1.3 Units and pods

- **Units live inside pods, usually.** "pods literally have to contain units, and it goes even the other way around, which means a unit has to be specific to a pod, most likely. I highly doubt a unit may stand alone... It's possible, and I think we can design for both" (TODAY, 12 Nov)
- **One unit, several pods.** "every unit has to be in a specific pod or multiple pods, give or take... a mean reverting scalper with specific risk and sizing rules, or multiple variants of risk and sizing rules. And you can argue against this" (TODAY, 12 Nov)
- **The risk session's real job.** "I think the whole point of that session was to just ship a template. That's it. Okay. We needed something that we can build pods around." (TODAY, 12 Nov). Later: "what I thought I requested for, maybe is the template to finish like a unit as a whole." (TODAY)
- **Pod-central now.** "I think the design kind of changes to now more of a pod central design... everything that session did, I'm not saying it's wrong, it's just that it might have been overkill." (TODAY, 12 Nov)
- **One pod or two in the first game plan.** "does ORB get its own pod?" (NUMBERS, 9 Nov 11:14). "do you think we should design two pods, or is just we first design only one pod?" (NUMBERS, 9 Nov 11:23). The agent proposed "two pods under one money group" (a scalper pod and an ORB pod sharing the $500).
- **Splitting money.** 1 Nov: split the seed $300 scalpers / $200 intraday (G1 / RISK summary). 9 Nov: "if our best chances... is not splitting. I won't split it... Splitting only works if we are sure that the split is necessary", then in the same turn "no, we can keep the split because... The scalpers take the rest of the day". (NUMBERS, 9 Nov 11:23). The agent's summary of the first pod: "Money: one pot, no split."
- **A unit is one whole algorithm.** "A unit is a strategy... they shouldn't have separations." (13 Oct, via G1). "Nothing other than the unit itself controls how it trades. The router never touches a thing." (24-28 Oct, via G1)

### 1.4 Accounts

- **Many accounts, by platform and asset class.** "we can have one central account... okay, not one. We can have many... IBKR if it's there... IC Markets... CTrader... the same account I use on crypto won't be the same account I use on futures, won't be the same account I use on CFDs and spot." (TODAY, 12 Nov)
- **Every pod touches an account balance.** "I think all pods obviously will have to touch as an account balance." (TODAY, 12 Nov)
- **Sizing from one shared balance: yes for now, no in general.** "It's a yes because at the moment it's going to be one. But as QMX grows, it's not meant to be limited... sharing an account across everything, ideally, I think no." (TODAY, 12 Nov)
- **Platforms, not brokers.** "brokers are connected to an intermediary platform... IC Markets connects to CTrader very well... I don't think MT5 is there... QML I think is best used with CTrader... we had that ability to add multiple brokers, or rather multiple platforms. So MT5 was catered for, I believe. CTrader was catered for, and I believe IBKR and others like Ninja Trader" (TODAY, 12 Nov). "when I get big enough, I think IBKR might be easier, but CTrader might be my long-term use one." (TODAY)
- **Brokers aren't fixed.** "CTrader is not the only platform, then as well as IC markets... Those are not fixed variables... I think there is Deriv." (NUMBERS, 9 Nov 11:23)
- **Demo means a broker demo account.** "A paper account is a paper or a demo trading account... Let me stop using the word paper trading. Let me use demo." (TODAY, 12 Nov)

### 1.5 Brakes and exits

- **Brakes prevent, never close.** "Breaks were never meant to close trades. No, breaks were meant to stop trading or prevent trading... Do not fix the symptom, fix the cause." (TODAY, 12 Nov)
- **What counts as a brake.** "The reverse house of money... the SQS and the kill switch, those are breaks because they take circumstantial values... If we are close to our kill line... the break was meant to prevent going below a certain value." (TODAY, 12 Nov)
- **Only the black-swan level closes.** "The only thing to close a trade automatically, I think, would have been I think the highest level of a kill switch, which is like a black swan event, and I think it's already there" (TODAY, 12 Nov)
- **Exits: unit first, pod may add.** "agents inside QMA... building the strategies from any source... depending on the source can give an exit. That's what QML, I think, already considers... However... there are exits that may be required depending on the trading methodology or depending on the pod it is in." (TODAY, 12 Nov)
- **Group invalidation idea.** "if the markets are moving against our overall spread book, overall spread bets, we can now use fast invalidation or move to break even. Anyway, it's just an idea." (NUMBERS, 9 Nov 11:14). The agent turned this into "related trades as one bet with one stop budget"; he called a related idea "interesting".
- **Stepping off a failing market.** "if it already fails in one market, it can, you know, get off that market... this is where now our breaks need to come in." (NUMBERS, 9 Nov 10:55)
- **Earlier: unit owns its exit.** "the unit is going to own its own exit" (30 Oct, R-04, via G4 §6 item 8). The exit may be part of the strategy's DNA (13 Oct, via G1).

### 1.6 What sits outside pods

- **Things external to a pod.** "Of course, we have a correlation ledger. Now, there are things that are meant to be external outside of the pod, so independent... I didn't mention this, but... there are things external to a pod." (TODAY, 12 Nov)
- **Account guard is outside the unit.** "account guard is outside the unit." (OCT27, 27 Oct)
- **Guards stand on their own.** SQS, news kill switch and similar guards "can be off... feeding of the news, feeding of the spread, those are all very, very independent" (OCT27, 27 Oct). The router never switches a unit on or off; a unit keeps trading if the router is down (27 Oct, via G1).
- **Breadth analysis is a workflow, not the pod.** "agents that could sort of do the analysis across all these... give us the instruments... It's the same way I think how hedge funds sort of work... this is already there... It's a workflow." (NUMBERS, 9 Nov 11:38)
- **Correlation, from the numbers talk.** He liked "trade per cluster" ("Now the trade per cluster is an interesting one", NUMBERS 9 Nov 11:32) and "trade on the strongest one" ("Oh, that's an interesting view", NUMBERS 9 Nov 11:23). Where that rule lives (in a pod or outside) was not discussed.

---

## 2. What the old Book and BMS did

- **Rule of command.** "Bots trade; books control bots; BMS accounts for and constrains books; nothing above a bot touches the market." One BMS per account; a Book binds one BMS; a bot binds one Book; a Book never spans brokers. (`C:/Users/Mubarak/Desktop/QMX/docs/components/qmf-risk.md:56-62`; ADR-0008)
- **Book.** A versioned config document with ten sections: charter, footprint_requirements, money_rules, admission_bar, leash_grammar, capacity_and_sweep, exit_policy, control_policy, protection_windows, paper. Every number is UI-editable; an edit mints a new version. The Book owned the exit; a bot could only propose to close or tighten. (`docs/components/qmf-risk.md:79-93`; `docs/glossary.md:118`)
- **Book sizing ladder.** Book capital minus kill line gives runway; runway divided by periods gives a period budget; that divided by a loss allowance gives the price of 1R. Each Book had its own capital and its own kill line. (G4 §3.4)
- **Seven doors.** Footprint, viability veto, R max, daily budget, breaker, exposure ledger, kill switch. (GB `book-template.md`)
- **Scalper Book (July GitBook).** The first Book instance: "a treasury-customered cash-flow machine judged by swept cash per month per dollar of seed". Seed, kill line, cap multiplier (2.5x seed, sweep profit above it), runway divisor, breaker after consecutive stop-outs, max concurrent live bots. Benches bots to paper. (GB `scalper-book.md`). The current docs keep it as "one reusable Book pattern", never a global law (`docs/constitution.md:66`, DEC-0080).
- **GitBook glossary:** "Book: A pod with charter, capital, roster, profile, rules, and journals." (`GBF:159`, via G6 line 38)
- **BMS.** Supervisor of one broker account. Four desks: Treasury, Exposure, Records, Reporting. Owns the virtual ledger, exposure, the kill-switch policy, news blocks and journals. Never trades or sizes. Cross-Book exposure authority was always an open gap (GAP-0008). (GB `book-management-system.md`; `docs/contracts/ct-27-bms-definition.yaml`)
- **What was missing.** No allocator across units on one account, no account-wide daily loss stop, no correlation cap. Account constraints were a section name with no fields. (G4 §3.7, §7)
- **Kill line closed trades.** Touching it closed the Book's trades and stood it down (`qmf-risk.md:115`). This differs from his 12 Nov "brakes never close".
- **October Lab pod (designed, unbuilt).** A versioned stack of pure blocks in seven slots: inputs, guards, allocator, sizer, throttles, caps, ledger. It reaches trading only by compiling to a Book + BMS fragment. (LAB `ARCHITECTURE-SPINE.md` AD-10, AD-11.) The October UI had "Books are now Pods (each with a live side and a paper side)", and a Portfolio pod card showing money, room above the kill line, method, units and weights (LAB `UI-TO-BACKEND-MAP.md:122`).

---

## 3. What exists in code today

### 3.1 On `engine/base` (merged)

- **Library kinds** `pod` (only a free `slots` object), `pod-block` (slot, form, Python code blob), `book` and `bms` (both empty shells, `"properties": {}`). Path: `qmx-agents/packages/qmx-library/src/qmx_library/kinds/`.
- **Lab:** "Pods are not part of this backend" (`qmx-agents/packages/qmx-control/src/qmx_control/lab.py:22`).
- **Book/BMS types and validators**, 24 modules in `packages/qmf-risk/src/qmf/risk/`. Shapes only; nothing computes size from equity (G4 §5).
- **Node account binding.** The roster holds a list of accounts. Each row carries a venue, account, world, credentials reference, one BMS fingerprint and its Book bindings (`qmn/src/qmn/config/roster.py:129`, `AccountBindingDecl`). So many accounts per node already exist in the data shape, each tied to one BMS.
- **Built protections:** kill line, bench, breakeven ratchet, kill switch with levels, news and dead-zone windows, SQS (`qmn/src/qmn/capital/`, `qmn/src/qmn/protection/`). Never deployed live (G4 §5.1).
- **Correlation ledger:** a records projection name only, "BMS cohort/chorus correlation observations" (`packages/qmf-data/src/qmf/data/logbooks.py:1133-1163`, `packages/qmf-risk/src/qmf/risk/journal.py:119`). No live control reads it.

### 3.2 Multi-platform brokers on `engine/base`

| Platform | What exists |
|---|---|
| cTrader | Full live and demo node client (`qmn/src/qmn/venue/ctrader.py`, `ctrader_account.py`, `qmf-venue`), demo probes, read adapter |
| CCXT (Hyperliquid, Binance, Bybit) | Node client (`qmn/src/qmn/venue/ccxt_client.py`), read adapter |
| MT5 | Declared as a read-only platform type, Windows only (`qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:60-76`), and a fills importer (`packages/qmf-data/src/qmf/data/importers/journal.py`). The node refuses `mt5` as a trading client (`qmn/tests/test_qmn_venue_selection.py:177-234`). So MT5 can be read, not traded. |
| IBKR | Nothing in code. One test record uses "ibkr" as sample data (`qmx-library/tests/test_market_kinds.py:105`); the rest is research notes. |
| NinjaTrader | Nothing. |

The node's trading client kinds are `ctrader`, `ccxt` and `conformance` (`qmn/src/qmn/venue/port.py:44-51`).

### 3.3 On the risk stack (`build/rc-*`, 28 rows gated, none merged)

Per `D:/QMX-worktrees/risk-ship/STACK-LIST.md` and memory, the stack lands at stop points, and stop A was not ready on 12 Nov.

Built and gated, relevant to pods:
- Unit split into a logic half and a risk half, each with a fingerprint (rc-03). A pod design can reuse this split.
- A sizer that answers money, and one converter to the venue's quantity in the account's currency (rc-05, rc-06, rc-07).
- Brakes as control rows in the unit, states read from one fold (rc-13, rc-14). **rc-16 lets a brake flatten and close its own trades**, which conflicts with his 12 Nov rule.
- Canary template (rc-17); draft to demo on his click (rc-18, rc-19).
- Named size modifiers (rc-21); numbers with derivation, range and authority (rc-23, rc-24, rc-25).
- A live account surface on the node (rc-27); several positions per market (rc-32).
- The daily account brake (rc-29) is parked with a known hole: off if the PC is off over midnight.

Planned, not built (all are the pod and group layer):
- RC-49 group document, RC-50 group caps: a "thin group" holding shared money, limits and a ledger; it can only cut, never size (SPINE AD-8).
- RC-53 pods as recipes, RC-54 one plan one click, RC-55 move risk in place, RC-56 stages, RC-57 seed the 20-pod gallery (SPINE AD-4 to AD-7; E2 section d).
- Book and BMS Library kinds go read-only, absorbed into "group" (INTENT-B, RC-49 note).
- SPINE section 12 already prices the alternative, "a pod that governs": about 4 to 6 more PRs, the fork is at slice 13, "decide by stop point B".

INTENT-B (12 Nov) already flags the gap: the build split his "pod" into a recipe plus a thin group "before telling him", and nothing makes a pod a mini app.

---

## 4. Contradictions and gaps

**Between his own words over time**
1. **Direction of containment.** 1 Nov: a pod is a risk template "for a unit", "inside the unit". 12 Nov: units live inside pods. The 12 Nov view is the newer one.
2. **What a pod equals.** 27 Oct: the BMS alone, the Book is overkill. 3 Nov: "more like the book". 12 Nov: Book plus BMS. GitBook: a Book is "a pod".
3. **Pod and mini app.** 3 Nov: "pods are meant to be mini apps". 7 Nov: "a mini app is different also". 7 Nov also used "pod" for a team of specialist agents per market.
4. **Splitting money.** 1 Nov split $300/$200. 9 Nov "I won't split it", then "we can keep the split", in one message.
5. **Exits.** 13 and 30 Oct: the unit owns its exit. 12 Nov: a pod may require exits such as first invalidation.

**Between his words and the risk plan**
6. **Pod as a recipe vs pod as a container.** SPINE AD-4: a pod is a saved risk half stamped into each unit, with money in a separate "group". He sees one thing that holds units, money, rules and versions.
7. **Pod exit rules are refused.** AD-4: "a recipe row touching a logic-bound number or an exit is refused by name". His scalper pod needs a pod-level first invalidation.
8. **Brakes that flatten.** rc-16 is built and gated with a flatten verb. The docs' kill line also closes trades. He says only the black-swan kill-switch level closes.
9. **One unit in several pods.** The plan gives each unit one stamped risk half. A second risk variant means a second unit version or deployment. The deployment key is `(unit, version, market)`, so two live copies of one version on one market cannot coexist (INTENT-B D5). His August decisions list "parallel bot paper twins" as dead (ADR-0009, ADR-0022), which sits close to "one unit, two pods".
10. **Own money vs account balance.** The old Book had its own capital and kill line. He now says sizing reads the account the unit trades through. If a pod is Book plus BMS, does it own a slice of money, or only rules over the shared balance? Not said.
11. **Pods and accounts.** Old rule: one BMS per account, a Book never spans brokers. The plan's group lives on one node process. He wants many accounts split by asset class, and pods "for a specific instrument or timeframe". Whether a pod can span accounts is open.
12. **Correlation ledger.** He puts it outside pods. In code it was a BMS projection, and BMS is now inside the pod. The plan's live correlation control is a bet key plus a group cap, which sits inside the group. "One trade per cluster" needs a home that sees all pods.
13. **Where pods are built.** The October design builds pods in the Lab. He said today the UI may drop the Lab and the copilot covers it.
14. **Scope.** He asked for a unit template to build pods around. The plan grew to 69 PRs and a 20-pod gallery. He calls it "overkill" but "not wrong".

**Gaps nobody has filled**
- A pod that is a team (agents, workflows, mini apps) is built nowhere.
- IBKR has no code. MT5 can be read but not traded. The node trades only through cTrader and CCXT.
- Nothing defines what happens across pods: total exposure on one account shared by several pods, and which pod wins room on the same bar.

---

## 5. Questions only he can answer

1. Does each pod hold its own pot of money with its own floor, or do all pods share the account balance and only add rules on top?
2. Can one pod use more than one account, for example cTrader CFDs and Hyperliquid crypto together, or is each pod tied to one account?
3. When one unit sits in two pods, is it one running copy that obeys both pods, or two copies that each trade with their own risk and sizing?
4. If a pod adds an exit, such as first invalidation for scalpers, and the unit has its own exit, which one wins, or does the earlier one fire?
5. Besides the correlation ledger, what else sits outside every pod? Candidates: the kill switch, the spread sensor, news blocks, an account-wide daily loss limit.
6. Is the kill line a pod setting that only stops new trades, or should touching it still close that pod's trades?
7. Is "pod" only the money and risk side, or does it also include its own team of agents, workflows and mini apps, like a hedge-fund desk?
8. May a pod change its own numbers inside limits you set, for example switch stage at $5,000 or open more slots as money grows, or does every change need a new version and your click?
