# 53: What comes next, and does the unit hold

Written 2026-10-31 by a second Fable 5.1 reader, after his message at 2026-10-31T05:09: "combining everything in the transcript from, I don't know, 2 to 3 days ago till now, what should be the next step? [...] What are we missing? [...] Building with an orchestrator prompt". Also his meaning of "it works": "does a unit actually make sense? Because remember, you are moving from a bot to now a unit."

What I read in full: the three transcripts (T1 = 20-28 Oct, T2 = 29-30 Oct, T3 = 30-31 Oct), the three dictation files, `STATE.md`, `STANDING-ORDERS.md`, `HANDOFF-RISK-SIZING.md`, `seeds.md`, `wayfinder/MAP.md` and `RESEARCH-QUEUE.md`, research 52, the project `CLAUDE.md`, the planning-lead playbook, the "planning workflow that worked" memory. Read in part: research 43 (§3.1, §3.2, Appendix B, headings), the risk pack (§4). Code was read with `git show`, `git ls-tree`, `git grep` and `gh pr list` from `C:/Users/Mubarak/Desktop/QMX` against `origin/engine/base` (cee216e0, 31 Oct) and `origin/build/wu4`; nothing checked out. Skills: 216 `SKILL.md` files inventoried by script across the four skill roots; the key ones read. No helper agent was started (none is available to this run). One file written, this one. No commits.

**Lead's note, added after this file landed (31 Oct):** step 0 is already done. He merged the stack into `engine/base` while this was being written: PRs 207 to 234 show MERGED on GitHub between 05:13 and 05:25 UTC (`gh pr view`), and `origin/engine/base` is now at c93407ca ("Merge pull request #234"). Only PR 204 (agent backtests through QMB's door) and the old draft #25 ("do not merge") stay open. Read every "27 open PRs" below as merged.

Labels: **CHECKED** = I read it at the cited place (transcript line and time, `file:line`, or a command I ran). **INFERRED** = my judgement.

---

## The answer, on one screen

**The next step is not more planning. It is one small piece of running code.**

You asked whether a unit makes sense. A bot was a set of rules that leaned on outside parts: the Book sized it, something else set its exits, the router placed it. A unit is one algorithm that owns its entry, its exits, its sizing and its journal, and tunes its own numbers from that journal. That shape is normal. Every platform studied builds a strategy from the same parts and differs only on who owns the exits and the size. So the unit as "one complete algorithm" holds.

What is not yet shown is the one new claim: that it tunes itself. Today nothing in QMX can even write a unit down. The Library's unit page has no fields. The strategy library forbids writing a rule's conditions. The one backtest door for agents places no trades. So the honest test is not a list of features. It is this: write one unit as a document, compile it into the strategy library as it exists today, run it through the backtester so it places real trades, let one of its numbers move by its own rule from its own journal, and have a script, not an agent, say pass or fail. If that runs, the unit holds. If it does not, no architecture would have saved it. That is a two-day prototype, thrown away afterwards.

**Steps, in order.** First, the open pull requests: you said you have none, but 27 are still open (I checked this morning; two merged today). Merging is your click. Second, one short map of the big parts as they really are, built, stacked or never run, with every connection point named. Third, the prototype above, at the same time. Fourth, one design file per part, each small, each starting from what exists. Fifth, one review, one fix round. Sixth, the build plan, checked to zero problems, and the orchestrator prompt. About six working days, then building.

**What was missed.** Your real end goal, the orchestrator prompt, was never written down as the destination. The earlier session's explainer pages were never used as inputs. The deterministic checker you asked for already exists in the code and nobody told you. The dictionary rebuild was proposed inside the big plan file but never shown to you. Journals, clocks, monitoring and the platform languages are recorded as rulings and designed nowhere. Details below.

**What is weak in the unit idea, plainly.** "Self-tuning" means three different things. Two of them (recompute size from the balance; move a number inside a tested range from finished trades) work everywhere and are what QMX should do. The third (change the rules themselves) does not work without a human, and your own rule already forbids it. A scalper on one market makes 5 to 30 trades a day, and telling a real small edge from luck needs hundreds of trades, so a unit retunes weekly or monthly, never within the day. And a unit cannot tune itself from a placeholder sizer; the prototype must move a real number by a real rule even if the formula is a stand-in.

**Six things are yours.** Merge the stack or not. Accept the prototype's pass marks as what "the unit works" means. What your click admits. What self-tuning may touch. When the risk session starts. Whether "System 2" is parked until the first unit has a journal. Each has my answer in section 5.

---

## 1. The next steps, in order

From where things stand now to the point where an orchestrator session dispatches builders, as `CLAUDE.md` describes for QMA v2 (one builder agent per numbered packet, the orchestrator verifies each PR; CHECKED `CLAUDE.md:7-12`). He stated this end goal himself: "all I want is for you to give me a prompt that uses potato mode [...] an orchestrator prompt" (T2:24, 2026-10-29T16:01, CHECKED).

Where things stand (CHECKED):
- `origin/engine/base` is at cee216e0 (31 Oct): PRs 207 and 211 merged this morning (`gh pr list --state merged`). Still open: 204, 208, 209, 210, 212 to 234, that is 27 build PRs, plus the old draft #25 (`gh pr list --state open`, run 31 Oct). The chain runs 208 → 209 → 210 → 212 → 213 → 214 → 215/216 → 217 → 218/219 → 220/221 → 222/223 → 224 → 225 → 226 … 229 → 231 → 230 → 233 → 232 → 234; 204 sits off the chain on `build/wu2`.
- Planning is on `plan/unit-system`, 45 research files, nothing pushed (`STATE.md`).
- His 31 Oct answers are recorded in `STATE.md` "Operator round 2026-10-31 morning" (CHECKED): placeholders for sizing and exits; a placeholder unit and market for the proof; Linux node with WSL as fallback; April rules scrapped; a server is a server; QMX must work out of the box for a newcomer; the fixed rulings as trimmed.

