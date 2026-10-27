# 10: The Hermes / Stats gold mine for QML

Research file for the unit work. Read-only study, 2026-10-27. No files changed outside this one.
Labels: **CHECKED** (I read it, path and position given), **REMEMBERED** (the operator said it), **INFERRED** (my reasoning).

Citation keys used below:

| Key | What it is |
| --- | --- |
| `GEN Lnnn` | `C:\Users\Mubarak\Desktop\Stats\.hermes\orchestration\transcripts-lineage\20260824_121737_86f88c-friendly-greeting.md`, line nnn (the genesis session) |
| `PKG` | `C:\Users\Mubarak\AppData\Local\hermes\cache\delegation\subagent-summary-1-20260824_170919_175475.txt` (the "strategy-package bot", 24 Aug, full text) |
| `EXP` | `...\delegation\subagent-summary-2-20260824_170919_180173.txt` (the "experiment-design bot", 24 Aug, full text) |
| `DOS` | `...\delegation\subagent-summary-0-20260825_132506_664562.txt` (25 Aug recovery dossier, quotes genesis messages M7xx-M9xx) |
| `DB n` | `C:\Users\Mubarak\AppData\Local\hermes\state.db`, table `messages`, `id = n` (read with `mode=ro`) |
| `RES #n` | `C:\Users\Mubarak\Downloads\hermes-resume-session-from-saved-json-file-20260826.json`, `messages[n]` |
| `GMX #n` | `C:\Users\Mubarak\Downloads\hermes-extract-strats-gold-mine-design-work-20260826.json`, `messages[n]` |
| `S27 #n` | `C:\Users\Mubarak\Desktop\strats\resume-strats-ground-state-work-20260827.json`, `messages[n]` |
| `GS Lnnn` | `C:\Users\Mubarak\Desktop\Stats\STRATS-GROUND-STATE.md`, line nnn |
| `GMA` | `C:\Users\Mubarak\Desktop\Stats\.hermes\orchestration\resume-20260826\gold-mine-session-analysis.md` |
| `DNA Lnnn` | `C:\Users\Mubarak\Desktop\Stats\schema\strategy-dna.md`, line nnn |
| `REC §n` | `DB 5678`, the 26 Aug "STRATS design-decision recovery" (56K chars, 20 sections) |

---

## 0. The short version

