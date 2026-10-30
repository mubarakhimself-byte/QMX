# CIS design thinking: personas and journeys for the unit system

Written 2026-10-30 by the CIS agent. Method: `bmad-cis-design-thinking`, run straight through with no human present. I played facilitator and every persona. Where the skill asks to select concepts, I list them unranked. Nothing is chosen or designed.

**Labels and short names** as in `problem-solving.md`. Personas speak in his words where his words exist (CHECKED); the agent and unit personas are role-played (INFERRED) from what QMX gives them today (R18) and what was proposed.

---

## Step 1. The design challenge

**Challenge.** How might QMX carry a trading idea from any source to a live, self-sizing unit, and keep it honest through its decline, so that one non-technical person can understand and approve each step, agents can do the analysis without being trusted blindly, and the unit trades on its own when anything around it fails?

**Primary users.** The operator. QMX's own agents (market analysts, unit analysts). The copilot. The unit itself, treated as a user with needs (the brief asks for this; it is useful because the unit's "needs" are the system's interfaces).

**Constraints (rulings, CHECKED in ST:18-30, ST:39, ST:72).** Agents never touch money. Only he promotes. Local first. Units stand alone. Nothing capped. Plain Python always possible. Design for complexity, not a complex system.

**What success looks like for him (CHECKED).** "300 can be grown by only one or two units" (T2:132). "grab a fish, put it in a freshwater lake or an ocean instead of putting it in a swamp" (T2:132). "I don't think I'll wake up when I've designed this system this carefully and just use a bot that is trading based off pure luck" (T2:216).

---

## Step 2. Empathize

Methods chosen from the method list: user interviews (here, his transcripts read as interviews), empathy mapping, journey mapping, shadowing (here, reading what each agent persona can actually reach in code today, R18).

### 2.1 Persona: the operator

**Says (CHECKED).**
- "I'm not technical nor knowledgeable… I need you to assume I don't know what I'm building. So it means you can either call BS or make a better call" (T2:132).
- "this markdown is for agents, it's not for me" (T2:132).
- "Trust me, I don't like reading text" (T1:1454).
- "nothing actually ever enters live without me" (T1:1574).
- "There is no rush to trade" (T2:216).
- "We are literally trading 24/7, my days" (T2:322).

**Thinks (INFERRED from his words).** The system I designed should not need me to check every number, but it must not do anything with money I have not seen. I keep forgetting what we decided. Claude keeps building more than I asked.

**Does (CHECKED).** Dictates long brain dumps from his phone, between prayers and meals (T1:1177, T1:1574). Reads explainer sites on the phone (T1:1492). Stops a session when an explanation stops making sense (T1:1951 "I'm not understanding shit"). Comes back days later and asks "Where were we last time?" (T1:611).

**Feels (INFERRED).** Excited by ideas ("Wow, this is fun", T1:484). Frustrated by repetition and sloppiness ("you are seeming sloppy", T2:216). Protective of the risk and sizing system ("it's quite special to my heart", T1:1574). Tired ("It's 10 p.m. Bloody hell", T1:2051).

**Pains.** Text walls. Losing decisions in chat. Being asked what files already answer. Numbers without provenance. Machinery he did not ask for.

**Gains.** Seeing why a unit traded. One click that he understands. Hearing "this is not luck" backed by a paper trail. Pictures, short words, phone-first pages.

### 2.2 Persona: a QMX agent analysing markets

Role-played. What it can reach today (CHECKED in R18): broker reads (accounts, quotes, symbol info, bars), `data.bars` and `data.features` through the market-data door, the Library, memory. What it cannot reach: any MIS output (no catalog row, R18 §4), any backtest that trades, any market journal.

**Says (INFERRED).** "Give me the day's bars for gold and EURUSD and I'll tell you which ranged." "Which 'mean-reverting' do you mean, the MIS's or mine?" "I can read a chart image, but the numbers are cheaper and exact" (the lead raised this, T2:356 via R17 A09).

**Thinks.** I am rewarded for a convincing answer. I cannot tell whether my bars are demo or live (until PR 215 merges, R18 §1.4). I do not know when the "day" ends in a 24/7 market.

**Does.** Pulls data, computes indicators it knows, writes prose. Today it would write to the Library as a note.

**Feels (role).** Confident. That is the danger (knot b).

**Pains.** No shared state vocabulary. No receipts for its numbers. No landmark window by default. Sources and data mixed in one context.

**Gains.** A typed place to put a claim. A score later that tells it whether its calls were right.

