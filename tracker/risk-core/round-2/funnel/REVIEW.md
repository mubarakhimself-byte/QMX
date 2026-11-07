# Independent review of the round-two funnel

Opus reviewer, 7 Nov 2026. Target: `round-2/funnel/FUNNEL.md`, `FATES.md`, `QUESTIONS.md`. Written under `round-2/BRIEF-COMMON.md`. Skill: `bmad-review`, run headless, one mind, lenses adversarial, edge-case and verification-gap. The funnel has no running code, so the verification-gap lens was applied to the claims and tests it relies on.

No dollars were simulated. Nothing below ranks an idea by survival or growth. Paths are as in the funnel's own header. `F` is `FUNNEL.md`. Code is `D:\QMX-worktrees\bld-repair-24` at `351e7521`; the funnel's line numbers came from `255f3bbf` and those I checked still hold.

**Verdict.** The funnel is a sound basis for the architects after the fixes below. The method, the quotes and the code reading hold. Its weak points are these: it says the core is cut when it is not; the baseline has never been walked from zero history; a build reading only sections 3 and 4 misses parts the funnel itself calls core; and four of the five forks are already decided by the core list.

---

## Must-fix

### M1. The "one bump" claim is overstated, and it is written as an invariant
- **Where:** V12, D41, C25, Q5, Appendix A, Appendix B story 1.
- **What the code says:**
  - The rule at `compiler.py:100-101` reads: "Bumped by any compiler change that alters a decision". Lifting a refusal changes no decision for any unit that compiled before, because a refused document never compiled. So Q5's "Every socket widening changes the compiler format" is false as written.
  - The format has already bumped in R04, R05 and R06 (`git log -G` on the constant), three slices apart, at no cost. Nothing was deployed.
  - The cost exists only for deployed units (`runtime.py:559-565`, `:2756`). `E5:478` says so: "unless units aren't yet deployed". The funnel keeps the "before any unit deploys" half but makes "one bump" the rule.
- **It also contradicts itself.** D6 and Q1 say step 3 (trails, partials, signed stop) waits on R24's demo facts, and 4.1 says trails "arrive with step 3". So trails land after the bump the baseline depends on. If a unit is on paper by then, the invariant is broken on the first planned follow-up.
- **Consequence:** a builder reads V12 as a big-bang change of about 69 rows in one compiler version. That is the opposite of small verified PRs, and C25 marks it "resolved". Meanwhile the real long-term cost is left as "content": every future format bump means a new test record for each of 200 units (D41 "re-test workflow per bump (content)").
- **Smallest fix:**
  1. Drop V12 as an invariant.
  2. Replace it with a sequencing note: "Bumps are free until the first unit deploys, so land sockets in slices. Bump only when a compiled decision changes. Step 3 is either before first deploy or pays a re-test."
  3. Move the re-test workflow to core: by the brief's test, its absence is what freezes the compiler later (Appendix B's own story 1).
  4. Rewrite Q5 (see Q section).

### M2. A pod edit can change live risk without his click
- **Where:** D31 ("A pod may change a unit's sizing rows at an anchor without a new unit identity (core seat)"), I10, I9 (two fingerprints), F1 Shape B ("one edit rolls out by pin"), 4.3 "pod patch" by the copilot, against V4 and V3.
- **Evidence:**
  - The node trusts one thing, the compiled fingerprint its G record tested (`compiler.py:1072-1079`, `runtime.py:2756`).
  - A pod outside that fingerprint is, by design, not re-tested.
  - D33 itself says "a guard changes which trades happen". The funnel never says what a G record tested once logic and pod split, who may move a live deployment to a new pod version, or whether the copilot's pod patch can reach a running deployment.
  - D17 says agents write "never on a running unit", but a pod is not a unit.
  - The funnel's collision list has no row for this.
- **Consequence:** a fixed line ("only he promotes", "agents never touch money") has a side door, and it is the very seat added to spare 200 re-proofs.
- **Smallest fix:** add one rule to S14 and V4: "Changing the pod version pinned by a live deployment is a click bound to that pod's hash; one click may cover many members; agents and the copilot write drafts only." State that G tests the logic fingerprint, plus that the pod's blocks passed their own checks. Add it as a collision row and as question Q6.