| # | Step | Produces | Who | Skills / method | Time |
| --- | --- | --- | --- | --- | --- |
| 0 | **Land the stack, or decide not to.** He believes "I don't think I have any unmerged PRs" (T3:1332). 27 are open. Nothing in them has run on his real QMX folder (research 42, CHECKED via STATE:259). | A yes or no from him; if yes, the lead verifies each merge with `gh` and `git ls-remote` (never merges itself; `never-merge-unasked` memory) | Him (the clicks), the lead (the checks) | none; `gh pr list`, `gh pr view` | 1 hour of his clicks, spread over the chain |
| 1 | **Level 0: the map of the big parts as they are.** One file: each part (QML, the unit, QMB, the MIS, journals, the trading node and its DevOps, external connections, the Library, the engine and templates, risk shapes), its job in one line, its state (built / stacked in PR N / missing / never run), file paths, and every connection point with the data that crosses it. Research 52 §9 is a first draft; research 18 and 42 are the groundings. Mostly assembly, not research. | `architecture/00-level-0.md` plus `architecture/01-connections.md`; one picture if he wants one | One Opus agent | `codebase-design` (seams, deep modules), `domain-modeling` (the fifteen words settled once), then `bmad-architecture` headless to cut the parent spine from it (small; `lint_spine.py` to 0) | 1 day |
| 2 | **The prototype: prove the unit in code.** Runs in parallel with step 1 on `build/unit-system` in a `proto/` folder, marked throwaway. Pass marks in section 3.3. | A few hundred lines that compile a unit document into QML's existing factory, run it through QMB with trades, write a journal, move one number by rule, and a checker that says pass or fail | One Opus `poteto-agent` builder | `prototype` skill (logic branch), `principle-prove-it-works`, `principle-foundational-thinking`; `tdd` optional | 1 to 2 days |
| 3 | **Level 1: one design pass per part, each its own file**, in the order the prototype teaches. Each file: what exists (paths), what is added, what it must not break, how it is checked, which of his rulings bind it, and the two shapes compared where a real fork exists. Parts: the unit template and the checker; QML (block catalogue, unit document, conformance extended, "the bot may not size" lifted for units, the language question); QMB (runner that trades, windowed reader, R, agent door); journals in depth; the trading node with its DevOps layer (clocks, monitoring, Windows, how orders are placed); external connections (cTrader on the PC merged today; CCXT reads only; Hyperliquid absent; a futures broker); the MIS as library readings with stamped logs; workflow templates reading the MIS's logs; contracts between parts. | `architecture/10-unit.md`, `11-qml.md`, `12-qmb.md`, `13-journals.md`, `14-trading-node.md`, `15-connections.md`, `16-mis.md`, `17-templates.md`, `02-contracts.md` | Three Opus agents, each holding related parts: [unit + QML + checker], [QMB + journals + contracts], [node + DevOps + connections + MIS + templates] | `bmad-architecture` headless, each inheriting the Level 0 parent spine (the skill supports this: "Inheriting a parent spine", CHECKED in its SKILL.md); `codebase-design`; `principle-exhaust-the-design-space` for the two real forks (unit seam; node as Linux program vs a Windows trading role); `blast-radius` on the shipped code each part touches | 1.5 to 2 days |
| 4 | **One review, one fix round.** Edge-case, adversarial and verification-gap lenses over the money-adjacent parts (node, connections, unit runtime, QMB runner). | A findings file; the Level 1 files amended once | One Opus reviewer, then the Level 1 authors fix | `bmad-review` with lenses edge-case, adversarial, verification-gap | 1 day |
| 5 | **The build plan and the orchestrator prompt.** Packets numbered from the Level 1 files; the first packets are the prototype hardened (unit document and compiler, QMB runner and reader, journal kind and door, checker, placeholder sizer and exits, feed keeper and demo order path on the PC). Plan checked to 0 problems. Coordinator prompt per `CLAUDE.md` and the playbook §6; builder template; `build/unit-system` as the merge target (his word, T2:442). Builders partly on other models as he plans. | `PLAN.md` (0 problems), `PROMPT-ORCHESTRATOR.md`, `PROMPT-BUILDER.md`, the build store | The lead | `poteto-mode` `check-plan.mjs` (`~/.claude/skills/poteto-mode/scripts/check-plan.mjs`, CHECKED), the playbook §6 | 0.5 day |
| ∥ | **The risk-and-sizing session**, from `RISK-SIZING-PACK.md`, when Level 1 is done. Its first job: the smallest honest sizer and one exit family for the first unit, replacing the placeholders. Not blocking, by his 31 Oct answer. | Rulings in `STATE.md`; the placeholder list to rip out | Him (the launch), a fresh session | the pack §4 socket questions | parallel |

About six working days to the orchestrator prompt, then one to two weeks of stacked PRs before the first unit trades on the cTrader demo from his PC (research 52 §8 item 10, INFERRED there and here). He said "there is no rush [...] can take up to 3 to 4 days" for planning (T2:845, CHECKED); the prototype adds a day or two and replaces every remaining research round.

What is deliberately **not** in the list: another expansion round, another convergence, the MIS models, breadth across markets, the trading server, news, the dictionary's 239 entries (only the ten or so the first unit needs), any UI. He fears "building things I didn't ask for, or building more on top of something simple" (T3:1091, CHECKED). The list above adds one new thing to QMX, the unit as data, and finishes three that exist (a backtest that trades, a journal, a demo order path on the PC).

---

## 2. What is missing: dropped or forgotten, checked against his words

Checked against the transcripts, not the lead's summaries.

1. **The destination was never written as he gave it.** 29 Oct: "the end goal of that entire workflow is planning, ideating edge cases and all that nonsense. [...] the end goal is having a session, okay, a prompt. [...] all I want is for you to give me a prompt that uses potato mode [...] an orchestrator prompt" (T2:24, CHECKED). The wayfinder map's destination reads "Architecture-ready decisions for every part" (`wayfinder/MAP.md:12`, CHECKED). No plan file, no packet list, no prompt draft exists on the branch (directory listing, CHECKED). The planning-lead playbook he pasted (T2:56) says the end products are "a ratified design, a plan checked to 0 problems, and a paste-ready coordinator prompt" (`PLANNING-LEAD-PLAYBOOK.md:8`, CHECKED). The run optimised for the first and never aimed at the other two.

