# Risk and sizing pack

Written 2026-10-30 for the operator's separate risk-and-sizing design session. It collects and organises. It designs no risk or sizing maths.

## 1. Read me first

This pack holds everything the operator has already said about risk and sizing, in his own words, with the date and the exact file and line of each quote. The session should read his words in section 2 before anything else, and should never reword them back to him as if they were his. Section 3 puts the research findings beside each topic, section 4 lists what the unit-system planning expects to hand this session and get back, and section 5 says what is out of date in the older hand-off. His standing rulings bind the session: only he promotes a unit to live, and the only automatic change is a risk rule stopping a unit, which is logged; agents never touch money; everything works on his PC first; nothing is capped; a unit keeps trading without the router; and every number ships as an editable default, never a fixed value. Where his statements disagree with each other, both sit side by side below, unresolved, because only he settles them.

---

## 2. His words

**How to read the quotes.** Every quote is his own turn, copied exactly, speech-to-text slips included. A "[...]" marks words left out inside one turn. Nothing here is an agent report relayed as his turn. Each quote was checked by searching the file for its text on 2026-10-30.

**File keys.**

| Key | File |
| --- | --- |
| T1 | `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/operator/transcript-2026-10-20-to-28.md` |
| T2 | `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/operator/transcript-2026-10-29-to-30.md` (still being appended; line numbers as of 2026-10-30 10:40) |
| D27 | `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/operator/2026-10-27-review-dictation.md` (line 9 is the whole dictation; it is the same text as T1:1574) |
| D28 | `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/operator/2026-10-28-router-system1-system2.md` (line 7 is the whole dictation) |
| Q5 | `C:/Users/Mubarak/Desktop/QMX/workroom/risk-lab-2026-10-05/sources/qrmx-session-2026-10-05-to-12.txt` (the 5 to 12 Oct session where the self-calibrating unit was born) |
| Q13 | `C:/Users/Mubarak/Desktop/QMX/workroom/risk-lab-2026-10-05/sources/qmx-position-sizing-session-2026-10-13.txt` (the 13 Oct session) |
| R19 | `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/research/19-grounding-old-system.md` (quotes his April 2026 words from the old vault) |

Line numbers in Q13 come from `grep -n`. Python's default line reading counts some stray carriage returns as extra lines and gives larger numbers there.

### 2.1 Self-configuring: the unit sizes itself

- **8 Oct, Q5:1739.** "what if each boat is to get its own assigned risk management and position sizing system whereby we can have it configure or reconfigure or recalibrate itself? This might require us to build some sorts of algorithms, in my opinion, whether we like it or not. Where do we see such a pattern recurring? Ideally, it would be in game development, according to me, mostly game development. Okay, an example. I mean, I don't know, dude. An example would be a character changing, you know, position, a character doing XYZ."
- **8 Oct, Q5:1739.** "So instead of us relying only on manually configuring, we can have an algorithm do that, but then how are we doing? How are we creating that algorithm? That's another question. Okay. So it means regardless of the backtest logs, the system can configure itself. Now what does this mean? It means that a bot is no longer a bot, it becomes a trading algorithm fully, okay, with its own custom risk management and rational sizing system, its own basically. Now, this now brings in the concept of the MIS being specific to it."
- **8 Oct, Q5:1742.** "my earlier idea was we consider a bot plus this its own version of this system that we are designing as one so instead of us designing them as different pieces no we design them as bloody one"
- **8 Oct, Q5:1671.** "if you are designing this system that is meant to handle multiple types of scalpers and optimizing it to handle every type at a god, that is a mess, a bloody vomit mess. Okay, it doesn't make sense."
- **13 Oct, Q13:1806.** "your bs call makes sense the problem is I'm reading it and laughing at the same time. Because you call you call that a real thing. It's just that I'm seeing how complex the self-optimizing thing is going to be. I don't know, maybe I'm overcomplicating this."
- **20 Oct, T1:376.** "The idea for the unit was, I was asking, can't I get one singular bot that can self-configure? I don't know if now you are seeing the breadth of research even. Because self-configuration, the idea is simple. Risk management, position sizing, all that stuff is done on the bot. So you don't have to recalculate, redo everything, and design a very complicated thing. No, we keep it simple in that the bot has a specific risk management position sizing based off how it trades, which means we can have better configuration, better things. [...] So, which means you can look at a risk management position sizing system which can handle maybe a mean reversion scalper. And with enough research under QMX on a daily, perhaps also, not on a daily, but try to get the idea, we can really derive the best system for that bot in terms of risk management, position sizing with the best variables. Again, this is more of a seed."
- **24 Oct, T1:1177.** "On part number 2, the bot never sizes and the unit sizes itself. I think we shall have to clear that when I come back later."
- **27 Oct, D27:9.** "And I think, not overkill, but it goes back to the other thing whereby I'm like self-configuring. I actually haven't seen how they are going to self-configure. I needed that more because it was proposed. You argued it's doable. I gave you how it should be, how I thought of it, not how it should be done, but how I thought of it in terms of game dev and all that. In the old conversation transcripts I gave you earlier. However, I haven't seen a singular thing in which or how it should be done, unless I'm wrong. Unless I'm wrong. Because you're saying on complete, it replaces the driving mode and this. Oh my days. Yo, I think that is one of the things I need most right now."
- **29 Oct, T2:219.** "That's the whole point of the unit, self-configuration, which again now is bothering me. How are we going to have this thing self-configure itself? Because I think we are not talking about the unit most of the time right now. We are talking about the MIS specifically. But self-configuration is mostly under the risk management and position sizing."
- **30 Oct, T2:788.** "But what is inside the thing that interacts with the market is a good question. But at the same time, remember, if it's going to be self-configuring, we need to know how it is going to be able to do that, which means risk management and position sizing might come in. [...] I think we need to actually define what is meant to be tuning itself, because we haven't really defined the unit in terms of structure. We don't know what it is fully, okay? I can say entry, exit rules and logic, because my idea was simple, yeah? If it can self-tune, I don't have to tune it myself, right?"
- **30 Oct, T2:788.** "Unit is literally a replacement of a trading bot. It's just a self-configuring trading bot. Simple as that."
- **30 Oct, T2:1125.** "The other things that, you know, are external are this thing of risk management and position sizing. Okay. And I think that's one, a very important session. Okay. Because it's handling the optimization, sorry, the configuration, self-configuration part quite well."

### 2.2 The old relentless system and the Book/BMS: combine them

