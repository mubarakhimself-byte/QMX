# BDD reconciliation — 85 frozen IDs vs UX-01..UX-12

Research only. Not architecture. Not ratification. No IDs minted. No Gherkin edited.

Sitting: `architecture-QMX-UI-2026-09-23`.  
Inspected 2026-09-23 from `main@92279dfe` (docs workspace) and `.worktrees/integration-inspect` at `integration@34c148be`.

## Verdict in one page

The original **85** challenge IDs still exist, still match the catalog 1:1, and the Pass-I freeze hash still matches. They are **backend oracles**, not UI journeys. Catalog field `future_ui_journey` is a stub on every row. None of the 85 is executable Gherkin and none has a passing run.

UX-01..UX-12 mostly **map** onto those oracles (session isolation, headless discovery, placement, cancel/unknown, data provenance, Book/BMS). The chrome, first-run, graph→code→return, composer references, Library screen, and settings/preview surfaces are **missing**.

SCN-0023..SCN-0027 are pack-and-grant kit law (J-KIT-01..07). They help Home instance-pick, optional copilot, nested Mission, retry, and diagnosis. They do not replace a UI catalog. They are **untracked on main** and **absent from integration-inspect**.

Section 7 of `03-EXPERIENCE-SCOPE.md` still needs **twelve new mixed/UI/headless journeys**. Suggested sitting IDs: `J-UI-01`..`J-UI-12`. Do not reuse the 85 `P1-*`/`P2-*` IDs. Do not reuse `SCN-0001`..`SCN-0027`.

Headline conflict: a **universal paper-trading gate** (week-or-two soak as a product requirement for every capability) is refused by current direction and by UX-10. Paper-then-live + L17 remains law for **trading compositions that take a seat**, not for headless utilities or non-trading ML.

---

## 1. Count of the original 85 IDs — freeze confirmed

### 1.1 Frozen Pass-I baseline

| Item | Value |
|---|---|
| File | `workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/bdd/context/INDEPENDENT-SCENARIO-BASELINE.md` |
| Canonical source | `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/codex-challenge-20260919/INDEPENDENT-SCENARIO-BASELINE.md` |
| SHA-256 | `1c2c865d1cef50076682a737472174fa307cf1fc8eb3663b122ed04ab6f39fd8` |
| Handoff pin | Same SHA in `GROK-RECONCILIATION-HANDOFF.md` and `TEST-AND-MUTATION-PLAN.md` |
| Packet `source-map.json` | Same SHA |
| This inspect | SHA-256 recomputed; **exact match** (Windows hash is uppercase; hex is case-insensitive) |

Pass I froze **65** `P1-*` rows in §6 of that file **before** the candidate was read. Do not rewrite those rows as if they came from later architecture.

### 1.2 Catalog

| Item | Value |
|---|---|
| File | `…/evidence/bdd/context/SCENARIO-CATALOG.jsonl` |
| SHA-256 | `8a8e709c2a0788b25943ef86bddf6ab92e8015b317af2fe049ca5297d34ccbe9` |
| Lines | **86** = 1 schema record + **85** scenario objects |
| Unique `id` | **85** |
| Duplicates | none |
| Pass I (`phase_origin=pass1`) | **65** |
| Pass II (`phase_origin=pass2-added`) | **20** |

Sample object shape (every data line): `id`, `phase_origin`, `user_goal`, `source`, `preconditions[]`, `stimulus`, `expected_observable`, `forbidden_effects[]`, `oracle_evidence[]`, `contracts_owners[]`, `failure_recovery`, `future_ui_journey`, `evidence_status`.

`evidence_status` on the frozen rows is `baseline-specified; execution pending`.  
`future_ui_journey` on those rows is the same boilerplate: *“Configure fixture, run stimulus, inspect timeline, artifacts, errors and provenance.”* That field is **not** UX coverage.

### 1.3 Feature files = catalog

All five files carry `@draft @specification_only`. Packet bytes match `source-map.json`.

| File | Declarations | SHA-256 |
|---|---|---|
| `capabilities-and-operations.feature` | 9 (incl. 1 `Scenario Outline`) | `d77d46ac237b03a81e1c18cb412636e606810ec304f7fb020dfb3c88fc6a9c50` |
| `catalog-completion.feature` | 49 | `bd6bff4bbcf7e183e93c0e0310c55d56425485d39b24d2621ba2daef6a310271` |
| `data-streams-and-market.feature` | 11 | `b1287615254e8df067af634f1fa0eba20a82ae54a537e433c3e26f24189c11ac` |
| `placement-and-recovery.feature` | 6 | `cd60e0032fb478ce7b4e5c306ee3ba238dd894524bcf144f8e2f20cad0e163f4` |
| `workflows-and-sessions.feature` | 10 | `685b24f3049c356c0bb44bc2d986157b46992d5cda0365b6ad23d5b95e5b0a0b` |
| **Total unique IDs** | **85** | — |