1. **Canonical folder: `Desktop\Stats`.** It holds the library (built 1 Sep) and, under `.hermes\orchestration\`, the whole design history. `Desktop\strats` is an empty husk: folders named `-C`, `-xzf`, `tar` and `strats-scaffold.tgz` from a broken unpack command, an empty git repo, and one 8-message export. CHECKED (§1.2).
2. **Correction to the premise:** Hermes did not build QML. On 24 Aug the operator said QML already existed "inside the latest version, it's a library in there" (`GEN L1431`, CHECKED). Hermes built **STRATS**, a strategy *knowledge* library and dictionary that QMX was meant to adopt. Today's plan merges the two: QML becomes the unit library, and STRATS supplies its dictionary, idea records and lineage rules. INFERRED.
3. **The richest design text is not in Stats.** It sits in Hermes's own store under AppData (`state.db`, 309 MB, and the delegation cache). Two 24 Aug subagent outputs (`PKG`, `EXP`) are the best pieces and exist only there. CHECKED.
4. **Gold to keep:** the three layers (dictionary → role binding → logic graph), DNA A–I with honest "class" and exit labels, variants as small *edit operations* on a parent, a lineage DAG with typed edges, named graph ports for combining strategies, "one source, one home" provenance with per-claim locators, and the old experiment contract (result identity, tries control, signal funnel, marginal value to the book). CHECKED (§2).
5. **Q2 answer from the old design:** a change of environment (costs, data, book, tester version) is a *re-run of the same unit*, not a new one; a fix to a wrong extraction is a *corrected successor*; a mix of two parents is a *composite* with both parents named; and whether a change is "new" can be read from the *kind of edit operation*. This fits and sharpens T2 option A. CHECKED (`PKG`, `EXP`), INFERRED mapping (§5).
6. **Rejected then and still right:** specialist fleets, curator and promotion ceremony for library entries, staging and release machinery, one overall confidence score, one "magical best" variant, invented exits. **Rejected then and now wrong:** "sizing and exits are the book's job", "no experiment records", "QMX stays out". Those were placement calls for an older QMX, and corrections 2-3 reverse them. INFERRED (§3).
7. **The biggest thing the operator may not see:** STRATS stored *ideas* (often incomplete, not runnable). A unit is a *runnable program*. The new unit spec has only a one-word `source` field. QML needs an idea record in front of units, or provenance stays a string. INFERRED (§6).

---

## 1. Timeline and folders

### 1.1 Which session did what

Times are local (session IDs carry local time). Every row is CHECKED against `state.db` table `sessions` (`cwd`, `title`, `model`, `started_at`) unless marked.

| When | Session / actor | Folder | What happened |
| --- | --- | --- | --- |
| 24 Aug 12:17-18:40 | `20260824_121737_86f88c` "Friendly greeting", gpt-5.6-sol, plus ~10 child subagents | `Desktop\Stats` | **Genesis.** Operator's four pillars (level, trigger, confirmation, risk) were turned into primitive → role binding → logic graph (`DOS` §1, quoting M795, M831). Strategy package, variants as overlays, lineage DAG, experiment contract, MIS rule, mini-KBs, Prime Terminal study (`GEN L760-1041`, `L1340-1428`). Operator's long reaction (`GEN L1429`). Rounds 1-3 of plans and reviews by DeepSeek, Terra, Luna, Kimi, GLM (`Stats\.hermes\orchestration\round-1..3`, `reviews\`). Population mandate (`GEN L3459`; `user-corrections\2026-08-24-population-mandate.md`). Phase-0 source inventory of 359 NotebookLM sources (`round-3\phase-0\source-inventory\`). |
| 25 Aug 11:55-13:25 | `20260825_115530_94412f` "Continue STRATS Forex context library", gpt-5.6-sol | `Desktop\Stats` | **The "gold mine".** Agent re-read genesis; operator dictated two long turns (`DB 2717`, 22.6K chars; `DB 2725`, 34K chars): STRATS is a knowledge base, n8n and Gemini for intake, 7,000-strategy scale, global index "like skills", experiments "like a Git worktree" but belonging to QMX. Recovery dossiers written by subagents (`DOS` and two siblings). |
| 26 Aug 08:12-11:22 | same session, after compaction | `Desktop\Stats` | Operator's "good morning" prompt (`DB 3262`, `DB 3449`). Agent regressed: probed models, wrote a shared contract, launched 4 dictionary workers (`Stats\.hermes\orchestration\dictionary-wave-1\`). Internet dropped; 2 of 4 died. Operator froze the run (`REC §18`). |
| 26 Aug 07:59, 09:00 | `20260826_105921_08008d` (Terra, "Build source-native strategy primitives"); `20260826_115957_94063f` (DeepSeek continuity audit) | `Desktop\Stats` | Worker and auditor sessions. |
| 26 Aug 11:53-15:30 | `20260826_115355_ae94f7` "Resume session from saved JSON file", gpt-5.6-sol = **`RES`** | `Desktop\Stats` | Resumed the two dead workers; 239 dictionary entries in total (`RES #156`). Operator pushed back: "I feel like you are missing some information" (`RES #168`). `RES #0` carries the operator's comments on parts A–I, including the genetic-lineage idea (§2.9). |
| 26 Aug 16:06 | `20260826_160607_5e547b` "Extract STRATS gold mine design work", gpt-5.6-sol = **`GMX`** | `Desktop\Stats` | Wrote `GMA` (1,005 lines): reconstruction, poison register, next steps = layout before population (`GMX #0`, `#299`). |
| 26 Aug 18:04 | `20260826_180446_36307b` "Recover STRATS design decisions", gpt-5.6-sol | (none) | **`REC`**: the fullest single recovery (20 sections). |
| 26 Aug 19:12 | GLM 5.2 audit session (named in `GS L37`; not matched by title in `state.db`) | `Desktop\Stats` | Wrote `STRATS-GROUND-STATE.md` (596 lines), the grounding document. |
| 27 Aug 09:49 | `20260827_094900_b1c59f` "Resume strats ground state work" = **`S27`** | `Desktop\Stats` | Proposed the corrected empty tree: flat `strategies/`, dictionary by concept family, indexes not copies (`S27 #7`). Also patched the Hermes skill to drop the compulsory curator rule (`S27 #4`). |
| 1 Sep 13:09-13:25 | **Not a Hermes session.** No `state.db` session exists on that day. INFERRED: another tool. | `Desktop\Stats` root | **The build.** Root `README.md`, `STRATS-BUILD-STATE.md`, `schema\` (DNA A–I lock, `ids.md`, `graph.yaml.md`, `strats.sql`), `dictionary\` (239 entries moved, byte-identical to the `.hermes` candidates: `cmp` CHECKED for the exits file, equal sizes for all four), `backend\` (import, export, validate; derived `strats.sqlite`), templates and the demo `STRAT-000001`. CHECKED file times. |
| 15-16 Sep | unknown tool | `Desktop\strats` | A broken unpack left empty folders `-C`, `-xzf`, `tar`, `strats-scaffold.tgz`. `strats-tmp\.git` points at `github.com/MubarakHimself/strats.git` with message "Initial scaffold: hypothesis library layout", but **no commit exists** (`git log`: "does not have any commits yet"; the only object is the empty tree). The 27 Aug session export was saved here on 16 Sep. CHECKED. INFERRED that it was a failed attempt to put Stats on GitHub. |
| 13 Oct | unknown tool | `Desktop\Stats\.reticle\` | A tool opened the folder. CHECKED (mtime). |
| 20-24 Oct | QMX unit research | worktree | `01-ground-truth.md:116` cites the Stats dictionary (239 entries, 9 collisions, about 7 runnable); ruling 16 calls the Stats design "reference only"; `decisions.md:53` calls it "a good seed, rebuilt and enhanced". CHECKED. |
| 27 Oct 06:01 | operator | `Downloads` | Exported the two 26 Aug sessions as the JSONs in this brief. CHECKED (`exported_at`). |

### 1.2 Which folder is canonical, and why we looked at the wrong one

| Folder | Verdict | Why |
| --- | --- | --- |
| `Desktop\Stats\` (root files) | **Canonical library.** | Holds the built tree, schemas, dictionary and templates. Its own authority order: operator > `STRATS-BUILD-STATE.md` > `STRATS-GROUND-STATE.md` (`Stats\README.md:77`). CHECKED. |
| `Desktop\Stats\.hermes\orchestration\` | **Canonical history**, with known poison. | Transcripts, rounds 1-3, recovery files, `GMA`. `GS L483-515` lists the poisoned files (stale "authoritative" pointer, round-3 software plan, false "no OpenCode" rule). CHECKED. |
| `AppData\Local\hermes\state.db` and `cache\delegation\` | **Richest originals.** | Full text of the 24-26 Aug messages and subagent outputs (`PKG`, `EXP`, `DOS`, `REC`). Not in any repo. CHECKED. |
| `Desktop\strats\` | **Not a library.** | Empty folders and an empty repo, plus one 97 KB export of the 27 Aug session. Its only value is `S27 #7`, the tree proposal that 1 Sep built. CHECKED. |
| `C:\Users\Mubarak\.hermes\` | **Irrelevant.** | `config.yaml` registers one MCP server; `orchestration\ucsatp-ews-20260903\` is an unrelated survey-analysis job. CHECKED. |

**Why the wrong one:** the names. The library folder is "Stats" (a typo of STRATS; `IDEA.md` reads "traing strategies and and ideas knowledgebase"), the project is "STRATS", and the husk is "strats". A search for "strats" lands in the husk. INFERRED. Our own 01 research did reach `Stats\dictionary\` (`01-ground-truth.md:116`, CHECKED) but read only the 239 entries. It never read the design behind them (DNA, graph contract, lineage, the experiment contract). That is the real miss. INFERRED.

---

## 2. The gold mine: what is worth keeping

### 2.1 Three layers, not four pillars

- The operator began with four pillars: level, trigger, confirmation/filter, risk/management. He said each pillar can hold "any number of components" and is "not finite" (`DOS` §1, quoting M779). CHECKED.
- Genesis turned this into three layers (`DOS` §1, quoting M795 and M831). CHECKED:
  1. **Dictionary** (primitives): "What things exist?"
  2. **Role binding**: "What job does this primitive perform here?"
  3. **Logic graph**: "How are the bound components combined?"
- The key sentence: "The true reusable unit is: primitive + role binding + timing + parameters + scope + evidence + data provenance" (M795, via `DOS` §1). CHECKED.
- Primitives have no fixed role. Bullish engulfing can be a level builder, trigger, confirmation or exit; RSI can trigger, confirm, filter a regime or exit (`DB 4065`, "Example: bullish engulfing pattern"; `GS L123-141`). CHECKED.
- The four pillars survive as a **human checklist view**, not folders (`DNA L126-140`). CHECKED.
- **Match with today:** QML already has CT-34 leg roles `level | trigger | confirmation | filter` in `qml/src/qml/declaration/confluence.py` (`04-platform-study.md` §3.2, CHECKED there). Those are binding roles, which is exactly the STRATS rule. The operator's 27 Oct ruling Q8 ("types are defaults, never a cage; the same goes for the dictionary", STATE.md:40) is the same principle. INFERRED.

### 2.2 Coordinates, timing and entry rules

- **A timeframe or session is a coordinate, not a level.** "London session" is context; "London-session high" is a level. Sniping "can use a level, but it is not itself simply a level": it is a composite of level, time window, narrow trigger, execution policy and tight invalidation (`DB 4065`, sections "Timeframes and pairs are coordinates" and "Sniping spans several roles"). CHECKED. This supports keeping sniping windows *inside* a unit (07 F-8). INFERRED.
- **Three confirmation timings:** pre-trigger filter, synchronous confirmation, post-trigger confirmation. Post-trigger confirmation moves the real entry price, so a backtest cannot use the trigger price (M795 via `DOS` §2). CHECKED.
- **Trigger ≠ order. Invalidation ≠ stop.** A finished trigger is not a market order; a broken level can cancel a setup without being a stop (`DNA L137-138`; `GS L186-215`). CHECKED.
- **Trigger and confirmation are the biggest search surface.** The safe order: fix the location and context, compare trigger families, keep a few robust ones, add one confirmation family at a time, measure the gain, test interactions last, then challenge across pairs, costs and regimes. "Otherwise, unlimited components create a combinatorial search engine that will eventually 'discover' noise." (`DB 4065`, "Trigger and confirmation are probably the largest optimization surface"). CHECKED.

### 2.3 The logic graph (`graph.yaml`)

- Operators: `ALL/AND`, `ANY/OR`, `NOT`, `K_OF_N`, `sequence`, `within`, `arming`, `reset`, `cooldown`, `re-entry`; long and short may be asymmetric and must not be silently mirrored (`Stats\schema\graph.yaml.md:22-36`). CHECKED.
- Node kinds: `primitive | operator | state | action | condition`; each primitive node carries `role`, `timing`, `session`, `direction`, `params`; unresolved values stay explicit (`graph.yaml.md:40-58`). CHECKED.
- An `exit:` block with five slots (invalidation, stop, targets, exit, management) and a `lifecycle:` block (arming, reset, cooldown, re-entry) (`graph.yaml.md:75-102`). CHECKED.
- **Named ports for combining strategies:** `setup_signal`, `entry_signal`, `invalidation_signal`, `exit_signal`, `regime_filter`. A composite imports ports from its parents, never their insides, with `conflict_policy: error` (`PKG`, "Strategy graph" and "Lineage DAG"). CHECKED. Not carried into the 1 Sep build. CHECKED (absent from `graph.yaml.md`).
- Worked example: `STRAT-000001` = ALL(Asian session high, liquidity sweep, bullish engulfing, London window) THEN enter long (`Stats\strategies\STRAT-000001-asian-high-london-reversal\logic\graph.yaml`). CHECKED. It is a layout demo, not an extracted strategy.

### 2.4 Strategy DNA A–I (the candidate record)

`Stats\schema\strategy-dna.md` locks nine parts (`DNA L33-43`). CHECKED:

| Letter | Part | Rule worth keeping |
| --- | --- | --- |
| A | Identity and class | Class is exactly one of `complete`, `entry_hypothesis`, `fragment`, `descriptive_pattern`, `composite` (`DNA L45-56`). |
| B | Evidence map | Locators, quotes, timestamps, frames, claim-to-rule links; evidence class per statement: source-stated / visual / inferred / standardized / unresolved. "Model output is interpretation, not ground truth." (`DNA L57-60`) |
| C | Primitive references | Point to the dictionary; never redefine. |
| D | Role bindings | Role, pair, timeframe, session, direction, timing, parameters, for this candidate only. |
| E | Logic graph | §2.3. |
| F | Exit completeness | Each slot labelled `source_defined`, `external_policy`, `deliberately_open` or `unresolved`. **Do not invent exits.** (`DNA L89-110`) |
| G | Dependencies and assumptions | Data, venue, bar construction, timezone, costs, transfer caveats (futures source → spot). |
| H | Unknowns and ambiguity | Searchable, not buried. |
| I | Lineage | Parents, variants, composites, semantic diff; a DAG. |

Also the 14-section long form (`GS L186-218`) and the per-file split inside one strategy folder (`DNA L144-168`). CHECKED.

### 2.5 The dictionary

- 239 entries in four family files, each with 12 fields: family, aliases, definition, boundaries, observable inputs, recognition semantics, parameters/profiles, eligible roles, market/data constraints, transfer notes, evidence/status, uncertainty/variants (`Stats\dictionary\README.md:27-42`). CHECKED.
- 10 family folders; 6 are still empty: indicators, liquidity/volume/order flow, time/sessions, execution, risk/sizing, market data (`ls Stats\dictionary\*`). CHECKED.
- 9 slugs collide across files (`liquidity-sweep` ×3; `vwap`, `order-block`, `fair-value-gap`, `moving-average`, `bollinger-bands`, `donchian-channel`, `keltner-channel`, `volume-profile` ×2); uniqueness is `(file_path, id)` (`Stats\catalog\dictionary-collisions.md`). CHECKED. 07 foundation 9 already plans to fix them (`07-funnel.md:659`). CHECKED.
- **Exits are already the richest family:** 57 entries, including level vs setup invalidation, structural/volatility/time/session stops, trailing, break-even, partials, exit ladder, close-confirmed vs intrabar exit, target-to-trail, spread-aware exit, re-entry, cooldown (`Stats\dictionary\invalidation-exits-and-management\exits-execution-management.md:13-853`). CHECKED.
- **It already holds a sizer menu:** `fixed-fractional-risk-sizing`, `fixed-cash-risk-sizing`, `fixed-notional-sizing`, `stop-distance-position-sizing`, `scale-in` (same file, lines 658-718). CHECKED. These match the MT5 "Money" modules 04 recommends (`04-platform-study.md` §3.5). INFERRED.
- **Execution contexts per market:** `otc-fx-execution-context`, `crypto-spot-execution-context`, `centralized-futures-execution-context`, `order-book-data-scope` (lines 733-778). CHECKED. Useful for "any instrument".
- **Relationship types between entries:** alias-of, equivalent-to, broader/narrower, profile-of, derived-from, constructed-from, depends-on, compatible-with, incompatible-with, often-composed-with, contradicts, supersedes (`GS L176-177`). CHECKED.
- **Weak points:** 86 of 239 entries say "needs source evidence" (`GS L79-86`). They are prose definitions; about 7 have runnable code (`01-ground-truth.md:116`). They were written after the compaction by workers the operator later called premature (`REC §18`). CHECKED.

### 2.6 Variants as edit operations

- "Variants should store semantic operations, not copied strategy graphs" (`PKG`, "Overlays and exact diffs"). CHECKED. The operation list:
  `add_binding`, `remove_binding`, `replace_parameter`, `add_constraint`, `remove_constraint`, `connect`, `disconnect`, `replace_subgraph`, `change_timing`, `change_entry`, `change_exit`.
- Every derived candidate records its ordered stack of operations and the resulting graph digest. Applying an operation to a stale parent fails; no "last write wins" (`PKG`). CHECKED.
- The baseline is "immutable once published; corrections create a successor node" (`PKG`, "Baseline"). CHECKED.
- Operator's reaction: "sweep B ... overlay sweep version one ... I like this lineage, I like it" (`DB 4066`, replay of genesis M975). CHECKED.

### 2.7 Lineage DAG

- Edge types: `derived_by_overlay`, `composed_from`, `merged_from`, `corrected_from`, `supersedes` (`PKG`, "Lineage DAG"). The 1 Sep SQL keeps `variant_of | composite_of | derived_from | supersedes` with a `delta` column (`Stats\schema\strats.sql:90-96`). CHECKED.
- Rules (`REC §14.1`, CHECKED):
  - a source-faithful baseline is never silently overwritten;
  - a changed trigger, filter, location, exit or parameter makes a traceable child;
  - a composite names all its parents;
  - "a generated composite must not be represented as if one source taught it";
  - source-defined and agent-generated variants stay distinguishable.
- **No single "magical best" variant.** Several can be valid by pair, session, cost or book (`REC §14.2`). Operator's wording: "it's not that we don't need one, over time we can create one, but it doesn't mean it's the only one" (`DB 4066`). And: "some bots might be good, they don't need succession ... we just make a new variant" (`RES #0`). CHECKED.

