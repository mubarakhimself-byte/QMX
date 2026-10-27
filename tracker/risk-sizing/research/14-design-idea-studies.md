# 14: Design-idea studies (router, independence, feed pool, journals, guard + pod, idea layer, QMB replay)

Written 2026-10-27. **Ideas and options only.** Nothing here is folded into architecture: no spine, no ADR, no final pick. Every option stays open for his conversation. Risk and sizing maths is out of scope (own session, `HANDOFF-RISK-SIZING.md`).

## How to read this

- **CHECKED** = I read it: `path:line` (code on `origin/engine/base` `d82be318`, the merged trunk, unless another path is given) or a URL read today.
- **INFERRED** = my reasoning. Every option is INFERRED unless a fact inside it is tagged.
- **Method.** Skills loaded and used: `codebase-design` (module, interface, depth, seam, adapter, leverage, locality, deletion test, "one adapter = hypothetical seam, two = real"), `domain-modeling` (challenge terms, sharpen fuzzy words, test against code, glossary in §11), `principle-boundary-discipline` (guards at the edges, pure logic inside), `principle-foundational-thinking` (data shapes first), `principle-subtract-before-you-add` (each study starts with what to remove), `principle-separate-before-serializing-shared-state` (one writer per fact; share by reading, never by co-writing).
- **One skill could not run.** `improve-codebase-architecture` refuses model invocation ("reserved for explicit user invocation"). He can run `/improve-codebase-architecture` himself later; this file does not imitate it.
- **Format of each study:** the question → what to subtract first → 2-3 options, each as a deep module (interface, what hides behind it, seams, where it runs, failure modes, what it touches in shipped code, Library fit) → a comparison → what stays open.
- "Design for complexity, never a complex system": every option below is allowed to be boring. Where an option is clever, the comparison says what the cleverness costs.

---

## 0. The short version

1. **The router becomes an advice publisher.** Its whole interface can be one call: `offers(now) -> [RouteOffer]`, each offer with an expiry. Units pull offers; nothing waits on the router. Three shapes: a central advice board (A), 09's planner kept but its gate turned into a lookup that never blocks (B), or client-side balancing where each unit chooses from a shared depth feed (C). INFERRED.
2. **Load-balancer algorithms map cleanly once the direction is flipped:** an *opportunity* (instrument × session window) is the request, units are the backends, and the router only offers. Power-of-two choices by correlation, least cost, and consistent hashing (affinity, and instrument → node sharding) are the three that earn their place. INFERRED (§2.3).
3. **Unit independence is a dependency table, not a feature.** A unit trades on: its spec and code, its admitted envelope, a local feed, local guards and a local journal sink. Router, PC link and Library are optional. The cleanest trick: MIS labelers are QML producers, so the same code can run *inside the unit* or be read from the keeper's cache. Two adapters, one interface (`labels.at`), so the "router is down" case vanishes. INFERRED (§3).
4. **"5 trading days" is the wrong clock for scalpers.** Split cadences by lens: seconds for live facts, session windows for offers, the unit's own trade count for its calibration, days or events for slow MIS labels. INFERRED (§3.5).
5. **Feed pool:** one feed keeper per broker connection; three bus shapes (in-process, local PUB/SUB, per-machine feed service). The keeper also records our own history through the market-data door, which ships no live collector today (CHECKED `qmn/src/qmn/venue/spot_recorded.py:1-5`). INFERRED (§4).
6. **Journals:** one writer per stream. Unit journal, market journal, router decision log and guard log are four separate append-only streams joined by keys, never copies. Three shapes: plain Parquet event streams (A), OpenTelemetry traces (B; the node already ships otelcol, Loki and Prometheus, CHECKED `qmn/deploy/observability/`), or Library-native items with partition blobs (C). INFERRED (§5).
7. **Account guard + pod:** the three shapes of Q1 drawn as modules with blast radius. All three share one small interface: `allow_new_risk(...) -> Allow | Refuse(reason)` plus `on_account(snapshot) -> [Stop | Flatten | Alert]`. It never resizes. INFERRED (§6).
8. **Idea layer:** the Library already has a `hypothesis` kind with `statement` and `source{object_id, locator}` (CHECKED `qmx_library/kinds/hypothesis.schema.json`), and a closed list of 25 relations (CHECKED `qmx_library/port.py:92-120`). Lineage needs four more edge types or an "edit kind" field. Three options (§7).
9. **QMB replay fix is bigger than 12 said.** The price history is copied **three times** per step: the `cumulative` list (CHECKED `qmb/src/qmb/host/replay.py:569`), `_freeze_evidence` (`replay.py:60-67`), and `deep_freeze` inside `MappingReadSurface` (CHECKED `qml/src/qml/protocol/evidence.py:875-885`, `qml/src/qml/footprint/_coerce.py:52-60`). The replay-equality check also compares whole frames (`qmb/src/qmb/host/replay_execution.py:824-828`). Any fix must touch all four. Three options (§8).
10. **Two shipped facts conflict with rulings 136-137:** the market-data door makes the **server** the primary (CHECKED `qmx_host/market_data.py:105-111, 192-194`) and defaults a 12-month holdout lock (`market_data.py:76-77`, and the class docstring "a door without the holdout lock is not a door"). Both are for the doc and code pass, not for him.
11. **Name collision:** the shipped `qmx-router` package is the **LLM provider router** (CHECKED `qmx-agents/packages/qmx-router/src/qmx_router/__init__.py:1-5`). The trading router needs another code name (§11, a vocabulary question).
12. **Research gaps:** a second live cTrader connection is "should not", not a published hard cap; error 67 exists, and the real hazard is the token refresh, which logs the other side out (§9.1). The old QMB battery was not refused by anyone else: the operator himself deferred it on 20 Aug under "keep it simple" (CHECKED, §9.2). LEAN and Jesse now both ship agent doors; the borrow list is in §9.3.

---

## 1. Ground truth: what shipped code already gives these studies

Every study below "touches" something here. All rows CHECKED on `origin/engine/base`.

| Area | What exists | Where |
|---|---|---|
| Library store | One store of objects, blobs, refs and edges. `put` on a ref the caller owns; `relate` with a closed vocabulary; `archive`, never delete (AD-6); `annotate` without a new version | `qmx-agents/packages/qmx-library/src/qmx_library/store.py:927-1024` |
| Library relations | 25 relations: `produced-by, consumed, derived-from, uses, part-of, cites, tested-by, tests, instance-of, run-of, ran-on (retired), variant-of, version-of, merged-from, annotates, replaces, archived-as, resolves, made-by, used-by, compiles-to, touched, mentions, explains, related-to`. An edge is `(from, type, to)` with no attributes | `qmx_library/port.py:92-120`; `store.py:956-983` |
| Library primary | `Epoch` on `refs/primary`: which store is primary, flips counted, stale primaries stop acting | `store.py:470-486` |
| Kind `unit` | class `governed`; empty `fields`; tabs Logic, Results, **Family tree** (`walk:variant-of:both`), **Markets** (`fields.markets`), Versions | `qmx_library/kinds/unit.schema.json` |
| Kind `pod` / `bms` / `pod-block` | `pod` is class `definition` with `fields.slots`; `bms` class `governed`, empty fields | `kinds/pod.schema.json`, `kinds/bms.schema.json` |
| Kind `hypothesis` | class `record`; `statement`, `source{object_id, locator}`, `subject`; tabs Evidence, Source, Family, History | `kinds/hypothesis.schema.json` |
| Kind `source` | `origin` enum `upload, agent, feed, capture, import`; `text_hash`, `replaces`, `licence`; blobs for original, text, transcript, frames | `kinds/source.schema.json` |
| Kind `trade` | `world` enum `backtest, paper, demo, live, synthetic`; `run_id`, `r`, `initial_risk`, `fees`, `swap`, exact integers | `kinds/trade.schema.json` |
| Kind `model` | blobs `weights`, `card`; tabs Metrics, Used by, Versions | `kinds/model.schema.json` |
| Run journal | Append-only, one writer per run volume, per-line fingerprint and `seq`, lock file | `qmx-agents/packages/qmx-ledger/src/qmx_ledger/journal.py:1-60` |
| Market-data door | One reader/writer of a machine's price store; `Placement = pc | node | server`; **server is primary**; 12-month holdout default; reads past 5,000 rows return a handle | `qmx-agents/packages/qmx-host/src/qmx_host/market_data.py:1-12, 70-77, 105-111, 170-193` |
| cTrader sign-in | "The PC is never the home: a second home refreshing the same grant logs the first out." Token kept in the home's vault | `qmx_host/venue_session.py:1-14` |
| Held streams | A node that stops answering keeps its rows with "server unreachable since …" and last values; retry every 5 s | `qmx_host/streams.py:1-25` |
| Node MIS | Producers: `identity, spread_state, gap_event, feed_state, degraded_sensors, spread_quality_sensor (SQS), liquidity_stress_v1, regime_classifier_v1`. The signal snapshot goes to **the Book door and the KSA only** | `qmn/src/qmn/mis/catalog.py:81-111`; `qmn/src/qmn/mis/__init__.py:1-6` |
| Node guards | Kill line per binding, operator-only resume; news calendar failure "fails entries closed while exits, protection, and recording continue"; seats quarantine on breach, operator-only reinstate | `qmn/src/qmn/capital/kill_line.py:1-10`; `qmn/src/qmn/data/news_calendar.py:1-10`; `qmn/src/qmn/seats/__init__.py:1-8` |
| Node journal rule | Journal before dispatch for every money-path effect | `qmn/src/qmn/journal_dispatch.py:1-11` |
| Node recording | Recorded spot ticks enter the archive, but "no live collector … is created" | `qmn/src/qmn/venue/spot_recorded.py:1-5` |
| Node observability | otelcol, Loki, Promtail, Prometheus, Grafana dashboards | `qmn/deploy/observability/` |
| QMB replay | Quadratic copy per step (three copies, §8) | `qmb/src/qmb/host/replay.py:60, 475-572`; `qml/src/qml/protocol/evidence.py:875-885` |
| LLM router | `qmx-router` = loopback relay for model keys, GPT translator, provider profiles | `qmx_router/__init__.py:1-5` |

