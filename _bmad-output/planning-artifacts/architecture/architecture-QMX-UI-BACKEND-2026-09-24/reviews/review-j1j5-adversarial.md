---
review: adversarial-j1j5
target: architecture-QMX-UI-BACKEND-2026-09-24
amended_spine: AD-1..AD-17 plus PAIRING/HOST/MAILBOX/CANCEL/ARTIFACTS/PACK-UI
reconciled_ui: architecture-QMX-UI-2026-09-23
date: 2026-09-24
inspect: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20
lens: 'Two factory units, every live AD to the letter, still incompatible on shared-data shapes, two owners of one entity, or conflicting mutation paths. Historical first-pass reviews are evidence, not law. Implementation-level DTO field lists stay downstream.'
status: sitting-candidate — not operator-accepted
tests: unexecuted
---

# Adversarial review — J1–J5 amended spine

## Method

Build **two factory units** one level down from this sitting (stories / builders). Both obey every **live** local AD (backend AD-1..AD-17), the companions those ADs name, named amendments AM-01..AM-16, and inherited parent / kit / QMA / UI law the spine already binds. They still cannot share a daemon, a wire, or a journal.

A pair is a hole only when **both readings are literal**. Stale first-pass reviews (`reviews/review-adversarial.md` and the 2026-09-24 as-reviewed packet that still named `pairing_session_id` and CT-40 `confirm_pair`) are not current law. Inspect types at `34c148be` are evidence of the substrate, not delivery. Implementation-level DTO field lists, token entropy, numeric TTL, and ordinary supervisor PID/signal mechanics are **out of this gate** (joint brief; `CLOSURE-J1-J5.md` remaining deferrals).

Closed slogans are credited. Remaining joints are the findings.

## Verdict

**Return remaining High holes. Do not treat J1–J5 as factory-unambiguous.**

The amendment **did** bind the slogans the joint review demanded: host-control instead of a dummy operator `cred://` for pairing; `pairing_proof` vs `pairing_record_id` with hash-only journals; daemon-issued `editor_draft_id`; named `publish_editor_draft`; typed `source_unreachable` plus dest-authored `transfer_complete`; mailbox principal check; optional `originating_product_session_ref`; `_ref` names. Origin-only issuance stays closed.

What remains is that several closed nouns still have an **unbound joint**. Two units can obey every AD as written and still ship clashing identities, two owners of one row, or two mutation paths for the same event. That is the hole.

| Axis | Slogan closed? | Remaining High joint |
| --- | --- | --- |
| J1 first operator | **Yes** as a path name (OS user + `host_control`, not provider login) | Operator principal has no AM-03 projection; CT-40 dummy `cred://`+`principal_class=operator` still authenticates; lost-token vs rotate; AD-26 `variable.set` vs host-control TTL |
| J2 pairing custody | **Yes** as two names + hash-only + confirm-once table | Concurrent `/pair/confirm` not under first-append-wins; renew/revoke loser is “no-op **or** typed refuse”; `pairing_record_id` mint time; “unclaimed” pending |
| J3 draft issuer | **Yes** as daemon-on-first-save | First-save coalescer is three keys; ownership unnamed; PUT→save window vs Library facade |
| J4 publication | **Yes** as a named command + AD-30 enable | “Local authoring pack” has no identity; two writers of `graph_template`; UI stored-verdict vs daemon rerun |
| J5 transfer | **Yes** as refusal class + dest ack name | Who records TLS origin; which daemon’s `complete` bit is the invoke gate; dest→source write under “never dials in” |
| Small | Names reconciled | Mailbox “principal” is inspect `PrincipalClass`; UI-vs-headless admit discriminator missing |

Tests remain unexecuted. Inspect SHA is unchanged. Candidate ≠ operator acceptance.

---

## Closures that hold (do not reopen)

Live law, not the as-reviewed packet:

- **R2 / AD-3.** A remembered Origin never issues a new `pairing_proof`. Path 1 is `qmb host pair <code>` then `POST /pair/confirm`. Path 2 is authenticated `POST /pair/renew` with an unexpired unrevoked proof + matching Origin. Cookies / `Set-Cookie` / `localStorage` of the proof are refused.
- **AD-5 / AM-09.** Pair/revoke/TTL/bootstrap are **local host-control**, “not CT-40 `confirm_pair` with a broker ref.” Addable CT-40 commands are `cancel_job`, `transfer_artifact`, `transfer_complete`, `save_editor_draft`, `publish_editor_draft`. There is no JSON-RPC `stage_artifact`.
- **AD-4 / J2 names.** `pairing_proof` is an RFC 6750 bearer returned **once**. `pairing_record_id` is the nonsecret row. Journals store `proof_fp1` only. Lost confirm → re-pair, no journal retrieval of the raw proof. Expiry and revoke **close** sockets that presented that proof. Renew **rotates** (new proof, old `proof_fp1` revoked, old WS closed).
- **AD-5 / AM-11.** Browser-paired `AuthenticatedWireSession` carries `principal_class=operator` and `pairing_record_id`; it does **not** populate `credential_ref` and does not pass the proof to `parse_credential_ref`. Machine/worker clients still present `credential_ref` (Story 41.4).
- **AD-7.** `send_message` is mailbox, not `InvocationEnvelope`. Delivery owner is Epic 46 / Story 46.4. Envelope field is `product_session_ref` (excluded from Envelope fp1). Own identity of the session row stays `product_session_id` (AM-14).
- **AD-8.** `handle_id` **is** `job_id`. UI cancel is starter-only via `originating_product_session_ref` when present. Headless omits the field. States unchanged. Not `stop_run`.
- **AD-9.** PUT `/artifacts/stage` then explicit `transfer_artifact`. Default loopback is typed `source_unreachable`. No silent local fallback. Dest authors `transfer_complete`. Invoke on **that placement** refuses until ticket `complete`.
- **AD-11.** Daemon is the sole durable `editor_draft_id` issuer. First save **omits** the id. Parent AD-30 enable remains compile identity. Drafts are not QMA AD-22 `RefinementProposal` (AM-07).
- **AD-10 / AM-16.** `get_pack_ui_request` by `instance_id` + `availability_revision`. `PluginManifest.copilot_profile` stays Epic 60 sibling.
- No sixth COMP. No new CT. No UI BFF. No Documentation Factory from this sitting.

Inspect honesty in the companions is accurate: `/pair/*`, `list_mailbox`, `cancel_job`, PUT path, `transfer_artifact`, `originating_product_session_ref`, `product_session_ref`, `qmb host`, `host_control` are **absent** at `34c148be`. `DaemonProcess._handle_client` still discards TCP bytes. `authenticate_before_protocol` is a shape gate on required `credential_ref`. That last fact is why AM-11 exists, and why AM-11 is still not enough to join authorization.

