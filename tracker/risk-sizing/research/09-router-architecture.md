# 09: Router architecture (how to make the MIS router fast)

Written 2026-10-24. Research only. Nothing here is ratified, and no code was changed.

## How to read this

- **CHECKED**: I read it at the cited URL or path on 2026-10-24.
- **INFERRED**: my reading or proposal.
- Every number in the QMX design below is an example setting. All of them are UI-editable, with no fixed values (operator standing rule).
- "Router" means the MIS as the operator seeded it: it places proven units on markets, sessions and windows. It never changes how a unit trades. CHECKED (`C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\seeds.md`, "MIS is a router").

Inputs read: `seeds.md`; `01-ground-truth.md` §0, §1.4, §1.5, §2; `05-academic.md` §1; `07a-funnel-party.md` Round 3 and ideas 6, 8, 28, 32, 34-36, 123, 170; `07b-funnel-cis.md` S2a-S2e.

---

## 0. The answer in ten lines

1. **The matching itself is tiny.** QMX has tens of units and tens of markets. Kubernetes scores up to 5,000 nodes for every pod, and Instagram ranks 500 posts on every scroll. Compute is not QMX's speed problem. CHECKED (sources in §1); the QMX scale is INFERRED.
2. **The real speed problems are two:** slow information (a regime change seen from 1-minute closes takes about 44 minutes to detect) and a remote dependency (the PC may be off). CHECKED (`05-academic.md` §1.3).
3. **Every fast system cited here solves this the same way.** It does the slow, smart work ahead of time. It then ships the result to where the decision happens, and it decides live with cheap lookups only.
4. **For QMX that means two speeds.** A **planner** on the PC turns proof and slow regime labels into a **placement plan**. A **gate** on the node checks cheap live facts against that plan every bar.
5. **The plan is a cached file with an expiry.** It carries a version, a sequence number, a "refresh by" time and a "stop using after" time. This is what Envoy, Cloudflare Quicksilver, Netflix Hollow and HTTP caches do. CHECKED (§1).
6. **Live facts become "taints" on a market, like Kubernetes taints.** Examples: spread too wide, flash move, feed stale, news window, session closed. Each unit's plan entry lists which taints it tolerates. CHECKED (Kubernetes); the mapping is INFERRED.
7. **The fast lane may only block new entries. The slow lane may move units.** A false alarm in the fast lane costs one skipped trade, so it can react quickly. Open trades stay with the unit, and account damage stays with the kill switch. INFERRED (`07a` idea 123).
8. **The node always runs from its cached plan, whether or not the PC is online.** So "PC offline" is not a special mode. It only means the plan stops being refreshed. That follows AWS "static stability" and "avoid fallback". CHECKED (§1.6).
9. **Recommendation: split the router.** Put the planner centrally (the PC today, any machine later) and the gate on the node. Neither "central only" nor "node only" survives the edge cases as simply. INFERRED (§3).
10. **Build no index, ranker, ML model or event bus in the hot path.** At QMX's size, a plain loop over every seat on every bar is the simplest and most reliable choice (the AWS "constant work" pattern). CHECKED (§1.6); the QMX sizing is INFERRED.

---

## 1. How other systems make matching fast

### 1.1 Kubernetes scheduler: filter, then score, then stop early