- **5 Oct, Q5:296.** "Okay, now slots. Most of the old system might be removed, trust me. Most of it. Okay? Slots are very, very, very arguable, I would say, okay? We might not actually use slots. We shall see anyway, because remember there is also the book and the BMS system. Well, literally the book best system. There is also that. That's another beast entirely, okay? That one is not as aggressive as this. That one is more organized. That one brings up the structure, okay? It can engulf this entire thing, I think anyway."
- **5 Oct, Q5:296.** "the reason I said it couldn't lose" [...] "it could lose, okay? Matter of fact, it could very much, depending on the bot you throw at it. But the thing is, this system was meant" [...] "it was meant to be that when it's losing, it controls the bleeding. This concept came from a series, actually, called Billions"
- **5 Oct, Q5:1002.** "something I've noted is that our biggest system or rather our biggest advantage and leverage is in compounding whether I like it or not because if we combine compounding with good hours with okay kill switch obviously has no effect but compounding with good hours with the market intelligence and fast invalidation plus the SQS literally we have a beast of a system on our hands"
- **5 Oct, Q5:1061.** "you did realize that the old systems had what we called clumps. I did re-echo this at the beginning. This is now getting a little bit frustrating. I literally told it through the GPT conversation. Those clamps were literally put in place so that we don't lose money. The same statement I used: control the bleeding. I remember saying this way many times. Control the bleeding. Let me tell you, under normal circumstances, there is no way I'm going to watch my account be split in half, and I'm just watching."
- **5 Oct, Q5:1061.** "If we have bots that perform well, okay, let's give them more risk because we know they'll literally perform. There is a genuine, and I quote, edge. Okay, if there is a genuine edge, why bother on focusing on everything? Let's make sure that, okay, these three slots perhaps are filled with our best performers until we reach a certain threshold that can allow now volume instead of quality. I don't know if you understand me. So instead of us doing quantity together with volume, that is an absurd actually figure that you will get. Okay, and there are so many things there. You're already dealing with something very stochastic, and then you want to add in something that is chaotic."
- **5 Oct, Q5:1058.** "I do believe the risk percentage okay percentage of risk per trade needs to really be adjusted I have a feeling that we are risking way less surely okay we are trading at a volume that is insane but but yeah I do believe we are risking way less okay I do believe it's better if we trade less and more than get more to trade more"
- **5 Oct, Q5:357.** "My view is of 1% is low. Since we are working with a small budget, why don't we put our money where the mouth is, or you get what I'm saying, okay? So in other words, we push for maybe 10%. We multiply it by, let's say, times 10 or times 5. Let's say $5 per trade per scalper"
- **13 Oct, Q13:1113.** "I'm seeing that we have the risk management and position sizing system which we haven't agreed on which one we are going to use. But I think we shall have to create a baseline which is configurable across. The best version would have been the book system. However, the book system is not so suitable for scalpers. Okay, it is, but you get the idea anyway. There is a scalping book."
- **20 Oct, T1:264.** "So the version or the seed idea for QMX started with the movie The Hummingbird Project, okay? Where I was like, I can't beat these guys in speed, obviously, but I can beat them in compounding. So when you look at specifically a scalper, I was like, okay, if I can scalp and make profits over time, obviously I will be able to compound them and with proper risk management and position sizing, blah, blah, blah, blah."
- **20 Oct, T1:444.** "Actually, this is why at first I was making the game of the first system cannot lose. Because also these things were sort of there in the first system."
- **20 Oct, T1:444.** "Now, earlier we had the risk management position sizing system, which handled all these. So the latest system, I think, still uses the book management system, or the BMS, or the book system. Like, it has a lot of names, but it's mostly the BMS."
- **27 Oct, D27:9.** "Let me continue to risk and sizing. Now, this is where I was like, nah, dude. Oh, okay. Ah, wow. Okay, no. Oh my days, bro. Because size column and flow ratchet. Yo. I think the idea for the risk management and sizing, risk and sizing, was combining the two systems, or the best of the two systems. I think this one will need a little bit more conversation, because I can't just look at this and say I've understood. [...] because it's quite special to my heart. Okay, it's very important that we look at it, or I'll go back to an old session and we just continue, because bro, this is very important. One small mistake here can lead to a very big, I mean, it's, sure, it's not self-configurable, but yo, we shall see anyway. [...] Okay, yeah, sure, I'm not asking for diagrams, but nah, I think in a more mathematical sense, and this thing needs taught, a lot of it, all right?"
- **27 Oct, D27:9.** "remember, at the same time, we have a very, should I say, special part of risk management and position sizing, which is in the old system. I believe in the old conversations I gave you, you saw it, that I talked about it, where I was like, it was a bit radioactive, for lack of a better word, which means while judging, we should put that in mind. Okay, we shouldn't just consider how it performs historically, because judging and improvement should come from historical and paper trading."
- **28 Oct, D28:7.** "Because the idea of compounding, when we look at now the risk management position sizing, I know you're not talking about it here, but when you look at, there are so many hybrids we had, I think this very session last week, okay, where we're looking at multiple ideas. Because when you look at the old versions of QMX and then the new versions, there is a system that was very aggressive and compounded. Now, what I'm trying to focus on with the load balancer or the market intelligence system is that compounding thing."
- **30 Oct, T2:908.** "The documents QMX version is very old. Okay, it's mostly had risk management and version sizing parts that I wanted. But most of it is not really that good. Okay, maybe risk management then a minus."
- **30 Oct, T2:1000.** "Because, like I said yesterday, most of what I intend inside the risk management and position sizing, I try to give you some sort of version of what I thought, is we are going to combine the old systems version and then the book version to create a standard one, okay? Because both of them have advantages and disadvantages. The old version is very good at accelerating growth, which means quantity doesn't matter, quality might matter. Depending, because the old version again was taking into account that we were trading 10 FX sessions. Okay, 10, I don't recall, but there are all the FX sessions across the world with like a 2-hour gap. Okay, that's in the old system, which means the new system, rather, which means in the old system, it was very relentless. And in other words, for lack of a better word, an agent once called it nuclear. But the new system is more organized, okay? The one we are having. So the one that uses the book-based system, in other words, the BMS and the book-based system, rather, okay? Now, it's more organized with better rules and stuff like that, but it's not relentless like the old one. So what we are going to try to do is figure out which one, which parts of what are we combining, then we go from there. But remember, your whole job is to leave room for that."

### 2.3 House money, reverse house money and Kelly

- **April 2026, quoted in R19:218-219 (old vault, his GPT conversation).** "it uses a more enhanced Kelly plus other things yeah it is standardized to my own liking" and "an enhanced Kelly with house of money effect fee monitoring and all that because I using sculpting I have to be very aware"
- **5 Oct, Q5:296.** "The reason you are seeing it in all RIB sessions is that we realized that there are sessions where historically we know that there is liquidity, so there are more suitable conditions for us to trade, or for a specific strategy to trade, okay? Or to find a winning trade, okay? So which means we are willing to give it more money because the probability of it actually having a higher, like, return, literally, is more. That's why we are willing to risk more money. However, based off specific conditions, we are also willing to reverse it if we start going in a losing direction. I think that's where Reverse House of Money came in."
- **5 Oct, Q5:357.** "So the house of money, reverse house of money. Yeah, this one, this is the one. It's gonna get a lot of restructuring."
- **6 Oct, Q5:1466.** "Now, house of money and reverse house of money. Actually I never commented on them. Can you explain to me how you are proposing to use them? Because I never understood them so well. I get reverse house of money, by the way, it's bloody brilliant. Then house of money, how does it come in? Because reverse house of money, that one made sense, but are we totally putting out the Kelly? That's another question."
- **6 Oct, Q5:1528.** "Oh, today's winnings, not my best. I almost forgot about that. Wow. So trades get a little bit bigger, but only with money won today. But get bigger how? Anyway, we shall talk about this when we reach sizing. Okay? When we start discussing the sizing design. Because bloody hell, this is going to be an interesting topic. I can't wait. [...] How did you come up with House of Money instead of Kelly? Okay. Oh my God! This is brilliant. This is brilliant. I'm actually laughing. I'm happy. What the... Yo, hang on, hang on, hang on. So you are saying Kelly becomes a ceiling, House of Money becomes the new amplifier, technically anyway."
- **6 Oct, Q5:1528.** "Yo, this Kelly paragraph is actually bloody insane. Now you really are talking about that Kelly is what? You're saying a new bot starts are too thin for Kelly to be trusted. Once a bot has a few hundred trades, approach Kelly. So hang on, I'm a bit confused. You do realize that we trade for on paper trading, rather for two weeks."
- **13 Oct, Q13:1576.** "Correlation is simple. House of money is simple. Reverse house of money, well, you get the idea. So it's simple. Kelly, Kelly is simple. Standard uh, branch. Sorry, standard formula. Then bench, decay. This one is all simple."
- **20 Oct, T1:264.** "So the House of Money, Reverse House of Money, stuff like that. But every part now, I won't say has to earn its job, but it needs to serve a logical thing"
- **27 Oct, D27:9.** "Now, question number four, may size go back? Now, this one I said, I already gave my opinion on the risk management and pressure size. This one needs a little bit more thought. I can't dictate and answer all this in one go. I need to think through this a lot. House of money, same thing."

### 2.4 Exits and stops