2. **The earlier session's artifacts were dropped as inputs.** He said it twice: "that session had a lot of work proposed or provided from the artifacts it had made [...] it seems to me as if you're not considering them" (T2:55, 2026-10-29T16:09, CHECKED); "it had artifacts that were necessary" (T3:1292, CHECKED). The two explainer sites (14 and 11 pages; `STATE.md:14-15`) hold the build-path page, the old-rules page, the judging page, the library page and his 27 and 28 Oct reviews of them. Research 43 cites no explainer page (`grep -c -i 'explainer\|claude.ai/artifact' research/43-convergence.md` = 0, CHECKED). Their source is on disk (`explainers/src`, `explainers/round2`); nobody fed them to the convergence.

3. **The deterministic checker he asked for exists, and he was not told.** "how will they know that they have written the init and the init is correct [...] Favor determinism over non-determinism. That's the whole point of QML [...] in the QML version we have now, it might be existing. I am not certain" (T3:1080, CHECKED). It is: QML's conformance gate "spawns no process, performs no I/O, and starts no thread" and gates registration (`qml/src/qml/conformance/__init__.py:1-6` at engine/base, CHECKED). It checks today's bot shape, not a unit document; extending it is the checker. Research 52 said so (§4 QML row); no reply to him said so.

4. **The dictionary rebuild was proposed and never shown to him.** He: "you really haven't rebuilt the dictionary or haven't proposed how it's going to be rebuilt" (T3:1292, CHECKED). Research 43 §3.2 proposes it in detail: three faces per entry (trader words, machine spec, implementation), status computed, every number with kind, range, motion, authority and origin, class packs in door order (`research/43-convergence.md:203-234`, CHECKED). He has not read 43 ("I'm not trusting this work", T3:1080). Both are right: it exists, and it was never put in front of him in his register. It belongs in the QML Level 1 file as one page.

5. **The gold mine's intent for QML is a ruling, not yet a design input.** "the goldmine session had a lot more to say of the intentionality of where the dictionary was meant to end and how we were intending to build caramel [...] You shouldn't just put it aside" (T3:1080, CHECKED). Research 39 recovered its three layers (building blocks, roles, logic graph), more roles than four, named ports, variants as edits (STATE:260). Research 52 adds that the Stats logic graph (`Stats/schema/graph.yaml.md`, `strategy-dna.md`; on disk, CHECKED) is the ancestor of the unit document. Nothing yet says "the unit document is the gold mine's graph, upgraded"; the QML Level 1 pass must open with that sentence.

6. **The platform-language question is unresearched.** "we need to also know whether it's going to be Python, Golang, or I don't know which language, because each provider uses a different language [...] most of them, they use, is it a .NET? [...] Or C#" (T3:1080, CHECKED). Research 38 covered venue access (futures brokers, Hyperliquid limits), not the language each platform's strategy layer and API speak (STATE:271, CHECKED). The lead added it to the new program and then stopped the agent (T3:1174, killed). My own reading, INFERRED from general knowledge, to be checked in the connections pass: cTrader's Open API is protobuf messages over TLS, language-neutral, so Python on the PC is fine; CCXT is a Python library; NinjaTrader's strategy host is C# and would need a bridge or a different venue; MT5's bridge is its own Python package on Windows. The unit's logic stays Python; the venue adapters speak each venue's protocol. That is an adapter question, not a rewrite.

7. **Clocks, time zones and monitoring across machines.** His words: "clocks and time is it's an interesting thing [...] a trading node located in Singapore, and then [...] London [...] how is a trading node trading FX in London going to be able to also be monitored?" (T3:1080, CHECKED). Recorded as ruling 15 (`STATE.md:51`); designed nowhere. Belongs in the node Level 1 file: UTC everywhere inside, venue local time only on the instrument record and the screen; one time service; the WSL clock catch from research 31.

8. **The DevOps layer has two stacks and no decision.** QMN carries its own Grafana, Loki and Prometheus; the host has OpenObserve deep logs in stacked PR 232 (research 52 §9.1 DevOps row, CHECKED there). He: "We have, at the moment, we were planning on using OpenObserve" (T3:1080, CHECKED). One stack must win; the node file decides it.

9. **Journals were designed to his first instruction and not his last.** 27 Oct: "the journal in logic, it should just be just some sort of, man, it's anything that can record data" (D27, CHECKED); 30 Oct: "I would prefer most simple data schemas" (T2:1148, CHECKED); 31 Oct: "The journals have one simple row shape. I disagree. [...] multiple instruments [...] which broker or which account [...] which platform [...] which trading node [...] is it paper [...] The journal is very important, please" (T3:1080, CHECKED). Research 43's F4 ("one row shape, one writer per stream") followed the first two. The journals file must start again from his 31 Oct list: keys for unit, world (backtest, stress, paper, demo, live), phase, instrument, broker, account, platform, machine; plus the gates that refused a trade ("why didn't it trade?", his 27 Oct DevOps framing). No journal kind exists in the Library (`git ls-tree origin/engine/base | grep kinds/.*journal` = none, CHECKED).

10. **Mini apps were never looked at.** "units might be need to be integrated in mini apps. [...] Mini apps also, I think you haven't looked at that" (T3:1289, CHECKED). They exist: `docs/decisions/ADR-0034..0036-miniapp-*.md` and the template `d9-mini-app-pipeline` under `qmx_engine/templates/` (CHECKED at engine/base). The newcomer's out-of-the-box path ("factor in the logic of a person who wasn't in the planning", T3:1289) and mini apps belong in the templates file as one section, not a new area.

11. **"It works" was misread as a feature checklist.** The lead's eight "proof tests" (T3:1307-1315) list system features. He meant the idea: "does a unit actually make sense? [...] A bot wasn't self-optimizing, it was relying on multiple things. A unit, it is self-optimizing, it's relying on very few things" (T3:1332, CHECKED). Section 3 answers that.

