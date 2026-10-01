# Independent consistency review — QMX UI host + backend-delta docs fold (2026-09-25)

Date: 2026-09-25. Reviewer: grok-4.6 (independent 8-lens synthesis; did not draft the fold). Scope: `docs/` plus `_docwork/gaps.yaml` and `_docwork/feature_inventory.yaml` as restamped by the 2026-09-25 UI host + backend-delta sitting. Authority: `_docwork/ui-backend-increment-brief.md`, `_docwork/riders/ui-and-backend-delta-2026-09-25.md`, ledger DEC-0469..DEC-0510, GAP-0081/0100 answered and GAP-0109..0114 deferred. No production code. No architecture invention. This file supersedes the same-path orchestrator stub that claimed pass-with-desk-amendments.

Taxonomy (assigned): **critical** = live-law contradiction or banned noun as current law; **major** = missing required annotation; **minor** = locator/index drift. Lens-severity disagreements are remapped to that taxonomy. Findings are deduplicated across lenses. Nothing is filed that the lenses did not evidence.

Lenses: `zombie-chrome`, `pairing-nouns`, `host-control`, `contracts`, `features`, `screens-index`, `honesty`, `parent-amendments`.

## Verdict: FAIL-with-amendments

The fold restamped chrome as the Svelte host in several new/increment sections, appended AM-01 on CT-40, and added UI scenarios and ADR-0026. It did **not** make that restamp the current law everywhere a builder or agent actually reads.

Six live-law defects remain: a CT-40 invariant still names **the Rust UI** as a current client; GAP-0081 is still asserted as deferred current law in AGENTS, the QMA deferred intro, and SCN-0013; AM-03 journal projections are a silent add against the DEC-0429/DEC-0440 complete-list; CT-40 still requires a Credential-Broker reference for every client; CT-46/CT-48 `schema.fields` read as inspect-present against DEC-0507 AMEND-absent; the overview mermaid presents pairing + Svelte + CT-40 JSON-RPC as the current operator path without DEC-0507.

Eighteen majors are missing required sitting annotations (pairing nouns, recover-control writer fence, origin-revoke argv, AM-10/AM-12/AM-02/AM-04/initialize, named holds, rail/artifact screens, honesty banners). Twelve minors are locator/frontmatter/gloss drift. No lens evidenced a new COMP-UI row, a `docs/contracts/ct-52*` file, or `pairing_session_id` as a live field.

## Hunt results

| # | Check | Result |
|---|---|---|
| 1 | GAP-0081 / GAP-0100 not left as live deferred chrome | **FAIL** — AGENTS source-of-truth, gap-report “22 stay deferred” intro, SCN-0013, FEAT-0041 notes, ADR-0020/0022 without a 2026-09-25 follow-up |
| 2 | No banned leftover as current law (`the Rust UI`, cookie/`localStorage` pairing, `pairing_session_id`) | **FAIL** — CT-40 live invariant still names `the Rust UI included`. Lenses did not evidence `pairing_session_id` as a live field |
| 3 | Named AM-01..AM-17 on inherited closed lists (not silent add) | **FAIL** — AM-03 silent on the daemon sqlite complete-list; AM-01/AM-11/AM-10/AM-12/AM-02/AM-04 incomplete on CT-40/CT-46/CT-48/qma-wire/qma-daemon |
| 4 | Pairing product nouns (`pairing_proof`, `pairing_record_id`, `pairing:<proof>`, `qmx.pair.<proof>`, memory+sessionStorage) | **FAIL** — bootstrap screen and security-model custody section incomplete |
| 5 | recover-control one-shot writer; origin-revoke `--session` / `--origin`; AM-10 host group | **FAIL** — writer fence, argv semantics, `COMMAND_GROUPS += host`, and T-H-03 not folded |
| 6 | Inspect honesty: proposed ≠ wired at `integration@34c148be` (DEC-0507) | **FAIL** — overview mermaid; SCN-0029..0035 banners; CT-46/CT-48 `wiring_status` |
| 7 | ADR-0024 / ADR-0025 original Decision unrewritten | **PASS** (lenses evidenced dated follow-up only on ADR-0024/0025; they did not evidence a Decision rewrite). ADR-0024 follow-up still does not map AM-03/AM-04 onto inherited bullets (minor) |
| 8 | No sixth COMP / no new CT | **PASS** — no lens evidenced `COMP-UI` or `ct-52*` |
| 9 | FEAT-0071 `blocked_by` is FEAT-0055 + FEAT-0066 + FEAT-0041 | **PASS** (parent-amendments). Named holds on FEAT-0041/0045/0055 notes still missing (major) |
| 10 | Frontmatter `decisions` / locators / index match the body | **FAIL** — systematic frontmatter and locator drift (minors); feature-wave table and “every file linked” claim are majors |

## Findings

### Critical

### 1. critical — `docs/contracts/ct-40-qma-wire-envelope.yaml` (transport invariant)

**Finding.** A live CT-40 invariant still says language-specific workers and non-Python clients — **the Rust UI included** — connect as clients and never re-implement a qmf contract. The same file already restamps `intended_consumers` and the GAP-0114/DEC-0509 invariant to the Svelte host. GAP-0081’s public answer is that a Rust UI SDK is refused and chrome is the Svelte client (DEC-0509).

**Lenses.** zombie-chrome (critical); honesty (major); contracts (minor). Same invariant.

**Contradicts.** DEC-0509; DEC-0505; rider “do not claim a Rust UI host as current law.”

**Fix.** Keep the language-boundary rule. Replace “the Rust UI included” with non-Python clients / the Svelte host as a specified CT-40 client. Do not pin Rust as the product UI. Keep the existing `wiring_status` note that the Svelte host is absent at `34c148be` (DEC-0507). Do not rewrite DEC-0304 Decision text elsewhere.

### 2. critical — `docs/components/qma-daemon.md` (journal projections); also `docs/decisions/ADR-0020-qma-agentic-system.md`; `docs/decisions/ADR-0024-workflows-construction-kit.md`

**Finding.** The UI section adds journal projections `pairing_pending` / `pairing_session` / `editor_draft_head` / `local_operator` with no AM-03 cite. `artifact_transfer_ticket` appears in no `docs/` match. ADR-0020 still says v1 daemon additions are the complete closed list, with no 2026-09-25 follow-up. ADR-0024 Decision AD-16 still says “complete list” / “No other new sqlite”; its 2026-09-25 follow-up only names AM-01..AM-17 as a range. AD-6’s closed store list is still the original projections plus the sixteen-member definition store; `local_operator` and pairing projections are not added there.