### M3. Section 3 is not the whole core, and the build reads section 3
- **Where:** H-133 says stage 6 "reads sections 3 and 4". F section 3 says "THE CORE LIST". But these are called core elsewhere and have no row:
  - D40: identity table wired, forwarding map, plan before change, rollout field, self-test card, rip-out check, spec and status generation stamp.
  - D5: feasibility verdict.
  - D49: working templates (partly in 4.2).
  - D50: module map, contract tests, `EXTENDING.md`.
  - D43: protected field list.
  - D45: the block face check.
- **Evidence:** a search of F lines 257-359 for feasibility, forwarding, identity table, plan before, rollout, self-test, rip-out, generation stamp, override chain and protected field finds nothing.
- **FATES breaks its own definition.** Its "core" must name a section 3 row, yet many name none:
  - `H3-T48/T49/T50/T54` and `E2-gap10` say "core D40".
  - `H3-T9` says "core D36".
  - `H3-T16`, `X0-44` and `X1-H37` say "core (keys reserved)"; the eleven-key override chain appears nowhere in section 3.
  - `H3-T42` says "core 'unit parts as a list'".
  - `H3-T51` and `H4-I-23` say "core rollout field".
  - `H5-45` says "core status expiry".
- **Consequence:** the placeholder swap with a record is the session's central job, and its mechanism (SWAP E16, identity table unwired) is not on the list the plan is built from.
- **Smallest fix:** add one row, "Identity and swap: table wired, forwarding map, which swaps keep which record". Add one row for the feasibility verdict. For the rest, either add a row or demote the word "core" in D and FATES. Then run a script: every "core" in F and FATES must name an existing row.

### M4. The baseline has never been walked from zero history
- **Where:** 4 ("It trades on paper with nothing set"), 4.1, 4.2, K7, C42, C23.
- **On by default, and each reads data that does not exist at the first tick:**
  - Own-percentile bench (template A and B): no trades, so no percentile.
  - Fast-invalidation cut "read from the winners' MAE": no winners.
  - Portfolio day stop "reading the book's own sized sigma": no sigma.
  - Parent limit on losing together: no co-movement record.
  - Cost hurdle: only the stressed, pooled fallback.
- **A deadlock:** D19 and REVIEW M7 say the gate refuses a small-stop scalper at most hours "until fills exist". C42 calls that "resolved" with the same stressed default that does the refusing. No entries means no fills, no fills means no calibration, so the unit refuses forever. Would-have rows (R3) do not create fills. Pre-mortem story 2 sees the symptom, and its only answer is to write R3 early.
- **Missing values:** V8 says every value is a labelled default, and section 4 says it depends on "nothing that waits for the numbers talk". But section 8 parks the fraction, floor, base, halt limits, cost allowance, SQS floor and parent limit. "Trades with nothing set" needs some number in each. Nobody is named to pick them. M50 asks for "something that can work even if we don't have the numbers set yet".
- **Smallest fix:**
  1. Every on-by-default block declares its cold behaviour as a row (`until_n: warn | shadow | fixed fallback`).
  2. The shipped hurdle only warns while its cell reads `uncalibrated`.
  3. State that the builder picks labelled placeholder values, reusing the existing placeholders where they exist, with no argument and owner `numbers talk`.
  4. K7 must run on a store with zero trades and zero fills and must end with a filled entry.

### M5. A model's results chose defaults: the same failure as Friday, in smaller form
- **Where:**
  - `FATES` `E5-size-test`: "Own-record press: large gain with runs for a scalper, loss for swing... template A press on (day anchor), B off | MODEL".
  - F 4.1 Numbers row, "Why this one": "`E5`'s test: stacked, they held across every world tried".
  - D16: "Shipped default: find, track, correct".
  - `E5:498`: "Recommendation moved from S to S+M1", from a results table across styles and worlds.