- **April 2026, quoted in R19:221.** "a trailing take profit and sort of like a reverse trailing stop loss which moves like the stop loss to break even if the direction is correct"
- **5 Oct, Q5:357.** "In fact, we might have made a mistake of putting stop losses and whatever. Well, I called stop losses and take profits. Don't get me wrong, we can have each trade have a take profit, but a stop loss, I think it's irrelevant now. Okay? Because we have fast invalidation, and I think most scalpers don't use SLs unless I'm wrong. But an SL on a scalper doesn't make much sense. You can correct me there. Like I said, I'm not a trader."
- **5 Oct, Q5:681.** "If it's going to lose the whole 1 R, then why are we having it? Let's take the assumption of 35%. Sorry, 0.35%. And I remember telling you why it's like that. It's not as it's set in stone. None of these figures are set in stone, okay? We are experimenting. Bloody hell, that's the reason it's called an experiment. So expected profit per trade after costs is above zero. Damn, that's a good test, okay? So I can go with that."
- **13 Oct, Q13:1489.** "The exits, yeah. Now exits is where we need to be inventive. I don't think any system really has a clear exit methodology. To be honest, whether it's the old QMX or the new QMX or even the strats or stats none of them have a clear exit methodology. To be honest, all right. So we need to figure that one out."
- **13 Oct, Q13:1894.** "Risk profile and account guard, these ones are easy. Exits are part of a strategy."
- **24 Oct, T1:1177.** "Then exits become a variant access. Yes, exits become variant, entry become variant. QML already has a very big structure, by the way. [...] For God's sake, it has a dictionary. I think the only thing we hadn't added is exit methodology, but that's best of the old system. But literally everything in here is going to be in a strategy."
- **30 Oct, T2:788.** "So entry rules, it contains a lot. Exit rules, it contains a lot with room for expansion, because entry and exit rules, man, they can expand in a way you can't think of, right?"
- **30 Oct, T2:1000.** "For me, because when you say that exits come in 16 unknown families, which is okay, but what is that telling us? It means that the risk management position sizing needs this small. In other words, that session might handle this small. Because why I'm saying this is because of the things that are there, profit targets that change over time, caps, account-wide halts. Now, this is towards the centralized parts, probability-based exits. As you are seeing, most of this is just towards that, whether we like it or not. So this is now the part that literally self-configures most of the time, or, well, we shall see."
- **30 Oct, T2:1000.** "Now, things like stopping and exit rules, I really do feel like that this part really should be part of the risk management and position sizing session. I don't know why, but I don't want to talk about that stuff now because you're going to get me now into math, a lot of it. Okay. There are so many ways we can do a stop and a target distance, a lot. Okay. For us, let's just leave room for that."
- **30 Oct, T2:1000.** "Because now when you start talking about exits, who owns the exit? The old systems were assuming that there is an external piece outside the bot that should own the exits. Because of how we had done the BMS and the book-based system, even in the old system, we were saying that no, exits should be owned externally. But at the moment, obviously we are seeing that the unit is going to own its own exit, rather."
- **30 Oct, T2:1000.** "There are hybrids, it was saying, whereby it was saying, you know, an exit can be used as a trigger and so on and so forth. Those ideas are very important, by the way."

### 2.5 Loss points, the cumulative counter and decay

- **6 Oct, Q5:1466.** "So, the new system, something I'm seeing, the loss points idea is actually brilliant. I think we can indulge ourselves a little bit more with it. Then measuring this thing over weeks, but over weeks. Do you think it's viable?"
- **6 Oct, Q5:1528.** "So loss points, those loss points? Brat? Points need a proper bloody definition in terms of phrase."
- **6 Oct, Q5:1528.** "And but I think for benching, we also need loss points, rather, both of them, benching and loss points. Anyway, all this is in sizing and trust. I'm proposing we do per session, then per day, I believe. Then we have to have some metric we measure, which can alert us that, okay, now this, like, there is decay here. In other words, alpha decay or the strategy can't perform properly. But over how long? Also, that's a question, okay? Because if a bot has a bad week, it doesn't mean it's poor. And then bench till tomorrow. It doesn't trade till tomorrow. I get that. But what if I'm not around for, like, three days? It won't trade, or will it trade?"
- **6 Oct, Q5:1528.** "So eight weeks? Ah, not eight weeks? Seriously? That's a long time. What if we do it per fortnight? We'd want adjust, but also we need to know alpha decay. So yeah. Actually, even you were suggesting per fortnight, literally. But alpha decay and optimization. Remember, there is a part that comes that has maintenance, yeah?"
- **8 Oct, Q5:1671.** "Okay, now three strikes. What we did. Okay, I think you didn't understand me. Okay, three strikes then paper. What it meant is that three total full stops of full stop losses being hit. Yeah, quote me right, please. [...] However, this rule can't really work when you have fast invalidation. You have to account for fast invalidation. Because if a port has the whole day just had first invalidation triggered, you really have to wonder if that bot is performing well or not"
- **8 Oct, Q5:1739.** "so instead of loss points we do accumulative loss counter but then now based off what the question is there the question of based off what is is very very huge okay I mean we are not meant to win every trade [...] if we can minimize how much we lose and we lose a few it's okay the whole point here is not losing money stupidly because we can always win okay but losing money stupidly is unacceptable so we take things in other words I'm trying to bring things that I can't control and you know try so hard to limit how much they have control over the system overall and for things I can control which is the losses I do as much as possible to control"
- **13 Oct, Q13:1894.** "the data lens, yeah, data and DevOps I would say observability logging because we also need to figure out alpha decay. I had not thought through that, but yeah, I'm seeing we might need to understand what alpha decay genuinely should be. And how do agents handle it?"
- **24 Oct, T1:1177.** "Spotting a dying edge, if you look at the old QMX system, I think I gave you access to it last time. It had something called WF3, if I'm not mistaken. Either WF3 or WF5, one of the two, but mostly the WF3. It's for alpha decay. And I think we can also look in how other platforms do the same thing. Then for tightening, never lose. Listen, nothing other than does unit itself controls how it trades. I want to make myself clear. The router never touches a thing. Okay, its whole point is in the bloody name, routing. Alright, but I don't think that's what you are saying. You are saying tighten never lose belongs on the drawdown floor, not an edge. Okay, that this is now part of the risk management and position sizing. So here, I will need a bit of my explanation."
- **27 Oct, D27:9.** "I think now fast stops and slow checks. Ooh. I think this is directly proportional to the quality of the risk management. Okay, not directly, but close. Oh yeah, the lost points thing. I almost forgot about that. Consum on R. Even this one, I think you may need to explain it to me. So decay. Decay, either you or I don't know. Another session. We shall see. But decay is an interesting one."
- **29 Oct, T2:325.** "Then also a nightly decay thing. But I think this does propose multiple workflows, more than one, in fact, because at the same time, man, I'm seeing so many workflows now because I'm seeing there are workflows that can look at actual data, like data for that day."

### 2.6 The book, correlation control and the pod