**Lenses.** parent-amendments (critical); host-control (major, AD-6 list).

**Contradicts.** DEC-0429 / DEC-0440 complete-list law; prefold DF-AM03-LIST (named add on the existing sqlite class, not a replacement list and not definition-store slots 17+).

**Fix.** Named-add AM-03 projections `pairing_pending`, `pairing_session`, `editor_draft_head`, `artifact_transfer_ticket`, `local_operator` on the existing DEC-0429/DEC-0440 sqlite class. Cite AM-03 on the daemon UI store paragraph. Restore `artifact_transfer_ticket` as the transfer-ticket projection. Add a 2026-09-25 ADR-0020 follow-up and thicken the ADR-0024 follow-up to name AM-03. Do not set those DECs `superseded_by`.

### 3. critical — `docs/AGENTS.md`; `docs/gap-report.md`; `docs/scenarios/SCN-0013-quant-over-the-wire.md`

**Finding.** Chrome is restamped answered Svelte (DEC-0509) in ADR-0026 and in later hard-rules, but current-law catalogs still treat GAP-0081 as live deferral:

- AGENTS source-of-truth still says `qma-ui-contract` is a deferred stub and “the UI extension SDK is deferred” (DEC-0333), and still lists “the 22 QMA deferred rows GAP-0070–GAP-0091” as open. The same file’s UI hard-rules restamp DEC-0509, so the file disagrees with itself. Reading order item 7 and “Where answers live” never point at ADR-0026, SCN-0028..0035, or `docs/lenses/ui/`. Frontmatter `decisions` stop at DEC-0468; `sources` omit the UI/backend-delta spines.
- gap-report heading “Deferred by the QMA sitting — 22” plus intro “Each deferred row stays deferred … and none is revived”, while the same table marks GAP-0081 answered (DEC-0509).
- SCN-0013 still: “the UI is Deferred and its extension SDK is Deferred … (DEC-0333, GAP-0081).”

**Lenses.** zombie-chrome (major ×3); screens-index (major ×2 on AGENTS routing/frontmatter).

**Contradicts.** DEC-0509; DEC-0333 restamp (wire/registry still bind now; chrome answered; leftover types GAP-0114); increment brief standing table.

**Fix.** Carve GAP-0081 out of the deferred-22 list (21 deferred plus GAP-0081 answered; do not revive it). AGENTS: Ratified UI-host bullet; chrome answered Svelte; leftover types GAP-0114; reading order + Where-answers-live + `decisions`/`sources` through ADR-0026 / SCN-0028..0035 / DEC-0510 / `docs/lenses/ui/`. Keep the Quant-over-the-wire first milestone on SCN-0013; dated-note chrome as DEC-0509 and leftover types as GAP-0114.

### 4. critical — `docs/contracts/ct-40-qma-wire-envelope.yaml`; `docs/components/qma-wire.md`

**Finding.** CT-40 still has the unamended transport-posture invariant: every client authenticates with a Credential-Broker-resolved reference before protocol bytes; an unauthenticated bind or a plaintext non-loopback bind is a hard startup refusal (DEC-0304, DEC-0336). AM-01 is appended later and says Bearer `pairing:<proof>` and that machine/worker clients still present `credential_ref`, but it never names `pairing_record_id` or “does not populate `credential_ref`.” `pairing_record_id` appears in no contract YAML. `qma-wire.md` parent transport body still requires a broker credential on every client and a single inbound port; AM-11/AM-15 are unnamed except in the ADR-0026 preflight table.

**Lenses.** contracts (major); parent-amendments (major). Same parent-auth hole.

**Contradicts.** DEC-0493 / AM-01 / AM-11 (browser-paired `AuthenticatedWireSession` carries `principal_class=operator` plus `pairing_record_id` and does not populate `credential_ref`; `pairing_proof` is not a broker ref and does not widen CT-45). AM-15 / DEC-0494 (host-control is outside 8765, not a second bind, not AM-01 HTTP).

**Fix.** Mark the Credential-Broker / unauthenticated-bind sentence as named-amended by AM-01/AM-11 (DEC-0493). State browser-paired session = operator + `pairing_record_id`, no `credential_ref`. Qualify the qma-wire transport paragraph with AM-11/AM-15: machine/worker still present `credential_ref`; browser pairing uses `Authorization: Bearer pairing:<proof>` / WS `qmx.pair.<proof>` and journals `proof_fp1` only; host-control is a token-gated loopback channel under `QMA_DAEMON_ROOT`. Do not whole-supersede DEC-0304 / DEC-0323.

### 5. critical — `docs/contracts/ct-48-qma-mailbox-envelope.yaml`; `docs/contracts/ct-46-qma-execution-environment-job.yaml`

**Finding.** Both contracts now mint additive UI fields in `schema.fields` while `wiring_status` still says matching source exists on `integration@1b451a8` (DEC-0286), with no `34c148be` / DEC-0507 stamp:

- CT-48: `envelope.product_session_ref` optional additive, excluded from Envelope fp1. DEC-0507: Envelope has no `product_session_ref` at inspect.
- CT-46: `job_handle.originating_product_session_ref` optional immutable at UI admit. DEC-0507: JobHandle has no `originating_product_session_ref` at inspect. No named AM-04 invariant. JobHandle invariant still describes only job id plus closed states.

CT-40 AM-01, by contrast, refused to add new fields to `schema.fields` and recorded inspect absence.

**Lenses.** honesty (major ×2); contracts (major ×2). Same honesty class on both files.

**Contradicts.** DEC-0507 AMEND-absent; DEC-0286 (source-inspected ≠ e2e).

**Fix.** Keep the additive spec in invariants. Stamp `wiring_status` / provenance: fields are specified AMEND, not present on inspect (DEC-0507); format mint FEAT-0067 / FEAT-0071. Add a named AM-04 / DEC-0496 invariant on CT-46. Do not place the JobHandle field on CT-42. Do not claim the new fields are implemented.

### 6. critical — `docs/architecture/overview.md`

