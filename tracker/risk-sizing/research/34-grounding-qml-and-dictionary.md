# 34: Grounding QML and its strategy dictionary

Research date: 2026-10-30. Read-only grounding. Nothing here is a design or a ruling. It records the journey, the reasons, the current state and the open questions.

Labels: **CHECKED** means I read it this session (path:line, command or message index given). **INFERRED** means my reasoning from checked material. Operator words are quoted from his own turns, never from a summary, unless marked otherwise.

Credential rule kept: Hermes exports and transcripts were read through a filter that withheld any line with key, token, password, secret or credential text. Nothing of that kind is copied here.

## Path and citation keys

| Key | What it is |
| --- | --- |
| `S/` | `C:/Users/Mubarak/Desktop/Stats/` |
| `H/` | `S/.hermes/orchestration/` |
| `GEN Lnnn` | `H/transcripts/20260824_121737_86f88c-friendly-greeting.md`, line nnn (genesis session, 24 Aug, model gpt-5.6-sol) |
| `M779` | Genesis operator turn 779, full text quoted inside `RES #43` |
| `RES #n` | `C:/Users/Mubarak/Downloads/hermes-resume-session-from-saved-json-file-20260826.json`, `messages[n]` |
| `GMX #n` | `C:/Users/Mubarak/Downloads/hermes-extract-strats-gold-mine-design-work-20260826.json`, `messages[n]` |
| `S27 #n` | `C:/Users/Mubarak/Desktop/strats/resume-strats-ground-state-work-20260827.json`, `messages[n]` (8 messages, exported 16 Sep) |
| `GS Lnnn` | `S/STRATS-GROUND-STATE.md` (26 Aug 19:12, GLM 5.2 audit) |
| `GMA Lnnn` | `H/resume-20260826/gold-mine-session-analysis.md` |
| `CSM Lnnn` | `H/resume-20260826/compacted-summary-message-00.md` |
| `DOS` | `C:/Users/Mubarak/AppData/Local/hermes/cache/delegation/subagent-summary-0-20260825_132506_664562.txt` (25 Aug recovery dossier) |
| `DNA Lnnn` | `S/schema/strategy-dna.md` (1 Sep lock) |
| `EB:` | `git show origin/engine/base:<path>` in `C:/Users/Mubarak/Desktop/QMX` (tip `d82be318`, 26 Oct) |
| `S16/` | `EB:_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-16/` |
| `T1 Lnnn` | `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/operator/transcript-2026-10-20-to-28.md` |
| `T2 Lnnn` | `.../operator/transcript-2026-10-29-to-30.md` |

---

## 1. The journey

### 1.1 Timeline