**One reading of this table (INFERRED):** the Library and node already contain most *mechanisms* these studies need (append-only journals, archive-never-delete, held streams with last values, fail-entries-closed guards, operator-only resume). What is missing is mostly *shape*: who owns which fact, and which way the arrows point.

---

## 2. Study 1: the router as a load balancer that directs and never switches

### 2.1 The question

He ruled: routing means directing traffic like a load balancer; it never switches a unit on or off; units stay independent; the router needs its own correlation ledger; several nodes or instruments raise "one router or many"; MIS models need per-instrument training (STATE.md:61-69).

### 2.2 Subtract first

- **Remove the gate.** 09's gate decides "seat OPEN / CLOSED for new entries" (09 §2.4). Under his ruling that is a switch. Its cheap checks (spread, news, feed age, session) move to two places that already exist: the unit's own conditions and the guards (CHECKED: news fails entries closed at the node, `news_calendar.py:1-10`).
- **Remove "seats" as router authority.** A seat in 09 is something the router grants. Keep the word only if it means "a market the unit is admitted to" (the envelope, §2.6), never "a slot the router opens".
- **Remove the router from the data path.** It reads the feed like a unit (12 §4.2). Units never ask it for prices.
- **What survives:** a ranking of opportunities, offers with an expiry, a decision log, the correlation ledger.

### 2.3 Load-balancer algorithms mapped to units and markets

The direction flips. In a web load balancer, a request picks a server. Here an **opportunity** (an instrument in a session window, at a broker) is the "request", **units** are the "backends", and the router *offers* the opportunity; the unit decides. A unit's **home market** is never part of the traffic the router hands out (13 round 3). INFERRED.

| LB algorithm | Its rule in a web LB | QMX mapping | Earns its place? |
|---|---|---|---|
| Round robin | Next server in turn | Rotate offers across eligible units so each gathers evidence | Weak; useful only for *paper* evidence gathering |
| Weighted round robin | More turns for stronger servers | More offers to units with stronger proof (grade) | Yes, as a weight inside a hybrid |
| Least connections | Server with fewest open connections | Offer goes to the **unit with the fewest open trades**, or the **market with the fewest correlated units already engaged** | Yes (the second reading fights herding) |
| Least response time | Fastest server | **Least cost**: the broker × hour with the lowest spread-to-target ratio right now (from the market journal) | Yes (his gold example) |
| Consistent hashing | Same key → same server; minimal reshuffle when a server leaves | **Affinity**: a unit keeps its known markets; and **instrument → node sharding** when there are several nodes | Yes, twice |
| Power of two choices | Pick 2 at random, send to the less loaded | Pick 2 eligible units, offer to the **less correlated** with what is already engaged | Yes; cheap, stops herding |
| Resource-based | Server reports capacity | **Liquidity capacity** of the market (depth, tick rate vs baseline) | Later, when depth is recorded |
| Random | Uniform | Exploration share for paper siblings only | Paper only |

**Hybrids** are a pipeline of filters then one scorer, like Kubernetes filter-then-score (09 §1.1, CHECKED there): `eligible(envelope, conditions)` → `affinity first` → `power-of-two by correlation` → `weight by grade` → `tie-break by least cost`. Every stage is a named, versioned policy, UI-editable. INFERRED.

### 2.4 Shared data shapes (all three options use them)

```
RouteOffer                                  # one piece of advice; immutable
  offer_id, unit_id@version
  market: (broker, account_type, instrument, session_window)
  inside_envelope: yes | no                 # no  -> it is a paper-sibling proposal, never live
  why: [label@version, ...], evidence: [result ids]
  grade: proven | hypothesis
  policy: name@version                      # which algorithm produced it
  issued_at, fresh_until, expires_at        # after expires_at it means nothing
  plan_version

OfferOutcome                                # written by the UNIT, in the unit journal
  offer_id, taken | ignored | expired, reason

CorrelationSnapshot                         # one writer (whoever computes it)
  as_of, window
  unit_pnl_corr[unit, unit], signal_corr[unit, unit]
  instrument_corr[instr, instr]
  consensus[instrument] = (long_count, short_count, split)   # MASS-style, own units, no LLM
```

Single-writer rule (principle-separate-before-serializing): the router writes offers, the unit writes outcomes, one job writes correlation snapshots. Nobody co-writes a row. INFERRED.

### 2.5 Options

#### Option A: the advice board (one central publisher, units pull)

```
          feed pool ──► ROUTER (any machine that reads the Library + pool)
 Library: envelopes,         │ offers(now) = pure function of
 grades, journals ──────────►│  (envelopes, grades, labels, correlation, policy)
                             ▼
                      offer board  ──► units pull "offers for me"
                      (bus topic + Parquet log)      │
                                                      └─► unit journal: taken / ignored
```

- **Interface (small):** `offers(now) -> list[RouteOffer]` and `offers_for(unit_id) -> list[RouteOffer]` (a filtered read of the same board). Policy is configuration, not interface.
- **Hides:** the algorithm pipeline, correlation reads, the envelope check, expiry, deduplication of repeat offers.
- **Seams:** policy (real seam: at least two algorithms ship, so two adapters); the board transport (in-process list on the PC; bus topic on the node; real seam once there are two machines).
- **Runs:** PC alone first (router, pool and paper units all on the PC). With a node: the router can stay on the PC; the node receives the board as a small file or topic, like 09's plan push. Servers: any machine with the Library.
- **Failure modes:** router down → board stops refreshing → offers expire → units trade their envelope on their own conditions (Q3 decides what "envelope" means when the router is off). A wrong policy floods offers → offers inside the envelope are still only advice; outside it they are only paper proposals. Stale correlation → offers herd; the pod's same-bet limit (§6) still holds.
- **Touches:** nothing on the money path. New: a `route-offer` stream; `RouteOffer` schema. Retires 09's gate idea. Keeps the node small.
- **Library fit:** policy and plan versions are Library objects (class `definition`). Offers are high-volume: Parquet partitions behind a Library card, the pattern 12 §5.3 proposes for router logs (`kind=router-plan`). Correlation snapshots: one Library record per day plus a Parquet series.
- **Depth:** high. Units learn one call; everything else is hidden. **Deletion test:** delete the router and units lose only extra traffic; nothing else breaks. That is exactly the property he asked for.

#### Option B: 09's planner kept, the gate turned into a lookup

```
 SLOW (PC / any machine)                       FAST (node)
 planner ──► placement plan (Library object) ──push──► plan cache (file)
   reads registry, labels, correlation                 │
                                                       ▼
                         unit asks: "is market M advised for me now?"
                         lookup(plan, unit, market, now) -> advised | not-advised | unknown
                         (never blocks: "not-advised" is information)
```