**Finding.** The QMA containers mermaid draws the Svelte host and `operator -->|pairs, then drives Quants via the Svelte host|` over `JSON-RPC 2.0 / WebSocket + HTTP GET queries (CT-40)`. The only inspect honesty in the file is DEC-0465 (InvocationEnvelope, GrantRecord, and `product_session` types exist as fixtures). The file never cites DEC-0507 and never says DaemonProcess discards TCP bytes. Frontmatter `decisions` end at the pack-and-grant block (through DEC-0465) and never cite DEC-0469 or DEC-0509, even though the mermaid is already Svelte.

**Lenses.** honesty (major); zombie-chrome (minor, frontmatter).

**Contradicts.** DEC-0507 ABSENT list (live CT-40 server, `/pair/*`, `qmb host`, Svelte host). A reader can take proposed chrome/pairing/serving as wired.

**Fix.** After the DEC-0465 paragraph add Honesty (DEC-0507): CONNECT types/fixtures remain; AMEND Envelope has no `product_session_ref` and JobHandle has no `originating_product_session_ref`; ABSENT live CT-40 server (DaemonProcess discards TCP bytes), `/pair/*`, `qmb host`, `list_mailbox`, `cancel_job`, PUT `/artifacts/stage`, Svelte host. Add a mermaid note: proposed connects ≠ implemented at `34c148be`. Add DEC-0469, DEC-0505, DEC-0509 to frontmatter `decisions`.

### Major

### 7. major — `docs/decisions/ADR-0020-qma-agentic-system.md`; `docs/decisions/ADR-0022-workbench-expansion.md`

**Finding.** Required 2026-09-25 dated follow-ups are missing. ADR-0020 Decision still: the UI and its extension SDK are Deferred (DEC-0333, GAP-0081); Consequences: “The UI is later and its extension SDK is Deferred”; follow-ups stop at 2026-09-23 pack-and-grant. ADR-0022 Decision still: “Rung 4 stays GAP-0081”; refused candidate “UI contribution SDK this sitting — GAP-0081, DEC-0280”; follow-ups stop at 2026-09-19. `qml.md` already restamps rung 4 to GAP-0114.

**Lenses.** zombie-chrome (major ×2); parent-amendments (major, ADR-0020 also for AM-01/AM-03/AM-11/AM-15 / DEC-0429).

**Contradicts.** Prefold: new normative sentences on already-ratified parent docs need a dated follow-up or annotation; do not rewrite Decision. DEC-0509; `qml.md` rung-4 restamp.

**Fix.** ADR-0020 follow-up 2026-09-25 (ADR-0026): Decision stands; GAP-0081 chrome is answered Svelte (DEC-0509); `qma-ui-contract` types remain GAP-0114; first milestone is still a Quant over the wire; name AM-01/AM-03/AM-11/AM-15 against DEC-0304/DEC-0323 and AM-03 against the DEC-0429 complete list; do not set those DECs `superseded_by`. ADR-0022 follow-up: rungs 1–3 unchanged; chrome answered (DEC-0509); remaining `qma-ui-contract` types are GAP-0114; do not mint `ui_view`.

### 8. major — `docs/lenses/ui/screens/bootstrap.md`; `docs/lenses/security/security-model.md`

**Finding.** The pairing screen never uses `pairing_proof`, `pairing_record_id`, HTTP `Authorization: Bearer pairing:<proof>`, or WS `qmx.pair.<proof>`. Callbacks are `onPairStart` → `POST /pair/start`, `qmb host pair <code>`, `onPairConfirm` → `POST /pair/confirm`, `onRenew` → authenticated `POST /pair/renew`. Sample data: proof stored in **sessionStorage only**. Origin-never-issues is only an Error row. The file never mentions in-memory, closed-tab cold start, `list_mailbox` restore, cloned-tab `producer_id`, or forbidding cookies/`localStorage`/IndexedDB.

Security-model pairing custody names Bearer `pairing:<proof>`, WS `qmx.pair.<proof>`, forbidden homes, and `proof_fp1`, but never names `pairing_record_id` (so proof versus journal identity is not split) and never names allowed homes (memory + sessionStorage; same-tab reload may restore; closed-tab cold start does not). Forbidden-homes without the allowed restore path contradicts DEC-0501.

**Lenses.** pairing-nouns (major ×3); screens-index (major ×2). Same pairing-noun hole.

**Contradicts.** DEC-0491, DEC-0485, DEC-0492, DEC-0501; DF-PROOF-WORDING / DF-COOKIE-LOCALSTORAGE.

**Fix.** On bootstrap: `pairing_proof` is the memory+sessionStorage bearer; `pairing_record_id` is the journal identity; HTTP `Authorization: Bearer pairing:<proof>`; WS `qmx.pair.<proof>`; Origin never issues a `pairing_proof` in Callbacks out (QMB confirm of that pending, or authenticated `/pair/renew`). Same-tab reload may restore; closed tab is cold start (empty storage, `list_mailbox`, never auto-resend). Forbid cookies, `localStorage`, and IndexedDB for the proof. On security-model: add `pairing_record_id` as the nonsecret journal identity (logs and `qmb host status` may show it only; never `pairing:<id>` in `Authorization`); state allowed homes.

### 9. major — `docs/lenses/security/security-model.md`; `docs/components/qma-daemon.md`

**Finding.** The 2026-09-25 security-model section states OS-owner stop-when-missing, stopped-daemon recover without the lost token, and preserve `local_operator`. It never names `.daemon_writer`, `host_control_fp1` append, listener down, port 8765, AM-01, or sqlite. Daemon line 305: recover-control is a one-shot daemon recover entry. FM-30 only refuses live/non-owner/readable-file and allows OS-owner stop-when-missing. Neither says acquire `.daemon_writer`, append `host_control_fp1`, exit, listener down, not 8765, not AM-01.

**Lenses.** host-control (major ×2).

**Contradicts.** DEC-0494 / DEC-0503; DF-RECOVER-WRITER.

**Fix.** Fold: QMB is the door; a one-shot daemon recover entry acquires `.daemon_writer`, appends `host_control_fp1`, releases the lock, exits with the listener down, does not bind 8765, is not AM-01 HTTP; QMB never writes daemon sqlite. Expand FM-30 Behavior to that writer. Keep rotate-control as the live-token path.

### 10. major — `docs/lenses/security/security-model.md`; `docs/components/qma-daemon.md`; `docs/components/qmb.md`

