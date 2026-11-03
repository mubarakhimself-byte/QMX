# X7 roundtable (bmad-party-mode, session mode, non-interactive)

Run headless on 2026-11-03 by the X7 agent, which voiced every persona. The operator's lines are built from his own words in `seeds/SEEDS.md` and `seeds/operator-words-2026-11-03.md`; quoted phrases are his. The hybrids under stress are in `expansion/X7-agents.md`.

**The room**
- 📉 **Dana**, risk manager at a multi-manager pod shop. Terse. Thinks in drawdown ladders and capital at risk.
- ⚡ **Kofi**, retail scalper, 1-minute FX and crypto. Hates being stopped out by a nanny. Watches spreads, not stories.
- 🛠️ **Priya**, platform engineer who built the host door. Thinks in seams, contracts and rework.
- 🎙️ **Mubarak** (the operator's voice, from his words).
- 🧪 **Ilya**, red-teamer for agent systems. Assumes every input is hostile.
- 📜 **Margaret**, model-risk validator from a bank. Says "effective challenge" a lot.
- 📟 **Tom**, SRE on-call lead. Has muted a thousand alerts and regrets most of them.
- 📊 **Wei**, statistician. Counts trials. Distrusts every backtest he did not see the denominator of.

---

## Round 1: the door (X7-H01, H02)

🛠️ **Priya:** The good news is half the door is built. The host names every caller. A chat is `agent:<session>`, an MCP client is an agent, a workflow is `workflow:<run>`. A `manage` operation answers only to the operator. Kill, pause, resume, flatten, deploy: all `manage`. So today an agent cannot touch them.

🧪 **Ilya:** Today. What stops someone adding a `domain_write` op called `nudge_risk_fraction` next month?

🛠️ **Priya:** Nothing. That's the hole. Approval tier says *who may call*. It says nothing about *which way risk moves*.

📉 **Dana:** Then add the direction. Read, propose, cut, raise, money. Agents get the first three. Everything else is his.

⚡ **Kofi:** "Cut" by an agent is still my trade not taken. I don't want some LLM halving my size because a headline said "BREAKING".

🧪 **Ilya:** You shouldn't. Strip the credibility cues before the model reads it. Same false claim, zero percent success in that sandbox.

🎙️ **Mubarak:** "Agents never touch money." That's the line. But "agents do most of the heavy lifting... they're meant to just give me the units. I click."

📜 **Margaret:** Both hold if the lattice is checked by machine, not by the agent's description. The checker reads the effect, not the story.

**Outcome.** H02 (monotone action lattice) survives and gains a contract test: the host refuses any operation whose declared direction is `raise` or `money` for a non-operator principal, and CI fails if a new operation lacks a direction. Kofi's objection moves to Round 2.

## Round 2: evidence as a fact the unit's own rule reads (X7-H03)

📉 **Dana:** Ruling 2 says only a unit's own rule may change trading by itself. Fine. So make the agent's record an input to the unit's rule. The unit decides. The agent testifies.

⚡ **Kofi:** And my scalper declares it reads... nothing. A 187-second LLM is useless at 1 minute.

📊 **Wei:** Then the template needs a style eligibility check. Evidence time to live must exceed the unit's holding time by a margin, or the unit cannot accept that kind.

🧪 **Ilya:** And the record must die quietly. Expired, malformed, or the feed is down: no change. Not a cut, not a raise. Neutral.

🛠️ **Priya:** Three feeds, three fail modes. The MIS board fails open. Isolation wants fail closed. Agent evidence fails neutral. If we don't show all three on one screen, nobody will remember which is which.

🎙️ **Mubarak:** "You can't simply say if they differ, you simply pull out. It can be a bad day, man." Size down, "but not quickly."

📉 **Dana:** Then the unit's rule has a maximum cut per kind and a floor. One news record can take you to 0.7, not to zero. Two corroborated from different feeds, maybe 0.5.

📜 **Margaret:** And it has to beat a random cutter that fires as often. Otherwise you're paying for a nervous agent.

**Outcome.** H03 survives with three amendments: (a) a per-style eligibility rule (`agent_evidence_style_scope`); (b) a per-kind largest cut and a floor (`agent_evidence_max_cut`); (c) a neutral fail mode, shown beside the MIS and isolation fail modes on the unit's preflight. H11 (matched random de-risker) becomes the condition for keeping the channel open per class.

## Round 3: the attention budget (X7-H15, H16, H18)

📟 **Tom:** Forty units, one card a night each. By Thursday he's muting the channel. I've seen it. ICU, 187 alarms per bed per day.

🎙️ **Mubarak:** "Long multi-section answers go unread." Give me the units. Three things that need me.

📟 **Tom:** So: a hard cap. Three cards a day. Ranked by money per minute of his reading. The rest goes to a digest he can ignore without guilt.

📊 **Wei:** Ranked by whose money estimate? The proposer's? That's the fox pricing the henhouse.

🛠️ **Priya:** The run surface computes it. Resize replay, trip tax, cost of conservatism. Deterministic. The agent never writes the number.

📉 **Dana:** And the quota per agent. Accepted and held, it grows by one. Reversed, it halves. TCP for proposals.

📜 **Margaret:** Two budgets on one flow will fight. Pick one hard limit. The other is a ranking weight.

📟 **Tom:** His attention is the hard limit. Agent credit only orders the queue.

🎙️ **Mubarak:** And if I say yes to the same kind of card ten times?

📟 **Tom:** Then it shouldn't be a card. Offer to make it a rule you approve once.

🧪 **Ilya:** With an expiry on the approval. Rules approved once and forgotten are how Knight Capital happened.

**Outcome.** H15 keeps one hard limit (cards per day) and uses H18's agent credit only for ordering; H10's staking stays wild. H16 (graduation into a pre-authorised rule) survives with an approval time to live and a re-confirm at expiry (`preauthorised_rule_ttl`).

## Round 4: slow isolation by nomination (X7-H21)

🎙️ **Mubarak:** "It can isolate crypto. And everything is off for crypto." "It should kick in with the evidence that this market should be isolated." Analysis "over 20 days."

📉 **Dana:** A pod shop doesn't wait for the PM to click when a book is bleeding. The risk desk cuts it. But the desk is code, not an analyst's essay.

🧪 **Ilya:** So the agent nominates. Code confirms on the same window with two independent tells. If both agree and he pre-authorised class isolation, it applies with a time to live.

⚡ **Kofi:** Crypto scalpers trade weekends. Your FX baselines will call a quiet Sunday "stress".

📊 **Wei:** Calendar-aware baselines per class. And every isolation records whether a loss followed. A noisy isolation rule is a defect.

🛠️ **Priya:** Blocker: there is no class scope in the kill switch, stand-downs or the board. That's a node change, not an agent change.

📜 **Margaret:** Then the isolation card is the only path until the scope exists. Ship the card first; the automatic path waits for the scope.

**Outcome.** H21 survives in two stages: stage 1 card-only (works on the shipped stack plus a card template); stage 2 nominate-confirm-apply once a `class:` and `region:` scope exists in the node. The agent's evidence window (`isolation_nomination_window_days`) is a number with a derivation, not "20" by habit.

## Round 5: the sitting-duck advocate (X7-H32, H05)

🎙️ **Mubarak:** "I don't want just safety. I want something that can like perform." The $300 "sitting duck".

📉 **Dana:** Every brake I run has a re-risk path. If it doesn't, it's a kill line wearing a hat.

⚡ **Kofi:** Finally. An agent on my side.

📊 **Wei:** On your side with evidence. Restore needs an e-value on trades after the cut plus a minimum time. Ten wins in a row prove nothing for a 70 % unit.

📟 **Tom:** And restore cards share the same three slots. Otherwise the advocate floods him too.

📜 **Margaret:** Watch the get-even pattern. A raise asked for right after a loss goes slow lane. Garvey, Murphy, Wu: the traders who asked hardest lost most.

**Outcome.** H32 survives, sharing the attention budget. H05's pre-authorised restore ladder survives as the main growth path, gated by the e-value rule; H19 (get-even guard) applies to the advocate as to everyone.

## Round 6: one door for the Lab, MCP agents and the department (X7-H36, H37, H38)

🛠️ **Priya:** Two homes are on the table: catalog rows in `qmx_control` (X1's list) or a risk mini app with its own MCP server. If we build both separately we'll maintain two tool sets forever.

🎙️ **Mubarak:** "We added MCPs... CTrader... I think we should also ship something for crypto." "Adapt the design so that I don't have to build more when the time reaches."

🛠️ **Priya:** Then one implementation: the app's operations. Catalog rows are thin aliases. Every call carries a run id, an agent profile id and a model id, so a shepherd can fork and replay runs later without the door changing.

🧪 **Ilya:** And the money MCPs stay inside the trading-node app. If the build session's cTrader MCP is a separate server with order tools, it bypasses the door. Somebody has to check.

📊 **Wei:** The Lab writes to the same search ledger. A pod variant tried in the Lab is a trial.

**Outcome.** H36 survives as "one implementation, two names". H38's run-id contract survives (QMA flag). The cTrader MCP check becomes a collision (C9) and a gap, not a design.

## Round 7: where it broke

📜 **Margaret:** The challenger must see the claim to attack it. Your rationale-blind checker hides it. Those are two different roles. Don't merge them.

📊 **Wei:** Autonomy demoted on book drawdown punishes agents for the market. Demote on *their* reversals and precision, and freeze, not demote, on book drawdown.

🎙️ **Mubarak:** "The sky's the limit." Agents should be able to propose anything.

📟 **Tom:** They can propose anything into the run surface. Only three things a day reach you.

**Outcome.** H13 (rationale-blind checker) and the challenger stay separate roles: the checker decides admissibility without the rationale; the challenger attacks with it and writes a note, never a verdict. H18's demotion trigger splits: agent-caused (reversals, precision) demotes; book drawdown only freezes new autonomy grants. "Sky's the limit" maps to an unlimited run surface and a limited queue.

---

## What changed in the hybrids

| Hybrid | Change from the roundtable |
|---|---|
| X7-H02 | contract test: every operation declares a direction; CI fails without one |
| X7-H03 | style eligibility, per-kind largest cut and floor, neutral fail mode shown beside other feeds |
| X7-H11 | becomes the condition for keeping an evidence channel open per class |
| X7-H15 | one hard limit (cards per day); agent credit only ranks |
| X7-H16 | pre-authorised rules carry an approval time to live |
| X7-H18 | demotion on agent-caused signals; book drawdown only freezes grants |
| X7-H21 | two stages: card first; automatic path after the node gains class and region scopes |
| X7-H32 | shares the attention budget; get-even guard applies |
| X7-H36 | one implementation, catalog rows as aliases |
| X7-H13 | stays separate from the challenger role |