- **20 Oct, T1:376.** "it means that this bot can literally perform, if it's a good performer, yeah, hypothetically again, it should be able to perform and compound profits across multiple. Of course, we consider correlation, we consider other things, you get me. But if it's performing in EURUSD, it can perform also in, let's say, a Tokyo session, in JPY and so on, even in Sydney, Switzerland, and so on and so forth. I don't know if you're seeing my angle. So it was about breadth in terms of compounding."
- **20 Oct, T1:444.** "No, dude, we have a correlation ledger. No, this is a simple fixer. Simple one, it's actually already there. Okay, it's already there. Breadth, I think, okay, for compounding, there are things we can configure here. Some of these things are not so hard, but you're making a good point, though. I think we should be able to rethink a cleaner way to consider this breadth thing. Because the breadth thing needs to be considered in a way that we need to be able to consider or factor in that the pairs that are registered perhaps are not correlating, or they're not correlating at that time."
- **20 Oct, T1:484.** "So I think you are seeing, I think expansion with domain, if you get domain expansion in terms of instruments, in terms of timeframes, it means you get new variants. And if you have the right systems in place to prevent correlations, to prevent the simple bugs that would come out of such systems, I think the compounding idea comes into play. So now you're seeing why compounding is so much. So the old system kind of considered most of this."
- **24 Oct, T1:828.** "And I think the way QMX is made is the lab, the pod, which means the pod is actually handling most of risk management and position sizing, but in terms of pod, okay, mostly those two areas, but literally portfolio management optimization, like there is that other lens, of course, for the pod."
- **27 Oct, D27:9.** "Bro, remember, you need a correlation ledger here. Most likely, I don't know if you have noticed it, but we need a correlation ledger, a certain one, okay? We need one in the router, whether we like it or not."
- **28 Oct, D28:7.** "Because correlation makes sense. But if you look at system one, correlation doesn't happen. It rarely happens, and it's simpler to do."
- **29 Oct, T2:219.** "Now, 20 markets ranging at once. This is what we have something called the correlation ledger, if I'm not mistaken. It's already existing. Even in the artifacts, you can confirm it exists. Okay, let's say we design a better one because it's a real point of 20 markets ranging at once. It's a real point, which means we can actually now make it part of the MIS, which means we can literally, by the way, it's a better thing. But then the problem is what, you know, the quality of what is inside the MIS. So, in other words, the quality of what's processing information inside the MIS is directly proportional to the quality of output, which means if we say that the correlation ledger is part of the MIS, it means it doesn't, okay, for me, I feel like it's again wrong to put it there. Maybe the correlation ledger can take the output also, all right? Because I believe we can centralize some parts. I proposed this in the other session where I was like, let's centralize some parts outside the unit. Because regardless, we might need some sort of ideal BMS. Okay, because I don't want to confuse you, but we have this system we are using right now. Okay, the one we are building or rebuilding has something called a BMS. But yeah, why I'm saying this, the BMS logic, in other words, you can reuse the BMS logic. Things like now that new skill switch, all that stuff can be centralized, okay? Then also the MIS. Those are the biggest two. So one deals with actual loss cutting. So in other words, most of the clamps are catered for in the other part."
- **29 Oct, T2:325.** "The correlation ledger. Okay. Even the correlation ledger data. Now, again, now I'm seeing that this is something I didn't see earlier. This is, I think, one of the reasons why I've always been so strict on how data is handled under QMX, because I'm seeing this thing whereby I think data collection and data stacking, I would say, is very important, because agents are very good with data, okay, especially if you give them a task. Because when you talk about now the correlation ledger, there are many ways that correlation ledger can be useful."
- **30 Oct, T2:788.** "Obviously, you know, look at how it interacts with things like the book or a BMS. Now, the problem is I don't want to confuse you when I say the BMS, rather. Not the book, the BMS. So in other words, the centralized parts, the BMS, the MIS, which the BMS is just what controls everything else, you know, not controls, but what holds things like the SQS and so on and so forth. You get me?"
- **30 Oct, T2:1000.** "Because a strategy that is trading on 1 minute and a strategy that's trading on 5 minutes, there is a high chance, okay, unless they are not trading the same pair. If they're trading the same pair, that's correlation, okay? If they are, if it's the same strategy, or rather the same unit trading the same pair on different time frames, that's just correlation. I don't think it's different. [...] It is one idea. That's true. It's correlation. It's not too different. I think it's logically, I just didn't see it, but I see it now. It's just correlating."
- **30 Oct, T2:1148.** "The book and correlation control units not stacking the same bit. No, I think this is under risk management operation sizing. By the way, I think you might need to create some sort of file that I might need to go with inside that session for risk management operation sizing, because, bruh, it's necessary."

### 2.7 The account guard and the guards

- **6 Oct, Q5:1407.** "So for you are proposing 40%. I think 40% is a better number, to be honest. We want to give our bots a little bit more room."
- **13 Oct, Q13:1180.** "So it seems like we have some things that we have to put external. Unless I'm wrong. So we either make them external so independent of the bot or we make them fixed values dependent on the bot. Or dependent or independent, whichever, I feel like the bot is still irrelevant."
- **24 Oct, T1:1177.** "For example, the money rule. The money rule, we had a problem with it in time where the agent I was working with when planning QMFV2 was saying, you know, it really fixated on this for a long time. And then, you know, when I broke down the fact that an agent really never accesses money, and it's kind of hard for it to access money, it understood, because bots do the trading. My broker is literally out of QMX. It's in a browser somewhere, which, funny enough, an agent will never figure out."
- **27 Oct, D27:9.** "in terms of the budget and numbers, this does go back to the same bloody thing. There is a problem that I'm finding whereby I'm like, I think we are handling two things at a go. We are trying to handle a portfolio overall, as well as the portfolio configuration. Yeah. And also you're handling live trading as well as strategy development, research, analysis, and curation. Like, I think let's handle one bit at a go. [...] However, when you look at the logic here, if you are trying to set 5%, I get it makes sense, but in the old system, it was okay. But in this new system, okay, there is what I'm trying to point it out. Because when you look at this here, you're realizing we don't want to centralize the pod or the risk management and position sizing. Well, it's not what we don't want. We might need to, depending, because it wasn't set in stone. It's everything that is a suggestion. All right, so it's a suggestion. Now, for me, what I'm proposing is, can we figure out a way in which maybe we have books? I don't know, man. Because I'm trying to figure out a way we can do this. Because I think the book system makes sense. But at the same time, I think maybe... No, not the book system entirely. The BMS alone. Okay? Because when you look at the book, I think, is a little bit overkill for such a system."
- **27 Oct, D27:9.** "Okay, because account guard is outside the unit. I think this is what I'm trying to point out. Then the pod, because the pod is literally the BMS in a way. I feel like it's literally the same bloody thing, but then the BMS already catered for everything in the account guard, so we need to standardize these two. Okay, because I'm back to the unit page, we need to standardize these to the account guard and the pod. Need to figure out, because me, I think it's ideal that we do that. However, in the same way, I think we need an account. Okay, account guard is there. I think it's what I was trying to figure out, but maybe let's combine it with the pod. What do you think? That's an open question to you."
- **27 Oct, D27:9.** "Okay, when you look at just market intelligence part, most of that should be independent of the spread quality sensor, new skill switch, the very, very high parts. Okay, in other words, the account guards. Okay, I don't think these are the account guards, but the guards themselves. Okay, the things that are more like the ones that prevent black swans, or at a low level black swan."
- **27 Oct, D27:9.** "Because if something happens in the router and then the bot, or rather the unit, can still trade, why should the unit stop trading? This is something that is not bothering me."
- **29 Oct, T2:135.** "It means that even a bot that is performing poorly, its edge can be amplified by these other things. So in other words, it can be amplified by the MIS. It can be amplified by the risk management and position sizing system. All right, because you already have things on top, SQS, the kill switches, and so on and so forth, that handle the basic stuff, all right?"
- **29 Oct, T2:325.** "There are lots of things that obviously should be able to stop a bot from trading. Now, this is mostly under risk management and position sizing, but you should obviously know what they are. I assume and we should know what they are."

### 2.8 Small accounts: $300 with one or two units

- **5 Oct, Q5:578.** "if we are able to go from, like, maybe let's say in this scenario that we ran 200 to 500, I would split, then, like, give that, okay, split that capital, then, like, increase the baseline, okay, from 200, obviously, to, like, 300, then that's the new baseline. And then 200 is now to other strategies. So obviously the book is in good hands"
- **5 Oct, Q5:296.** "So the sweep ca Okay, so I got cut off a bit. So I was saying earlier, the ship cup is actually something important, as you will see if you explore deep enough."
- **5 Oct, Q5:1061.** "We give them a perfect outset amount to risk or percentage to risk, the system focuses on those until you reach a certain sweep cap, maybe which can open more locks."
- **6 Oct, Q5:1466.** "I mean, my account is way too small. Do you think it's viable? But then we have leverage, which is something I think I need to talk about with you, or explain to me a little bit more. I get the meaning. I get how it works, I would say, partially anyway."
- **20 Oct, T1:376.** "So intraday and scalpers, but mostly scalpers, to build up a book, then intraday, and eventually shall shift to a spot-only system. That was the plan."
- **29 Oct, T2:135.** "I'm proposing this because it is going to give us a higher advantage. Because imagine if you are able to use a risk management and position sizing system that is suitable, again, to a specific type of trading, which is, for example, scalpers, which means instead of, again, having multiple units trading at a go, you can start with very few, but perform very, very well with proper risk management, position sizing, obviously, which means even at a 300 or a small account, right, you're realizing that done right, 300 can be grown by only one or two units, all right? So me, that's what I'm seeing. It can give us that advantage. But now, what does that mean at a large enough scale? It means at a large enough scale, if we grow a huge enough capital base, we won't have to worry, because positioning now, overall positioning over unit. So in other words, what I'm trying to do is optimize for efficiency and performance."
- **29 Oct, T2:219.** "So it will obviously be variable. Like I said, there should be some sort of centralized parts of this entire system, like the BMS, but not the BMS that we have right now. I don't want to confuse you. Anyway, so 300, if the what I'm seeing is, if the whole budget is 300 and, you know, there are only two active bots, those two bots should be able to use all the 300. That's what I'm planning anyway. Like I said, it's not part of your session, but that's what I'm planning. So it means the more the bots increase, certain variables should be able to configure themselves. That's the whole point of self-configuring. So that I don't have to come and manually do it."