`P1-OP-004` is a `Scenario Outline` with **four** example rows (`queued` / `running` / `non-cancelable` / `complete`). An eventual runner would expand that to **88 parameterized cases**. That does **not** change the **85 catalog IDs**.

Catalog IDs not in features: **none**. Feature IDs not in catalog: **none**.

### 1.4 Family counts (the 85)

| Family | P1 | P2 | Total |
|---|---:|---:|---:|
| CAP | 6 | 3 | 9 |
| OP | 5 | 3 | 8 |
| WF | 7 | 2 | 9 |
| SES | 6 | 5 | 11 |
| DATA | 8 | 3 | 11 |
| STR | 5 | 1 | 6 |
| MKT | 10 | 1 | 11 |
| PLC | 6 | 1 | 7 |
| APP | 8 | 0 | 8 |
| SKL | 4 | 0 | 4 |
| INT | 0 | 1 | 1 |
| **Sum** | **65** | **20** | **85** |

Pass-I index (do not renumber):  
`P1-CAP-001..006`, `P1-OP-001..005`, `P1-WF-001..007`, `P1-SES-001..006`, `P1-DATA-001..008`, `P1-STR-001..005`, `P1-MKT-001..010`, `P1-PLC-001..006`, `P1-APP-001..008`, `P1-SKL-001..004`.

Pass-II index:  
`P2-CAP-007..009`, `P2-OP-006..008`, `P2-WF-008..009`, `P2-SES-007..011`, `P2-DATA-009..011`, `P2-STR-006`, `P2-MKT-011`, `P2-PLC-007`, `P2-INT-001`.

Near-duplicate inside the 85 (inventory C-008 / `bdd-inventory.md`): **`P2-SES-008` and `P2-SES-011`** share the reconnect-does-not-imply-approval oracle. **Retain both catalog rows.** Do not treat them as two UX patterns.

### 1.5 Three ID systems — do not collapse them

| Namespace | What it is | Count / range here | Execution claim |
|---|---|---|---|
| `P1-*` / `P2-*` | Stage-B challenge-local IDs | 85 frozen | specification only |
| `SCN-NNNN` | Canonical `docs/scenarios/` | committed `SCN-0001`..`0022` on main; untracked `SCN-0023`..`0027` | specification of intended behavior |
| `Jnn` / `J-KIT-nn` / (proposed) `J-UI-nn` | Architecture-sitting journeys | workflows J01–J27; kit J-KIT-01..07 | prose traces, not tests |

The 85 are **not** `SCN` ids. Mapping a UX area onto `P1-SES-002` does not create `SCN-0028`.

---

## 2. Map UX-01..UX-12 → existing scenario IDs

Legend used in the **Status** column:

- **retain** — keep the existing ID as a binding oracle; do not rewrite it; it already states the invariant the UX must honour.
- **map** — the ID is a related backend/session constraint; the UX still needs a visible/headless journey with a **new** ID.
- **conflict** — existing law or current direction contradicts a naive reading of the UX row.
- **missing** — no existing ID covers the observable (usually chrome, first-run, or graph↔code).

Every UX row also inherits the state checklist in `03` §2: loading / empty / unavailable / failed / recovery, plus focus/keyboard. That checklist is **not** twelve dashboards.

### UX-01 — Launch, first run and reconnect

| Status | IDs | What they actually cover |
|---|---|---|
| map | `P1-SES-002`, `P2-SES-008`, `P2-SES-011` | Tab/window close → session restore; reconnect ≠ approval |
| map | `P1-PLC-004`, `P2-STR-006` | Server-owned job continues when UI closes; disposing a tab does not cancel a durable consumer |
| map | `P1-PLC-001`, `P2-SES-007` | Preflight missing GPU/entitlement; stale/revoked credential refused |
| map | `SCN-0024` Then (3) | Future UI tab/panel dispose does not cancel work |
| missing | — | Splash/status, first usable window, local/remote discovery, provider/API-key or CLI-proxy setup, partial readiness, missing-dependency retry, **do not block all work behind one unavailable provider** |

Reconnect of an existing session is specified. **First-run and provider onboarding are not.**

### UX-02 — Home and platform navigation

| Status | IDs | What they actually cover |
|---|---|---|
| map | `SCN-0023`, J-KIT-03 | Home/main copilot is authoring with `app_instance_id` absent until invoke; exactly one `selected_refs` kind `instance_id`; no third `ProductSessionProfile` |
| map | `P1-SES-001` | Concurrent workflow / strategy / ML sessions stay isolated |
| map | `P1-PLC-004` | Close view ≠ stop durable work |
| conflict | `SCN-0023` Branch A | Modelling Home as a new session profile is forbidden |
| missing | — | Running/attention items independent of opened apps; opened-app rail; Home vs worker health; multiple-instance chrome; resume-the-right-instance **as a screen** |

`SCN-0023` is session-identity law, not Home chrome.

### UX-03 — Main copilot and composer