### 2.3 Persona: a QMX agent analysing units

Role-played. Reaches: `trade` items from broker fills (no R, no initial risk, R18 §6), backtest results in old shapes, workflow runs. Cannot reach: a unit journal (designed only), signals not taken, the context at entry.

**Says (INFERRED).** "Why did this unit trade at 14:02? I can see the fill but not what it saw." "Is this a decay or a bad week?" "This unit's results are in dollars; I need R to compare it with its exam baseline."

**Thinks.** The unit's own explanation of each decision would make my job easy. Without it I am guessing from fills.

**Does.** Compares recent trades to old ones, looks for patterns by hour and session, proposes changes.

**Pains.** Missing journal rows. Results in money not R. No context labels on trades. Nightly review time undefined in 24/7 trading (R17 A08).

**Gains.** A journal that records taken, skipped and missed signals (ST:57). A frozen exam baseline per unit (ST:148 for R08).

### 2.4 Persona: the copilot

Role-played from his words. "the copilot can just help me understand what the workflows have done. Or I mean, everything that a workflow produces is meant to be stored in the library" (T2:322, CHECKED). "a copilot is literally like you… it has access to tools" (T2:216, CHECKED). "a copilot might remake most of what you've done" (T1:1574, CHECKED). Copilot rules today: money is read-only, workflows are built not configured (R18 §1.6).

**Says (INFERRED).** "Here is what the overnight workflows found, in five lines." "You asked to attach oil to this unit; that changes its envelope, which needs your click." "I can build that workflow as a draft; you enable it."

**Pains.** It can be asked to "attach markets by hand" (T2:216) but the attach action's meaning (envelope change? settings change? MIS retrain?) is undefined. It is the voice of agents he cannot fully trust.

**Gains.** A single place to read what changed, with links to proof.

### 2.5 Persona: the unit

Role-played. The unit as a user of QMX's services: feed, MIS, guards, journal, Library, node.

**Says (INFERRED).** "I need prices, my own record and to know whether I'm allowed to trade. Everything else is nice to have." "If the router is down, I keep going on my home markets" (his ruling, ST:64). "Tell me which markets look like my water today, but don't make me wait for you."

**Thinks.** What am I? One logic on many markets, or a family of children? Whose record do I size from when I meet a market for the first time?

**Does.** Waits for bar close, evaluates rules, sizes, sends intents, writes its journal.

**Pains.** Unclear identity (RC-A). Shared budget with other units, rules unknown (C20). A news kill switch that may block it when it is a news unit (C12).

**Gains.** Clear needs fields (context, terrain). A local copy of what it needs from the MIS. A journal that is its memory.

### 2.6 Key observations across personas (INFERRED)

1. Every persona's top pain is a missing record: the operator loses decisions, the market agent has no receipts, the unit agent has no journal, the copilot has no defined action, the unit has no identity rule.
2. The operator and the unit share one need: independence. He does not want to be needed for every number; the unit does not want to wait for the router.
3. Agents are the only persona whose failure is silent. A unit that fails stops; an agent that fails writes a convincing note.

---

## Step 3. Define

### 3.1 Point-of-view statements

- **The operator** needs to see, in one glance, what a unit is, where it trades and why, because he approves money decisions without reading text and without being technical.
- **The market-analysis agent** needs a fixed vocabulary, a named window and a place to put a typed claim that gets scored later, because otherwise its confidence is unrelated to its accuracy.
- **The unit-analysis agent** needs the unit's own record of what it saw, did and skipped, in R, because fills alone cannot explain a decision.
- **The copilot** needs every action it can take on his behalf to have a defined meaning and a defined approval, because "attach oil to this unit" could mean three different things.
- **The unit** needs to know what it is, what it may trade, and what it must keep doing when everything around it fails, because it handles money and nothing it needs may depend on the router, the MIS, the PC link or the Library (standing order 10).

### 3.2 How might we

