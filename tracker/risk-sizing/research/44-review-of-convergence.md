# 44: Independent review of the convergence (research 43)

Written 2026-10-30 by the review agent, before the operator reads 43. Review only: nothing here is a design, and 43 is not edited.

## How this was made

- **Method.** `bmad-review` (`.claude/skills/bmad-review/SKILL.md`), three lenses run in sequence by one agent: adversarial (`references/lens-adversarial.md`), verification-gap (`references/lens-verification-gap.md`), edge-case (`references/lens-edge-case-hunter.md`). Each finding uses the skill's shape (location, trigger condition, guard or fix, consequence) plus `kind`. No severity or ranking, per the skill.
- **Read in full.** 43; `STATE.md`; `STANDING-ORDERS.md`; the skill and its three lens files; every operator turn in `operator/transcript-2026-10-29-to-30.md` (T2) except pasted agent reports; research 42; `RISK-SIZING-PACK.md` §1, §2.4, §2.9, §2.10, §2.11, §3.4, §3.9, §4; rulings 135 to 142 (`tracker/qma-v2/research/methodology/26-operator-rulings-and-alignment.md:244-274`).
- **Read in part (where 43 leans on them).** `operator/transcript-2026-10-20-to-28.md` (T1): every turn 43 quotes, read in context, plus searches of all his turns for QMB, LEAN, Jesse, Python, news, workhorses and leverage. The 28 Oct dictation (every "system two" passage). Research 35 §0, §2, §3.1, §4, §6, §7. Research 41 §1.5, §2.1, the summary table. Research 39 K1 and FG 831. Research 36 §0. Research 14 §9.3. Research 05 short answer 2 and research 15/16 on the 8-hour bound. The operator-question tables of `qml-field.md`, `mis-field.md`, `live-field.md`. `wayfinder/MAP.md` and four grilling tickets. Research 17 to 21, 34, 39 to 40 beyond that were not read in full; findings below do not rest on them.
- **Quote check.** A script extracted every double-quoted string in 43 and searched all transcripts and operator files for it. Every quote 43 attributes to him exists verbatim. Line numbers below are `grep -n` lines on the current files (a first Python pass counted stray carriage returns as lines and ran one high after T2:219; `grep -n` agrees with 43, so 43's line numbers are right except where noted).
- **Code check.** Read with `git show` at `origin/build/sy5` (`074670ac`, the stack tip) in `C:/Users/Mubarak/Desktop/QMX`. No checkout, no fetch.
- **Labels.** CHECKED = read at the cited path, line or command this session. INFERRED = my reasoning.

---

## Lens 1. Adversarial

**A01.** kind: misquote
- location: §3.2 "Every number", 43:185 ("His answer to 'what tunes' is the frame: 'It's numbers.' (`T2:788`)").
- trigger_condition: "It's numbers" is him reading back the lead's own option, then rejecting it as incomplete.
- guard_snippet: The lead's question 1 part 2 at T2:726-729 reads "The part that tunes itself: its numbers, inside those ranges" (CHECKED). At T2:788 he says "The part that tunes itself actually is part two, under question number one. It's numbers. [...] I think we need to actually define what is meant to be tuning itself [...] how do we make sure that those if-else statements can self-tune? Maybe that's the question at hand" (CHECKED). Quote his question, not the echo, and answer it in plain words: the numbers inside the rules move by themselves within declared ranges; the rules themselves (which blocks, which branches) change only as a counted new version or unit that he approves, which is what every shipped platform does (research 35 §4.1-4.2; research 20 via STATE).
- potential_consequence: He reads his own open question presented back as his answer.

**A02.** kind: misread-ruling
- location: §3.1 "What he called System 2 becomes 'a market's own settings'" (43:147); decision 4; decision 9 ("market settings" for System 2).
- trigger_condition: His System 2 includes changing the logic per market, and he called it QMX's end goal.
- guard_snippet: 28 Oct: "system two before live can work if we are changing or enhancing different logics for different markets" (`operator/2026-10-28-router-system1-system2.md:7`, CHECKED). 29 Oct: "what system two does is [...] making rather that unit more specific [...] we are trying to do that sniping thing [...] It's as if system two is the end goal of QMX" (T2:135, CHECKED). 43 keeps only the settings half under his name and moves "rules changed for one market" to "a new unit in the family". Say plainly that his System 2 is split into two things (a market's own settings, earned from its record; rules changed for a market, a new unit in the family), cite both lines, and let decision 9 name both, not rename System 2 to "market settings".
- potential_consequence: What he called the end goal of QMX is renamed into a tuning detail.

**A03.** kind: re-asks-settled
- location: §6 decision 2 (the 239 entries); §3.2 "It is still decision 2".
- trigger_condition: His own words already pick the recommended option, and he already said whose design it was.
- guard_snippet: Binding correction 3: "The dictionary was GPT's idea: a good start, not sacred" (`STATE.md:22`, CHECKED). "the dictionary was GPT's idea, not mine" (T1:1211). "the dictionary needs a rebuild, an entire thing, like a whole bloody, because the ideas are there" (T2:219). "the hammer's not mine. Those things were not mine, they were from GPT" (T2:219). "this is mostly the handiwork of a GPT model" (T2:1000). Research 41 §2.1: "permanent" meant library content, reviewed first if doubted, never left as scratch; the summary table calls it "Resolved by him" (`41:158`, `:245`, CHECKED). Keep every idea and rebuild the form is what these say together. Report it in one line as settled; drop "only you can say which August choices were your intent".
- potential_consequence: He is asked again a question he has answered four times.

**A04.** kind: misread-ruling
- location: §8 Parked, "Funding modelling for perps beyond the instrument record | His 'a bit out of scope for now'" (43:561).
- trigger_condition: His "funding" there means the money part of a unit, not perps funding rates.
- guard_snippet: T2:219: "things like trading hours, finding, I already told you, is a bit out of scope for now". The "already told you" is T2:135: "Maybe the thing I may have a lot of control on is just the funding. In other words, the money part of a unit, the risk management and position sizing system" (both CHECKED). Unpark perps funding as a cost QMB charges on replay and the instrument record carries (Hyperliquid funds hourly, STATE research 02 row); hand "funding = the money part" to the risk session, where the pack already files it (pack §2.9).
- potential_consequence: Perps backtests ignore funding, so the second door's results come out too good.

**A05.** kind: misquote
- location: §3.4 "Forge changed" (43:219) and §4 L08-12 ("'It runs and waits' is enforced by the rerun rule").
- trigger_condition: He meant QMB is a tool an agent calls and waits on, like a test suite.
- guard_snippet: T2:135: "All I want is something that an agent can call as a tool. It runs the same way you run your tests. [...] So it means it runs and waits. It doesn't have to tinker with the results. It gets those results" (CHECKED; the line is 135, not 132). Cite it for the tool shape (one call, wait, one typed result), which PR 204's door already gives. The rerun rule can stay as a lead call on its own reason.
- potential_consequence: His words are bent to back a rule he did not state.

**A06.** kind: missing-source
- location: Read me item 7 (43:25); §3.4 options table (43:211-215).
- trigger_condition: His QMB seed is "combine LEAN CLI, Jesse and StrategyQuant; toss or rebuild". 43 offers LEAN and Jesse only as a swap.
- guard_snippet: T2:135: "we are combining Quant Connect Lean CLI, the JSE framework, and then I think I added strategy quant with that thing of what if scenarios. [...] Now we either toss or we rebuild QMB based off this. [...] I really, really don't think it's remaining the same" (CHECKED); STATE 27 Oct "Base: QuantConnect LEAN CLI logic; also consider Jesse". Research 14 §9.3 already lists what QMB borrows (one verb per job, live results over the backtest, Jesse's agent door with a significance test, optimise with a held-out period, research runners) and what not to borrow (LEAN's C# engine, Jesse's float money) (CHECKED). Reword item 7 ("the backtester is rebuilt on what LEAN, Jesse and StrategyQuant do well, keeping the parts QMX already has"), list the §9.3 rows taken, and replace the straw option.
- potential_consequence: Item 7 of the read-me says the opposite of his words.

**A07.** kind: missing-source
- location: General (no section).
- trigger_condition: His stack question is dropped without a word.
- guard_snippet: T2:55: "Even the stack discussion is very up for discussion, in other words. We might need to discuss the stack we are going to use. I don't think Python will be suitable, depending" (CHECKED). 43 assumes Python throughout ("compile the unit spec to a Python closure", plain Python units). Add it to §7 high level with what separates the options (per-quote speed for 100 markets on his PC, the Python QMF, QML, QMN and QMB already shipped), or settle it as a lead call with its reason.
- potential_consequence: A seed from his first evening vanishes.

**A08.** kind: missing-source
- location: §1 Read me; general.
- trigger_condition: His "multiple experiences" (his own user experience) has no section.
- guard_snippet: T2:858: "if me, I'm a user, how am I going to be using units, okay, to literally trade and make money [...] all this just gives us a beefier advantage compared to a person just using a simple bot" (CHECKED; STATE seeds 30 Oct). Add a short "your day with QMX" paragraph to the read-me: what he sees each morning, which cards wait for his click, what he watches live, and why that beats one bot on MT5.
- potential_consequence: The part he said justifies QMX to himself is missing.

**A09.** kind: contradiction
- location: §3.6 Failure, "Every live order carries its stop at the broker" (43:257); §4 "Full disk ... protection kept".
- trigger_condition: Stop or no stop is an unresolved risk-session conflict, and 43 itself admits no-stop units.
- guard_snippet: Pack §2.10 C7 (stop loss or not, unresolved): "a stop loss, I think it's irrelevant now. Okay? Because we have fast invalidation" (5 Oct) against "There are so many ways we can do a stop and a target distance [...] For us, let's just leave room for that" (T2:1000). Appendix C, C1: "Grid units and time-exit units have no stop". Reword: "whatever protection the unit's exit set declares is placed at the broker where the venue allows"; send "must every live order carry a broker stop?" to the risk session as a question.
- potential_consequence: The plan settles a risk-session conflict, and a no-stop unit has no broker protection in its own failure plan.

**A10.** kind: contradiction
- location: §3.1 identity table row 1 (43:141); §2 Subtract first item 2 (43:111); §3.1 "intents widened to carry size and exits".
- trigger_condition: These decide questions the pack lists as coming back from the risk session.
- guard_snippet: Pack §4 "What the planning run expects back" item 2 (unit or sizer module emits the size) and item 3 (does a moved risk number make a new version); pack §2.10 C1 and C2 (risk on the unit, the pod, or a central BMS) are unresolved (CHECKED). His "there should be some sort of centralized parts of this entire system, like the BMS, but not the BMS that we have right now" (T2:219). Exempt risk and exit numbers from the identity table ("the risk session sets how these move and what a move means"). Invert the Book premise for units, but keep the Book/BMS seam (ATC/PolicyPair, the Book admission inputs) until that session rules, instead of deleting the old path now.
- potential_consequence: The unit plan designs part of risk and may delete what a central BMS would reuse.

**A11.** kind: misread-ruling
- location: §8 grilling table, 11 rows marked "Lead"; §4 "Cross-ticket calls".
- trigger_condition: The map says grilling tickets wait for him live and are never answered for him.
- guard_snippet: `wayfinder/MAP.md:24`: "Grilling and prototype tickets wait for him, live. [...] Never answer for him"; each ticket file ends "With him, live [...] Never answer for him" (CHECKED: `what-qmx-is-for-first.md`, `units-and-the-mis.md`, `registry-and-router.md`, `domain-expansion-rule.md`). Several are `blocked_by` research that has not run (units-and-the-mis by three MIS research tickets; what-qmx-is-for-first by the small-account ticket). STATE:134: "nothing about the MIS or standing alone is set in stone before the angles are exhausted"; T2:788: "I don't want to set it in stone yet". Keep the recommendations, but list the 11 in §6 as "my answer unless you say otherwise", one plain line each, marked provisional where their research is still out.
- potential_consequence: He loses the grilling the plan promised him, on questions he reserved.

**A12.** kind: misread-ruling
- location: §6 decision 4 ("On 27 October you said yes [...] Or: keep your 27 October answer").
- trigger_condition: The framing ignores his later positions, which already moved past the 27 Oct yes.
- guard_snippet: 28 Oct: System 1 for live, System 2 before live (STATE:107-110; dictation :7). 29 Oct: Path A, a System 2 version is earned from a record (STATE:120; T2:219 "by the time that happens, there is already a history, a track, a paper trail"). 30 Oct: same pair on 1m and 5m "that's just correlation" (T2:1000). Present his newest position, show how the recommendation follows it, and drop the "keep 27 Oct" option or label it as his superseded answer.
- potential_consequence: It reads as reopening something he already revised.

**A13.** kind: over-built
- location: §3.4 Recommendation, the judge's ten stages (43:217); §3.7 judge block.
- trigger_condition: Ten stages by default conflicts with his "don't be too strict" and correction 1.
- guard_snippet: STATE:87: "Look at how professional quants judge; don't be too strict" (binding round, CHECKED); STATE:20: "No 'every part must prove itself' machinery". Name a short default chain (cost stress, walk-forward, counted tries, the try-corrected best), make the other stages opt-in steps on the judge card, and say research 26 sets the default order.
- potential_consequence: Almost no unit reaches paper, through the machinery he rejected.

**A14.** kind: contradiction
- location: §3.4 "then one locked look at a sealed window"; §4 Q24 "one sealed window per finding"; §5 "Holdout: off".
- trigger_condition: A sealed window as a standard judge stage is a default holdout, which ruling 137 forbids.
- guard_snippet: Ruling 137: "A lock that refuses by default [...] is a bug, not a safety feature. A holdout is an optional setting he chooses per study, off by default" (`26-operator-rulings-and-alignment.md:266`, CHECKED). Make the sealed-window stage off by default and switched on per study, and say so in §3.4.
- potential_consequence: The judge brings back a default lock he called a bug.

**A15.** kind: contradiction
- location: Appendix B Must ("one reference unit on the cTrader demo"; "risk socket slots with a test placeholder") against §8 risk socket row ("an empty slot runs a labelled placeholder in backtests and blocks paper and live").
- trigger_condition: The Must list's reference unit cannot reach demo under 43's own socket rule.
- guard_snippet: State that the reference unit's demo run waits for the risk session's first sizer and exit set (his T2:219: "by the time you are done shipping, before the UI, the risk and sizing will obviously be also there"), or allow a labelled placeholder on demo only and say why.
- potential_consequence: The first build cannot finish its own Must list.

**A16.** kind: under-built
- location: Appendix B Must; §3.6 Feeds and routes.
- trigger_condition: No live feed is in the first build, and nothing shipped holds a long-running cTrader connection.
- guard_snippet: Research 42 Q11: broker reads open one short TLS session per read on This PC, and the long-running ConnectionManager (WU10) waits on gate G-CT (`42:413`, `:297`, CHECKED there). Add the feed keeper and the market-journal minute writer to Must, name WU10 as the code to finish or replace, and count it in the build.
- potential_consequence: The reference unit has no live prices to trade on.

**A17.** kind: misquote
- location: §3.4 Recommendation, 43:217 ("a factory, a declaration and policy as data", CHECKED in r42 §5).
- trigger_condition: Research 42 says "Book policy"; 43 drops the word "Book".
- guard_snippet: `42:315`: "Needs a factory, a declaration and Book policy that no recorded config carries" (CHECKED). STATE QMB door section lists `BookAdmissionContext` among the missing execution inputs. Quote it exactly and add "replace the Book policy input with the unit's socket" to the runner's work.
- potential_consequence: The runner's work is undercounted by the one seam the inversion touches.

**A18.** kind: over-built
- location: §2 Subtract first item 4 ("Delete the declaration" of the `library` node kind, 43:113).
- trigger_condition: Engine clean-up unrelated to units is folded into the unit build.
- guard_snippet: The fact holds (`registry.py:94` declares `library` with `available=True`, CHECKED at TIP), but STATE correction 7: "every proposal names what it touches. Never casually remove shipped backend work". Move it to the backlog as a finding.
- potential_consequence: Scope creep in a planned run.

**A19.** kind: contradiction
- location: §3.3 "A rule input or a veto binds a reading the unit computes itself [...] nothing changes when the MIS is down" against §8 "What runs on the trading node" ("a unit uses the board while it is fresh, else its own readings", 43:542).
- trigger_condition: Two different rules for where a unit's rule input comes from.
- guard_snippet: Keep the §3.3 form and delete "uses the board while it is fresh" from §8, or explain when the board value wins.
- potential_consequence: A rule reads two sources that differ, so live and replay disagree.

**A20.** kind: unclear-to-him
- location: §5 Numbers rows marked INFERRED ("Market's own settings: 100 trades", "Shrinkage: half at 100 trades", "Paper before his card: 30 trades or 4 weeks", "Seasonal baseline 20 weeks", "Stale symbol 30 s").
- trigger_condition: Numbers he never asked for, with "INFERRED" as their only origin.
- guard_snippet: He objected to exactly this: "Where are you getting that number from?" (T2:219, on the 270-550 range) and "I don't trust the math because I never requested for it" (T2:325). For each INFERRED row give a one-sentence reason, or mark it "placeholder until research N". Also say where 43 changes a shipped default: the shipped `b` template judges at 100 trades and 1.5x costs (`TPL/b-build-and-prove/README.md:13`, `scripts/gates.py:4-6`, CHECKED), while 43's table says 200 trades and 2x.
- potential_consequence: It repeats the 270-550 incident.

**A21.** kind: unclear-to-him
- location: §4 "An agent-built unit's first judged window starts after the building model's training cutoff [...] Model memory is a look-ahead" (43:323).
- trigger_condition: He called the "model may remember past markets" point sloppy, and 43 repeats it unexplained.
- guard_snippet: T2:385: "I never said that the agents are going to be using past or their training data. No, I said they are going to be using live. [...] It's very sloppy" (CHECKED). That objection was about analyst agents on live data. Add one line: the cutoff rule applies only when a model builds a unit and it is tested on history; analysts on live data are untouched.
- potential_consequence: He reads the point he rejected, with no reason given.

**A22.** kind: misread-ruling
- location: §4 L01-14 ("Warm start from history removes DEC-0261's warm-up wait"); §3.6 and §8 ("dead man's switch").
- trigger_condition: DEC-0261 has no warm-up wait; it bans warm-up and renamed the dead man's switch.
- guard_snippet: `docs/AGENTS.md:60` at TIP: "no per-bot warm-up, probation, ramp or paper lane on the node [...] A bot promoted mid-day does not trade until the next trading day" (DEC-0261); `:64`: "The external watcher is the `liveness heartbeat`, renamed from 'dead-man's switch'" (DEC-0261) (CHECKED). Say what DEC-0261 actually imposes (next-day activation, which has no meaning in 24/7 markets) and call the venue feature "cancel on disconnect".
- potential_consequence: A ratified rule is misstated, and a renamed word comes back with another meaning.

**A23.** kind: missing-source
- location: §6 decision 1 (three options) and §3.6 Keys.
- trigger_condition: Options and operator questions from the live field are dropped or settled as lead calls.
- guard_snippet: `live-field.md` operator questions: N-02 "Does a Linux layer inside his PC count as 'first run on my machine'?" (settled by 43:251 as "lead call"), N-09 "Is a passive second node worth its monthly cost" (money), S-02 "Is a trade-only, no-withdraw key a live key?" (settled at 43:259), S-05 "Is a small live canary account on the PC acceptable to him?" (missing) (`live-field.md:272-369`, CHECKED). STATE's ruling-135 options include "a tiny live test account on the PC". Put N-02, S-05 and the second server's cost into decision 1, and say in one line which options were dropped and why.
- potential_consequence: A money decision is put to him with options hidden.

**A24.** kind: missing-source
- location: General; §8 Parked.
- trigger_condition: Seeds and operator questions from the fields dropped without saying so.
- guard_snippet: Missing from 43 (searched, none found): `qml-field` Q39 (is populating the library still a goal), Q79 (fundamentals entries; STATE:134 "fundamentals when used"), Q80 (how he hears that a unit tuned itself), Q12 (the smallest demo of a unit configuring itself; STATE:78 "This is what he needs most"; 43:551 hands that prototype to the risk session although its content is QML's numbers); `mis-field` QO04 (may his and the copilot's labels retrain the MIS; T2:219 "we can retrain a version of the MIS that can also see such"), QO09 ("the MIS a constant"); funnel round 2 Q5 (paper sequence) and Q3 (with the router off, see E12); STATE:89 "Account for the old risk system's special ('radioactive') sizing when judging"; research 42 Q3 (what of QMN's admission, seats and Book door survives). Answer each or list it in Parked with a reason.
- potential_consequence: He finds his own seeds missing and loses trust in the rest.

**A25.** kind: unclear-to-him
- location: §6 decision 8 (the April rules).
- trigger_condition: The recommendation is circular and takes a side on his faith and values.
- guard_snippet: "they no longer bind, since CFDs, perpetuals, futures and indices are now in scope" uses the conflict as its reason. §4 names them "the April Sharia rules" but decision 8 hides that. Frame it neutrally with no recommendation: "Your April rules (no leverage, swap-free, no futures) clash with the markets you added since. Which wins, or which units follow them?" and state what each answer removes.
- potential_consequence: He is advised on a values question by an agent.

**A26.** kind: over-built
- location: §3.2 dictionary, "Each entry gets three faces" plus status ladder, transfer status per class, minimum data level and fallback.
- trigger_condition: Several hand-kept statuses per entry, times classes, for 239 to 400 entries.
- guard_snippet: Compute the status ladder by script (has a spec, has code, has a golden test, used by a unit) instead of storing it; leave transfer status "not assessed" until a class pack is built. Fewer stored fields, same answers.
- potential_consequence: The dictionary becomes a large matrix nobody keeps current.

**A27.** kind: unclear-to-him
- location: §3.2 "terrain on the instrument record" (43:178); §3.1 "earning a specialist" (43:153); §8 "specialist desks" (43:546, 567).
- trigger_condition: Words he disowned or said he does not understand.
- guard_snippet: "Terrain was not mine" (T2:788) and 43's own words ticket retires it (43:530). "Specialist, what do you mean by a specialist? I don't know what you mean by that" (T2:788). Replace with "the market's facts" and "a market's own settings".
- potential_consequence: The same words that confused him come back.

---

## Lens 2. Verification gap

43 is a plan, so the "changed behaviour" is what it says the build will do and the claims it makes about shipped code. Each finding says what was checked.

**V01.** kind: under-built
- location: F5 "counted at the QMB door, not by the agent that asked for it".
- trigger_condition: A script step can read prices and score a variant without passing QMB's door.
- guard_snippet: The judge refuses any result that does not carry a door-issued run id, and the price door records reads per family so a bypass shows up.
- potential_consequence: Tries go uncounted, and luck re-enters through scripts.
- gap_shape: missing-adoption-gap
- consumer: shipped template scripts, e.g. `TPL/download-dukascopy/scripts/download.py:41`, which imports `qmx_host.market_data.MarketDoor` and opens the door itself.
- evidence: research 42 §1.3 row "Script step reads prices" (`42:104`, CHECKED there); 43 names no check that ties every scored result to the door.

**V02.** kind: under-built
- location: §3.6 Failure, "The client order id is the trade's trace id, so a retried send never doubles a position".
- trigger_condition: Safe retry assumes the venue rejects a repeated client order id.
- guard_snippet: Before any resend, read open orders and positions by that id and resend only if absent; add it to the monthly demo drill.
- potential_consequence: A retry after a lost reply can open the position twice.
- gap_shape: regression-gap
- consumer: the trading runtime's send path (§7 low level item 6).
- evidence: 43 cites no venue source for de-duplication; research 38 (venues) has not run. INFERRED.

**V03.** kind: contradiction
- location: §3.3 "Proof that the MIS helps" (dark-MIS run, shuffled-readings run).
- trigger_condition: Under 43's own design these two tests cannot fail for rule inputs.
- guard_snippet: Units compute their own rule inputs (§3.3), so cutting the MIS off changes only placement. Define the dark-MIS run as "placement from home markets only" and the shuffled run as "the unit's own readings shuffled", and say what each proves.
- potential_consequence: The proof passes by construction and proves nothing.
- gap_shape: broken-verification-gap
- consumer: the judge block (§3.7 core) and every unit's record.
- evidence: 43 §3.3 paragraphs 2 and 3, read together.

**V04.** kind: under-built
- location: F2 "library code that runs the same in QMB and live"; §4 L16-03.
- trigger_condition: No check is named that the stored reading equals what the unit computed.
- guard_snippet: A golden replay: one recorded day through QMB, the MIS and a unit, values compared per reading id and version.
- potential_consequence: Readings drift between callers and no one sees it.
- gap_shape: regression-gap
- consumer: the context receipt (F1) and every lift study.
- evidence: golden values are named only for catalogue blocks (§3.2, seams S4); none for readings.

**V05.** kind: other
- location: F4 Reuses ("the Library outbox for saves made while the PC is away", 43:82) and §3.6 ("the node's outbox syncs when the PC returns").
- trigger_condition: The shipped outbox works the other way round.
- guard_snippet: `LIB/outbox.py:1-2` at TIP: "The PC's write outbox: a save made while the Library server is away is kept, then replayed once" (CHECKED); research 18:278 says the same. Move the node outbox (`live-field.md` B032) from Reuses to new work.
- potential_consequence: The build plan counts a part as built that is not.
- gap_shape: other

**V06.** kind: other
- location: §6 decision 6 ("Your PC had about 12 GB free when last read").
- trigger_condition: A money decision rests on a stale, partial disk figure.
- guard_snippet: `Get-PSDrive` on 2026-10-30: C: 16.0 GB free, D: 57.7 GB free (CHECKED). Give both drives and say whether D: can hold the tick archive.
- potential_consequence: He may buy a disk he does not need yet, or the reverse.
- gap_shape: other

**V07.** kind: under-built
- location: §3.6 "One image, two places"; §5 "Twin run before first live".
- trigger_condition: Nothing records that the PC and the server ran the same build.
- guard_snippet: The connect self-test's passport item records the image digest, and every journal row carries its writer's version, so the twin-run diff can tell code drift from venue drift.
- potential_consequence: A rehearsal on one build proves nothing about another.
- gap_shape: missing-adoption-gap
- consumer: the twin run (`live-field.md` B018) and the passport item (§3.6 Setup).
- evidence: §3.6 lists the passport's contents; no build identity among them.

---

## Lens 3. Edge cases

Scope is the whole of 43 (a document, not a diff). Only unhandled paths are listed.

**E01.** kind: under-built
- location: F4 "Unit journal | the trading runtime for paper, demo and live".
- trigger_condition: PC demo twin and server live, or a failover server, write one unit journal.
- guard_snippet: Partition key = unit + world + machine; one lease per unit and account during a failover.
- potential_consequence: Two writers on one stream, against F4's own rule.

**E02.** kind: under-built
- location: F1 receipt and F4 "Reading history | the MIS".
- trigger_condition: The unit computed its own reading, but only the MIS writes reading history.
- guard_snippet: The unit journal keeps the compact values it computed, or a local reading stream with the unit as its one writer.
- potential_consequence: What the unit saw cannot be replayed when the MIS was down.

**E03.** kind: under-built
- location: F1 and Appendix C, C1 ("R comes from the declared invalidation").
- trigger_condition: Fast invalidation is a condition, not a price, so R is undefined.
- guard_snippet: Judge such units in money with a flag, or ask the risk session for an invalidation distance per trade.
- potential_consequence: His preferred no-stop scalpers cannot be judged in R.

**E04.** kind: under-built
- location: F6 instrument record; §3.6.
- trigger_condition: Two units trade one symbol on a netting account.
- guard_snippet: F6 or the account record stores netting or hedging; netting allows one unit per symbol, or the runtime nets per unit.
- potential_consequence: One unit's close silently closes the other's position.

**E05.** kind: under-built
- location: §3.6 "Where a venue offers a dead man's switch, silence cancels resting orders".
- trigger_condition: The venue's cancel-all also removes the protective stops 43 relies on.
- guard_snippet: Use it only where protective orders are spared, or re-place stops after it fires; add to research 38.
- potential_consequence: Positions lose protection exactly when the server is down.

**E06.** kind: under-built
- location: F6 calendar; §3.6.
- trigger_condition: A unit holds an expiring CFD future at expiry (IC never rolls them).
- guard_snippet: A declared at-expiry action on the instrument record (no entries N days before, close at T), replayed by QMB.
- potential_consequence: Forced close at an unplanned price, unmatched in backtests.

**E07.** kind: under-built
- location: §5 "Seasonal baseline: same minute of the week over the last 20 weeks".
- trigger_condition: A daylight-saving change or a new instrument with under 20 weeks.
- guard_snippet: Baseline in venue session time; a shorter history shows "thin baseline".
- potential_consequence: "Now versus usual" fires falsely for weeks after each clock change.

**E08.** kind: under-built
- location: §3.2 "a snapshot ships as QML package data"; §4 L01-14.
- trigger_condition: Library down: the instrument record and the calibrated values are not on the node.
- guard_snippet: The trading machine holds a snapshot of every instrument record its units use, refreshed on change.
- potential_consequence: Contract facts are missing, so the sizer cannot size.

**E09.** kind: under-built
- location: §4 L15-04 "A unit recalibrates on its slow clock".
- trigger_condition: The PC is off for a week; where does recalibration run?
- guard_snippet: Say it runs where the unit runs, from the local journal.
- potential_consequence: Calibration stalls whenever the laptop is shut.

**E10.** kind: under-built
- location: §3.1 Lifecycle state machine.
- trigger_condition: Who moves tested to paper, stopped back to anything, and who parks?
- guard_snippet: A transition table with the actor on every edge; unit state against per-market state when they disagree.
- potential_consequence: Unclear who may restart a stopped unit.

**E11.** kind: under-built
- location: §3.1 identity table.
- trigger_condition: A learned block is retrained, or a shared block's code is fixed.
- guard_snippet: Two rows: retrain = calibration only if declared "learned" with bounds, else a new version; a shared block fix makes a new version of every unit using it and queues their re-test.
- potential_consequence: A bug fix silently changes many live units.

**E12.** kind: contradiction
- location: Appendix C, C5 ("a stale list falls back to [home markets]") against decision 3 and STATE:64.
- trigger_condition: Finder stale: home markets only, or every ticked market?
- guard_snippet: STATE:64: "If the router is slow, down or offline, the unit keeps trading if its own conditions, the pair and the broker allow" (binding). Funnel round 2 Q3 put this exact choice to him (STATE:226). Move the fallback into decision 3 as his choice.
- potential_consequence: His question is settled in an appendix, against his binding words.

**E13.** kind: under-built
- location: §5 "Twin run before first live: 5 trading days"; "Session clocks".
- trigger_condition: A 24/7 crypto or perps unit has no trading days.
- guard_snippet: Define the twin run in calendar days or closed trades for 24/7 markets.
- potential_consequence: The rule has no meaning on the second door.

**E14.** kind: under-built
- location: §3.6 Keys ("the whole stack runs on his PC [...] in shadow, on live prices").
- trigger_condition: Shadow on live prices needs a live-account read grant on the PC.
- guard_snippet: Ruling 135 allows read-only keys on the PC (`26-operator-rulings:250`, CHECKED), but code refuses a live-capable grant there (`BRK/adapters.py:107`, via research 42). Name the read-only grant path and confirm cTrader issues one; otherwise say shadow runs on demo prices.
- potential_consequence: The shadow run silently uses demo prices.

**E15.** kind: under-built
- location: §5 "Stale symbol: 30 s without a quote".
- trigger_condition: Weekends and holidays make every FX symbol stale.
- guard_snippet: Stale counts only inside the instrument's open calendar.
- potential_consequence: Alarms flood every weekend.

---

## Count per kind

| kind | count | findings |
| --- | --- | --- |
| misquote | 3 | A01, A05, A17 |
| misread-ruling | 5 | A02, A04, A11, A12, A22 |
| re-asks-settled | 1 | A03 |
| trader-knows | 0 | none of the ten decisions is a question any trader answers (checked against research 35 §6) |
| missing-source | 5 | A06, A07, A08, A23, A24 |
| contradiction | 7 | A09, A10, A14, A15, A19, V03, E12 |
| over-built | 3 | A13, A18, A26 |
| under-built | 19 | A16, V01, V02, V04, V07, E01-E11, E13-E15 |
| unclear-to-him | 4 | A20, A21, A25, A27 |
| other | 2 | V05, V06 |

Total: 49 findings (27 adversarial, 7 verification-gap, 15 edge-case).

## Must fix before he reads it

1. **His words.** Fix the "It's numbers" misquote and answer his if-else question (A01); restore his System 2 (logic per market, "the end goal of QMX") in §3.1, decision 4 and decision 9 (A02, A12); fix the funding misread and unpark perps funding as a cost (A04); fix the "runs and waits" use and the "Book policy" quote (A05, A17).
2. **Drop decision 2**, which he has settled four times (A03).
3. **QMB**: read-me item 7 contradicts his "toss or rebuild"; engage his LEAN, Jesse and StrategyQuant seed through research 14 §9.3 (A06).
4. **Out of the risk session's lane**: "every live order carries a broker stop", risk numbers in the identity table, and deleting the Book seam now (A09, A10).
5. **The 11 grilling tickets marked "Lead"**: list them for him as answers he can overrule (A11). Put the finder-down fallback into decision 3 (E12).
6. **Ruling 137**: make the sealed-window judge stage off by default (A14). Trim the judge's default chain (A13).
7. **The Must list must reach its own reference unit**: the socket placeholder blocks demo, and no feed keeper is in the build (A15, A16).
8. **Numbers he never asked for**: give each INFERRED number a reason or a "placeholder" label, and say where 43 overrides the shipped `b` template's 100 trades and 1.5x costs (A20).
9. **Missing seeds**: the stack question, his user experience, and the dropped field questions (A07, A08, A23, A24).
10. **Facts**: the outbox runs the other way (V05); the disk figure is stale and misses the D: drive (V06); DEC-0261 is misstated (A22); decision 8 is neutral, with no recommendation (A25).

## What held up under review

- **Every quote of his words exists verbatim.** A script found all of them in the transcripts, and 43's `grep -n` line numbers match the current files, except "it runs and waits" (T2:135, cited as 132). The problems above are about context, not invented words.
- **Code claims checked at the stack tip `074670ac`** (CHECKED): `trade.schema.json` carries `initial_risk` and `r`; `landing.py:1-18` sends governed kinds to drafts that wait for his yes; `qml/declaration/alternative.py` authors a PolicyPair "without Book keys"; `qml/protocol/intents.py:1-7` says "the bot may not size"; `STAGE0_NEVER_SIZES` exists (`qml/research/stage0.py:36`); `confluence.py:51-61` forbids condition fields; `docs/glossary.md:150` (a tuned assignment mints a new version) and `:558` (the MIS feeds "the Book door and the KSA, never bots"); `ct-03-instrument-identity.yaml:46` "no futures and no options ever (DEC-0015)"; `registry.py:94` declares `library` runnable; `HAR/packs.py:44` never writes hooks; `ENG/settings.py:179` judge cheap and `:187` builder strong; the four QMB and QML replay files exist.
- **Ruling 135 is stated honestly** as a lead's rule against his own words, and the Spotware app approval and "one home per sign-in" match the ruling text (`26-operator-rulings:248-255`).
- **The 1m and 5m call matches his words** (T2:1000), and research 35 §6 item 4 agrees. It covers the same pair only; 43's extension to other markets is correctly put to him as decision 4.
- **Units still trade when the MIS is down** matches T2:135 and STATE:64.
- **The 8-hour trend bound** matches research 05 short answer 2 and research 16.
- **No risk or sizing maths.** Exits stay slots, the 57 exit entries become named blocks whose maths the risk session supplies, and the socket points at pack §4. The breaches are the narrow ones in A09 and A10.
- **Decisions 1, 3, 5, 6, 7 and 10 are genuinely his** (money, scope, choices he posed, a product call per research 35 §6 item 9). None of the ten is a question any trader knows the answer to.
- **Research citations sampled are accurate**: research 36 §0 items 1, 4 and 6; research 39 K1 (home, close analogue, adversarial); research 35 §6 items 1, 5, 10 and 15; research 42 on PR 204's silent runner, the missing trading-server kind and QMN's Linux and systemd needs.
- **The read-me is plain** and is written to him in short sentences, apart from the words in A27.
- **Standing alone, local first and "only he promotes"** are kept throughout: the only automatic move is the risk stop, the catalogue ships as package data, and every guard runs on the trading machine.