| Date | What happened | Evidence |
| --- | --- | --- |
| July 2026 | The old vault described an earlier QML: a "shared contract library", "the load-bearing stratum" every component depends on, with feature modules, a runtime and a compiler/validator for a `.qml` language. He has since called this vault very old and weak; it is listed here only as the start of the name. | CHECKED `C:/Users/Mubarak/Documents/Claude/QMX-discussion/02-Components/00-QML-shared-library/00-QML-overview.md:7-23` |
| 21 Aug | QML redesigned as a thin bot-authoring library, QL-1 to QL-10. It is "never a framework, never an engine", and the old load-bearing role is retired. A governed bot is two artifacts: a declaration (CT-33) and plain Python logic. Plain Python stays first class. | CHECKED `EB:docs/components/qml.md:1-19` (generated 2026-08-21, status ratified by operator delegation) |
| 23 Aug | QML code scaffolded (story 11.1). | CHECKED `git log --reverse EB -- qml/src`: `89dc4ce1 2026-08-23` |
| 24 Aug (Hermes genesis) | His first message: build "a knowledge base that i can later refer to and use together with other agents", split "specific organs" from strategies, build mini knowledge bases, and categorise "every idea to something that can be coded by any agent (so like a strategy spec, i have a target of N...)". | CHECKED `S16/research/goldmine-4065-range.md:21` |
| 24 Aug | **His four pillars** (`M779`, his words): "every strategy has around four pillars": the level ("a place on a chart that you are watching"), the trigger ("the event that tells you to enter a trade"), confirmation ("filters out the weaker setups"), and "the fourth part is what literally QMX handles with a lot of care which is risk management and position sizing". Also "it's not finite okay you just need to find the best combinations or the simplest version that produces results". | CHECKED `RES #43` (tool result carrying M779 verbatim) |
| 24 Aug | The assistant (gpt-5.6-sol) answered "Your four pillars make sense" and then turned them into three layers: dictionary, role binding, logic graph. The pillars became "a human-facing strategy/trading-plan lens, not the complete data model". | CHECKED `RES #43` (M795 header); `GEN L277`; `DOS` §1 lines 7-40 |
| 24 Aug 14:35 | His reaction to the dictionary idea: "if we build a strong enough dictionary, it can be reused in the strategy itself... where an agent was going to be writing long sentences, it just... says, maybe this is a bullish engulfing... and in the dictionary, bullish engulfing will be described. It maybe it has ranges... certain things might need specific numbers or defaults." Same turn: "all that is written in QML. You can read QML inside the latest version, it's a library in there". | CHECKED `GEN L1428-1430` |
| 24 Aug | Population mandate recorded: build and "substantially populate" the library "now, while QMX is still being developed", because he "should not sit idle waiting for QMX", subscriptions may expire, and the library "will later feed actual QMX". | CHECKED `H/user-corrections/2026-08-24-population-mandate.md:5-14` |
| 25 Aug | His dictation on the dictionary: "I'm not so much of a trader, but I'm good with dev work. So, the idea was... due to wanting of organization and structure... have an X amount of phrases that could be used in the dictionary... that stuff is under levels, triggers, confluence." And on timing: "I had a decision to make whether I build this now or build it after building KMX, I still have to build it, and it's very independent. So... let me just build it now." Also "a global index the same way, like you have skills". | CHECKED `S16/research/goldmine-all-user.md` msg 2717/2725 block (lines 43-48) |
| 25 Aug | A recovery dossier compared the three-layer model against "the current eight-part candidate" (market context/location, trigger, filters/confirmations, entry semantics, invalidation/stop, targets/exits/management, timing/sequence, scope) and split or kept each. | CHECKED `DOS` lines 300-325 |
| 26 Aug (morning) | After a compaction, four dictionary workers ran under a shared contract; the internet dropped, two died and were resumed. Result: 239 candidate entries in four files under `H/dictionary-wave-1/candidates/`. | CHECKED `GS L29-51`; `H/dictionary-wave-1/shared-contract.md` |
| 26 Aug | His long "good morning" turn (quoted in §2). He praised "the pillars against the completeness model", said "logic graph wasn't my idea", "a bot that has ambiguity shouldn't be tested", "most strategies actually are not coming from Forex traders, they're coming from futures traders", "let's just leave QMX out. QMX will adapt to the library", and "the whole job is having it populated, having strategies ready to go". | CHECKED `S16/research/goldmine-4065-range.md:182`; same text in `RES #0` |
| 26 Aug 19:12 | Ground-state audit (GLM 5.2) listed **seven** human-facing completeness lenses (see §2.6). | CHECKED `GS L143-155` |
| 27 Aug | A Hermes session proposed the empty folder tree: dictionary folders by concept family, not by role; one flat strategies folder; methodology and horizon as indexes, not homes. It also removed a "compiler/curator/promotion" rule from the Hermes skill. | CHECKED `S27 #0`, `#6`, `#7` |
| 1 Sep | The library tree was built in `S/` root: README, build state, `schema/` (DNA A-I lock, ids, graph contract, SQL), the 239 entries moved into four family files, a derived SQLite index, templates, and the layout demo `STRAT-000001`. "Population is explicitly not done." No Hermes session exists that day, so another tool built it. | CHECKED `S/STRATS-BUILD-STATE.md:9-17, 63-67`; file times (`ls -la S`); no-session finding from research 10 §1.1 |
| 15-16 Sep | A failed unpack left empty folders in `Desktop/strats`; the 27 Aug export was saved there on 16 Sep. | CHECKED `ls -la C:/Users/Mubarak/Desktop/strats` |
| 16 Sep | QMX architecture sitting (Grok). First draft treated Stats as a language QMX adapts to. **His restart**: "STRATS was a staging mill (noise to structured hypothesis) under the assumption QMX was unfinished; it is NOT a second QMX language. Absorb as QML expansion (bot-creation library)". Result: QML "Stage 0" research surface (dictionary entries, role bindings, graph, honesty holes) before the governed bot. | CHECKED `S16/.memlog.md` (restart event line); `S16/QML-EXPANSION.md:14-30` |
| 16-17 Sep | `qml.research` coded (stories 49.5 to 51.s6): dictionary 12-field parser over bytes the host passes, Stage 0 hypothesis types, a read-only view of `STRAT-000001`, refusals for invented exits. | CHECKED `git log EB -- qml/src/qml/research` (`1f6dc26d 2026-09-16` to `e8c08814 2026-09-17`) |
| 16 Sep onward | The decisions stay `provisional` in the ledger and `[PROPOSED]` in the docs. | CHECKED `main:_docwork/ledger.yaml:3774-3784` (DEC-0395 `status: provisional`); `EB:docs/glossary.md:284-286` |
| 20 Oct | He framed bots from first principles: "algorithmic trading is logically, if else statements. So it's rules based off rules. If this happens, buy. If this happens, sell." | CHECKED `T1 L264` (USER 2026-10-20T11:51) |
| 24 Oct 17:36 | "QML already has a very big structure... It has a dictionary... I think the only thing we hadn't added is exit methodology". | CHECKED `T1 L1177` |
| 24 Oct 17:43 | "the dictionary was GPT's idea, not mine. I never said it's unique... QML's whole point is to be used by agents to build strategies, but now we are turning it to build units, which means it also needs to be broadened". | CHECKED `T1 L1211` |
| 27 Oct | He pointed the run at the Hermes sessions: "Look at how we were trying to build QML back then"; "Same thing, I think, goes the dictionary, all right? Keep it free." | CHECKED `T1 L1574` (USER 2026-10-27T03:03) |
| 28 Oct 18:23 | "this was one of the biggest reasons we actually built the dictionary, so that we have a standardized form" (a YouTube trader "cannot just simply say, oh, no, this is just mean reverting"). | CHECKED `T1 L1951` |
| 28 Oct 19:03 | His recollection of the pillars: "we had like four pillars of a strategy. I've just forgotten... market context was there, but it was an event, a trigger, then... risk management, position sizing was the last. Then there is a fourth pillar". | CHECKED `T1 L2051` |
| 29 Oct | "the Hermes notes... Those things were not mine, they were from GPT." Later: "the dictionary needs a rebuild, an entire thing... because the ideas are there... QML is next in Q." | CHECKED `T2 L216` (USER 2026-10-29T17:25) |
| 30 Oct | STATE records the miss: QML and the dictionary get their own grounding; the Stats and strats Hermes work is "very important". | CHECKED `STATE.md:134, 142` |