- **Against:** the brief lines 36 ("A simulation may only test that a mechanism behaves as described") and TIMELINE 6.2. That turning point was a modelled result deciding tiers. These tables are not in dollars, but they do rank by outcome.
- **Also false:** Appendix B first principles says the baseline is "the smallest set of blocks that fills every socket with something BUILT or REAL". Section 4.1 and 4.2 ship several things that are neither:
  - Cost hurdle: PROPOSAL.
  - Fast-invalidation cut: MODEL.
  - Percentile bench: MODEL.
  - Day stop: MODEL.
  - Motion stack: MODEL.
  - Cushion on: MODEL, and D13 says "no gain on independent trades".
- **Smallest fix:**
  1. Delete Appendix B's sentence, or make it true.
  2. Give each default a configuration reason: "needs least, explainable, has an off switch".
  3. Cite the E5 tables only as "the mechanism behaved as described and did not run away".
  4. For the scalper press, write "on because he asked for it (M5, M39, M50), value open", not because of a model gain.
  5. F2's architects must not treat `E5` as having settled it.

### M6. Compiler refusals in the walks that no core row lifts
Checked in `compiler.py:896-961`. F section 3 has no mention of the following, and neither does anything else in F that I found by search.

| Refusal | Line | Walk it breaks |
|---|---|---|
| `streams_not_built`: one stream only | `:898-899` | Template A says "1m and 5m bars"; any unit reading two timeframes; M10's macro and micro structure |
| `settings_not_built`: no per-market number (SWAP E5) | `:944-957` | Gold and FX in one scalper with different stops; ORB numbers per open. 4.3 lists it as locked "until the sockets land", and no socket lands it |
| `roll_not_built` | `:938-943` | The futures week. I4 lists "roll rules" as a record field, but the compiler refuses the unit's `roll` |
| `context_not_built` | `:907-912` | `E4 L11` lead-lag's second instrument; FATES says "core... `context_needs`" |
| Exit scope (SWAP E3, `:472-477`) | | D7's basket cut; FATES `H2-I75k` calls it content "no core change" |
| Motion inputs and constants (SWAP E12, E18) | | "How it is derived" for anything beyond `{strength, r}`; CONTRACTS' "all editable" |

- **Also wrong:** 3.6 lists "target-position curves" as arriving with "no core change", yet D48 says they need "a per-bar sizer update and partial closes". SWAP 1 says the sizer has no per-bar update, and FATES `E4-L07` calls the answer type core. S1 and S3 do not carry it.
- **Also wrong:** the node's gate `runtime.py:1102-1106` refuses any order whose venue stop it cannot prove. S and I do not list it, though SWAP 11 says the no-stop widening touches compile, `enter`, handler and node.
- **Smallest fix:** go through SWAP sections 1b and 2.4 row by row. Each refusal gets a core row, a named "stays refused, here is why", or content. Add this as a check in D50's census (the census test already exists).

### M7. The fleet watch is "resolved" but unowned, and an app cannot do it
- **Where:** C17 "resolved"; D44 "the shipped watch (content...)"; 4.4 "It does not need him to watch it"; 3.6 lists it as arriving later; 4.1 has no fleet row; section 8 gives the doors to the agentic upgrade.
- **Evidence:** the capability check at `qmx_apps/supervisor.py:891` handles only `market` for `data_reads`. `E5-app1` to `app4` are all open gaps or UNKNOWN.
- **His words (M49):** "Why would I have to be there monitoring units?... As a mini app also." This is his loudest complaint, and his fix is deferred to a session that has not been planned. Until then the shipped decay job is the only watcher, and the funnel itself models it at about 91 cards a night.
- **By the brief's test:** if an app cannot read journals or land a card, that is a socket, and leaving it out forces rework.
- **Smallest fix:**
  1. Add the app read door (journal and fleet read) and the card-landing path to K2, as core.
  2. Name who builds the first scripted version (one ranked row per unit, no agent) in this build.
  3. Change C17 from "resolved" to "answered on paper; ships with X".
  4. Switch off or replace the shipped decay rule at the same time, or 200 units get about 91 cards.