### 2.9 What tunes, who decides, and how to build it

- **6 Oct, Q5:1528.** "What I'm saying is, okay, we do it in such a way that by the time a bot comes to live, it can be more like a, what is it called? A gradient, okay? In that... okay, slope, bloody hell. In that, before it comes to live, it starts slowly, then it continues, it continues. Okay, when it comes to live, rather not before, but when it comes to live, it starts slowly, then continues until it reaches its optimized Kelly. So that can take, like, a month. Bloody hell, it's gonna be a mess to put in the UI, but you get me? Okay? That's my opinion there, because the Kelly placement is brilliant."
- **13 Oct, Q13:1894.** "I think the thing we might need to look at are the actual numbers. But and also, no, no, no, and also the risk management and position sizing system. Yeah, I almost forgot about that. Yeah, that one might need also some stuff. So the unit itself, we haven't agreed on the actual structure. I said I I said the the one you gave me above is a baseline. I never agreed on it."
- **20 Oct, T1:442.** "For me, what I'm trying to paint a picture of is we can also bring in sniping, which means some bots can have specific sniping, which means the risk management position setting there is better if there is proof that it performs. But at the same time, it can also continue trading without sniping on the same pair, and other pairs it can do the same."
- **24 Oct, T1:1177.** "By the way, keep it stupid simple. Design for complexity, not design a complex system. Those are two different things. I always say this, and I think you have this engraved in your memory. Design for complexity means design a system that can handle very hard edge cases, very complex edge cases, things that are tested to its boundaries. In other words, like the 95th percentile or so."
- **27 Oct, D27:9.** "And remember the whole point of having everything here, QML, the unit and so on, is just to have a standard because we are using agents way more. We are actually just calibrating the system for agents, okay, inside QMX. We are not doing this just because we can't write using normal Python."
- **27 Oct, D27:9.** "Who promotes me? I'm the only one who promotes. Nothing else enters live with, nothing actually ever enters live without me. If so, the only time where things enter live without me is when the we used to call it, is it a kill switch? In other words, they stop trading for the best of the risk management positioning rules. Then there it can enter, but it should be monitored and the log, it should be logged. Okay. But initially, no. For any variant, any unit, it's only me."
- **29 Oct, T2:135.** "Maybe the thing I may have a lot of control on is just the funding. In other words, the money part of a unit, the risk management and position sizing system. Now that right there is a very long session. Okay, it's not long actually. I might think about it, but it's I think different, and I would prefer it being different. Okay, not different from this one, but we can design sort of a template and leave it there."
- **29 Oct, T2:219.** "Risk and sizing as a socket. Yeah, I mean, just design. Okay, you should design for that. And as I've given you an idea of what I'm planning for the risk and sizing, you obviously are seeing where I'm going with this. So just leave it. But I think it will, by the time you are done shipping, before the UI, the risk and sizing will obviously be also there."
- **30 Oct, T2:1208.** "I don't think a fresh handoff. I think overall in this entire session, I've mentioned a few things that might be necessary for the whatever, the risk and sizing session. It may be necessary. Okay. For so that, I don't re-echo, because some things I might re-echo or might use wrong wording, and you know how wrong wording has messed us up so far."

### 2.10 His statements that conflict, side by side (unresolved)

**C1. Where risk and sizing lives: on the unit, in the pod, or centralised.**

| On the unit | In the pod, or centralised outside the unit |
| --- | --- |
| 20 Oct, T1:376: "Risk management, position sizing, all that stuff is done on the bot." | 24 Oct, T1:828: "the pod is actually handling most of risk management and position sizing" |
| 30 Oct, T2:788: "It's just a self-configuring trading bot. Simple as that." | 29 Oct, T2:219: "let's centralize some parts outside the unit. Because regardless, we might need some sort of ideal BMS." |
| 13 Oct, Q13:1180: "we either make them external so independent of the bot or we make them fixed values dependent on the bot." | 30 Oct, T2:1125: "The other things that, you know, are external are this thing of risk management and position sizing." |
| | 27 Oct, D27:9: "we don't want to centralize the pod or the risk management and position sizing. Well, it's not what we don't want. We might need to, depending" |

**C2. The Book and the BMS: use it, use part of it, or rebuild it.**

| Date and source | His words |
| --- | --- |
| 5 Oct, Q5:296 | "That one is not as aggressive as this. That one is more organized. That one brings up the structure, okay? It can engulf this entire thing" |
| 13 Oct, Q13:1113 | "The best version would have been the book system. However, the book system is not so suitable for scalpers." |
| 27 Oct, D27:9 | "No, not the book system entirely. The BMS alone. Okay? Because when you look at the book, I think, is a little bit overkill for such a system." |
| 29 Oct, T2:219 | "there should be some sort of centralized parts of this entire system, like the BMS, but not the BMS that we have right now." |
| 30 Oct, T2:1000 | "we are going to combine the old systems version and then the book version to create a standard one" |

**C3. Quality versus quantity.**

| Quality first, few units | Quantity, breadth, every session |
| --- | --- |
| 5 Oct, Q5:1061: "these three slots perhaps are filled with our best performers until we reach a certain threshold that can allow now volume instead of quality. [...] So instead of us doing quantity together with volume, that is an absurd actually figure" | 30 Oct, T2:1000: "The old version is very good at accelerating growth, which means quantity doesn't matter, quality might matter. Depending, because the old version again was taking into account that we were trading 10 FX sessions." |
| 29 Oct, T2:135: "instead of, again, having multiple units trading at a go, you can start with very few, but perform very, very well" | 20 Oct, T1:376: "it should be able to perform and compound profits across multiple. [...] So it was about breadth in terms of compounding." |

The 30 Oct sentence is ambiguous as dictated: "quantity doesn't matter, quality might matter" describes the relentless system. STATE.md summarises it as "quantity over quality" (`STATE.md:145`). That summary may be the reverse of his words. Ask him.

**C4. The same logic on 1m and 5m.**

| 20 Oct, T1:484 | 30 Oct, T2:1000 |
| --- | --- |
| "if you get domain expansion in terms of instruments, in terms of timeframes, it means you get new variants." | "the same unit trading the same pair on different time frames, that's just correlation. I don't think it's different." |

STATE.md records the 30 Oct statement as superseding the 20 Oct seed (`STATE.md:146`). It is shown here because the two can still both be true: a new variant for the record, one bet for the risk.

**C5. Where the correlation ledger sits.**

| Date and source | His words |
| --- | --- |
| 20 Oct, T1:444 | "No, dude, we have a correlation ledger. [...] it's actually already there." |
| 27 Oct, D27:9 | "We need one in the router, whether we like it or not." |
| 29 Oct, T2:219 | "if we say that the correlation ledger is part of the MIS, it means it doesn't, okay, for me, I feel like it's again wrong to put it there. Maybe the correlation ledger can take the output also" |
| 30 Oct, T2:1148 | "The book and correlation control units not stacking the same bit. No, I think this is under risk management operation sizing." |

**C6. Simple or hard.**

| Simple | Hard |
| --- | --- |
| 13 Oct, Q13:1576: "House of money is simple. [...] Kelly, Kelly is simple. [...] Then bench, decay. This one is all simple." | 13 Oct, Q13:1806: "I'm seeing how complex the self-optimizing thing is going to be." |
| 13 Oct, Q13:1894: "Risk profile and account guard, these ones are easy." | 27 Oct, D27:9: "One small mistake here can lead to a very big [...] this thing needs taught, a lot of it" |

**C7. Stop loss or not** (a tension never answered since 5 Oct).