| Status | IDs | What they actually cover |
|---|---|---|
| retain | `P1-SES-001`, `P1-SES-005` | Concurrent sessions do not leak; history citation does not retarget a command |
| retain | `P1-SES-003`, `SCN-0019`, `SCN-0024` Then (2) | App-use mints `change_request`; does not apply; v1 stays |
| retain | `P1-SES-004` | Nested component cannot union authoring/trading grants |
| retain | `P1-SES-006` | Specialist identity remains behind one copilot surface |
| map | `P1-SES-002`, `P2-SES-007`..`011`, `SCN-0023` | Reconnect, stale target/credential, grants across refresh, exactly-one instance on invoke |
| missing | — | Compact composer (not the rejected picker); file vs existing-path vs dataset vs app vs widget chips; context inspect/remove; keyboard; concurrent streamed jobs; result links; conversation navigation; tabbed preview; “what will this conversation use?” provenance |

`03` §4 is new product semantics. The 85 specify **session/grant isolation**, not attachment chips.

### UX-04 — App workspace and widget expansion

| Status | IDs | What they actually cover |
|---|---|---|
| map | `P1-APP-001`..`008` | Cross-app artifact/op, partial composite failure, shared vs independent provider, missing component, identity≠label, parameter cycle |
| map | `P1-WF-005` | Layout/display-name change does not invalidate semantics |
| map | `P2-STR-006` | UI dispose ≠ cancel shared stream |
| map | `SCN-0025` Then (1), J-KIT-04 | Widget may bind `start` of a template; widget dispose does not cancel the Mission |
| missing | — | App-owned nav; widget density; optional right copilot; scoped settings; add/edit widgets; compact/detail; **Open/Expand and return with retained viewport**; shared filters without cross-app leakage |

### UX-05 — Library

| Status | IDs | What they actually cover |
|---|---|---|
| map | `P1-CAP-001`..`006`, `P2-CAP-007`..`009` | Headless discover, atomic refuse, migration, grants unchanged, dependants, secret-free export, index rebuild, pinned in-flight, unavailable dep |
| map | `SCN-0018`, `SCN-0022` | Pin → disable = tombstone, never another version; atomic roster; export scanner oracle |
| map | `P1-APP-001`, `P1-DATA-008` | Cross-app artifact; non-trading artifact catalogued without Book/BMS |
| conflict | UX-05 last sentence | “Library navigation is not a new universal backend object type.” Do not mint a Library store to satisfy the screen |
| missing | — | Search/filter/preview UI; open/use/reference/save/fork; lineage as a screen; unavailable/stale/deleted; upgrade/rollback chrome; import/export screens |

Catalog/package identity is specified. A **Library screen** is not.

### UX-06 — App composition and extension authoring

| Status | IDs | What they actually cover |
|---|---|---|
| retain | `P1-SES-003`, `SCN-0019`, `SCN-0024` | Install ≠ grant; app-use cannot apply; `copilot_profile` optional |
| map | `P1-APP-*`, `P1-CAP-*`, `P1-SKL-001`..`003` | Composite pins, missing component, skill activate while old run pinned |
| map | `P1-WF-001`, `P1-WF-002` | Storyboard vs selected runnable subgraph; semantic mismatch refused |
| missing | — | Build views/widgets; draft vs installed preview; component/resource picker; validation/diff/review chrome; optional packaging; version compatibility UI; installation vs permission-grant as distinct operator acts |

### UX-07 — Workflow/ML graph and code

| Status | IDs | What they actually cover |
|---|---|---|
| map | `P1-WF-001`..`007`, `P2-WF-008`..`009` | Selected subgraph, semantic ports, joins, bounded cycle, layout-only, version pin, schedule dedupe, partial outputs, checkpoint resume |
| map | `SCN-0025`, J-KIT-05 | Nested Mission = own JobHandle; live Task Graph merge refused |
| map | `P1-PLC-001`, `P1-DATA-007` | Placement preflight; incomplete GPU weights not promotable |
| missing | — | Visual graph editor; **open a code node and return to the retained graph** (viewport, selection, version); node inspect vs Open/Expand; code/diff surface; run-from-boundary chrome; run history as a surface |

This is the largest chrome hole. Inventory already said: no concrete visual graph-editor / code-node / return journey.

### UX-08 — Research, charts and data

| Status | IDs | What they actually cover |
|---|---|---|
| retain | `P1-DATA-001`..`004` | Provider disagreement; ticker≠instrument; revision does not rewrite old result; truncation ≠ empty ≠ unavailable ≠ denied |
| map | `P1-DATA-005`, `P2-DATA-009`..`010`, `P1-STR-001`..`005`, `P2-STR-006` | Recipe alignment/leakage; stale entitlement; schema mismatch; replay/live; gaps; backpressure; shared-feed cancel |
| missing | — | Instrument/time/query pickers; linked views; provenance/units/timezone/freshness **cues**; large tables; streaming plots; “ordinary analytics charts do not satisfy financial charting” as a product rule |

