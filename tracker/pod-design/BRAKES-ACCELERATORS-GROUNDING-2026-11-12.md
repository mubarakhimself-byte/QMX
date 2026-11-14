# Brakes and accelerators: what he said, in his words (grounding, 12 Nov 2026)

Read-only research. All quotes are from transcripts and are the owner's dictation, kept as dictated. In his dictation "breaks", "Brex" and "bricks" mean brakes, and "house of money" means house money. Times are UTC from the transcript lines; commit times are local (UTC+3). Text marked **AGENT** is the agent's words, not his.

Sources:
- Early part of the planning session: `C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/3843585b-786c-489b-aec5-b6c33ec14833.jsonl` (1 Nov 13:20 to 3 Nov 10:46). This file is the richest source. The file named in the brief (`2928e6ee-...jsonl`) is the same session's continuation from 3 Nov onwards.
- Continuation: `.../2928e6ee-7392-4c1c-87c8-23b375749b4f.jsonl` (3 Nov 10:44 to 10 Nov 18:14) and its `subagents/`.
- Today: `.../dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26.jsonl` line 2274 (12 Nov 12:29).
- October: `b3275c9d-...jsonl` ("QMX position  sizing risk management", 13 Oct), `ea2b5af9-...jsonl` ("Risk & sizing QML redesign", 15 to 20 Oct), `df6630a9-...jsonl` ("QRMX risk management and precision sizing", 5 to 12 Oct).
- Plan files: `D:/QMX-worktrees/risk-plan/tracker/risk-core/`.
- Code: branches `build/rc-13` to `build/rc-16` and `build/rc-22` in `C:/Users/Mubarak/Desktop/QMX`.

---

## 1. Timeline

| When (UTC) | What | Source |
|---|---|---|
| 5-6 Oct | QRMX session. He first reacts to house money and reverse house money. | `df6630a9` lines 190, 1381, 1404 |
| 13 Oct | Position sizing session. He calls house money and reverse house money "simple". | `b3275c9d` line 769 |
| 15 Oct | Risk & sizing QML redesign. The **AGENT** derives the cushion formula: size from the money above the kill line, so house money and reverse house money "fall out of the math". He does not speak about brakes in this session. | `ea2b5af9` line 70 |
| **1 Nov 13:20** | **Early exploration starts** ("QMX risk management and position sizing"). The agent grounds the old system and the Book/BMS. | `3843585b` line 466 (13:54) |
| 1 Nov 15:33:50 | His first long dictation. He names "accelerators". | `3843585b` line 477 |
| 1 Nov 15:33:59 | **Compaction 1** (idle; summary written 14:49). His 15:33 dictation sits after the summary, so it stayed in context. | `3843585b` lines 484-501 |
| 1 Nov 15:43 | The **AGENT** gives "Brakes first, accelerators second", the daily brake and the cushion. | `3843585b` line 752 |
| 1 Nov 16:26 and 17:48 | His second and third dictations. He agrees "Brex first, accelerator second", asks for a buffer before the floor, and talks about the black swan. | lines 763, 818 |
| 1 Nov 17:52 | The **AGENT** proposes several brakes (unit streak, Book daily, BMS daily, buffer). | line 888 |
| 3 Nov 10:44:41 | **Compaction 2** (idle; the summary was written 1 Nov 19:50 and covers all of 1 Nov). From here on the agent sees 1 Nov only through the summary and the seed files (`seeds/SEEDS.md`, `seeds/operator-words-2026-11-01.md`). | `3843585b` line 1189; `2928e6ee` line 8 |
| 3 Nov 10:44 | His 3 Nov dictation: the circuit breaker, market isolation, and "I can't agree to all this" about the brake list. | `3843585b` line 1175 = `2928e6ee` line 14 |
| 3 Nov 14:14-14:43 | He asks for brakes and accelerators research and says the agent must define the words. Research R9 runs and returns definitions. | `2928e6ee` lines 2610, 2657, 2706, 2738, 2758; subagent `agent-a842c3abc44a85f8f` |
| 6 Nov | Round 1 funnel, architecture and explainer. The explainer asks him Q1b: "May a rule close positions by itself, or only stop new entries?" The agent's default is "Entries only at go-live." | `explainers/risk-template.html:359`; commit 519bfc998 |
| 7 Nov 12:41:37 | **Compaction 3**. | `2928e6ee` line 4341 |
| 7 Nov 13:00 | His critique of round 1, including "may a rule close position by itself? I think no." | `2928e6ee` line 4366 |
| 7 Nov 16:11 | He orders the rerun: "go back to Tuesday ... I don't think you need me." | `2928e6ee` line 5707 |
| **7 Nov 16:13 to about 20:15** | **The rerun ("round two"), unattended.** Seeds go to SEEDS-2, then expansions, a Fable funnel, the architecture, the build plan, and `WALKTHROUGH.html` (commit dda19a637, 23:15 local). `RUN.md` says the run finished on 8 Nov. | `round-2/RUN.md`; subagents from 16:13 onwards |
| 9-11 Nov | Build stack: rc-13 to rc-16 (brakes) on 9-10 Nov, and rc-22 (house money) on 11 Nov. Nothing is merged. | git, section 5 |
| 12 Nov 12:29 | Today: "Breaks were never meant to close trades." | `dd8f4ab2` line 2274 |