**Finding.** Origin-revoke is only named as a `journal_seq` barrier for that Origin (DEC-0492). Security-model and the daemon pairing paragraph never write `pair revoke --session <pairing_record_id>` or `--origin <origin>`, and never say after R a new `/pair/start` is legal. `qmb.md` lists both argv forms but omits barrier semantics: `--origin` is that static Origin at creating-event `journal_seq < R`, including a renew that committed earlier; never discarded as a first-append/CAS loser; `--session` is that `pairing_record_id` only, never origin-wide; after R new `/pair/start` is legal; never Origin-permanent death.

**Lenses.** host-control (major ×3).

**Contradicts.** DEC-0492; DF-ORIGIN-ARGV / DF-JSEQ-CREATE.

**Fix.** Cite both argv forms and the creating-event `journal_seq < R` barrier on security-model, daemon pairing, and the qmb host group.

### 11. major — `docs/components/qmb.md`

**Finding.** Host-lifecycle lists `qmb host` verbs but never `COMMAND_GROUPS`. Structural seed `doors/cli` remains “qmb command tree (thin)”. `docs/` has zero `COMMAND_GROUPS`, `HostedBot`, or `qmb.host.adapter`. Missing token plus existing principal is called not first-start bootstrap, but T-H-03 is not folded: `start` may spawn if the lock is free without reminting; running-daemon pair/configure/rotate/revoke/status still require the token; pairing proofs stay valid until TTL; OS-owner stop-when-missing remains the path to recover. B-1 still says the Python API door exposes the same pure-function surface for the UI backend (consumed in-process), while line 291 says the product UI must not import qmb in-process (DEC-0478). AM-10/AM-15 are unnamed on the inherited COMMAND_GROUPS / QMA AD-24 human-gate / AD-26 write-path contracts.

**Lenses.** host-control (major ×3); parent-amendments (major).

**Contradicts.** AM-10 / AM-15; DEC-0478; DEC-0494; HOST-LIFECYCLE T-H-03; CT-33 `qmb.host` (HostedBot) is not this CLI.

**Fix.** State AM-10 as `COMMAND_GROUPS += host` (`start|status|stop|pair|configure|rotate-control|recover-control` plus the two revoke forms) over host-control. Honesty at `34c148be`: `COMMAND_GROUPS` has no `host`; do not reuse package `qmb.host`. Date-annotate B-1: research/Python callers may import the library; the Svelte product UI is a qma-wire client and must not import qmb (DEC-0478). Fold T-H-03. Cite AM-10/AM-15. Do not append host verbs to the CT-40 human-gate catalog.

### 12. major — `docs/components/qma-daemon.md`; `docs/contracts/ct-40-qma-wire-envelope.yaml`; `docs/components/qma-wire.md`

**Finding.** AD-26 still says a registry-homed value is set only by operator-principal `variable.set`. The Configuration table has no `pairing.session_ttl` row. A later pairing bullet says only host-control may write that key. CT-40 never mentions `variable.set` or `registry:pairing.session_ttl`; the human-gate invariant still says AD-24 `variable.set` is the write path with no exception. The refuse rule lives on `qma-wire.md` FM-17 and `docs/registry/variables.yaml` notes only. `qma-wire.md` Configuration intro still says each row is a UI-editable, registry-homed AD-26 variable set only by operator-principal `variable.set`, against the table row that says CT-40 `variable.set` of this key refuses.

**Lenses.** host-control (major); parent-amendments (major + minor on qma-wire intro); contracts (major).

**Contradicts.** DEC-0492 / AM-10; GAP-0109 (mint no TTL number); DF-AM10-WRITEPATH.

**Fix.** Named-amend the AD-26 write-path paragraphs and add `registry:pairing.session_ttl` to the daemon Configuration table. Add a CT-40 invariant: CT-40 `variable.set` of that key refuses. Qualify the qma-wire Configuration intro with the AM-10 exception. Only `qmb host configure pairing-ttl` over host-control may write the row. Do not append host start/stop/pair/recover-control to the human-gate catalog. Mint no TTL number.

### 13. major — `docs/contracts/ct-40-qma-wire-envelope.yaml` (DEC-0500 initialize)

**Finding.** AM-01 lists addable names (`list_mailbox`, `get_pack_ui_request`, `get_editor_draft_head`, `cancel_job`, `transfer_artifact`, `transfer_complete`, `save_editor_draft`, `publish_editor_draft`) and says PUT/GET are byte channels, but does not mention initialize capabilities `pairing`, `caller_kind`, `pack_ui_request`, or `stage_artifact`. `stage_artifact` appears in no contract YAML. `docs/components/qma-wire.md` addable-names paragraph does fold initialize `pairing` / `stage_artifact`.

**Lenses.** contracts (major).

**Contradicts.** DEC-0500; AM-09 (no JSON-RPC `stage_artifact`; the capability means authenticated PUT `/artifacts/stage` exists).

**Fix.** Add a CT-40 named-amendment invariant for DEC-0500 initialize capabilities, stating `stage_artifact` means the PUT exists and is never a WireCommand (AM-09). Do not add those names to `schema.fields`; seed 9/7/10 stay the seed.

### 14. major — `docs/contracts/ct-46-qma-execution-environment-job.yaml`; `docs/contracts/ct-40-qma-wire-envelope.yaml` (`cancel_job`)

**Finding.** `handle_id` appears in no `docs/contracts` match. CT-46 `schema.fields` has `job_handle.originating_product_session_ref` and `job_handle.job_id` but no `handle_id`. CT-40 AM-01 lists `cancel_job` among addable names only. JobHandle.operations still says cancel with no wire identity rule. AM-04 is named only in the ADR-0026 preflight table.

**Lenses.** contracts (major); parent-amendments (major).

**Contradicts.** DEC-0496 / AM-04 (“Addable command `cancel_job`. `handle_id` is `job_id`.”); SCN-0035 states the equality in scenario prose only.

**Fix.** On CT-46 (and the CT-40 `cancel_job` addable-name line): `handle_id` is `job_id`; UI `cancel_job` is unavailable when `originating_product_session_ref` is absent; states stay closed (DEC-0316, DEC-0439). Named-amendment usage note AM-04 / DEC-0496. Do not put the field on CT-42. Do not set DEC-0439 `superseded_by`.

### 15. major — `docs/contracts/ct-40-qma-wire-envelope.yaml` (AM-12)