---

## J1 — First operator trust root vs CT-40 vs dummy `cred://` vs `host_control` recovery

### Live law

Backend AD-17:

> Trust root is the **OS user who owns `QMA_DAEMON_ROOT`** plus a daemon-minted **`host_control` token** stored under that root with owner-only ACL. The channel is loopback-only and is **not** the CT-40 listener … `qmb host start` on an empty root: acquire lock, mint the first operator principal (journal), mint `host_control`, refuse pairing issue until `qmb host configure pairing-ttl` has written the registry row. Proof verification: QMB must present the current `host_control` token from that root; a forged `credential_ref` / caller-selected `principal_class` is not proof … Recovery: stop, same OS user, same root, start — principal remains; rotate `host_control` via `qmb host` on that root.

Backend AD-5:

> QMB pair/revoke/TTL/bootstrap use the **local host-control channel** (AD-17), not CT-40 `confirm_pair` with a broker ref. … Browser-paired `AuthenticatedWireSession` carries `principal_class=operator` and `pairing_record_id`; it does **not** populate `credential_ref`.

HOST-LIFECYCLE recovery / rotate:

> Same OS user, same root, start: principal remains; `qmb host rotate-control` mints a new token and invalidates the old.
> `qmb host rotate-control` — New host_control token. Does not: Change operator principal.

AM-03 named projections: `pairing_pending`, `pairing_session`, `editor_draft_head`, `artifact_transfer_ticket`. Spine consistency table (same file): “Pairing records, mailbox, draft head, transfer tickets, **operator principal** are journal projections.”

QMA AD-24 transport custody (inherited, amended only as named):

> The daemon authenticates before protocol bytes and never offers an unauthenticated bind. The client credential is itself a broker-resolved reference.

Story 41.4 (still planned, hold only the unauthenticated-bind sentence per DEPENDENCY-MAP):

> a Credential-Broker-resolved credential has authenticated it first and the contract carries only the credential reference.

Inspect `AuthenticatedWireSession` (`qma-wire` `auth.py`): required `credential_ref: CredentialRef`, `principal_class`, `authenticated_before_protocol`. Inspect tests authenticate `cred://models/openai` with `principal_class="operator"` and `cred://operator/ui` with `principal_class="operator"`. `parse_credential_ref` is a shape gate. The broker allowlist is `models|inference|compute|sandbox|corpus|knowledge|telemetry/` — no operator-login family (AD-12 / AM-15: **not** widened).

QMA AD-26:

> A `registry`-homed value is set only by an `operator`-principal wire command (AD-24) recording a `variable.set` journal event.

AD-4 TTL: `registry:pairing.session_ttl` “must be set on the local-control path (AD-17) before first issue.”

### Two units

Shared, both units: empty per-user root → `qmb host start` mints something called “operator principal” plus a `host_control` file; pairing HTTP refuses issue until TTL is configured over host-control; browser never presents `cred://` as `/pair/*` login; forged `cred://models/…` as pairing login is refused (T-P-08 / T-BE-23); QMB pair is host-control, not CT-40 `confirm_pair`.

**Unit A — host-control is the only operator door; dummy CT-40 operator is dead.**

- Empty start: daemon process (sole writer) appends a journal projection `operator_principal` (new name, not on AM-03) and writes `$QMA_DAEMON_ROOT/host_control`. QMB reads the file after spawn. Subsequent host verbs present that token on a loopback channel that is not port 8765.
- CT-40: `principal_class=operator` is accepted **only** after Origin+`proof_fp1` table match (browser) or an equivalent host-control-issued operator session. `authenticate_before_protocol("cred://operator/ui", principal_class="operator")` is refused. `cred://models/openai` + `principal_class="operator"` is refused. Headless `qmb` invoke uses host-control or a pairing_proof QMB obtained locally; it does not use Story 41.4 shape-gate operator.
- Lost `host_control` file: `start` on the same root does **not** remint (principal remains, token missing). `rotate-control` requires the current token, so it cannot run. Recovery is QMA AD-27 restore of a tree that included the file, or wipe the root.
- TTL: host-control `configure pairing-ttl` is the **only** writer of `registry:pairing.session_ttl`. Later CT-40 `variable.set` of that key is refused (special-cased off AD-26).

**Unit B — host-control is the pairing bootstrap; Story 41.4 operator CT-40 remains.**

- Empty start: QMB sets `QMA_DAEMON_ROOT`, spawns `python -m qma.daemon`. Daemon mints `host_control`. “Operator principal” is the inspect `PrincipalClass.OPERATOR` token, not a new row. AM-03 is not extended. Pairing_session later copies `principal="operator"`.
- CT-40: Story 41.4 still authenticates with a credential_ref before protocol. Headless `qmb` presents `cred://operator/ui` (or any opaque ref that survives `parse_credential_ref`) with caller-selected `principal_class=operator`, as inspect tests already do. That is not `/pair/*` login, so T-P-08 does not fire. AD-17’s “forged credential_ref is not proof” is read as a **host-control** rule only. Browser pairing still maps to class `operator`. Dummy `cred://` is now an operator wire identity that never touched `host_control`.
- Lost `host_control` file: AD-17 recovery sentence “stop, same OS user, same root, **start** — principal remains” is read as: `start` notices the missing token, remints `host_control` because OS-user ownership of the root **is** the trust root. `rotate-control` is the explicit path when the old token is still present.
- TTL: host-control writes the first value (required before pairing issue). After a browser is paired, CT-40 `variable.set` on `registry:pairing.session_ttl` also writes the same row (AD-26 letter). Two mutation paths.

### Why both are literal

- AD-17 names OS user + token + “mint the first operator principal (journal)” and never names the projection. AM-03 was invented so “not a new sqlite class” would still satisfy Story 42.2 / QMA AD-6. Operator principal is claimed as a journal projection in the spine consistency table and **omitted** from AM-03. Unit A adds the missing name. Unit B reuses inspect `PrincipalClass`.
- AD-5 / AM-11 close **browser** `credential_ref`. They explicitly keep Story 41.4 for machine/worker clients. They do not say headless QMB operator CT-40 is gone. QMA AD-24 still says the operator class “comes only from an interactive human credential presented by a client a human is driving” — Unit B treats `cred://operator/ui` + caller-selected class as that credential; Unit A treats host-control / pairing_proof as the only human credential.
- AD-17 recovery names both `start` (principal remains) and `rotate-control` (new token). HOST-LIFECYCLE rotate “Does not: Change operator principal.” Neither sentence says whether a **missing** token file is reminted on start. Rotate, as specified, needs the current token (`Proof verification: QMB must present the current host_control token`).
- AM-10/AM-15 put TTL on host-control. They do not amend QMA AD-26’s sole `variable.set` writer for registry-homed rows. `registry:pairing.session_ttl` is registry-homed by its name.