He said today that the rerun came "2 days later, in fact, not 4 days later". The record shows two dates of live work with him, Sunday 1 Nov and Tuesday 3 Nov, and the rerun on Saturday 7 Nov.

---

## 2. Brakes

### 2.1 His words, in date order

- **5 Oct 12:52** (`df6630a9` 190): "Reverse House of Money and House of Money were put in for specific reasons ... based off specific conditions, we are also willing to reverse it if we start going in a losing direction. I think that's where Reverse House of Money came in."
- **6 Oct 08:42** (`df6630a9` 1381): "I get reverse house of money, by the way, it's bloody brilliant."
- **13 Oct 17:50** (`b3275c9d` 769): "Kill switch news, that one is simple and it has survived a lot of uh, code variations. ... Correlation is simple. House of money is simple. Reverse house of money, well, you get the idea."
- **1 Nov 15:33** (`3843585b` 477). He is reading the agent's Book summary aloud and reacting: "Closing a trade is never blocked. Now, it's ironic that you haven't talked about things like the kill switch, the SQS. ... The kill switch has survived multiple versions. Okay, so it earned its spot, I would say. So, this is an interesting thing of closing a trade is never blocked. Wow. I think also the old system had that, obviously." He also says: "Also, this is going to change money breaks. Money breaks are important."
- **1 Nov 16:26** (763): "Now these two are accelerators and decelerators. Well, I don't know." (This is about house money and reverse house money.) Also: "in other words, these sort of accelerators and limiters were never doing a thing in a way."
- **1 Nov 17:48** (818):
  - "So at maybe half of the six, so in other words, at three losses ... so that we don't really go with a straight downfall. You get me? So yeah, I'm trying to add a cap."
  - "The thing is, while being aggressive, we needed to have clamps that make sure that, okay, in its aggressiveness, while we lose, we don't lose [stupidly]."
  - "So Brex first, accelerator second. So Brex, accelerator is house of money. yeah, sure. Thank you."
  - "As you can see, I have had a lot of issues with the daily break. And I think we are going to need to have to add way more than one break. And I think the book-based system did that very well. More than one break. Because if you're trading 24 hours a day, multiple instruments, we need to be able to not just do one break at a go. Okay? We need to be able to know what is breaking."
  - "we have accelerators and we also have bricks."
  - "what I would propose, is that the BMS doesn't allow the floor to be touched. So we give a buffer. Think of it like if we are designing a prop firm-based system."
  - "What I'm proposing is we don't allow, okay? That's what the breaks are for. And I think that's why that there were so many clumps in the old system. ... the cushion is 300, true, but we don't want to ever reach that. ... the only time that can happen is during a black swan event ... And then you are telling me that kill switch is failing, the SQS is failing."
  - "Daily drawdown ... They had rules at which if a daily drawdown is hit, we move on."