**Finding.** CT-40 still: every wire command is idempotent on the pair producer id plus id, and the daemon keeps a dedup cursor whose window is `registry:wire.dedup_window` (DEC-0304). No `send_message` exception. The collision law is folded only in SCN-0031, not in CT-40 or the qma-wire.md idempotency section.

**Lenses.** contracts (major).

**Contradicts.** DEC-0495 / AM-12: `send_message` same `(producer_id, id)` plus different payload hash refuses for journal lifetime (mailbox sends only); other commands keep `wire.dedup_window`.

**Fix.** Named-amend the CT-40 dedup invariant. Do not change MessageKind / DeliveryState.

### 16. major — `docs/contracts/ct-48-qma-mailbox-envelope.yaml` (AM-02)

**Finding.** AM-02 landed the additive `product_session_ref` field and fp1 exclusion. It does not say “replies inherit.” PARENT-AMENDMENT-MAP AM-02: “Replies inherit.” No `docs/` match for that phrase. DEC-0495 also requires principal equality on `send_message` / `list_mailbox` when the field is present; that admit rule is on `qma-daemon.md` only, not CT-40/CT-48.

**Lenses.** contracts (major).

**Contradicts.** DEC-0495 / AM-02. Reply Envelopes can drop `product_session_ref` and break restore-by-`psess:`.

**Fix.** Extend the CT-48 AM-02 invariant: replies inherit `product_session_ref`; when the field is present, `send_message` / `list_mailbox` admit only if connection operator principal equals the session durable principal. Keep MessageKind / DeliveryState closed.

### 17. major — `_docwork/feature_inventory.yaml` (FEAT-0041 / FEAT-0045 / FEAT-0055)

**Finding.** Prefold D1 named holds and the FEAT-0041 initialize-capability annotation are missing from the only notes this sitting was allowed to patch. FEAT-0041 notes still: “The wire contract binds now while the UI is later (DEC-0333)”; scope Out still: “the qma-ui-contract beyond a deferred stub (GAP-0081, DEC-0333)”. No Story 41.4 unauthenticated-bind hold and no DEC-0500 addable initialize names. FEAT-0045 notes have no Story 46.4 Envelope-field-list hold. FEAT-0055 notes are only “Feeds from GAP-0095.”

**Lenses.** features (major); parent-amendments (major + minor on Out).

**Contradicts.** Prefold D1 / DF-HOLD; DEC-0509 (GAP-0081 answered; leftover types GAP-0114); DEC-0500.

**Fix.** On FEAT-0041 notes only: hold Story 41.4 unauthenticated-bind (machine clients stay `credential_ref`; AM-01 is the `/pair/start|/pair/confirm|OPTIONS` carve-out); list DEC-0500 addable initialize names; restamp GAP-0081 answered / stub = GAP-0114; retarget Out to GAP-0114 / no `ui_view` / no COMP-UI. On FEAT-0045 notes: hold Story 46.4 Envelope field list for additive `product_session_ref` excluded from fp1. On FEAT-0055 notes: hold Epic 57 handle record for optional `originating_product_session_ref` (CT-46, states unchanged). Leave epics-QMA / pack-and-grant epic files unchanged. Do not mint new FEAT ids.

### 18. major — `docs/knowledge/traceability.md` (feature locator)

**Finding.** Inventory-derived waves (wave = 1 + max blocker): FEAT-0065=10, FEAT-0066=11, FEAT-0067=12, FEAT-0068=12, FEAT-0071=19 (via FEAT-0055 derived 18). The locator UI table lists FEAT-0066 as wave 12, then lists FEAT-0067 and FEAT-0068 as wave 12 while naming FEAT-0066 as a blocker (same-wave-as-blocker). The same file lists FEAT-0055 as wave 22 (Workflows table) while FEAT-0071 blocked_by FEAT-0055 is wave 19. Header: “Feature locator — 56 entries” while `stage_state` / `validate_inventory` report 71 features. Intro lists FEAT-0058–FEAT-0063 and FEAT-0064–FEAT-0071, but there are no `| FEAT-0058 |` .. `| FEAT-0063 |` rows. UI table starts at FEAT-0064 wave 12 blocked_by FEAT-0058, so those waves cannot be checked in-docs.

**Lenses.** features (major ×2). Same locator.

**Contradicts.** Inventory graph; the same file’s other wave rows.

**Fix.** Header 71 entries. Insert a FEAT-0058..0063 wave table matching inventory (0058=11, 0059=12, 0060=12, 0061=19, 0062=17, 0063=20) before the UI table. Set FEAT-0066 wave to 11. Keep 0064=12, 0065=10, 0067=12, 0068=12, 0069=13, 0070=12, 0071=19. Either restamp FEAT-0051..0057 waves to inventory-derived numbers (0055=18 so 0071=19) or note that QMA 0040..0046 remain build-order while every later row is `validate_inventory`-derived. Do not mint duplicate feature ids.

### 19. major — `docs/lenses/ui/design-system.md`

**Finding.** Density mentions a narrow rail and a substantial Copilot column. `docs/lenses/ui` has no matches for Settings, divider, or opened-app. SCN-0034 Given: Home, Copilot, Library, Authoring above the divider; Worked numbers: four named product destinations plus Settings chrome; opened-app icons stay below.

**Lenses.** screens-index (major).

**Contradicts.** DEC-0470, DEC-0474.

**Fix.** Add a Rail section: four destinations above the divider (Home, Copilot, Library, Authoring); Settings is chrome not a fifth product destination; opened-app icons below; WidgetFrame expand/return is not a rail destination.

### 20. major — `docs/lenses/ui/screens/library.md`

**Finding.** Callbacks: `onStageFile` → authenticated PUT `/artifacts/stage`; `onCite(fp1, provenance)`; `onTransfer` only when destination is recorded reachable TLS. Error: interrupted PUT refused; no partial fp1. No matches for `transfer_complete`, `source_unreachable`, or `stage_max_bytes`.

**Lenses.** screens-index (major).

**Contradicts.** DEC-0488, DEC-0497, SCN-0032, GAP-0110.

**Fix.** Add `onTransferComplete` as dest-authored `transfer_complete`; typed `source_unreachable` for loopback-only remote; invoke refused until the ticket is complete; PUT refuses when `registry:artifact.stage_max_bytes` is unset (mint no number).

### 21. major — `docs/index.md` (corpus claim)