### Holes

**H-J1-PRINCIPAL — two owners of “the operator.”** Unit A’s journal row is a person. Unit B’s `principal` is a class. Mailbox AD-7, cancel AD-8, and pairing_session “operator principal” all compare “the connection’s operator principal” to “that session’s durable principal.” After this fork those strings are different types. T-BE-08 (“operator A writing B’s session”) is unsatisfiable on Unit B (there is only class `operator` per daemon) and requires the missing AM-03 row on Unit A.

**H-J1-DUMMY — CT-40 dummy `cred://` bypasses the trust root.** Unit B ships a legal Story 41.4 operator session that never presented `host_control`, never configured TTL, and never paired. It can `send_message` / invoke / create `psess:` as `principal_class=operator`. J1’s negative traces only refuse forged refs **as login** and remote callers **without host_control** on the pair/configure path. They do not refuse inspect’s `authenticate_before_protocol("cred://models/openai", principal_class="operator")`.

**H-J1-TOKEN — lost `host_control` is two recoveries.** Unit A locks the operator out until backup/wipe. Unit B remints on start from OS ACL. Both cite AD-17 recovery. QMA AD-27 backup contents are journal, ledgers, artifact, staging, telemetry — **not** the `host_control` file. After an honest restore, Unit A and Unit B still disagree.

**H-J1-TTL — two writers of `registry:pairing.session_ttl`.** Host-control configure (AD-17) and CT-40 `variable.set` (QMA AD-26) are both legal unless one is named as the sole writer. Missing TTL refuses **issue**; it does not say a later `variable.set` is illegal. Rolling renew lifetime is “now + configured TTL”; whoever last wrote the row owns every live session’s remaining life.

**Not a High fork (DTO / deferred).** Loopback host-control being a UDS vs a loopback TCP port vs a file-in-the-root protocol; token entropy; exact TTL duration; stale-PID lock recovery (HOST-LIFECYCLE already defers this).

### Required bind (one sentence each)

1. Name the operator-principal journal projection in AM-03 (or explicitly say the inspect `PrincipalClass` token **is** the durable principal and T-BE-08 is cross-daemon only).
2. State whether CT-40 `principal_class=operator` is legal **without** a pairing table match / host-control session. If no, Story 41.4 / inspect `authenticate_before_protocol` must be amended, not only `/pair/*`.
3. Lost `host_control` file: remint on start, or refuse until restore/wipe. Rotate remains the live-token path.
4. Sole writer of `registry:pairing.session_ttl`: host-control only, or host-control **plus** `variable.set` after an operator exists. One path.

---

## J2 — `pairing_proof` vs `pairing_record_id`; confirm retry; renew vs revoke; what is stored; WS expiry

### Live law

AD-4: `pairing_proof` bearer; `pairing_record_id` nonsecret; journal stores `proof_fp1` only; expiry **closes** sockets that presented that proof; renew **rotates**.

PAIRING lifecycle table (live):

| Event | Durable result |
| --- | --- |
| `POST /pair/start` | New `pairing_pending` `{pending_id, code_fp1, origin, expires_at}` |
| `qmb host pair <code>` | Pending `confirmed_at`; does **not** issue proof |
| `POST /pair/confirm` first time | Mint proof; store `proof_fp1` + `pairing_record_id`; pending **consumed** |
| `POST /pair/confirm` retry same pending | Typed `already_issued` — **no second proof** |
| Lost confirm | Unrecoverable; re-pair |
| `POST /pair/renew` | **Rotate:** new record+proof; old `proof_fp1` revoked; **close** WS that offered the old subprotocol |
| Lost renew | New proof issued, old revoked; unrecoverable for both if client has neither |
| TTL elapsed | Record expired; **close** WS on that proof; HTTP Bearer refuses |
| `pair revoke --origin` | Journal-ordered cutoff: all sessions and **unclaimed** pendings for that Origin with `issued_at`/`created_at` ≤ cutoff are revoked/deleted |
| Concurrent renew vs revoke | First durable journal append wins. Loser is **no-op or typed refuse** against the new head |
| Daemon restart | Hashes and principals reload; still-valid proofs work until TTL |

AD-14: same-tab reload restores `pairing_proof` (and may restore `pairing_record_id`). Cold start: empty storage; `/pair/renew` impossible; new pair needs QMB confirm. Lost `/pair/confirm` response: proof unrecoverable.

### Two units

Shared: confirm returns `{pairing_record_id, pairing_proof, expires_at}` **once**; retry is `already_issued`; journals never store raw proof; renew rotates and closes old WS; expiry closes WS; Origin-only issuance refused.

**Unit A — pending_id becomes pairing_record_id; confirm is serialized; revoke beats in-flight renew as typed refuse; “unclaimed” = not QMB-confirmed.**

- `pairing_record_id` **is** `pending_id` after confirm (same row, status change). `qmb host status` pending/bound record ids are one namespace. Renew mints a **new** `pairing_record_id` (table: “new record+proof”).
- Two in-flight `POST /pair/confirm` on the same pending: journal append is the consume. Second sees consumed → `already_issued` with `pairing_record_id` in the error body (nonsecret) so the UI can show “this pending is spent, re-pair.”
- Concurrent renew vs origin-revoke: if revoke’s cutoff `issued_at ≤ now` lands first, renew is **typed refuse** (old proof already revoked). If renew lands first, the new row’s `issued_at` is ≤ the revoke cutoff, so the just-issued proof is also cut. Operator who renews then immediately revokes the Origin kills both.
- “Unclaimed pendings” = rows without `confirmed_at`. A QMB-confirmed, unconsumed pending **survives** origin revoke; `/pair/confirm` still returns the one proof.

**Unit B — pairing_record_id is minted at confirm; confirm is not under the concurrent row; loser is silent no-op; “unclaimed” = not yet consumed by confirm.**