- **Interface:** `advice(unit_id, market, now) -> Advised(offer) | NotAdvised(reason) | Unknown`. Plus the planner's own `plan(inputs) -> Plan`.
- **Hides:** the plan format, signatures, `seq` gap detection, fresh/stale clocks (09 §2.5).
- **Seams:** plan transport (file push, Library pull); planner policy.
- **Runs:** planner on the PC first; the lookup sits beside units wherever they run, on the PC or the node.
- **Failure modes:** plan past `hard_until` → lookup returns `Unknown` → unit falls back to its declared router-off mode. 09's "after hard_until no new entries anywhere" (09 §2.6) is **removed**; that was a switch.
- **Touches:** reuses most of 09's design (plan, `seq`, signatures, make-before-break). Smallest change from what he already read.
- **Library fit:** `router-plan` as a Library object per node slice; decision log as Parquet.
- **Depth:** medium. The lookup is shallow (it is a dictionary read), but the planner is deep. Risk: "not-advised" drifts back into a switch if someone wires it to block. A hook or test should forbid any caller from turning `NotAdvised` into a refusal.

#### Option C: client-side balancing (no central chooser)

```
 keeper ──► depth feed: labels per instrument (spread state, vol state, session, liquidity)
 correlation job ──► correlation snapshot (shared, read-only)
                         │
            each unit runs choose(my_envelope, depth_feed, correlation) locally
            (like gRPC client-side load balancing / power-of-two in the client)
```