**Finding.** “The corpus contains 157 files: 109 Markdown documents and 48 YAML artifacts. Every file is linked once below.” Linked Markdown is 108 (6 root + 2 architecture + 21 components + 26 ADRs + 35 scenarios + 1 knowledge/traceability + 17 lenses). `docs/research/codex-code-review-comparison.md` exists (`type: knowledge`, `status: reviewed`). The index has no match for that path or `docs/research`.

**Lenses.** screens-index (major).

**Contradicts.** The same page’s “every file is linked once” sentence. Prefold: do not fold `research/` as law.

**Fix.** Either link the research note under knowledge as not live law, or drop it from the count (108 Markdown, 156 files) and keep the every-file-linked sentence true.

### 22. major — `docs/lenses/ui/screens/home.md` (and rail peers)

**Finding.** Grep of `docs/lenses/ui/**/*.md` for CT-40|CT-46|CT-48 returns no matches. home.md Data in: running JobHandles; mailbox rows for Home chat keyed by `product_session_ref` (DEC-0484). Callbacks: `dispatchChat`; `dispatchCancel` when `originating_product_session_ref` is present. Lens catalog requires data consumed (contract references).

**Lenses.** screens-index (major).

**Contradicts.** Lens catalog (screens must cite contracts they consume).

**Fix.** On home.md cite CT-48 `product_session_ref` (excluded from Envelope fp1) and CT-46 `originating_product_session_ref` (not CT-42). On copilot.md cite CT-48/CT-40 `send_message`. On widget-frame.md keep ActionContext as host-minted, not a store fetch.

### 23. major — `docs/scenarios/SCN-0029-origin-revoke-vs-renew.md` through `SCN-0035-*.md` (banner); especially `docs/scenarios/SCN-0030-recover-control.md`

**Finding.** SCN-0028 Given cites DEC-0507 and says this scenario is specification. SCN-0029 Given is “An Origin has a live `pairing_proof` P1” then When runs `POST /pair/renew` and `qmb host pair revoke --origin`. Same missing banner on SCN-0031–SCN-0035 (`Envelope` persists `product_session_ref`, `list_mailbox`, PUT `/artifacts/stage`, rail chrome, `cancel_job`). Older SCN-0018–SCN-0027 all open with specification-of-intended-behavior. SCN-0030 Given/When narrates `qmb host recover-control` then `qmb host start` with no DEC-0507 and no “this scenario is specification.” ADR-0026 ABSENT list includes `qmb host` and `host_control` / recover-control.

**Lenses.** honesty (major ×2).

**Contradicts.** DEC-0507; DEC-0286; the SCN-0028 banner pattern. SCN-0030 is the banned live-`qmb-host` reading.

**Fix.** Copy the SCN-0018/SCN-0028 banner onto SCN-0029–SCN-0035: specification, not inspect proof; pairing, `qmb host`, `list_mailbox`, `cancel_job`, PUT, and Svelte chrome are absent at `integration@34c148be` (DEC-0507); class/test existence is not e2e (DEC-0286).

### 24. major — `docs/components/qma-core.md`

**Finding.** No GAP-0081, GAP-0114, Svelte, or DEC-0280 chrome sentence in `qma-core.md`. `qml.md` already has the restamp. The DEC-0280 locator points at `qma-core`, which has no rung-4 restamp. The UI increment section states PackUiRequest ingested at enable, `copilot_profile` stays Epic 60 sibling, drafts live as artifact bytes plus `editor_draft_head`, with no DEC-0507 / `34c148be` sentence. `PluginManifest.copilot_profile` is on the DEC-0507 ABSENT list.

**Lenses.** zombie-chrome (major); honesty (minor on PackUiRequest). The component restamp is the required annotation; the locator is filed under minors.

**Contradicts.** DEC-0280 restamp (DEC-0509 / GAP-0114); DEC-0507 ABSENT (`copilot_profile`, `get_pack_ui_request`, draft save/publish/head).

**Fix.** One dated note: rungs 1–3 bind; chrome answered DEC-0509; remaining `qma-ui-contract` types GAP-0114; no `ui_view`. Add DEC-0507: those UI increment surfaces are absent at `34c148be`; keep DEC-0465 type-existence.

### Minor

### 25. minor — frontmatter `decisions` / `depends_on` / `sources` not extended

Bodies cite DEC-0469..DEC-0510; YAML lists often stop earlier.

| Doc | Evidence |
|---|---|
| `docs/architecture/overview.md` | mermaid is Svelte; `decisions` end at pack-and-grant (through DEC-0465) |
| `docs/components/qmb.md` | `decisions` end at DEC-0450; prose cites DEC-0494/0492/0503/0478/0507 |
| `docs/lenses/security/security-model.md` | `depends_on` omits COMP-QMB; `decisions` end at DEC-0286 |
| `docs/components/qma-daemon.md` | `decisions` end at DEC-0465; body cites DEC-0491..0507 |
| `docs/constitution.md` | L7/L31 cite DEC-0504/0505/0478; frontmatter ends at DEC-0462 |
| `docs/contracts/ct-40-qma-wire-envelope.yaml` | `decisions[]` omits DEC-0492/0502/0491/0494; `gaps` omits GAP-0110 |
| `docs/index.md` | `sources` stop at architecture-QMX-2026-09-18; body cites ADR-0026 |
| `docs/lenses/ui/design-system.md` | `depends_on` repeats its own `COMP-QMA-WIRE` |

**Lenses.** zombie-chrome, host-control, contracts, screens-index, parent-amendments (minors).

**Fix.** Append the DECs / COMP-QMB / SRC-27/SRC-28 / rider each body actually cites. Point design-system `depends_on` at peers (COMP-QMA-DAEMON) or leave empty; keep `component: COMP-QMA-WIRE`.

### 26. minor — DEC-0333 / DEC-0280 locators and `qma-wire` Related footer

`docs/knowledge/traceability.md`: DEC-0333 locator still points only at ADR-0020 / qma-wire with no chrome answer; DEC-0280 locator points at `qma-core`, which has no rung-4 restamp (`qml.md` does). `docs/components/qma-wire.md` Related-footer DEC-0333 gloss still says the UI extension SDK is deferred after the body restamped chrome.

**Lenses.** zombie-chrome (minor ×3); parent-amendments (minor, qma-wire footer).