- `pending_id` and `pairing_record_id` are different types. Status may list pending ids; revoke `--session` takes only `pairing_record_id` (HOST: `pair revoke --session <pairing_record_id>`). A confirmed-unconsumed pending cannot be session-revoked by id because no `pairing_record_id` exists yet.
- Two in-flight confirms both read “unconsumed,” both mint proofs, both store distinct `proof_fp1` + `pairing_record_id`. The table’s concurrent row names **renew vs revoke**, not confirm. AD-4 “proof once” is read as once **per successful HTTP response**, not once per pending. T-P-03 (“second confirm → `already_issued`”) is the retry-after-response case, not the in-flight race.
- Concurrent renew vs revoke: loser is **no-op** (table allows “no-op or typed refuse”). Client of a no-op renew may still hold the old proof in `sessionStorage` and believe it renewed; the WS may already be closed by the winner. Client of a no-op revoke believes the Origin is dead; a winning renew just issued a new proof.
- “Unclaimed” = not consumed by `/pair/confirm`. Origin revoke deletes QMB-confirmed pendings too. `/pair/confirm` after origin revoke is `already_issued` or missing pending — either way no proof. Unit A would still issue.

### Why both are literal

- The table lists `pairing_record_id` only on the confirm-success row, not on start. HOST status speaks of “pending/bound **record ids**.” Both a renamed pending_id and a new UUID satisfy those sentences.
- First-append-wins is specified **only** for “Concurrent renew vs revoke.” Confirm consume is “pending **consumed**” with no serialization sentence. T-P-03 is “Second confirm same pending → `already_issued`” — a sequential retry, not two requests in flight.
- “Loser is no-op **or** typed refuse” is an explicit disjunction in live law.
- “Unclaimed pendings” is undefined. Confirmed-unconsumed is a real state (`confirmed_at` set, proof not minted).

### Holes

**H-J2-CONFIRM — two in-flight confirms can mint two proofs.** Unit B is AD-legal because the concurrent row does not mention confirm. That reopens J2’s original “approved pending issues repeatedly” defect for the only race that matters (the browser and a local attacker both POST confirm after QMB pair). `/pair/confirm` is **unauthenticated** (AD-5). Origin header match is required; a non-browser local caller can spoof Origin.

**H-J2-RACE — renew vs revoke has two specified outcomes.** “No-op or typed refuse” is not a bind. Combined with origin-revoke `issued_at ≤ cutoff`, a renew that committed 1ms before revoke is either a live proof (if cutoff is exclusive of the new row, which the table does not say) or immediately dead (if `≤` includes it). Two units will ship both.

**H-J2-ID — `pairing_record_id` mint time is two shapes.** Revoke `--session`, status, traces, and UI diagnostics all key on that id. Unit A can revoke a confirmed-unconsumed pending by the pending id. Unit B cannot. Renew “new record+proof” is a third mint. Lost-confirm recovery is re-pair in both; the diagnostics the operator sees are not the same object.

**H-J2-UNCLAIMED — origin revoke either leaves or kills confirmed-unconsumed pendings.** That is the window between `qmb host pair` and `POST /pair/confirm`. The whole point of splitting those two steps (HOST: “does **not** issue proof; page still confirms”) is that window.

**WS expiry is not a remaining High fork.** Live table says TTL elapsed **closes** WS and Bearer refuses. T-P-05 / T-BE-04 agree. Timer-close vs close-on-next-frame is implementation as long as an expired proof cannot issue another command (original J2 required result). Credit the amendment.

**Restart is not a remaining High fork.** “Hashes and principals reload; still-valid proofs work until TTL” plus “raw proofs not in sqlite” is one outcome. Lost confirm stays unrecoverable.

**Not a High fork (DTO / deferred).** Proof token charset/entropy (CLOSURE-J1-J5 already defers this, requiring only unguessable + RFC 6455 token-safe); whether `already_issued` JSON includes `pairing_record_id`; whether `sessionStorage` holds the record id (AD-14 “may”).

### Required bind

1. Concurrent `/pair/confirm` on one pending: first journal consume wins; second is `already_issued`; **no second `proof_fp1`.** Put it in the lifecycle table next to renew-vs-revoke.
2. Pick **one** loser outcome for renew vs revoke (typed refuse, not no-op). State whether origin-revoke cutoff includes a renew that already appended.
3. When `pairing_record_id` is minted (confirm vs rename of `pending_id`). One namespace for status/revoke.
4. Define **unclaimed**: no `confirmed_at`, or not consumed by confirm.

---

## J3 — First save omit id vs `client_draft_correlation` vs subsequent CAS

### Live law

Backend AD-11:

> Saved drafts are artifact-store bytes plus journal projection `editor_draft_head`. `editor_revision` **is** that content fp1. **Daemon** is the sole durable `editor_draft_id` issuer. First `save_editor_draft` **omits** `editor_draft_id`; `expected_revision` is empty; optional `client_draft_correlation` makes lost-ack retry return the same durable id. Result is `{editor_draft_id, editor_revision}`. Subsequent saves require durable id + `expected_revision` = current head fp1.

PACK-UI draft table: lost first-save ack retries with the **same** `client_draft_correlation` **and same bytes** → same durable id + fp1; no second working copy. Stale CAS → typed conflict; head unchanged. Library facade excludes these blobs.

CLOSURE-J3 negative: “First save that *supplies* a client-minted durable id is not the issuer path.”

UI AUTHORING 2.1a (live, reconciled):

> Duplicate `command_id` with same payload → prior durable result (parent AD-29). Different payload on the same id refuses.

Parent AD-29 `command_id` namespace is `(product_session_id, principal, command_id)`.

### Two units

Shared: first save omits `editor_draft_id`; daemon returns `{editor_draft_id, editor_revision=fp1}`; subsequent saves CAS on `expected_revision`; two restored clients at R1: first save wins, second conflicts (T-R5-07 / T-BE-17).

**Unit A — correlation is the first-save coalescer; `command_id` is a second key; omitted correlation mints a new draft; client-supplied id is ignored; ownership is the operator principal; PUT bytes are ordinary artifacts until `save_editor_draft`.**

- Lost-ack retry **requires** the same `client_draft_correlation`. Same correlation + **different** bytes → journal-lifetime collision refuse (AM-12 shape, applied to drafts). Omitted correlation: every retry is a new `editor_draft_id` (two working copies; T-BE-17 “no two working copies” is read as “when correlation is present”).
- AUTHORING 2.1a `command_id` is **also** required (parent AD-29). First save therefore has two coalescers. They can disagree: same correlation, different `command_id` → Unit A returns the correlated id and also stores a second command row; same `command_id`, different correlation → parent AD-29 duplicate vs AD-11 new draft.
- First save that supplies `editor_draft_id`: ignore the client field and mint a daemon id (CLOSURE “not the issuer path,” not “refuse”).
- `publish_editor_draft` “ownership of `editor_draft_id`” = connection principal equals the principal recorded on `editor_draft_head` at first save. No `product_session_ref` on the head (AM-03 does not name one). Any paired tab of that operator can publish any draft.
- `PUT /artifacts/stage` of draft bytes uses the AD-9 Home-attach path. Between PUT and `save_editor_draft`, the fp1 is a Library ArtifactHit. Facade exclusion starts when the head row exists.