### UX-09 — ML evaluation

| Status | IDs | What they actually cover |
|---|---|---|
| retain | `P1-DATA-008` | Non-trading clustering/report is first-class; no bot/Book wrapper |
| map | `P1-DATA-006`..`007`, `P2-DATA-011` | Side-by-side model versions; incomplete weights; promotion lineage |
| map | `P1-PLC-001`, `P1-DATA-005` | GPU/entitlement preflight; leakage recorded on recipe |
| conflict | layout only | `02` **U**: LSE ML Studio UI is rejected as a layout. Capabilities may inform coverage. Do not recreate a fixed Train/Optimise form |
| missing | — | Dataset/features/split/version chrome; progress/logs/cancel; run comparison surface; cancellation vs interruption as UI states |

Aligned with “support non-trading ML.” Not aligned with a rigid ML Studio app.

### UX-10 — Trading / risk / position-sizing

| Status | IDs | What they actually cover |
|---|---|---|
| retain | `P1-MKT-001` | Default Book/BMS regression |
| retain | `P1-MKT-003`..`010`, `P2-MKT-011` | Explicit intelligence mode; account targeting; sequential owner; residual; unknown order; no unfill on rollback; stale process; ambiguous writers; partial-fill handover |
| map | `SCN-0006` | Book paper transition is a dated binding-epoch change (Book-scoped, not a universal UI gate) |
| map | `SCN-0020`, J03 / J03b / J10 | Two honest trading compositions; dummy Book = `INVALID_INPUT`; live ATC after paper-then-live + L17 |
| **conflict** | UX-10 + `02` **U** vs a universal paper gate | See §6.1. “No blanket paper-trading requirement.” Paper is relevant **only** where a capability executes trades or materially affects trading/risk |
| conflict (inherited) | `P1-MKT-002` vs older AD-11/L36 | Coverage-and-gaps still marks complete non-Book **deploy** contradictory pending L36. Stage C / DEC-0448 named-amended L36: ATC may exist; live still needs paper-then-live + L17. Sensing is **not** ATC |
| missing | — | Order-ticket chrome; paper-to-live **screen** as product UI; broker-credential onboarding. Do not infer those from generic handover cases |

### UX-11 — Operations and observability

| Status | IDs | What they actually cover |
|---|---|---|
| map | `P1-OP-002`..`005`, `P2-OP-006`..`008` | Lost ack → unknown; cancel-by-state; expiry; partial artifact; resume; no blind retry; interrupt ≠ cancel |
| map | `P1-PLC-001`..`006`, `P2-PLC-007` | Preflight, staging, UI close, coordinator loss, unverified restore, cross-store verify |
| map | `SCN-0021`, `SCN-0026`, `SCN-0027`, J-KIT-06/07 | Outbox/JobHandle; host retry `none`/`read` only; `failure_class` + JSON-lines; logs ≠ journals |
| missing | — | Health screens that **consume** those contracts; correlated run/events/logs UI; queue/backpressure; diagnosis as a useful screen (not a fourth observability product) |

`03` §2: operational screens consume current observability contracts rather than duplicating them. `SCN-0027` Branch A forbids a fourth observability product.

### UX-12 — Settings, local files, terminal, previews

| Status | IDs | What they actually cover |
|---|---|---|
| map | `P1-PLC-002`, `P1-PLC-003` | Local path → remote worker is staged as a content-identified artifact or refused; interrupted/escape staging is clean |
| map | `P1-CAP-006`, `SCN-0022` | Export strips secrets/private paths; scanner is the oracle |
| map | `P2-SES-007` | Stale credential refused; no silent substitute |
| missing | — | Global/app/session/instance setting **scope** UI; browser/video/code/diff/terminal/model/result previews; file location vs remote availability; persisted layout; unsupported-preview fallback; “preview rendering must not imply installation or execution permission” (`03` §4) |

### Coverage roll-up

| UX | Dominant status | Backend oracles exist? | UI/headless journey exists? |
|---|---|---|---|
| UX-01 | map + **missing first-run** | reconnect/preflight yes | splash/provider setup **no** |
| UX-02 | map + Home-profile **conflict** | instance-pick yes | rail/attention **no** |
| UX-03 | retain isolation + **missing composer** | sessions/grants yes | chips/preview **no** |
| UX-04 | map | composition yes | expand/return **no** |
| UX-05 | map + Library-kind **conflict** | catalog/pack yes | Library screen **no** |
| UX-06 | retain apply-law + **missing authoring chrome** | change-request yes | diff/preview **no** |
| UX-07 | map + **missing graph↔code** | workflow semantics yes | editor journey **no** |
| UX-08 | retain data law + **missing charts** | provenance yes | linked views **no** |
| UX-09 | retain non-trading ML + layout **conflict** | weights/lineage yes | eval workspace **no** |
| UX-10 | retain Book path + **paper-gate conflict** | trading compositions yes | ticket/promotion chrome **no** (and must not become universal) |
| UX-11 | map | op/placement/diagnosis yes | ops screens **no** |
| UX-12 | map + **missing previews** | staging/secrets yes | settings/terminal **no** |