12. **The risk hand-off file is stale and still the named entry point.** The pack found 14 stale points in `HANDOFF-RISK-SIZING.md` (pack §5, CHECKED); he said "not a fresh handoff, collect what I said" (T2:1208, CHECKED). So the pack is the hand-off. The old file should carry one line at the top saying so, and nothing else.

13. **His own open loop.** "Market and gaps, I'll rewrite my own pace and give you a response if need be" (D27, CHECKED). Never came. It is not needed for the first unit; note it so nobody waits on it.

14. **The replay study and the sign-in.** `research/29-study/` is built and did not run because the Claude Code login had expired (T3:811, CHECKED). It is a nice-to-have for the agent-check design; one `/login` from him when convenient. Not a blocker.

What was **not** missed, so it stops being re-raised: the real-money key question (dropped by his word, STATE:45); his country (he has the accounts); the data terms (own backtests only, recordings are the history); System 1 and System 2 as names (settled as explanation names); the 1m/5m question (one correlated idea, T2:1000); "agents never touch money" (moot by design, his Q6 answer).

---

## 3. Does the unit make sense, and how do we find out

### 3.1 What he means by a unit, in his words

Born 8 Oct as "each bot gets its own risk management and position sizing system that configures, reconfigures and recalibrates itself" (T1:1220, the lead quoting the 8 Oct transcript, CHECKED). 20 Oct: "can't I get one singular bot that can self-configure? [...] the bot has a specific risk management position sizing based off how it trades" (T1:376, CHECKED). 24 Oct: "a unit literally is now just a trading bot [...] it's just that we combined" (T1:1211, CHECKED). 30 Oct: "Unit is literally a replacement of a trading bot. It's just a self-configuring trading bot. Simple as that." (T2:788, CHECKED). 31 Oct: "A bot wasn't self-optimizing, it was relying on multiple things. A unit, it is self-optimizing, it's relying on very few things" (T3:1332, CHECKED).

So the unit has two claims: **completeness** (it owns entry, exits, sizing, condition needs, journal; outside it only the account-wide stops, the MIS, the feed and his click) and **self-tuning** (its numbers move from its own record, inside limits he sets).

### 3.2 Judgement

**Completeness holds, and it is not exotic.** Research 35 found every platform and trading book splits a strategy into the same parts and differs only on who owns the exit and the size (STATE:249, CHECKED). Jesse and freqtrade give the strategy its exits; the MT5 Wizard ships signal, trailing and money modules as one EA (research 04 via STATE:228, CHECKED). QMX's own code is the odd one: "the bot may not size" (`qml/src/qml/protocol/intents.py:4-5`, CHECKED), the exits belong to the Book, and conditions may not be declared (`confluence.py:51-61`, DEC-0175, CHECKED). The unit reverses three code rules that were written for the April design. That is a reversal of QMX's premise, not of trading practice. It holds.

**"Relies on very few things" holds for trading, with one honest list.** To trade, a unit needs: a price feed, the instrument's facts (lot step, tick value, hours), its budget share, and his admission. Not the MIS, not the Library, not the PC link, not the router (standing order 10). The account-wide stops stay outside and only stop, never resize. That is few. It is the same list a human scalper needs.

**Self-tuning is where the idea is weak, and the weakness is precise.** Research 20 found "self-configuring" means three things in shipped systems: (1) recompute a trade's size from the balance by a fixed rule; (2) update the rule's inputs from finished trades; (3) change the trading rules themselves. MT5, freqtrade and Jesse do (1) and (2); "nobody changes policy without a human" (STATE:247, CHECKED). His own rulings already confine the unit to (1) and (2): only he promotes; a moved number inside its range is a journal row, a changed rule is a new version by his click (research 43 §3.1 identity table, CHECKED). So:
- If "self-optimizing" means (1) and (2), the unit holds, and it is a small addition: QML's parameter space already carries bounds, step, a default and a `ui-editable` flag per number (`qml/src/qml/declaration/parameters.py:1-8`, CHECKED). What is missing is one field per number: its **motion rule** (what statistic drives it, how often, within which bounds, who approves). The MQL5 census found "the dictionary has no field for how a number changes over time" (STATE:251, CHECKED). One field, one compiler change, one journal row kind. Research 43 §3.2 already names it ("Every number carries [...] its motion [...] its authority", CHECKED).
- If it means (3), it does not hold in practice: every rule change is a new try, needs its own proof, and the search overfits (research 11: gains decay after about 15 refinement rounds, STATE:235). He does not mean (3); he said agents propose and he promotes. Say it once so no builder tries to make the rules rewrite themselves.

**Three more honest weaknesses, INFERRED unless cited.**
1. **Trade count.** A scalper on one market gives roughly 5 to 30 trades a day. Telling a +0.1R edge from zero needs about 270 trades to pass half the time and about 620 to pass four times in five (research 24 via STATE:269, CHECKED). So a unit retunes its edge-dependent numbers weekly or monthly, never within a session. Volatility-scaled numbers (a stop in ATR units, less risk in high volatility) move every bar because they read price, not the journal, and research 35 calls exactly those "safe to auto-tune" (STATE:249). The unit's "self-tuning" is therefore two speeds: price-driven numbers fast, record-driven numbers slow. Nobody has written that split down; the unit file must.
2. **The placeholder trap.** He ruled placeholders for sizing and exits (T3:1274, CHECKED). A unit cannot show self-tuning through a placeholder that never moves. The prototype must move one real number by one real motion rule from the journal, even if the sizing formula is a stand-in (a fixed fraction whose fraction tightens after a losing streak is enough to prove the mechanism). The risk session then replaces the formula, not the mechanism.
3. **Breadth is not independence, and picking the best market is luck.** Research 16 and 24 (STATE:240, 269). He waved this off ("I'm not that desperate", T2:219). It is arithmetic, not desperation. The fix is one rule fixed before results are read (judge every market by the same test, pull thin records toward the whole). It is one line in the judge, not machinery, and it should be in the first build.