**Unit B — content fp1 coalesces first save even without correlation; `command_id` is not on this command; client-supplied id is typed refuse; ownership is a `psess:`; PUT is draft-namespace and never a Library hit.**

- Lost-ack retry with same bytes returns the same id whether or not `client_draft_correlation` is present (content-addressed working copy; AD-11 “optional”). Same correlation + different bytes → typed conflict (not last-writer-wins; first save has empty `expected_revision`, so this is a new rule Unit B invents to avoid two copies).
- `save_editor_draft` is not a parent-AD-29 mutate of `product_session`. CHAT already forbade using `command_id` for mailbox; Unit B extends that: draft save is a third identity family. AUTHORING 2.1a `command_id` row is UI residue, not daemon law (backend AD-11 never names `command_id`).
- First save that supplies `editor_draft_id` → typed refuse (only way to keep “daemon is the sole issuer”).
- Ownership = authoring `psess:` recorded on the head. A second authoring session of the same operator cannot publish. AM-03 does not name this field; Unit B adds `product_session_ref` to `editor_draft_head` (AM-14-legal pointer, not on the amendment list).
- PUT of draft bytes is excluded from the facade immediately (header or separate prefix). Home attach of a non-draft file still uses the same URL; the two PUTs are distinguished by a flag AD-9 does not name.

### Why both are literal

- AD-11 makes `client_draft_correlation` **optional** and says it “makes lost-ack retry return the same durable id.” It does not say what happens when it is omitted, or when it is reused with different bytes. PACK-UI adds “same bytes” only on the retry-with-correlation row.
- First save has **empty** `expected_revision`, so CAS cannot distinguish two first-saves. The only coalescer the backend names is optional. The UI companion names a second coalescer (`command_id`) the backend AD never copied.
- CLOSURE-J3 “not the issuer path” does not pick refuse vs ignore.
- “Ownership of `editor_draft_id`” is unchecked English. `editor_draft_head` has no named owner field in AM-03 / AD-11.
- AD-11 “Library facade excludes these blobs” does not say **when** exclusion begins relative to PUT.

### Holes

**H-J3-COALESCE — three legal first-save identities.** `(client_draft_correlation)`, `(command_id, psess, principal)`, and content `fp1` can each be “the” lost-ack key. Two units will mint one working copy or two for the same operator keystroke. That was the original J3 defect (two issuers). It is now two **coalescers**.

**H-J3-OWNER — two owners of one draft.** Operator-global vs per-`psess:`. `publish_editor_draft` “unauthorized draft → refuse” (PACK-UI) fires for different people.

**H-J3-PUT — two owners of the staged bytes.** AD-9 PUT is the possession path for Library artifacts **and** (PACK-UI) the first step of draft save. Facade exclusion is claimed for drafts. The window between PUT and `save_editor_draft` is either a Library hit (Unit A) or an unnamed draft namespace (Unit B). Same fp1 cannot be both a composer `selected_refs` kind `artifact` (Home attach, UI AD-22) and an excluded draft blob.

**Not a High fork (DTO / deferred).** Exact `save_editor_draft` JSON field list beyond “omit `editor_draft_id` / empty `expected_revision` / optional correlation”; whether unsaved validate PUTs a transient fp1 (AD-11 allows unsaved validate and mints no JobHandle; bytes channel is still PUT).

### Required bind

1. One first-save coalescer. If correlation is omitted, state whether same-bytes retry coalesces on fp1 or mints a second id.
2. Same correlation + different bytes: refuse, or ignore bytes and return the original id (lost-ack semantics). Not last-writer-wins (empty CAS would otherwise allow it).
3. Is parent AD-29 `command_id` on `save_editor_draft` / `publish_editor_draft` or not. If yes, it **is** the coalescer and correlation is redundant; if no, strike AUTHORING 2.1a’s command_id row for this path.
4. Owner field on `editor_draft_head` (principal and/or `product_session_ref`). Add it to AM-03 if it is a pointer.
5. First save that supplies `editor_draft_id`: refuse.
6. When facade exclusion starts, and how draft PUT is distinguished from Home-attach PUT without a second byte channel.

---

## J4 — `publish_editor_draft` vs AD-30 enable vs unsaved validate

### Live law

Backend AD-11 / PACK-UI publication:

> Addable **`publish_editor_draft`** checks draft ownership, `expected_revision`, reruns validation against that immutable fp1, and writes the local authoring-pack contribution. … No mandatory extra validation record. Unsaved preview/validate stay legal and mint no JobHandle. Parent AD-30 **enable** remains compile identity.

UI AD-21 (spine, reconciled): same command, then enable that pack, grant, select instance, `dispatchInvoke`.

UI AUTHORING 2.2 (live companion, **not** removed by the changelog):

> Publish into the local authoring pack requires a **currently valid** validation of the hash being published. Re-validate is explicit.

T-R5-01: publish of a dirty buffer without a new valid validation **refuses**. T-BE-18: publish then enable; “client-only validation” forbidden; “second enable machine” forbidden.

Parent AD-30: enable after validate; collision of `(point, qualified_id)` refuses; failed validation restores last usable roster. Parent AD-4: compile identity `(qualified_id, version)` **at enable**.

### Two units

Shared: `publish_editor_draft` exists; enable is compile identity; unsaved preview/validate mint no JobHandle; draft Run is `draft_not_runnable`; export is later.

**Unit A — one magic unpublished pack per daemon; publish overwrites its `graph_template` bytes after an inline revalidation; enable reads that pack; no stored verdict.**

- Pack identity is a well-known daemon roster item (`local.authoring` or equivalent). Second `publish_editor_draft` of a different draft with the same contribution point **overwrites** unpublished bytes (not an enabled version, so parent AD-4 in-place-overwrite of enabled bytes does not fire).
- Daemon **reruns** DAG/schema checks inside `publish_editor_draft` (CLOSURE-J4 / PACK-UI). A prior validate command is unnecessary. AUTHORING 2.2 is chrome: the UI may call validate for display; the daemon does not read a `ChangeValidation`-class row.
- Enable of that pack is parent AD-30 and assigns `(qualified_id, version)` from a daemon-generated manifest. Publish’s “pack contribution identity” is a file path / fp1, not a qualified_id.

**Unit B — each draft publishes into its own unpublished pack identity; publish requires a stored currently-valid verdict; enable is a second validation; qualified_id is chosen at publish.**