| 5 Oct, Q5:357 | 30 Oct, T2:1000 |
| --- | --- |
| "we can have each trade have a take profit, but a stop loss, I think it's irrelevant now. Okay? Because we have fast invalidation" | "There are so many ways we can do a stop and a target distance, a lot. Okay. For us, let's just leave room for that." |

**C8. Spot only, or every market.**

| 20 Oct, T1:376 | Later sessions |
| --- | --- |
| "eventually shall shift to a spot-only system. That was the plan." | 24 Oct, T1:651 and STATE: futures, CFDs and crypto perpetual futures are being added. Leverage and funding change what sizing must handle. |

### 2.11 Words that have drifted (keep these straight)

- "Unit" is Claude's word from 8 Oct; he adopted it on 27 Oct ("keep the word unit", D27:9). Before that his words were "bot", "algo" and "trading algorithm" (CHECKED, grounding/06 header notes).
- "Radioactive" is his October word for the old system's sizing. It appears in no old file (CHECKED, R19:215). "Nuclear" is an agent's word he repeated (T2:1000). "Relentless" is his own (T2:1000).
- "Tighten, never loosen" is Claude's proposed rule from 8 Oct, never answered by him (CHECKED, grounding/06 §1.4). His dictation renders it "tightening, never lose" (T1:1177) and asks for it to be explained.
- "Loss points" is Claude's term that he embraced (Q5:1466). "Lost points" and "Consum on R" in D27:9 are dictation for loss points and CUSUM on R.
- "Book" and "BMS" are not the same to him: "Not the book, the BMS" (T2:788). "The BMS" also means a future one: "not the BMS that we have right now" (T2:219).
- He never said "pod" on 13 Oct; the word came from the Lab UI (CHECKED, grounding/08 header notes). By 24 Oct he uses it himself (T1:828).
- Dictation slips that recur: "boat" and "port" for bot, "first invalidation" for fast invalidation, "new skill switch" for news kill switch, "pressure size" and "operation sizing" for position sizing, "House of Money" for house money, "sweep ca", "ship cup" for sweep cap, "size column and flow ratchet" for size and floor ratchet (INFERRED).
- "System 1", "System 2" and "terrain" were brainstorming names, never QMX terms (CHECKED, `STATE.md:134`).
- He found the word "exam" "cringe" for a unit's test baseline (grounding/06 §2.2).

---