- **Two steps.** It first filters out every node that cannot run the pod, then scores the nodes that remain. A filter stops at the first failure for that node. CHECKED (https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/ ; https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/).
- **It stops looking once it has enough.** `percentageOfNodesToScore` stops the search after enough feasible nodes are found. The default is 50% for 100 nodes and 10% for 5,000. Below 100 nodes it checks them all, because there is nothing to gain. CHECKED (https://kubernetes.io/docs/concepts/scheduling-eviction/scheduler-perf-tuning/).
- **Taints and tolerations.** A node carries taints, and a pod lists the taints it tolerates. There are three effects:
  - `NoSchedule` (no new pods)
  - `PreferNoSchedule` (avoid if possible)
  - `NoExecute` (evict running pods, optionally after `tolerationSeconds`).
  CHECKED (https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/).
- **Conditions become taints automatically.** The control plane adds `unreachable`, `not-ready`, `memory-pressure` and similar taints when node conditions change. Pods get a default 300-second tolerance before eviction. The rate of new taints is limited so that a network cut does not evict everything at once. CHECKED (same page).
- **Heartbeats are leases.** The kubelet renews a Lease every 10 seconds. A node becomes "Unknown" after a 50-second grace period, and eviction waits a further 5 minutes. CHECKED (https://kubernetes.io/docs/reference/node/node-status/ ; https://kubernetes.io/docs/concepts/architecture/nodes/).

**Lesson for QMX:** keep hard rules as cheap filters, use scoring only on what survives, describe market conditions as taints, and make units declare what they tolerate. INFERRED.

### 1.2 Recommendation feeds: precompute candidates, rank a few live

- **YouTube** splits retrieval in two. Candidate generation picks hundreds of videos from millions using coarse features. A richer ranking model then scores only those few hundred. CHECKED (https://static.googleusercontent.com/media/research.google.com/en/pubs/archive/45530.pdf §2, §4).
- **Instagram Explore** first filters out ineligible content, then builds an eligible inventory per person. On each request it samples 500 candidates and ranks them in three passes: 500 → 150 → 50 → 25, with cheap models first. CHECKED (https://ai.meta.com/blog/powered-by-ai-instagrams-explore-recommender-system/).
- **Instagram adds a diversity penalty.** Posts from the same author are pushed down, more strongly each time that author repeats. CHECKED (same page). This is the feed version of "do not stack correlated units on one market".

**Lesson for QMX:** the registry plays the role of "eligible inventory", built offline. The plan plays the role of "candidates for this week". The live step only filters a few dozen seats. INFERRED.

### 1.3 Ad serving and pub/sub: index the rules, probe with the event

- **Matching targeting rules fast.** Ad targeting rules and pub/sub subscriptions are Boolean expressions. An event, such as a page view or a market state, is a set of attribute values. The task is to find every rule the event satisfies. Yahoo indexed the rules in inverted lists, so each event probes the index instead of testing every rule. CHECKED (https://www.vldb.org/pvldb/vol2/vldb09-83.pdf , abstract and §1).

**Lesson for QMX:** a placement rule is exactly this shape: unit U tolerates taints {a, b} and needs session in {London, NY}. An index only pays off with millions of rules, so QMX should keep a plain list. INFERRED.

### 1.4 Load balancers: health checks, ejection, panic, draining

- **Envoy outlier detection** ejects a misbehaving host for a base time multiplied by how many times in a row it has been ejected. Repeat offenders stay out longer, and the multiplier decays while the host is healthy. A cap (`max_ejection_percent`) limits how many hosts can be ejected at once. CHECKED (https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier.html).
- **Envoy panic threshold.** If too few hosts are healthy (50% by default), Envoy either ignores health and uses all hosts, or sends traffic to none. "None" is the right choice when failures are all-or-nothing. CHECKED (https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/panic_threshold).
- **Google's lame duck state.** A backend that is shutting down asks clients to stop sending new requests and finishes the requests it already has. CHECKED (https://sre.google/sre-book/load-balancing-datacenter/).
- **Google weighted round robin.** Backends report their load and error rate, and clients adjust weights periodically. CHECKED (same page).
- **Circuit breaker.** It has three states. Closed passes calls. Open fails fast. Half-open lets a few test calls through before closing again. CHECKED (https://www.martinfowler.com/bliki/CircuitBreaker.html ; https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker).

**Lesson for QMX:**
- Use a growing cool-down for flash moves and for units that keep misbehaving.
- Fail closed when most markets are tainted at once.
- "Drain" a unit (no new entries, open trades finish) instead of killing it.

INFERRED.

### 1.5 Caches, CDNs and config distribution: ship the answer, expire it on purpose

- **HTTP stale controls (RFC 5861).** `max-age` sets how long a response is fresh. `stale-while-revalidate` lets a cache serve the old copy while it fetches a new one. `stale-if-error` lets a cache serve the old copy when the origin fails, up to a stated limit, and after that the error goes through. CHECKED (https://httpwg.org/specs/rfc5861.html §3, §4).
- **Envoy and its control plane.** When the management server is unreachable, Envoy "will latch on to the previous configuration" and keeps retrying. An optional per-resource TTL removes config when contact is lost. The TTL can be refreshed with a light heartbeat. Rejected updates leave the last valid config in place. Updates follow "make before break": add the new target before pointing traffic at it. CHECKED (https://www.envoyproxy.io/docs/envoy/v1.28.0/configuration/overview/mgmt_server ; https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol , TTL and eventual-consistency sections).
- **Cloudflare Quicksilver.** Configuration is written centrally and replicated to every edge server, which reads it locally. That is 90% of reads under 1 ms. Each update carries a sequence number, so a gap shows that an update was missed. Secondary mains keep enough history for a machine to be offline for a week and resync. CHECKED (https://blog.cloudflare.com/introducing-quicksilver-configuration-distribution-at-internet-scale/ ; https://blog.cloudflare.com/quicksilver-v2-evolution-of-a-globally-distributed-key-value-store-part-2-of-2/).
- **Netflix Hollow.** A producer publishes snapshots and deltas. A validator runs before a new state is announced, and a failed validation rolls the producer back. Consumers hold the whole dataset in memory and can pin to an older version. CHECKED (https://hollow.how/producer-consumer-apis/ ; https://hollow.how/getting-started/).

**Lesson for QMX:** the plan is a small, versioned, validated file that the node holds locally. It has two clocks, "fresh until" and "usable until stale". INFERRED.

### 1.6 Static stability, constant work, and why "fallback" is a trap

- **Static stability (AWS).** The data plane keeps its existing state and keeps working when the control plane is impaired. It gets no updates, but "everything that had been working before continues to work." Control planes have more moving parts and fail more often. CHECKED (https://aws.amazon.com/builders-library/static-stability-using-availability-zones/ ; https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/static-stability.html).
- **Avoid fallback (AWS).** A fallback path runs rarely, so it is likely to be broken when it is needed. AWS prefers:
  - pushing data proactively to where it is needed, such as IAM credentials pushed to each instance and valid for hours
  - making the main path robust
  - running any second path all the time.
  CHECKED (https://aws.amazon.com/builders-library/avoiding-fallback-in-distributed-systems/).
- **Constant work (AWS).** Route 53 pushes a fixed-size table of health statuses to its DNS servers every few seconds. At query time each server cross-references every candidate answer against that table, including answers it has already found healthy. AWS Hyperplane nodes reload the full config file every few seconds even when nothing has changed. The idea: "they don't have modes", and under stress they do the same work or less. CHECKED (https://builder.aws.com/content/3F05oqNtNUWxHJ5r6L6I2HrH4rI/reliability-constant-work-and-a-good-cup-of-coffee).

**Lesson for QMX:** the node should always run from its local plan, and the gate should evaluate every seat every bar. That leaves no offline mode to test separately and no event storm to fall behind on. INFERRED.

### 1.7 Feature stores and materialised views: precomputed baselines plus fresh values

- **Feast and Uber Palette.** An offline store keeps history for training. An online key-value store keeps the latest value for live reads. Batch jobs compute the slow features, and streaming jobs (Flink) compute the near-real-time ones. The same definition feeds both stores, to avoid "training-serving skew". CHECKED (https://docs.feast.dev/v0.14-branch/getting-started/quickstart ; https://www.infoq.com/presentations/michelangelo-palette-uber/).
- **Materialize.** A materialised view is updated as each input change arrives, so reads are just memory lookups. CHECKED (https://materialize.com/docs/fundamentals/concepts/arrangements/).
- **Kafka log compaction.** It keeps the latest value per key, so a restarted consumer can rebuild current state. CHECKED (https://docs.confluent.io/kafka/design/log_compaction.html).

**Lesson for QMX:**
- The "usual level for this time of day" is a batch feature: a seasonal baseline table built offline.
- The live value is a streaming feature.
- The ratio between them is one division.
- The same code must compute these facts in QMB and on the node, or proof and live states will differ (`07b` S2e).

INFERRED.

### 1.8 The techniques in one table

| Technique | Who does it (CHECKED above) | QMX use (INFERRED) |
|---|---|---|
| Precompute offline, decide online with lookups | YouTube, Instagram, feature stores | Registry and plan offline; gate online |
| Filter before score; stop early | Kubernetes | Hard taints first; the planner scores; the gate only filters |
| Taints and tolerations | Kubernetes | Market taints; tolerations per unit seat |
| Push state to the decider; read locally | Quicksilver, IAM roles, Route 53 | Plan and baselines shipped to the node |
| Cache with fresh time and stale limit | RFC 5861, Envoy TTL | Plan `fresh_until` and `hard_until` |
| Sequence numbers and validation before publishing | Quicksilver, Hollow | Plan `seq`; node rejects gaps and bad plans |
| Last known good on control-plane loss | Envoy, AWS static stability | Node keeps trading from the cached plan |
| Constant work, no modes | Route 53, Hyperplane | Gate loops over every seat every bar |
| Growing cool-down on repeat failures | Envoy outlier ejection | Flash-move and cost-drift cool-downs |
| Fail closed when most targets are bad | Envoy panic (no-hosts mode) | Many markets tainted → no new entries anywhere |
| Drain, not kill | Google lame duck | Moving a unit: block new entries, let open trades finish |
| Diversity penalty | Instagram | Planner limits same-family units per market |
| Lease heartbeats with a grace period | Kubernetes | PC ↔ node link status, with no drastic action on loss |
| Event-driven rebuild of a view | Materialize, Kafka | Planner reruns on events, not on a timer alone |

---

## 2. Mapping the techniques onto QMX's router

### 2.1 The picture

```
            SLOW LANE  (PC today; any machine later)                    FAST LANE  (node, near broker)
  ┌──────────────────────────────────────────────────────┐    ┌───────────────────────────────────────────┐
  │                                                      │    │                                           │
  │  QMB grid runs ──► REGISTRY  (proof per cell)        │    │  broker stream ──► LABELERS (facts)       │
  │                     unit × instrument × timeframe    │    │   spread, range/vol, tick rate, depth,    │
  │                     × window × state, + evidence     │    │   feed age, gap, session, news window     │
  │                          │                           │    │            │                              │
  │  slow regime labels ─────┤                           │    │            ▼                              │
  │  correlation families ───┤                           │    │   live ÷ BASELINE  ──► TAINTS per market  │
  │  venue limits, capital ──┤                           │    │            │                              │
  │                          ▼                           │    │            ▼                              │
  │                     PLANNER  (deterministic code)    │    │   GATE, every bar, every seat:            │
  │                          │                           │    │     plan usable? in window? facts fresh?  │
  │                          ▼                           │    │     every taint tolerated? cap free?      │
  │                 PLACEMENT PLAN  (signed file)        │    │            │                              │
  │                  seats, tolerations, priorities,     │ push│            ▼                              │
  │                  seasonal baselines, calendar,       ├────►│   seat OPEN / CLOSED for new entries      │
  │                  version, seq, fresh_until,          │    │            │                              │
  │                  hard_until                          │    │            ▼                              │
  │                                                      │◄───┤   decision journal ──► synced back        │
  └──────────────────────────────────────────────────────┘ sync└───────────────────────────────────────────┘
                                                                  units trade their own way inside open seats
                                                                  kill switch stays separate, always local
```

### 2.2 What is precomputed, and when

| Thing | Where it is built | Rebuilt when | Changes how often |
|---|---|---|---|
| **Registry**: proof per cell (unit version, instrument, venue, timeframe, window, optional state bucket, grade preferred/hypothetical, run ids, cost-calibration version, trade count, anti-luck stats, tolerations, exclusions) | PC, from QMB results in the Library | New QMB result, new unit version, new cost calibration, operator edit | Days to weeks |
| **Seasonal baselines**: the usual spread, range, tick rate and depth per (venue, instrument, time-of-week bucket) | PC from history, or the node from its own recorded stream | Weekly, plus calendar events (DST shift, holiday, contract roll) | Weekly |
| **Slow regime labels** (T3 in `05` §1.1) | PC | Daily, or on a confirmed change flag | Hours to weeks, and they lag by that much |
| **Placement plan**: the chosen seats for the next period | PC planner | Daily, plus events (§2.5) | Daily |

All of this is INFERRED design. The registry and baseline shapes follow `seeds.md` (registry, key-value), `01` §1.5 (the SQS baseline is already keyed by venue, environment and instrument, CHECKED) and `05` §1.6 (make that baseline generic, INFERRED there).

**One plan seat (INFERRED shape):**

```
seat:
  seat_id, unit_id@version, venue, instrument, timeframe
  windows:      [London 07:00-11:00, NY overlap 12:00-16:00]   # sessions or sniping windows with proof
  grade:        preferred | hypothetical (probe size only)
  tolerates:    [wide-spread:soft, news:none, roll-week:none, ...]
  family:       correlation family id        # for caps and anti-affinity
  priority:     1..n                         # who wins when seats compete
  evidence:     registry cell ids
plan:
  plan_version, seq, issued_at, fresh_until, hard_until, signature
  baselines_version, calendar_version
```

### 2.3 What is computed live (cheap facts only)

Every fact below is a direct observation or one division. None of them is a model. Their lag is only the smoothing window, measured in seconds to minutes. CHECKED (`05-academic.md` §1.1 T0/T1 rows, §1.3).

| Fact | How | Taint when bad (example) |
|---|---|---|
| Session and window | Clock plus venue calendar | `session-closed` |
| News window | Calendar (the KSA news windows already exist, CHECKED `01` §2 row 32) | `news` |
| Feed age | Time since the last tick (the feed-state labeler exists, CHECKED `01` §1.5) | `feed-stale` |
| Gap | Gap-event labeler (exists, CHECKED `01` §1.5) | `gap` |
| Spread ratio | Live spread ÷ baseline (SQS, exists, with hysteresis, CHECKED `01` §1.5) | `wide-spread` |
| Range or vol ratio | High-low range or tick variance ÷ baseline (range needs about 5× fewer bars than closes, CHECKED `05` §1.3) | `flash-move`, `dead-market` |
| Tick rate and depth ratio | Live ÷ baseline | `thin-liquidity` |
| Cost drift | Live fill cost ÷ the cost the proof assumed | `cost-drift` (per seat) |

**Live-only rule.** A regime model never runs in the gate. Detecting a 1.5× volatility change from 1-minute closes takes about 44 minutes, and a new trend takes hours. A scalper's holding time passes many times over in that span. So regime belongs to the planner. CHECKED (`05` §1.2, §1.3).

### 2.4 The gate (the whole live router)

```
every closed bar (or every N seconds), for every seat in the plan:

  open_for_new_entries(seat) =
        plan.now < plan.hard_until
    and seat.window contains now
    and facts for seat.instrument are younger than their max age
    and every active taint on (venue, instrument) is in seat.tolerates
    and seat has no own taint (cost-drift, cool-down)
    and family / venue caps are not full (priority decides)

  log (seat, inputs, result) to the decision journal
```

- **Why loop over everything:** at, say, 50 seats and 10 taints per bar, the gate makes about 500 comparisons. That is microseconds. No index, cache layer or event bus is needed, and the code has no modes (AWS constant work). INFERRED.
- **What the gate never does:** it never sizes, exits or changes a unit's rules. A seat is only open or closed for new entries. Open trades are managed by the unit under the profile they opened with (sticky sessions, `07a` idea 32). INFERRED.
- **Replay:** the gate is a pure function of (plan, facts, clock). QMB can therefore run the same gate code on history (`07b` S2e; `07a` Round 3: "router decisions must be replayable"). INFERRED.

### 2.5 What is cached, for how long, and what refreshes it

| Cached item | Where | Fresh for (example) | Stale but usable for (example) | Refreshed by |
|---|---|---|---|---|
| Placement plan | Node disk and memory | `fresh_until` = 24 h | until `hard_until` = 5 trading days | Daily plan run, plus events below |
| Seasonal baselines | Node, inside the plan bundle | 7 days | 14 days, then taint `baseline-stale` | Weekly job; calendar events |
| Venue calendar | Node, inside the plan bundle | to the end of the published calendar | none; past the end, taint `no-calendar` | Plan push |
| Live facts | Node memory | max age per fact (seconds) | none; past max age, taint `feed-stale` | The broker stream |
| Registry | PC (Library) | no time expiry; versioned | n/a | Events only |

**Events that trigger a new plan** (event-driven, as in Materialize):
- a new QMB proof
- a unit admitted or removed by the operator
- a slow regime label flip
- the start of the trading week
- a DST or holiday calendar shift
- a correlation spike between seated units
- a node-reported health problem (a seat drained for cost drift, repeated cool-downs).

Events are an extra trigger on top of the daily run, never a replacement for it. INFERRED.

**Push, validate, then switch** (Hollow, Quicksilver, Envoy):
1. The PC builds the plan and validates it: schema, every seat cites registry cells, caps respected.
2. The PC pushes the full plan. It is a few KB, so deltas are not worth the complexity.
3. The node checks the signature and that `seq` = last + 1.
4. The node switches between bars. A unit moving markets is handled make-before-break: its old seat drains and its new seat opens.
5. A rejected plan leaves the old plan running and raises an alert.

INFERRED design over CHECKED patterns.

### 2.6 When the PC is offline and only the node runs

```
PC link   up ───────────┐ lost                                       ┌── back
                        │                                            │
plan      [fresh]───────┼──[stale: still used, alert shown]──────────┼──[new plan pushed]
                        │          ...                hard_until     │
                        │                                 │          │
gate      normal ───────┴── normal (same code) ───────────┴─ all seats closed to new entries
                                                            (units manage open trades,
                                                             kill switch still armed)
```

- **Nothing changes at the moment the link drops.** The node keeps using the cached plan, as Envoy and AWS data planes do. The gate code is identical online and offline. CHECKED (pattern); INFERRED (QMX).
- **Between `fresh_until` and `hard_until`:** trading continues, and the operator sees "plan N hours old" when he looks. This is `stale-if-error`. INFERRED.
- **After `hard_until`:** no new entries anywhere, and open trades finish under the units' own exits. This is the one place where time alone changes behaviour, so it must be drilled (below). INFERRED.
- **Kill switch:** fully local and independent of the plan. Which levels fire alone is still open (`01` §2 row 36, CHECKED). INFERRED.
- **On reconnect:**
  1. The node uploads its journal and decision log.
  2. The PC replays the node's decisions from the logged inputs and checks they match. This is the "router self-test on connect", `07a` §3.21.
  3. The PC pushes a fresh plan.

  INFERRED.
- **Drill the expiry.** The node self-test on connect (`seeds.md`, trading-node seed) should include a forced short `hard_until` on a demo seat, to prove the stop works. That follows AWS's advice to exercise rare paths. INFERRED.

---

## 3. Where the router lives

### 3.1 Options

| | A. Central only | B. Node only | C. Split: planner central, gate on node |
|---|---|---|---|
| What runs where | The PC decides every seat open or closed and tells the node | The node holds the registry, baselines, regime models and planner | The PC builds and pushes the plan; the node runs the gate |
| PC offline | **Breaks**: no new decisions, so the node must guess or stop | Works | Works on the cached plan until `hard_until` |
| Live latency | A network round trip per decision | Local | Local |
| Node size | Small | Large: needs the Library, QMB results and models. Cuts against "simplify QMN to its basics" (CHECKED `seeds.md`) | Small: labelers, gate, plan file, kill switch |
| Operator can see and edit | Easy | Harder: state lives on a remote server | Easy: the plan is built where the Library and UI are |
| Many nodes later | One brain | Each node plans alone, with no shared view of correlation across nodes | One planner, one plan slice per node (like Envoy xDS per proxy) |
| Replay and proof | Needs a log of central inputs | Needs a log of everything on the node | Plan file plus node fact log replays both halves |
| Matches the seed? | No: the seed says the node holds the MIS | Literally yes | Yes, if "the node holds the MIS" means its live half (§3.3) |

### 3.2 Recommendation: C, split

Reasons:
1. **Static stability.** The data plane (node) keeps working when the control plane (PC) is gone. This is the main reason the node exists at all: "they keep trading when his laptop is closed". CHECKED (`seeds.md`; AWS static stability).
2. **Each half sits next to its data.** Proof lives in the Library and QMB, on the PC side. Fast facts live in the broker stream, on the node side. Moving either half wastes effort. INFERRED.
3. **It keeps the node small**, as the operator asked: labelers, a gate, a file and a kill switch. CHECKED (`seeds.md`, "simplify QMN"); INFERRED design.
4. **It scales to many nodes without redesign.** The planner writes one plan per node, as `07a` idea 135 parks for later. INFERRED.
5. **The live half needs no slow information,** so nothing is lost by keeping the planner away from the venue. The detection-lag bound means faster regime calls are not possible anyway. CHECKED (`05` §1.3).

"Central" does not have to mean his laptop. The planner is a deterministic job, and it can run on any connected machine that can read the Library (the Lego "any compute provider" idea). INFERRED.

### 3.3 One wording to confirm with the operator

`seeds.md` says "the trading node keeps only the MIS and the kill switch." Under option C:
- the node keeps the MIS's **live half** (labelers, taints, gate, cached plan)
- the **planning half** runs where the Library is.

If he meant that the whole MIS must sit on the node, option B is the fallback. It costs a much bigger node. INFERRED; this is a vocabulary check, not a new decision.

---

## 4. The hard edge cases, handled simply

### 4.1 Stale cache

| What is stale | Detection | Behaviour |
|---|---|---|
| Plan (PC offline or planner failed) | `now > fresh_until` | Keep using it and show an alert; at `hard_until`, no new entries |
| Plan missed an update | `seq` gap | Keep the old plan, ask for a full resend (Quicksilver) |
| Bad new plan | Signature or validation fails | Keep the old plan (Envoy last valid config; Hollow rollback) |
| Baselines (DST, holiday, roll) | `baselines_version` age; calendar events | Calendar events trigger a rebuild; past the limit, taint `baseline-stale` and seats close unless they tolerate it |
| Proof itself (the unit has decayed live) | Node-side `cost-drift` and live-versus-replay drift (`07a` idea 28) | Fast: the node drains that seat (blocks new entries). Slow: the planner removes or demotes it |
| Regime moved but the plan has not | Nothing fast can see this; that is the 44-minute bound | Fast taints still guard the cheap facts. The planner reruns on the label flip. Accept the lag |

All INFERRED, built on the CHECKED patterns in §1.5-1.6.

### 4.2 Flash move

- **Detection:** range or tick-variance ratio over its threshold within the smoothing window. That takes seconds to a few minutes, not 44 minutes, because range and tick data carry more information than closes. CHECKED (`05` §1.3, Parkinson).
- **Effect:** taint `flash-move` on that market at once. Effect: no new entries for seats that do not tolerate it. INFERRED.
- **Clearing:** only after the ratio stays calm for a cool-down. The cool-down grows each time the taint repeats within a day, like Envoy ejection time, and decays afterwards. This is hysteresis, so seats do not flap. INFERRED over CHECKED Envoy behaviour.
- **False alarms are fine.** A spike that was nothing costs one skipped entry. That is why this lane may be twitchy, and why it may only block (`07a` idea 123). Robust detectors are for the slow lane (`05` §1.5). INFERRED.
- **Open trades:** handled by the unit's own stops. Account damage is handled by the kill switch. The router does not touch either. INFERRED.

### 4.3 Feed gap

- Each fact has a maximum age. Past it, the market gets `feed-stale`, and seats there close to new entries. CHECKED (feed-state labeler exists, `01` §1.5); INFERRED rule.
- After the feed returns, the taint holds until enough fresh bars refill the smoothing windows (warm-up). Ratios computed on a half-empty window are not trusted. INFERRED.
- If one venue's whole feed is stale, taint the venue, not each instrument. INFERRED.

### 4.4 Many units want the same market

- **Settle it in the planner, not live.** The planner applies:
  - a per-market cap on seats
  - a per-family cap (correlation family, so 1m and 5m of one logic on one pair count as one bet, CHECKED `seeds.md` caveat)
  - venue request and order budgets (cTrader request limits and Hyperliquid's request budget, CHECKED via `07a` idea 36).

  Seats get a **priority** from proof strength, with a diversity penalty for repeats in a family, as Instagram does. INFERRED.
- **Live, the gate only enforces caps by priority.** If two seats of one family want to enter on the same bar, the higher priority goes first. The cap then blocks the other. No live auction. INFERRED.
- Sizing across units stays out of the router. It belongs to the units and the account guard (`seeds.md`: "The MIS stays outside"). INFERRED.

### 4.5 The node loses its PC link

- See §2.6. In short: same code, same plan, an alert when the plan is old, no new entries after `hard_until`, and the kill switch stays armed.
- **Link status works like a lease.** The PC renews the plan's lease with a light heartbeat, the way Envoy TTL heartbeats work. The node shows "PC link lost at T". Nothing drastic happens on loss, just as Kubernetes rate-limits evictions after a network cut. CHECKED (patterns); INFERRED (QMX).
- **Panic case:** if most markets on a node are tainted at once (a broker or venue failure, a global event), the node fails closed: no new entries anywhere. It does not "spread to all", following Envoy's no-hosts panic mode. CHECKED (Envoy); INFERRED (QMX choice).

---

## 5. What not to build (keeps it simple)

- No per-tick re-ranking or scoring on the node. Scoring is the planner's job.
- No regime model, HMM, BOCPD or ML model in the gate. CHECKED (`05` §1.2, §1.3) for why.
- No index structure, Redis, Kafka or stream processor. A list, a dict and a loop fit QMX's size. INFERRED.
- No separate offline mode. The node always runs from the cached plan. CHECKED (AWS avoid fallback).
- No live call from the node to the PC on the trading path. INFERRED.
- No router control over size, exits or rules. CHECKED (`seeds.md`).

---

## 6. Open points for the design session (not questions for now)

1. The default values for `fresh_until`, `hard_until`, cool-downs and fact max ages. They need UI fields with no built-in defaults. INFERRED.
2. Whether a hypothetical seat may stay open after `fresh_until` or must close earlier than preferred seats. INFERRED.
3. Who signs a plan: the planner key, his click for first admission only, or both. The seed's "manual admission" rule covers units, not daily plans. CHECKED (`seeds.md`, trading-node seed); the rest is INFERRED.
4. Where the seasonal baselines are built: on the PC from history, or on the node from its own stream. The node's version follows its live feed exactly. The PC's version matches what QMB used. INFERRED.
5. Registry form, from `07a` disagreement D8. This design fits Hal's "query for proof, stored record for placement": the registry can be a query, and the plan is the stored, signed record. INFERRED.

---

## Sources (all read 2026-10-24)

Scheduling
- Kubernetes scheduler: https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/
- Scheduling framework: https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/
- Scheduler performance tuning: https://kubernetes.io/docs/concepts/scheduling-eviction/scheduler-perf-tuning/
- Taints and tolerations: https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
- Node status and heartbeats: https://kubernetes.io/docs/reference/node/node-status/ ; https://kubernetes.io/docs/concepts/architecture/nodes/

Recommendation and ads
- Covington, Adams & Sargin 2016, YouTube: https://static.googleusercontent.com/media/research.google.com/en/pubs/archive/45530.pdf
- Meta AI, Instagram Explore: https://ai.meta.com/blog/powered-by-ai-instagrams-explore-recommender-system/
- Whang et al. 2009, Indexing Boolean Expressions (Yahoo): https://www.vldb.org/pvldb/vol2/vldb09-83.pdf

Load balancing and resilience
- Envoy outlier detection: https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier.html
- Envoy panic threshold: https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/panic_threshold
- Envoy management server unreachability: https://www.envoyproxy.io/docs/envoy/v1.28.0/configuration/overview/mgmt_server
- Envoy xDS protocol (TTL, make before break): https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol
- Google SRE, Load Balancing in the Datacenter: https://sre.google/sre-book/load-balancing-datacenter/
- Fowler, Circuit Breaker: https://www.martinfowler.com/bliki/CircuitBreaker.html ; Azure pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
- AWS, Static stability: https://aws.amazon.com/builders-library/static-stability-using-availability-zones/ ; https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/static-stability.html
- AWS, Avoiding fallback: https://aws.amazon.com/builders-library/avoiding-fallback-in-distributed-systems/
- AWS, Constant work: https://builder.aws.com/content/3F05oqNtNUWxHJ5r6L6I2HrH4rI/reliability-constant-work-and-a-good-cup-of-coffee

Caching and distribution
- RFC 5861: https://httpwg.org/specs/rfc5861.html
- Cloudflare Quicksilver: https://blog.cloudflare.com/introducing-quicksilver-configuration-distribution-at-internet-scale/ ; v2: https://blog.cloudflare.com/quicksilver-v2-evolution-of-a-globally-distributed-key-value-store-part-2-of-2/
- Netflix Hollow: https://hollow.how/producer-consumer-apis/ ; https://hollow.how/getting-started/

Feature stores and views
- Feast quickstart: https://docs.feast.dev/v0.14-branch/getting-started/quickstart
- Uber Michelangelo Palette (InfoQ talk): https://www.infoq.com/presentations/michelangelo-palette-uber/
- Materialize arrangements: https://materialize.com/docs/fundamentals/concepts/arrangements/
- Kafka log compaction: https://docs.confluent.io/kafka/design/log_compaction.html

QMX inputs
- `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\seeds.md`
- `D:\QMX-worktrees\agent-system\tracker\risk-sizing\research\01-ground-truth.md` (§0, §1.4, §1.5, §2)
- `D:\QMX-worktrees\agent-system\tracker\risk-sizing\research\05-academic.md` (§1)
- `D:\QMX-worktrees\agent-system\tracker\risk-sizing\research\07a-funnel-party.md` (Round 3, ideas list, D7, D8)
- `D:\QMX-worktrees\agent-system\tracker\risk-sizing\research\07b-funnel-cis.md` (S2a-S2e)