### 1.2 The phrases in the brief I could not find

- "There are reasons why the dictionary was made like that" and "how do we make sure that those if-else statements can self-tune" do not appear in either transcript or the dictation files. CHECKED (`grep -i "made like that|self-tune|self tune"` over `operator/*.md`: only an unrelated MIS line at `T1`). They are relayed by the brief from a later turn. INFERRED.

### 1.3 Who authored what

| Part | Author | Evidence |
| --- | --- | --- |
| Four pillars (level, trigger, confirmation, risk and sizing), "not finite" | The operator | CHECKED `M779` in `RES #43` |
| Three layers (dictionary, role binding, logic graph); pillars as lenses | gpt-5.6-sol in Hermes | CHECKED `DOS` §1; operator: "logic graph wasn't my idea" (`RES #0`); "the dictionary was GPT's idea" (`T1 L1211`) |
| The quoted "true reusable unit is: primitive + role binding + ..." | Recovery-agent synthesis, not verbatim from M795 | CHECKED `CSM L290-293` (audit finding). Research 10 §2.1 quotes it as M795; that attribution is wrong. |
| 239 entries | Four post-compaction workers (DeepSeek, Terra and others) under one shared contract | CHECKED `GS L42-46`; `H/resume-20260826/full-recovered-transcript.md` message 18 |
| DNA A-I lock, library tree | 1 Sep build, tool unknown | CHECKED `S/STRATS-BUILD-STATE.md:13-17` |
| QML Stage 0 | 16 Sep Grok sitting after his restart | CHECKED `S16/.memlog.md` |

---

## 2. Why the dictionary is shaped the way it is

Each reason below is a recorded reason, rule or constraint. None is ratified by STATE.md for the new plan; STATE says only "a good start, not sacred" (`STATE.md:22`) and "the same goes for the dictionary" (types never a cage, `STATE.md:43`).

### 2.1 The workflow it assumed

| Reason | Evidence |
| --- | --- |
| He is a developer, not a trader, so agents must do the trading domain work and turn dictated words into proper terms. | CHECKED `GS L16`; `GEN` snapshot constraints (lines 117-120); 26 Aug: "I'm not a trader and I'm not that technical. So, it means I'll need you guys to do most of the heavy lifting" (`goldmine-4065-range.md:182`) |
| Sources are loose. A trader on YouTube explains to humans, not to code. A shared vocabulary turns loose talk into one standard form. | CHECKED `T1 L1951`; 26 Aug: "Most guys are going to give you abstract strategies" (`goldmine-4065-range.md:182`) |
| Agents should cite a known term instead of writing long prose each time. | CHECKED `GEN L1428-1430`; `GS L157-159` ("A canonical reusable trading language") |
| The assumed pipeline: inventory sources, treat playlists as seeds, cheap capture before any model, extract atomic claims, align chart and transcript, map to dictionary concepts, bind roles, build a graph, package, record lineage, reconcile aliases. | CHECKED `GS L436-453` |
| Ambiguity was expected to be common, so the dictionary had to make it visible. | CHECKED `GEN L1428` ("especially when we later get ambiguity in the sources"); `DNA L116-118` (part H) |
| The output was a candidate specification for later coding, not a bot. "Specking a bot" meant a candidate spec. | CHECKED `S16/research/library-intent-from-sessions.md` §3; `DNA L5, L31` |

### 2.2 "Populate early", and how that changed

| Stage | What was said | Evidence |
| --- | --- | --- |
| 24 Aug | Front-load the library while QMX is being built. Pilots are not the product. | CHECKED `H/user-corrections/2026-08-24-population-mandate.md:5-24` |
| 25 Aug | "let me just build it now" because it is independent of QMX. | CHECKED msg 2717/2725 block, `goldmine-all-user.md:43-48` |
| 26 Aug | "the whole job is having it populated, having strategies ready to go". | CHECKED `goldmine-4065-range.md:182` |
| 26 Aug (later) | He froze population: "I want to first see empty folders. We haven't done the layout." | CHECKED `GS L519-520` |
| 1 Sep | "Pause before populate... Do not start ingestion." | CHECKED `S/README.md` "Pause before populate" section |
| 16 Sep | The mill was "built under the assumption that QMX was still unfinished"; it becomes QML Stage 0. Population still not started; code refuses it (`POPULATION_INGEST_STARTED = False`). | CHECKED `S16/QML-EXPANSION.md:14-20`; `EB:qml/src/qml/research/projection.py:54` |
| 24-29 Oct | QML now builds units, not strategy specs, so it "needs to be broadened"; the dictionary "needs a rebuild". | CHECKED `T1 L1211`; `T2 L216` |

INFERRED: the original reason for a separate, prose-only library (QMX was not ready) no longer holds. QML exists, the unit is runnable code, and agents now build inside QMX.

### 2.3 Roles versus classes

- A dictionary entry is "role-neutral". It is not permanently a trigger, confirmation or stop; the job is assigned per strategy by a role binding. CHECKED `S/dictionary/README.md:3`; `DNA L16-17`.
- The reason: the same thing plays different jobs. Bullish engulfing can build a zone, trigger, confirm or exit; RSI can trigger, filter, mark a regime or exit. CHECKED `GMA L69-73`.
- Folders therefore group by what a concept is about, never by job. "That would permanently encode contextual roles as taxonomy." CHECKED `S27 #7` ("Dictionary folders are concept families, not roles").
- His seed behind it: SMC and ICT are "collections of multiple strategies", and "a scalper can use a level from SMC, a trigger from ICT, and a confirmation from elsewhere". CHECKED `GEN L1428`.
- The candidate's own "class" (complete, entry hypothesis, fragment, descriptive pattern, composite) is a label on the strategy record, not on the dictionary. CHECKED `DNA L45-55`.