---

## 3. SCN-0023..SCN-0027 vs UI scope

### 3.1 Where the files live (honesty)

| Ref | SCN-0023..0027 present? | Notes |
|---|---|---|
| Working tree `docs/scenarios/` on this checkout | **yes, untracked** (`git status` `??`) | Pack-and-grant Documentation Factory output on disk; **not** in `main@92279dfe` |
| `main@92279dfe` committed | **no** | Committed catalog ends at `SCN-0022-pack-lifecycle-headless.md` |
| `integration@34c148be` and `.worktrees/integration-inspect` | **no** | Inspect tree’s `docs/scenarios/` ends at `SCN-0014-money-path-barrier.md` |
| `git log --all -- docs/scenarios/SCN-0023-home-instance-pick.md` | empty | Never committed on any local ref inspected here |

Treat SCN-0023..0027 as **sitting-law on disk**, docs-authority in the pack-and-grant fold, **not** as integration-inspect runtime. Each file says it is specification, not executed proof at `34c148b` (DEC-0465).

Committed on main and relevant to UI, but **outside** 0023–0027: `SCN-0018` (pin honesty), `SCN-0019` (change-request), `SCN-0020` (two trading compositions), `SCN-0021` (outbox/JobHandle), `SCN-0022` (pack lifecycle / headless door parity). Integration-inspect does not carry 0018–0022 either.

### 3.2 Per-ID vs UX / §7

| ID | Pins | UI-scope reading | Not UI-scope |
|---|---|---|---|
| **SCN-0023** Home instance pick | J-KIT-03; DEC-0463/0464 | UX-02 / UX-03: main copilot may chat with no instance; invoke needs exactly one `instance_id` ref; envelope `instance_id` still required | Does not specify Home rail, attention list, or a third profile |
| **SCN-0024** Optional copilot / headless | J-KIT-01/02; DEC-0452/0454 | UX-01 close-tab; UX-03/04 optional copilot; UX-06 install≠grant; **§7 headless invocation without any view** | Not GAP-0081 chrome; panel is not a second copilot product |
| **SCN-0025** Nested Mission | J-KIT-04/05; DEC-0455 | UX-04 widget-starts-workflow; UX-07 nested work; dispose ≠ cancel | Not a visual graph merge; live Task Graph splice forbidden |
| **SCN-0026** Host retry | J-KIT-06; DEC-0457 | UX-11 / **§7 duplicate submit**: `read`/`none` retry in host; `external-egress` without receipt → `unknown`; no second send | Not a per-pack retry dialect; not a retry-ceiling number (GAP-0108) |
| **SCN-0027** Diagnosis JSON-lines | kit AD-5; J-KIT-07; DEC-0456 | UX-11: headless diagnosis (`grant\|workflow\|view\|dependency\|host`); ops screens must consume this, not duplicate it | Logs are not evidence; no fourth observability product |

Kit journeys in `architecture-QMX-2026-09-23/JOURNEYS.md` (J-KIT-01..07) are the missing pack-and-grant traces. They are **headless-first**. They do not cover splash, Library, graph↔code, or composer chips.

---

## 4. New UI / headless / mixed journeys required by `03` §7

`03` §7: reconcile the 85 first, then propose UI scenarios with explicit observable outcomes for the twelve sequences below. These are **proposed sitting journeys**, not minted `SCN` rows and not a rewrite of the 85.

**ID rules**

- Do **not** reuse `P1-*` / `P2-*` (the 85).
- Do **not** reuse `SCN-0001`..`SCN-0027`.
- Do **not** reuse workflows `J01`–`J27` or kit `J-KIT-01`..`07`.
- Sitting-local journey IDs: **`J-UI-01`..`J-UI-12`** (parallel to `J-KIT-*`).
- If a third challenge catalog is kept beside the 85: **`P3-UI-001`..`P3-UI-012`** (Pass-III, UI/mixed). Same order as J-UI.
- Future canonical docs, if Documentation Factory later absorbs them: start at **`SCN-0028`**. **Not minted here.**

Each row: observable outcome the architecture must name; related frozen/canonical IDs to **cite**, not replace.