**On "a unit is one JSON document".** He: "my analogy made sense, but it's an analogy. It's not what it's meant to be like" (T3:1080, CHECKED). Agreed, and 43 did not take it literally: its recommendation is "declared skeleton, coded blocks", named slots filled by tested code blocks compiled once into the existing factory (`43:155-157`, CHECKED). The data-first option (a JSON graph interpreted per quote) was rejected there for speed and expressiveness. That is the right call. The document is the unit's **declaration**; the blocks are code; the compiler is QML. QMX's workflow engine already runs an if-else rule as data (its `rule` node, STATE:253), which shows the pattern is at home in this codebase.

**Verdict.** The unit holds as "one complete algorithm whose numbers move inside tested ranges by declared rules from its own record, and whose rules change only as a new version by his click." It does not hold as "a bot that rewrites itself". The distance between today's code and the first is small: fields on the unit kind, a compiler into the existing factory, the conformance gate extended, "the bot may not size" lifted for units, a runner that trades, a journal kind. None of it is designed by thinking harder. It is shown by running it.

### 3.3 How to find out: the prototype, with pass marks in plain words

Not "proof tests". The question is "does the unit idea survive contact with the code we have". One builder, one to two days, throwaway, on `build/unit-system` in `proto/`. It passes when all of these are true, each shown by a command and its output, not by a report:

1. **A unit can be written down.** One document names its slots (market need, level, trigger, confirmation, entry, exit set, sizer) and binds each to an existing block with numbers that carry a range. The Library's unit kind gets those fields (`unit.schema.json` `fields.properties` is `{}` today, CHECKED).
2. **QML compiles it without changing the host seam.** The document becomes the `factory(declaration, assignment, read surfaces) -> callback` QML already runs (`factory.py:1-6`, CHECKED). The only code-law changes: conditions allowed inside declared blocks, and `requested_r` accepted for a unit (`intents.py:4-5`).
3. **QMB trades it.** A runner that is not `silent` (`backtest_door.py:60` on build/wu4, CHECKED) takes the compiled unit and one month of EURUSD 1-minute data and produces trades with money and R. This has never happened for an agent-built strategy. Data: his old Dukascopy ticks are on disk with checksums (research 52 §9.1 Data row); research 22 found no Library partition on the PC, so the prototype author must build one partition or wait for PR 214 (LF4, brings his old data in) to land. INFERRED which is quicker.
4. **It trades alone.** The prototype imports nothing from the MIS, the router, the Library's live store or the PC link. A grep of its imports is the test.
5. **One number moves by its own rule.** After the run, the prototype re-reads the journal and moves one declared number (a logic number such as a lookback, and the placeholder risk fraction) by its declared motion rule, stays inside its range, and writes a calibration row that says what moved, from which rows, by which rule. Run it again; the second run differs in the expected way.
6. **A script says pass or fail.** The conformance gate, extended to the document, rejects a unit with a condition field outside the schema, a number outside its range, or a missing exit, with a typed refusal and no agent in the loop. Three broken documents, three refusals.
7. **A cheap model can write one.** A Haiku agent, given the schema, three good examples and the checker, produces a passing document within a handful of tries (he said tests run on Haiku through the plan login). This is the "can agents build units" question he asked (T3:1280). It needs his `/login`.

If 1 to 6 pass, the unit holds and the Level 1 files describe what works. If 2 or 3 fail, the architecture would have been wrong and we learn it for two days' work. If 5 fails, "self-tuning" needs the risk session before anything else. Nothing here is a study; research is done.

**Then, in the build, the live proof:** the first unit on the cTrader demo from his PC (the PC sign-in merged today, PR 211, CHECKED), a feed keeper, a demo order path, the journal he opens and understands. That is a packet, not a prototype.

---

## 4. How the lead should work from here

- **Stop widening.** Seven expansion rounds produced about 800 ideas and 339 questions; the convergence used perhaps twenty (research 52 §1.2). No more party mode, brainstorming or CIS as agent rounds. Research only when a packet needs a fact (the platform languages; the clock service), and then by the agent writing that packet, not a separate research wave.
- **Layer, as he asked.** "Let's first look at the high level architecture. So that will list the biggest things [...] then each part gets its own [pass]" (T3:1081, CHECKED). Level 0 is the parent spine; each Level 1 file inherits it. The connection points get their own file. He wanted the areas kept apart: "don't combine the MIS work with the QML work and the unit work" (T3:1080).
- **Prove before folding.** The prototype runs beside Level 0, not after Level 1. His word: "we need to first make sure that what we think can work in theory can actually be pulled off in practice" (T3:1080). The lead's new program put proof last (`STATE.md:62`); that order is wrong.
- **Few agents, grouped.** Level 0: one agent. Prototype: one builder. Level 1: three agents holding related parts (section 1). Review: one. Fix: the three authors. About eight agents over six days, against 13 in one afternoon on 30 Oct (research 52 §1.1). His rule: "If more than two things can be handled by one agent, do so" (T3:737, CHECKED). One line to him before each launch: "starting X to do Y".
- **Packets, not one file.** "one file specifically compiling everything we have on QML, then one file [...] for agents addition, then another file perhaps compiling the MIS" (T3:1080). Research 43 stays as the source; each Level 1 file lifts its area from it and strips every decision he has answered.
- **Calls, not decisions.** "you can either call BS or make a better call because you are more knowledgeable" (T2:135, CHECKED). Every technical call goes in one line in a veto ledger (`architecture/VETO-LEDGER.md`); he scans it, "veto" is the only action. Only money, values and the words on his screen come to him as questions, and only the six in section 5 now.
- **Words.** The lead's coined nouns (specialist, terrain, envelope, telescope, finder, two-speed, brain and arm, claim card, death certificate, conveyor) stay out of anything he reads. His words: unit, MIS, journal, trading node, server, market context, placeholders. Everything to him through `bro` and `unslop`.
- **Show grounding, do not file it.** Level 0 is the "what exists" page he keeps asking for ("First, get a grounding. What has been built so far? What exists?", T3:1081). One page per part: built, stacked, missing, never run, with paths. After that, "you didn't ground" stops.
- **The lead's own context.** Agents read; the lead reads their files before relaying (it relayed 43 after reading only §6). `STATE.md` stays the index; it does not grow a new 40-line round section each morning. Each area's file holds its own detail.
- **Merge discipline.** The stack is his click. The lead verifies each merged head with `git ls-remote` and `gh pr view`, and says plainly how many remain. Today the plain fact is: 27.