### 2.4 Families

- Ten family folders were planned in the 27 Aug tree; only four have files. CHECKED `S27 #7` (tree); `ls S/dictionary`.
- Rule: "Do not fork per market." Forex, crypto spot and prop-firm rules are tags and overlays, not separate dictionaries. CHECKED `S/dictionary/README.md:18-20`.
- Rule: append, do not rewrite the 239 seeds; a new family is a new folder and file in the same format. CHECKED `S/dictionary/README.md:22-27`; `S/README.md` ("Do not rewrite the 239 seed entries").
- Rule: same slug in two files is allowed and kept; uniqueness is `(file_path, id)`. CHECKED `S/STRATS-BUILD-STATE.md:69`. QML keeps the same rule. CHECKED `EB:qml/src/qml/research/__init__.py:7`.

### 2.5 The A-I record

`DNA L33-43` locks nine parts. CHECKED. The reasons recorded for its rules:

| Part | Rule | Reason recorded |
| --- | --- | --- |
| A class | exactly one of five classes | Ideas are often incomplete; "the refusal to invent" is the mill's real gift. CHECKED `DNA L49-55`; `S16/QML-EXPANSION.md:32-34` |
| B evidence | evidence class per statement; "Model output is interpretation, not ground truth" | Keep source truth apart from agent reading. CHECKED `DNA L57-59` |
| C references | point to the dictionary, never redefine | One definition, many users. CHECKED `DNA L61-63` |
| D bindings | role, pair, timeframe, session, direction, timing per candidate | Roles and scope belong to the strategy, not the term. CHECKED `DNA L65-67` |
| E graph | ALL, ANY, NOT, K_OF_N, sequence, within, arming, reset, cooldown, re-entry; long and short may differ | His pillars are "not finite", so a flat list fails. CHECKED `DNA L69-87`; `RES #2` skill pitfall "Flat pillar lists: unlimited components require graph relationships" |
| F exits | label each slot `source_defined`, `external_policy`, `deliberately_open`, `unresolved`; "Do not invent exits" | Source honesty. His 26 Aug view: exits "are not mandatory... a boat most times will have its own exits under a book". CHECKED `DNA L89-110`; `goldmine-4065-range.md:182` |
| G dependencies | data, venue, bars, timezone, costs, transfer caveats | Futures-sourced ideas must not pass as spot facts. He also said G "is going to undermine QMX. QMX handles a lot of this already." CHECKED `DNA L112-114`; `goldmine-4065-range.md:182` |
| H unknowns | searchable, not buried | His words: "a bot that has ambiguity shouldn't be tested"; he asked for tags or colour coding. CHECKED `DNA L116-118`; `goldmine-4065-range.md:182` |
| I lineage | a family tree, not overwrites | His genetic idea: "mutate and adopt certain features from specific bots... combine them to make hybrids, tribids". CHECKED `DNA L120-122`; `goldmine-4065-range.md:182` |

### 2.6 The pillars, and four versus seven

| Date | Count | List | Evidence |
| --- | --- | --- | --- |
| 24 Aug | 4 (his) | level; trigger; confirmation (filters); risk management and position sizing | CHECKED `M779` in `RES #43` |
| 24 Aug | 4 kept as a "lens" | the assistant kept his four but made them a view over the three layers; risk and sizing "later corrected and repartitioned" | CHECKED `DOS` lines 7-14, 40 |
| 25 Aug | 8 | "the current eight-part candidate": market context/location, trigger, filters/confirmations, entry semantics, invalidation/stop, targets/exits/management, timing/sequence, scope | CHECKED `DOS` lines 302-314 |
| 26 Aug (recovered summary) | 4 | level/location, trigger, confirmation/filter/confluence, exits/invalidation/management | CHECKED `CSM L324-325` |
| 26 Aug (starting brief) | 9 areas | location/level, market context/filter, trigger, confirmation/confluence, entry semantics, invalidation, exits/management, timing/sequence, scope | CHECKED `H/user-corrections/2026-08-26-starting-brief.md` "Recovered semantic core" |
| 26 Aug (gold-mine analysis) | 7 items | location/level; context/filter; trigger; confirmation/confluence; entry/execution semantics; invalidation/stop/target/exit/management; timing/scope/evidence/ambiguity/lineage | CHECKED `GMA L720-728` |
| 26 Aug 19:12 (ground state) | **7, numbered 1-7** | the same seven as the gold-mine analysis | CHECKED `GS L143-155` |
| 1 Sep (lock) | 4 pillars + 4 more lenses | pillars: location/level, market context/filter, trigger, confirmation/confluence; also: entry semantics, invalidation vs stop, targets/exits/management, timing/sequence | CHECKED `DNA L126-140` |