## 3. Findings beside his words

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/`. G01, G06, G08 are files in `C:/Users/Mubarak/Desktop/QMX/workroom/risk-lab-2026-10-05/grounding/`. Each line says what the file found and how that file labelled it.

### 3.1 Self-configuring

- Three different things get called self-configuration: resizing from a balance with a fixed rule, updating the rule's inputs from completed trades, and changing the policy itself. None of the six systems studied learns sessions, stops and risk together. `research/20-self-configuring-systems.md` §1 (lines 7-13, INFERRED from CHECKED sources).
- A balance going from $300 to $330 at 0.5% risk moves cash risk from $1.50 to $1.65 with no edge learned. That is compounding, not self-tuning. `research/20` §5, "Editable starting values" (INFERRED arithmetic).
- MT5 Wizard's money module is the precedent for a small interface (signal, trailing and money as one expert), but its numbers are not self-calibrated. `research/20` §3 (CHECKED vendor docs); the precedent itself is G06 §1.1 step 7.
- What practice says is safe to adapt on its own: volatility-scaled distances, adaptive indicators with fixed rules, sizing from the unit's own record, and stop rules. Structure changes (which exits, which filters) are the riskiest search and count as tries. `research/35-trading-lens-strategy-anatomy.md` §4.1-4.2 (lines 136-160; sources CHECKED, synthesis INFERRED).
- The dictionary records where a number came from but has no field for how it moves (fixed, scaled, refit, branched by state, learned). All five motions appear in the MQL5 corpus. `research/36-dictionary-vocabulary-census.md` §6.3 and §7 q8 (CHECKED counts, INFERRED reading).
- Nothing in today's code tunes a unit's own risk. House money, reverse house money and per-unit self-tuning are MISSING. `research/18-grounding-today.md` §5, last row (CHECKED by `git grep`).

### 3.2 The old relentless system and the Book/BMS

- The April system's chain: safety gates, a fee-viability gate (net RR at least 1.1), half Kelly, nine multipliers, then the minimum of six caps, then lots. Sizing ended up near the slot cap in practice. G01 §2 (DOC; the derived note is a simulator reading).
- Its compounding: every fill re-bases the next trade; no per-session dollar cap; only the daily loss limit stops the loop. Equity bands set daily limits of 10%, 5% and 3%. G01 §1.1 and §1.3 (DOC; band thresholds MISSING).
- The July Book core forbade compounding between cycles for the Scalper Book and reset equity to seed at each sweep. That pulls the opposite way from the April system. `research/19-grounding-old-system.md` §5 (lines 245-256, CHECKED; the contrast INFERRED).
- The July rule "take the smaller of the book's offer and a trust-bounded, cost-aware Kelly" was left unfinished on purpose. Both legacy sizing systems were later listed as retired. `research/20` §1 and §4 (CHECKED).
- Today's code holds the Book and BMS as shape and grammar only. The sizing ladder is "defined-unwired" and has never sized a real trade. `research/18` §5 (CHECKED, `qmf-risk/sizing.py:1-34`).
- The 5 to 12 Oct session's own sizing proposals ("three weights and one cap", budget-based sizing recomputed per session) were PROPOSED and never discussed again. G06 §2.3.

### 3.3 House money, reverse house money and Kelly

- House money changed owner inside the old system: the 28 Apr decision made it bot-scoped and reset on swap; the later vault spec made it slot-scoped and inherited. The same decision ruled Kelly on paper-trading realised stats, not planned reward to risk. `research/19` §5 (lines 222-230, CHECKED).
- Old values: house money ×1.5 above a P&L threshold (threshold MISSING); reverse house money only in ORB windows (×0.7 at 2-3 losses, ×0.5 at 4+). G01 §2.1 rows 3 and 9 (DOC).
- Equity-curve sizing (house money and its reverse) lowers expected return on a random walk and helps only when a unit's own returns show momentum. Proposed test: measure the serial correlation of a unit's trade R in QMB before switching either on. `research/05-academic.md` §4.4 (CHECKED papers, INFERRED rule).
- Chance of ever touching a kill line 40% below seed, for a known edge: full Kelly about 60%, half about 22%, quarter about 3%. With an estimated edge, shrink further. `research/05` §4.1 (formula CHECKED, numbers INFERRED).
- A one-way "tighten, never loosen" ratchet on a noisy estimate drifts to the minimum size even when the edge never changed. The principled home for a one-way ratchet is the drawdown floor, which can rise with the high-water mark. `research/05` §4.3 and §4.6 (CHECKED paper, INFERRED application).
- The funnel's recommended answer, not his ruling: house money stays off per unit until its own record shows streaks. `research/07-funnel.md:742` and `STATE.md:213` (recommendation; he ruled "not decided", `STATE.md:40`).

### 3.4 Exits and stops

- Exits form about sixteen known families. Five have no dictionary heading: time-varying profit targets (an ROI table), unrealised-profit caps, giveback exits, account and strategy halts, and probability or model exits. `research/35` §5.1 and §5.3 (CHECKED).
- Stops lose money on a random walk and help under momentum or regime switching. So the right exit depends on the context the unit trades. `research/35` §5.2 and `research/05` §5.1 (CHECKED papers, INFERRED consequence).
- No retail platform ships a live "chance of stop first versus chance of target first" exit. Triple barrier and meta-labelling exist in the literature only. `research/35` §7 q4 (CHECKED).
- Where exits live is split across practice: Pine, Jesse and freqtrade keep them in the strategy; MT5 and StrategyQuant make them modules; LEAN puts generic ones at portfolio level. `research/35` §0 item 2 (CHECKED).
- The old system: the SL/TP authority owned all exits; breakeven once at +1R and never trailed; losers ran to the full stop; take-profit extended with no cap. It had no fast invalidation. G01 §3 and G06 §2.1 (DOC).
- His "stop loss is irrelevant" met Claude's case for a wide disaster stop (no stop means no 1R to size from). He never answered. G06 §2.1 (OPEN).
- Fast invalidation's real cost: a 0.35R cut plus 0.1R costs is a 0.45R loss. G06 §2.1 (PROPOSED, he accepted the point).
- MQL5 authors write stops in points (84 articles) far more than in ATR multiples (9). `research/36` §4.3 (CHECKED).

### 3.5 Loss points and decay

- Loss points as proposed on 6 Oct: a full stop costs 1 point, a cut costs its size, a win does not erase points. His own call: count per session, then per day. Bot level, not book level. G06 §2.2 (concept and level AGREED; numbers PROPOSED).
- Old WF3 was "pool cleaning": it read synced journals, scored decay and chose keep, reduce, demote, retire or rehab. There was no WF5. The decay maths was never written down. `research/08-old-qmx-testing-and-decay.md` §2.1 (CHECKED).
- A CUSUM on trade R, with one false alarm per 1,000 trades, takes about 240 trades to notice an edge falling from +0.1R to zero. This corrects the ~1,400 in `research/05` §4.6. `research/08` §0 (INFERRED, formula plus simulation).
- So fast protection must stay rules (loss limits) and slow decay detection must be statistics. Both files agree. `research/05` §4.6 and `research/08` §2.3.
- The recommended decay check is one nightly job per unit journal with four readings (CUSUM, Monte Carlo cone, cost drift, behaviour drift) and three states (OK, Watch, Alarm). It informs; it does not act. `research/08` §2.3 (INFERRED design, numbers configurable).
- Prop firms call a trader down to sim on patterns, never one bad day, and back only on shown consistency. `research/08` §2.2 (CHECKED).
- Today's code has no daily loss limit term. `research/18` §5 (CHECKED, `git grep` = 0).

### 3.6 The book, correlation control and the pod

- Today's "correlation ledger" in the docs is a lineage projection (intent to enactment), not market correlation. A draft hourly workflow computes currency legs, overlap and effective number of bets, but needs the node. No live correlation gate exists. `research/18` §5 (CHECKED; "no live gate" INFERRED).
- The July core named the control an "exposure ledger" door; the BMS correlation ledger he remembers may carry that name. The August STRATS idea was a dated ledger storing method, horizon and regime per pair. `research/19` §4 (CHECKED).
- The old Intent Aggregator resolved opposite intents per symbol in a 50 ms window and dropped intents that pushed portfolio correlation too high. No current file mentions it. `research/19`, "Ideas the old system had" item 1 (CHECKED).
- Pods today are designed only: seven slots, a simulator and a compiler port. `research/18` §5 (CHECKED).
- On 13 Oct Claude proposed "pod = account guard + router, with units inside". He never answered. G08 §2.5 (PROPOSED).
- Same logic on 1m and 5m of one pair is one idea, highly correlated; platforms treat timeframe as a sweepable parameter. `research/35` §6 item 4 (INFERRED from CHECKED platform practice).

### 3.7 The account guard

- Account guard: DESIGNED-ONLY, zero code hits. Kill line, breakeven ratchet, bench fold, the five-level kill switch, the news kill switch and SQS are BUILT but never deployed. `research/18` §5 (CHECKED).
- Single-trade exits are covered in the dictionary. Account-level exits are not: basket profit exits, equity kill switches, daily loss limits, grid take-profit, close-by (199 article hits together). `research/36` §0 item 4 and §4.3 (CHECKED).
- Where account-level exits live (dictionary, the empty risk-and-sizing folder, or house policy outside the dictionary) is an open question. `research/36` §7 q5.
- Starting values from 5 to 13 Oct: $300 start, kill line 40% of seed, daily budget = (equity − kill line) ÷ 5. The 40% was AGREED; the ÷5 PROPOSED. G06 §2.3; workroom `decisions.md:27`.
- The old circuit breakers: a persisted LIVE → PAPER → RECOVERY → RETIRED machine and a separate quality breaker, never wired to each other. `research/19` §5 (CHECKED).

### 3.8 Small accounts

- At 30:1 leverage, 1R on a 10-pip EURUSD stop is at most $8.33 on $300. Spot caps risk at the stop distance. G06 §2.3 (INFERRED arithmetic).
- If the minimum lot forces risk above the Kelly ceiling, skip the trade and count "skipped for size" on its own. Otherwise the record looks better than the real fill rate. `research/05` §4.7 (INFERRED).
- On gold, 0.01 lot with a $3 stop is already 1% of $300. `research/07` F-4 (INFERRED, from 07b §3.3).
- A drawdown floor that rises with the high-water mark makes risk fall near the kill line; set high, it would choke compounding on $300. `research/05` §4.3 (INFERRED).
- His sweep idea (200 to 500, raise the base, send the rest elsewhere) was AGREED as a concept, levels OPEN. G06 §2.4. The July Book's sweep reset equity to seed at a 2.5× cap. `research/19` §5.

### 3.9 What tunes and who decides

- The funnel's small first version: a unit's calibrator tunes three numbers on a schedule (risk per trade in R under a Kelly ceiling, loss points per session with a day cap, session weights), shrinks fast on rules, and grows back only on fresh evidence inside ranges. `research/07` F-4 (lines 252-265; a funnel outcome, not his ruling).
- Loosening after a cut only on new evidence: an e-value crossing 1/α (for example 20) plus a minimum time. `research/08` §2.3 and `research/05` §4.6 (INFERRED).
- The old lifecycle spec held automatic probation and reinstatement steps. Those cannot override his ruling that only he promotes. `research/20` §2, table row 5 (CHECKED).
- Calibration "by statistics first (percentiles, Bayesian ramp, bandits), ML later" was PROPOSED on 8 Oct and never answered. G06 §1.3.

---

## 4. The socket: what the unit planning hands this session, and what it expects back

These are questions, not decisions. Sources: his 30 Oct calls in `STATE.md:144-146` and the seams file `research/funnel4-qml/cis/seams-options.md` §6 (lines 190-226).

**What the planning run assumes it hands over.**
1. The unit owns its exits. The old "exits are owned outside the bot" is reversed (`STATE.md:145`). Is that settled for every exit family, including account-wide halts, or only for per-trade exits?
2. A risk socket that "must take whatever that session designs", with no exit or sizing maths written by the planning run (`STATE.md:145`). Which of the socket shapes does this session need: two ports (exits and sizer), one deep risk module per unit, roles in the logic graph, a policy record per unit, or a library the unit's code calls (seams §6.2, options R-A to R-E)?
3. Room for every one of the sixteen exit families without a QML change, at three scopes: one position, one unit, the whole account (seams §6.1 items 1-2). Does this session agree with three scopes, or does it need others (per pod, per broker account)?
4. Readable inputs for a sizer: entry and stop, instrument facts (tick value, lot step, margin), account facts (balance, equity, open risk), the unit's journal in R, market volatility, and the limits he sets (seams §6.1 item 3). Which of these does the design actually read, and is anything missing (funding, swap, session calendar)?
5. A slot in the journal for risk events: size chosen, size refused, halt fired, exit fired with its reason (seams §6.1 item 5). What else must be logged for the decay check and for him?
6. One automatic transition only: a unit's own risk rule stops it, with no click and no router (seams §6.1 item 6; `STATE.md:39`). Which rules count, and where does a stopped unit go (bench, paper, off)?
7. Every exit and sizer replays the same in QMB and live (seams §6.1 item 7). Which exits need tick data to replay honestly?
8. The execution form of each exit (stop-market or stop-limit, server-side or client-side, last, mark or index price) is carried by the socket (seams §6.1 item 8). Who picks it: the unit, the session's defaults, or the broker adapter?

**What the planning run expects back.**
1. How a unit's risk numbers move: which move, from which journal data, by what rule, how often, inside what limits, and which stay fixed (seams §6.1 item 4). The same "motion and authority" question is open for QML parameters too.
2. Whether the unit or a sizer module emits the size, given today's code law that "the bot may not size" (contradiction C-Q1, `research/funnel4-qml/cis/problem-solving.md:346`).
3. Whether a moved risk number makes a new unit version or stays the same unit (C-Q10, same file line 355).
4. Where a unit's editable numbers live so the UI can edit them (C-Q3 and C-Q11, same file lines 348 and 356).
5. A default exit set for a source that states no exit, so an "entry hypothesis" can become a unit (C-Q4, same file line 349).
6. The shape of the account guard and pod, and whether they are one thing (`STATE.md:76-78`; funnel round-2 question 1 at `STATE.md:220`).
7. How the budget splits when System 1 lets one unit trade many matching markets at once, and when units are added to a $300 account (his words in 2.8).

**What QML must not do** (seams §6.3): fix any number, threshold or formula for exits or sizing; keep "the bot may not size" for units without this session's say; make the socket depend on the router, the MIS, the PC link or the Library at trade time.

---

## 5. What is stale in `HANDOFF-RISK-SIZING.md` (written 27 Oct)

Line numbers refer to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/HANDOFF-RISK-SIZING.md`. That file is not edited here.