---

## 5. The few things only he can decide, each with my answer

Kept to what changes the route. Not re-asked: anything in `STATE.md` "Operator round 2026-10-31 morning" or his six answers.

1. **Land the 27 open PRs now, or build the unit on top of the stack tip and land later?** My answer: **land now**, in chain order from 208, with 204 rebased last. Reason: nothing in the stack has run on his real folder; the prototype needs LF4 (his old data in, PR 214) and the PC's cTrader sign-in (211, merged today); building on an unlanded stack means every packet rebases twice. Cost: an hour of his clicks and the lead's checks. He said he thought they were merged; two were, this morning.

2. **Are the seven pass marks in 3.3 what "the unit works" means for now?** My answer: **yes**, edited by him in his words if he likes. This is the definition he said was missing ("I feel like you haven't defined the tests yet properly", T3:1280). Without it the prototype has no finish line and the lead will list features again.

3. **What does his click admit?** (research 43 decision 2, still his per STATE:56.) My answer: **a unit together with the markets he ticks and one broker account**; inside that list the unit trades wherever its own conditions hold, with or without the MIS; a market outside the list comes to him as a card, never trades. This is the one place "only he promotes" meets "the unit stands alone", and it fixes the shape of the admission packet.

4. **What may self-tuning touch?** My answer: **numbers inside their declared ranges, by declared motion rules, from the unit's own journal or from price; never the blocks, branches or exits, which change only as a new version by his click.** He has said the halves separately; saying it once as one sentence is what lets the prototype and every builder know what "self-configuring" means in code. It also closes the risk session's "expects back" item 1 at the mechanism level (the formulas stay theirs).

5. **When does the risk-and-sizing session start?** My answer: **when the Level 1 files are done, in parallel with the build**, from the pack, with the prototype's journal and calibration rows as its first exhibit. Not before: it would design a socket for a unit that does not yet run. Not after the first demo: he should not watch a placeholder trade for long.

6. **Park "what System 2 is" until the first unit has a journal?** He said on 31 Oct "I'll first sit down and I see what I can say about it" (T3:1080). My answer: **park it, explicitly**, with research 43's two readings (a market's own settings; a market's own version) written on the unit file as "both supported, neither built first". It changes nothing in the first build, and parking it stops it being re-asked, which he hates.