| Sitting ID | Alt catalog ID | §7 sequence | Kind | Observable outcome (minimum) | Cite, do not reuse | Gap vs 85 |
|---|---|---|---|---|---|---|
| **J-UI-01** | P3-UI-001 | Switching apps during an ML run | mixed | Visible app B is selected while ML run R (started under app A / session S) continues. Streamed tokens, questions, and completion for R still bind to S. Switching does not redirect the answer or retarget the command. Closing B’s view does not cancel R. | `P1-SES-001`, `P1-PLC-004`, `P2-STR-006` | 85 isolate concurrent sessions; they do not specify **visible-app switch** during a live ML job |
| **J-UI-02** | P3-UI-002 | Headless invocation without any view | headless | Pack with no `view:*` and no `copilot_profile` is enabled. Operator invokes via CLI/wire. JobHandle exists. No navigation pane is created. A later optional inspector can attach without becoming a runtime requirement. | `P1-CAP-001`, `P1-OP-001`, `P1-PLC-005`, `SCN-0024`, J-KIT-01 | Backend parity exists; need an explicit **no-pane** mixed proof the shell can survive |
| **J-UI-03** | P3-UI-003 | Opening a code node and returning to its graph | UI | Select node N on graph G (draft/version V, viewport/selection recorded). Explicit Open/Expand shows code/diff for that draft. Validation/test-run names V. Return restores G’s viewport, selection, and version. Editing V2 is distinguishable from running V1. | `P1-WF-001`, `P1-WF-005`, `P1-WF-006` | **Missing.** No graph-editor / code-node / return ID in the 85 |
| **J-UI-04** | P3-UI-004 | Cross-app reference with separate conversations | mixed | Composer on session S_A adds a reference to instance/artifact of app B. Conversations remain separate. Command authority stays S_A’s grants. History of B is not merged. Unavailable B is labelled; the draft around the chip is preserved. | `P1-SES-001`, `P1-APP-001`, `P1-SES-004`, `SCN-0023`, J-KIT-03 | 85 cover isolation and artifact consume; not **reference chips** or “what will this conversation use?” |
| **J-UI-05** | P3-UI-005 | Missing resource | UI | Library or composer shows a named missing/unavailable/deleted resource. Invocation is refused with that identity. Surrounding draft/history remains. No silent substitute version (tombstone, not retarget). | `P1-APP-006`, `P2-CAP-009`, `P1-OP-005`, `SCN-0018` | Need the **visible** missing state, not only composite-degraded backend |
| **J-UI-06** | P3-UI-006 | Stale data / reconnect | mixed | After transport loss: shell shows reconnecting vs stale results as distinct from failed. Reconnect restores session context and pending approval **without** replaying intent or implying approval. Stream gap is surfaced, not drawn as continuity. | `P1-SES-002`, `P1-STR-002`, `P2-SES-008`/`011`, `P2-SES-010`, `P2-DATA-009` | 85 have reconnect/gap; not the **stale-badge vs reconnecting vs failed** shell |
| **J-UI-07** | P3-UI-007 | Duplicate submit | mixed | Double-activate of the same submit (click/Enter) on an `external-egress` or money-adjacent op does not create a second send. Second activation is coalesced or refused; state is `unknown` until reconcile if ack was lost. Ordinary `read` may retry in host without paging the operator. | `P1-OP-002`, `P2-OP-007`, `P1-WF-007`, `SCN-0026` | Need the **control** race, not only lost-ack after the fact |
| **J-UI-08** | P3-UI-008 | Cancellation racing success | mixed | Cancel clicked while completion is in flight yields one race-safe terminal: cancelled, already-complete, or unknown — never both “cancelled” chrome and a new execution. Worker-loss interrupt is not labelled cancelled. A cancelled **display** is not proof the worker stopped. | `P1-OP-004` (four states), `P2-OP-008` | Outline covers backend states; need the **chrome winner** and the display≠stopped rule from `03` §6 |
| **J-UI-09** | P3-UI-009 | Local file used remotely | mixed | Operator attaches a local path to a remote/VPS job. Preflight stages a content-identified artifact **or** refuses before the worker reads the path. Partial/symlink escape is not a successful stage. UI shows staging vs refused vs running-on-remote. Remote failure does not silently retarget locally. | `P1-PLC-002`, `P1-PLC-003` | Need the **staging progress/refusal** surface |
| **J-UI-10** | P3-UI-010 | Backend incompatibility | mixed | Enable/install of a pack whose host version/API is incompatible is refused with a stable compatibility error. Prior roster/index remains. Shell remains usable. Partial rebuild is not published. | `P1-CAP-002`, `P2-CAP-007`, `SCN-0022` | Need the **enable-time** message in shell/Library, including “QMX core too old/new” |
| **J-UI-11** | P3-UI-011 | First-run provider failure | UI | First launch: splash/status, then first usable window. One provider/API-key/proxy fails. Other work that does not need it remains available. Retry is actionable. Failure is not an indefinite full-app block. | none in the 85 | **Missing.** Closest are `P1-PLC-001` / `P2-SES-007`, which are preflight/credential at invoke, not first-run |
| **J-UI-12** | P3-UI-012 | Install / update / rollback | mixed | Library (or equivalent) shows installed vs enabled vs granted as distinct. Failed activation/migration keeps installed≠active and offers rollback or precise recovery. In-flight pinned run is not retargeted. Export/import of unavailable deps is honest. | `P1-CAP-003`, `P2-CAP-007`/`008`/`009`, `SCN-0022` | Need the **operator-visible** lifecycle, including grant unchanged until explicit re-grant (`P1-CAP-004`) |