Findings:
- **Seven exists.** The ground-state file numbers seven lenses (`GS L143-155`), written 26 Aug 2026. Research 21 searched only the 1 Sep lock and called his memory unconfirmed (`research/21-old-system-loose-ends.md` §2). CHECKED.
- **Not May.** The earliest pillar record anywhere I searched is 24 Aug (`M779`). Searched: all of `S/` including `.hermes`, both Downloads exports, the strats export, QMX `docs/` and `_docwork/` on engine/base and main, `Documents/QMX` (wiki, raw, _bmad-output, inbox, references), and the GPT conversation. CHECKED (`grep -i pillar`, zero hits outside Stats and the exports). A May origin is not supported by these sources.
- **His fourth pillar moved out.** Risk and sizing was his fourth pillar. It left the pillar list on 24-26 Aug ("no longer a universal STRATS/QMX-governance pillar", `RES #33` lines 50-52) and was replaced by market context. The 1 Sep lock has no risk or sizing pillar. CHECKED.
- **His 28 Oct memory blends two lists.** "Event, trigger, risk management, position sizing" is close to his own August four; "market context was there" matches the lock's four. CHECKED `T1 L2051` against `M779` and `DNA L130-133`. INFERRED: both memories are real, from different days.
- Every version says the lenses are "not finite" and "not folders". CHECKED `GS L155`; `DNA L128`; `CSM L260-261`.

### 2.7 The twelve fields and other format rules

- Each entry has 12 fields: family, aliases, definition, boundaries, observable inputs, recognition semantics, parameters/profiles, eligible roles, market/data constraints, transfer notes, evidence/status, uncertainty/variants. CHECKED `S/dictionary/README.md:31-44`.
- About 25 fields were discussed (including candidate reference algorithms, code implementations, ranges and defaults with provenance, latency and spread sensitivity, failure modes), but "exact serialization not ratified". CHECKED `GS L172-173`.
- Twelve relation types between entries were designed (alias-of, equivalent-to, derived-from, compatible-with, contradicts, supersedes and others). CHECKED `GS L175-176`. They are not in the shipped files: no entry carries a relation field. CHECKED (field list above).
- Every parameter value must carry a label (`source-stated`, `published-convention`, `STRATS-standardized`, `inferred`, `unresolved`): "do not silently invent defaults". CHECKED `H/dictionary-wave-1/shared-contract.md` "Required entry format".
- **Prose by design.** The workers were told: "Do not create Python, YAML schemas, CLIs, Pydantic, tests, adapters, databases, pilots, manifests, or runtime machinery" and "Do not inspect or discuss QMX". CHECKED same file, "Quality rules". The 26 Aug rule behind it: "This entire thing is not code, it's just a folder" (`GS L519`). This is the single biggest reason no entry runs. INFERRED from both.
- Optimisation, test runs, genetic machinery and live state were kept out of the library on purpose: they "belong" to QMX. CHECKED `GS L459-470`; `GMA L148`.

### 2.8 Scope

- Markets: forex and crypto spot. Horizons: scalp, intraday, swing. Futures and position trading excluded as targets, but futures sources allowed with transfer caveats. CHECKED `S/README.md` "Markets"; `GS L18-23`; `DNA L25`.
- His reason: "most strategies actually are not coming from Forex traders, they're coming from futures traders" while he trades forex and crypto spot. CHECKED `goldmine-4065-range.md:182`.

---

## 3. What is in it today

### 3.1 Counts

| Family file | Entries | Needs evidence | Parameters with a number | Eligible roles include "context" |
| --- | --- | --- | --- | --- |
| `market-structure-and-location/locations-and-structure.md` | 56 | 15 | 26 | 55 |
| `price-action-and-patterns/triggers-patterns-transitions.md` | 60 | 13 | 2 | 24 |
| `context-regime-and-intermarket/context-filters-confirmations.md` | 66 | 24 | 38 | 52 |
| `invalidation-exits-and-management/exits-execution-management.md` | 57 | 33 | 0 | 0 |
| **Total** | **239** | **85** | **66** | **131** |

CHECKED by a parse of `S/dictionary/*/*.md` (scratch script `dictparams.py` and `dictstats.py`, splitting on `## ` headings that carry a `**Definition:**` field). The ground state says 86 need evidence (`GS L79-86`); my count is 85. The difference is one entry and is unexplained.

- Six family folders are empty: indicators-and-transformations, liquidity-volume-and-order-flow, time-sessions-and-events, execution-and-order-semantics, risk-and-sizing, market-data-venues-and-observability. CHECKED `ls S/dictionary/*`.
- Nine slugs collide across files and are kept. CHECKED `S/STRATS-BUILD-STATE.md:69`; `S/catalog/dictionary-collisions.md`.

### 3.2 Runnable versus prose

- No entry contains code: zero code blocks in all four files. CHECKED (`dictstats.py`, `with_code 0` for every file).
- 130 entries have a formula-like "recognition semantics" line (an equation, a comparison or an if). Example: RSI "= 100 − 100/(1+RS)", "period 14 `source-stated` (Wilder); overbought 70 / oversold 30 `published-convention`". CHECKED `context-filters-confirmations.md:185-199`; count from `dictparams.py`.
- The "about 7 runnable" figure is inherited from research 01 (`01-ground-truth.md:116`), which cites an older grounding note. INFERRED: it most likely counts entries that match something QMX already computes (RSI, momentum, rate of change, moving averages, swing high and low), not entries that hold code.

### 3.3 What each entry carries

Twelve fields (§2.7). Trigger and exit entries name their parameters but give no numbers: "`rejection_distance`, `completion_window`, `close_requirement`, `direction`; all `unresolved` unless source-stated". CHECKED `triggers-patterns-transitions.md` (first Parameters line); `exits-execution-management.md` (first three Parameters lines: "all `source-stated` or `unresolved`").

### 3.4 Coverage against the brief's list