- Pack identity is derived from `editor_draft_id` (or from a name in the draft). Two drafts are two roster items. Collision at enable if both used the same `qualified_id`.
- AUTHORING 2.2 is daemon law: publish refuses unless a validation record for **that fp1** is currently valid. “No mandatory extra validation record” (CLOSURE-J4) is read as “no new record **type**”; reusing `ChangeValidation`-class / parent AD-6 checks is allowed. T-R5-01 is a daemon refuse, not chrome.
- Publish writes `contributes: graph_template` with a `qualified_id` the authoring UI supplied. Enable must not change that id (or parent AD-30 collision / identity drift fires).

### Why both are literal

- “Local authoring pack” is never given an id, a roster key, a plugin_id, or a cardinality. UI AUTHORING: “this machine’s unpublished roster.” One vs many both fit.
- CLOSURE-J4: “No mandatory extra validation record. … publication can rerun validation against immutable bytes.” PACK-UI: “Reruns validation against that **immutable fp1** (no mandatory extra validation record).” AUTHORING 2.2: “requires a currently valid validation of the hash being published.” Both packets were reconciled in this amendment (`UI-CANDIDATE-CHANGELOG.md` Round 2 lists AUTHORING issuer/publish but did **not** delete §2.2). Live law currently contains both sentences.
- Who mints `qualified_id` — publish write vs enable compile — is unnamed. Parent AD-4 says enable **is** compile identity, which Unit A uses to delay qualified_id until enable. Pack authors normally put `qualified_id` in the manifest **before** enable, which Unit B uses.

### Holes

**H-J4-PACK — two owners of “the” local authoring pack.** One daemon-global unpublished pack (last publish wins, silent clobber of another draft’s contribution) vs one pack per draft (enable collisions). First Run (T-R5-00) cannot name which roster item to enable.

**H-J4-VALID — stored verdict vs inline rerun.** A UI builder that skips validate because the daemon reruns, and a daemon builder that refuses publish without a stored verdict, do not assemble. This is not “DTO field list”; it is whether a prior command is a precondition of `publish_editor_draft`.

**H-J4-ENABLE — two writers of `graph_template` contribution bytes.** Publish writes pack bytes; enable publishes ContributionHits. If publish already wrote a `qualified_id` that enable would re-derive, they can disagree. If publish writes bytes that enable must not re-validate (Unit A trusts publish), parent AD-30’s enable-validate is skipped. If both validate, failed enable restores last usable roster **without** unwriting the published contribution — a third state (published, not enabled, last roster still V1) that neither trace names.

Unsaved validate minting no JobHandle **holds**. Do not reopen draft test-run.

**Not a High fork (DTO / deferred).** Exact publish result DTO beyond “pack contribution identity”; distributable export (parent AD-18 later).

### Required bind

1. Cardinality and identity of the local authoring pack (one per daemon / one per draft / one per `(qualified_id)`).
2. Whether `publish_editor_draft` requires a prior valid verdict of that fp1, or only reruns checks itself. Strike or amend AUTHORING §2.2 so the two packets match.
3. Which step mints `(qualified_id, version)` — publish must not pretend to be compile identity; enable must not invent a different qualified_id than the pack it is enabling.
4. What enable-failure does to the just-published contribution bytes.

---

## J5 — Loopback `source_unreachable` vs recorded TLS vs dest completion ack vs invoke-before-complete

### Live law

Backend AD-9:

> `transfer_artifact` … issues `artifact_transfer_ticket` only when the **source daemon origin is recorded reachable TLS** that the destination environment’s network allowlist can dial. Default loopback is **not** a remote route: typed `source_unreachable`. Never silently expose loopback. Never fall back to local invoke. Ticket binds `ticket_id`, source origin, fp1, byte count, operator/`product_session_ref`, destination environment identity + placement revision, and the **exact machine `credential_ref` audience**. The already-authenticated destination control connection is notified; only that audience may `GET /artifacts/<fp1>` with `X-QMX-Transfer-Ticket`. After dest hash/byte-count verify and durable placement, dest authors `transfer_complete` (idempotent on `ticket_id`/`command_id`). Only that ack marks the ticket complete. Invoke on that placement refuses until complete. Failure leaves the source local-complete fp1.

ARTIFACTS topology:

> Notify the already-authenticated destination control connection (worker dial-out to **its** daemon; that daemon then pulls the recorded source origin). … dest daemon sole writer of dest store; source daemon records the ack.

AM-06: dest pulls from recorded reachable TLS; `source_unreachable` on loopback-only; dest-authored `transfer_complete` closes the ticket. **Daemon never dials in.**

Story 41.4: worker dials out; daemon never dials in; deployed side exposes **no listener or second transport channel**.

CLOSURE-J5 deferral: “How the operator records a non-loopback TLS origin (host config UX) is an implementation story; the refusal class is bound.”

Ticket states: `issued | notified | claimed | complete | failed | expired`. No ticket TTL number.

### Two units

Shared: loopback-only source → `source_unreachable`; no local-invoke fallback; dest GET with ticket + matching machine `credential_ref`; dest verifies hash+count; dest authors `transfer_complete`; lost ack retries; invoke on dest placement refuses until complete.

**Unit A — recorded origin is a host-config registry row independent of bind; dest daemon POSTs `transfer_complete` to the **source** as the ticket audience; dest-local placement is complete only after source returns the ack; loopback bind + recorded public HTTPS is the supported laptop→VPS route.**

- `qmb host configure` (or equivalent) writes `registry:…source_origin=https://…`. Listener may still be `127.0.0.1:8765` for the SPA. Transfer uses the recorded HTTPS origin as GET target. Default bind remains loopback; “default loopback is not a remote route” means “unrecorded loopback,” not “any process that also listens on loopback.”
- Dest daemon, after local verify, sends addable `transfer_complete` **to the source daemon** (dest dials source; source does not dial in). Same machine `credential_ref` as GET. Source journal is the ticket owner. Dest stores a placement row only when source returns complete (T-X-01 “complete ack → invoke allowed”).
- Dest offline at `transfer_artifact`: ticket stays `issued` until the dest control connection exists, then `notified`. Invoke on dest cannot run (no dest daemon).

**Unit B — recorded origin **is** the listener bind; a loopback-bound daemon can never be a transfer source; `transfer_complete` is dest-local; source infers complete from the GET finishing; invoke uses dest-local completeness.**