### M8. He told us to look at the UI itself, twice over, and pods were designed without it
- **Where:** H-118 "not held by this funnel", handed to the UI session; `E2-UNK` "UI not run"; Appendix C.
- **His words (M49):** "You don't even, I highly doubt you even know what a pod is... I told you to look at the UI by looking at the UI itself, not the code... Spawn up the server... You didn't do that. Disappointed again."
- **The problem:** the funnel is honest about the gap but then decides S14, D32 and D33 and the pod vocabulary anyway, and F1 goes to architects on the same blind ground. `MAP` says "The UI is a demo", which is exactly what he said to go and look at. His viewpoint is that the UI's own pods are the reference.
- **The brief's out-of-scope line is on the UI *build*, not on looking.**
- **Smallest fix:** one agent starts the demo, reads the Pods, Lab, Portfolio and notification screens, and writes a short note before stage 4. That note goes to the F1 architects and may correct D32 and D33.

---

## Should-fix

### Fidelity
- **S1. His circuit breaker is not in the baseline, and coverage says it is.** H-57 reads "D10 two-speed; 4.1". Section 4.1 and 4.2 hold no circuit breaker; `FATES H2-I48` says "content". The seed reads: "The old circuit breaker is the baseline, improved" (`SEEDS-2:800`), from M10: "it's a baseline improve it, please", "It was a big break. One of the biggest". Fix: ship the two-speed block in the template (off or on, with reason) and correct the row.
- **S2. His "I think" is recorded as a ruling.** The legend says RULING means his words, but these rows overstate:
  - `E2-sense2`: 'RULING ("I think", M51)'. M51 opens that passage with "I think, I did not say it is".
  - `H4-I-67c` and `X7-H24`: 'RULING (M49 hill climb)'. M49 says "More of a hill climb challenge. To be honest, I don't know."
  - `E2-Pod9`: RULING (M51). M51 adds "keep this aside".
  - `E2-Pod15`: RULING (M50). M50 says "These are all just ideas".
  - `H1-3`: RULING (M10 accepted it). M10 says most of it "is what I think".

  Fix: add a label `HIS THOUGHT` and use RULING only for direct decisions.
- **S3. A remark became a core seat.** I10 and D31's "pod changes sizing rows at an anchor without a new identity" comes from "at 5,000 the math changes" (M51), which he asked to keep aside, and `H2-I27` rates it GUESS. It is also what opens M2. Keep the seat only if M2's rule is added. Otherwise make it a new version.
- **S4. "Live trading" is dropped for a newcomer.** M49 says "use tomorrow to have their own system trading up and live trading". D49 and K7 stop at paper; the installer and launcher go to a release lane with no plan. V2 and V4 say "his hand" where a stranger has no "him". Fix: K7 ends with the owner's promote click on the fake broker's live lane. Reword to "the account owner's hand".
- **S5. "Amplify" is quietly dropped.** M10 says the system should "carry or amplify the load... a low one will get a buffer and a high one will get even a bigger buffer". C10 "resolves" this by saying the default needs no edge; H-29 cites no mechanism, only "no choke law". Fix: say plainly it is not delivered by the default, and name the seat and first block that would (no value).
- **S6. "His M51 frame" oversells the cost hurdle** (D26, 4.1). M51 is about observing costs and not trading an instrument on its news day. He never asked for a per-trade R hurdle, which is the agent's proposal (E1). Reword to "fits".
- **S7. C5 and D22 state readings as facts.** "The old question meant..." (C5) is an inference; label it. "A morning list, never per trade" (D22, C41) is a law drawn from a simulated lag ("about 4 to 5 hours... simulated"). Against M5, where the MIS "act[s] like a router". Say "by default; a per-trade read is expressible and warned".
- **S8. D32 retires Book and BMS while saying he need not decide.** D35 and C15 say "decide later" and "kept open, his"; M10 said "the book is the right skeleton", M49 said "decide later". Q3(a) still takes retirement as the default. Remove that clause.
- **S9. His direct questions have no plain answers on file.** He asked: "What exactly is a starting level?"; "What do you mean by unit stepping down?"; "Why lots?... explain to me"; "What do you mean by a rule I approve?... let's first talk about it"; "At 1 unit .83, typical end is 1,400. After how long?"; "my scalper may not exist yet" (all M49). The funnel routes each to a row. RVOL, MIS and ORB get answers; these mostly do not. Fix: a short list for the walkthrough page.
- **S10. M50's flagship walk is oversold.** D37 says "His futures week runs on these roads". Q2's default is no futures route; `roll` is refused (M6); M51 says the copilot can't just take raw video; methodology does not exist. Say "this is what remains before it can run".