| Area | What exists | What is missing |
| --- | --- | --- |
| Exits | 57 entries: 8 invalidation, 17 exit and management, 12 entry order and timing, 10 pending order and re-entry, 5 source-native sizing, 5 execution transfer. CHECKED `exits-execution-management.md:3-12` | No numbers at all (0 of 57). Exits are named mechanisms only. His 24 Oct view: "the only thing we hadn't added is exit methodology" (`T1 L1177`). |
| Indicators | ATR, RSI, MACD, stochastic, Bollinger, Donchian, Keltner, ADX mentions, Ichimoku, VWAP, moving averages, inside the context file. CHECKED coverage table `context-filters-confirmations.md:16-29` | Their own family folder is empty. |
| Statistical tests | none | zero hits for Hurst, variance ratio, z-score, cointegration, Kaufman efficiency ratio. CHECKED `dictstats.py` term counts |
| Models | none | zero hits for HMM, hidden Markov, GARCH, machine learning. CHECKED same |
| Events | 3 news entries (economic-calendar-event, news-event-window, news-event-class). CHECKED coverage table | time-sessions-and-events folder empty; "news-event-class has no cross-market taxonomy". CHECKED `context-filters-confirmations.md:1041-1042` |
| Order flow | exchange-volume, volume-profile, vwap, order-book-depth, footprint-order-flow, cumulative-delta, absorption, spot-fx-tick-volume, each with "non-transferability" notes. CHECKED `context-filters-confirmations.md:1029` | No own folder; written as "centralized-exchange truth" versus broker tick volume |
| Futures | 81 mentions, mostly transfer caveats; `centralized-futures-execution-context` entry. CHECKED term count; research 10 §2.5 (lines 733-778 of exits file) | Out of declared scope as a target |
| Perps | "perpetual" once; "funding" 16 times, mainly as swap or rollover cost | no funding-rate, open-interest (0 hits) or liquidation entry. CHECKED term counts |
| Indices | `dollar-index`; "index" 18 mentions | no index-specific entries (cash index, futures index, sessions) |
| Sizing | 5 source-native sizing entries (fixed fractional, fixed cash, fixed notional, stop-distance, scale-in). CHECKED research 10 §2.5 | No Kelly (0 hits); risk-and-sizing folder empty |

### 3.5 How it describes market context

- As a pillar: "Market context / filter: regime, session, higher-timeframe, vetoes". CHECKED `DNA L131`.
- As a role, not a class: "None of `filter`, `confirmation`, or `confluence` is treated here as an intrinsic permanent class". CHECKED `context-filters-confirmations.md:3-7`.
- As 66 entries in ten groups: trend and regime 8, momentum 6, volatility 7, indicator family 6, session and time 6, spread/liquidity/cost/data health 7, volume/profile/order flow 12, intermarket 5, news 3, pattern quality 6. CHECKED `context-filters-confirmations.md:16-29`.
- As durable concepts only, never live state: news kept "as durable primitives (schedule/class/window) only, no live snapshots or market bias". CHECKED `H/resume-20260826/full-recovered-transcript.md` message 18.
- With a known hole: `market-regime` says "a canonical regime taxonomy is not standardized" and its thresholds are `unresolved`. CHECKED `context-filters-confirmations.md:80-93, 1040`.
- His sense of context (seed): "price action and technical analysis... market context is key" and the source "tells us which market context the strategy is meant to work in". CHECKED `T1 L1951`.
- Hermes framing that conflicts with tuning per market: "Pair, session, and regime are normally challenge coordinates, not tunable strategy factors" (24 Aug experiment bot). CHECKED via research 10 §2.10 (`EXP` file); not re-read this session.

---

## 4. QML in code and docs today

All CHECKED on `EB` (`d82be318`) unless marked.

| Part | What it is | Evidence |
| --- | --- | --- |
| Identity | A thin authoring library, `import qml`, built on QMF; "never a framework, never an engine". | `docs/components/qml.md:17` |
| Two artifacts | A declaration (CT-33) plus plain Python logic. "Plain Python stays first-class forever: an unregistered bot needs zero QML imports to run". | `docs/components/qml.md:19` |
| Three legal entries | Ungoverned Python into QMB with zero QML; registration without Stage 0; Stage 0 then graduation. "None a toll booth." | `docs/components/qml.md:210` |
| Runtime protocol | A factory and a per-instant callback. Denied: clock, I/O, network, undeclared randomness. | `qml/src/qml/protocol/contract.py:31-35` |
| Declaration | CT-33 with a strategy family, confluences, a parameter space and a footprint. | `docs/glossary.md:138` |
| Confluence (CT-34) | Legs of any mix of `level | trigger | confirmation | filter`. "Condition semantics live in Python logic in V1": the declaration names what is consumed and which role; the code decides when. | `qml/src/qml/declaration/confluence.py:1-10`; `docs/components/qml.md:80-82` |
| Parameter space | Each variable: type (exact integer, exact rational, categorical, boolean), bounds, step, a mandatory default, optional hard constraint, unit kind, and one `ui-editable | uneditable` flag. Defaults together are the "canonical assignment". | `qml/src/qml/declaration/parameters.py:1-7, 37-52` |
| Conformance | Layer 1 linter at registration; Layer 2 execution verdict; prediction linter (Book versus bot). "Technical, never performance". | `qml/src/qml/conformance/layer1.py:1-6`, `layer2.py:1-5`, `prediction.py:1-6`; `docs/components/qml.md:98` |
| Exits | The bot declares only permitted exit intents; "no `exit_logic` field"; exit modules sit in the Book. The example bot "never sizes... and never carries Book exit logic". | `docs/components/qml.md:104`; `qml/examples/conformant_bot/bot.py:6-9` |
| Families | An opaque id; "Constraining stays the Book's job". | `qml/src/qml/families/__init__.py:1-8` |
| Typed mechanism nouns | Entry/Exit/Filter/Session nouns (GAP-0085) and a first generator algorithm (GAP-0063) are deliberately unfilled. | `qml/src/qml/generation/gaps.py:1-8` |
| Indicators that run | Six wrappers: SMA, EMA, WMA, RSI, MOM, ROC. Named but not wrapped: ATR, MACD, BBANDS, ADX, STOCH, OBV, VWAP, session VWAP, session range. | `packages/qmf-indicators/src/qmf/indicators/wrappers.py:146-193`; `arithmetic.py:111-131` |
| Structure | One governed family: swing points. | `packages/qmf-structure/src/qmf/structure/families.py:1-27` |
| Configuration | "QML mints no configurable rows and no new pins"; thresholds live in the Book. | `docs/components/qml.md:252` |