Not his, and the lead should stop asking: which language each venue speaks (the connections pass finds out); WSL now versus a Windows trading role later (answered: Linux node, WSL fallback, T3:1283); the clock design; the journal keys; the dictionary rebuild method (the lead proposes a page; he reads it); the words "market settings" and "market version" (lead's working words until he gives his own).

---

## 6. The skills at hand, which to stack, and whether the workflow fits

### 6.1 What exists

216 `SKILL.md` files across the four roots, after removing links that point at the same file (`~/.claude/skills` 104, `~/.agents/skills` 16 not already linked, the project's `.claude/skills` 69 BMad skills, and 27 in plugin marketplaces; script run 31 Oct, CHECKED). Grouped by what they are for:

| Group | Skills | Use here |
| --- | --- | --- |
| **Design and planning** | `wayfinder`, `grilling`, `grill-me`, `domain-modeling`, `codebase-design`, `architect`, `arena`, `bmad-architecture`, `bmad-spec`, `bmad-prd`, `bmad-product-brief`, `bmad-forge-idea`, `bmad-party-mode`, `bmad-brainstorming`, `bmad-cis-*` (problem solving, design thinking, innovation, storytelling), `bmad-advanced-elicitation`, `improve-codebase-architecture` (he must run it himself), `figure-it-out`, `prototype`, `how`, `why`, `blast-radius`, the `principle-*` set | the core of the next steps; see 6.2 |
| **Review** | `bmad-review` (lenses: adversarial, edge-case, verification-gap, structure, prose), `bmad-code-review`, `code-review`, `interrogate`, `false-green-tests`, `correct`, `no-comments` | one review round; `bmad-code-review` in the build |
| **Build and verify** | `poteto-mode` (and `check-plan.mjs`, autopilot-stack), `tdd`, `agentic-tdd`, `implement`, `bmad-build` (banned by `CLAUDE.md`), `run`, the web-app verifiers (`reticle`, `install-and-verify`, `verify-ui-change`, `audit-my-app`, `drive-desktop-app`) | `poteto-mode` for the plan and prompts; `tdd` in packets; verifiers only when the UI session comes |
| **Research** | `research`, `bmad-deep-recon`, `watch`, `strats-video-populate` | only inside a packet that needs a fact |
| **Words and pages** | `bro`, `unslop`, `technical-writing`, `writing-for-agents`, `documentation-factory`, `anatomy`, `playground`, `project-artifact`, `wait-what` | `bro` and `unslop` on everything he reads; `anatomy` for one Level 0 picture at most; `documentation-factory` for the docs pass after the build |
| **Operations and lanes** | `swarm`, `to-tickets`, `to-spec`, `queue-publish`, `to-kanban`, `sssf`, `morning-brief`, `ship-check`, `wizard`, `handoff`, `recall`, `reflect`, `show-me-your-work` | `show-me-your-work` for the build run's trail; the factory lanes are retired (`CLAUDE.md` and memory); `wizard` later for the trading-server setup |
| **Not for this work** | shadcn, frontend, typescript, math, plugin-dev, MCP server dev, M5 devices, receipts, session-report, claude-md tools, security scan | none |

Two facts that shape the choice (CHECKED): `~/.agents/pstack-models.md` says "arena and swarm are not used by default" and sets `architect runners: opus, fable`; `CLAUDE.md` bans `bmad-build` and the factory lanes for this project and says the orchestrator-session model is how QMA v2 ships.

### 6.2 Which to use, stacked, in order

| Step | Stack | Why this and not more |
| --- | --- | --- |
| Level 0 | `codebase-design` → `domain-modeling` → `bmad-architecture` (headless, parent spine, `lint_spine.py` 0) | seams and words first, then a small spine that fixes only what two builders could choose incompatibly (the skill's own test, CHECKED in its SKILL.md). No party mode: the parts are known; the fog is in the centre, which the prototype clears. |
| Prototype | `prototype` (logic branch) + `principle-prove-it-works` + `principle-foundational-thinking` | a throwaway that answers a question is what the skill is for; `tdd` only if the builder wants the red-green loop on the checker |
| Level 1, per part | `bmad-architecture` headless inheriting the parent spine → `codebase-design` → `principle-exhaust-the-design-space` on the two real forks → `blast-radius` on the shipped files touched | per-part child spines are the layering he asked for and the skill supports it; two shapes compared in the file replaces a party agent; blast-radius proves "it won't break QMB and the node" by running code, which is the technical depth he wants ("as if building a Bloomberg terminal", T2:1148) |
| Review | `bmad-review` lenses edge-case + adversarial + verification-gap, one agent | the "everything that can go wrong" pass from the playbook, once, over the money-adjacent parts |
| Plan and prompt | `poteto-mode` `check-plan.mjs` → coordinator prompt per `CLAUDE.md` and the playbook §6 → builder template with "Read the poteto-mode skill's SKILL.md in full [...] Do not spawn sub-agents" | the 0-problem plan and the orchestrator prompt are the destination; `poteto-agent` exists (`~/.claude/agents/poteto-agent.md`, CHECKED) |
| Build run | `show-me-your-work` (decision trail), `bmad-code-review` per PR, `tdd` in packets, light verification | per the playbook and his light-verification rule |
| Always | `bro`, `unslop` | his register |
| `wayfinder` | re-chart **once**, small: destination = "the orchestrator prompt and its packets", at most ten tickets, the 21 grilling tickets become veto-ledger lines, closed tickets keep their links | he asked for it twice ("I told you to use the wayfinder skill", T3:1091) and it is the only index of decisions so far; but its current destination is wrong and its grilling tickets are the questions he refuses to be asked. Charting is half a day for one agent; do not let it drive. |

**Drop for now:** `bmad-party-mode`, `bmad-brainstorming`, `bmad-cis-*`, `bmad-forge-idea` as agent rounds (expansion is done; party mode is built for a live room and only runs non-interactive as an exception, CHECKED `bmad-party-mode/SKILL.md:45`); `arena` and `swarm` (not default per pstack; the forks here are two shapes, not N candidates); `architect` (its arena phase doubles the cost and the Level 1 pass does its sketch step); `bmad-spec` and `bmad-prd` (a PRD is not required here: `CLAUDE.md` lets architecture run on the existing corpus, and `STATE.md` plus Level 0 is that corpus; a spec folder would be a layer on top of a simple thing); `grilling` on him (he will not be grilled; the lead grills itself in his shoes and logs the calls); `research` as a wave.

### 6.3 Does the planning workflow fit?

The "planning workflow that worked" (memory file, read in full, CHECKED) has twelve steps and a cut-down version of seven. The unit run followed the big one (`STATE.md` "The planning run"): grounding, alignment, two expansion rounds plus five more, a wayfinder chart, research in two waves, a convergence, a review, a fix round. He judged the result shallow in the technical lens and mixed across areas (T3:1080).

**Verdict: the big version does not fit this work and the medium version is close but misses two things he asked for.**

- The big version was built for a greenfield design (the QMA v2 workflow system, 58 PRs from nothing). Its generative steps (6 and 7) are sized for discovering a shape. Here the shape of nine of ten parts is already in 300,000 lines of code; only the centre (the unit as data) is new. The funnel produced about 800 ideas for one new thing. That is the over-production he felt.
- The medium version (inventory, primary sources, alignment, wayfinder, architecture, edge-case review, PR plan) fits the size. It lacks **layering** (one spine, then one pass per part with the connections designed on their own) and **proof in code before the fold**. Both are his 31 Oct asks (T3:1080-1081).
- Both versions put research as a wave before design. Here the research is done (45 files). What remains are packet-level facts.

**Replace it with this layered version, and keep the playbook's rules (one agent per deliverable, briefs carry the settled facts, verify before relaying, 0-problem plan, never merge unasked):**

1. Inventory: done (research 18, 42, 52 §9). Refresh only the stack state.
2. Level 0 parent spine, with the connection contracts, from the inventory.
3. Prototype the centre, in parallel with 2.
4. Level 1 child spines, one file per part, grouped into three agents.
5. One review (edge-case, adversarial, verification-gap), one fix round.
6. Re-centralise: veto ledger, rulings page, `STATE.md` index, wayfinder re-chart.
7. PR plan to 0 problems, orchestrator prompt, builder template, build store.

"Scale it, never skip it" still holds: every step of the old workflow is present, sized to one new centre and nine existing parts. What is removed is repetition: no second alignment, no funnel, no second convergence, no second independent review.

---

## 7. Who was right where it changes the route (short)

Research 52 §5 has the long table. Only what moves the next step:

- **He is right** that the areas were mixed, that one plan file is the wrong shape, that journals need depth, that the gold mine is a key seed, that the end goal is an orchestrator prompt, and that proof in practice comes first.
- **He is wrong** that no PRs are open (27 are), that connections for Hyperliquid and crypto are "already set up" (Hyperliquid has 0 lines at engine/base, `git grep -i -l hyperliquid` = 0, CHECKED; CCXT is a read adapter), and that nothing was proposed for the dictionary (43 §3.2 is a proposal; it was never shown).
- **The lead is right** on the technical centre (43's six foundations match the code gaps) and on "declared skeleton, coded blocks". **The lead is wrong** on order (proof after architecture), on shape (one file), on register (coined nouns, nine decisions), and on telling him what exists (the conformance gate; mini apps; the dictionary proposal).
- **Research 52 is right** on nearly everything and goes one step too far on "stop researching" only in tone: two facts remain to look up (venue languages; the clock service), inside the packets that need them.

---

## Appendix: evidence index

Transcript positions (all CHECKED by reading the files):

| Moment | Where |
| --- | --- |
| end goal: a poteto-mode orchestrator prompt | T2:24, 2026-10-29T16:01 |
| "it seems to me as if you're not considering [the artifacts]"; the planning-lead prompt pasted | T2:55-56, 2026-10-29T16:09 |
| "you can either call BS or make a better call"; "system two is the end goal"; the socket as "male and female connector"; QMB "runs and waits" | T2:135, 2026-10-29T16:41 |
| "I'm not that desperate"; exits to the risk session first raised | T2:219, 2026-10-29T17:25 |
| branches `plan/unit-system` and `build/unit-system` | T2:442, 2026-10-30T04:43 |
| "be efficient [...] If more than two things can be handled by one agent, do so" | T3:737, 2026-10-30T11:01 |
| the if-else question; "a self-configuring trading bot. Simple as that" | T2:788, 2026-10-30T06:11 |
| "no rush [...] 3 to 4 days"; "sloppiness won't be tolerated" | T2:845, 2026-10-30T06:14 |
| exits, stops, targets to the risk session; 1m and 5m is correlation | T2:1000, 2026-10-30T06:42 |
| node first on the PC; templates; "QMA agentic stuff is already done"; Bloomberg-terminal depth | T2:1148, 2026-10-30T07:31 |
| "not a fresh handoff"; "you take the wheel" | T2:1208, 2026-10-30T07:35 |
| the long 31 Oct correction: layer the architecture, test the unit in practice, determinism, languages, Windows, journals, clocks, DevOps, mini apps, "one file" | T3:1080-1081, 2026-10-31T04:05 |
| "I told you to use the wayfinder skill"; "firing in so many directions" | T3:1091, 2026-10-31T04:08 |
| the Fable read requested; "we have already almost everything we need" | T3:1128, 2026-10-31T04:13 |
| the six answers: placeholders, placeholder unit, Linux node with WSL fallback, April rules scrapped, a server is a server, mini apps, the trimmed rulings | T3:1273-1292, 2026-10-31T04:51-05:03 |
| "does a unit actually make sense"; "the PRs are merged. I don't think I have any unmerged PRs"; this file requested | T3:1332, 2026-10-31T05:09 |
| the journal as "anything that can record data"; the router never switches; "Market and gaps, I'll rewrite my own pace" | D27, 2026-10-27T03:03 |
| unit born as self-configuring; the MIS as load balancer | T1:376, 2026-10-20T12:20 |
| "a unit literally is now just a trading bot"; deep modules; QML as the library for units | T1:1211, 2026-10-24T17:43 |
| the 8 Oct birth quoted by the lead | T1:1220, 2026-10-24T17:44 |

Code and files (CHECKED with the commands shown, 31 Oct):

- `gh pr list --state open --json number,headRefName,baseRefName`: 204, 208, 209, 210, 212-234 open; draft 25. `gh pr list --state merged`: 200-203, 205, 206 (26 Oct), 207 and 211 (31 Oct).
- `git log -1 origin/engine/base` = cee216e0 2026-10-31 "Merge pull request #211"; `origin/build/sy5` = 074670ac 2026-10-29; `origin/main` = c3e8ec5e 2026-09-27.
- `qmx-agents/packages/qmx-library/src/qmx_library/kinds/unit.schema.json`: `"fields": {"type": "object", "properties": {}}`; page tabs Logic, Results, Family tree, Markets, Versions.
- `qml/src/qml/protocol/intents.py:1-8`: "the bot may not size"; `qml/src/qml/declaration/confluence.py:51-61`: `FORBIDDEN_CONDITION_FIELDS`, DEC-0175; `qml/src/qml/conformance/__init__.py:1-6`: the pure conformance gate; `qml/src/qml/protocol/factory.py:1-6`: the factory seam; `qml/src/qml/declaration/parameters.py:1-8`: bounds, step, default, `ui-editable` per variable.
- `origin/build/wu4:qmb/src/qmb/host/backtest_door.py:60`: `RUNNERS = frozenset({"silent"})`.
- `packages/qmf-risk/src/qmf/risk/sizing.py:1-34`: the sizing ladder "defined-unwired", DEC-0158; `qmn/src/qmn/capital/{kill_line,ratchet,bench_fold}.py` exist; the ratchet is a breakeven ratchet only (`ratchet.py:1-6`).
- `git grep -i -l hyperliquid origin/engine/base -- qmb qml qmn packages qmx-agents` = 0 files; `git ls-tree -r --name-only origin/engine/base | grep -i 'kinds/.*journal'` = none.
- Mini apps: `docs/decisions/ADR-0034..0036-miniapp-*.md`, `qmx_engine/templates/d9-mini-app-pipeline/`.
- `grep -c -i 'explainer\|claude.ai/artifact' research/43-convergence.md` = 0.
- Skills: `~/.claude/skills/poteto-mode/scripts/check-plan.mjs`; `~/.claude/agents/poteto-agent.md`; `~/.agents/pstack-models.md` ("arena and swarm are not used by default"; `architect runners: opus, fable`); `bmad-architecture/SKILL.md` ("Inheriting a parent spine"); `bmad-party-mode/SKILL.md:45` (`--non-interactive` as the only non-live path); the inventory script output (216 files).
- Stats on disk: `C:/Users/Mubarak/Desktop/Stats/schema/{strategy-dna.md, graph.yaml.md, ids.md, strats.sql}`.

Research relied on where I did not re-run the check (their own CHECKED labels, via `STATE.md` rows): 04 (platform contract shape), 11 (refinement decay), 16 and 24 (pooled vs per-cell; the picking simulation), 20 (three meanings of self-configuring), 22 (no Library partition on the PC), 31 (WSL present; network-bound timing), 35 (strategy anatomy; safe auto-tuning), 36 (no motion field), 38 (venues), 42 (nothing has run on his folder), 52 (the whole-run read).