### Rigidity
- **S11. V5** ("The true floor is never reset by a restart or a banker act") is a law not on the fixed-line list. It presumes a floor exists, while D3 says the floor is the user's, E2 Pod 20 has none, and "banker act" is unexplained. V9 says only fixed lines refuse. Fix: "A floor, if set, survives a restart; only the owner changes it."
- **S12. V7** forbids a unit that depends on a reading or desk at trade time; D37 says "A stopped desk stops nothing". An unusual unit may want "no reading, no trade". It is also what kills two fork shapes (S20). Fix: every shipped template stands alone, and a unit may declare `fallback: stand aside`.
- **S13. S1 forces every base to answer in dollars at risk.** A fixed contract count ("one micro"), a notional or leverage target (Pod 18, perps) and a no-stop unit have no natural dollars-at-risk. Crypto accounts may not be in USD. Fix: the base answers a typed amount (money at risk, notional, or quantity), and the one converter reads the type.
- **S14. V3** says agents never "place" with no qualifier, but D43 allows anything in a sandbox and M10 wants agents acting as traders. The fixed line is about money. Say "on a live account".
- **S15. H-27** "a blank blocks the live click only" is a refusal outside the fixed lines, and V9 says those warn. Pick one.
- **S16. 4.1 "for every unit" against the canary** ("fixed money per trade, one position, kill only", 4.2). A heading mismatch, but a stranger's first run is the one with no brakes. State it on purpose or fix it.
- **S17. `unknown` and "stale calendar fails closed" have no stated verb, restore or card** (D27, D29, 4.1). A dead free calendar then blocks every template unit that "tolerates none", contrary to V7 and "sitting duck", with nobody told. Fix: `fail` is a row; the default is a card and `prefer not`, and the kill switch keeps the hard kill.

