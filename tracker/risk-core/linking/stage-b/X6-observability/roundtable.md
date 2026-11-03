# X6 roundtable (bmad-party-mode, session mode, non-interactive)

All voices played inline by one agent; no subagents. The operator's voice uses only his recorded words (SEEDS, OW1, OW3, UI-NOTES quotes). Hybrids stressed: X6-01 fold, X6-06 codes, X6-08 motion receipts, X6-11 six lights, X6-15 burn tiers, X6-17 wake contract, X6-21/22 brake scorecard and trip tax, X6-30 cost ledger.

**Personas.** Dana, pod-shop risk manager. Kofi, retail scalper (FX and gold, about 30 trades a day on cTrader). Priya, platform engineer and on-call lead. The operator's voice. Helen, ICU clinical alarm engineer. Ruiz, aviation human-factors engineer. Sam, swing trader (indices, two trades a week). Lin, crypto desk that never closes. Mei, bank model validator.

## Round 1: the fold (X6-01) and the six lights (X6-11)

- **Dana.** My morning one-pager per PM is P&L, drawdown from peak, distance to the stop-out, gross and net exposure by factor. If your fold has those per unit and per book, I am happy. I do not care about heartbeats.
- **Priya.** Emitting the full fold every pass on a scalper's node will fill the VPS disk and the journal. On change plus a heartbeat, deltas on the journal, the full fold in memory and on read.
- **Operator's voice.** "how do we know that this is wrong, this is right, it's working, it's up, it's on ... Then, you know, it's trading." (M12)
- **Ruiz.** Design the dark cockpit. When everything is normal nothing is lit. Six lights glowing green all day train the eye to stop looking.
- **Helen.** And a green that is stale is worse than no light. Every light needs an age.
- **Outcome.** X6-01 emits on change plus heartbeat. X6-11 adds the dark-cockpit rule: normal is quiet, and a stale fact shows UNKNOWN (grey), never green. Dana's one-pager becomes the unit and book card fields in X6-13.

## Round 2: codes and two ledgers (X6-06, X6-05)

- **Kofi.** Half my losers are cut early. If your breaker counts them like full stops I am benched by lunch. And I want to see my FI rate; when it drops my edge is gone before my P&L shows it.
- **Mei.** Record the cause class of every red: model, imprecision, bad luck, execution. Basel does it. Without it a red teaches nothing.
- **Priya.** Text-matched codes are a bug factory. Codes at the source, a contract test, delete the map.
- **Outcome.** Codes at source (X6-06) carry the cause class Mei asked for. The event ledger (X6-05) shows FI rate, scratch rate and full-stop share on the scalper card.

## Round 3: alerts and the phone (X6-14, X6-15, X6-16, X6-17)

- **Sam.** Two trades a week. Your burn rate over an hour is noise; one bad trade is a 50 % burn. Give me a per-trade rule.
- **Lin.** "Pushes only while the market is open." Crypto is always open, and my weekend gap risk is on FX positions held into Monday. Page on open positions, not on open markets.
- **Helen.** Add a delay per signal from its own history so a 2-second spread spike never sounds. And measure how many pages he ignores.
- **Ruiz.** One aural at a time, by priority. And a page must name the action. If there is no action, it is not a page.
- **Operator's voice.** "Because if you're trading 24 hours a day, multiple instruments, we need to be able to not just do one break at a go ... We need to be able to know what is breaking." (M8)
- **Dana.** Your account must stop safely without him. A page is information, not the control.
- **Outcome.** X6-15 adds the low-traffic rule (per-trade loss against the card's p95 when the trade rate is under a set level). X6-17 wakes on open positions and money at risk, never on market hours, and every page names an action and a deadline. X6-16 groups by root cause. Helen's ignored-page count becomes X6-26.

## Round 4: what safety costs (X6-21, X6-22, X6-23)

- **Operator's voice.** "I don't want just safety. I want something that can like perform" and the "sitting duck thing" (M33).
- **Dana.** We charge every stop-out to the risk desk's own book of 'opportunity lost'. If a brake costs more than it saves for a year, it goes.
- **Mei.** Precision needs a null. A brake that fires as often at random and does as well is worth nothing.
- **Kofi.** Show me the would-have line. If the brake had not fired, what would I have made today?
- **Helen.** Hospitals found 85-99 % of alarms need no action. If your brakes are like that, he will turn them off in his head.
- **Outcome.** X6-21 scores each brake against a random brake at matched frequency. X6-22 shows trip tax and the sitting-duck meter on the unit card. Precision of fewer than N fires reads "too few fires to judge".

## Round 5: numbers that move (X6-08) and costs (X6-30)

- **Operator's voice.** On self-set numbers: every move needs a stated reason, the volleyball picture (A13); "What if I want to change the way it is derived?" (D46).
- **Priya.** Spec is his; status is the runtime's. Never let a controller write the spec.
- **Kofi.** Show my real spread by hour against what the card assumed. On gold at the rollover hour it triples.
- **Lin.** Funding is a cost line, not a loss. Book it apart.
- **Outcome.** X6-08 keeps spec and status apart and adds the applier mode to every receipt. X6-30 keys cost cells by instrument, hour, broker and order type, with funding, swap and roll as their own lines (A5-95).

## Round 6: dissent kept

- **Dana** wants brake thresholds hidden from agents so they cannot propose sizes that sit just under a trip. **Priya** says agents must see distance to trip to make feasible proposals (A4-133). Kept as a collision (X6 collisions, item 10).
- **Sam** doubts the silence detector for swing units: two trades a week means silence is normal for days. Kept: X6-12 is marked plausible, with the weakest link named.
- **Ruiz** wants a sound map (X6-47). **Priya** calls it gimmick. Kept as wild.

## What changed after the roundtable

1. Dark-cockpit rule and stale-to-grey rule on X6-11.
2. On-change emission on X6-01.
3. Low-traffic rule on X6-15.
4. Page on open positions, not market hours, on X6-17.
5. Cause class on every red (X6-06), from Mei.
6. Random-brake null on X6-21.
7. Funding, swap and roll as separate cost lines on X6-30.