### 2.8 Sources and provenance

- **One source, one home:** `sources/items/SRC-NNNNNN-slug/` with `manifest.md` (kind, locator, creator, publisher/channel, rights, hash, acquired, duration, transcript availability). Indexes by creator, channel, playlist, publisher and modality are pointers, not copies (`Stats\schema\ids.md:134-151`; `sources\items\_template\manifest.md`). CHECKED.
- **Nine evidence layers**, never flattened: raw source, manifest, normalized transcript, frames/OCR, transcript-to-visual alignment, atomic claims with locators, model interpretation, dictionary mappings and graph, later empirical results kept separate (`GS L222-232`). CHECKED.
- **Six confidence dimensions, no single score:** extraction confidence, rule explicitness, source quality, ambiguity, empirical status, portability. "High extraction confidence ≠ edge. Low extraction confidence ≠ bad strategy." (`GS L234-236`). CHECKED. Matches DEC-0162 (no stored composite scores, STATE.md). INFERRED.
- **Promotional claims are kept and labelled** (win rates, testimonials, course funnels), never used as rule evidence (`REC §7.4`). CHECKED.
- **One source can yield many outputs:** several strategies, a partial setup, primitives, creator definitions, mini-KB notes, performance claims (`REC §8.3`). CHECKED.
- **Seeds, not corpus:** a playlist or notebook is a starting point to expand and deduplicate (`REC §8.2`). CHECKED.
- **Inventory already done:** 359 NotebookLM sources in 6 notebooks (294 YouTube, 58 web); title triage: 46 priority-forex, 11 cross-market, 70 tool/implementation, 214 out of scope (`round-3\phase-0\source-inventory\notebooklm-inventory-summary.md`; `title-triage-report.md` §1). CHECKED.
- **Cheap first:** yt-dlp, ffprobe/ffmpeg, caption parsing, hashing and MarkItDown before any model reads anything; a 10-stage video pipeline, transcript first, frames only for chosen windows (`GS L296-327`). CHECKED.