- **3 Nov 10:44** (1175):
  - "if live results drift from the back tests ... You're meant to size down, I think, but not quickly, I would say. That's why in the old system we had, was it called a circuit breaker? ... these are part of the breaks, I would say, that were installed so to keep this thing intact, okay? So circuit breaker, I think if you had a full stop loss, I think 2 times you stop trading as a unit."
  - "it helped us detect alpha decay. It also, you know, helped with losing. It was a big break. One of the biggest, but again, it's a baseline improve it, please."
  - "if you are to now introduce a circuit breaker, perhaps at the BMS level, it means the system can automatically sense this type of move and switch off entirely. ... it can isolate crypto. And everything is off for crypto. ... It should kick in with the with evidence that this market should be isolated."
  - "The daily breaks. Now, the daily breaks is we are adding so many breaks. We need to also see which ones are useful, which ones we can combine ... There should be several breaks. That is a proposal I had. I didn't say there should, but you seem like you're agreeing, but me, I would say, nah. Let's first explore. ... I can't just say unit break. BMS daily break. I can't agree to all this. I really can't. ... it's circumstantial."
  - "the rules 357, 10, 10, 5, 3 ... They are debatable, okay? Very debatable."
- **3 Nov 14:14** (`2928e6ee` 2610): "the brakes, the accelerators, I forgot to tell you about that. Maybe looking at that alone also might be key. In other words, expanding research on that alone".
- **3 Nov 14:20** (2657): "I hope you know that break and accelerator are just words we are using to, so that we don't have to define everything. You should define them, or you should figure out a definition, or have the agent figure out a definition. ... I don't think they have any. ... House of Money was simple to see, but reverse House of Money was my idea."
- **3 Nov 14:23** (2706): "if you're looking at Brex accelerators, you should look at the transcript, how you have been, like, talking about them ... especially what we had on Sunday".
- **7 Nov 13:00** (4366): "Breaks and accelerators. Seriously, how it configures itself. I don't think I have any opinion. I'm going to leave that part to you. ... More of a hill climb challenge." Also: "You are saying may a rule close position by itself? I think no." (The full quote is in section 4.)
- **7 Nov 14:47** (4824): "There is a simple decision to be made, or you are meant to put accelerators and brakes. It's the very reason we had them in the first place. Because when you have reverse house of money, it's one of the reasons we have such things."
- **7 Nov 15:15** (5074): "the MIS, SQS, a lot of the breaks, the accelerators ... I was proposing maybe overhauls or enhancements, even QML itself".
- **12 Nov 12:29** (`dd8f4ab2` 2274): "Breaks were never meant to close trades. No, breaks were meant to stop trading or prevent trading. ... the SQS and the kill switch, those are breaks because they take circumstantial values ... If we are close to our kill line, yeah, trust me, I think the break was meant to prevent going below a certain value. ... The kill switch is a break. It's never meant to interrupt with the trading directly". (The full quote is in section 4.)

### 2.2 The definition settled with him in the early session (1 and 3 Nov)

These are **AGENT** words that he answered "yeah, sure" or "I like it" to (1 Nov 15:43, `3843585b` 752):
> "**Brakes first, accelerators second:** **Brakes** (reverse house money, a daily brake) can act fast. Cutting risk when you're wrong is cheap even if the signal is noisy. **Accelerators** (house money, ramping toward Kelly) should act slowly and only on counted trades. ... one fixed core, plus named accelerators and brakes that each switch on with evidence."

> "**The daily brake.** The kill line is the floor for the whole seed. A daily brake stops one bad day from eating that whole cushion in one go."

Also **AGENT**, 1 Nov 17:52 (line 888): "Hitting a daily brake: trading restarts automatically the next session. Hitting the floor: the pot stops until you re-seed it." He pushed back on the *list* of brakes on 3 Nov ("I can't agree to all this"), but not on what a brake does.

What he settled, in his own words: a brake is a loss-side limiter, the mirror of an accelerator (his "accelerators and decelerators"). Reverse house money is the model brake. The circuit breaker ("2 times you stop trading as a unit") is "one of the biggest". There should be a buffer so the floor is never touched, and a brake should say what tripped. Every brake action he described is **stop trading, size down, or switch a market off**. In the early session he never described a brake that closes an open trade. The only automatic closing he mentions is through the kill switch ("news is already catered for by the kill switch", 1 Nov 17:48).

Open ambiguity: "switch off entirely ... everything is off for crypto" (3 Nov) does not say whether open crypto trades close.

### 2.3 What changed later, and who changed it