**Fix.** Gloss DEC-0333 as wire/registry bind now; chrome answered DEC-0509; leftover types GAP-0114. Point DEC-0280 at `qml.md` and ADR-0026.

### 27. minor — `docs/contracts/ct-40-qma-wire-envelope.yaml` (`consumers` comment)

`consumers: []` comment still: every client (the **out-of-scope UI**, non-plugin workers …). `intended_consumers` already names the Svelte host (DEC-0505).

**Lenses.** zombie-chrome (minor).

**Fix.** Say Svelte host / non-plugin workers / language adapters. Do not call chrome out-of-scope.

### 28. minor — `_docwork/gaps.yaml` (GAP-0100 recommendation)

Status is answered; answer cites DEC-0509. Recommendation still: “UI chrome, not this epic set. … GAP-0081 chrome stays deferred.”

**Lenses.** zombie-chrome (minor).

**Fix.** Park the old recommendation as history. Point current text at Home attention plus kit queries (DEC-0480, DEC-0509).

### 29. minor — `docs/decisions/ADR-0023-qml-research-expansion.md`

Provisional Decision still: “AD-12 / DEC-0392 — json-render / MCP Apps present only. GAP-0081 stays.” Last follow-up is 2026-09-19 Workflows. Do not flip the mill package to accepted.

**Lenses.** zombie-chrome (minor).

**Fix.** Add a provisional follow-up: adapters stay present-only; chrome answered DEC-0509; types beyond stub GAP-0114.

### 30. minor — pairing product-noun leftovers

| Location | Evidence |
|---|---|
| `docs/glossary.md` `pairing_record_id` | Not distinguished from CT-28 `pairing_record` (BMS demo-account link) |
| `docs/glossary.md` `pairing_proof` | Forbidden homes listed; never names sessionStorage or in-memory as allowed home |
| `docs/components/qma-daemon.md` pairing paragraph | Uses `pairing_proof` / `pairing_record_id`; omits Bearer `pairing:<proof>` and `qmx.pair.<proof>` |
| `docs/decisions/ADR-0026-ui-host-and-backend-delta.md` blast radius | Lists CT-40, CT-42, CT-48; omits CT-46 (`originating_product_session_ref`) |
| `docs/components/qma-daemon.md` FM-29 | Unbackticked “pairing proof” instead of `pairing_proof` |
| `docs/registry/variables.yaml` `pairing.session_ttl` | Notes say “Pairing proof lifetime” instead of `pairing_proof` |

**Lenses.** pairing-nouns (minor ×6).

**Fix.** Write the product nouns; add the CT-28 distinction; name CT-46 in blast radius (JobHandle field stays on CT-46, not CT-42).

### 31. minor — host-control index leftovers

| Location | Evidence |
|---|---|
| ADR-0026 host-verbs bullet | Lists start\|status\|stop\|pair\|configure\|rotate-control\|recover-control; omits the two revoke forms (DF-HOST-VERBS) |
| qma-daemon FM-30 Condition | ANDs `host_control` is missing with live recover, then ORs file still readable; unlike qmb FM-13 |
| `qmb.md` recover-control | Writer mechanics cited to DEC-0503; `.daemon_writer` / no-8765 bind is DEC-0494 |
| SCN-0029 | Barrier identity is `journal_seq` R not wall clock; creating-event versus `issued_at`/`recorded_at` is not said (DF-JSEQ-CREATE) |
| bootstrap.md | Covers `qmb host pair <code>` and no cookie set; no OS-owner `qmb host stop` when `host_control` is missing/unreadable (DF-UI-STOP-AUTH) |

**Lenses.** host-control (minor ×5).

**Fix.** Complete the host-verbs index; align FM-30 Condition with qmb FM-13; cite DEC-0494 for the writer and DEC-0503 for trust-root / no-remint / empty-root; state creating-event `journal_seq`; one-line bootstrap setup note for OS-owner stop-when-missing.

### 32. minor — contract annotation leftovers

| Location | Evidence |
|---|---|
| CT-42 enums | `copilot_profile` sibling annotation buried inside the no-`ui_view` enum bullet; PackUiRequest named only there |
| CT-45 | Allowlist categories unchanged; no `pairing_proof` / `host_control` sentence (AM-15 / DEC-0503: do not treat them as broker refs) |
| CT-40 AM-01 byte-channel | “Pairing HTTP and artifact PUT/GET are byte channels, not a fourth family (DEC-0502).” No ticket header, no dest audience, no authenticated GET `/artifacts/<fp1>` with `X-QMX-Transfer-Ticket` |
| `docs/architecture/dependencies.yaml` COMP-QMA-WIRE notes | Correctly refuse COMP-UI; do not record that host-control is outside port 8765 / not a new `depends_on` to COMP-QMB (AM-15) |

**Lenses.** contracts (minor ×4).

**Fix.** Lift a one-line CT-42 invariant for `copilot_profile` / PackUiRequest / closed eight / no `ui_view`. Annotate CT-45 that `pairing_proof` and `host_control` are not `credential_ref` values. Cite DEC-0497/DEC-0502 on the byte-channel invariant. On WIRE and DAEMON notes only: host-control is outside 8765; no new `depends_on` to COMP-QMB; product UI must not import qmb in-process. Do not add a COMP-UI row.

### 33. minor — feature-inventory / locator notes leftovers

| Location | Evidence |
|---|---|
| FEAT-0064 notes | Only “Feeds GAP-0081 / GAP-0100 answered delivery…”. Prefold D1: chrome consumes planned FEAT-0059/0060/0062; `blocked_by` correctly only FEAT-0058 |
| FEAT-0065 / FEAT-0066 In | 0065 has start\|status\|stop\|configure\|rotate-control\|recover-control and the stop exception, no pair. 0066 has “origin-revoke barrier C2” without `qmb host pair` or revoke argv. Pair and both revoke forms have no In-list owner |
| FEAT-0038 notes | “GAP-0062 (host machine) and GAP-0081 (rung 4) stay deferred” after GAP-0081 answered |
| traceability.md Workflows intro | “GAP-0092..GAP-0100 stay deferred and must not be filled in prose.” Same file later restamps GAP-0100 answered with delivery FEAT-0064 |

**Lenses.** features (minor ×4).