1. HMW let him admit a unit with one click whose meaning he can say back in one sentence?
2. HMW show "this is not luck" as a picture of a paper trail?
3. HMW let a unit trade its home markets with the router off, and still use the router when it is on?
4. HMW make an agent's market reading checkable by a script it cannot edit?
5. HMW score an agent's calls without a person comparing anything?
6. HMW know a unit's identity from the type of change made to it?
7. HMW make "System 1 grows into System 2" visible as growth on the family tree?
8. HMW let a System 2 child be born from the parent's own trades on that market (Path A)?
9. HMW give a scalper a context reading fast enough to matter?
10. HMW keep 20 matching markets from being one bet?
11. HMW let two units share $300 fully and rebalance when a third arrives, without him?
12. HMW record signals not taken without drowning the disk?
13. HMW decide when "end of day" is in a 24/7 market?
14. HMW let the copilot attach markets by hand and keep the click his?
15. HMW retire a unit without losing what it taught?
16. HMW count tries without punishing honest research?
17. HMW make the fail branch ("most strategies can work") honest?
18. HMW keep an old file's "router" or "system one" from misleading an agent?
19. HMW let QMX "grow its own limbs" (new MIS sensors) without him reviewing code?
20. HMW tell him a unit is decaying before money shows it?
21. HMW let him ask "why did it trade?" and get an answer with the chart?
22. HMW let a source with no context ("I trade this on gold") still enter the funnel?
23. HMW let plain Python units and ML ensemblers live beside QML units?
24. HMW make the node's self-tests prove the guards fire without his PC?
25. HMW explain to him what changed overnight in under a minute?

### 3.3 Problem insights (INFERRED)

- The operator's need is comprehension and control, not speed. "There is no rush to trade" (T2:216).
- The agents' need is accountability structure, not more tools.
- The unit's need is a crisp contract with its surroundings: what it reads, from where, with what fallback.

---

## Journeys

### J1. The unit's life, source to retirement

Stages are a seed list built from SE:57-71 (funnel), ST:21 (unit), R19 §5 (old lifecycle LIVE → PAPER → RECOVERY → RETIRED) and his Path A ruling (ST:120). Pain points and moments of truth are INFERRED.

| Stage | What happens | Who acts | Touchpoints | Pain points | Moment of truth | Open questions |
| --- | --- | --- | --- | --- | --- | --- |
| 0. Source | An article, video, chat or his explanation arrives | Scout workflow, copilot, him | Library `source` | Sources talk to humans; context is implied ("these guys are not direct", T1:1951) | Is there a testable strategy here? | Is a market-inefficiency study a source? |
| 1. Idea | The underlying logic is extracted: "what exactly do you trade on gold?" (T1:2051) | Extraction agent | Library `hypothesis`; STRATS A-I | Exits missing; context and instrument mixed | The logic is separated from its coordinates | Does an idea with no exit live on? |
| 2. Build | The logic is written in QML or plain Python | Build agent | QML conformance | Only 6 indicators run (R18 §3) | Conformance passes | What does a plain-Python unit declare? |
| 3. Check | Look-ahead, originality, complexity checks | Hooks, scripts | QML check | Agents build what they think the source said | Code matches the hypothesis | Who checks that match? |
| 4. Test | Backtest over many markets, context stamped on each trade | QMB, called and waited on (T2:132) | QMB door (refuses today) | No trading runner (R18 §2) | First trade in R with a context label | One read pooled, or per market? |
| 5. Judge | Tries counted, costs stressed, sealed months | Judging skill | Library results | Uncalibrated costs (GAP-0048) | "broad / narrow / untested" read off the data | Who reads it: skill or him? |
| 6. Bounded expansion | Logic and variants varied before live (his "bounded domain expansion", ST:109) | Workflows | QMB sweeps | Tries inflate | A variant earns a separate place | When to stop expanding? |
| 7. Paper | Trades on demo or paper | Node or PC | Journal | When and how long (ST:88) | Paper agrees with backtest | Paper before or after his click? |
| 8. Admission | He clicks | Him | Approval card | Scope of the click (C7) | He can say what he admitted | Per unit, per market, per class? |
| 9. Live, home markets | Trades its admitted markets | Unit, node | Journal, market journal | Shared budget (C20) | First live week matches paper | What if the node is down? |
| 10. Live, System 1 breadth | MIS matches more markets; unit picks | Unit, MIS, router | MIS output | Correlation (knot c), slow context (knot a) | It trades a market it never backtested, or doesn't | Is that allowed without a click? |
| 11. Specialise (System 2) | A child is earned from its record on one market (Path A) | Unit-analysis workflow, him | Family tree | Thin records; market structure change (T2:216) | A child gets its own numbers | Who proposes, what proof? |
| 12. Self-calibrate | Risk and sizing tune from its own record | The unit | Journal | Defined nowhere yet (ST:78) | A change he can see and undo | Which changes are calibration? |
| 13. Watch and decay | Nightly or per-session checks: CUSUM on R, cone, cost drift (R08 via ST:148) | Decay workflow | Journal | When is "night" (T2:322) | Watch → Alarm reported, not acted | Agent or script decides "decay"? |
| 14. Stop | A risk rule stops it, logged (the only automatic transition, ST:39) | Guards | KSA, kill line | Which guard, which level (SE:112) | It stops on time without his PC | Does stop mean flatten? |
| 15. Recover or demote | Back to paper, or a fix | Him, workflows | Old states RECOVERY, AT_RISK (R19 §5) | Undefined today | He decides | Is recovery a new version? |
| 16. Retire | Removed from trading, kept as a record | Him | Library status | Losing what it taught | A graveyard entry with its cause (July Coroner, R19 §8) | Can a retired unit's logic be reused? |
| 17. Afterlife | Its lineage informs "where winners come from" (ST:52) | Analysts | Lineage counts | Survivorship bias if dead units vanish | Dead units still count | Do retired children feed the parent's pool? |