| Date | Change | Who |
|---|---|---|
| 3 Nov | R9 (`research/R9-accelerators-and-brake-pairs.md` §0.2) writes the definitions he asked for: "**Brake.** A rule that, on evidence of danger, holds the unit's risk-taking at or below baseline: smaller size, fewer trades, no new entries, narrower scope, or less exposure. ... It never blocks a close". "Less exposure" is the first opening for a brake that reduces positions. | Agent, on his instruction to define the words |
| 6 Nov | Round 1 SPINE: "**Brake** a row that trips or tapers on a ledger ... **Bench** no new entries for the rest of a window, exits run." Kill levels: "RED close this node's positions at scope ... BLACK close everything and pause". The explainer's default for Q1b is "Entries only at go-live." | Agent; consistent with him |
| 7 Nov | He answers Q1b: "I think no." | Him |
| 7 Nov (rerun) | Round-two FUNNEL row C5 marks his "I think no" as **dissolved**: "My reading, not his words: the old question meant a portfolio rule reducing positions (de-gross, cushion clip); that is a control verb `reduce` or `flatten`". Round-two SPINE AD-12 gives every brake row a verb `none`, `no_new_entries`, `reduce(factor)` or `flatten`. A "sticker" (a stand-down note on a scope) can also have strength `flatten`. | Agent (Fable funnel judge and the architecture fold), while he was away |
| 7 Nov (rerun) | `round-2/WALKTHROUGH.html` line 130 tells him: "**Can a rule close a position?** Yes, and you were right: the dictionary has the mechanisms." This turns his "I think no" into a "yes". | Agent |
| 9-10 Nov | RC-16 builds it. The plan says: "A brake can now close its own trades." | Builders, from the agent's plan |

Note: the idea of a brake that flattens entered from the QML side before the risk session. The pre-existing halts slot contract was "`none`, `no_new_entries` or `flatten` out" (grounding G10:127). On 2 Nov the content wave (commit 433daeb41, Codex) wrote five halt blocks, taken from MQL5 articles, that each answer FLATTEN. He did not ask for either.

---

## 3. Accelerators

### 3.1 His words, in date order

- **6 Oct 08:52** (`df6630a9` 1404): "Oh, today's winnings, not my best. I almost forgot about that. Wow. So trades get a little bit bigger, but only with money won today. ... So you are saying Kelly becomes a ceiling, House of Money becomes the new amplifier".
- **8 Oct 09:41** (`df6630a9` 1548): "when a bot comes in, it should by default have a session it prefers. This also does bring in the House of Money amplifier quite well".
- **1 Nov 15:33** (477): "Then you are saying House of Money and the other adjustments almost never changed. This is something else we might need to consider, which is we are going to call them accelerators, I think. So, for example, House of Money is an accelerator." Also: "Sizing and limits, apparently. And they are tied to accelerators". And: "I don't think I want to lose house of money As I was saying, I don't think I want to lose the house of money and the accelerators analogy."
- **1 Nov 16:26** (763): "House of money. ... Now these two are accelerators and decelerators. Well, I don't know."
- **1 Nov 17:48** (818): "Aggressiveness, I think, is just based off accelerators. I think the whole point of aggressiveness was about accelerating, but at the same time, aggressive and nuclear are two things". Also: "So Brex first, accelerator second. So Brex, accelerator is house of money. yeah, sure. Thank you. The word accelerator, actually. I like it."
- **3 Nov 14:20** (2657): "an accelerator like House of Money, the way it was used ... It was just pattern recognition."
- **7 Nov 13:00** (4366): "Breaks and accelerators. Seriously, how it configures itself. I don't think I have any opinion. I'm going to leave that part to you."
- **7 Nov 14:47** (4824): "how we can achieve having a large risk per trade without having a bad week wiping out everything. ... you are meant to put accelerators and brakes. It's the very reason we had them in the first place. ... House of Money came in like month 4 of QMX."
- **9 Nov 16:32** ("QMX numbers and strategy", `5534aebf` 935): "Considering everything that goes into the trading, from the breaks to the accelerators, which you haven't talked about, if we actually need any."
- **12 Nov 12:39** (`dd8f4ab2` 2364): "we've talked about brakes, we haven't looked at accelerators. I think that's something you should also consider."

### 3.2 The definition settled early

**AGENT** (1 Nov 15:43): "Accelerators (house money, ramping toward Kelly) should act slowly and only on counted trades. ... **House money stays,** but each unit earns it. The research says it only pays when a unit's wins tend to come in clusters, so we measure that per unit before switching it on." **AGENT**, on the cushion: "Win up to $600: the cushion is $300, so $30 a trade (5%). That's house money behaviour, automatically." He agreed to the name and to the order (brakes first). He wanted accelerators to carry "aggressiveness" (the Hummingbird growth idea), held in check by clamps and brakes.

