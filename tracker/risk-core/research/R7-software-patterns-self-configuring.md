---
ticket: R7-software-patterns-self-configuring
title: Software that already works like a self-configuring unit, and what QMX could borrow
date: 2026-11-03
author: opus research agent (read-only on the repo; this file is the only write)
asked by: operator, 3 Nov 2026: "For mini apps, VS Code made sense. But for a unit, a self-configuring one... somewhere, somehow, software has to have something like that."
method: URLs found with web search, pages read in the built-in browser (navigate, then page text or a text search inside the page). Raw source files (HotSpot, Terraform, Guava, OpenFeature spec, Kubernetes API conventions, NixOS manual sources, ESLint docs, Hystrix README) fetched as text with curl, time-limited. Two PDFs (OtterTune, Kephart and Chess) turned to text with pdftotext. Two arXiv papers read through alphaXiv.
labels: CHECKED = seen in a vendor page, a spec or source code this run (link given). SNIPPET = seen only in a search-result summary; weakest grade. INFERRED = my reading of the checked facts. [judgment] = one line on what a QMX unit or its risk template could borrow; an opinion, not a design.
builds on: `grounding/G8-unit-chassis-and-extensibility.md` sections 1 to 4 (cited as G8 x.y) and `research/R1-platforms-risk-sizing-extensibility.md` (n8n, LEAN, StrategyQuant, Nautilus, MT5 money classes). R1 is not repeated here.
not done: QMX is not designed here. No account was made and nothing was signed in to. Nothing was committed.
---

# R7: Software that already works like a self-configuring unit

## 0. The short answer

1. **The closest match is the Kubernetes controller model, with the Vertical Pod Autoscaler (VPA) as its self-tuning part.** An object has a typed spec with defaults. The owner writes limits into the spec. A recommender learns a value from that object's own decayed history and writes a target plus a low and a high bound into the object's status. A separate updater applies the value only in the mode the owner chose: off, only at start, or live. This is the same shape as a QMX number with `range`, `motion`, `authority` and a calibration row (G8 1.1, 3.9, 3.10). See section 2.5 and 11.
2. **For versions, the closest match is progressive delivery: Argo Rollouts with Kayenta-style canary analysis.** A new version gets a small share first. An analysis template judges it against a fresh copy of the old version running at the same time. The run ends in one of three states: pass (go on), fail (roll back), or inconclusive (pause for a human). See 4.1 to 4.3.
3. **Every evidence-driven sizer in software grows slowly, shrinks by the strength of the signal, and has a floor and a ceiling.** TCP halves on a mild loss signal and drops to one segment on a timeout. Netflix's AIMD limit grows by one only when at least half the current limit is in use, and multiplies by 0.9 on a drop. See 2.1 and 2.2.
4. **"Shrink slowly, not on one bad day" exists as a named setting.** The Kubernetes HPA, before it scales down, takes the highest recommendation of the last 300 seconds. It also treats missing data as "no change" in the cautious direction. See 2.4.
5. **Self-tuning software always keeps a slow, safe path and a counter of failed guesses.** HotSpot falls back to the interpreter when a speculation fails, and after 400 recompiles of one method it stays in the interpreter. The Simplex architecture switches to a simple verified controller near the edge of the safe region, and switches back only after a dwell time. See 2.7 and 8.2.
6. **Brakes in resilience libraries are graded, sample-aware and testable in shadow.** resilience4j needs 100 calls before it judges, probes with 10 calls in a half-open state, and has a METRICS_ONLY state that records but never trips. Envoy ejects outliers by comparing peers, never ejects more than 10 % of a cluster, and grows the ejection time with each repeat. See 5.1 and 5.3.
7. **Levels nest the same way in every cascade.** The most specific level wins for normal values. An outer level can mark a value "important" or "policy", and then the outer level wins. CSS, VS Code policy settings, Nix priorities and ESLint's `noInlineConfig` all do this. See section 6.
8. **The one template system that breaks its users is the one with no versions.** Home Assistant re-imports a blueprint by overwriting it, and warns this "can break your automations". Simulink solves the same problem with forwarding tables that map an old block version to a new one, with a function that maps old parameters to new. See 7.2 and 7.3.
9. **Trading platforms are the weakest models here.** MT5 makes inputs read-only to the program, so an EA cannot tune them. TradingView's `strategy.risk.*` commands are always on and cannot be bypassed, but every one is a cliff (cancel, close, stop). See section 9.

---

## 1. What a match must do (from G8 and the brief)

Each system below is read against eight needs. They come from the unit as built (G8) and from his words in the brief.

| Need | What it means for a unit | Where the unit stands (G8) |
|---|---|---|
| N1 defaults with reasons | Every number has a default and says why | `NumberSpec` has `default`, `origin`, `authority` (1.1, 1.2) |
| N2 tunes itself from evidence | Some numbers move from the unit's own record and market facts | Two motion modes compile; `risk_fraction` cannot move (3.10) |
| N3 safe while tuning | Moves stay inside bounds; a bad guess falls back | Shrink toward default, one step, a calibration row (3.9); `authority` and `applies_to_open_positions` never read (3.10) |
| N4 levels nest | Unit, book, methodology, BMS, account | Halts at three scopes, refused by the compiler; cross-unit hook never called (2.1, 3.5) |
| N5 extends any way | He, the copilot or agents add pieces | Blocks, Library, layer F, agent rows; no row saves a block (3.11, 4.1) |
| N6 versions | A new sizer or halt is a new version or unit | Identity table; the rip-out costs each unit its record (3.6) |
| N7 runs alone on the node | No outside call at trade time | Sizer, exits, halts run inside the hosted unit (G8 6.3) |
| N8 graded brakes | Size down slowly; no cliffs | Halts are `no_new_entries` or `flatten` only (2.1) |

---

## 2. Control loops that size up and down by evidence

### 2.1 TCP congestion control (RFC 5681) — CHECKED