### 2.9 Exits, sizing and the operator's genetic idea

- **Exit rule (operator, 24 Aug):** keep a strategy's own stop and exit; if it has none, a fallback may come from outside; reusable exits are one canonical module referenced by many bots, "not ... ten unrelated inventions". Example: `opposing-liquidity-exit-v1` referenced by bots A, B and C (`DB 4065`, "Your exit-mechanism ruling fits better than I expected"). CHECKED.
- **Operator, 26 Aug:** missing exits should not block a strategy: "QMX ... can suggest exits. However, a bot most times will have its own exits" (`RES #0`). CHECKED.
- **Sizing:** genesis withdrew Kelly as a STRATS default and left sizing to the book (`DB 4065`, "Kelly: I withdraw the premature recommendation"). CHECKED. Correction 2 now puts sizing in the unit (STATE.md:20). So this boundary is out of date (§3).
- **Genetic lineage (operator, 26 Aug):** "logical lineage ... if you look at the logic of genetic algorithms ... we can mutate and adopt certain features from specific bots, and then we combine them to make hybrids, tribids ... if we do over time realize that a certain confirmation mechanism can give us a higher win rate ... we test it across families" (`RES #0`). CHECKED. This is a **feature transplant across families**, a different axis from 07's domain expansion (same logic across cells). INFERRED.
- **Experiments like Git worktrees, and keep the failures:** "experiment is like a copy ... we can run multiple ... like git worktrees"; "we might need to keep even the failed experiments ... a ledger ... when it failed, how it failed" (`DB 4066`, replay of M975). CHECKED.