- **Interface:** inside the unit, one call: `choose(envelope, depth, corr, policy) -> ranked markets`. Centrally: only `depth_feed` and `correlation_snapshot`, both plain read-only data.
- **Hides:** nothing central to fail. The "router" becomes a QML library function every unit can import.
- **Seams:** policy (same as A); the depth feed transport.
- **Runs:** wherever units run. PC alone needs nothing extra.
- **Failure modes:** no central view at decision time, so two units may pick the same market in the same second. Herding protection moves entirely to the pod's same-bet limit (§6). Hard to measure "router value" because there is no single decider.
- **Touches:** QML gains a `choose` block; the MIS becomes a feed, not a decider (this is D66's lean).
- **Library fit:** policies as QML blocks; correlation snapshot as a Library record series.
- **Depth:** very high per unit, but the decision log scatters across 200 unit journals; an analyst must join them.

### 2.6 The admission envelope (I180) as a data shape

```
Admission                         # written only by the operator principal
  admission_id, unit_id@version
  markets:  [(broker, account_type, instrument)]
  sessions: [session windows]
  router_mode: ignore | advise | follow-offers        # default advise (13, I58)
  router_off: home-only | whole-envelope | last-offers   # Q3
  signed_by: operator, at
```

- **Where it lives (two Library options, INFERRED):** (i) in the unit's own `fields.markets` (the `unit` kind already has a Markets tab reading `fields.markets`, CHECKED `kinds/unit.schema.json`), so a changed envelope is a new unit version; or (ii) a separate `admission` record with an edge to the unit, so his click does not version the unit. (ii) keeps "only he promotes" structural: the ref it lives on is owned by the operator principal, and the store refuses anyone else (CHECKED owner check in `store.put`, `store.py:931-933`).
- Inside the envelope an offer is live advice. Outside it, an offer is a paper-sibling proposal card he may accept.

### 2.7 The router decision log

- **One row per offer issued** (the router writes), **one row per outcome** (the unit writes). Joined by `offer_id`. INFERRED.
- Enough inputs on each row to replay: `policy@version`, `plan_version`, label versions, correlation `as_of`. Router policies are pure functions over logged inputs, so QMB can replay them (13 I110).
- **Router value** (I50): compare "units that took offers" with "units that ignored them" on the same markets. This is the only honest way to know whether the router earns its keep.

### 2.8 The correlation ledger: three owners

| Owner | How | Trade-off |
|---|---|---|
| Router | Router computes and keeps it | Matches his words (D57). Pod must read the router's object to enforce same-bet limits, so the pod depends on the router: against independence |
| Pod / BMS | The old BMS held it (13 round 3, CHECKED there) | The router reads the pod's object: router depends on the pod, which is fine (pod is local and always on) |
| Shared object, own writer | A small job writes `correlation-snapshot`; router reads it for direction, pod reads it for limits (I63) | One computation, two readers, no dependency between router and pod. Most aligned with "separate before serializing" |

INFERRED. The third keeps the deletion test clean: delete the router and the pod still has its ledger.

### 2.9 One router or many (several nodes, several instruments)

| Shape | Picture | When it fits |
|---|---|---|
| One planner, per-node slices | One router computes offers for all units; each node gets its slice (xDS-style, 09 §3.1) | A handful of nodes; one correlation view across all of them |
| One router per node + shared correlation | Each node runs its own router (A or B) over its own units; all read one correlation snapshot | Nodes far apart or on different brokers; avoids a central bottleneck |
| Hierarchical | Per-node routers for fast offers; one central planner for slow offers (new markets, siblings) | Many nodes; mirrors CDN edge + origin (13 I66) |

**Instrument sharding across nodes:** consistent hashing on `(broker, instrument)` assigns each instrument's units to one node, so adding a node moves only a slice of instruments. INFERRED. Local-first holds for all three: on the PC alone, "one router, one slice" is the degenerate case.

### 2.10 Per-instrument model training (where and when)

- **What exists:** `regime_classifier_v1` has a corpus, design, train, eval and register path, offline, operator-run; models register as versioned artifacts with lineage edges (CHECKED `qmn/src/qmn/mis/__init__.py:6-24`).
- **Shapes (INFERRED):**
  1. *Pooled plus per-instrument fit* (13 I69): one class-level model (FX majors, metals, indices) shares strength; each instrument gets a small fine-tune. Cheap; works with thin data.
  2. *One model per instrument*: simplest to reason about; needs years of data per instrument; many models to keep fresh.
  3. *No trained model at first*: rule labelers only (spread state, vol ratio, session), which already exist on the node. Train only when a labeler's journaled value shows it misses something.
- **Where:** the PC trains (local first); a burst server may train in its place; the node never trains. **When:** on a frozen data month, on a decay alarm from the market almanac, or by his click. Never on a timer that nobody reads.
- **Library fit:** `model` kind exists (weights + card blobs, Versions tab, CHECKED). Training data edge: `model --consumed--> dataset@fingerprint`; labeler outputs stamped `labeler@version` (13 I77).
- **"MTFA":** STATE.md:116 notes it meant "MT5 articles" (speech-to-text). 06 parked the article-mining run; any per-instrument training ideas from the articles are still unmined. Not a question for him.

### 2.11 Comparison

| | A advice board | B planner + lookup | C client-side |
|---|---|---|---|
| Depth (leverage per unit of interface) | High | Medium | High per unit, low for analysts |
| Router down | Offers expire; units trade envelope | Lookup says `Unknown`; units trade envelope | Nothing changes |
| Central view (herding, value) | Yes | Yes | No |
| Change from what he read (09) | Medium | Small | Large |
| Risk of drifting back to a switch | Low | **Medium** (needs a guard against `NotAdvised` → block) | None |
| Fits "MIS changes if units read it" (D66) | Partly | Partly | Fully |

**Open for him:** Q2 (what the click admits), Q3 (router-off behaviour), Q4 (units reading MIS). Plus a vocabulary question: the trading router's name (§11).

---

## 3. Study 2: unit independence

### 3.1 The question

What does a unit need to keep trading when the router, the PC link or a guard feed is slow or down? How do guards stay independent? What do the Q4 options do to cadence?

### 3.2 Subtract first

- Remove every call from a unit to the router (offers are pulled, not awaited).
- Remove every call from a unit to the PC (the PC is a client of the node for observing, not a server for trading; 09 §3.2).
- Remove "MIS = Book door and KSA only" as the single route for labels (CHECKED `qmn/src/qmn/mis/__init__.py:3-5`); labels become a feed anyone may read (Q4 decides whether units may).

### 3.3 The dependency table (what a unit needs, and what happens without it)

| Needs | Hard or soft | Source when present | When missing |
|---|---|---|---|
| Its spec and code @version | Hard | Local copy on the machine | Unit cannot start (a deploy problem, not a runtime one) |
| Its admission envelope | Hard | Local copy, signed | Cannot start; never fetched live |
| Feed for its symbols | Hard per symbol | Keeper on this machine (§4) | Symbol `stale` → no new entries on that symbol; open trades keep broker-side stops (12 §4.3, CHECKED pattern) |
| Warm-up history | Hard at start | Recorder partitions + last-value cache | Unit waits in warm-up (trading-locked), as QMB already does (13; ADR-0017 R5) |
| Guards' verdicts | Hard | Local guard process reading the same pool | If the guard itself is down: no new entries for its account (fail closed, as news already does) |
| Journal sink | Hard (journal before dispatch) | Local append log | Sink refusal blocks the effect, entries only (CHECKED `journal_dispatch.py:3-7`) |
| Router offers | Soft | Board / plan / own `choose` | Offers expire → router-off mode (Q3) |
| MIS labels | Soft or none (Q4) | Keeper cache or own compute | Declared fallback (§3.4) |
| PC link | None for trading | Held stream (CHECKED `streams.py:1-12`) | Rows show "unreachable since …"; nothing else |
| Library | None for trading | Local cache | Writes queue in an outbox (the Library already has `outbox.py`, CHECKED file list) |

INFERRED except where tagged. The rule that falls out: **every hard need is local to the machine the unit runs on.** That is "static stability" (09 §1.6, CHECKED there) applied per unit.

### 3.4 Options for units reading live data and MIS output (Q4 a/b/c)

#### Option (a): never. Units read raw feed only; labels serve the router and guards

- **Interface for the unit:** `feed.last(symbol)`, `feed.bars(symbol, tf, n)`. Nothing else.
- **Effect:** independence is total by construction; the 20 Oct seed stands. "Depth of information" reaches the unit only as offers (Study 1).
- **Cost:** a unit that wants "is spread wide vs usual?" must compute it itself, duplicating the SQS baseline per unit. That breaks "no duplication" (D30) in compute, not in storage.

#### Option (b): optional context with a declared fallback, tested both ways

- **Interface:** the unit declares `context_needs: [spread_state@v1, vol_state@v1, ...]` and, per need, `when_missing: ignore | compute-locally | no-new-entries`. At run time: `context.at(name, instrument, t) -> value | Missing`.
- **QMB:** runs the unit twice, with and without context, and reports both (13 I59).
- **Cost:** two runs per check; the declaration is one more field agents must fill (a hook can fill a default).

#### Option (c'): "compute where you are" (a variant of c that keeps independence)

```
                labels.at(name, instrument, t)          # one interface
                  │                       │
      adapter 1: read keeper cache   adapter 2: compute from own feed with the same QML producer
      (cheap, shared)                (no dependency; same code, same version)
```

- **Why it is deep:** MIS labelers are QML producers already (the node's MIS producers have fixed ids and versions, CHECKED `catalog.py:81-111`). If the same producer code runs in the keeper *or* inside the unit, the unit never depends on anyone: when the cache is missing, it computes. Two adapters behind one interface = a real seam (codebase-design).
- **Cost:** CPU per unit when the cache is down; slow labels (trained models) are heavy to compute in-unit, so this works for rule labelers, not for `regime_classifier_v1`.
- **Effect on the MIS:** the MIS splits into *fast rule labelers* (library code, runnable anywhere) and *slow trained labels* (a feed with expiry, router-grade only). This is the "MIS changes" he predicted (D66). INFERRED.

#### Option (c): freely, like any feed, no declaration

- Simple to write; a router or keeper outage silently changes behaviour. Against his ruling unless paired with (c')'s local adapter.

### 3.5 Cadence: what each option does to "5 trading days"

09 put `hard_until = 5 trading days` on the plan (09 §2.5). His point: fine for the MIS lens, shaky for a scalper (D67). Split by lens (INFERRED):

| Lens | Clock | Example default (all editable) | Who uses it |
|---|---|---|---|
| Live facts (spread, feed age, flash move) | Seconds | stale after 5× usual gap (12 §6) | Guards; units under (b)/(c') |
| Offers | Session windows | An offer lives for the window it names (London open, NY overlap) | Router → units |
| Unit calibration | The unit's own trades | Recalibrate after N closed trades or a calibration receipt event, never a calendar | The unit (risk session owns the maths) |
| Slow labels and plans | Days or events | Daily plus on a label flip, DST, holiday, new proof | Router planner |
| Model retraining | Data months | On a frozen month or a decay alarm | PC training job |

Under (a) the unit has no MIS clock at all. Under (b) and (c') the unit sees live-fact labels on the seconds clock, and slow labels only as context with expiry. In no option does a scalper wait on a 5-day plan. INFERRED.

### 3.6 Guards that stay independent

```
            feed pool (local)            news calendar cache (local)      broker account stream
                 │                                 │                            │
          ┌──────┴────────┐                ┌───────┴───────┐            ┌───────┴───────┐
          │ SQS guard     │                │ news guard    │            │ account guard │
          │ spread vs     │                │ window open?  │            │ kill line,    │
          │ baseline/hour │                │ calendar old? │            │ daily loss    │
          └──────┬────────┘                └───────┬───────┘            └───────┬───────┘
                 └────────────── verdict(scope, now) ──────────────────────────┘
                     allow | block-new(reason) | flatten(reason) | alert
                                     │
                       guard journal (one writer per guard)
```

- **Common interface (small):** `verdict(scope, now) -> Allow | BlockNew(reason) | Flatten(reason)`, scope = `(account)` or `(account, instrument)`. Units consult it before an entry; the node's protection dispatcher already ranks controls (CHECKED `qmn/src/qmn/protection/__init__.py:1-12`).
- **Inputs are local only**: pool, calendar cache, broker account stream. No router, no PC.
- **Shipped behaviour to keep:** news failure fails entries closed, exits continue (CHECKED `news_calendar.py:5-9`); kill line flattens one binding, operator-only resume (CHECKED `kill_line.py:3-9`). These already match "the only automatic transition is the risk rules stopping a unit" (STATE.md:36).
- **Drill:** 13 I100 (unplug router, MIS, PC during a node self-test; the guard still stops). INFERRED.

### 3.7 Comparison

| | (a) never | (b) declared fallback | (c') compute where you are |
|---|---|---|---|
| Independence | Total | Total if fallbacks are honest | Total for rule labels |
| Duplication | Compute duplicated per unit | None | Compute only when the cache is down |
| QMB cost | One run | Two runs | One run (same code both ways) |
| Agents must declare | Nothing | `context_needs` + fallbacks | `context_needs` only |
| MIS change | None | Small | MIS splits into library labelers + slow feed |

**Open for him:** Q4 (he leaned toward units reading both). (c') is offered as a way to say yes without breaking independence.

---

## 4. Study 3: the market-feed pool for 200+ units

### 4.1 Subtract first

- One subscription per `(venue, symbol, kind)`, never per unit (12 §4.2).
- No broker history calls for warm-up: warm-up comes from our recorder; the venue's history budget is kept for gap repair (12 §4.2).
- The router reads the pool like any reader; it owns nothing in it.

### 4.2 Shared interface (all options)

```
feed.subscribe(venue, symbol, kind) -> Stream      # kind: quote | bar:1m | depth | trades | asset_ctx
feed.last(venue, symbol, kind) -> Value | Stale     # last-value cache
feed.health(venue, symbol) -> live | stale(since) | closed(session) | down(reason)
```

**Hidden behind it:** sockets, app and account auth, token refresh, heartbeats, reconnect with backoff, resubscribe, gap backfill marked `backfilled`, deduplication, sequence numbers, the last-value cache, unsubscribe grace, recording, the market-journal rollup, venue limits. That is a lot of behaviour for three calls: a deep module. INFERRED.

### 4.3 Options for the bus

#### Option A: in-process keeper, asyncio fan-out

- Keeper and unit workers in one process (or a few), queues per reader, seq numbers, last-value cache. 12's recommendation for day one (12 §4.2).
- **Runs:** PC alone, unchanged on the node.
- **Fails:** one crash takes its units down; run units in a few worker processes to limit the blast.
- **Seam:** none needed yet (one adapter = hypothetical seam). Do not build the bus interface until a second adapter exists.

#### Option B: keeper process + local PUB/SUB (ZeroMQ or one NATS binary)

- Units, guards, router and recorder are separate processes on one machine.
- **Fails:** ZeroMQ drops for slow readers (catch with seq); NATS adds a binary to run. Not re-verified on Windows (12 §7).
- **Seam:** real once A and B both exist (in-process adapter for tests, socket adapter for production).

#### Option C: a feed service per machine, readable across machines

- Each machine's keeper also serves its pool over the private network. The PC can read the node's live pool without its own live connection.
- **Fails:** a network hop for remote readers; only for observers and research, never for a unit's own trading.
- **Fits** the existing held-stream pattern (CHECKED `qmx_host/streams.py`: one held stream per node, last values kept when unreachable).

### 4.4 Platforms

| Platform | Rule that shapes the keeper | Keeper shape (INFERRED) |
|---|---|---|
| cTrader Open API | Docs: "At most, you **should** create two connections: one for demo accounts and one for live accounts" (CHECKED https://help.ctrader.com/open-api/connection/). No symbol cap (12 §4.1). 50 req/s, 5 req/s history, per connection (CHECKED https://help.ctrader.com/open-api/). Token refresh fires `ProtoOAAccountsTokenInvalidatedEvent` ("token was refreshed") (CHECKED https://help.ctrader.com/open-api/messages/) | One keeper per (app, environment). The live connection has one holder at a time (§4.5). Research on the PC can use the demo connection |
| MT5 | One terminal per account; Python package polls; Windows only (12 §4.1) | Keeper polls `symbol_info_tick` or an EA pushes over a socket; MT5 keepers live on a Windows machine |
| Hyperliquid | Per IP: 10 connections, 1,000 subscriptions (12 §4.1) | Each machine subscribes on its own; no lease |
| CCXT / Binance | 1,024 streams per connection; every connection cut at 24 h (12 §4.1) | Keeper rotates connections before the 24 h cut (make before break) |
| Futures (Rithmic, CQG, IB, Databento) | Paid per exchange subscription | One keeper per subscription; price it per feed, never per unit |

### 4.5 The cTrader one-connection rule: PC and node taking turns

| Option | How | Fails how |
|---|---|---|
| Lease | One lease record per (app, environment) like the Library's `refs/primary` Epoch (CHECKED `store.py:470-486`). Holder renews; the other side reads its pool (option C) | Lease handover needs his click or a timeout he sets |
| Two apps | Register one cTrader app per machine | Each app needs its own grant; a refresh on one must not log out the other. venue_session says the *same* grant refreshed twice logs the first out (CHECKED `venue_session.py:12-13`); two apps have two grants, so INFERRED safe, untested |
| Split by environment | Node holds live; PC holds demo for research and paper | Paper on the PC then sees demo prices, not live ones; costs differ |

The open fact behind this table is §9.1.

### 4.6 Recording our own history

```
keeper ──► recorder ──► staging files ──► market-data door commit(files) ──► monthly partitions
                                            (CHECKED market_data.py:3-6: "nothing else writes the store")
       └─► market-journal roller ──► costs-1m partitions (same door, kind=costs-1m)
```

- Today the node records spot ticks into the archive but creates no live collector (CHECKED `spot_recorded.py:1-5`). The recorder fills that gap and is the Dukascopy escape route (12 §2.1).
- Storage tier: bars on the PC; ticks on the storage machine and bucket, the PC caching what a run needs (12 §5.2). INFERRED fit.

### 4.7 Comparison

| | A in-process | B local PUB/SUB | C per-machine service |
|---|---|---|---|
| PC-alone simplicity | Best | Good | Good |
| Crash isolation | Weak | Good | Good |
| Cross-machine reads | No | No | Yes |
| New moving parts | None | A library or a binary | A network door |

**Open:** technical, not his call. Settle with one demo test (§9.1).

---

## 5. Study 4: journals as the DevOps layer

### 5.1 Subtract first

- No spread, fee, swap or session columns in unit journals; one market journal holds them (D31; 12 §5.1).
- No every-bar logging by default (events by default; every bar on request; tick debug time-boxed, 13 I38).
- No second results store: the trade rows QMB produces and node trades both use the Library `trade` shape (CHECKED `kinds/trade.schema.json`, `world` enum covers backtest to live).

### 5.2 Four streams, one writer each

| Stream | Writer | Holds | Key |
|---|---|---|---|
| Unit journal | QMB for backtest/stress; node for paper/live; agents only in a notes section | Signals taken, **seen-not-taken** (typed reason), **missed** (computed by replay afterwards), orders, fills, own slippage, sizing inputs, condition checks, calibration receipts, offer outcomes, agent notes and proposals | `unit_id@version`, `trace_id` per trade |
| Market journal | Feed keeper's roller on the machine holding the connection | Spread stats, ticks, gaps, swap, commission, funding, session state; slippage folded in nightly from all fills (aggregates only) | `(broker, account_type, instrument, bucket)` |
| Router decision log | The router | Offers issued with inputs and versions | `offer_id` |
| Guard journal | Each guard | Every block, stop and flatten, level and reason | `(account, instrument?, at)` |

One writer per stream (principle-separate-before-serializing). The UI joins at read time. INFERRED.

### 5.3 One id from source to trade

```
source (Library `source`, text_hash) ──cites──► idea record ──derived-from──► unit@v1 ──version-of──► unit@v2
                                                                                  │
   origin_id (minted once at the source or the operator's dictation) ─────────────┤ copied onto every row
                                                                                  ▼
   trade: trace_id ── signal span ─ checks span ─ order span ─ fill span ─ manage spans ─ exit span
          market_key = (broker, account_type, instrument, bucket) ──► market journal row (join, no copy)
          offer_id? ──► router decision log row
```

"Where do winners come from" becomes a group-by on `origin_id` with tries in the denominator (13 I8). INFERRED.

### 5.4 Options

#### Option A: plain append-only event streams in Parquet

- **Interface:** `journal.append(event)` for the single writer; `journal.read(unit, from, to, kinds)` returning a handle past 5,000 rows (the door already uses handles, CHECKED `market_data.py:70-71`).
- **Hides:** partitioning by month, fingerprinting, compaction of open months, the read-time joins.
- **Runs:** PC first; node writes its own and syncs partitions back.
- **Touches:** builds on `RunJournal` (append-only, per-line fingerprint, CHECKED `qmx_ledger/journal.py`) for the hot log; Parquet for the archive.
- **Library fit:** one Library card per unit journal pointing at partitions (12 §5.3).

#### Option B: OpenTelemetry traces and metrics, Parquet as the archive

- Each trade is a trace; guard and router decisions are spans or events; unit SLOs (trade rate, slippage band, R band) are metrics with burn-rate alerts that become OK / Watch / Alarm (13 I36).
- **Touches:** the node already ships otelcol, Loki, Promtail, Prometheus and Grafana dashboards (CHECKED `qmn/deploy/observability/`). Reuse, do not add.
- **Cost:** OTel is an ops tool; the Library and QMB cannot read it directly, so an exporter writes Parquet anyway. Two stores for one fact unless the exporter is the only writer of Parquet.

#### Option C: Library-native journals

- Each unit journal is a Library item (a new `journal` kind or `trade` + `note` objects) with monthly partition blobs; agents write `note` objects with an `annotates` edge to the trade or unit (relation exists, CHECKED `port.py`).
- **Cost:** many small objects; the Library's catalog grows with trades unless partitions are blobs, not objects.
- **Gain:** lineage, search (`fts.py` exists) and the UI's card/page renderers come free.

### 5.5 Storage tiers (INFERRED from 12 §5.2)

| Data | Hot (PC) | Warm (storage machine) | Cold (bucket) |
|---|---|---|---|
| 1m bars, active instruments | yes | yes | yes |
| Ticks | months a run needs | full | full |
| Unit journals, events | current + last months | full | full |
| Market journal 1m | last year | full | full |
| Router log, guard log | last months | full | full |

### 5.6 Preview and detailed view of the family tree

- **Index line** (one sentence, like a skill description), **preview card**, **detailed view**: one JSON object rendered for agents and UI (13 I23). The Library already renders cards from `card.facts` and pages from `page.tabs` per kind (CHECKED unit schema: facts `version, state, used_in`; tabs incl. Family tree, Markets).
- **Preview fields (proposal):** stage, origin, family, home markets, tries, grade, last-30-trades R sparkline, guard state, open proposals.
- **Detailed tabs (proposal):** journal sections, lineage graph, market map, runs, calibration receipts, proposals, notes, offers taken/ignored.
- **Family-tree preview:** per family, a small graph: nodes coloured by stage, edges by type (§7), sized by trades. Detailed: click into any node.

### 5.7 Comparison

| | A Parquet streams | B OTel + archive | C Library-native |
|---|---|---|---|
| Simplicity on the PC | Best | Needs the OTel stack | Good |
| Reuse of shipped parts | RunJournal, door | Node observability stack | Library cards, search, edges |
| Agents read | Through handles | Via exporter | Natively |
| Volume risk | Low | Low | Catalog growth |

**Open:** technical. A plausible blend (INFERRED): A as the store of record, B's stack for live dashboards fed from the same writer, C only for low-volume objects (notes, proposals, calibration receipts).

---

## 6. Study 5: account guard + pod / BMS (shape only, no sizing maths)

### 6.1 Ground

- Old record: the BMS "accounts and constrains; never trades or sizes; one BMS per account" (13 round 5, CHECKED there from `grounding/02`).
- Shipped Library: `pod` (class `definition`, `fields.slots`), `bms` (class `governed`), `pod-block` kinds exist (CHECKED). Node: kill line per binding, KSA severity fold with operator-only resume (CHECKED `protection/__init__.py:3-5`).
- Name collision: in the Lab, "pod" means a risk/sizing system you build and test (13 round 5). Keep it in mind for §11.

### 6.2 Shared interface (all three shapes)

```
allow_new_risk(unit, intent, context) -> Allow | Refuse(reason)     # before every entry; never resizes
on_account(snapshot) -> [Stop(unit|account) | Flatten(scope) | Alert]   # on every account update
state() -> GREEN .. BLACK                                            # escalates alone; de-escalates by his click
```

Everything else (budget, same-bet limits, kill line, daily loss, news windows, correlation reads) hides behind it. INFERRED.

### 6.3 The three shapes as modules

#### (a) One object: pod = BMS = guard + shared budget + same-bet limits, one per account

```
account ── POD/BMS ── units
           [guard rules][budget][same-bet limits][ledger read]
```

- **Blast radius:** one bug in one object reaches every unit on the account. One copilot edit can touch the floor.
- **Simplest to explain;** matches his lean (D18, D20).
- **Touches:** merges `bms` and `pod` kinds; the node's kill line and KSA become parts of it.

#### (b) Two layers: fixed guard per account + pod templates above it

```
account ── GUARD (fixed, local, unremovable) ── POD template(s) ── units
           kill line, daily loss, news,          budget, same-bet limits,
           SQS, ladder                           copilot may remake
```

- **Blast radius:** a bad pod cannot lower the floor; the guard is small enough to test exhaustively.
- **Costs:** two modules; two places to look.
- **Touches:** guard = today's node kill line + KSA + news window; pod = Library `pod` kind with `slots`.

#### (c) One shape, locked block

```
POD template = [GUARD block: locked] + [budget block] + [same-bet block] + [...]
```

- **Blast radius:** like (b) if "locked" is enforced structurally (a hook refuses any template whose guard block hash differs from the signed one); like (a) if it is only a convention.
- **Gain:** one shape for the copilot to learn; `pod-block` already exists as a kind (CHECKED).

### 6.4 Comparison (blast radius first)

| | (a) one object | (b) two layers | (c) locked block |
|---|---|---|---|
| A bad copilot edit can lower the floor | Yes | No | No, if the lock is a hash check |
| Modules to learn | 1 | 2 | 1 |
| Fits "copilot can remake pods" (D40) | Risky | Yes | Yes |
| Fits "pod is the BMS" (D18) | Exactly | Partly | Mostly |
| Matches shipped node | Needs a merge | Closest | Needs a template format |

**Open for him:** Q1. Separately (D16): design and instance are two lenses on the same code: pod *design* in the Lab, tested in QMB (13 I98); pod *instance* on the node with live state.

---

## 7. Study 6: the idea layer, lineage and provenance; plain Python, mini apps and ML stay first-class

### 7.1 Subtract first

- No DNA A–I ceremony on every idea: three required fields (class, source with locator, claims), the rest lazy (13 round 1).
- No new kinds where an existing kind fits: `hypothesis`, `source`, `note`, `model`, `mini-app`, `workflow-run` all exist (CHECKED kinds list).

### 7.2 Edge vocabulary: what exists and what is missing

| Needed link | Existing relation | Gap |
|---|---|---|
| version of a unit | `version-of` | none |
| variant | `variant-of` (drives the Family tree tab) | none |
| derived from an idea | `derived-from` | none |
| composite of parents | `merged-from` (closest) | meaning differs: merge of edits vs composite of strategies |
| corrected extraction | `replaces` (closest) | loses "the old one was wrong" |
| sibling (same logic, new market) | none | **missing** |
| transplanted part | none | **missing** |
| rewritten in new code | none | **missing** |
| source of an idea | `cites` | none |
| run of a unit | `run-of` | none |

The vocabulary is closed (AD-4) and edges carry no attributes (CHECKED `store.py:956-983`). INFERRED.

### 7.3 Options

#### Option A: extend `hypothesis` as the idea record; add four relations

- `hypothesis.fields` gains `class` (complete | entry_hypothesis | fragment | descriptive_pattern | composite, from Stats DNA A, 10 §2.4), `claims[]` with locators, `origin` (source | agent | operator).
- Relations added to AD-4: `sibling-of`, `transplanted-from`, `rewritten-from`, `composed-from`.
- **Touches:** one schema, one frozen set in `port.py`. Small.
- **Gain:** the Family tab already walks `variant-of` (CHECKED hypothesis schema).

#### Option B: a new `idea` kind; keep relations closed, put the edit kind on the child

- The child unit's fields carry `edit: {kind: transplant | sibling | rewrite | composite | correction | version, ops: [...]}` (the Stats edit operations, 10 §2.6). One generic edge `derived-from` to each parent.
- **Gain:** no change to AD-4; the edit kind decides "new or same" mechanically (10 §5.1).
- **Cost:** the graph view must read child fields to colour edges.

#### Option C: no idea kind; lineage by edges and annotations only

- A source `cites` a unit directly, with the locator in the unit's fields; ideas that never became units live as `note` objects.
- **Gain:** smallest. **Cost:** the 7,000-idea backlog (10 §2.11) has no home of its own; "where winners come from" needs ideas as first-class rows.

### 7.4 Genetic transplants across families

```
family X unit ── port: confirmation ──┐
                                      │ transplant op: replace_subgraph(port=confirmation, from=X@v3)
family Y unit@v5 ─────────────────────┴──► family Y unit@v6   edge: transplanted-from X@v3
                                                              counted as a try in family Y
```

- Needs named ports (`setup, entry, invalidation, exit, regime`, CHECKED 10 §2.3 from Stats `PKG`). QML's CT-34 roles `level | trigger | confirmation | filter` are the nearest shipped vocabulary (10 §2.1).
- Plain-Python donors: an agent rewrites the part into ports; the original stays (13 I149).
- Record the overrule: 07 killed "genetic crossover"; his 26 Aug idea revives it (13 I151).

### 7.5 Plain Python, mini apps, ML ensemblers beside QML

- **Shipped:** QMB keeps "the plain-Python bridge first-class" (CHECKED `docs/decisions/ADR-0017-qmb-experimentation-library.md`, Consequences); the ungoverned lane (`qmb.run()`) returns values and writes no ledger (DEC-0270, same ADR, follow-up). The node refuses ungoverned Python bots in a seat (CHECKED `qmn/src/qmn/seats/__init__.py:6-8`).
- **Unit kinds (proposal, 13 I138):** QML graph · QML hooks · plain Python · ML model · ensembler. Same journal, same judge, same tries.
- **Two modes, one check (13 I141):** refuse in agent mode, warn in human mode. A plain-Python unit gets an `outside_standard` flag and "look-ahead not verified" on its report; it is never blocked.
- **Open tension (for the node session, not him now):** the node's seat refusal of ungoverned bots vs "plain Python is always possible". A plain-Python unit can paper and run in QMB freely; live seats are where the standard bites. INFERRED.

### 7.6 Comparison

| | A extend hypothesis + 4 relations | B idea kind + edit field | C edges only |
|---|---|---|---|
| Change to Library | Small schema + AD-4 | New kind | None |
| "New or same" decided mechanically | By edge type | By edit kind (best) | No |
| Backlog of ideas has a home | Yes | Yes | No |

**Open:** technical, except Q2 (held by him).

---

## 8. Study 7: the QMB replay fix and lookback

### 8.1 What really copies (CHECKED; extends 12 §1)

```
for each quote step k:
  cumulative.append(quote_k)                                   # replay.py:557
  payload = _freeze_evidence({"samples": list(cumulative)})    # replay.py:566-571  copy #1 (list) + copy #2 (tuple per item)
  frames[k] = payload                                          # replay.py:572
MappingReadSurface(frames)                                     # evidence.py:875-885
  __post_init__: deep_freeze(payload) for every frame          # _coerce.py:52-60   copy #3
replay equality: supplied.frames == authoritative.frames       # replay_execution.py:824-828  O(total) compare
both entries call _materialise_quotes                          # replay.py:442 (recorded), :729 (typed)
```

So memory and time grow with the square of the steps, three times over. Lifting the 1,000-step bound needs all four sites changed. INFERRED from the CHECKED lines.

### 8.2 Options

#### Option A: shared series + end offset (a view, not a copy)

- One immutable series per stream; each frame is `SeriesView(series_id, end)`; `samples` reads `series[:end]` lazily.
- **Touches:** `replay.py:557-572` (build views), `_freeze_evidence` (must not walk a view), `deep_freeze` (must treat a view as already frozen), equality (compare `(series fingerprint, end)` pairs). `MappingReadSurface` is a QML contract type, so QML's evidence tests move too.
- **Gain:** same answers, linear memory, no unit changes. **Risk:** any producer that expects a real tuple must accept a sequence view.

#### Option B: declared window (ring buffer)

- Keep only the last W samples per stream, W from QML's footprint (`warm_up`, `warm_up_time_bound`, CHECKED `qml/src/qml/footprint/template.py:140, 159-160, 188-189`).
- **Gain:** constant memory per step; matches what live will hold.
- **Cost:** a unit with no declared bound needs a fallback (A). Two adapters behind one read interface = a real seam.

#### Option C: lazy frames (a cursor, not a dict)

- `MappingReadSurface` becomes `at(instant)` over a cursor that materialises a frame only when asked, from the shared series.
- **Gain:** nothing precomputed; long runs stream.
- **Cost:** the biggest contract change (frames is a public `Mapping` field today, CHECKED `evidence.py:878`); the equality check must replay rather than compare.

### 8.3 Lookback, after any fix

- No `lookback_max`; `lookback_default_start = 2020-03-01` per run kind; a request older than the data gets a plain answer (12 §1, §6).
- **Ruling 137 conflict (CHECKED rulings file line 266; `market_data.py:76-77`):** the door defaults a 12-month holdout and its docstring calls a door without the lock "not a door". Ruling 137 says a holdout is an optional study setting, off by default. For the doc and code pass.
- **Ruling 136 conflict (CHECKED rulings file line 265; `market_data.py:105-111, 192-194`):** `Placement.SERVER` is the primary. Ruling 136: the PC is primary, servers stand in. For the doc and code pass.

### 8.4 Comparison

| | A shared view | B declared window | C lazy cursor |
|---|---|---|---|
| Unit changes | None | Units declare a window (QML already computes it) | None |
| Contract change | Medium | Medium | Large |
| Memory | Linear | Constant per step | Linear, streamed |
| Matches live behaviour | Partly | Best | Partly |

**Open:** technical. A plausible sequence (INFERRED): A first (unblocks "1990" with no unit changes), B as an adapter later.

---

## 9. Research gaps closed (or narrowed)

### 9.1 Does a second live cTrader Open API connection actually fail?

- **Docs:** "At most, you **should** create two connections: one for demo accounts and one for live accounts." A recommendation, not a stated cap. CHECKED (https://help.ctrader.com/open-api/connection/, "Best practices").
- **A cap exists somewhere:** error 67 `CONNECTIONS_LIMIT_EXCEEDED`, "Your app has too many open connections." CHECKED (https://openbrokerapi.com/errors/ctrader/connections-limit-exceeded; also listed in the error table at https://openbrokerapi.com/platforms/ctrader/messages/protooaerrorres). No page read today gives the number.
- **Forum:** a 2022 user wrote "Application 1 ↔ N Connections (max 25 according to limitations in docs)"; Spotware's reply did not confirm or deny the number. CHECKED (https://community.ctrader.com/forum/connect-api-support/37539/). The current docs do not show 25. So the number is unverified.
- **The real hazard is the token, not the socket.** `ProtoOAAccountsTokenInvalidatedEvent` fires when a token "was refreshed" (CHECKED https://help.ctrader.com/open-api/messages/). QMX's own sign-in code says "a second home refreshing the same grant logs the first out" (CHECKED `qmx_host/venue_session.py:12-13`).
- **Verdict (INFERRED):** a second live connection under one app probably connects (error 67 implies a cap above two), but two machines that each refresh the same grant will knock each other's accounts off. Design for one token holder per grant. The one-minute demo test in 12 §7 still settles the socket question; it costs nothing.

### 9.2 Why the old QMX QMB features were dropped

- **Nobody else refused them; the operator deferred them himself.** QMB architecture memlog, operator ruling round 2026-08-20: walk-forward confirmed; "old engine's heavy battery (PBO/CSCV etc.) stays deferred — 'keep it simple' reaffirmed." CHECKED (`C:\Users\Mubarak\Desktop\QMX\_bmad-output\planning-artifacts\architecture\architecture-QMB-2026-08-20\.memlog.md:14`). The spine repeats it: pass batteries "remain candidates for the GAP-0048/0049 sittings ('keep it simple' — operator)." CHECKED (`…\ARCHITECTURE-SPINE.md:248`).
- **Pass numbers were dropped by design:** QMB may never "store a frozen pass/fail bar verdict"; verdicts are a read-time fold per requirement, and a blank bar answers `not-yet-ruled` (DEC-0162). CHECKED (`C:\Users\Mubarak\Desktop\QMX\docs\components\qmb.md:25, 79`). The thresholds were then never set (GAP-0049, CHECKED `docs/gap-report.md:20`).
- **Per-bot paper and warm-up:** moved outside the node by DEC-0261 ("backtesting, iteration and paper trading happen BEFORE promotion and OUTSIDE the node"). CHECKED (`docs/decisions/ADR-0019-trading-node.md:87`).
- **Parity replay of the live node:** a node replay "is an ungoverned diagnostic report — never … evidence that gates anything" (DEC-0206). CHECKED (`docs/components/qmb.md:209`).
- **Donor code:** "nothing is adopted as code — the two donors were reverse-engineered … never use the code" (DEC-0013). CHECKED (`docs/decisions/ADR-0017-qmb-experimentation-library.md`, Context).
- **Lost quietly in the reconcile:** parameter-sensitivity / isolated-spike flag (OPT-22), hard optimisation constraints, minimum-trades gate, locked validation window, DataFrame ergonomics, machine-observable data progress. These "did not land" without being deferred. CHECKED (`…\reviews\review-reconcile-intake.md:88-101, 161, 182`).
- **Reading (INFERRED):** the battery was deferred for simplicity, not judged wrong. His 27 Oct "don't be too strict" fits warn-only defaults (13 I103) and still respects DEC-0162 (warnings are read-time, never stored verdicts).

### 9.3 What a professional QMB borrows from LEAN CLI and Jesse, versus the old system

Read today: LEAN CLI docs (https://www.quantconnect.com/docs/v2/lean-cli, `/api-reference/lean-backtest`, `/lean-optimize`, `/lean-research`, `/reports`); Jesse docs (https://docs.jesse.trade/, `/docs/mcp/`, `/docs/routes.html`, `/docs/research/optimize`, `/docs/monte-carlo/`). The 20 Aug intake map is in `review-reconcile-intake.md` (CHECKED).

| Borrow | From | Why for agents | Old QMX had it? | QMB today |
|---|---|---|---|---|
| One CLI verb per job: `init, backtest, optimize, research, report, data` | LEAN (CHECKED command pages) | An agent learns a few verbs, not code | No CLI | Command tree "landed weakened" (CHECKED reconcile :212) |
| Report with **live results overlaid on the backtest** (`lean report --live-results`) | LEAN (CHECKED Reports page) | The live-vs-exam compare QMB lacks (13 I125) | WF3 compared journals by hand | Missing |
| Results in a per-run output folder, never overwriting | LEAN (`--output`, CHECKED) | Result identity | Wanted it | Fingerprinted ledger line (QMB has it) |
| An **MCP door with agent rules**: backtests, optimise, significance tests, Monte Carlo, candle import, results and charts in chat | Jesse (CHECKED `/docs/mcp/`) | The exact "agents use QMB, never hand-roll" door he asked for | No | MCP door after CLI v1 (ADR-0017) |
| **Rule significance test** (signal vs random entries) | Jesse (CHECKED `/docs/mcp/`) | Cheap first filter for agent-generated signals | No | Shipped as library function (CHECKED `docs/components/qmb.md:121`) |
| Monte Carlo on **trades and on candles** | Jesse (CHECKED `/docs/monte-carlo/`) | Robustness, never edge | 1,000 shuffles | Shipped, labelled robustness-only |
| Optimise with a **held-out test period** and a target trade count; Optuna | Jesse (CHECKED `/docs/research/optimize`) | Agents cannot peek at the test window | Walk-forward | Optuna pinned; locked validation window "did not land" |
| Routes and data routes (multi-symbol, multi-timeframe without look-ahead) | Jesse (CHECKED `/docs/routes.html`) | One spec runs many cells | No | Stream sets (B-12) |
| **Research runners**: spare machines take backtests, results land on the main dashboard | Jesse (CHECKED `/docs/mcp/`) | The same shape as ruling 136: servers extend the PC | No | B-15 passive hub only |
| Fixed pass numbers in R, PBO, min trades per window, slices by session/regime, MAE/MFE, stress stage, per-bot paper | Old QMX (08 §1.1, CHECKED there) | Judging is the product | Yes | Deferred (§9.2); return as warn-only |
| Tries ledger, honest synthetic labels, raw measures judged later, sealed holdout, costs from real fills | New QMX (08 §1.5) | Prevents fooling ourselves | No | Shipped |

**What not to borrow (CHECKED reasons in ADR-0017, Options):** LEAN's engine (C# in Docker); Jesse's float money, global state, zero slippage and flat fees. Neither has a retail-FX fill model, which is the thing QMX needs most (GAP-0048).

---

## 10. How the studies fit together (one picture)

```
                         ┌──────────── PC (home; can run everything alone) ─────────────┐
 sources ─► idea records ─► units (QML / Python / ML)  ─► QMB (replay fix §8) ─► journals │
                │                    │                                     ▲             │
                │      admission (his click only) ──► envelope             │             │
                │                    │                                     │             │
                │   router (§2): offers with expiry ◄── correlation snapshot (one writer) │
                └────────────────────┼───────────────────────────────────────────────────┘
                                     │ plan / offers / envelopes (files, pulled)
            ┌──────────── node (trades when the laptop is closed) ────────────────────┐
 broker ──► feed keeper (§4) ──► local bus ──► units ──► orders (journal before dispatch)  │
              │   │                  │  ▲                                              │
              │   └─► recorder ─► door│  └── guards (§3.6, §6): SQS, news, account     │
              └─► market journal      └── offers (optional) / labels.at (§3.4)          │
            └──────────────────────────────────────────────────────────────────────────┘
 storage machine: archives (ticks, journals) — extends, never replaces
```

Every arrow into a unit on the node is local or optional. Every write has one owner. INFERRED.

---

## 11. Domain glossary (the ubiquitous language)

Terms only, no implementation. "Avoid" lists words that collide or blur. Built with `domain-modeling`; contradictions with code are flagged.

| Term | Meaning | Avoid |
|---|---|---|
| **Unit** | One complete trading algorithm: entry, exits, its own self-calibrating risk and sizing, condition needs, session profile, exam baseline, journal. Tested and run as one | bot (fine in talk), strategy (that is an idea), seat |
| **Unit kind** | How a unit is written: QML graph, QML hooks, plain Python, ML model, ensembler | type (scalper types are tags) |
| **Version** | The same unit after a logic change, linked to its parent | |
| **Sibling** | Same logic on another instrument, timeframe or broker: its own calibration and journal, same family, shared tries | variant (blurs with version) |
| **Family** | All units descended from one idea, through versions, siblings and transplants | correlation family (that is a bet group) |
| **Idea (idea record)** | A recorded trading idea with a source and claims; may be incomplete; not runnable | strategy, hypothesis (the Library kind name; see §7) |
| **Source** | Where an idea came from: video, post, paper, MQL5 article, chat, copilot chat, his dictation, a workflow run, an agent | |
| **Origin id** | The one id minted at the source and carried to every trade | |
| **Transplant** | Moving one part (by named port) from a unit in one family into a unit of another; a try in the receiver | crossover (07's killed term) |
| **Named port** | A part of a unit that can be swapped as a whole: setup, entry, invalidation, exit, regime | |
| **Market** | A tradable instrument at a broker and account type | pair (FX only), symbol (a venue id) |
| **Opportunity** | A market in a session window: the "traffic" the router offers | |
| **Home market** | A unit's own admitted market; never the router's to give or take | |
| **Admission** | His click that lets a unit trade live; nothing else admits | promotion (an old word with automatic meanings) |
| **Envelope** | The markets, sessions and brokers his admission covers | seat |
| **Router** | The part that directs opportunities to units by a balancing policy and never switches anything. Code name must differ from the shipped `qmx-router` (the LLM provider router) | gate, switch, MIS (the MIS is its inputs) |
| **Route offer** | One piece of advice: unit, opportunity, why, grade, policy, expiry | signal, instruction |
| **Balancing policy** | The algorithm that ranks offers: weighted round robin, least cost, power of two, affinity, hybrids | |
| **Router decision log** | The router's own record of offers issued, with inputs | router journal (that word was used for market facts) |
| **Correlation ledger** | Rolling correlations of units' P&L and signals, of instruments, and units' long/short consensus per instrument; one writer | |
| **MIS label** | A fact about a market computed by a labeler at a version (spread state, vol state, session, liquidity) | regime (one label among many) |
| **Depth feed** | The stream of MIS labels per instrument | |
| **Journal (unit journal)** | Everything a unit did or saw: taken, seen-not-taken, missed, orders, fills, calibration receipts, offer outcomes, agent notes | log (too narrow), ledger (QMB's run record) |
| **Seen-not-taken** | A signal the unit detected and skipped, with a typed reason | |
| **Missed** | A trade the unit would have taken but could not (offline, stale feed), found by replay afterwards | |
| **Market journal** | Market facts per broker, account type, instrument and time bucket: spread, fees, swap, funding, sessions, slippage aggregates | router journal |
| **Guard journal** | Every block, stop and flatten by a guard, with reason | |
| **Calibration receipt** | A journal entry saying which number a unit changed, from which data, by which rule, inside which range | |
| **Feed keeper** | The one owner of a broker connection on a machine; subscribes once per symbol and fans out | feed handler, adapter |
| **Feed pool** | All keepers on a machine and their bus | |
| **Last-value cache** | The latest price per symbol, read at once by a starting unit | |
| **Recorder** | Writes the pool into our own price history through the market-data door | |
| **Guard** | A local, always-on check that can block new entries or flatten: SQS, news guard, account guard | kill switch (one guard action), MIS |
| **SQS** | The spread quality sensor: live spread against its usual level for that hour | |
| **Account guard** | The guard for one account: kill line, daily loss, ladder | |
| **Kill line** | The loss floor that flattens and stands a unit down; only he resumes | |
| **Pod** | Shared rules above the units of an account: budget and same-bet limits; may include the guard (Q1) | Book (retired for this design); note the Lab also says "pod" for a risk/sizing system: needs one meaning |
| **BMS** | The old name for the account-level constrainer; his lean: pod = BMS | |
| **Same bet** | Units whose journals move together count as one bet | |
| **Grade** | Where a unit stands in judging: uncalibrated → screened → backtested → stressed → sealed → paper → live | score (banned as a stored composite, DEC-0162) |
| **Stop (automatic)** | A guard taking a unit out; logged; only he puts it back | retire |
| **Retire** | His click ending a unit; everything kept | delete |
| **Paper sibling** | A sibling that trades on paper because it is outside an admitted envelope | |
| **Primary** | The machine whose store is the main copy. Ruling 136: the PC. Shipped code says the server (conflict, §8.3) | |
| **Placement** | Where a part runs: PC, node, server | |

---

## 12. Operator questions each study raises, mapped to the 7 in STATE

STATE's list (STATE.md:131-139): Q1 guard + pod, Q2 what the click admits, Q3 router off, Q4 units reading MIS, Q5 paper sequence, Q6 his unfinished thought, Q7 paying for data.

| Study | Questions it raises | Maps to | New? |
|---|---|---|---|
| 1 Router | What his click admits (one market vs envelope vs anything his conditions allow) | Q2 | no |
| 1 Router | With the router off: home only / whole envelope / last offers | Q3 | no |
| 1 Router | Default balancing policy (power of two vs least cost vs weighted) | none: technical, a UI-editable default | no |
| 1 Router | The trading router's name, since `qmx-router` is taken by the LLM router | vocabulary | **N1 (new, vocabulary he cares about)** |
| 1 Router | Correlation ledger owner | none: technical (§2.8) | no |
| 2 Independence | Units reading MIS: never / declared fallback / freely; (c') "compute where you are" as a way to say yes | Q4 | no (option added) |
| 2 Independence | Cadence by lens instead of "5 trading days" | none: technical | no |
| 3 Feed pool | Lease vs two apps vs split by environment for cTrader | none: technical, settle by a demo test | no |
| 3 Feed pool | Paid feeds per platform | Q7 | no |
| 4 Journals | Which lens his unfinished thought means (almanac / cell map / cost-aware placement) | Q6 | no |
| 4 Journals | Store shape (Parquet / OTel / Library) | none: technical | no |
| 5 Guard + pod | One object / two layers / locked block | Q1 | no |
| 5 Guard + pod | One meaning for "pod" (Lab's risk system vs account-level rules) | Q1 (vocabulary part) | folded into Q1 |
| 6 Idea layer | When something is "new" | Q2 of the first round, **held by him** (STATE.md:35) | no |
| 6 Idea layer | Paper siblings: may an agent start a paper sibling without his click (paper is not live)? | Q5 | folded into Q5 |
| 7 QMB replay | None for him; ruling 136/137 conflicts go to the doc and code pass | none | no |

**Net new questions: one (N1, the router's name).** Everything else maps to Q1-Q7 or is technical and settled in one line when the time comes (correction 11: bring him only real ambiguity).

---

## 13. Not verified

- The number behind cTrader error 67 (§9.1).
- Two cTrader apps on one cTID refreshing independently (§4.5); inferred safe, untested.
- ZeroMQ and NATS behaviour on Windows (carried from 12 §7).
- Whether producers inside QML accept a sequence view instead of a tuple (§8.2 A); needs a code read of each producer.
- Storage sizes (carried from 12 §5.2; measure on the first real month).