Source: [RFC 5681](https://www.rfc-editor.org/rfc/rfc5681.html), sections 3.1, 3.2, 4.1.

- **Mechanism.** The sender keeps a "congestion window": how much data may be in flight. It starts small. In slow start it grows by up to one segment per acknowledgement, which roughly doubles it each round trip. Past a threshold (`ssthresh`) it grows by about one segment per round trip.
- **Inputs and outputs.** In: acknowledgements (proof of delivery), duplicate acknowledgements, timeouts. Out: the window size.
- **The cut is graded by how bad the signal is.**
  - On the third duplicate acknowledgement (a mild signal), `ssthresh = max(FlightSize / 2, 2*SMSS)` and sending goes on from there.
  - On a timeout (a severe signal), the window "MUST be set to no more than the loss window, LW, which equals 1 full-sized segment", then slow start again.
- **After idle.** "A TCP SHOULD set cwnd to no more than RW before beginning transmission if the TCP has not sent data in an interval exceeding the retransmission timeout." A connection that went quiet starts small again.
- **Defaults and overrides.** The initial window has a hard upper bound (2, 3 or 4 segments by segment size). The initial `ssthresh` "SHOULD be set arbitrarily high", so that "network conditions, rather than some arbitrary host limit" set the rate.
- **Safety when it tunes itself.** Growth is counted in bytes acknowledged, not in the number of acknowledgements. The RFC calls this robustness against a receiver that tries "to artificially inflate cwnd" by splitting acknowledgements ("ACK Division").
- **Versions.** Not covered by this RFC.
- **[judgment]** Borrow three things for a sizer's moving size: grow only on closed evidence, cut by the severity of the signal (a stop-out is not a slow bleed), and restart small after a long idle spell. Also count evidence in R or money, not in trade count, so that many tiny trades cannot inflate the size.

### 2.2 Netflix concurrency-limits (TCP ideas applied to services) — CHECKED

Sources: [README](https://github.com/Netflix/concurrency-limits), [AIMDLimit.java](https://github.com/Netflix/concurrency-limits/blob/master/concurrency-limits-core/src/main/java/com/netflix/concurrency/limits/limit/AIMDLimit.java), [Hystrix README](https://github.com/Netflix/Hystrix).

- **Mechanism.** The library treats a service's concurrency limit as a TCP window. It finds the limit by measuring instead of setting it by hand.
- **The AIMD rule in code.** On a drop, or a response slower than the timeout (default 5 s), the limit is multiplied by `backoffRatio` (default 0.9; the builder refuses values outside 0.5 to below 1.0). Otherwise, and only when `inflight * 2 >= currentLimit`, the limit grows by 1. The result is clamped to `minLimit` 20 and `maxLimit` 200. The initial limit is 20.
- **Growth needs use.** The limit grows only when at least half of it is in use. Unused headroom earns nothing.
- **Shares.** A "percentage" strategy guarantees request groups a share of the limit, for example live 90 % and batch 10 %.
- **Why it exists.** Netflix's Hystrix README says Netflix's focus "has shifted towards more adaptive implementations that react to an application's real time performance rather than pre-configured settings".
- **Versions.** Not covered.
- **[judgment]** Grow a size only after trades were actually taken at the current size, and keep hard floor and ceiling bounds with a validated backoff range. The guaranteed-share strategy is a ready shape for unit shares inside a book or BMS budget.

### 2.3 Adaptive bitrate streaming (dash.js) — CHECKED

Sources: [dash.js ABR overview](https://dashif.org/dash.js/pages/usage/abr/), [ABR settings](https://dashif.org/dash.js/pages/usage/abr/settings.html), [ABRRulesCollection.js](https://github.com/Dash-Industry-Forum/dash.js/blob/development/src/streaming/rules/abr/ABRRulesCollection.js).

- **Mechanism.** The player picks a video quality each segment. "Each rule casts a switch request, the results are aggregated into the final quality decision."
- **How proposals combine (source).** Each request has a priority: weak, default or strong. Within one priority the lowest bitrate wins. A strong request overrides a default one, and a default overrides a weak one. Only one of the two main rules runs at a time: the throughput rule or BOLA (buffer-based), chosen by buffer level.
- **Safety rules beside the main rule.** InsufficientBufferRule, AbandonRequestRule, DroppedFramesRule and SwitchHistoryRule (which "penalizes qualities that were recently abandoned").
- **Defaults and overrides.** The app sets `initialBitrate`, `minBitrate` and `maxBitrate`. Built-in rules can be switched off one by one, and a custom rule is added with `player.addABRCustomRule()`.
- **Versions.** Not covered.
- **[judgment]** This is a working model for many sizing opinions on one trade. Each modifier proposes a cap with a reason, the smallest cap wins within a priority, and a strong priority (a halt) beats the rest. Today a `sizing_modifier` slot can only gate (G8 1.1).

### 2.4 Kubernetes Horizontal Pod Autoscaler (HPA) — CHECKED

Source: [HPA docs](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/).

- **Mechanism.** `desiredReplicas = ceil(currentReplicas × currentMetricValue / desiredMetricValue)`. If the ratio is within a tolerance of 1.0 (default 0.1), nothing changes.
- **The two directions have separate settings.** The defaults are:
  - Scale down: a stabilization window of 300 s, and at most 100 % of pods removed per 15 s.
  - Scale up: no window, and at most the larger of 100 % or 4 pods per 15 s (`selectPolicy: Max`).
  - `selectPolicy: Min` picks the most cautious policy. `Disabled` turns a direction off.
- **"Don't act on one bad reading".** For scale-down, "the algorithm looks into previously computed desired states, and uses the highest value from the specified interval". This "approximates a rolling maximum".
- **Missing data is cautious.** If metrics are missing, the controller assumes those pods use 100 % of the target on a scale-down and 0 % on a scale-up. "If the new ratio reverses the scale direction, or is within the tolerance, the controller doesn't take any scaling action."
- **Warm-up is ignored.** By default the CPU of a pod in its first 5 minutes is ignored unless the pod is ready (`--horizontal-pod-autoscaler-cpu-initialization-period`).
- **Defaults and overrides.** "Only values which need to be customized can be specified. These custom values are merged with default values."
- **Versions.** Not covered here (the HPA is an object like any other).
- **[judgment]** The `behavior` block is a ready vocabulary for "size down slowly": a stabilization window per direction, a rate cap per period, a tolerance band, cautious handling of missing data, and ignoring a new unit's first trades. For QMX the defaults would point the other way: cut fast, grow slowly.

### 2.5 Kubernetes Vertical Pod Autoscaler (VPA) — CHECKED

Sources: [components.md](https://github.com/kubernetes/autoscaler/blob/master/vertical-pod-autoscaler/docs/components.md), [quickstart.md](https://github.com/kubernetes/autoscaler/blob/master/vertical-pod-autoscaler/docs/quickstart.md), [flags.md](https://github.com/kubernetes/autoscaler/blob/master/vertical-pod-autoscaler/docs/flags.md), [features.md](https://github.com/kubernetes/autoscaler/blob/master/vertical-pod-autoscaler/docs/features.md).

- **Mechanism.** Three separate parts:
  - The **recommender** "monitors the current and past resource consumption" and puts recommendations "in status of the VPA resource, where they can be inspected".
  - The **updater** decides which pods to change and applies the change in place or by eviction. It respects disruption budgets.
  - The **admission controller** sets values on new pods.
- **How the recommender learns (default flags).**
  - History is a decaying histogram. A sample loses half its weight after 24 h (`cpu-histogram-decay-half-life`).
  - The target is the 90th percentile (`target-cpu-percentile 0.9`) plus a 15 % safety margin (`recommendation-margin-fraction 0.15`).
  - The lower bound is the 50th percentile and the upper bound the 95th.
  - A "confidence multiplier" for the bounds is computed over a 24 h interval.
  - Floors: 25 millicores and 250 MB per pod.
  - After an out-of-memory event, memory is bumped by 1.2×.
- **Owner's limits.** `minAllowed` and `maxAllowed` per container, `controlledResources`, and `mode: "Off"` per container.
- **Update modes (who may apply).**
  - `"Off"`: recommendations are calculated "and can be inspected in the VPA object", and nothing changes.
  - `"Initial"`: values are set "only... on pod creation and never" changed later.
  - `"Recreate"` (the default): pods are evicted and recreated when values "differ significantly".
  - `"InPlaceOrRecreate"`, and `"InPlace"`, which never evicts.
- **Safety when it tunes itself.**
  - The updater evicts at most 50 % of replicas (`eviction-tolerance`) and needs at least 2 replicas (`min-replicas`).
  - In-place mode updates long-running pods only when the recommendation differs by more than 10 %.
  - It "tracks infeasible resize attempts to prevent infinite retry loops".
- **Versions.** Not covered by VPA itself.
- **[judgment]** This maps almost field for field onto a QMX number:
  - `range` is minAllowed and maxAllowed.
  - `motion` is the recommender.
  - `authority` is the update mode: Off is shadow, Initial is "apply only when flat or at a new position", Recreate or InPlace is live.
  - The calibration row is the status with its bounds.
  - It also shows how `risk_fraction` could move without a logic slot: from its own decayed record, inside bounds he owns (G8 3.10).

### 2.6 Database auto-tuning: OtterTune (SIGMOD 2017) — CHECKED

Source: Van Aken, Pavlo, Gordon, Zhang, [PDF copy](https://www.cs.purdue.edu/homes/csjgwang/CloudNativeDB/OtterTuneSIGMOD17.pdf), sections 3.1, 3.2, 6.

- **Mechanism.**
  1. A controller observes the database for an "observation period" and sends metrics to a tuning manager.
  2. The manager first maps the workload "to a workload for the same DBMS and hardware profile that it has seen (and tuned) in the past".
  3. It then recommends the next settings with a Gaussian process model. It either explores regions it knows little about or exploits the area near the best settings so far. It "always chooses the configuration with the greatest expected improvement".
- **Who decides.** OtterTune gives "an estimate of how much better the recommended configuration is compared to the best configuration that it has seen so far". The process "continues until the DBA is satisfied".
- **Safety.**
  - A "curated black-list of knobs for each DBMS version". The DBA may add knobs, including ones "that could have hidden or serious consequences (e.g., potentially causing the DBMS to lose data)".
  - The DBA can "tune only dynamic knobs" (no restart).
  - Tuning trials can run on "a second copy of the database" with a replayed workload.
  - Data is kept per major DBMS version, so old-version knobs are not used on a new version.
- **Defaults.** Random starting points are drawn "from within the range of valid values for that knob".
- **[judgment]** Borrow three things: a deny-list of numbers that may never self-tune (his call, per template); priors borrowed from the most similar past units when a new unit's record is empty (G8 5.1-5.2: QMB edge numbers never reach the sizer); and trying tuned values on a shadow copy (QMB or paper), not first in the money path.

### 2.7 JIT compilers that tune themselves (HotSpot) — CHECKED (source)

Sources: [globals.hpp](https://github.com/openjdk/jdk/blob/master/src/hotspot/share/runtime/globals.hpp), [compiler_globals.hpp](https://github.com/openjdk/jdk/blob/master/src/hotspot/share/compiler/compiler_globals.hpp), [deoptimization.hpp](https://github.com/openjdk/jdk/blob/master/src/hotspot/share/runtime/deoptimization.hpp).

- **Mechanism.** Code starts slow and always correct, in the interpreter. Hot methods are compiled with guesses taken from the profile. Default thresholds: tier 3 at 200 invocations, tier 4 at 5000. When a guess fails, the code "deoptimizes" with a named reason, for example `Reason_unstable_if`: "a branch predicted always false was taken".
- **Graded responses (the `DeoptAction` enum).**
  - `Action_none`: "just interpret, do not invalidate".
  - `Action_maybe_recompile`.
  - `Action_reinterpret`.
  - `Action_make_not_entrant`: "invalidate the nmethod, recompile (probably)".
  - `Action_make_not_compilable`: "invalidate the nmethod and do not compile".
- **Limits on guessing.**
  - `PerBytecodeTrapLimit` 4.
  - `PerMethodTrapLimit` 100.
  - `PerMethodRecompilationCutoff` 400: "After recompiling N times, stay in the interpreter".
  - `TieredStopAtLevel` caps how far optimization may go.
- **Versions.** Not applicable.
- **[judgment]** Treat a tuned number as a guess with a guard. When the guard trips, fall back to the default, log the reason, and count it. After a set number of trips, freeze that number at its default and flag it for him. That gives `authority` a concrete runtime meaning (G8 3.10).

---

## 3. Reconciliation and desired state

### 3.1 Kubernetes controllers and the spec/status split — CHECKED

Sources: [Controllers](https://kubernetes.io/docs/concepts/architecture/controller/), [API conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md).

- **Mechanism.** "Controllers are control loops that watch the state of your cluster, then make or request changes where needed." An object's `spec` is the desired state and its `status` the observed state.
- **Level-based, not edge-based.** If a value changes "from 2 to 5 in one PUT and then back down to 3", the system need not "touch base at 5". The conventions say this "enables robust behavior in the presence of missed intermediate state changes".
- **Separate write rights.** Users get "full write access to `spec` and read-only access to status", while "controllers are granted read-only access to `spec` but full write access to status".
- **Version of what was observed.** `observedGeneration` tells whether the reported status "reflects the most recent desired status". A condition at generation 9 while the spec is at 12 "is out of date".
- **Many small loops.** "It's useful to have simple controllers rather than one, monolithic set of control loops... Controllers can fail, so Kubernetes is designed to allow for that." Labels stop one controller from touching another's objects.
- **[judgment]** Split the unit into a spec (his and agents' choices: blocks, ranges, motion rules, authority) and a status (the runtime's tuned values, brake states, calibration rows), with separate write rights. Stamp each status with the version it belongs to, which the A10 snapshot already does by fingerprint (G8 3.7).

### 3.2 Terraform plan and apply — CHECKED

Sources: [plan](https://developer.hashicorp.com/terraform/cli/commands/plan), [apply](https://developer.hashicorp.com/terraform/cli/commands/apply), [backend_local.go](https://github.com/hashicorp/terraform/blob/main/internal/backend/local/backend_local.go).

- **Mechanism.** "The plan command alone does not actually carry out the proposed changes." A plan without `-out` is "speculative". A saved plan, passed to `apply`, "performs the operations in the saved plan without prompting".
- **Staleness check (source).** Apply refuses with "Saved plan is stale: The given plan file can no longer be applied because the state was changed by another operation after the plan was created."
- **Approval.** By default, `apply` prompts for approval. `-auto-approve` carries a warning about drift.
- **[judgment]** Make an agent's edit to a unit's risk parts produce a plan that lists, before anything changes, the identity-table result (new version or new unit), whether the record survives, and which numbers move. He approves the plan. It is refused if the unit changed since the plan was made. The diff labels already exist (G8 3.6).

### 3.3 GitOps (OpenGitOps, Argo CD) — CHECKED

Sources: [OpenGitOps principles](https://opengitops.dev/), [Argo CD automated sync](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/).

- **Principles v1.0.0.**
  1. Desired state is "expressed declaratively".
  2. It is "Versioned and Immutable" with "a complete version history".
  3. It is "Pulled Automatically" by software agents.
  4. It is "Continuously Reconciled".
- **Argo CD safety defaults.**
  - An automated sync runs only when the app is OutOfSync, and only "one synchronization per unique combination of commit SHA1 and application parameters".
  - It "will not reattempt a sync if the previous sync attempt against the same commit-SHA and parameters had failed".
  - Self-heal is off by default.
  - "Rollback cannot be performed against an application with automated sync enabled."
- **[judgment]** Unit versions already live as immutable Library items (G8 3.8). Borrow "a failed deploy of a version is not retried until a new version exists" and "automation and manual rollback cannot both drive the same unit at once".

---

## 4. Progressive delivery with gates

### 4.1 Argo Rollouts — CHECKED

Source: [Analysis](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/).

- **Mechanism.** A rollout is a list of steps such as `setWeight: 20`, `pause: {duration: 5m}`, then `analysis`. "The success or failure of the analysis run decides if the rollout will proceed to the next step, or abort the rollout completely."
- **Template and instance.** An AnalysisTemplate defines metrics, how often to measure, and pass or fail conditions, and "may be parameterized". An AnalysisRun is one instance of it. A ClusterAnalysisTemplate is shared across namespaces.
- **Three outcomes.** Runs end "Successful, Failed, or Inconclusive", and the rollout continues, aborts or pauses "respectively". Inconclusive covers a value that meets neither condition. It exists "to automate the execution of analysis runs... but still allow human judgement".
- **Shadow metrics.** A metric "running in the dry-run mode won't impact the final state of the rollout... even if it fails".
- **Other settings.** `failureLimit` (for example 3), and background analysis over the whole rollout.
- **[judgment]** A new sizer, halt or template version could ramp as a canary on a small share of a unit's size or markets, with a template-level analysis. "Inconclusive, pause for his card" fits his rule that live promotion is his.

### 4.2 Flagger — CHECKED

Source: [Deployment strategies](https://docs.flagger.app/usage/deployment-strategies).

- **Settings.** `interval` (default 60 s), `threshold` ("max number of failed metric checks before rollback"), `maxWeight`, `stepWeight`, `stepWeightPromotion`, `skipAnalysis`.
- **Time is declared.** The minimum time to promote is `interval * (maxWeight / stepWeight)`. The time to roll back on failures is `interval * threshold`.
- **Gates.** It halts advancement while metrics fail, when pods are unhealthy, when a webhook fails, and "while canary deployment is being scaled up/down by HPA". On reaching the threshold, it routes "all traffic to primary" and scales the canary to zero.
- **[judgment]** Make every version ramp state its time to promote and time to roll back as plain numbers. Do not judge a version while another loop, such as the sizer's own motion, is changing it at the same time.

### 4.3 Kayenta (Spinnaker canary judge) — CHECKED

Sources: [How canary judgment works](https://spinnaker.io/docs/guides/user/canary/judge/), [Best practices](https://spinnaker.io/docs/guides/user/canary/best-practices/).

- **Compare against a fresh baseline.** "Compare canary against baseline, not against production." The baseline runs the current version with the "same time of deployment", "same size", and "same type and amount of traffic". This controls "for version and configuration only".
- **Judge.**
  - A Mann-Whitney U test per metric. "The judge needs to be 98% confident there's a real difference."
  - A tolerance band ("dead zone") around zero.
  - Labels: Pass, High, Low, Nodata.
  - Group scores are the share of passing metrics, combined by weight.
  - A `critical` metric failing sets the score to 0.
  - "If 50% or more of all metrics are classified as Nodata", the canary fails.
- **Thresholds.** Below "marginal", the canary "fails immediately". The final run must reach "pass".
- **Sample size.** At least "50 pieces of time series data per metric". A starting point is a 3-hour lifetime with a 1-hour interval.
- **[judgment]** Judge a new risk-template version against the old version running beside it, on the same markets at the same time (shadow or paper), not against the old version's past record. The built judge is size-blind (G8 5.3), so a size test would need money measures added.

### 4.4 Feature flags (OpenFeature specification) — CHECKED

Sources: [flag evaluation](https://github.com/open-feature/spec/blob/main/specification/sections/01-flag-evaluation.md), [types](https://github.com/open-feature/spec/blob/main/specification/types.md).

- **Mechanism.** Every evaluation call takes a "`default value` ... required". Calls "MUST NOT throw exceptions" and "must always return the `default value` in the event of abnormal execution".
- **Every value carries a reason.**
  - STATIC.
  - DEFAULT ("fell back to a pre-configured value").
  - TARGETING_MATCH.
  - SPLIT (pseudorandom assignment).
  - DISABLED.
  - STALE ("non-authoritative or possibly out of date").
  - ERROR.
- **[judgment]** Make every number a sizer uses resolve with a reason code: default, calibrated, inherited from the book, capped by the account, or stale data so default. That gives "every number has a default with a reason" a runtime form. The sizer receipt (hard-coded today, G8 1.4) is the natural place for it.

---

## 5. Resilience patterns

### 5.1 Circuit breaker with half-open (resilience4j; Hystrix retired) — CHECKED

Sources: [resilience4j CircuitBreaker](https://resilience4j.readme.io/docs/circuitbreaker), [Hystrix README](https://github.com/Netflix/Hystrix) ("no longer in active development, and is currently in maintenance mode").

- **States.** CLOSED, OPEN and HALF_OPEN, plus three special states: METRICS_ONLY, DISABLED and FORCED_OPEN.
- **Defaults.**
  - Sliding window of 100, count-based or time-based.
  - `minimumNumberOfCalls` 100 ("If only 9 calls have been recorded the CircuitBreaker will not transition to open even if all 9 calls have failed").
  - `failureRateThreshold` 50 %, `slowCallRateThreshold` 100 %.
  - `waitDurationInOpenState` 60 s.
  - `permittedNumberOfCallsInHalfOpenState` 10.
  - `maxWaitDurationInHalfOpenState` 0 (wait for all probes).
- **Half-open.** After the wait, it permits a set number of calls. If their failure or slow rate is at or above the threshold, it goes back to OPEN. Otherwise it goes to CLOSED.
- **Shadow state.** In METRICS_ONLY, events and metrics are recorded "similar to CLOSED state but... the circuit does not open when any of the thresholds are breached".
- **Defaults and overrides.** A registry holds a global default config. Named configs can be shared by many breakers, and any breaker can take its own.
- **[judgment]** This is a ready improvement path for the old circuit breaker he wants kept:
  - A minimum sample before judging, which answers the count-brake-versus-frequency finding (STATE item 10).
  - A half-open state that probes with a few small trades and judges them as a group.
  - METRICS_ONLY as a shadow halt that writes `would_have` journal rows (G8 5.2) before it may act.

### 5.2 Bulkhead (resilience4j) — CHECKED

Source: [Bulkhead](https://resilience4j.readme.io/docs/bulkhead).

- **Mechanism.** It limits concurrent executions with a semaphore or a fixed thread pool. Defaults: `maxConcurrentCalls` 25 and `maxWaitDuration` 0, so a call to a full bulkhead is refused at once.
- **[judgment]** Give each unit and market a compartment of open risk, so one unit cannot use the whole account's room. Today every unit sizes from the venue account's whole equity (G8 5.3).

### 5.3 Outlier ejection (Envoy) — CHECKED

Sources: [Outlier detection overview](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier), [API reference](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/v3/outlier_detection.proto).

- **Mechanism.** A host is ejected from load balancing when it is an outlier.
  - By count: 5 consecutive server errors by default.
  - By peer comparison: the threshold is "mean - (stdev * success_rate_stdev_factor)", with the factor at 1.9.
- **Sample rules.** A host counts only with 100 or more requests per interval. Detection is skipped if fewer than 5 hosts qualify.
- **Ejection time grows with repeats.** It is `base_ejection_time` (30 s) "multiplied by the number of times the host has been ejected in a row", capped by `max_ejection_time` (300 s). "When the host becomes healthy, the ejection time multiplier decreases with time." An ejected host "will automatically be brought back into service".
- **Caps on isolation.** `max_ejection_percent` defaults to 10 %, so no more than that share of a cluster is ejected at once.
- **Ramped enforcement.** `enforcing_*` is "the % chance that a host will be actually ejected... This setting can be used to disable ejection or to ramp it up slowly."
- **[judgment]** This is the closest existing shape for his market isolation protocol and for a book- or BMS-level breaker:
  - Compare a market or unit against its peers, with a minimum sample.
  - Cap the share that may be isolated at once.
  - Lengthen isolation with each repeat and shorten it with good behaviour.
  - Start enforcement at 0 % (shadow) and raise it.

### 5.4 Rate limiter with warm-up (Guava RateLimiter) — CHECKED (source)

Sources: [RateLimiter.java](https://github.com/google/guava/blob/master/guava/src/com/google/common/util/concurrent/RateLimiter.java), [SmoothRateLimiter.java](https://github.com/google/guava/blob/master/guava/src/com/google/common/util/concurrent/SmoothRateLimiter.java).

- **Mechanism.** It is a token bucket with a stable rate. The warm-up version "smoothly ramps up its rate, until it reaches its maximum rate at the end of the period". If left "unused for a duration of warmupPeriod, it will gradually return to its 'cold' state". The cold interval is 3 × the stable interval (`coldFactor` 3.0).
- **Why.** Past underuse can mean the server "has become less ready for future requests", for example because its caches went stale.
- **[judgment]** This is the same rule as TCP's restart window (2.1). A new version, or a unit back from a long quiet spell, starts below full size and ramps over a declared period.

### 5.5 Load shedding by priority (Google SRE book) — CHECKED

Source: [Handling Overload](https://sre.google/sre-book/handling-overload/).

- **Mechanism.** Every request carries one of four criticality values: CRITICAL_PLUS, CRITICAL, SHEDDABLE_PLUS or SHEDDABLE. Load is shed from the bottom first. "Four values were sufficiently robust to model almost every service." More values were turned down as too costly to run.
- **Adaptive throttling.** Clients throttle themselves from the ratio of requests sent to requests accepted, with a multiplier K. "We generally prefer the 2x multiplier." "Reducing the multiplier will make adaptive throttling behave more aggressively."
- **[judgment]** When a book or BMS budget tightens, shed by a declared priority (paper or probation units before proven ones) rather than cutting everyone pro rata. A few classes are enough.

### 5.6 Error budgets and burn-rate alerts (Google SRE workbook) — CHECKED

Sources: [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/), [Error Budget Policy](https://sre.google/workbook/error-budget-policy/).

- **Mechanism.** A budget is the loss allowed over a window. "Burn rate is how fast, relative to the SLO, the service consumes the error budget." A burn rate of 1 uses exactly the whole budget by the window's end.
- **Tiers (recommended).**
  - 2 % of the budget in 1 hour (burn 14.4): page.
  - 5 % in 6 hours (burn 6): page.
  - 10 % in 3 days (burn 1): ticket.
- **Two windows.** "A good guideline is to make the short window 1/12 the duration of the long window." The alert fires only while the budget is still being burned.
- **Policy.**
  - When the budget for the past four weeks is used up, "halt all changes and releases other than P0 issues or security fixes".
  - "If a single incident consumes more than 20% of error budget over four weeks", a postmortem is required.
- **[judgment]** This gives each level's drawdown budget a graded response: a fast burn means halt, a slow burn means size down, a ticket means review. "Budget used up, freeze version changes" fits units where every risk change is a new version.

---

## 6. Defaults with overrides and cascading config

### 6.1 CSS cascade — CHECKED

Source: [MDN, Introduction to the CSS cascade](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascade/Introduction).

- **Mechanism.** For normal declarations, precedence runs from low to high: user-agent, then user, then author (the page). So the most specific origin wins. For `!important` declarations the order reverses: author `!important`, then user `!important`, then user-agent `!important` on top. "The !important flag reverses the precedence of cascade layers."
- **[judgment]** One rule covers both of his needs. On normal values, the unit (the most specific level) wins. A limit that an outer level (account, BMS) marks as important wins the other way round, from the outermost level in.

### 6.2 VS Code settings scopes — CHECKED

Source: [User and workspace settings](https://code.visualstudio.com/docs/configure/settings).

- **Order.** "Later scopes override earlier scopes": Default, User, Remote, Workspace, Workspace Folder, then the language-specific versions of each. Last, "Policy settings - Set by the system administrator, these values always override other setting values."
- **Merge rule.** Primitive and array values are overridden. "Values with Object types are merged."
- **Scope restrictions.** "Application-wide settings related to updates and security can not be overridden by Workspace settings."
- **[judgment]** Each risk number could declare which levels may set it, with one policy level above all of them: the account, which is his. The mini-app analogy he already accepts carries over to settings.

### 6.3 Helm values — CHECKED

Sources: [Values Files](https://helm.sh/docs/chart_template_guide/values_files/), [Charts](https://helm.sh/docs/topics/charts/), [helm rollback](https://helm.sh/docs/helm/helm_rollback/).

- **Precedence.** "values.yaml is the default, which can be overridden by a parent chart's values.yaml, which can in turn be overridden by a user-supplied values file, which can in turn be overridden by --set parameters."
- **Removing a default.** Set the key to `null`.
- **Shared values.** `global` values reach every subchart.
- **Validation.** `values.schema.json` is validated on `helm install`, `helm upgrade`, `helm lint` and `helm template`.
- **Versions.** A chart has a required `version`. "This command rolls back a release to a previous revision"; `helm history` lists revisions.
- **[judgment]** A per-type risk template (scalper, ORB) has the same parts as a chart: a defaults file, a schema checked on every change, a parent (book) layer, user overrides, and numbered revisions to roll back to. `unit_new(template, overrides)` is already the "install with -f" step (G8 4.1).

### 6.4 systemd drop-ins — CHECKED

Source: [systemd.unit(5)](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html).

- **Mechanism.** Drop-in `.conf` files "take precedence over unit files wherever located". "Multiple drop-in files with different names are applied in lexicographic order." `/etc` beats `/run`, which beats `/usr/lib`.
- **Type-wide drop-ins.** A `type.d/` folder (for example `service.d/`) alters "all corresponding unit files", with "lower precedence compared to files in name-specific override directories".
- **Templates.** A unit "may be instantiated from a template file". Assigning an empty string to a list option resets it.
- **[judgment]** A methodology- or book-wide drop-in could apply to every unit of a type, beaten by a unit's own drop-in. An explicit "reset" covers lists such as halts.

### 6.5 Nix modules — CHECKED (manual source)

Sources: NixOS manual sources [option-def](https://github.com/NixOS/nixpkgs/blob/master/nixos/doc/manual/development/option-def.section.md), [option-declarations](https://github.com/NixOS/nixpkgs/blob/master/nixos/doc/manual/development/option-declarations.section.md), [assertions](https://github.com/NixOS/nixpkgs/blob/master/nixos/doc/manual/development/assertions.section.md), [rollback](https://github.com/NixOS/nixpkgs/blob/master/nixos/doc/manual/administration/rollback.section.md).

- **Mechanism.** An option is declared with a name, type and description, and usually a default. Many modules may define the same option. Definitions merge according to the type.
- **Priorities.** "All option definitions that do not have the lowest priority value are discarded":
  - Option defaults: 1500.
  - `mkDefault`: 1000.
  - A plain definition: 100.
  - `mkForce`: 50.
- **Checks.** Modules declare `assertions` and `warnings`, which give "clear feedback to the user and prevents errors after the build".
- **Versions.** Every rebuild is a numbered system generation. `nixos-rebuild switch --rollback` switches to the previous one. The boot menu lists "All configurations".
- **[judgment]** Numbered priorities make "who wins" readable and checkable across five levels. Assertions are layer E (G8 3.3). Generations are unit versions you can switch back to.

### 6.6 ESLint flat config — CHECKED (docs source)

Source: [configuration-files.md](https://github.com/eslint/eslint/blob/main/docs/src/use/configure/configuration-files.md).

- **Mechanism.** Configuration objects "are merged with later objects overriding previous objects".
- **Locking.** `noInlineConfig: true` makes "all inline configuration... ignored". `--inspect-config` shows "which config objects apply to a specific file".
- **[judgment]** Borrow a switch that stops lower levels from overriding a value, and an inspector that answers "where did this number come from".

---

## 7. Plug-in and composition models

### 7.1 Entity-component systems (Bevy) — CHECKED

Sources: [Bevy ECS quick start](https://bevy.org/learn/quick-start/getting-started/ecs/), [Component trait docs](https://docs.rs/bevy/latest/bevy/ecs/component/trait.Component.html).

- **Mechanism.** "Entities are unique 'things' that are assigned groups of Components, which are then processed using Systems." "Systems are logic that runs on a specific set of component types."
- **Required Components.** "If some Component A requires Component B, then when A is inserted, B will also be initialized and inserted (if it was not manually specified)", using its default.
- **[judgment]** A unit is the entity, and risk pieces are components. The host runs one "halt system" for every unit that carries a halt. Adding a halt could pull in the statistics it reads, with defaults. Today no host computes those statistics or runs halts (G8 2.1, 3.5).

### 7.2 Home Assistant blueprints (a warning) — CHECKED

Sources: [Blueprint schema](https://www.home-assistant.io/docs/blueprint/schema/), [Using blueprints](https://www.home-assistant.io/docs/automation/using_blueprints/).

- **Mechanism.** A blueprint declares `input` fields, each with a name, a description, a `selector` (which builds the UI field) and a `default`. An automation uses the blueprint with its own input values. `min_version` names the oldest Home Assistant release it runs on.
- **Versions: none.**
  - Re-importing "overwrites the blueprint you currently have". "If the re-imported blueprint is not compatible, it can break your automations."
  - "Take control" turns one automation into a plain one. "You can't convert the automation back."
- **[judgment]** This is the negative example. A template update must not silently change running units. A fork from a template is fine, but it is one way and should be recorded as lineage.

### 7.3 Simulink library blocks and forwarding tables — CHECKED

Sources: [Linked Blocks](https://www.mathworks.com/help/simulink/ug/creating-and-working-with-linked-blocks.html), [Forwarding Tables](https://www.mathworks.com/help/simulink/ug/make-backward-compatible-changes-to-libraries.html).

- **Mechanism.** A block placed from a library is a "linked block". The link "allows the linked block to update when the library block is updated". Only changed parameters are saved in the model, as "linked data".
- **Link states.** Links can be locked, disabled (temporary), restored, or broken (permanent).
- **Versions.** A forwarding table maps "Old Block Path", "Old Block Version", "New Block Path" and "New Block Version", plus a "Transformation Function" that maps old parameters to new ones. Simulink applies it when a model opens or a block is added or replaced. Per the search summary (SNIPPET), broken or disabled links cannot be updated through it.
- **[judgment]** A forwarding entry plus a parameter map is a declared migration, for example from `fixed-fraction-at-stop@1` (placeholder) to a real sizer. The identity table could then treat it as a new version that keeps the record, not a new unit (G8 3.6, judgment). The upgrader chains for stored shapes (G8 3.7) are the same idea, one level down.

### 7.4 PLC function blocks and a self-tuning PID (Siemens PID_Compact) — CHECKED in part

Source: [PID_Compact V2 output value](https://docs.tia.siemens.cloud/r/en-us/v20/using-pid_compact-s7-1200-s7-1500/pid_compact-as-of-v2-s7-1200-s7-1500/configuring-pid_compact-as-of-v2-s7-1200-s7-1500/advanced-settings-as-of-v2-s7-1200-s7-1500/output-value-as-of-v2-s7-1200-s7-1500) (Siemens TIA docs, V20).

- **Mechanism.** A controller block that can tune its own parameters ("pretuning", "fine tuning") and then run in automatic mode.
- **Hard limits.** "Absolute output value limits are not violated in neither manual mode nor automatic mode. If an output value outside the limits is specified in manual mode, the effective value is limited."
- **Failed tuning.** "When any other error occurs, PID_Compact cancels the tuning and switches to the mode from which tuning was started."
- **Error reaction.** The user chooses the reaction to an error: zero (inactive), the current value, or a substitute value. Siemens warns the last two keep the block in automatic mode, "may cause a violation of the process value limits and damage your system".
- **SNIPPET only.**
  - The mode list (Inactive, Pretune, Fine tuning, Automatic, Manual, Substitute output value with error monitoring) comes from a Siemens forum post.
  - A `LoadBackUp` flag reloads the last parameter set, per a Siemens Openness PDF seen in search results.
  - IEC 61131-3 function-block types and instances were not read this run.
- **[judgment]**
  - Self-tuning is a mode the block enters and leaves. A failed tune returns to the previous mode and values.
  - Hard output limits clamp even manual input, so his manual override cannot pass an account cap either.

---

## 8. Self-adaptive systems research

### 8.1 MAPE-K (Kephart and Chess, "The Vision of Autonomic Computing", IEEE Computer 2003) — CHECKED

Source: [PDF copy](https://jmvidal.cse.sc.edu/library/kephart03a.pdf).

- **Mechanism.** An autonomic element is "one or more managed elements coupled with a single autonomic manager". The manager monitors, analyses, plans and executes over shared knowledge (the paper's Figure 2). Systems "manage themselves given high-level objectives from administrators".
- **Self-optimization.** Systems "will monitor, experiment with, and tune their own parameters".
- **Authority.** Elements act "in accordance with policies that humans or other elements have established".
- **Warnings.**
  - Autonomic systems "will also greatly magnify the consequences of any error humans do make in specifying goals".
  - "Ensure that goals are specified correctly in the first place, and ensure that systems behave reasonably even when they are not."
  - Emergent behaviour across many elements is an open problem. The authors point to "distributed or hierarchical control theories".
- **[judgment]** The vocabulary fits QMX levels. Each level (unit, book, BMS, account) is a manager over the one below. The warning argues for keeping his inputs few, explicit, range-checked and visible.

### 8.2 Simplex architecture — CHECKED (secondary paper)

Source: Jäger et al., ["Towards Safe Path Tracking Using the Simplex Architecture"](https://arxiv.org/abs/2503.10559), section III, describing Sha's 2001 architecture. Sha's own paper was not found; per the search summary (SNIPPET) it is "Using Simplicity to Control Complexity".

- **Mechanism.** It has three parts:
  - A high-performance controller that "may be complex and adaptive, and is not required to provide guarantees".
  - A high-assurance controller "designed to stabilize the system and guarantee safety".
  - A decision module.
- **Switching.** The module switches to the safe controller when the one-step predicted state would leave the safe region. It switches back only after a dwell time, "to avoid oscillations between controllers".
- **[judgment]** A tuned sizer would run only while projected open risk and drawdown stay inside a region where the fixed, simple sizer can still recover. Past that line, the fixed sizer takes over for a declared dwell time. This is "safe when it tunes itself" with a named fallback.

### 8.3 Rainbow and Stitch (architecture-based self-adaptation) — CHECKED (secondary)

Source: Vogel and Giese, ["Requirements and Assessment of Languages and Frameworks for Adaptation Models"](https://arxiv.org/abs/1805.08679), section 6. The Stitch paper itself (Cheng and Garlan, JSS 2012) was not read.

- **Mechanism.** Stitch captures adaptation "as explicit adaptation strategies consisting of condition-action pairs". It has three levels: operators (system commands), tactics (one adaptation step) and strategies (which orchestrate tactics). The action is chosen "based on utility preferences", and each step carries cost and benefit attributes.
- **Weakness noted.** Stitch checks consistency "only... by observing intermediate effects... but not beforehand at the model level".
- **[judgment]** Brakes as tactics (cut half, pause new entries, flatten), arranged into strategies with conditions and declared costs, are a known shape for graded brakes (N8).

### 8.4 Models at runtime — SNIPPET

- **What was seen.** Only workshop records and a survey's keywords ("Causal connection, Self-reflection"). The 2009 IEEE Computer article was not found.
- **[judgment]** The unit document plus its journal already works as a runtime model. Nothing new to borrow beyond 3.1.

---

## 9. Trading platforms beyond R1

### 9.1 MT5 EA inputs and the optimiser — CHECKED

Sources: [Input Variables](https://www.mql5.com/en/docs/basis/variables/inputvariables), [Strategy Testing](https://www.metatrader5.com/en/terminal/help/algotrading/testing).

- **Inputs are read-only to the program.** "A variable with the input modifier can't be changed inside mql5-programs." Values "can be changed only by a user from the program properties window".
- **Excluding inputs from optimisation.** `sinput` marks an input as excluded: "Start, Step and Stop fields are not available for such a variable."
- **Forward testing.** It re-runs on "the second (latest) part of the total period" (1/2, 1/3, 1/4 or custom) "to avoid parameters fitting".
- **[judgment]** Keep his inputs read-only to the unit, with tuned values held as separate working state. That is MT5's rule, and also Kubernetes' spec/status split (3.1). `sinput` is the "never moves" mark.

### 9.2 TradingView strategy settings — CHECKED

Source: [Pine Script, Strategies](https://www.tradingview.com/pine-script-docs/concepts/strategies/).

- **Defaults and overrides.** `default_qty_type` and `default_qty_value` in `strategy()` are defaults that "script users can adjust... via the 'Default order size' inputs in the 'Settings/Properties' tab". A `qty` on an entry call overrides them.
- **Risk commands.**
  - `strategy.risk.allow_entry_in`.
  - `max_cons_loss_days`.
  - `max_drawdown`.
  - `max_intraday_filled_orders`.
  - `max_intraday_loss`.
  - `max_position_size`.
- **Always on.** They "execute on every tick and order execution event". "There is no way to deactivate any of these commands on specific script executions."
- **All cliffs.** Each one cancels, closes and stops.
- **[judgment]** Borrow "declared with the strategy, always on, not bypassable per call". The graded responses have to come from elsewhere (sections 2 and 5).

### 9.3 cTrader cBot parameters — SNIPPET

- **What was seen.** Per the search summary of cTrader help, `[Parameter]` takes `DefaultValue`, `MinValue`, `MaxValue`, `Step` and `Group`. This is the same schema-next-to-code pattern R1 found in StrategyQuant and the MT5 Wizard. Nothing new.

---

## 10. How each system fits the eight needs (INFERRED)

S = strong match, P = partial, – = not addressed.

| System | N1 defaults with reasons | N2 tunes from evidence | N3 safe tuning | N4 levels | N5 extensible | N6 versions | N7 runs alone | N8 graded brakes |
|---|---|---|---|---|---|---|---|---|
| TCP | P | S | S | – | – | – | S | S |
| Netflix AIMD limit | P | S | S | P (shares) | P | – | S | P |
| dash.js ABR | P | S | P | – | S | – | S | P |
| Kubernetes HPA | S | S | S | – | P | – | P | S |
| **Kubernetes VPA** | S | **S** | **S** | P | P | – | P | P |
| OtterTune | P | S | S | – | – | P | – | – |
| HotSpot JIT | P | S | S | – | – | – | S | S |
| **K8s controllers, spec/status** | S | P | S | S | **S** | P | P | – |
| Terraform plan | – | – | S | – | P | S | – | – |
| GitOps / Argo CD | P | – | S | – | P | S | P | – |
| **Argo Rollouts + Kayenta** | P | P | S | – | P | **S** | – | P |
| OpenFeature | **S** | – | S | P | P | – | S | – |
| resilience4j CB | S | P | S | – | P | – | S | S |
| Envoy outlier | S | S | S | S | – | – | S | S |
| SRE budgets | P | P | S | P | – | P | – | S |
| CSS / VS Code / Nix / Helm | S | – | P | **S** | S | P (Nix, Helm) | – | – |
| Bevy ECS | P | – | – | – | S | – | S | – |
| Home Assistant blueprints | S | – | – | – | S | – (warning) | – | – |
| Simulink forwarding | P | – | – | – | S | **S** | – | – |
| PID_Compact | P | S | S | – | – | P | S | P |
| Simplex | – | P | **S** | – | – | – | S | S |
| MT5 inputs / TradingView | P | – | P | – | – | – | S | – |

---

## 11. The closest match

**1. The Kubernetes controller model, with the Vertical Pod Autoscaler as its self-tuning part.**

VS Code fits mini apps because it is a host where anyone ships a packaged extension against declared contribution points. Kubernetes fits a self-configuring unit for the same kind of reason. It is a host where every object is a typed document with defaults, and small control loops keep each object's numbers right from evidence, inside limits a person owns. The VPA is the one piece that does exactly what his unit must do with its numbers.

- **Typed object with defaults (N1).** The spec has a schema. "Only values which need to be customized can be specified. These custom values are merged with default values" (HPA). The QMX unit document is already this kind of object (G8 1.1).
- **A learner, separate from an applier (N2).** The VPA recommender learns from that object's own decayed history and gives a target with low and high bounds. The updater applies it, and the admission controller sets it at creation. QMX's motion engine is a learner with no separate applier. That is why `authority` and `applies_to_open_positions` are parsed and ignored (G8 3.10).
- **The owner's bounds and authority as plain fields (N3).** `minAllowed`/`maxAllowed`, `mode: Off` per field, and `updateMode` Off/Initial/Recreate/InPlace. Separate write rights: people write the spec, controllers write the status.
- **Small loops per level (N4, N5).** "Simple controllers rather than one, monolithic set of control loops", each owning one aspect and allowed to fail. Anyone can add a new object type with its own controller (the operator pattern). The HPA's `behavior` block (per-direction windows, rate caps, tolerance, cautious missing data) supplies the "size down slowly" settings.
- **Where it falls short.** It has no idea of a record that a version change could cost (N6), and it assumes a cluster, not a lone node (N7). The second match covers N6. The patterns in section 12 cover the rest.

**2. Argo Rollouts with Kayenta-style analysis, for versions (N6).**

His rule that a new sizer or a new halt is a new version or a new unit (G8 3.6) is exactly what progressive delivery handles:

- the new version takes a small, declared share first;
- a reusable, parameterized analysis template judges it;
- the comparison is against a fresh baseline of the old version running at the same time;
- the run ends as pass (go on), fail (roll back) or inconclusive (pause for a human);
- dry-run metrics let a new check run in shadow.

This turns "the rip-out costs each unit its record" into "the new version earns its own record beside the old one, then takes over".

## 12. Patterns to combine

Each pattern names its source system and the existing QMX seam it would attach to. These are borrowings, not a design.

1. **Spec and status with separate write rights** (Kubernetes 3.1, MT5 9.1). His and agents' choices go in the unit document. Tuned values and brake states go in status, written only by the runtime and stamped with the version. Seam: unit document plus snapshot (G8 1.1, 3.7).
2. **A recommender with bounds and an authority mode per number** (VPA 2.5). A target with low and high bounds from the unit's decayed record, clamped by his range, applied as Off (shadow), at-flat, or live. Seam: `NumberSpec.motion`, `range` and `authority` (G8 1.1, 3.10).
3. **Asymmetric, rate-capped motion with a stabilization window** (HPA 2.4, TCP 2.1, AIMD 2.2). Cut by signal severity. Grow only on evidence gathered at the current size. Take the cautious value over a window before moving the other way. Treat missing data as "no change". Seam: motion rule blocks (G8 3.9).
4. **Warm-up and restart-after-idle** (Guava 5.4, TCP 2.1, HPA 2.4). New versions and long-idle units start small and ramp over a declared period. Their first trades are ignored for growth.
5. **A guarded guess with a fallback and a trip counter** (HotSpot 2.7, Simplex 8.2, PID_Compact 7.4). A failed guard reverts the number to its default. Too many trips freeze it. Leaving the safe region hands sizing to the fixed sizer for a dwell time.
6. **Many opinions, smallest cap wins, each with a reason** (dash.js 2.3, OpenFeature 4.4). Sizing modifiers and caps each propose a cap. A priority order (halt above modifier) decides ties. Every resolved number carries a reason code into the receipt. Seam: `sizing_modifier` role and the sizer receipt (G8 1.1, 1.4).
7. **A cascade with a reversed "important" rule and a policy top** (CSS 6.1, VS Code 6.2, Nix 6.5, ESLint 6.6). Most specific wins for normal values. Outer-level limits marked important win from outside in. Each number declares which levels may set it. An inspector shows where each value came from.
8. **Graded, sample-aware, shadow-first brakes** (resilience4j 5.1, Envoy 5.3, SRE 5.6). A minimum sample before judging. Half-open probes at reduced size. A METRICS_ONLY or dry-run state that writes `would_have` rows. Peer comparison for isolation, with a cap on the share isolated and ejection times that grow and decay. Burn-rate tiers per level's budget. Seam: halt slot, journal `would_have` and `guard` kinds (G8 2.1, 5.2).
9. **Compartments and priority shedding** (bulkhead 5.2, AIMD shares 2.2, SRE 5.5). Each unit gets its own share of open risk. When a budget tightens, shed by declared class. Seam: the cross-unit hook (G8 2.1).
10. **Templates with schema, layers and numbered revisions** (Helm 6.3, systemd 6.4, Nix 6.5). Per-type risk templates as defaults plus a schema plus layer drop-ins, with revision numbers to roll back to. Never the Home Assistant overwrite (7.2). Seam: `unit_new(template, overrides)` (G8 4.1).
11. **A plan before any change, refused if stale** (Terraform 3.2, GitOps 3.3). Agent edits produce a plan with the identity-table result and record impact, and he approves it. A failed deploy of a version is not retried. Seam: identity diff (G8 3.6), agent rows (G8 4.1).
12. **Canary versions with a fresh baseline and three outcomes** (Argo Rollouts 4.1, Flagger 4.2, Kayenta 4.3). Declared time to promote and roll back. Judge only while no other loop is moving the version. Seam: paper scoring and the judge, which needs money measures added (G8 5.2, 5.3).
13. **A migration map between block versions** (Simulink 7.3). A forwarding entry plus a parameter map lets a placeholder-to-real swap be a version that keeps the record. Seam: identity table and upgrader chains (G8 3.6, 3.7).
14. **A deny-list and borrowed priors** (OtterTune 2.6). Numbers that may never self-tune are an explicit list he owns. An empty record borrows a prior from the most similar past units, and tuned values are tried on a shadow copy first.
15. **Required components** (Bevy 7.1). Adding a halt or modifier brings the statistics it reads, with defaults, so the host can run it for every unit that has it. Seam: halts' unread statistics (G8 2.4, 3.5).

## 13. Limits of this pass

- Read only. No code was run apart from text extraction. Nothing was committed.
- **Not read:**
  - Sha's original Simplex paper, the IBM autonomic blueprint (its link returned 404), the Stitch paper and the models@run.time article. Secondary sources were used and are marked.
  - The BOLA paper (only dash.js's rule aggregation was read).
  - Linux TCP variants such as CUBIC.
  - LaunchDarkly or other commercial flag tools.
  - Google's Autopilot paper.
  - The IEC 61131-3 standard.
  - The Prettier docs (the brief named Prettier with ESLint).
- **SNIPPET-grade claims:** PID_Compact's mode list and `LoadBackUp`; cTrader's `[Parameter]` fields; Simulink's limit on broken links; the title of Sha's paper.
- Line-level source references (HotSpot, Guava, Netflix, Terraform) are from the default branches on 3 Nov 2026 and will drift.