### 2.10 The experiment contract (designed for QMX, parked)

The 24 Aug experiment-design bot (`EXP`) is the most advanced testing text in the whole history. CHECKED throughout:

- **Three parts:** a preregistered spec (frozen after the first run), a run envelope (exact snapshots), an append-only result and decision ledger.
- **A result's identity:** `(graph_hash, book_policy_hash, book_initial_state_hash, data_hash, cost_model_hash, evaluator_hash)`. "Any change creates a new run lineage rather than overwriting history."
- **Judge by marginal value to the book, not alone:** `ΔBookUtility = Utility(book with candidate) − Utility(incumbent book)`. "Win rate remains descriptive, never the optimization target."
- **"A book-policy change makes prior certification stale, not false. Re-run it."**
- **Variant factorization:** location, context filters, trigger topology, confirmations, entry timing, candidate-owned exits, then numbers *within* each structural family. "Pair, session, and regime are normally challenge coordinates, not tunable strategy factors."
- **Node-level fire counts and a signal funnel** "so over-restrictive compound logic is visible".
- **Staged testing, not brute-force grids:** semantic gates (no look-ahead, timing, entry-price availability) → screening → ablation → interactions → sensitivity (costs, latency, parameters, walk-forward decay) → a locked final challenge.
- **Tries control:** preregister candidate count, stopping rule and minimum trades; purged/embargoed walk-forward; block bootstrap; Holm or max-T for planned contrasts; FDR for exploration; Reality-Check/SPA when many variants competed.
- **Three-pair challenge:** home pair, close analogue, adversarial pair, chosen before results are seen (also `DB 4065`, "Three Forex pairs and the pair knowledge base"). Operator approved the three-pair rule (`DOS` §6).
- Operator's reaction: "I don't understand most of what it says but I know it's good ... these are like new ideas for QMX" (`DB 4066`). CHECKED. It was parked as "deferred QMX ideas" (`GEN L1504`). CHECKED.

### 2.11 Catalog, scale and mini-KBs

- **Scale:** an aspiration of about 7,000 strategies (a crypto contact claimed ~7,000) (`RES #0`; `REC §14.3`). CHECKED.
- **Index "like skills":** "you can have a global index the same way like you have skills, you have a short description" (`DB 2725`). CHECKED. That is exactly `qml.find` in 07 §6.1. INFERRED.
- **Mini-KBs = durable research, not live state:** pairs, sessions, methodologies, macro, styles, prop firms, creator terms. "knowledge = slower durable understanding; intelligence = dated changing observations"; the operator put intelligence in QMX's UI and database (`DB 4066`; `GS L239-247`). CHECKED. Today's router journal for market-level facts (STATE.md:55) is that "intelligence" layer. INFERRED.
- **Pair similarity, not one correlation number:** shared currency, session, spread, volatility, range, news sensitivity, trend vs mean-reversion tendency, rolling correlation, broker execution (`DB 4065`, pair section). CHECKED. Directly useful for the router's "hypothetical markets" (seeds.md, registry). INFERRED.
- **SMC/ICT are collections; scalping is cross-cutting:** "a scalper can use a level from SMC, a trigger from ICT, and a confirmation from elsewhere" (`DB 4066`). CHECKED. So "methodology" and "style" are tags, never folders (`Stats\catalog\open-questions.md`). CHECKED.

---

