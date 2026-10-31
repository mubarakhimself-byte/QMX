# The versions of the architecture and the foundation set

Agent A0, 31 Oct 2026, step 1 of the brief `architecture/briefs/A0-versions-and-level-0.md`. Three versions of the whole architecture, scored against his three tests, the foundation test, the twenty foundation properties and every case in the edge-case catalogue. One is picked; the losers' good parts are kept. The Level 0 spine (`architecture/level-0/ARCHITECTURE-SPINE.md`) is distilled from the pick.

**Labels.** CHECKED = read at the cited path or run (command named). INFERRED = judgement. Scores are INFERRED judgements over designs, made by a script (`score.py` in this agent's scratchpad) from per-property scores and named overrides, so they can be rerun and argued with. They rank the versions; they do not prove the pick works. The dummy unit's pass marks do that (`funnel/solutions/unit.md` §9).

## Read me first

1. **Version A wins: a small core that must always agree with itself, plus three mini apps on the mini-app core that already exists.** The core is QML with the dictionary, the unit template and its checker, the judge and the try ledger, journals, and one page of facts per market. The apps are QMB, the trading node and the MIS publisher.
2. **Scores out of 570 (267 cases plus 18 risk rows, 2 points each):** A 567, C 442, B 382. A misses on three cases, named in §6.
3. **B (everything an app) fails where two versions must never disagree:** the checker, the judge and the catalogue. **C (thick core, no new apps) fails a ruling:** QMB variants side by side (STATE midday ruling 22).
4. **The party found five refinements to A** that the funnel did not have (§7), one of them by running real code: a unit's size sent under a new field is silently dropped by both intent doors today, so sized unit intents must be a new CT-23 format version, which both doors refuse safely.
5. **Kept from the losers:** from B, the three apps and a unit-holding app template for research and paper; from C, no new machinery where the built core already does the job (the node's organs stay libraries; the trading profile is a host setting).

## 1. How this was made

| Skill | How it ran | Output |
| --- | --- | --- |
| `bmad-party-mode` | `--non-interactive --mode session`, inline cast with Winston, ten rounds; activation scripts run; factory facts and `on_complete` ignored | `party-transcript.md` |
| `principle-exhaust-the-design-space` | three versions that differ in where the core ends (not three flavours of one shape), each sketched, then compared side by side | §2 to §6 |
| `codebase-design` | depth, seams (one adapter is hypothetical, two is real) and the deletion test on the winner's modules | §9 |
| `domain-modeling` | the contested words fixed once, in the glossary format | `GLOSSARY.md` |
| `blast-radius` (early use) | the sizing seam was run during the party because it decided a version detail; the full set is in `level-0/blast-radius.md` | §7 item 2 |

Inputs read in full: the frame, the best session's method, `STATE.md`, the ledger, the workflow and skills file (sections 3 to 5), G1, G2, G3, G4a, G4b, research 54, the lead's review of the funnel, the funnel's index and all fifteen part files, the edge-case catalogue, the experience files (design thinking in its harvest, needs, defaults and lead's calls; problem solving in its recommendations), the QMA v2 spines' decision lists and the rules of the decisions this work touches, and the `docs/` index.

## 2. The three versions

All three sit on what is built: one catalog (`qmx_control/catalog.py`), one Library, one engine, one host process per machine (`qmx_host`), the mini-app core (`qmx_apps`), QML's runtime seam, QMB's measuring parts, the node's trading organs. They differ only in where the core ends.

### Version A. A small core, three default apps (the frame, refined)

- **Core (one copy, must agree with itself):** QML with the dictionary and catalogue; the unit template (a Library kind) and its checker; the judge, the study spec and the try ledger; journals (envelope, kinds, writer library); instrument, venue and account records; the reading blocks the MIS runs; contracts; plus what exists (the Library, the engine and templates, the catalog and the copilot, the mini-app core, the host).
- **Mini apps (installed by default, replaceable, may run as several versions):** QMB (risk `runs`); the trading node (risk `money`, the only order path); the MIS publisher (risk `shows`), with an instance on his PC and one on each trading machine.
- **Content (removable and improvable):** workflow templates, units, dictionary entries, reading cards.
- **First build:** the kernel's shapes and checks, the QMB app with a runner that trades a unit, the dummy unit end to end, the practice node on This PC, the MIS reading blocks and the PC instance, the journal shipping job.
- **In a few sentences:** "QMX has a small core that must always agree with itself: the library units are written in, the checker, the referee, the records and the market facts. Everything that runs on a machine and might need a second version is an app on that core: the backtester, the trading node, the market reader. Only the node sends orders, and it trades on its own machine with nothing else up."

### Version B. Mini apps all the way down (his seed, taken to its end)

- **Core:** only the Library, the engine, the catalog, the mini-app core, the host and the contract rules. The unit kind's schema stays in the core.
- **Mini apps:** a QML app (check, compile, explain operations), a catalogue app (the dictionary and blocks), a judge app, QMB, the trading node, the MIS, an instrument-records app (venue refresh), all installed by default.
- **First build:** seven apps and their contracts with the core.
- **In a few sentences:** "QMX is a platform; every trading part is an app you can swap." Explaining which QML, which judge and which catalogue a given unit used takes a page.

### Version C. A thick core, no new apps (boring technology)

- **Core:** everything. QMB stays a library behind a host door (PR 204 rebased as designed); the trading node becomes a built-in trading role of the host; the MIS runs inside the host.
- **Mini apps:** none new; the mini-app core stays for his own apps.
- **First build:** the door, the role, the MIS service inside the host.
- **In a few sentences:** "QMX is one program on every machine; on a trading server it also trades."

### Per part, per version

| Part | A | B | C |
| --- | --- | --- | --- |
| QML with the dictionary | core | apps (QML app, catalogue app) | core |
| The unit template and its checker | core | schema core, checker in the QML app | core |
| The judge and the try ledger | core | app | core |
| Journals | core | core (writer library) | core |
| Instrument, venue and account records | core | app | core |
| The Library, the engine, the catalog, the mini-app core, the host | core (built) | core (built) | core (built) |
| QMB | mini app | mini app | host door |
| The trading node | mini app (`money`) | mini app (`money`) | host role |
| The MIS | reading blocks core; publisher app | app | host service |
| External connections | core ports, adapters behind them | core ports | core ports |
| Workflow templates | content | content | content |
| DevOps and clocks | core | core | core |

## 3. His three tests and the foundation test

| Test | A | B | C |
| --- | --- | --- | --- |
| Handles the hard cases fully | Yes, with three named gaps (§6) | No: a check or a judge that lives in an app can be off, swapped or two versions apart (160 cases below full marks) | No for QMB variants (ruled) and for node isolation and updates (126 cases below full marks) |
| Can be maintained and debugged | Yes: one copy of each core piece; each app's health log and breaker for free (ruling 24) | Hard: seven app contracts with the core; a bug can sit in the mismatch between two app versions | Mostly: one program, but the node's lifecycle is the host's lifecycle |
| Explained in a few plain sentences | Yes (§2) | No: "which QML, which judge" needs a page | Yes |
| Foundation: QMX grows on top without rework | Yes: a new venue, class, reading, QMB, risk block or unit kind is a record plus code behind a door that exists | Partly: growth is easy, but every growth step widens the core-to-app contract surface | No: each new QMB or node build is a host change; variants need a switch |

## 4. The twenty foundation properties

Scores: 2 = held by a core property with no special code; 1 = partly, or needs special code; 0 = not held.

| Property | A | B | C | Why a version scores below 2 |
| --- | --- | --- | --- | --- |
| F1 versioned contracts with an overlap window | 2 | 1 | 2 | B adds a versioned contract between the core and every app that holds core logic |
| F2 extension points with working defaults | 2 | 1 | 2 | B: a check or a judge in an app has no default while the app is off |
| F3 one way to add a thing | 2 | 2 | 1 | C: a QMB variant needs a host switch; a new node build is a host change |
| F4 owned names | 2 | 2 | 2 | |
| F5 declared inputs, known times, deterministic runs | 2 | 1 | 2 | B: two QML apps can disagree on when a block's value is knowable |
| F6 same code in research and live | 2 | 1 | 2 | B: the QMB and node apps each bundle a QML, so research and live can drift |
| F7 unknown is a state | 2 | 2 | 2 | |
| F8 at least once, with an id | 2 | 2 | 2 | |
| F9 fail closed for new risk, open for protection | 2 | 2 | 1 | C: trading shares a process with the engine and, on the PC, with chats |
| F10 immutable, versioned records | 2 | 1 | 2 | B: verdicts depend on which judge app version ran |
| F11 lifecycle with reasons and saved state | 2 | 2 | 1 | C: a host update restarts trading |
| F12 every problem at once, checked at the door | 2 | 0 | 2 | B: the Library door cannot call a checker that lives in an app that may be off |
| F13 observable by default; health means progress | 2 | 2 | 1 | C: loses the mini-app health log and breaker for QMB and the node |
| F14 declared rights; limits report, never cap | 2 | 2 | 1 | C: no manifest rights for the node |
| F15 standalone and local first | 2 | 1 | 2 | B: the node must carry its own copies of core apps |
| F16 only he promotes; one automatic stop | 2 | 2 | 1 | C: no money-app signature on node versions |
| F17 one time scale | 2 | 2 | 2 | |
| F18 one owner per stream, credential and position | 2 | 1 | 2 | B: two judge apps can each count tries |
| F19 typed market facts | 2 | 1 | 2 | B: market facts served by an app the node must reach |
| F20 explainable in a sentence | 2 | 1 | 2 | B: needs a page |
| **Total (of 40)** | **40** | **29** | **32** | |

## 5. How A holds each property (one line each, so the score can be checked)

| Property | Held by, in A (spine AD) |
| --- | --- |
| F1 | JSON Schema with `schema_version`, addable never redefined, a contract handshake on every cross-machine connect (AD-6) |
| F2 | every slot ships a working default or a labelled placeholder; the three apps install with one click (AD-14, AD-15, AD-33) |
| F3 | the "one way to add" table (AD-1) |
| F4 | app outputs namespaced by app id; core names reserved (AD-30) |
| F5 | QML's `knowable_at` guard kept; cut-against-full and warm-up tests on every block (AD-16, AD-19) |
| F6 | one compiled callback, one motion engine, one reading code path in QMB and the node (AD-5) |
| F7, F8 | the node's CT-19 and CT-20 laws kept; reconcile before trading; idempotent ids everywhere (AD-13, AD-39) |
| F9 | AD-12 and the node's journal-before-dispatch kept |
| F10 | pins by `id@version`; successors, never edits (AD-7) |
| F11 | desired state, warm-up from local recordings, reasons on every state change (AD-38) |
| F12 | one checker in QML, reached at the Library door, a catalog row, template steps and a hook (AD-11, AD-17) |
| F13 | OpenObserve only; health is progress; off shows as off (AD-42) |
| F14 | mini-app rights and isolation; the money signature (AD-33) |
| F15 | the trading path is local to one machine (AD-2) |
| F16 | governed drafts; the money app signature; risk stops wait for his resume (AD-3, AD-38) |
| F17 | AD-10, AD-43 |
| F18 | one writer per partition; one feed keeper per venue and environment per machine; machine-pinned deployments (AD-8) |
| F19 | instrument records and typed units of measure (AD-9, AD-26) |
| F20 | §2's sentences |

## 6. Every edge case, scored

**Totals.** 285 rows (267 cases and 18 risk rows), maximum 570. A 567, C 442, B 382 (CHECKED: `python -I score.py catalogue.md out`, output `out/summary.txt`). Cases below full marks: A 3, C 126, B 160.

**A's three misses, stated plainly.**
- **QML-15** (code evades the scan). Units run inside the node's process, so a block that dodges the import scan with `exec` could reach files or the clock live. The wall is the sandbox run of checker layer G before any deploy, plus his click. Accepted, logged as a lead's call.
- **QB-17** (a long backtest competes with the live recorder on the PC). Nothing gives live paths priority by default; the QMB app's CPU share is unset (`APPS/manifest.py:86-104`). A named setting for Level 1.
- **TN-09** (Hyperliquid's dead man's switch cancels stops). A designs protection as a reduce-only trigger order re-placed after any cancel; whether the venue accepts that as a resting stop is unproven until the testnet probe (lead's review, gaps).

**The risk rows** score the same in every version: each leaves the same socket and journal fields; the content is the risk session's.

**The table.** "A, B, C" are the scores. A case scores the lowest score of the properties the catalogue names for it, unless a named override applies (the note says why). Properties come from the catalogue's own column.

| Case | What happens | Odds, harm | Properties | A | B | C | Why a score is below 2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QML-01 | A block uses future data inside its own maths (centred window, a ... | H, Silent | F5, F12 | 2 | 0 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable; F12: B: the Library door cannot call a checker that lives in an app that may be off |
| QML-02 | A swing point or pattern is only confirmed k bars later, but the ... | H, Silent | F5 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable |
| QML-03 | A recursive indicator (EMA, ATR with smoothing) gives a different ... | H, Silent | F11, F6 | 2 | 1 | 1 | F11: C: a host update restarts trading; F6: B: QMB and node apps each bundle a QML; research and live can drift |
| QML-04 | A streaming indicator recomputes all history on every update, so a ... | M, Stop | F11, F6 | 2 | 1 | 1 | F11: C: a host update restarts trading; F6: B: QMB and node apps each bundle a QML; research and live can drift |
| QML-05 | A stop of "20" means 20 pips on EURUSD (5 digits), 2 dollars on ... | H, Money | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| QML-06 | The same symbol has different digits, contract size or money per ... | H, Money | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| QML-07 | A dictionary entry is used in a role it was not meant for, because ... | H, Stop | F3, F12 | 2 | 0 | 1 | F3: C: a QMB variant needs a host switch; a new node build is a host change; F12: B: the Library door cannot call a checker that lives in an app that may be off |
| QML-08 | A unit cites an entry with no code behind it (ATR, MACD, ... | H, Silent | F12, F3 | 2 | 0 | 1 | F12: B: the Library door cannot call a checker that lives in an app that may be off; F3: C: a QMB variant needs a host switch; a new node build is a host change |
| QML-09 | One word means different things across classes. Volume is a tick ... | H, Silent | F19, F5 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach; F5: B: two QML apps can disagree on when a block's value is knowable |
| QML-10 | An entry written "crypto spot only" is used on perps or futures | M, Silent | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| QML-11 | A dictionary entry's meaning is edited while units cite it, so ... | M, Silent | F10, F1 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran; F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| QML-12 | A shared block gets a bug fix, and every unit using it changes ... | M, Money | F10, F16 | 2 | 1 | 1 | F10: B: verdicts depend on which judge app version ran; F16: C: no money-app signature on node versions; rebuilt by hand |
| QML-13 | A learned block (a model) is retrained. Is that calibration or a ... | M, Silent | F10, F5 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran; F5: B: two QML apps can disagree on when a block's value is knowable |
| QML-14 | Undeclared randomness (`numpy.random` is not in the deny list) ... | L, Silent | F5 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable |
| QML-15 | Code evades the scan (`exec`, `importlib`, `__import__` are not ... | L, Silent | F14 | 1 | 1 | 1 | units run in-process on the node; the real wall is the pre-deploy sandbox run plus his click (accepted risk, LEAD-CALLS 19) |
| QML-16 | A threshold lives as a literal in the Python logic, so tuning, the ... | H, Silent | F5, F12 | 2 | 0 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable; F12: B: the Library door cannot call a checker that lives in an app that may be off |
| QML-17 | Long and short rules are silently mirrored when the source made ... | M, Silent | F5 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable |
| QML-18 | A confirmation that comes after the trigger moves the honest entry ... | H, Silent | F5, F6 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable; F6: B: QMB and node apps each bundle a QML; research and live can drift |
| QML-19 | A plain-Python unit reads the forming bar as if it had closed ... | H, Silent | F6, F5 | 2 | 1 | 2 | F6: B: QMB and node apps each bundle a QML; research and live can drift; F5: B: two QML apps can disagree on when a block's value is knowable |
| QML-20 | A 1-minute unit reads the 1-hour close before the hour has closed; ... | H, Silent | F5, F17 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable |
| QML-21 | A weighted-vote combiner ties, or every input is absent at start, ... | M, Silent | F2 | 2 | 1 | 2 | F2: B: a check or judge that lives in an app has no default while the app is off |
| QML-22 | A unit reads another unit's live output ("a mini scalper for an ... | M, Money | F15 | 2 | 1 | 2 | F15: B: the node must carry its own copies of kernel apps |
| QML-23 | Refusal functions and `GAP_*` constants from old rulings read as ... | H, Stop | F1 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| QML-24 | Two registries hold "bots" (qmf-registry through QMB, and the ... | H, Silent | F3 | 2 | 1 | 2 | B: the QML app keeps its own registry beside the Library |
| QML-25 | QML needs Python 3.14 exactly; a newcomer or a server image with ... | M, Stop | F2, F13 | 2 | 1 | 1 | F2: B: a check or judge that lives in an app has no default while the app is off; F13: C: loses the mini-app health log and breaker for QMB and the node |
| QML-26 | A venue or plain-Python code passes binary floats into exact money ... | M, Silent | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| UT-01 | An agent's unit passes every check and still trades nonsense: ... | H, Silent | F12, F5 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off; F5: B: two QML apps can disagree on when a block's value is knowable |
| UT-02 | A checker false positive blocks good work: an `os.path` helper ... | H, Stop | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| UT-03 | The checker changes and a unit that passed yesterday fails today, ... | M, Stop | F1, F13 | 2 | 1 | 1 | F1: B adds a versioned contract between kernel and every app that holds kernel logic; F13: C: loses the mini-app health log and breaker for QMB and the node |
| UT-04 | A unit's version changes while a trade is open, and the new ... | H, Money | F10, F11, F18 | 2 | 1 | 1 | F10: B: verdicts depend on which judge app version ran; F11: C: a host update restarts trading; F18: B: two judge apps can each count tries |
| UT-05 | A self-tuned number swings back and forth on too few trades | H, Money | F5, F10 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable; F10: B: verdicts depend on which judge app version ran |
| UT-06 | Self-tuning drifts toward more risk over months | M, Money | F16 | 2 | 2 | 1 | F16: C: no money-app signature on node versions; rebuilt by hand |
| UT-07 | A placeholder sizer or exit reaches a live account without anyone ... | M, Money | F13, F16 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node; F16: C: no money-app signature on node versions; rebuilt by hand |
| UT-08 | A unit's invalidation is a condition, not a price, so R is undefined | M, Silent | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| UT-09 | Unit state (calibration, counters, an armed setup) is lost on ... | H, Money | F11, F1 | 2 | 1 | 1 | F11: C: a host update restarts trading; F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| UT-10 | The node restarts mid-session and a unit needs 200 bars before it ... | H, Money | F11, F15 | 2 | 1 | 1 | F11: C: a host update restarts trading; F15: B: the node must carry its own copies of kernel apps |
| UT-11 | Warm-up history comes from another source than the live feed ... | M, Silent | F5, F13 | 2 | 1 | 1 | F5: B: two QML apps can disagree on when a block's value is knowable; F13: C: loses the mini-app health log and breaker for QMB and the node |
| UT-12 | A unit needs depth or a trades tape, and the market or machine has ... | H, Silent | F19, F12 | 2 | 0 | 2 | F19: B: market facts served by an app the node must reach; F12: B: the Library door cannot call a checker that lives in an app that may be off |
| UT-13 | A unit built for FX hours is placed on a 24/7 crypto perp, or on ... | H, Silent | F17, F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| UT-14 | Two units trade one symbol on a netting account, and one unit's ... | H, Money | F18, F19 | 2 | 1 | 2 | F18: B: two judge apps can each count tries; F19: B: market facts served by an app the node must reach |
| UT-15 | A unit signals twice on consecutive bars and pyramids without ... | H, Money | F2 | 2 | 1 | 2 | F2: B: a check or judge that lives in an app has no default while the app is off |
| UT-16 | A unit emits an exit and an entry on the same instant, or opposite ... | M, Money | F5 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable |
| UT-17 | An edit is wrongly called a new unit, a new version or a ... | H, Silent | F10 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran |
| UT-18 | A unit has no exit that is sure to fire, and holds through a ... | M, Money | F2, F12 | 2 | 0 | 2 | F2: B: a check or judge that lives in an app has no default while the app is off; F12: B: the Library door cannot call a checker that lives in an app that may be off |
| UT-19 | The unit template moves to schema version 2 and stored units must ... | M, Stop | F1 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| UT-20 | A plain-Python unit (always allowed, CC-08) wants to trade, and ... | M, Stop | F3, F2 | 2 | 2 | 2 | plain Python passes the safety layers and deploys (all versions) |
| UT-21 | A unit is saved without the source it came from (a video, a chat, ... | M, Silent | F10 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran |
| UT-22 | The PC is off for a week; where does a unit's slow recalibration run? | M, Money | F15 | 2 | 1 | 2 | F15: B: the node must carry its own copies of kernel apps |
| UT-23 | A unit's general settings and its market version (U-13) are both ... | M, Money | F10, F16 | 2 | 1 | 1 | F10: B: verdicts depend on which judge app version ran; F16: C: no money-app signature on node versions; rebuilt by hand |
| QB-01 | A long backtest dies on memory because every replay step copies ... | H, Stop | F6, F14 | 2 | 1 | 1 | F6: B: QMB and node apps each bundle a QML; research and live can drift; F14: C: no app manifest rights for the node |
| QB-02 | Futures trades, crypto trade prints and perps tape cannot replay; ... | H, Stop | F3, F19 | 2 | 1 | 1 | F3: C: a QMB variant needs a host switch; a new node build is a host change; F19: B: market facts served by an app the node must reach |
| QB-03 | The test uses one spread, but live spreads at the 17:00 New York ... | H, Money | F19, F6 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach; F6: B: QMB and node apps each bundle a QML; research and live can drift |
| QB-04 | Triple swap on Wednesday (FX), Friday financing (index CFDs), ... | H, Silent | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| QB-05 | A futures continuous series is back-adjusted, so a unit tuned on ... | M, Silent | F19, F10 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach; F10: B: verdicts depend on which judge app version ran |
| QB-06 | An IC futures CFD expires and is never rolled, forcing a close at ... | M, Money | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| QB-07 | A weekend gap jumps through the stop, and the test fills at the ... | H, Silent | F6 | 2 | 1 | 2 | F6: B: QMB and node apps each bundle a QML; research and live can drift |
| QB-08 | The computed size is under the minimum lot, so it rounds to zero ... | H, Money | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| QB-09 | An agent scores variants in a script without passing QMB's door, ... | H, Silent | F12, F13 | 2 | 0 | 1 | F12: B: the Library door cannot call a checker that lives in an app that may be off; F13: C: loses the mini-app health log and breaker for QMB and the node |
| QB-10 | The best-looking of 20 markets is picked, and its edge was luck | H, Silent | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| QB-11 | An agent-built unit is tested on years the model remembers, so it ... | M, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| QB-12 | A template brings back a default holdout lock (60/20/20 split), ... | H, Stop | F2 | 2 | 1 | 2 | F2: B: a check or judge that lives in an app has no default while the app is off |
| QB-13 | Two QMB variants (he wants new versions and variants, T3:1383) ... | M, Silent | F1, F13, F10 | 2 | 1 | 0 | C cannot run QMB variants side by side (his ruling 22); B lets each variant judge itself |
| QB-14 | The same run twice gives two results (thread order, dictionary ... | L, Silent | F5 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable |
| QB-15 | A run that placed no trades is read as a finished backtest | H, Silent | F12, F13 | 2 | 0 | 1 | F12: B: the Library door cannot call a checker that lives in an app that may be off; F13: C: loses the mini-app health log and breaker for QMB and the node |
| QB-16 | Synthetic data for crypto or futures comes from a forex-CFD generator | M, Silent | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| QB-17 | A long backtest on the PC competes with the live recorder or a ... | M, Stop | F9, F15 | 1 | 1 | 1 | no version enforces live priority over research by default; a named setting in Level 1 |
| QB-18 | A data hole is replayed as a flat market, and indicators bridge a ... | H, Silent | F13, F5 | 2 | 1 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node; F5: B: two QML apps can disagree on when a block's value is knowable |
| QB-19 | Results are money only, so units on different instruments and ... | H, Silent | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| QB-20 | The backtest child is killed by the OS; on Windows the memory ... | M, Stop | F11, F13 | 2 | 2 | 1 | F11: C: a host update restarts trading; F13: C: loses the mini-app health log and breaker for QMB and the node |
| QB-21 | Daily bars in the history are UTC while the broker's day ends at ... | H, Silent | F17 | 2 | 2 | 2 |  |
| QB-22 | What-if filters that improve results are not counted as tries | M, Silent | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| QB-23 | Live trades differ from what the backtest would have done on the ... | H, Silent | F6 | 2 | 1 | 2 | F6: B: QMB and node apps each bundle a QML; research and live can drift |
| QB-24 | An agent edits the test tool or its output to get a pass | L, Silent | F14, F13 | 2 | 2 | 1 | F14: C: no app manifest rights for the node; F13: C: loses the mini-app health log and breaker for QMB and the node |
| LD-01 | A Dukascopy hour comes back empty with no error after the bot wall | H, Silent | F13, F8 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| LD-02 | Weekend and holiday bars: present for crypto, absent for FX, ... | H, Silent | F17, F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| LD-03 | A source changes its timestamp unit (Binance moved from ... | M, Silent | F5, F10 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable; F10: B: verdicts depend on which judge app version ran |
| LD-04 | A source changes its cadence (Hyperliquid's book snapshots changed ... | M, Silent | F10, F13 | 2 | 1 | 1 | F10: B: verdicts depend on which judge app version ran; F13: C: loses the mini-app health log and breaker for QMB and the node |
| LD-05 | An upstream archive file is replaced, so an old backtest can no ... | M, Silent | F10 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran |
| LD-06 | His Library is empty in the new layout (no bring-in has run), so ... | H, Stop | F13, F2 | 2 | 1 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node; F2: B: a check or judge that lives in an app has no default while the app is off |
| LD-07 | The Library is down or on an unreachable server while the node ... | M, Money | F15 | 2 | 1 | 2 | F15: B: the node must carry its own copies of kernel apps |
| LD-08 | An agent's tool call cannot pass a holdout or a run id, so reads ... | M, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| LD-09 | Recording ticks fills the disk (D: about 57 GB free, C: 16 GB) | M, Stop | F9, F13 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down; F13: C: loses the mini-app health log and breaker for QMB and the node |
| LD-10 | A source's terms limit use (Dukascopy, Binance Vision) | L, Friction | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| LD-11 | A backup reading the price store makes the live recorder wait ... | M, Stop | F9 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| LD-12 | The same instrument from two sources (Dukascopy gold against IC ... | H, Silent | F19, F13 | 2 | 1 | 1 | F19: B: market facts served by an app the node must reach; F13: C: loses the mini-app health log and breaker for QMB and the node |
| LD-13 | Index CFD dividend cash adjustments are missing from price series, ... | M, Silent | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| LD-14 | Two agents edit the same Library item | M, Silent | F10, F18 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran; F18: B: two judge apps can each count tries |
| LD-15 | The bundled SQLite has a write-ahead-log reset bug; two writers ... | L, Silent | F18 | 2 | 1 | 2 | F18: B: two judge apps can each count tries |
| LD-16 | History is stamped in UTC, the broker in GMT+2 or +3, and someone ... | H, Silent | F17 | 2 | 2 | 2 |  |
| LD-17 | A save made while the server Library is away is replayed twice, or ... | M, Silent | F8 | 2 | 2 | 2 |  |
| MIS-01 | The MIS is down or slow, and units must keep trading | M, Money | F15, F9 | 2 | 1 | 1 | F15: B: the node must carry its own copies of kernel apps; F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| MIS-02 | A stale reading is used as if it were fresh | H, Silent | F8, F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| MIS-03 | "Regime" means volatility in the code and trend or mean reversion ... | H, Silent | F1, F20 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic; F20: B: which QML, which judge, which catalogue app needs a page, not a sentence |
| MIS-04 | The same reading computed in QMB, the MIS and a unit gives three ... | H, Silent | F6 | 2 | 1 | 2 | B: the MIS app may bundle another reading version than QMB's |
| MIS-05 | A retrained model relabels the past, so a backtest sees new labels ... | M, Silent | F10, F5 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran; F5: B: two QML apps can disagree on when a block's value is knowable |
| MIS-06 | Bid-ask bounce makes a price-only mean-reversion sensor raise ... | H, Silent | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| MIS-07 | A trend or mean-reversion label takes hours to show, and a scalper ... | H, Silent | F5 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable |
| MIS-08 | A corpus built on three FX sessions is applied to 24/7 crypto | H, Silent | F19, F17 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| MIS-09 | The slow-lane shortlist does not arrive before a session (a ... | M, Money | F15, F2 | 2 | 1 | 2 | F15: B: the node must carry its own copies of kernel apps; F2: B: a check or judge that lives in an app has no default while the app is off |
| MIS-10 | The unit computed a reading while the MIS was down, but only the ... | M, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| MIS-11 | The shuffled-readings proof passes by construction, because units ... | M, Silent | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| MIS-12 | A new sensor is approved, and older records were labelled without it | M, Silent | F10, F1 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran; F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| MIS-13 | Templates wait to read MIS logs that never reach the PC, because ... | H, Stop | F8 | 2 | 2 | 2 |  |
| MIS-14 | A market's data level changes (a venue drops depth), and a sensor ... | M, Silent | F13, F19 | 2 | 1 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node; F19: B: market facts served by an app the node must reach |
| JR-01 | Two writers land on one unit journal: a demo twin on the PC and ... | M, Silent | F18 | 2 | 1 | 2 | F18: B: two judge apps can each count tries |
| JR-02 | The journal cannot be written before an order goes out (disk full, ... | M, Money | F9 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| JR-03 | A unit in an error loop logs every tick, and the log flood fills ... | M, Money | F9, F13 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down; F13: C: loses the mini-app health log and breaker for QMB and the node |
| JR-04 | Signals seen but not taken, and missed trades, are not recorded | H, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| JR-05 | A trade's world (backtest, paper, demo, live) is labelled wrongly | M, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| JR-06 | A unit goes back to paper, and paper trades mix into its live figures | H, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| JR-07 | Fills replayed after a reconnect land twice | H, Silent | F8 | 2 | 2 | 2 |  |
| JR-08 | Backfilled rows mix with live rows, so a live statistic includes ... | M, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| JR-09 | Rows from two machines with drifting clocks sort in the wrong order | M, Silent | F17 | 2 | 2 | 2 |  |
| JR-10 | Market facts (spread, fees, slippage) are copied into every unit ... | H, Stop | F3, F18 | 2 | 1 | 1 | F3: C: a QMB variant needs a host switch; a new node build is a host change; F18: B: two judge apps can each count tries |
| JR-11 | An agent's analysis written into a journal is later read as a record | H, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| JR-12 | The journal row shape changes partway through a unit's life | M, Stop | F1 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| JR-13 | A capped memory or journal silently drops old rows to stay under a ... | M, Silent | F14 | 2 | 2 | 1 | F14: C: no app manifest rights for the node |
| JR-14 | An artifact sits in a tool folder, outside the Library, and an ... | M, Silent | F10, F3 | 2 | 1 | 1 | F10: B: verdicts depend on which judge app version ran; F3: C: a QMB variant needs a host switch; a new node build is a host change |
| JR-15 | Imported broker fills carry no initial risk, so R is missing for ... | H, Silent | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| JR-16 | Journals made on the node must reach the PC; the one-way pull was ... | H, Stop | F8, F15 | 2 | 1 | 2 | F15: B: the node must carry its own copies of kernel apps |
| JR-17 | A failed effect is retried silently and lands twice, or is retried ... | M, Money | F7 | 2 | 2 | 2 |  |
| AG-01 | An agent never calls the unit checker | H, Silent | F12, F3 | 2 | 0 | 2 | B: the backstop at the Library door needs the checker in the kernel |
| AG-02 | An agent writes a unit with `python -c`, past a hook bound to ... | H, Silent | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| AG-03 | A slow check inside the 10 s guard blocks the tool call | M, Stop | F12, F13 | 2 | 0 | 1 | F12: B: the Library door cannot call a checker that lives in an app that may be off; F13: C: loses the mini-app health log and breaker for QMB and the node |
| AG-04 | A hook added mid-session only applies at the next launch | M, Friction | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| AG-05 | Workflow agent steps cannot write files, so a unit authored inside ... | H, Stop | F3 | 2 | 2 | 1 | F3: C: a QMB variant needs a host switch; a new node build is a host change |
| AG-06 | An agent grades its own unit, agrees with him, or several agents ... | H, Silent | F12 | 2 | 1 | 2 | B: the judge app version decides |
| AG-07 | A source (a video description, a forum post) carries instructions ... | M, Silent | F14, F13 | 2 | 2 | 1 | F14: C: no app manifest rights for the node; F13: C: loses the mini-app health log and breaker for QMB and the node |
| AG-08 | A cheap model uses a dictionary word wrongly | H, Silent | F12, F20 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off; F20: B: which QML, which judge, which catalogue app needs a page, not a sentence |
| AG-09 | Unit tools placed inside a mini app do not reach the default copilot | M, Stop | F3 | 2 | 0 | 2 | B puts unit tools in an app, cut from the default copilot surface |
| AG-10 | Two agents edit the same unit at once | M, Silent | F10, F18 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran; F18: B: two judge apps can each count tries |
| AG-11 | An agent loops on the checker (fix, new error, fix) for hours | M, Friction | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| AG-12 | An agent states a market value from its training memory | M, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| AG-13 | An agent proposes a promotion while he is away, and it is treated ... | M, Money | F16 | 2 | 2 | 1 | F16: C: no money-app signature on node versions; rebuilt by hand |
| AG-14 | The model provider is down overnight, and the slow lane fails | M, Stop | F15, F9 | 2 | 1 | 1 | F15: B: the node must carry its own copies of kernel apps; F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| AG-15 | A tool answer over 20,000 characters spills to the Library; the ... | M, Silent | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| AG-16 | Copilot and workflow agents see different tools for the same job | M, Friction | F3 | 2 | 2 | 1 | F3: C: a QMB variant needs a host switch; a new node build is a host change |
| WF-01 | A template needs a door that does not exist yet, installs as a ... | H, Friction | F13, F2 | 2 | 1 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node; F2: B: a check or judge that lives in an app has no default while the app is off |
| WF-02 | The `market_open` check holds crypto runs on Saturdays | H, Stop | F17, F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| WF-03 | Zone defaults disagree (templates London, the build skill Berlin, ... | H, Friction | F17 | 2 | 2 | 2 |  |
| WF-04 | A 24/7 market has no end of day, so "the nightly review" has no time | H, Friction | F17 | 2 | 2 | 2 |  |
| WF-05 | An event-trigger chain loops: a template lands an item that fires ... | M, Friction | F8, F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| WF-06 | A run pass minted on the PC fails at the server's door while the ... | M, Stop | F1 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| WF-07 | An agent step idles on a long tool and its cache expires | M, Friction | F11 | 2 | 2 | 1 | F11: C: a host update restarts trading |
| WF-08 | The `library` node kind is marked available but has no executor | M, Stop | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| WF-09 | A QMX update ships a newer template and overwrites the one he edited | M, Friction | F10 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran |
| WF-10 | A webhook trigger has no sender signature check | L, Silent | F14 | 2 | 2 | 1 | F14: C: no app manifest rights for the node |
| WF-11 | An analyst workflow marks its own forecasts | H, Silent | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| WF-12 | The shared judge step is edited, and every past verdict changes ... | M, Silent | F10, F1 | 2 | 1 | 2 | B: the judge app's version changes verdict meaning |
| WF-13 | A run's home machine dies mid-run | M, Stop | F7, F18 | 2 | 1 | 2 | F18: B: two judge apps can each count tries |
| WF-14 | The PC was off for two days and missed scheduled runs | H, Friction | F11 | 2 | 2 | 1 | F11: C: a host update restarts trading |
| MA-01 | A unit lives in a mini app, and the app's breaker stops it after 3 ... | M, Money | F16, F9 | 2 | 1 | 2 | B tempts units into apps; A and C keep orders in the node only |
| MA-02 | The machine an app lives on dies; a move is a snapshot plus a ... | M, Stop | F18, F10 | 2 | 1 | 2 | F18: B: two judge apps can each count tries; F10: B: verdicts depend on which judge app version ran |
| MA-03 | A newcomer installs an example app that imports deleted code and ... | H, Friction | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| MA-04 | An app's `provides` contract changes shape and its consumers break | M, Stop | F1 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| MA-05 | The trading node as a mini app is a `money` app, which needs his ... | M, Stop | F16, F11 | 2 | 2 | 2 | A: his signature binds a version, restarts need none (supervisor.py:542-547); C has no money app |
| MA-06 | `app_op {app: qmb}` fails because no app named `qmb` runs | H, Stop | F3 | 2 | 2 | 1 | C needs app_op rerouted to a host door |
| MA-07 | Several QMB variants are installed; which one does `backtest_run` ... | M, Silent | F2, F13 | 2 | 2 | 0 | C has no variants to choose between |
| MA-08 | A long backtest in an app needs more memory than he set | L, Stop | F14 | 2 | 2 | 1 | F14: C: no app manifest rights for the node |
| MA-09 | A mini app reads another app's output while that app is offline | M, Stop | F8, F15 | 2 | 1 | 2 | F15: B: the node must carry its own copies of kernel apps |
| MA-10 | Two mini apps, or two QMB variants, publish under the same ... | M, Silent | F4, F1 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| CA-01 | Routes carry no version and the API title is fixed at 0.1.0, so a ... | H, Stop | F1 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| CA-02 | The `unit` kind has an empty schema, so anything lands as a unit | H, Silent | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| CA-03 | "The bot may not size" is in four layers; a half-done change ... | H, Money | F1 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| CA-04 | Adding a venue means editing a closed enum in the node's law | H, Stop | F3 | 2 | 2 | 1 | F3: C: a QMB variant needs a host switch; a new node build is a host change |
| CA-05 | Errors come in different shapes: tools give code, message and next ... | M, Friction | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| CA-06 | The PC and the node run different contract versions after an ... | H, Stop | F1, F15 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic; F15: B: the node must carry its own copies of kernel apps |
| CA-07 | The risk socket is built now and the risk session's design does ... | M, Stop | F2, F1 | 2 | 1 | 2 | F2: B: a check or judge that lives in an app has no default while the app is off; F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| CA-08 | A unit's logic fingerprint does not match its stored source | M, Stop | F10 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran |
| CA-09 | The same capability exists through two doors with different rules | M, Silent | F3 | 2 | 1 | 2 | B: app operations and catalog rows both offer unit work |
| CA-10 | An outside agent's observer token outlives its purpose | L, Friction | F14 | 2 | 2 | 1 | F14: C: no app manifest rights for the node |
| CA-11 | A browser client cannot resume a stream, because EventSource ... | L, Friction | F8 | 2 | 2 | 2 |  |
| CA-12 | A copilot-made pack, app or Library kind takes a name the core ... | M, Stop | F4 | 2 | 2 | 2 |  |
| TN-01 | A reply is lost after an order went out; a resend opens the ... | M, Money | F7, F8 | 2 | 2 | 2 |  |
| TN-02 | The node crashes after a fill and before journaling it, leaving an ... | M, Money | F7, F9 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| TN-03 | He presses the kill switch while the node is offline or unreachable | M, Money | F9, F15 | 2 | 1 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down; F15: B: the node must carry its own copies of kernel apps |
| TN-04 | Two nodes run the same unit: a restored server image, or a PC ... | M, Money | F18 | 2 | 1 | 2 | F18: B: two judge apps can each count tries |
| TN-05 | A token expires at night, or a refresh on one machine logs out ... | H, Money | F18, F13 | 2 | 1 | 1 | F18: B: two judge apps can each count tries; F13: C: loses the mini-app health log and breaker for QMB and the node |
| TN-06 | The broker's weekend maintenance cuts the Open API and everyone ... | H, Stop | F11, F17 | 2 | 2 | 1 | F11: C: a host update restarts trading |
| TN-07 | An exchange halts or hits a price limit; orders are rejected and ... | L, Money | F19, F9 | 2 | 1 | 1 | F19: B: market facts served by an app the node must reach; F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| TN-08 | The node dies and cTrader has no dead man's switch, so only ... | M, Money | F9 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| TN-09 | Hyperliquid's dead man's switch cancels all open orders, stops ... | M, Money | F9 | 1 | 1 | 1 | a Hyperliquid reduce-only trigger order as the broker-side stop is unproven until the testnet probe (lead review gap, Part C) |
| TN-10 | The node looks finished but cannot trade. Its only host profile is ... | H, Stop | F2 | 2 | 1 | 2 | F2: B: a check or judge that lives in an app has no default while the app is off |
| TN-11 | The one-click server setup fails halfway (an expired Tailscale ... | H, Stop | F11, F8 | 2 | 2 | 1 | F11: C: a host update restarts trading |
| TN-12 | Self-healing loops: crash, restart, crash | M, Money | F9, F13 | 2 | 2 | 1 | C: healing the loop means restarting the host |
| TN-13 | The VPS provider reboots the server at 03:00 | H, Stop | F11, F7 | 2 | 2 | 1 | F11: C: a host update restarts trading |
| TN-14 | The WSL fallback shuts itself down when idle, its clock is ... | H, Money | F17, F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| TN-15 | The laptop sleeps or loses power during a rehearsal on the PC | H, Stop | F15, F13 | 2 | 1 | 1 | F15: B: the node must carry its own copies of kernel apps; F13: C: loses the mini-app health log and breaker for QMB and the node |
| TN-16 | Deploying one new unit restarts the node and every other unit | H, Money | F3, F11 | 2 | 2 | 1 | C: a node code change is a host restart |
| TN-17 | The PC and the server run different QMX builds, so a rehearsal ... | M, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| TN-18 | The node's disk fills and journal-before-dispatch blocks entries | M, Stop | F9, F13 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down; F13: C: loses the mini-app health log and breaker for QMB and the node |
| TN-19 | The socket to the broker stays open but delivers nothing (a ... | H, Money | F13, F9 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node; F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| TN-20 | A feed goes stale, and stale alarms flood every weekend | H, Money | F17, F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| TN-21 | Units outnumber what one connection allows (cTrader 50 requests a ... | M, Stop | F18, F14 | 2 | 1 | 1 | F18: B: two judge apps can each count tries; F14: C: no app manifest rights for the node |
| TN-22 | A quoting unit spends Hyperliquid's address action budget and then ... | M, Money | F14, F9 | 2 | 2 | 1 | F14: C: no app manifest rights for the node; F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| TN-23 | A partial fill: 1.3 lots of 2 fill, and the stop is set for 2 | M, Money | F7 | 2 | 2 | 2 |  |
| TN-24 | The broker rejects a stop as too close, or the market is closed, ... | H, Stop | F7, F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| TN-25 | The broker changes a symbol's lot step, margin or digits without ... | M, Money | F19, F10 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach; F10: B: verdicts depend on which judge app version ran |
| TN-26 | The venue switches a symbol to close only (cTrader trading-mode ... | L, Money | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| TN-27 | Proof-campaign and readiness machinery (about 11,900 lines) ... | H, Stop | F2 | 2 | 1 | 2 | F2: B: a check or judge that lives in an app has no default while the app is off |
| TN-28 | The observability stack is down, and trading must go on | M, Stop | F9, F13 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down; F13: C: loses the mini-app health log and breaker for QMB and the node |
| TN-29 | An automatic escalation fires falsely (a bad time source trips the ... | M, Money | F13, F16 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node; F16: C: no money-app signature on node versions; rebuilt by hand |
| TN-30 | The node on his PC needs a live key, and the QMX host refuses to ... | H, Stop | F18, F15 | 2 | 2 | 1 | C: the host refuses live grants everywhere; a host role must special-case it |
| TN-31 | A new trading server needs its own cTrader app, and Spotware takes ... | M, Stop | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| TN-32 | The node runs in a region far from the broker's servers | M, Money | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| TN-33 | A clock step or pause on the host corrupts every timing until resync | L, Silent | F17, F9 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| TN-34 | An "unused" module is deleted in the cut, and it was the one ... | L, Money | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| EX-01 | A cTrader spot event carries only the bid or only the ask | H, Silent | F5 | 2 | 1 | 2 | F5: B: two QML apps can disagree on when a block's value is knowable |
| EX-02 | cTrader depth is differential with no snapshot message, so after a ... | H, Silent | F11 | 2 | 2 | 1 | F11: C: a host update restarts trading |
| EX-03 | cTrader gives no trades tape, real volume or open interest, and a ... | H, Silent | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| EX-04 | cTrader history comes one side per request, one week per request, ... | M, Stop | F14 | 2 | 2 | 1 | F14: C: no app manifest rights for the node |
| EX-05 | The broker switches the Open API off for his account | L, Stop | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| EX-06 | CCXT symbols differ per exchange, and QMX's adapter refuses every ... | H, Stop | F3, F19 | 2 | 1 | 1 | F3: C: a QMB variant needs a host switch; a new node build is a host change; F19: B: market facts served by an app the node must reach |
| EX-07 | A CCXT unified method is missing on one exchange, or the exchange ... | H, Stop | F3, F12 | 2 | 0 | 1 | F3: C: a QMB variant needs a host switch; a new node build is a host change; F12: B: the Library door cannot call a checker that lives in an app that may be off |
| EX-08 | A CCXT upgrade changes an exchange's behaviour | M, Silent | F1 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| EX-09 | Hyperliquid keeps only the last 5,000 candles, so history must be ... | H, Stop | F15 | 2 | 1 | 2 | F15: B: the node must carry its own copies of kernel apps |
| EX-10 | Hyperliquid's nonce window, one agent per process and agent ... | M, Stop | F18, F17 | 2 | 1 | 2 | F18: B: two judge apps can each count tries |
| EX-11 | Above 1,000 open orders on Hyperliquid, new reduce-only and ... | L, Money | F9, F14 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down; F14: C: no app manifest rights for the node |
| EX-12 | Real futures order flow needs a paid feed, and whether a personal ... | M, Stop | F2, F3 | 2 | 1 | 1 | F2: B: a check or judge that lives in an app has no default while the app is off; F3: C: a QMB variant needs a host switch; a new node build is a host change |
| EX-13 | A futures unit's contract changes at the roll (ES.c.0 rolls by ... | M, Silent | F19, F10 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach; F10: B: verdicts depend on which judge app version ran |
| EX-14 | A futures-style CFD on cTrader has no expiry field and turns ... | M, Money | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| EX-15 | A CFD unit reads futures order flow as a proxy, and the price gap ... | M, Silent | F19, F17 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| EX-16 | IBKR needs a manual login each week; TopstepX bans orders from servers | L, Stop | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| EX-17 | A rate limit (HTTP 429) or a ban after bursts | H, Stop | F14 | 2 | 2 | 1 | F14: C: no app manifest rights for the node |
| EX-18 | A venue outage or a stale feed while units hold positions | M, Money | F9 | 2 | 2 | 1 | F9: C: trading shares a process with chats and the engine; an out-of-memory chat takes the loop down |
| EX-19 | Demo behaves differently from live (fills, spreads, liquidity), so ... | H, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| EX-20 | Perps funding flips sign, and a unit holds through the funding time | H, Money | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| EX-21 | MT5 forces Windows and a running terminal per account | M, Stop | F3 | 2 | 2 | 1 | F3: C: a QMB variant needs a host switch; a new node build is a host change |
| EX-22 | A crypto exchange lists a new contract, or delists one a unit holds | L, Money | F19 | 2 | 1 | 2 | F19: B: market facts served by an app the node must reach |
| DO-01 | Two monitoring stacks: the node's Grafana, Loki and Prometheus, ... | H, Friction | F3 | 2 | 2 | 1 | F3: C: a QMB variant needs a host switch; a new node build is a host change |
| DO-02 | Monitoring is off by default, no target is named, and he believes ... | H, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| DO-03 | OpenObserve has never run on real telemetry | H, Stop | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| DO-04 | Known monitoring gaps: incidents not exported, a copy age always ... | M, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| DO-05 | A restore drill or a restored backup cuts over automatically into ... | L, Money | F16 | 2 | 2 | 1 | F16: C: no money-app signature on node versions; rebuilt by hand |
| DO-06 | A restore brings back an old unit version and its old state | M, Silent | F10, F16 | 2 | 1 | 1 | F10: B: verdicts depend on which judge app version ran; F16: C: no money-app signature on node versions; rebuilt by hand |
| DO-07 | QMX on the PC updates while the node is trading | M, Stop | F1, F15 | 2 | 2 | 1 | C: updating QMX on a trading host restarts trading |
| DO-08 | The node's CI lane and the whole GitHub battery do not run on PRs ... | H, Silent | F12 | 2 | 0 | 2 | F12: B: the Library door cannot call a checker that lives in an app that may be off |
| DO-09 | Credentials from old Hermes logs get copied into the repo | M, Money | F14 | 2 | 2 | 1 | F14: C: no app manifest rights for the node |
| DO-10 | A health check checks the wrong thing, so the process is up while ... | H, Money | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| DO-11 | Alert fatigue from weekend and holiday alarms, so a real alarm is ... | H, Friction | F17, F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| DO-12 | The server firewall step locks him out | L, Stop | F11 | 2 | 2 | 1 | F11: C: a host update restarts trading |
| DO-13 | A store opens at a newer version than the code understands, after ... | M, Stop | F1 | 2 | 1 | 2 | F1: B adds a versioned contract between kernel and every app that holds kernel logic |
| DO-14 | Secrets leak onto a public surface (logs, a served page) | L, Money | F14 | 2 | 2 | 1 | F14: C: no app manifest rights for the node |
| CK-01 | His PC's clock drifts: Windows Time is stopped, start type Manual, ... | H, Silent | F17, F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| CK-02 | The DST mismatch weeks: London and New York are 4 hours apart ... | H, Money | F17 | 2 | 2 | 2 |  |
| CK-03 | A Singapore node and a London node keep different local times, and ... | H, Money | F17 | 2 | 2 | 2 |  |
| CK-04 | The time-zone database is pinned two IANA years old (2025.2 ... | M, Silent | F1, F13 | 2 | 1 | 1 | F1: B adds a versioned contract between kernel and every app that holds kernel logic; F13: C: loses the mini-app health log and breaker for QMB and the node |
| CK-05 | The broker's server runs at GMT+2 or +3, the history is UTC, and ... | H, Silent | F17 | 2 | 2 | 2 |  |
| CK-06 | Smeared and non-smeared time sources are mixed around a leap second | L, Silent | F17 | 2 | 2 | 2 |  |
| CK-07 | Backups, first start and the host's command line use the machine's ... | M, Friction | F17 | 2 | 2 | 2 |  |
| CK-08 | WSL's clock is unsynchronised | H, Silent | F17 | 2 | 2 | 2 |  |
| CK-09 | Hyperliquid rejects signed actions whose nonce falls outside its ... | M, Stop | F17 | 2 | 2 | 2 |  |
| CK-10 | A "same minute of the week over the last 20 weeks" baseline breaks ... | M, Silent | F17 | 2 | 2 | 2 |  |
| CK-11 | A cron time is skipped or repeated at a DST change | L, Friction | F17 | 2 | 2 | 2 |  |
| CK-12 | Exchange calendars lag (an open-source CME break still shown as ... | M, Silent | F10, F17 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran |
| CK-13 | "Five trading days" means nothing for a 24/7 unit | M, Friction | F17 | 2 | 2 | 2 |  |
| OP-01 | A newcomer's first install fails silently (wrong Python, `uv` ... | H, Stop | F13, F2 | 2 | 1 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node; F2: B: a check or judge that lives in an app has no default while the app is off |
| OP-02 | The first real start on his own folder, with his logins, has never ... | H, Stop | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| OP-03 | He promotes the wrong version of two units with similar names | M, Money | F16, F13 | 2 | 2 | 1 | F16: C: no money-app signature on node versions; rebuilt by hand; F13: C: loses the mini-app health log and breaker for QMB and the node |
| OP-04 | He is away for a week: units trade, nightly workflows fail, nobody ... | H, Silent | F15, F13 | 2 | 1 | 1 | F15: B: the node must carry its own copies of kernel apps; F13: C: loses the mini-app health log and breaker for QMB and the node |
| OP-05 | He edits a number in the UI while a trade is open | H, Money | F10, F11 | 2 | 1 | 1 | F10: B: verdicts depend on which judge app version ran; F11: C: a host update restarts trading |
| OP-06 | His laptop's C: has 16 GB free and something writes there (WSL, ... | H, Stop | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| OP-07 | One word means two things on his screens ("node setup" sets up a ... | H, Friction | F20 | 2 | 1 | 2 | F20: B: which QML, which judge, which catalogue app needs a page, not a sentence |
| OP-08 | Mock data on a screen looks real (a demo account shown as "IC ... | M, Silent | F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| OP-09 | He tests at the weekend, nothing trades, and it looks broken | H, Friction | F17, F13 | 2 | 2 | 1 | F13: C: loses the mini-app health log and breaker for QMB and the node |
| OP-10 | He presses kill twice, or resume while the cause is still there | M, Money | F7, F16 | 2 | 2 | 1 | F16: C: no money-app signature on node versions; rebuilt by hand |
| OP-11 | Speech-to-text puts a misheard name on a unit or template | M, Friction | F10 | 2 | 1 | 2 | F10: B: verdicts depend on which judge app version ran |
| RS-01 | The computed size is under the minimum lot (a $300 account), so it ... | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-02 | Self-tuning drifts toward bigger risk | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-03 | Correlation spikes across every unit at once | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-04 | The same idea on 1m and 5m, or 20 matches that are one bet | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-05 | The node's kill line flattens, while standing order 7 says a risk ... | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-06 | R is undefined when invalidation is a condition, not a price | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-07 | Size grows back after a cut; house money | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-08 | A placeholder sizer or exit reaches live | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-09 | Margin jumps at the session close (futures intraday against ... | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-10 | Two units on one netting account | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-11 | A daily loss limit must fire with the PC off; no account guard ... | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-12 | An automatic fallback to general settings after a drift alarm ... | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-13 | A gap through the stop makes a loss bigger than 1R | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-14 | Perps funding eats a scalper's edge | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-15 | The kill-switch matrix values are blank and operator-owned | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-16 | The old system's special ("radioactive") sizing must be accounted ... | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-17 | A decay alarm suggests "back to paper", but only a risk rule may ... | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |
| RS-18 | Leverage changes on a venue (Hyperliquid `setLeverage`, broker ... | risk session | socket | 2 | 2 | 2 | every version leaves the same socket and journal fields; the content is the risk session's |

## 7. The pick: Version A, with five refinements from the party

**Why A.** It is the simplest version that handles the hard cases: every core piece exists once, so nothing that must agree with itself can drift, and everything that may need a second version or a machine of its own is an app with the health log, breaker, signature gate and home machine the mini-app core already gives (G4b Q5). B handles growth well and agreement badly. C handles agreement well and growth badly, and fails ruling 22.

**Refinements found in the party, each now in the spine:**
1. **The MIS splits by job.** Execution-health readings (spread against usual, quote gaps, feed state, spread quality) run inside the node as its own guards, because the node's feed keeper holds the only live connection on that machine and a guard must not depend on another app. Market-state readings (volatility state, trend against range, efficiency ratio, funding state and the rest) are the MIS app's; its instance on a trading machine reads that machine's market-data store. A unit that needs any reading at tick speed computes it itself from the catalogue's code (spine AD-40).
2. **A unit's size travels as CT-23 format version 3, never as a new field.** CHECKED by running `br1_ct23_sizing.py` against the exported `c93407ca`: an entry intent with a `requested_quantity` key passes both `qmf.risk.door.parse_inbound_intent` and `qml.protocol.accept_intents` and the size is silently dropped; the same intent stamped `contract_format_version: 3` is refused by both as an unsupported capability. Only `requested_r` is refused today (AD-18).
3. **The PC pulls journals and MIS history from each node, with a host pass.** The PC is home and writes its own store; the node needs no key to the PC and keeps every partition until the PC confirms a verified copy. The known gap (a run pass minted on the PC fails at a server's door, G2 §6) is named as a prerequisite (AD-28, AD-44).
4. **Two nodes on one account are stopped by the broker, not by a lease service.** A deployment names one machine identity (QMN already pins it, `qmn/src/qmn/host/configured_runtime.py:278-280`); every client order id carries the node's id, so a start-up reconcile sees a foreign claimant and refuses that account (AD-8, AD-38).
5. **The node's shell is deleted in one wave with three callers moved.** CHECKED by import scan (`br4_node_shell.py`): nothing outside `qmn/` imports `qmn.seats`, `qmn.promotion`, `qmn.paper`, `qmn.host`, `qmn.bench` or `qmn.observability`; the three callers to move are `qmx_tools` (`qmn.doors.api`), `qmn.capital.kill_line` (`qmn.paper.demotion`) and `qmn.mis.regime_register` (`qmn.promotion.hub`) (AD-36).

## 8. The losers, and what is kept from each

| From | Kept | Dropped, and why |
| --- | --- | --- |
| B | QMB, the trading node and the MIS publisher as apps; a unit-holding app template for research, backtests and paper (lead's review, settlement 2); the dictionary's growth as a workflow template, not core code | the checker, the judge, the catalogue and the market facts as apps: each is a place two versions must never disagree |
| C | no new machinery where the core already does the job; the node's organs stay libraries; the trading role is a host profile (a setting), not a new program; PR 204's one landing function stays the landing | QMB as a host door (no variants, ruling 22); the node as a role inside the host process (a host update or crash touches trading) |

## 9. The verdict per part: core, or a mini app with defaults

| Part | Verdict | Why |
| --- | --- | --- |
| QML with the dictionary | core | two QMLs would give two meanings of one unit; "a small mistake in there is very costly" (T3:1264) |
| The unit template and its checker | core (a Library kind, a schema, a checker in QML) | units are records two apps run; the checker is the door no path skips |
| The judge and the try ledger | core | a swapped tester must not change the score |
| Instrument, venue and account records | core (Library kinds, a snapshot on every trading machine) | every part reads them; a unit must size with the Library down |
| Journals and records | core | one envelope everyone slices by |
| The Library | core (built) | the centre (ruling 51) |
| Contracts and APIs | core | the rules every shape follows |
| The copilot and agents | core (built), changed by registration only | ruling 24 |
| Workflows and templates | the engine is core (built); templates are content | removable and improvable (ruling W-01) |
| The mini-app core | core (built), fixed only where it blocks | ruling 46 |
| QMB | **mini app**, risk `runs`, installed by default | he may build a new version or run several (ruling 22) |
| The trading node | **mini app**, risk `money`, installed by default for practice | contained so the kill switch works; a server of its own (rulings 27, 43) |
| The MIS | reading blocks core; **publisher a mini app**, risk `shows`, PC and node instances | readings must be one code in QMB and live; the process lives on machines |
| External connections | core ports, adapters behind them | a new venue is a declaration plus an adapter |
| DevOps and clocks | core (mostly built) | one place to look, one time scale |
| The host | core (built), with a new trading profile | the one composition root per machine |

## 10. Deep modules on the winner (`codebase-design`)

| Module | Interface (what a caller learns) | What it hides | Deletion test | Seam and adapters |
| --- | --- | --- | --- | --- |
| QML door | five verbs: `new`, `check`, `compile`, `find`, `explain` | slot resolution, combiners, motion engine, units of measure, the conformance layers, the catalogue snapshot | delete it and every host builds factories and execution inputs by hand, as the QMB fixtures do today (G1 §3.3): earns its keep | the BotFactory seam (structural, CHECKED by `br2_factory_seam.py`); two real callers, QMB (`qmb/host/adapter.py:59`) and the node (`qmn/seats/host.py:255`, moving to the node shell) |
| The checker | `check(document) -> problems` | seven layers; the sandbox run on recorded bars | delete it and checks scatter into templates and hooks: earns its keep | four entry points over one function (catalog row, Library save, template step, hook); the function is the seam, the entry points are not adapters |
| The judge | `judge(result ids, study spec) -> verdict` | the chain, presets, shrinkage, clustering, the try ledger | delete it and every template copies gate scripts again (`b`, `d3` today): earns its keep | one adapter; an internal seam only |
| Instrument records | `get(venue, symbol, at)`; the snapshot | refresh jobs, conversions, calendars, data levels | delete it and sizers read raw venue documents live, and QMB cannot replay past facts: earns its keep | refresh adapters per venue (cTrader, CCXT): a real seam |
| Journal writer | `write(envelope, body)`; `journal_query` | partitioning, one writer per partition, the shipping job | delete it and QMB and the node each invent row shapes: earns its keep | one writer library used by QMB and the node: an internal seam |
| QMB contract | the app's operations and the `backtest-result` shape | the 91,000 lines | delete the contract and variants cannot be compared: earns its keep | a real seam: today's QMB, any variant, and the conformance pack as the test adapter |
| Venue-client port | `open_session`, `submit`, `observations`, `reconcile`, `verify_capabilities` | wire formats, rate limits, protection rules per venue | a real seam: cTrader now, CCXT next | futures clients are one-adapter seams: kept as declared placeholders, not code |
| Data-route port | `levels`, `subscribe`, `history` | normalising prints, quotes, books, bars | a real seam: cTrader, CCXT, two downloaders | Databento stays a key check (no adapter now, lead's review) |
| The node app | its operations (`status`, `deploy`, `pause`, `resume`, `kill`, `flatten`, `mode`, `self_test`, `passport`) | feed keepers, unit runtime, guards, reconcile, healing, shipping | delete the shell and the organs have no supervisor; keep the organs as libraries | one adapter per placement (PC practice, server live); a real seam because two placements exist |

**Shallow spots to avoid (from the deletion test):** a QML verb that only forwards to QMB (backtest is QMB's, not QML's); a "unit service" beside the catalog (a second door, contracts §3 Shape B); an app operation per catalogue entry (the catalogue is data, not operations).

## 11. Words, fixed once

The glossary (`GLOSSARY.md`) fixes the words this architecture uses: unit, unit document, slot, block, catalogue, dictionary entry, reading, number kinds, motion, calibration row, placeholder, market, instrument record, data level, world, lifecycle state, market settings and market version (working words he may rename), try, study spec, verdict, baseline card, the journals, deployment, trading node, server, This PC, profile, feed keeper, kill switch, risk stop and health stop, heal, regime and volatility state, session, office time, R.

## 12. Lead's calls made in this step

Logged with what, why and how to undo in `architecture/level-0/LEAD-CALLS.md`, ids LC-A0-01 to LC-A0-08: the pick of A; the MIS split by job; CT-23 format version 3 for sized intents; the PC pulls journals; machine-pinned deployments with node-tagged order ids; the node app inside the host supervisor; the judge as its own core package; A's accepted risk on in-process units.

## 13. Quote check

Every `"quote" (Tn:line)` in this folder was checked by `quotecheck.py` (this agent's scratchpad), which opens each transcript with `newline=''`, splits on `\n` only and normalises whitespace and curly quotes. Result on 31 Oct after the last edit, over this folder, the Level 0 folder and `01-connections.md`: 24 quotes found on their cited lines, 0 not (22 in the party transcript, 1 here, 1 in the spine).