### 4.1 Vertical slice (still a proposal, not a cap)

`03` §7 asks for a later coding slice after source reconciliation: differentiated shell + one widget/detail flow + one headless or graph-run path + real status restoration.

A slice that actually hits the new IDs without pretending the 85 are UI tests:

1. Shell + Home instance-pick (`J-UI-01` switch, `SCN-0023`).
2. One widget expand/return (`UX-04`; not yet a dedicated J-UI row — belongs with `J-UI-03` if the widget is graph-backed, else add later).
3. Headless invoke with no pane (`J-UI-02` / `SCN-0024`).
4. Reconnect restoration (`J-UI-06`).

Do not treat that slice as the architecture ceiling.

### 4.2 Journeys the 85 already make unnecessary to **re-derive**

Keep these as citations when writing J-UI Gherkin later; do not clone them under new P1/P2 numbers:

- Headless discover/invoke: `P1-CAP-001`, `P1-OP-001`, `SCN-0024`
- App-use cannot apply: `P1-SES-003`, `SCN-0019`
- Unknown ≠ failed; no blind retry: `P1-OP-002`, `P2-OP-007`, `SCN-0026`
- Layout-only edit is not a rerun: `P1-WF-005` (feeds `J-UI-03` return)
- Non-trading ML without Book: `P1-DATA-008`

---

## 5. Written Gherkin vs executable vs passing runs

**Expected: specification only. Confirmed.**

| Layer | What exists | What it proves | What it does not prove |
|---|---|---|---|
| **Written Gherkin** | 5 feature files, 85 IDs, tags `@draft @specification_only` | A human-readable behavioral spec with 1:1 catalog trace | Runtime behavior |
| **Catalog JSONL** | 85 objects; `evidence_status=baseline-specified; execution pending` | Trace integrity (TEST-AND-MUTATION-PLAN check) | `.feature` execution |
| **Step definitions / runner** | **None** found for these five files. Root `pyproject.toml` pytest `testpaths = ["adws/tests"]`. Dev group: ruff, pytest, mypy — **no** pytest-bdd, behave, or Cucumber | Inspected config has no Gherkin binding | Not a claim that some other uninspected mechanism exists |
| **Passing runs of the 85** | **Zero.** Inventory: “No tests were run for this inventory.” Challenge plan: QML mill/store **47 passed** and QMN conformance **5 passed, 1 skipped** at `270e992` — those are **package tests**, not these features | Unrelated package slices at the then-pinned SHA | UI, Gherkin, or e2e |
| **Canonical SCN docs** | `SCN-0001`..`0022` committed on main; `0023`..`0027` untracked specification | Intended behavior + forbidden branches | Code at `34c148b` (DEC-0465 / DEC-0450 / DEC-0286: fixtures ≠ e2e) |
| **Kit journeys** | J-KIT-01..07 in `architecture-QMX-2026-09-23/JOURNEYS.md` | Missing pack-and-grant traces | Execution |
| **Workflows journeys** | J01–J27 in `architecture-QMX-2026-09-18/JOURNEYS.md`; 85 remain independent | Reconciled candidate claims | Replacement of the 85 |
| **Reticle** | `02` **U**: user-facing implementation needs `reticle_act_and_wait` / `reticle_assert`; `unknown` is not a pass | Future UI proof bar | This sitting is documents only; no app connected |

Keep later quality planes separate (`03` §7): static checks, unit/component, contract/integration, browser interaction, failure injection, performance, installed-product evidence. Review tools inspect code; they do not replace startup, layout, or runtime.

---

## 6. Conflicts

### 6.1 Paper-trading universal gate vs current direction — **the named conflict**

| Source | Statement |
|---|---|
| `03` UX-10 | “No blanket paper-trading requirement.” Paper/simulation **where relevant**. Operations with financial effects distinct from analysis |
| `02` **U** | “Paper trading is relevant only where a capability executes trades or materially affects trading/risk behavior. General data tools, headless utilities and non-trading ML need suitable functional/operational evaluation instead. **No universal week-or-two paper gate is approved.**” |
| `SCN-0020` Then (6) | Live ATC without paper-then-live + L17 is `not_promoted` |
| OD-01 (closed, recheck handoff) | L36 named-amended (DEC-0448). Live ATC still requires paper-then-live + L17. Sensing is not a trading composition |
| `SCN-0006` | Book paper transition is a dated **Book** binding-epoch change; soak items are **node** machinery-proof, not a UI-wide gate |
| Trading-node / DEC-0261 | Paper for a **bot** is outside the node (QMB/research) before promotion; node paper is soak-week + BMS/Book demotion — still **trading-node**, not every mini-app |
| `P1-MKT-001` / `P1-MKT-002` | Keep default Book/BMS; a complete non-Book composition validates/simulates without dummy Book |
| `COVERAGE-AND-GAPS.md` | BR-MKT **contradictory** for complete non-Book **deploy** (AD-11 held live/node-paper without Book pending L36) |