## 3. What was rejected then, and whether it still holds

Sources: `REC §19` "Rejected or superseded"; `GS L455-515`; `STRATS-BUILD-STATE.md:86` and `:141`. All CHECKED. The verdict column is INFERRED.

| Rejected then | Why then | Still holds? |
| --- | --- | --- |
| Model probing → specialist fleet → staging → curator → promotion gates, as the way to build the library | The operator stopped it twice; "the regression was the ceremony" (`RES #157`; `REC §18.3`) | **Yes.** Correction 1 (keep it simple) and "one agent per job" say the same. |
| Promotion gates for *library entries* | Ceremony for a folder | **Yes for knowledge.** Different from **unit stages** (research → … → live), which the operator now wants, with only him promoting to live (STATE.md:36). Do not confuse the two. |
| "A pilot" for a folder; tests as the product | "this entire thing is not code ... it's just a folder" (`DB 4067`) | **Yes** for the dictionary and idea records. **No** for units: a unit is code and must pass `check`. |
| Executable test manifests, run results, ledgers, optimisers inside STRATS | They belong to QMX | **Placement changed, idea returns.** QML is now inside QMX. QMB's tries ledger and the unit journal are the new home for the experiment contract. The operator always wanted failed runs kept (§2.9). |
| Package lockfiles, digests, release machinery | Software ceremony in a knowledge folder | **Mostly yes.** No lockfiles. But each journal run should pin spec version, data window and cost source, which 07 §6.4 already does (`cost_source`, `sealed`). A light merge. |
| QMX adapter | Not needed; QMX adapts later | **Moot.** QML is QMX's own library now. |
| Sizing and exits outside the strategy (book owns them) | QMX docs of August: "bots trade; books control bots; BMS accounts" (`DB 4065`) | **No longer holds.** Correction 2: the unit owns exits and self-calibrating sizing. Keep only the *source-honesty* part: never claim the source said an exit it did not. |
| One aggregate confidence score | Hides different kinds of doubt | **Yes.** Matches DEC-0162. |
| One "magical best" variant | Different cells and books prefer different trade-offs | **Yes.** Matches sibling units. |
| Inventing thresholds, stops or exits | Source fidelity | **Yes for the idea record.** A unit may get exits added by its builder, labelled as agent-added (DNA F `external_policy`). |
| Compulsory `entry_hypothesis` for every incomplete source | Too strong; exits not mandatory | **Yes.** Keep the class as a label, not a gate on recording. It should be a gate on becoming a unit (§6). |
| Rigid four-column schema; fixed roles per primitive | Roles depend on the strategy | **Yes.** Matches Q8. |
| Scalping as a methodology; sniping as a methodology | They are cross-cutting / composite | **Yes.** |
| Live intelligence, agent memory, account state inside STRATS | Runtime state is QMX's | **Yes.** It now lives in journals, the router journal and the Library. |
| n8n as required intake | Not needed yet | **Yes.** QMA workflows cover it. |
| Futures as a target market | STRATS scope was forex + crypto spot only (`GS L18-23`) | **No.** Today: any instrument, including futures and perps (STATE.md; 01 table row 4). The transfer-caveat discipline matters *more* now. |

---

## 4. Old vs new, part by part

New = today's direction: QML as the unit library (`07-funnel.md` §6, lines 501-645) and the platform study (`04-platform-study.md` §0, §3). Verdicts are INFERRED.

| Part | Old (STRATS, Aug-Sep) | New (07 §6, 04) | Verdict |
| --- | --- | --- | --- |
| What the library is | Knowledge folder of *ideas*; not runnable; QMX tests later | Library agents use to *build runnable units*; verbs `new`, `check`, `test`, `promote`, `watch`, `find` | **Merge.** Two tiers: idea records (old) feed units (new). §6.1. |
| Three layers | Dictionary → binding → graph | Spec + two hooks (`entry`, `exit`, optional `manage`) in Python; `blocks` list | **Merge.** The graph is the agent-safe authoring form that compiles to the hooks; plain Python stays allowed (STATE.md:44). 04 §3.2 already proposes "see the code" graph and code views. |
| Roles | Lenses; role lives on the binding | CT-34 leg roles; Q8 "types never a cage" | **Keep the old.** It is already the rule. |
| Graph operators | ALL/ANY/NOT/K_OF_N/sequence/within/arming/reset/cooldown/re-entry; named ports | 04: configurable combiner block (mean, min, all-of, k-of-n, weighted); signal strength 0-1; signal expiry | **Merge.** Old operators plus new strength and expiry. Expiry = old `within`/`pending-order-expiry`. Add ports for composites. |
| Dictionary | 239 prose entries, 12 fields, relations, evidence status | "Runnable first"; librarian proposes; entries need code, a test and a look-ahead pass (07 D19) | **Merge.** Keep the 12 fields as the *documentation* of a block; add runnable code. An entry without code stays a definition, not a block. |
| Exits | 57 dictionary entries; canonical modules referenced, not copied; F labels | Exit blocks frozen at compile; safety exits inside the unit (07 F-10) | **Merge.** The old 57 entries are the exit block catalogue's spec list; "referenced, not copied" is the old rule worth keeping. |
| Sizing | Out of scope (book) | Unit sizes itself; MT5 Money-style sizer menu | **New is better.** Reuse the 5 old sizer entries as the starting menu. |
| Identity record | DNA A–I, class token, 14 sections | Unit spec v1 (`unit_id`, `version`, `family`, `parent`, `link`, `source`, `stage`…) | **Merge.** Add to the unit spec: `idea_id`, `origin` (source / agent / operator), `class` of the idea, and the F labels for exits. |
| Stages | Research status separate from source truth | Stage tag research → backtest → optimise → stress → paper → live | **New is better.** Old kept "clarity ≠ edge"; stages make it concrete. |
| Variants | Edit operations on a parent; ordered stack; digest | Version / sibling / "rewritten from" links | **Merge.** Use the edit-operation kinds to decide the link type automatically (§5.1). |
| Lineage | DAG; 5 edge types; source vs generated flagged; composites multi-parent | `parent` + `link` enum of 3 | **Keep the old (richer).** Add `composed-from` (many parents) and `corrected-from`. |
| Provenance | SRC items, 9 evidence layers, claim-to-rule map, 6 confidence dimensions | One string `source` | **Keep the old.** §5.2. |
| Catalog / search | Global one-line index; indexes by creator, channel, method, pair; "like skills" | `qml.find` over units, templates, blocks | **Merge.** `find` should search idea records and sources too. |
| Testing | Experiment contract: result identity, ΔBookUtility, staged tests, tries controls, fire counts, 3-pair challenge | QMB door; tries counted per family; deflated Sharpe, PBO; exam baseline; journal sections | **Merge.** The new side has the plumbing; the old side has three things the new lacks: node fire counts / signal funnel, marginal value to the pod (ΔBookUtility), and "policy change = stale, re-run". |
| Pair challenge | Home + close analogue + adversarial, chosen before results | Domain expansion with a numeric stop rule; sibling units | **Merge.** The three-pair choice is a good first expansion step and counts as tries. |
| Mini-KBs | Durable research per pair, session, method | Not in 07 | **Keep the old**, as Library notes the router and builders read. |
| Storage | Markdown + YAML files are truth; SQLite derived | JSON schemas; QMX Library kinds `unit`/`bot`/`pod` | **New is better** for units; keep markdown for idea records. Both must "fit the Library" (STATE.md:67). |
| Ambiguity | "A bot that has ambiguity shouldn't be tested" (`RES #0`); H section | `check` refusals name the fix | **Merge.** An idea with unresolved H items cannot become a unit until the builder resolves and labels them. |
| Market scope | Forex + crypto spot; transfer caveats | Any instrument; typed instrument spec | **New is better**, keep the old transfer notes per dictionary entry. |