### Too much machine
- **S18. 69 rows, and 560 of 1,496 fate rows say core** (FATES counts). Appendix B says each row "met a deletion test", but no test is on file. Applied strictly:
  - **Move out (additive later, no rework):**
    - S19 check layer.
    - I14 expectation at birth.
    - R12 lineage (methodology).
    - R14 isolation accuracy (a query over R3 and S10).
    - R16 recipe kind (D45 itself says recipes are content) and all block-entry fields. `block_fingerprint` hashes only `block.py` (`loader.py:81-83`) and the lock row holds id, version, fingerprint and weights, so those fields do not move compiled fingerprints. This closes D41's and Appendix C's UNKNOWN.
    - K4 twins (S14's side key leaves the room).
    - D40's rollout field and self-test card.
    - V8 and V11 (principles, not invariants).
    - V12 (M1).
  - **Merge into one mechanism:**
    - S6, S7, S9's pass or refuse, S10 and K1: one ordered entry chain, where each link answers pass, shrink or refuse at a scope. Today five things can do that.
    - S4, S5 and S12's `restore` and `guard_statistic`: one control row.
    - I11 and I15's size band into S2 and S1.
    - I12 into I1.
    - I8 into S8 (agent evidence is a reading).
    - K3 into S8.
    - R5 into R9 (one fold).
    - R6 into R2.
    - R10 into R4.
    - R15 into R1 (D42 already says it).
    - Cost cells appear in both I2 and I4.
    - K6 is a grab bag; split it into S16, S5 and I10.
  - **Result:** about 35 rows with nothing lost. This also tests "Design for complexity" (M8).
  - **Conflict to settle:** FATES `E1-A1-20` says "gate can't size (S2 only sizes)", while S6's verb list includes `shrink`.
- **S19. S15 misreports today.** Its "Today" cell reads "Lab simulator designed, unbuilt; guard package missing". But QMB and the node already drive one handler, `UnitSliceHandler` (`runtime.py:1587`, SWAP 2.5, 2.6). So the "new small core, four drivers" may be a second core beside a working one, which is the two-worlds trap D50 warns about. No Lab package exists to import it (`qmx-agents/packages` listing). Fix: state widening and extracting the existing handler as the first option. D5's row-level contract also needs trimming: D8 lists about 18 attributes against "R9's nine" (H-51). Require a few and default the rest, or a newcomer's brake is a form.

### Forks
- **S20. Only F5 is still open, and it only partly.**
  - **F1 is decided by the core list.** D33 and S14 carry "empty pod = the unit's own blocks", placement per row and a pod reference on the deployment. That is Shape B's text. V7 rules out Shape C ("a unit no longer stands alone").
  - **F2:** D16 ships Shape C and 4.1 depends on it.
  - **F3:** I6, S6 and S8 are Shape B, and V7 rules out Shape C.
  - **F4 is plumbing** (which file holds status), against the funnel's own "shape, not plumbing". Its one structural part is where the core library lives.
  - **Missing real forks:**
    1. Core size and delivery: everything at once against a small core widened in slices (M1, S18).
    2. Node execution at 200 units: one `node-runtime` thread (`runtime.py:2157`) against several, and how a group stage works across two nodes or two brokers (PC plus servers). E2 rt4's "a pod lives on one place" meets the default group row and `account-daily-loss-halt`.
    3. Entry chain as one mechanism or several seats (S18).
  - **Fix:** mark the core items that presume a shape as "if F1=B", or tell architects they may strike them. Replace F4 with fork 2.

### Holes from the walks
Full walk table below. Beyond M4, M6 and M7:
- **S21.** Venue capability is not on any record: partial close, amend, hedging or netting, minimum stop distance, order types. Only `book-or-quote` is there (I4). A unit needing partials compiles and refuses at the node (`runtime.py:1807-1808`). Add it to I4, and check at compile.
- **S22.** Swap with an open position and a record: which block governs the open trade; rows where `r_after_costs` holds no costs (SWAP E13) while motion reads that field (`engine.py:124`), so fixing the field shifts calibrated numbers; a time-exit fix changing old rows' meaning. Add to M3's row.
- **S23.** Restart: an anchor passed while down (does the restore fire? does the day counter roll?); stickers that expired while down; five states and the cushion ledger rebuilt. V5 is the only line; only `risk_stop` has a restart test (SWAP 23). Add a "catch up at start" rule to the fold.
- **S24.** Guard failure: K1 and V1 cover "guard, sizer, read or fold", not a faulty *exit block* in the new stack, or a hung group stage, or `RiskState` UNKNOWN's effect on entries. S15's single `decide` puts entries and exits in one function. Fix: exits take a separate path from `decide`; a faulty exit falls to the next rank, then `_close_scope`.
- **S25.** The group default `on_fire: stand_down(all) + card` has no restore in 4.1, so it waits on a card, which is him monitoring. State a rule.
- **S26.** Readings have no publisher check: `source: app:mis` can be written by any app or agent. S8 and K3 need the host to stamp the source.
- **S27.** The new-fact path: a new brake needing a fact outside D2's list is a core change, against "one folder, zero core edits" (`H3-T19`). A stdlib block also bumps the money app and needs his signature (SWAP 2.2), so the Library path (D46, UNKNOWN today) is what the promise rests on. Trace it first.

### Evidence
- **S28.** Section 5's "resolved" means a design on paper; none is built or tested (C17, C23, C24, C42, C41). Use "answered on paper".
- **S29.** 4.1 Exits reads "BUILT, bugs fixed", but `timer()` still builds long-side today (SWAP 4). Halts labelled BUILT "never run in a host" is honest; keep that form. "REAL (`R1` pattern 1)" means platforms ship it, not that it works.
- **S30.** Broken references: D3 cites "(D21)" for the parent limit, should be D31. D34 and D41 cite "D44" for QML growth, should be D45. H-20 cites D4 for the type tag, should be I9. D45 cites a "S3 proof" reached through E4.
- **S31.** `accepts_evidence` (I8's Today cell): no match under `qml/src` in my search. Check the source of that claim.
- **S32.** Stale board (D23, I5, C24): true of the docstring at `runtime.py:366-369`, but it means the unit's own markets, only when a placement is set, and the board is unwired. Keep the fix, but don't describe it as live.
- **S33.** Appendix A: "the quant lost" (C12) is one mind arguing with itself. It is disclosed, but do not cite it as dissent.

---

## QUESTIONS.md

| Q | Verdict | Change |
|---|---|---|
| Q1 demo sign-in | Keep | Fine |
| Q2 data | Keep | Tell him plainly: M51 and M52 say "I think" order flow is handled, and `MAP` found no owner. Say the futures week cannot run without a route |
| Q3 words | Cut to one | (a) keep only pod against desk; he raised it himself in M51. (b) "quantity" is plumbing: the wire already says `"quantity"` (`unit.py`, intent body). He asked for an explanation, so answer in the walkthrough. (c) sticker and toleration are internal; the screen word belongs to the UI session, and he has said no codenames with him |
| Q4 cut-only agent fact | Keep | The default takes the looser reading of a fixed line while he is away. Nothing is built before he reads it, so that is harmless now, but say the build ships it as a card until he answers |
| Q5 branch and one bump | Half | Keep the landing branch. Remove "is one bump acceptable": it is a false premise (M1) and not his kind of question |
| Missing Q6 | Add | "Does moving a live deployment to a new pod version need your click?" Default yes, one click per pod edit (M2). Same class as Q4 |

The "Not asked" list is right, and the filter worked: no number, no methodology, no pod policy reaches him. Its one gap is S9: "not asked" must not mean "not explained", since he said of house money "let's first talk about it".

---

## Walks

| Walk | Result | Where it stops |
|---|---|---|
| Newcomer to a unit on paper | Fails | Installer has no owner; G8 UNKNOWN (backtest before a broker); zero-history blocks and hurdle deadlock (M4); no values picked; `first_real_start.py --rehearsal` covers setup only |
| Gold scalper, fast invalidation, no stop | Expressible on paper only | I13 is right; node gate `:1102-1106`, handler, R21's stop restore unlisted (M6); money-at-risk undefined without tail budget (S13); per-market numbers refused (M6); no template. The FI needs bars; finer clocks wait on I7 and Q2 |
| ORB across several opens | Partly | S9, R6 and the family tag hold; `position_limit` per open is not in S17 (per instrument in `model.py:321`); per-open numbers refused (M6); `FATES UB-15` puts a volume-gated variant in the template while Q2's default has no volume |
| Futures week, M50 | Fails at the end | Mechanisms fine; no route, `roll` refused, no methodology, copilot cannot use raw video (M51), agentic upgrade unbuilt (S10). Fine as a later session if said honestly |
| Mini app feeding another | Holds to the unit's door | Roads A and B BUILT; D on paper (K3); publisher identity unchecked (S26); `data_reads` market only; as-of history for QMB UNKNOWN (R13) |
| 200 units and fleet watch | Fails today | Nobody owns it; app doors (M7); single runtime thread and group stage latency UNKNOWN; two nodes (S20); retention unmeasured (D50) |
| Placeholder swap with a record | Fails on list | Mechanism is in D40, not section 3 (M3); open position and old-row meaning (S22). Note: the sizer swap reading the parent's record is per R11 (body, not read) |
| New brake, developer | Mostly holds | S5 plus folder plus code family (R4, good catch on `unlisted`); long form; new fact and signature (S27, S19) |
| New instrument class | Holds for rows | Fields not branches is right; venue capability absent (S21) |
| MIS down | Holds | V7, I5; but the calendar and `unknown` path (S17) |
| Guard failure, positions open | Mostly | K1 and V1 are right; exit block fault and hung stage open (S24) |
| Restart | Partly | R22 snapshot and F4 undecided; anchors missed while down (S23); cold restore UNKNOWN |

---

## Checks

**25 coverage items against the seed and his text.**
- Sound: H-01, 02, 04, 05, 06, 07, 12, 15, 21, 30, 33, 38, 40, 46, 50, 54, 55, 64, 89, 96, 97, 107, 118 (honest), 134, 136.
- Faulty:
  - H-57 (false, S1).
  - H-29 (no mechanism, S5).
  - H-20 (wrong reference).
  - H-98 (depends on an unbuilt door, M7).
  - H-19 ("learner and status object kept out" while D40 keeps spec and status as core; a partial truth).
  - H-45 (PH 19 appears in no column; it is covered only by the note, and "close, hedge or alarm" has no `hedge` anywhere).

**Quotes in F section 1.** All ten checked against the text. Accurate.

**30 code claims.**
- Held:
  - Format 4 (`compiler.py:100`).
  - Compiled fingerprint's four parts (`:1072-1079`).
  - G refusal (`runtime.py:559`, `:2756`).
  - `reads`, `halts`, `sessions` refused (`:900-904`).
  - Sizer inputs refused (`:930-936`).
  - Limit 1 (`:958`).
  - Receipt literal `0/1` (`unit.py` receipt).
  - Partial refused (`runtime.py:1807`).
  - `equity()` is balance (`ctrader_account.py:706`).
  - One template.
  - `pod` shell, 772 bytes.
  - `template` retired.
  - `Authority` has one value (`model.py:203`).
  - `QuoteBar` has no volume (`unit.py:120`).
  - No `commission` in the instrument schema.
  - `risk_stop` has no caller (`qmn/src`, `qmx-agents/apps` searched).
  - Hook stub (`runtime.py:1147`).
  - `before_order` has no caller in `qmb/src`, `qmn/src`.
  - YELLOW hard-coded (`:2628`).
  - `SlowState.read` grows (`engine.py:124`).
  - Widening law (`unit_intent.py:725`).
  - Scope strings (`:1675`).
  - Checker stops at F (`SKILL.md:30`).
  - `data_reads` (`supervisor.py:891`).
  - `MotionSwitch`.
  - Rehearsal is setup only.
  - Board docstring.
- Wrong or overstated: "every widening changes the format" (M1); S15's Today (S19). `accepts_evidence` not found (S31).
- Newly settled: `block_fingerprint` covers `block.py` only, so entry fields do not move compiled fingerprints (S18).

**The plans.** SWAP read in full; its PH rows match the sampled `RISK-SIZING-PLACEHOLDERS.md` rows 1, 5, 19, 26. A search of the build folder's plan files for a format-bump policy found nothing.

## What is solid
- The test was applied as written, and no dollar verdict survives as a fate. D3's default and "the horizon formula as a block" undo Friday correctly.
- D1 with a shared converter, the USDJPY root, and C11. D6's exit stack with three verbs. D15's number spec. D27's stickers dissolving four collisions (kill switch kept apart). D13's one-ledger pair.
- C2, C4, C6, C9, C12 and C22 turn refusals and his contradictions into rows without asking him. Exactly what he asked for.
- C1 is left open and honest. REVIEW M4's caveat stays on the block.
- D30's answer on ORB and sniping, D24 on the MIS, D25 on RVOL: plain and direct.
- D49's honest "tomorrow". Appendix C's stated limits. The section 8 hand-offs. The QUESTIONS filter.
- K1 and V1, R1's replayable row with `explain_size`, and the warning from `_CEILING` and `unlisted`.
- FATES places every source I sampled and states how it counted.

## What I did not read
- H1 to H5 and E1 to E5 in full: sampled by search, plus E5's bump section and results header. X0 to X7 bodies: not opened.
- `UNIT-PLAN.md`, `CONTRACTS.md`, the Lab spine, repair plan parts: searched only, or via SWAP.
- Old `funnel/REVIEW.md` and `SPINE.md`: not read, so REVIEW M4 and M7 are taken as F quotes them.
- TIMELINE: phases 5 and 6 only. `system-map.md`: searched. `SEEDS-2.md`: sampled by search.
- I ran no code or tests and did not open the UI. `FATES.md`, `FUNNEL.md`, `QUESTIONS.md`, SWAP and the named operator messages were read in full (M5, M7 and M8 by passage search and a size-limited view, not end to end).