- If bind is `127.0.0.1`, every `transfer_artifact` is `source_unreachable` even if the operator typed a DNS name in a UI field. “Recorded reachable TLS” = the inspect Story 41.4 non-loopback listener config (HTTPS/WSS recorded operator configuration). Laptop v1 (loopback default) **cannot** transfer. Remote-to-remote (two recorded TLS daemons) can.
- Dest daemon is sole writer of dest store: `transfer_complete` is a CT-40 command **on the dest daemon** (machine principal). Source never hears it. Source marks `complete` when GET of the full byte count succeeds (the pull **is** the ack). AM-06 “dest-authored `transfer_complete` closes the ticket” is read as dest-local ticket replica.
- T-X-05 lost-ack retry is dest retrying dest-local `transfer_complete` (idempotent). Source already complete from GET.
- Invoke on dest checks dest-local placement. If GET succeeded and dest `transfer_complete` is lost, Unit B still allows invoke (bytes are there). Unit A would refuse until source acked.

### Why both are literal

- CLOSURE-J5 explicitly defers **how** the operator records the origin and claims “the refusal class is bound.” Who writes “recorded,” and whether a loopback **bind** plus a recorded **name** is legal, is the whole supported route. AD-9 “default loopback is not a remote route” and ARTIFACTS “source origin is recorded non-loopback TLS” both fit Unit A (record a non-loopback name) and Unit B (bind must be non-loopback).
- Two journals are named: “dest daemon sole writer of dest store; source daemon records the ack.” Addable `transfer_complete` lives on `qma-wire` (AM-09) — **each** daemon has qma-wire. The command’s **target process** is unnamed.
- “Only that ack marks the ticket complete. Invoke on that placement refuses until complete.” “That placement” is dest. “The ticket” is a source projection (`artifact_transfer_ticket` in AM-03). Two complete bits.
- Story 41.4 “deployed side exposes no listener” plus “daemon never dials in” plus dest must GET source: dest daemon **dials source**. That outbound dial is the supported pull. Whether dest also dials source for `transfer_complete` is unspecified. Unit B avoids the second dial by treating GET as completion.

### Holes

**H-J5-ORIGIN — two mutation paths for “recorded reachable TLS.”** Host-config registry vs listener bind vs a field on `transfer_artifact`. Laptop v1 either can transfer (Unit A split-horizon) or can never transfer (Unit B). That is the original J5 topology defect, not a UX deferral. Deferring “how the operator records” without saying **whether loopback bind + recorded name is a legal source** leaves both products AD-legal.

**H-J5-ACK — two owners of `complete`.** Source ticket row vs dest placement row. Invoke-before-complete is a dest gate that must read one of them. Lost `transfer_complete` (T-X-05) has different meaning if GET already completed the source ticket (Unit B) vs if only the dest-authored command does (Unit A).

**H-J5-NOTIFY — dest control connection may not exist.** “The already-authenticated destination control connection is notified.” If the dest worker is offline, Unit A parks at `issued`; Unit B refuses `transfer_artifact`; a third legal reading waits until `expired` with no expiry policy. Ticket state `expired` is named; no clock is.

**H-J5-INVOKE — which invoke, citing which fp1.** AD-9 “Invoke on that placement refuses until complete.” Local invoke on the source of a still-open ticket is allowed (failure leaves source local-complete). Remote invoke citing that fp1 without a ticket is either refuse (no ticket) or a silent “bytes are local to dest somehow.” Home-staged fp1 + later remote instance (T-R6-01) needs this gate at `dispatchInvoke` on **dest**, keyed by fp1 + placement revision. That compare is unnamed (artifact inventory on JobHandle? input_schema artifact refs? ticket table?).

**Not a High fork (DTO / deferred).** Ticket JSON field list beyond the named binds; numeric ticket TTL; host-config chrome for recording origin **once the legality of split-horizon is bound**.

### Required bind

1. Legal source: (a) loopback bind + separately recorded HTTPS origin, or (b) only a non-loopback TLS listener. Pick one. If (a), name the sole writer of that origin (host-control registry, not a client-supplied transfer arg).
2. `transfer_complete` target process: source daemon (dest dials source as the ticket audience) or dest daemon (and then how source’s AM-03 ticket becomes `complete` without dest dialing source and without source dialing in).
3. Invoke gate: dest refuses `dispatchInvoke` that cites fp1 until **which** row is `complete`. Lost-ack retry must not flip that bit twice.
4. Dest offline at issue: refuse, or `issued` until notify, plus what `expired` means.

---

## Small reconciliations

These were in the joint brief. Names moved. Joints remain.

### Mailbox principal check

Live AD-7 / MAILBOX:

> `send_message` **and** `list_mailbox` admit only when the connection’s operator principal **equals** that session’s durable principal **before** append or snapshot.

Inspect `product_session.principal` is parsed as `PrincipalClass` (`operator` | `machine`) — a **class**, not a person (`product_session.py` `_parse_principal` → `parse_closed(PrincipalClass, value)`). Parent CONTRACTS examples use `"principal": "operator"`.

**Unit A:** equality is `PrincipalClass.OPERATOR == session.principal`. Every paired browser and every dummy CT-40 operator (H-J1-DUMMY) may `list_mailbox` every operator `psess:` on that daemon. T-BE-08 cannot fail.

**Unit B:** equality is AD-17’s minted operator-principal **id** (H-J1-PRINCIPAL). Inspect `product_session.principal` must be amended. AM-02/AM-14 did not amend it.

This is the same joint as H-J1-PRINCIPAL, expressed on mailbox admission. Binding J1’s principal object binds this. Until then the “small” check is a tautology.

Daemon-originated replies inherit `product_session_ref` and “may not accept an arbitrary session” — holds. Do not reopen chat-as-invoke.

### Optional `originating_product_session_ref`

Live AD-8 / CANCEL:

> UI-originated admits store immutable **`originating_product_session_ref`**. Headless/QMB admits **omit** the field. UI `cancel_job` is unavailable when the field is absent; Story 36.5 remains the headless abort door.

`JobHandle.owner` remains Quant `ActorId` (inspect + CANCEL). `caller_kind` is still an Epic 60 adoption gap; until it exists UI pack invoke is `caller_kind_unsupported` (UI AD-8) but headless `qmb` remains a door.

**Unit A:** “UI-originated” = the admitting connection has `pairing_record_id` (browser). Headless QMB with a `psess:` still **omits** the field (CANCEL table: “Headless QMB / no product session” is read as “headless QMB, **even if** a psess is present” — the slash is “or”). UI cannot `cancel_job` a QMB-started job that the operator can see on Home.

**Unit B:** “UI-originated” = admit copied `caller_session_ref` / selected `psess:` onto the handle whenever a product session is present. Headless QMB invoke **with** a `psess:` **stores** the field. UI `cancel_job` then works on QMB-started work. “Must not make headless work impossible” is satisfied because Story 36.5 still exists; the field is extra.

The slash in “Headless QMB / no product session” is the fork. Nested children “store the session that started **that child**, or omit if that admit was headless” repeats it.