---

## 5. Answers to Q2 and to lineage and provenance

### 5.1 Q2: when is something new?

The old design answers most of Q2 in plain rules. CHECKED unless marked.

1. **Environment change → same unit, new run.** "A QMX change causes a rerun of the same pinned candidate; it does not create a strategy variant unless strategy logic changed." (`PKG`, "QMX boundary"). "A book-policy change makes prior certification stale, not false." (`EXP` §2). So new costs, new data, a new QMB version or a new pod policy = a new journal run, not a new unit.
2. **Logic change → new node with a parent.** Any change to a trigger, filter, location, exit or parameter "should create a traceable child/variant" (`REC §14.1`).
3. **Numbers inside a structural family → tries, not new structure.** The experiment bot lists "numerical parameters within each structural family" as the last factor, separate from structural changes (`EXP` §3).
4. **Fixing a wrong extraction → corrected successor** (`corrected_from`), not a variant. The baseline is immutable; "corrections create a successor node" (`PKG`).
5. **Mixing parents → composite**, its own package, every parent named and pinned, importing named ports (`PKG`).
6. **A good parent does not retire.** "Some bots might be good, they don't need succession ... we just make a new variant." (`RES #0`, operator).
7. **Origin is always flagged:** source-defined vs agent-generated (`REC §14.1`).

**Mapping to T2 option A (07-funnel.md:360-368). INFERRED:**