**Fix.** FEAT-0064 notes: chrome consumes diagnosis/JSON-lines (0059), host retry (0060), and listing/health (0062) when those planned slices land; do not add them to `blocked_by`. Put pair + revoke argv on FEAT-0066 In (`--origin` = that Origin’s `journal_seq` barrier; `--session` = that `pairing_record_id` only). Keep GAP-0062 deferred; change GAP-0081 rung 4 to answered by FEAT-0064 (DEC-0509); do not fold chrome into FEAT-0038. Write GAP-0092..GAP-0099 stay deferred; GAP-0081 and GAP-0100 are answered UI sitting law delivered by FEAT-0064..0071 and remain out-of-scope as kit holes.

### 34. minor — UI lens / index copy drift

| Location | Evidence |
|---|---|
| `docs/lenses/ui/screens/copilot.md` | Mailbox snapshot keyed by `psess:` instead of `product_session_ref` (session identity remains `psess:` / `product_session_id`) |
| `docs/lenses/ui/screens/authoring.md` | Never states QMA AD-22 RefinementProposal is not the graph/draft store (DEC-0487, DEC-0499, SCN-0033) |
| `docs/index.md` gap-report blurb | Intro records the UI sitting and GAP-0081/0100 answered; the gap-report bullet is still pre-UI (46 gaps answered; QMA GAP-0070..0091 deferred; no GAP-0081/0100 restamp, no GAP-0109..0114) |
| `docs/index.md` CT-46 / CT-48 one-liners | Omit optional `originating_product_session_ref` at UI admit (DEC-0496) and optional `product_session_ref` excluded from fp1 (DEC-0495); SCN pins on the same page already name those fields. Do not put the JobHandle field on the CT-42 line |

**Lenses.** screens-index (minor ×4).

**Fix.** Align those one-liners with the same page’s SCN pins and gap-report.md.

### 35. minor — inspect-honesty leftovers

| Location | Evidence |
|---|---|
| `docs/architecture/stack.md` | UI host stack pins Svelte/SvelteKit/Vite as the product UI seed; no `34c148be` / DEC-0507. Only Node.js is marked unexecuted scaffold (DEC-0510 A13) |
| `docs/components/qma-wire.md` opening | Present-tense “binds NOW: chrome is the 2026-09-25 Svelte host”; DEC-0507 absence is only later (line 167) |
| `docs/architecture/dependencies.yaml` | COMP-QMA-WIRE notes cite `Inspect 34c148be (DEC-0507)` without CONNECT/AMEND/ABSENT; COMP-QMA-DAEMON notes still stop at DEC-0465 / `34c148b` |
| rail screens other than bootstrap | home/copilot/library/authoring describe mailbox rows, `dispatchChat`, and cancel as current screen data with no inspect honesty |
| `docs/gap-report.md` pack-and-grant summary | Attaches DEC-0507 to truncated pin `34c148b`, mixing DEC-0465 and DEC-0507 and inviting a two-SHA reading |

**Lenses.** honesty (minor ×5). qma-core PackUiRequest honesty is folded into finding 24.

**Fix.** One honesty line on stack, qma-wire opening, both dependency notes, and each rail screen. Cite DEC-0507 only with the ABSENT serving/pairing/`qmb host`/Svelte list, not as a second SHA.

### 36. minor — `docs/decisions/ADR-0024-workflows-construction-kit.md` (2026-09-25 follow-up)

Follow-up restamps GAP-0081/0100 and says named pairing/host-control/mailbox-field amendments are AM-01..AM-17 (DEC-0506) and do not rewrite this ADR’s Decision. Decision AD-16 complete sqlite list and AD-17 “not a v1 `ui_view` plugin point until a named GAP-0081 increment” remain, correctly unedited, but the follow-up never maps AM-03/AM-04 onto them.

**Lenses.** parent-amendments (minor). AM-03 silent add on the daemon is finding 2 (critical).

**Fix.** Keep the Decision body unchanged. Extend the follow-up with one line per inherited closed list: AM-03 adds named projections to DEC-0429; AM-04 adds optional `originating_product_session_ref`; GAP-0081 increment is not permission for `ui_view`.

## Checks the lenses did not evidence as defects

Do not re-open these unless a later lens does:

- No `COMP-UI` / sixth COMP row and no `docs/contracts/ct-52*` file.
- No `pairing_session_id` as a live field.
- ADR-0024 / ADR-0025 original Decision text not rewritten (dated follow-up only).
- FEAT-0071 `blocked_by` is FEAT-0055 + FEAT-0066 + FEAT-0041, not FEAT-0067.
- CT-42 correctly has no `originating_product_session_ref`.
- Seed CT-40 9/7/10 families not expanded in `schema.fields` by AM-01.
- JobHandle states remain the parent closed vocabulary in the CT-46 invariant (the missing piece is AM-04 / `handle_id`, not a new state).
- MessageKind / DeliveryState remain closed on CT-48.
- ADR-0023 mill package stays `status: provisional` (finding 29 is a follow-up, not a standing flip).

## Counts

| Severity | Open findings |
|---|---|
| critical | 6 |
| major | 18 |
| minor | 12 |
| **total** | **36** |

## Suggested gate

Treat as **not green** until findings 1–6 (critical) and 7–24 (major) are amended. Findings 25–36 may ride the same desk-fix. The orchestrator stub on this path that recorded pass-with-desk-amendments is not the independent-lens result.

Must-fix (critical + major): drop “the Rust UI included” from the live CT-40 invariant; name AM-03 (including `artifact_transfer_ticket`) against the complete-list; restamp GAP-0081 as answered in AGENTS / gap-report intro / SCN-0013; named-amend CT-40/qma-wire broker-ref and unauthenticated-bind; stamp CT-46/CT-48 `wiring_status` DEC-0507 AMEND-absent; add overview DEC-0507 honesty; dated ADR-0020/0022 follow-ups; fold pairing nouns and DEC-0501 homes on bootstrap and security-model; fold recover-control writer fence; fold origin-revoke argv; name AM-10 `COMMAND_GROUPS` / T-H-03 / B-1; named-amend AD-26 `pairing.session_ttl`; add CT-40 initialize, AM-12, AM-04/`handle_id`, and CT-48 replies-inherit; named holds on FEAT-0041/0045/0055; fix locator waves and FEAT-0058..0063 table; rail geometry; library transfer/stage_max_bytes; index every-file-linked; UI screen contract cites; SCN-0029..0035 specification banners; qma-core rung-4 + DEC-0507 note.