### 3.3 What changed later

- **3 Nov, R9 (agent, on his instruction):** "Accelerator. A rule that, on evidence of opportunity or proof, raises risk-taking above baseline ... It always has a ceiling, and any active brake outranks it." Growing back after a cut becomes a separate "restore". R9 also finds that accelerators do not pay when trades are independent, and do pay only when results persist. The best tested live pair it found is Topstep's tiers.
- **6 to 8 Nov:** house money becomes one cushion rule on one ledger, in shadow until earned, with a "press gate" in front of it. This is the agent's design. He handed over "how it configures itself" on 7 Nov. The walkthrough says it is "on in the scalper template because you asked for it".
- **Nothing he said was reversed on accelerators.** The loss is the other way round: today he says accelerators were never looked at properly. In round two they shrank to house money alone, plus "ramping toward Kelly", which nobody built.

---

## 4. "May a brake close trades?": every statement of his

1. **1 Nov 15:33** (`3843585b` 477), reacting to the agent's summary of the Book: "Closing a trade is never blocked. ... So, this is an interesting thing of closing a trade is never blocked. Wow. I think also the old system had that, obviously." This is about a close never being *prevented*. It is not about brakes *causing* a close.
2. **1 Nov 17:48** (818): "Once that news and session opens, I think news is already catered for by the kill switch." He gives the kill switch, not a brake, the job of handling news.
3. **1 Nov 17:48** (818): reaching the cushion means "either black swan event or something genuinely is wrong in that system ... And then you are telling me that kill switch is failing, the SQS is failing."
4. **3 Nov 10:44** (1175): the circuit breaker means "2 times you stop trading as a unit"; a BMS circuit breaker could "switch off entirely ... isolate crypto. And everything is off for crypto." This is ambiguous about open trades.
5. **7 Nov 13:00** (`2928e6ee` 4366), answering the explainer's Q1b ("May a rule close positions by itself, or only stop new entries?"): "So, bruh, I don't know. You are saying may a rule close position by itself? I think no. Listen, yeah? This is the part now I think you're missing. When I meant the technical lens, you're meant to look at what exactly is already there in the unit also, okay? Because the unit already has QML. It has a dictionary. If you look at the dictionary has closing mechanisms. Okay, you can't just say you can't just suggest this."
   - Reading A (plain): no, a risk rule shouldn't close positions; closing belongs to the unit's own exits, which the dictionary already has.
   - Reading B (the agent's): the dictionary already has closing mechanisms, so yes. The round-two walkthrough reported this reading to him as "Yes, and you were right." FUNNEL C5 labels its own version "My reading, not his words."
6. **7 Nov 13:00** (4366), on the agent's Q5 (may the portfolio day stop raise the kill switch itself): "question number five is really more of a pod life question."
7. **12 Nov 12:29** (`dd8f4ab2` 2274): "Number five, should breaks close trades by themselves? ... I think yes and no. ... depending on the source can give an exit. That's what QML, I think, already considers. Okay. However, and this is a big however, there are exits that may be required depending on the trading methodology or depending on the pod it is in. ... for a scalper, we may require first invalidation, which is relating to the money rules or the rules inside the pod. ... Okay, so do breaks close trades themselves? I think not really. ... Breaks were never meant to stop trading ever. Oh, sorry, not close. No. Let me recall this. Breaks were never meant to close trades. No, breaks were meant to stop trading or prevent trading. ... The kill switch is a break. It's never meant to interrupt with the trading directly, because by the time trading is happening, it means the breaks either have failed or were never activated. ... The only thing to close a trade automatically, I think, would have been I think the highest level of a kill switch, which is like a black swan event, and I think it's already there, if I'm not mistaken."

**Does today's answer match his earlier words?** On brakes, yes. Nothing he said from 5 Oct to 7 Nov describes a brake closing a trade. Every brake he described stops, prevents, sizes down or isolates. His one direct answer (7 Nov) was "I think no", and today's "never" agrees with it. The flatten verb came from the agent's round-two reading and from the QML content wave, not from him.

**Two places where today's words are narrower than the record:**
- **The kill switch.** Today he says only "the highest level ... like a black swan" closes trades. But the plan and node already close at **RED** ("close this node's positions at scope") as well as BLACK. The old system's kill switch also had a **soft news kill** that exits positions in 25% chunks before news ("block entries at T−15, exit in 25 % chunks every 2 minutes from T−13 to T−5, flat by T−5", grounding G10:226). He himself said on 1 Nov that "news is already catered for by the kill switch."
- **Exits by method or pod.** Today he allows "exits that may be required depending on the trading methodology or depending on the pod", such as first invalidation. He files those under exits and money rules, not brakes.

---

## 5. What the code does today

Everything below is on stacked branches, pushed to origin and **merged nowhere** (not `integration`, not `main`).

- **RC-13** (`build/rc-13`, commit 8b667d2fc "Run a brake as a control row in the unit", 9 Nov). The `halts` field becomes control rows that run in the unit. The default verb is `no_new_entries` (`packages/qmf-risk/src/qmf/risk/controls.py`: "a brake stops entries and nothing else, so it can never reach an exit").
- **RC-14** (4e9d0f573) folds every brake's state into one word: ACTIVE, REDUCING, BENCHED, HALTED or RESTORE.
- **RC-15** (550e1aa67) writes a `risk_event` row for every fire.
- **RC-16** (`build/rc-16`, head 14065fc64, PR 371; review `D:/QMX-worktrees/risk-ship/review/rc-16-check-14065fc6.md` CLEAN, after a NOT CLEAN on the PR body):
  - fc2493700 "Let a brake's flatten and reduce verbs run". Before this, `reduce` and `flatten` were refused at compile with `verb_not_built`.
  - 1908fd176 "Flatten through the exit path ...": `flatten` "mints one close per held position through the same helper the per-bar exits use, with reason `control_flatten`".
  - 9fd39ba7d "Send a stopped member back to paper by rule, never to live".
  - A row whose restore is `hand` calls `Runtime.risk_stop`.
  - The plan's "You see" line: "A brake can now close its own trades."
- **Today, by default, no brake closes anything.** The verb comes from the row (`qml/protocol/controls.py:168-169` uses `row.verb`), the default is `no_new_entries`, and the shipped template `dummy-trend-pullback.json` has empty halts. A brake closes trades only if a unit or pod author writes `verb: flatten`.
- **Two latent traps:**
  - Five stdlib halt blocks from the 2 Nov content wave describe themselves as flattening: `account-daily-loss-halt`, `equity-drawdown-halt`, `losing-days-halt`, `session-fill-limit-halt` and `session-loss-limit-halt` ("Flatten the account for the day ..."). Under a default row they only stop entries, so their dictionary text says the opposite of what they do.
  - The `qmf-risk` controls docstring still says reduce and flatten "are refused", which RC-16 made stale.
- **The kill switch** (node, pre-existing): RED closes positions at scope; BLACK closes everything and pauses until his hand.
- **Accelerators:** one is built. **RC-22** (`build/rc-22`, head 1b09f81c9, 11 Nov; commits 0ee1f8ce8 and e4b14b11f) adds two blocks:
  - `cushion-rule@1`: "House money and reverse house money as one sizing modifier: the size moves with the unit's closed trades in R since an anchor". A fixed anchor both presses and brakes; a running-peak anchor only brakes. It reads closed trades only.
  - `press-gate@1`: allows raises only while the unit's word is ACTIVE.
  - Neither block is bound in any shipped template. The review `rc-22-check-1b09f81c.md` is NOT CLEAN (a red gate). No other accelerator (ramp toward Kelly, Topstep-style tiers, session premium) is built.

---

## 6. Open questions only he can answer

1. On 7 Nov you said "may a rule close position by itself? I think no ... the dictionary has closing mechanisms." Did you mean "no, closing is the unit's exits' job"? The rerun told you that you had said yes.
2. Should the "flatten" option that RC-16 added to brakes be removed, or kept as something a pod may switch on with the default off?
3. Which kill-switch levels may close trades? Today the plan closes at RED (one scope) and at BLACK (everything). The old system also closed positions before scheduled news.
4. When a circuit breaker isolates a market ("everything is off for crypto"), should open crypto trades be closed, or only new ones stopped?
5. Is house money (size grows only from closed winnings, and any brake blocks a raise) the accelerator you want first, or should other accelerators be explored before it ships?