| Edit operation (from `PKG`) | Q2 result |
| --- | --- |
| `replace_parameter` with a value inside the spec's range | Same unit; the value is a try |
| `replace_parameter` outside the range, `add/remove_constraint` | New version (the range is part of the logic) |
| `add/remove_binding`, `connect/disconnect`, `replace_subgraph`, `change_timing`, `change_entry`, `change_exit` | New version, `derived-from` parent |
| Same logic on a new instrument, timeframe or broker | Sibling unit, same family, shared try count (Q1) |
| Session or sniping window | Inside the unit (session profile); old design agrees: sessions are coordinates, sniping is a composite (§2.2) |
| Self-calibration of numbers | Journal event |
| Rewritten in new code | New unit, `rewritten-from` |
| Two or more parents combined | New unit, `composed-from` (missing in today's `link` enum) |
| Extraction error fixed | New version, `corrected-from` (missing in today's enum) |
| Cost, data, tester or pod-policy change | Same unit, new run; old verdicts marked stale |

Benefit: an agent never decides "is this new?" by judgment. The type of edit decides it, and `qml.check` can enforce it. INFERRED.

**One tension.** The old design calls pair, session and regime "challenge coordinates, not tunable strategy factors" (`EXP` §3). Q1 makes instrument a sibling unit. They agree if "sibling" means "same logic, own calibration and journal, never tuned per instrument by search without counting tries". INFERRED.

### 5.2 Lineage and provenance: every unit traceable to its source

The old chain, which already meets "no vibe trading" (STATE.md:48) for external sources. CHECKED pieces, INFERRED joins:

```text
SRC item (one home: kind, locator, creator, channel, rights, hash, acquired)
  → atomic claims (exact quote, timestamp/page/frame, evidence class)
    → claim-map (claim → binding / node / parameter)
      → idea record (DNA A–I, class, F exit labels, H unknowns, origin)
        → unit v1 (spec + hooks; idea_id; family)
          → versions, siblings, composites (typed lineage edges)
            → journal runs (pinned spec, data window, cost source)
```

**What the old design lacks for today's ask (INFERRED):**

- **Source kinds for chats.** The manifest kinds are `youtube-video | playlist | channel | book | paper | website | social | podcast | other` (`sources\items\_template\manifest.md`, CHECKED). Add `chat-session` (with session id and message id), `copilot-chat`, `operator-dictation` and `workflow-run`. A chat locator is a message id, the same way a video locator is a timestamp.
- **Agent ideas need a source too.** When an agent invents a variant, its "source" is the workflow run and its parent. The old flag "agent-generated" covers the label but not the locator.
- **The analyst lens** ("where high performers come from", STATE.md:49) falls out for free: the old indexes by creator, channel, methodology and modality, joined to journal results, show which creators and source kinds produce survivors. Needs `idea_id` on every unit.
- **The preview / detailed view** in the UI (STATE.md:50): the one-line catalog row is the preview; DNA A–I plus the journal is the detailed view.

---

## 6. What the operator may not be seeing

1. **An idea is not a unit.** STRATS stored ideas: often incomplete (entry only), often ambiguous, not runnable. A unit is a complete, runnable program. If QML holds only units, the 7,000-idea backlog and its evidence have no home, and provenance shrinks to the one-word `source` field in 07 §6.3. Keep an *idea record* tier in QML (DNA A–I, markdown is fine) and let units point to it. Only `complete` ideas, or ideas whose missing exits a builder fills and labels, become units. INFERRED.
2. **The best text is outside the repo, and holds secrets.** `PKG`, `EXP` and the full genesis and gold-mine messages live only in `AppData\Local\hermes\` (`state.db` 309 MB, delegation cache). One cleanup or reinstall loses them. "Research lives in the repo" applies, but `REC` warns that "credentials appeared in historical session material" (`DB 5678`, last line, CHECKED). Copy only redacted extracts. INFERRED.
3. **Stats has no backup.** It is not a git repo; the 15 Sep GitHub attempt never committed (§1.1). One Desktop copy. CHECKED.
4. **The 239 entries are vocabulary, not blocks.** 86 say "needs source evidence"; about 7 are runnable; they were written after a compaction by workers he later froze. Use them as names, definitions and test cases for blocks, not as ready parts. CHECKED counts, INFERRED advice.
5. **The old boundary was drawn for an older QMX.** STRATS excluded sizing, exits and testing because the August QMX gave them to the book and BMS (`DB 4065`). Correction 2 reversed that. Any agent that reads STRATS-GROUND-STATE §8 will refuse to put sizing in a unit. Mark that section superseded when Stats is absorbed. INFERRED.
6. **We are re-deriving August.** Tries control, staged tests instead of grids, the three-pair challenge, "stale not false", the signal funnel and marginal value to the book were all written on 24 Aug (`EXP`) and parked. 05, 07 and 08 rebuilt several of them from scratch. The parked ones not yet rebuilt are worth taking: **node fire counts / signal funnel** (shows over-tight logic and feeds the "signals detected but not taken" journal he asked for, STATE.md:54), **ΔBookUtility** (judge a unit by what it adds to the pod, not alone), and **operator-specific neutralization** (removing a node from a K-of-N must not change the rest's meaning). INFERRED.
7. **His genetic idea is a missing axis.** 07 expands *one logic across cells*. His 26 Aug idea transplants *one component across families* ("test it across families", `RES #0`). The edit operations in `PKG` make that mechanical (`replace_subgraph` from family X into family Y). Every transplant is a try in the receiving family. INFERRED.
8. **Judging is the product, and the queue is already big.** 359 NotebookLM sources (46 priority forex) were inventoried in August and never processed (`phase0-source-backlog-summary.md`: 136 blocked, 226 deferred). That is a ready first feed for the funnel once judging works. CHECKED counts.
9. **Names will keep biting.** STRATS, Stats, strats and QML name overlapping things. When Stats is absorbed into QML, record the old names as aliases in one place and archive `Desktop\strats`. INFERRED. (Deletion needs his go.)
10. **"Ambiguous ideas shouldn't be tested" vs "tests are nearly free".** His August rule protects against wasted tests; his October view says judging is the product. Both fit if ambiguity blocks *becoming a unit* (check refuses) but not *recording the idea*. INFERRED.

---

## 7. Sources read, and what was not read

**Read (CHECKED):** `STATE.md` and `seeds.md`; `Stats\README.md`, `STRATS-BUILD-STATE.md`, `STRATS-GROUND-STATE.md` (all), `IDEA.md`; `schema\` (all four files); `dictionary\README.md` and the exits file's headings and sample entries; `catalog\` (README, collisions, open questions); `lineage\`, `knowledge\`, `sources\`, `strategies\` READMEs and templates; all `STRAT-000001` files; backend file headers; `.hermes\orchestration\resume-20260826\gold-mine-session-analysis.md` (lines 1-700); population mandate; phase-0 inventory summaries; the genesis transcript (all user turns; assistant turns at `GEN L760-1041`, `L1060-1230`, `L1340-1428`; grep elsewhere); `PKG`, `EXP`, `DOS` in full; `DB 2701`, `2717`, `2725` (scanned), `4065`, `4066`, `4067`, `5678` (§7.4, 8, 14, 18-20); `RES #0`, `#88`, `#156-168`; `GMX #0`, `#299`; `S27 #0-7`; `Desktop\strats` contents and its git state; `.hermes` home config; `state.db` session list; `research\01` (§1.2, table), `04` (§0, §3.1-3.5), `07` (§3 F-8, F-9; T2; §6; §7).

**Not read:** the four dictionary family files in full (only headings and samples); `round-1`, `round-2` plans and the `reviews\` files (judged superseded by `GMA` §3); the 571 KB `transcripts\` copy (duplicate of the lineage copy); `title-triage.json` and `phase0-source-backlog.json` bodies; `vendor-inspection\claude-video`; `DB 2725` beyond keyword scans; the GLM 5.2 audit session itself; the Hermes skill `trading-strategy-knowledge-engineering` beyond `S27 #2`.