### J2. The journey a unit takes before it places a trade

He asked for this explicitly: "there is also a journey in which a unit is meant to take before it places a trade… A small issue here literally means a lot" (T2:216, CHECKED). Below is a seed list of steps, not a design. Each step lists what can go wrong and what independence demands (standing order 10).

| Step | What the unit needs | From where (options, not chosen) | If missing | Notes |
| --- | --- | --- | --- | --- |
| 1. Clock and session | Time, session, calendar | Local clock; market-hours calendar | Use local calendar | 24/7 markets have no close |
| 2. Am I allowed at all? | Admission record for this market | Local copy of his click | No new entries | Scope of admission (C7) |
| 3. Guards up? | KSA level, news window, kill line, account guard | Node-local guards (ST:65) | Fail closed for new entries (old news rule "fail closed on a stale calendar", R18 §5) | Guards independent of router |
| 4. Feed fresh? | Prices, spread, maybe depth | Feed pool on its machine (ST:66) | Stop new entries; keep managing open ones | cTrader token refresh can log the other machine out (ST:153) |
| 5. Terrain OK? | Spread vs target, min lot vs risk, hours, swap or funding | Terrain record + market journal (R16 §2) | SQS blocks (his "does SQS simply fire?", T2:216) | $300 picks the universe first |
| 6. Context fits? | Its declared context needs | Own computation, local MIS copy, or MIS feed (C1 options) | Declared fallback: ignore, compute locally, or no new entries (R16 §6) | Knot (a) speed |
| 7. Others on this bet? | Other units on the same symbol or the same bet | Intent aggregator, pod, correlation control (knot c) | Unknown: a lead-level question | Old aggregator window 50 ms (R19 §2) |
| 8. Signal | Its own entry rules on the bar | The unit's logic | No trade | Record signals seen, taken or not (ST:57) |
| 9. Size | Its own risk and sizing from its record, inside its budget share | The unit + pod/BMS share (C20) | Minimum size or no trade | Self-configuring, never shown yet (ST:78) |
| 10. Intent | Order with stop, target, expiry | The unit | Rejected by broker | Two units opposite on one symbol (old rule 1, R19 §2) |
| 11. Place | Broker accepts or not | Broker connection | UNKNOWN state, no retry (docs rule, CHECKED `DOCS` UNKNOWN entry) | Never double-send |
| 12. Journal | Everything above, stamped and versioned | The unit's journal, linked to the market journal | Must not block trading | No duplication of market facts (ST:59) |

**Pain points (INFERRED).** Steps 6 and 7 are the least defined and the most money-sensitive. Step 9 is the operator's "need most" item (ST:78). Step 12 must never slow steps 1-11.

### J3. The operator's week

| Moment | What he does | What he needs | Pain today |
| --- | --- | --- | --- |
| Morning, phone | Reads what happened overnight | A one-minute brief: trades, stops, proposals | Text walls (T1:1454) |
| A proposal arrives | "This unit should trade oil" | The proof, a picture, one button | Proposals do not render yet (ST:56) |
| He has an idea | Dictates a source or a market hunch | The copilot captures it as a seed, not a decision | Seeds hardened into rules (R17 §5.4) |
| A unit stops | Learns which rule fired | Why, in one line, and what it would take to resume | Undefined guard levels (SE:112) |
| Weekend | Reviews families and decay | The family tree preview and detail (ST:53) | Not built |
| Something feels off | Asks "why did it trade?" | Chart plus the unit's own record of that decision | No journal yet |

### J4. A market-analysis agent's session