**Reconcile without pretending it is already closed in UI:**

- **Not a conflict** if paper-then-live + L17 is scoped to **trading compositions that take a QMN seat** (`ResolvedRunConfig` default path, `AlternativeRunConfig` ATC).
- **Is a conflict** if architecture, first-run, or Library treats paper as a **universal product gate** for headless packs, data tools, or non-trading ML (`P1-DATA-008`, `UngovernedWorkConfig`, UX-09, `02` **U**).
- **Is a conflict** if UI copies a “week-or-two paper” checklist onto every capability.
- Dummy Book as a fake paper path remains `INVALID_INPUT` (`SCN-0020`, `P1-MKT-002`).

UI sitting should **not** invent a paper-trading onboarding screen for non-trading work. Trading apps that submit/risk may show environment identity and readiness evidence (UX-10) without making that the shell’s first-run.

### 6.2 Other conflicts and traps

| # | Clash | Resolution for this sitting |
|---|---|---|
| 1 | Home as a third `ProductSessionProfile` vs `SCN-0023` Branch A | Home is authoring with absent instance, not a new profile |
| 2 | Library as a new persisted kind vs UX-05 | Navigation/search chrome over existing hits/artifacts/packs; no new universal object type |
| 3 | LSE ML Studio layout vs UX-09 | Cover ML evaluation; reject that layout/form as default |
| 4 | `P2-SES-008` ≈ `P2-SES-011` | Retain both 85 rows; one UX reconnect-approval pattern (`J-UI-06`) |
| 5 | Preview rendered ⇒ installed/granted | `03` §4 forbids the implication; no 85 ID states it — add under `J-UI-04` / UX-12 |
| 6 | Cancelled display ⇒ computation stopped | `03` §6; `P1-OP-004` / `P2-OP-008` are backend; `J-UI-08` must keep display≠stopped |
| 7 | Closing a view ⇒ cancel work | Forbidden by `P1-PLC-004`, `P2-STR-006`, `SCN-0024`, `SCN-0025` |
| 8 | Headless pack refused because it has no copilot | Forbidden by `P1-CAP-001`, `SCN-0024` Branch A |
| 9 | Logs as evidence / fourth observability product | Forbidden by `SCN-0027`; UX-11 screens consume contracts |
| 10 | Claiming SCN-0023..0027 or the 85 are executed at `34c148b` | Forbidden (DEC-0465, `@specification_only`, fixtures ≠ e2e) |
| 11 | Collapsing `P1-*` into `SCN-*` or into `J-UI-*` | Three namespaces; cite, don’t merge |
| 12 | `P1-MKT-002` “complete non-Book” vs calling sensing a second trading system | Sensing/`UngovernedWorkConfig` is not ATC (`SCN-0020` Branch B) |

### 6.3 Inherited unresolved (not for UI to silently decide)

From `COVERAGE-AND-GAPS.md` / Grok reconciliation Gate 1: whether complete non-Book **deployment** stays in scope or stays L36-narrowed. Stage C recorded DEC-0448 / `SCN-0020`. UI must not reopen that as a chrome decision. Show environment identity where a trading composition exists; do not require Book widgets on non-trading apps.

---

## 7. What this sitting should not do

- Do not rewrite Pass-I rows.
- Do not drop the 85 down to a “UI-sized” subset (`GROK-RECONCILIATION-HANDOFF.md`: use the 85 as oracles).
- Do not run `/documentation-factory` from this research file.
- Do not implement Gherkin runners, step defs, or Reticle checks here.
- Do not treat untracked `SCN-0023`..`0027` as committed main or as integration-inspect code.

---

## Sources read

- `workroom/qmx-ui-architecture-handoff-2026-09-23/03-EXPERIENCE-SCOPE.md` (§2 UX-01..12, §7 journeys)
- `workroom/qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md`
- Five feature files under `…/evidence/bdd/behavior/`
- `…/evidence/bdd/context/INDEPENDENT-SCENARIO-BASELINE.md` (SHA verified)
- `…/evidence/bdd/context/SCENARIO-CATALOG.jsonl` (85 IDs + schema)
- `…/evidence/bdd/context/COVERAGE-AND-GAPS.md`
- `…/evidence/bdd/context/GROK-RECONCILIATION-HANDOFF.md`
- `…/evidence/bdd/context/TEST-AND-MUTATION-PLAN.md`
- `…/evidence/bdd/README.md`, `source-map.json`
- `…/evidence/session/handoff-working/bdd-inventory.md`
- `docs/scenarios/SCN-0006`, `SCN-0018`..`SCN-0027` (0023–0027 untracked)
- `architecture-QMX-2026-09-23/JOURNEYS.md` (J-KIT-01..07)
- `architecture-QMX-2026-09-18/JOURNEYS.md` (J01–J27; 85 remain independent)
- Git: `main@92279dfe`, `integration@34c148be` via `.worktrees/integration-inspect`