1. **Paths (lines 3, 9).** It points to `D:\QMX-worktrees\agent-system\tracker\risk-sizing\`. Planning moved to the `D:\QMX-worktrees\unit-plan` worktree on branch `plan/unit-system` (`STATE.md:121`). The agent-system copy of `STATE.md` was last written 28 Oct 22:18 and is 33 KB; the live one is 59 KB (CHECKED, `ls -la`).
2. **"It outranks everything else" (line 9).** It names the 27 Oct round only. The 29-30 Oct round is also binding and newer: code first, numbers later; broaden before defining; everything he says is a seed (`STATE.md:112-122`).
3. **The two systems to combine (lines 23-25).** It says the old system plus "the new self-calibrating unit". His 30 Oct words are the old relentless system plus the Book version, the "BMS and the book-based system" (T2:1000; `STATE.md:145`). The self-calibrating unit is where the result lives, not one of the two systems.
4. **Wrong pointers (line 14).** "F-5 (unit sizing), F-14 (new cells start small) and F-15 (house money)" do not match `research/07-funnel.md`. F-5 is trust against the exam baseline; there is no F-14 or F-15. Unit sizing is F-4 (line 252); new variants starting small is C18 (line 103); house money is C12 (line 97) and D15 (line 419) (CHECKED by grep).
5. **"Read these, not the raw transcripts" (line 15).** Standing order 3 and the 29-30 Oct ruling now require his verbatim words. The raw 5-12 Oct and 13 Oct transcripts are on disk (Q5, Q13) and are quoted in section 2.
6. **Research pointer without its correction (line 12).** It sends the reader to `research/05` §4. That section's CUSUM table (~1,400 trades) was corrected to ~240 by `research/08` §0. Line 31 already says 240, but the pointer does not warn.
7. **Scope added since (lines 22-36).** Missing: exit methodology, stops, targets, time-varying targets, profit caps, account-wide halts and probability exits; the book and correlation control (units not stacking the same bet); a $300 account with one or two units using its whole budget, and variables reconfiguring as units are added; the socket (`STATE.md:145`, `STATE.md:152`; T2:219, T2:1000, T2:1148).
8. **System 1 (written before 28 Oct).** It does not know that one unit may trade many matching markets at once, picked by the MIS (`STATE.md:107`). That changes what the budget split and correlation control must handle. Nor does it know that 1m and 5m on one pair is one bet (`STATE.md:146`).
9. **Recommendations framed as topics (lines 34-35).** "Whether size may grow back after a cut" and "house money switching on only when a unit's record shows streaks" are Claude's recommended answers (`STATE.md:212-213`). He ruled both "not decided" (`STATE.md:40`).
10. **"The aggressive 'radioactive' sizing: session capital, house money, reverse house money, compounding across sessions" (line 24).** His 30 Oct description adds the parts that define it for him: relentless, every FX session (about 10, two hours apart), accelerating growth (T2:1000). "Radioactive" is his October word, not an old-system term (`research/19:215`).
11. **Old-system sources (lines 15-19).** It lists G01, G02, G06 and G09 only. `research/19` §5 corrects G01 and G09: house money was first bot-scoped, Kelly was first ruled on paper stats, and the July Book forbade compounding between cycles.
12. **The explainer page as a done condition (lines 20, 52).** On 30 Oct he said "No need for an explainer site. No need. Okay. Let's keep everything in chat for now." (T2:602). That was said about the planning run; whether it holds for this session is his call.
13. **Missing guidance on wording.** It does not carry his warning about reworded words (T2:1208) or point to this pack as the source of his words.
14. **Still current.** The Kelly kill-line figures (line 33), "design for complexity, never a complex system", "agents never touch money", "only he promotes", "local first" and "nothing limited by default" (lines 39-43) all still match `STATE.md`.

---

## 6. Questions moved here from the unit planning (2026-10-30, scope revision)

His 30 Oct ruling put the book, correlation control, the pod and the account guard in this session. The unit planning had research and grilling tickets on them, written before that ruling. They are closed there and carried here as open questions, word for word from the tickets. The unit planning keeps only the socket (§4) and what a unit records for this session (readings stamped at entry and exit, results in R).

**From the correlation research ticket** (`wayfinder/tickets/research-correlation-and-bets.md`):
- What should a correlation control measure: currency legs, return correlation, a shared context label, dated by method and horizon?
- On a day when 20 markets match one unit's context, how many independent bets are there by pairwise correlation, by effective number of bets, and by shared label, and do they agree?
- Is a simple bet counter (units entering on the same label within some minutes count as one) as safe?
- Which of the correlation controls he remembers existed, and in what form? Start from `research/funnel3/cis/problem-solving.md` knot (c) (six eras, ten options), `research/19-grounding-old-system.md` §2 (the Intent Aggregator) and §4, the draft `rk2-correlation-drift` template and `qmf-risk` `door.py:315-347` on `origin/engine/base`.
- Settled on 30 Oct, not open: the same unit on 1m and 5m of one pair is one correlated idea, not two bets.

**From the correlation-control grilling ticket** (`wayfinder/tickets/correlation-control.md`):
- Which correlation jobs QMX needs now: a funding gate, a sizing multiplier, a per-tick conflict resolver, an exposure ledger, a dated pair record, cohort correlation in judging?
- Where each runs so it works with the router and MIS down and never stops a unit only because they are down.
- Does the name "correlation ledger" keep the docs' meaning (order lineage) or his?

**From the pod, guard and shared budget grilling ticket** (`wayfinder/tickets/pod-guard-and-shared-budget.md`):
- Combine the account guard and the pod, or keep them apart? What is the "ideal BMS" he means, as opposed to today's?
- Is the book per account, per broker, or across every account?
- The unit sizes itself, yet two units on $300 "should be able to use all the 300" (T2:216): does a unit size inside a share a central part allocates, negotiate its share, or own all sizing with the guard only stopping it?
- When units compete for one budget: first setup wins, or a ranking?
- Which stops belong to the unit and which are central (kill line, daily loss, account floor)?
- Does the news kill switch sit in the MIS, in the ideal BMS, or beside both as its own guard?

**From the $300 research ticket, sizing half** (`wayfinder/tickets/research-small-account-universe.md`; the broker facts half moved to research 32, which this session can read for minimum lots, money per point and margin):
- With $300, which instruments can a unit trade at safe risk at the minimum lot, per venue?
- Can one unit hold more than two or three markets at once at safe risk?
- Does trading breadth amplify a weak edge, as he says, and how would that be shown (the fundamental law of active management; Kelly with many simultaneous bets)? Contradiction C36: grow $300 with one or two units, or compound across breadth.

**From the judging research ticket** (`wayfinder/tickets/research-quant-judging.md`):
- How is the old "radioactive" sizing (enhanced Kelly with house money) replayed when judging a unit? The unit planning's research 26 notes only what QMB must record so this replay is possible later.

## 7. The build's placeholders (added 2026-11-01 by the unit system build plan)

The unit system build ships stand-ins for sizing, exits, halts and the kill switch, each labelled `origin: placeholder` and never refused. `build/RISK-SIZING-PLACEHOLDERS.md` lists all 31, with where each sits, the PR in `build/UNIT-PLAN.md` that puts it there, and what this session must replace or decide. Once the build lands, `tools/qml/placeholders.py` lists every published unit and binding that still uses one, and a replacement block must pass `qml/tests/test_socket_contracts.py`.