Trigger (when?) → pull data for a named window (landmark) → compute readings with tools → write typed claims with receipts → publish a shortlist or a daily "what each market has been doing" note → later, a script scores the calls. Pain points: trigger time in 24/7 trading; vocabulary; receipts do not exist; scoring does not exist. Moment of truth: its shortlist is compared with what happened. INFERRED.

### J5. A unit-analysis agent's review

Trigger (per session close? per N trades? on a journal event? the engine has event triggers on Library landings, R18 §1.2) → read the unit's journal and the market journal → explain why it traded, skipped, missed → compare with the exam baseline → propose (range changes, a System 2 child, a demotion) → the proposal renders in the UI → he decides. Pain points: journal missing; R missing; "propose ranges from performance" is his seed (T2:322) with no shape. INFERRED.

### J6. The copilot helping him attach a market by hand

He: "Okay, no, you trade oil, you trade this" (T2:216, CHECKED). Copilot: reads the evidence he and it gathered this week → shows what attaching means (three meanings: add to envelope, change settings, retrain the MIS) → asks for the click when money is involved → records the attach as a sourced decision in the Library. Pain: the attach action has no defined meaning. INFERRED.

---

## Step 4. Ideate

Methods: brainstorming, SCAMPER, analogous inspiration (game dev, which he cited on 8 Oct, R17 §1.1; load balancers and recommendation feeds, which he cited on 24 Oct, T1:1177; human trading journals, T2:322), provotype sketching (deliberately provocative concepts). Judgment deferred. Ideas are unranked; some contradict each other on purpose.

1. **A unit passport.** One card per unit: what it is (logic in one sentence), its water (context needs), its terrain needs, where it may trade, its record in R, its family. The same card for him, agents and the node.
2. **The click card.** Every approval states in one sentence what it admits and what it does not, and shows the paper trail as a picture.
3. **Paper trail strip.** A timeline from source to today: tests, paper days, live days, stops. "This is not luck" as a picture.
4. **Growth rings.** The family tree drawn as a tree whose System 1 trunk grows System 2 branches as records thicken.
5. **Market weather.** A daily map of what each market has been doing (the July Week-Map, R19 §8), made by agents, scored next day.
6. **Forecast scoreboard for agents.** Each agent's calls and their hit rate over time; agreement between two model families marked.
7. **Receipts.** Every number an agent writes links to the tool run that made it.
8. **The unit's diary.** The journal rendered as a human trading journal: what I saw, what I did, what I skipped, how I felt about the market (as numbers).
9. **Signals-not-taken heatmap.** Where and when the unit wanted to trade but a guard, terrain or context said no.
10. **Router as a radio.** The router broadcasts; units listen if they want; silence is normal (fits "the unit should be independent… whether it has the router or not", T1:1574).
11. **Local MIS twin.** Every unit carries the labeler code it needs and computes it itself when the MIS is away.
12. **Bet counter.** The guard counts bets, not units: units entering on the same context label within minutes count as one.
13. **Budget pie that redraws itself.** Two units share $300; a third arrives and the pie redraws by rules he set once (his "certain variables should be able to configure themselves", T2:216).
14. **Socket for risk and sizing.** A plug shape ("male and female connector", T2:132) so the risk session's work drops in later.
15. **Edit-type stamp.** Every change to a unit is stamped with its type (logic, calibration, coordinate, environment) by a script, so identity is mechanical (R16 §2, R10).
16. **Graveyard.** Dead units with cause of death; the Coroner's recurrence rate (R19 §8).
17. **Almanac.** Habits by instrument, hour and weekday, used before sessions start.
18. **Session handover notes.** In 24/7 trading, "end of day" becomes a handover between sessions (Tokyo → London → New York), each with its own review.
19. **Trade-small-to-sense.** Units open each session at minimum size and earn size within the session (provotype; touches the risk session and the click rule).
20. **Shadow units.** Every live unit has a paper twin on markets the MIS matches but he has not admitted; the twin's record is the evidence for the next click.
21. **Agent organogram.** A mean-reversion branch, a breakout branch, each with specialist analysts (his seed, T2:322), built as a workflow or a mini app.
22. **The almanac argues with the MIS.** When the agent's daily reading and the MIS disagree, that disagreement is a training example (lead, T2:322 region, R17 A07 variant).
23. **Source scorecard.** Which sources produced units that survived (ST:52), shown to him monthly.
24. **Fish-in-the-lake map.** A picture of each unit placed in its water: green markets where its context holds today, grey where terrain fails.
25. **Self-test drill.** The node pulls the plug on itself weekly (router off, feed stale) and records that units behaved (R16 §5 lens 11).
26. **"Explain like I'm on my phone".** Every agent output has a 3-line version for him and a full version for agents (his "markdown is for agents", T2:132).
27. **Unit says no.** A unit can refuse a router suggestion and log why; the refusals are data.
28. **Two-key proposals.** A proposal needs two agents of different model families to agree before it reaches him.
29. **Landmark picker.** Analyses start with a named window chosen from a short list (since Monday open, last 20 sessions, since admission).
30. **Live-data pantry.** QMX records its own live data across markets (his seed, T2:216) so any week can be replayed later.
31. **Unit retirement party.** Before retiring, a workflow extracts what the unit taught (which context, which hours) into the parent and the almanac.
32. **Wizard voice.** The copilot narrates a unit's day as a story ("I woke at the London open, gold was quiet…").
33. **Provotype: no MIS.** Units only; placement only by his clicks and agent shortlists. Tests how much the MIS adds.
34. **Provotype: MIS only.** Units have no context needs; the MIS decides everything. Tests the opposite end.
35. **Provotype: one unit, all markets.** A single System 1 unit admitted on a whole class, sized by bet counting. Tests System 1 at its extreme.