### 4.1 Where the dictionary meets code

- `qml.research` parses dictionary entries (the 12 fields) from bytes a host passes in. No file access. CHECKED `qml/src/qml/research/__init__.py:1-11`; `docs/components/qml.md:216`.
- The only dictionary text inside the repo is a test fixture of three family files and `STRAT-000001`. The live dictionary stays in `S/` and is bound by `root_path`, never copied in. CHECKED `git ls-tree EB qml/tests/fixtures/research-seed`; `S16/QML-EXPANSION.md` §4.
- Stage 0 holds hypothesis types: dictionary cites, role bindings, a graph (boolean, temporal, lifecycle), the five classes, origins (`idea`, `chart`, `journal`, `seed_package` and others), the five exit slots and four labels. CHECKED `qml/src/qml/research/stage0.py:59-93`.
- Graduation maps roles: `level`, `location` → `level`; `trigger`, `confirmation`, `filter` stay. Everything else (`context`, `invalidation`, `stop`, `exit`, `management`, `sequence`, `within`, `arming`) falls to "Python WHEN". CHECKED `qml/src/qml/research/collapse.py:42-76`.
- Refused on purpose: compiling the graph to a run, minting a bot from the record, completing unresolved exits, starting population, and Stage 0 sizing (`STAGE0_NEVER_SIZES`). CHECKED `projection.py:8-9, 54, 203-283`; `stage0.py:36`.
- Status: code merged 16-17 Sep; docs and ledger still say proposed or provisional. CHECKED §1.1.

INFERRED: the dictionary connects to code only as read-only vocabulary. Nothing turns an entry into a running block. The block catalogue is missing (research 18 §3, CHECKED there).

---

## 5. What could tune itself today

His framing (seed, `T1 L264`): a bot is if-else rules. Split by that lens.

### 5.1 Numbers with ranges today

| Where | What is a number | Evidence |
| --- | --- | --- |
| QML parameter space | every declared variable has bounds, step and a default; a flag says if the UI may edit it | CHECKED `parameters.py:1-7` |
| Indicator wrappers | period and similar settings per running indicator | CHECKED `wrappers.py:219-295` (`_period_numerator`, `configure_wrapper`) |
| Dictionary context and location entries | labelled conventions, for example RSI 14, 70/30; ADX 20/25; R:R ≥2; correlation ±0.7. The file says adopting them as defaults "is a deliberate decision left open". | CHECKED `context-filters-confirmations.md:1043` |
| Dictionary trigger and exit entries | parameter names only, no values | CHECKED §3.3 |
| Graph operators | the K in `K_OF_N`, the window in `within`, cooldown length | CHECKED `DNA L78-84` (operators); values unset in `STRAT-000001` (`specification/parameters-and-provenance.md`, all `unresolved`) |

### 5.2 Structure today

| Where | What is structure | Evidence |
| --- | --- | --- |
| Roles | which job a term plays (level, trigger, confirmation, filter; and open roles at Stage 0) | CHECKED `collapse.py:42-76` |
| Graph | ALL, ANY, NOT, sequence, arming, reset, re-entry; long versus short | CHECKED `DNA L69-87` |
| Confluence | which producers a bot consumes | CHECKED `confluence.py:1-10` |
| Logic | when a leg fires lives in Python | CHECKED `docs/components/qml.md:82` |
| Exits and sizing | currently Book policy, not unit structure | CHECKED `docs/components/qml.md:104`; contradicts `STATE.md:21` (see §6) |

### 5.3 What the sources already say about self-tuning

- His 24 Aug seed: a dictionary term "maybe... has ranges... certain things might need specific numbers or defaults". CHECKED `GEN L1428`.
- His 24 Aug seed: focus on one style to get "the perfect identity" so that "all the stuff above kind of updates itself". CHECKED `GEN L1428`.
- His 24 Aug pillar note: "find the best combinations or the simplest version that produces results". CHECKED `M779`.
- Hermes 24 Aug: trigger and confirmation are "the largest optimization surface"; tune location and context first, add one confirmation family at a time, or "unlimited components create a combinatorial search engine that will eventually 'discover' noise". CHECKED via research 10 §2.2 (`DB 4065`); not re-read this session.
- Hermes 24 Aug experiment bot: tune "numbers within each structural family"; pair, session and regime are "challenge coordinates, not tunable strategy factors". CHECKED via research 10 §2.10.
- His 26 Aug genetic idea: "if we do overtime realize that a certain... confirmation mechanism can give us a higher win rate... we test it across families". CHECKED `goldmine-4065-range.md:182`.
- STRATS kept tuning out: "evolution/optimization... do not belong in this plain-file library". CHECKED `GMA L148`; `GS L465`.
- QMX docs today: QML adds no configurable numbers; thresholds sit in the Book. CHECKED `docs/components/qml.md:252`.
- Optuna 4.9.0 was already on the integration branch on 16 Sep. CHECKED `S16/.memlog.md` (version line). Whether QMB wires it to a unit's parameter space was not checked here.
- Current plan seeds: a unit has "self-calibrating risk and sizing" (`STATE.md:21`); "a setting moved inside its range = same unit, each value counted as a try" is an open recommendation, not a ruling (`STATE.md:184`). "Self-configuring has never been shown concretely" (`STATE.md:78`). Research 20 separates three meanings of self-configuration (`STATE.md:176`). CHECKED.