`handle_id` **is** `job_id` holds. Exact handle/run/attempt fences hold. Do not reopen observer cancel.

### `_ref` vs `_id`

AM-14 live: Envelope/handle pointers are `product_session_ref` and `originating_product_session_ref`. Do not add `product_session_id`-on-envelope or `originating_psess` to the QMA ten-exception list. ProductSession **own** identity stays `product_session_id`.

That **name** bind holds. Remaining joints are value shape and extra fields, not the AM-14 spelling:

- **Value of `product_session_ref`.** Unit A: the same `psess:…` string as `product_session_id`. Unit B: a structured pointer `{store, id}`. QMA `_ref` law requires a discriminator so a validator can enforce it; neither packet names the discriminator for these two new pointers.
- **Wire pair + payload hash** “live on the journal row and are echoed on every `list_mailbox` row” (AD-7). They are **not** AM-02 Envelope fields. Unit A puts `producer_id` / `wire_id` on the CT-48 Envelope (fails inspect `ENVELOPE_REQUIRED_FIELDS` / `ENVELOPE_OPTIONAL_REFS` unless amended). Unit B keeps them as journal extras + query DTO only. AM-02 only added `product_session_ref`. This is a real Envelope-vs-journal shape clash, but it is the size the brief called “implementation-level DTO” **if** both units keep them off Envelope fp1 and off the CT-48 required set. Flag as **Medium**: name “journal extras, not Envelope fields” in one sentence so Unit A cannot extend `ENVELOPE_OPTIONAL_REFS` without an amendment.
- `pairing_record_id`, `pending_id`, `ticket_id`, `editor_draft_id` are own-identity `_id` / `id` forms. They do not need the exception list. Do not reopen AM-14.

### Shell ≠ provider; `get_pack_ui_request`

PROVIDER-AND-COMPAT vs UI TRACE first-run: shell = `qmb host start` + TTL + pair + initialize; provider needs an already-stored allowlisted ref. **Holds** as a slogan. It does not close H-J1-DUMMY (CT-40 operator without provider ref is still “shell”).

`get_pack_ui_request` keyed by `instance_id` + `availability_revision` **holds** as a read contract. DTO of the returned document is UI VIEW-AND-PACK-CONTRACT.md (already specified). Not a J1–J5 hole.

---

## What is not a High fork (leave downstream)

Per joint brief and `CLOSURE-J1-J5.md` remaining deferrals:

| Item | Why it is not this gate |
| --- | --- |
| Numeric pairing TTL / `stage_max_bytes` | Operator-supplied / registry row; refuse if missing is already bound |
| Proof-token entropy and RFC 6455 charset | Implementation story; both units must be unguessable and subprotocol-safe |
| Ordinary supervisor PID/signal/stale-lock | HOST-LIFECYCLE already defers; sole-writer + lock-release hold |
| Exact host-control transport (UDS vs loopback TCP) | Protocol family is “not CT-40 / not `/pair/*`”; byte schema is DTO |
| Exact `save_editor_draft` / `transfer_complete` / `list_mailbox` JSON field lists beyond named keys | Brief: “Implementation-level DTO field lists beyond named commands” |
| Native/QMB write-once helper for provider secrets | Deferred; shell ≠ provider holds |
| Distributable pack export | Parent AD-18 later |
| WS close code / timer vs next-frame | Expiry **closes** and cannot issue further commands is bound |
| `sessionStorage` optionally holding `pairing_record_id` | AD-14 “may” |

Do not spend the next amendment pass on these while H-J1-PRINCIPAL / H-J2-CONFIRM / H-J3-COALESCE / H-J4-PACK / H-J5-ACK remain.

---

## Cross-cutting: `AuthenticatedWireSession` is still the join that is not a type

Inspect session:

```text
credential_ref: CredentialRef   # required
principal_class: PrincipalClass
authenticated_before_protocol: bool
```

Live AD-5: browser session **does not populate** `credential_ref` and **does** carry `pairing_record_id`.

Both units must change this type. That change is required, not a fork. The fork is **what mailbox/cancel compare** after the change:

- Unit A (with H-J1-B): compare `principal_class` (tautology) or compare `credential_ref` on machine connections and `pairing_record_id` on browser connections — two pairing records of the same operator are different people for cancel, same person for mailbox, or the reverse.
- Unit B (with H-J1-A): compare the AM-03 operator-principal id copied onto pairing_session, product_session, and the wire session. Renew rotates `pairing_record_id` and does **not** change that id. That is the only join that makes T-BE-08, cancel starter-only, and “browser pairing maps to that principal” the same person.

The first-pass review’s H-PAIR (internal `CredentialRef` per pairing row vs one copied OS ref) is **closed as a slogan** by AM-11 (no `credential_ref` on browser sessions). It is **not** closed as a join: the replacement object (`pairing_record_id` vs operator-principal id vs `PrincipalClass`) is exactly H-J1-PRINCIPAL.

---

## Required binds (minimum set to close this gate)

One outcome each. Not DTO lists.

1. **Operator principal object** — named AM-03 projection **or** explicit “inspect `PrincipalClass` is the v1 person (single operator per root).” Then mailbox equality, cancel equality, and pairing_session “operator principal” cite that same field.
2. **CT-40 operator without host-control / pairing** — refuse or allow. If refuse, amend Story 41.4 / `authenticate_before_protocol` so dummy `cred://` + caller-selected `principal_class=operator` is not a legal unit.
3. **Lost `host_control`** — remint on start from OS ACL, or locked until restore/wipe. Sole writer of `registry:pairing.session_ttl`.
4. **Concurrent `/pair/confirm`** — first consume wins; no second `proof_fp1`. One loser outcome for renew vs revoke. Define unclaimed. Define when `pairing_record_id` is minted.
5. **First-save coalescer** — one key; omitted-correlation behavior; client-supplied id refuses; owner field on `editor_draft_head`; PUT vs Library window.
6. **Local authoring pack identity** + whether publish requires a stored verdict + which step mints `qualified_id`.
7. **Recorded TLS source legality** (split-horizon vs bind-must-be-TLS) + which daemon’s `complete` bit gates dest invoke + `transfer_complete` target process.
8. **UI-originated vs headless admit** — pairing_record_id, presence of `psess:`, or both. Headless+psess must have one cancel door.

Until those eight are single-outcome, two factory units can obey every live AD and still fail to assemble.

## Honesty

No live daemon, no executed tests, no installed-product run. This file does not edit the spine, the UI candidate, or historical first-pass `reviews/`. Documentation Factory, epic rewrite, and factory execution stay out of this sitting.