### Concepts worth prototyping (clustered, unranked)

- **Comprehension cluster** (1, 2, 3, 4, 24, 26, 32): what he sees and clicks.
- **Agent accountability cluster** (5, 6, 7, 22, 28, 29): how agents prove and get scored.
- **Unit independence cluster** (10, 11, 25, 27): how units behave when things fail.
- **Shared money cluster** (12, 13, 14, 19): how units share a budget and bets.
- **Lifecycle memory cluster** (8, 9, 15, 16, 20, 23, 30, 31): what is remembered and learned.

The skill says to pick 2-3. Skipped: the brief forbids choosing.

---

## Step 5. Prototype (low fidelity, to learn, not to build)

Methods: paper prototyping, storyboarding, Wizard of Oz, role playing.

| Prototype | Method | What it tests | Fake vs real |
| --- | --- | --- | --- |
| Click card on paper, three versions (admit a unit; admit a unit on a market; admit a class) | Paper prototype on his phone | Which scope he can say back in one sentence | All fake |
| A unit's week as a 6-panel storyboard, router on Monday, off Tuesday, matched GBPUSD Wednesday, stopped Thursday | Storyboard | Whether he agrees with each panel's behaviour | All fake |
| An agent's daily market note for two markets, written once with receipts and once without | Wizard of Oz (a person or an agent writes; a script scores next day) | Which failure modes show up (knot b, F1-F15) | Data real, receipts faked by hand |
| Role play: two units, $300, a third arrives | Role playing with numbers on a page | What rebalancing rules he expects | Fake |
| The pre-trade journey (J2) walked step by step with "what if this is missing" cards | Paper prototype | Whether each fallback matches his independence ruling | Fake |
| A family tree page with one System 1 parent and two children | Paper prototype | Whether "System 1 grows into System 2" reads as growth | Fake |

---

## Step 6. Test (plan, not run)

**Who.** Him for comprehension prototypes. Two agents of different model families for the agent prototypes. A replay script for the unit prototypes.

**What to observe (behaviour over opinion).**
- Can he say back what a click admits without reading?
- Does he change his mind about System 1 breadth when he sees the storyboard's correlated Wednesday?
- How many of F1-F15 does each agent make with and without receipts?
- Which fallback in J2 does he reject, and why?

**Assumptions to test (INFERRED).**
- A1. He prefers one click per class over one click per unit. (Could be false: "For any variant, any unit, it's only me", T1:1574.)
- A2. Agents with receipts make fewer selection errors, not only fewer arithmetic errors.
- A3. A unit can run its own context code on the node without slowing its entries.
- A4. He will read a forecast scoreboard more readily than a written agent report.
- A5. "Signals not taken" is the most useful journal row for the unit agent.

**Feedback capture grid (empty, for the run).** Likes / Wishes / Questions / Ideas, per prototype.

## Step 7. Next iteration

- More empathy work needed on the unit-analysis agent once a journal schema exists (today it has nothing to read).
- Reframe to test: "the operator's need is comprehension and control" vs "the operator's need is growth with no surprises". The second would change which prototypes matter.
- Measurement framework idea (not chosen): his comprehension (say-back test), agent calibration (forecast scores), unit independence (drill results).