INFERRED: today only the parameter space is a tunable surface with declared ranges. Roles, graph shape, exits and context requirements are structure, and the dictionary gives numbers mainly for indicators and levels, not for triggers or exits.

---

## 6. Open gaps and contradictions (questions, unanswered)

**About the dictionary's purpose**
1. The library was prose by order ("not code, just a folder") because QMX was not ready. Now that QML builds runnable units, which of the twelve fields stay documentation and which must become code? (`H/dictionary-wave-1/shared-contract.md`; `T1 L1211`)
2. "Populate early" was paused before layout and never restarted. Is population still a goal, and who populates: a QMX workflow, the copilot, or the unit builder? (`S/README.md`; `projection.py:54`)
3. He says the dictionary was GPT's idea and needs a rebuild; he also says it was built so agents are never confused. Which parts are his intent and which were GPT's shape? (`T1 L1211`; `T2 L216`; `T1 L1951`)

**About the pillars**
4. His four (level, trigger, confirmation, risk and sizing) became the lock's four (location, context, trigger, confirmation). Risk and sizing left the list when sizing was the Book's job. Correction 2 puts sizing back in the unit. Does the pillar view take it back? (`M779`; `DNA L130-133`; `STATE.md:21`)
5. Seven lenses (26 Aug) versus four plus four (1 Sep) versus nine areas (26 Aug brief): which list, if any, should a unit builder see? (§2.6)
6. Where does "event" sit, which he named on 28 Oct: inside trigger, inside context, or its own lens? (`T1 L2051`; `DNA L132`)

**About honesty rules versus units**
7. The 26 Aug audit removed "missing exit means entry hypothesis" as a universal rule; the 1 Sep README and lock put it back. Which holds? (`CSM L264, L294-296`; `S/README.md:35`; `DNA L40, L99`)
8. "Do not invent exits" protects source truth. A unit needs exits to trade. How is a builder-added exit labelled so both rules hold? (`DNA L106`; `STATE.md:21`)
9. "A bot that has ambiguity shouldn't be tested" versus agents that fill gaps: what does an unresolved H item block? (`goldmine-4065-range.md:182`)

**About QML code versus the new intent**
10. QML says the bot "never sizes", carries no exit logic, and leaves thresholds to the Book. STATE says the unit owns exits and self-calibrating sizing. Which QML laws change? (`bot.py:6-9`; `docs/components/qml.md:104, 252`; `STATE.md:21, 229, 235`)
11. Market context is a pillar and an eligible role, yet graduation has no context role; it drops into Python. Where does a unit declare the context it needs? (`collapse.py:60-76`; `DNA L131`)
12. Stage 0 code is merged but its decisions are provisional. Is Stage 0 kept, merged into the unit spec, or replaced? (`main:_docwork/ledger.yaml:3774-3784`)
13. The dictionary lives outside the repo by rule (QMA AD-19, "Forbid" git absorb). Does a runnable block catalogue live in QMX, in Stats, or both? (`S16/QML-EXPANSION.md` §4-5)

**About coverage**
14. Scope is forex and crypto spot. Today's intent is any instrument, including futures and perps. Who adds funding, open interest, liquidations, roll and index sessions, and in which family? (§3.4)
15. No statistical tests or models exist as entries. Are they dictionary entries, MIS sensors, or both? (§3.4; research 16 §3.2)
16. `market-regime` has no state list and no thresholds. Who defines the states? (`context-filters-confirmations.md:1040`)
17. Twelve relation types and about 25 fields were designed but not shipped. Are relations needed for agents to find and combine parts? (`GS L172-176`)
18. Nine slug collisions are kept on purpose. Do they survive when entries become code with one name each? (`S/catalog/dictionary-collisions.md`)

**About tuning (his if-else question)**
19. Which parts of a unit may tune themselves without becoming a new unit: only declared parameter ranges, or also graph shape, roles, exits and context needs? (§5)
20. The Hermes rule says pair, session and regime are test coordinates, not tunable factors. His later seed tunes a strategy per market. Which wins, and where is the line? (§3.5; `STATE.md:110`)
21. Trigger and confirmation were called the largest search surface, with a warning about finding noise. How are tries counted when agents recombine parts across families? (§5.3)
22. Dictionary conventions (RSI 70/30 and the rest) were left as "a deliberate decision left open". Do they become editable defaults, starting ranges, or stay notes? (`context-filters-confirmations.md:1043`)

**About the record itself**
23. Research 10 quotes "the true reusable unit is..." as the assistant's M795; the 26 Aug audit says it is not verbatim. Downstream files that repeat it should say "recovery synthesis". (`CSM L290-293`)
24. Research 10 called `Desktop/strats` an empty husk. It holds the 27 Aug session that proposed the family-not-role tree. (`S27 #7`)
25. One entry differs between my count of "needs evidence" (85) and the ground state (86). Unexplained.
26. The 1 Sep build has no Hermes session; the tool that built it is unknown. (research 10 §1.1)
