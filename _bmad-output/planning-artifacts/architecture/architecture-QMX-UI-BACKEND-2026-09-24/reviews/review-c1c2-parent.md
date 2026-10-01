---
name: C1/C2 parent-consistency review
sitting: architecture-QMX-UI-BACKEND-2026-09-24
lens: parent / QMA inherited law (focused C1 recover-control, C2 origin-revoke)
against: architecture-QMA-2026-08-28; architecture-QMX-2026-09-18
child: ARCHITECTURE-SPINE.md AD-4 / AD-6 / AD-15 / AD-17; PARENT-AMENDMENT-MAP.md AM-10 / AM-03 / AM-15; HOST-LIFECYCLE.md; PAIRING-AND-ADMISSION.md
date: 2026-09-24
reviewer: Grok 4.6 independent parent-consistency (C1/C2)
status: pass-with-residuals
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
tests: unexecuted
---

# Reviewer gate — LENS: C1/C2 parent / QMA consistency

**Subject:** C1 (`qmb host recover-control`) and C2 (`pair revoke --origin` journal-seq barrier) in `architecture-QMX-UI-BACKEND-2026-09-24`, after the focused correction recorded in `CLOSURE-C1-C2.md`.
**Parents:** QMA `architecture-QMA-2026-08-28` (especially AD-5 transport posture / single inbound port / unauthenticated bind as hard startup refusal; AD-6 one journal, sole writer, `journal_seq` total order, fold contract; AD-15 listener never unauthenticated; AD-24 authenticate-before-protocol and human-gate list; AD-26 `variable.set`; AD-27 backup/restore) and parent `architecture-QMX-2026-09-18` (especially AD-2 QMB never opens daemon sqlite; AD-16 complete v1 sqlite additions; AD-21 QMB is the only operator CLI).
**Child law read live:** backend AD-4, AD-6, AD-15, AD-17; AM-10, AM-03, AM-15; `HOST-LIFECYCLE.md`; `PAIRING-AND-ADMISSION.md`; plus TRACE T-BE-27..31 / T-H-01..04 / T-P-11..13 and UI `BOOTSTRAP-AND-AUTH.md` §12 as wording check. Historical `reviews/*.md` are prior evidence, not current text.
**Question this lens answers:** does C1 recover-control or C2 origin-revoke silently rewrite inherited law? Does AM-10 name `recover-control`? Is recover-control a second unauthenticated 8765 bind (QMA AD-5 / Story 41.4)? Does the origin-revoke barrier silently rewrite QMA AD-6 `journal_seq` rules?
**Out of scope:** implementation; Documentation Factory; epic rewrite; editing historical first-pass files under `reviews/`; re-opening J3/J4/J5 except to confirm they are not disturbed.

**Verdict: PASS WITH RESIDUALS.**

The two C1/C2 parent bars hold:

1. **AM-10 names `recover-control`.** The host group lists `rotate-control` and **`recover-control`**. Running-daemon verbs stay token-gated; recover is OS-owner of a **stopped** root and does not present the lost token.
2. **Recover-control is not a second unauthenticated 8765 bind.** Local AD-15 / AD-17 / AM-15 put host-control **outside port 8765**, not CT-40, not `/pair/*`. Recover requires the daemon **stopped**, so it cannot be an AM-01 pairing HTTP path and cannot be a live 8765 listener. QMA AD-5 / AD-15 / AD-24 / Story 41.4 unauthenticated-bind law is named (AM-01 on the wire carve-out, AM-15 on the extra loopback channel), not silently overridden by C1.
3. **The origin-revoke barrier uses parent `journal_seq` as the single total order.** C2 is an append at `journal_seq` R plus a fold over pairing rows with announcement `journal_seq` < R. It does not mint a second sequence number, does not put `journal_seq` on the wire as `seq`, does not trim or rewrite journal history, and does not treat origin-revoke as an AD-5 first-append-wins CAS loser. That **upholds** QMA AD-6; it does not rewrite it.

J3/J4/J5 and the small reconciliations are untouched by this correction.

Residuals below are uniqueness / writer-process holes, not a silent 8765 bind and not a renamed `journal_seq`. They are cheap to freeze if this packet is touched again. They are not enough to return C1/C2 as a parent override.

---

## Method

A local rule that weakens a parent without an AM-id is a silent override. A named AM whose proposed text is narrower than the local AD is also a silent override.

Especially checked for this focused pass:

| Bar | Parent | Child must |
| --- | --- | --- |
| AM-10 names recover-control | parent AD-21 `COMMAND_GROUPS`; QMA AD-24 human-gate list | `recover-control` on AM-10, not only HOST prose |
| Recover-control ≠ unauthenticated 8765 | QMA AD-5 single inbound port; unauthenticated bind = hard startup refusal; AD-15 listener never unauthenticated; AD-24 transport custody; Story 41.4 | Offline OS-owner replace; daemon stopped; not port 8765; not AM-01 |
| Origin-revoke ≠ rewrite of `journal_seq` | QMA AD-6: one journal, global monotonic `journal_seq` is the only total order; fold contract stream / `journal_seq` / `as_of` over `recorded_at` / equal-instant ascending `journal_seq`; sole writer; append-only never trimmed. QMA AD-5: `journal_seq` never appears on the wire as `seq` and is opaque to clients | Barrier is the revoke event’s `journal_seq` R; history kept; renew-then-revoke kills the new proof; revoke-then-renew refuses |

---

## Numbering collisions (standing caution)

Factory prose that drops the prefix still collides. Worst pairs for **this** correction:

| Local backend-delta | QMA 08-28 | Parent 09-18 | Misread if prefix dropped |
| --- | --- | --- | --- |
| AD-5 pairing HTTP carve-out | **AD-5 wire; unauthenticated bind is hard startup refusal; single inbound port** | AD-5 mapping | C1 recover treated as already-legal unauth 8765 because “AD-5 allows pairing HTTP” |
| AD-6 `qmb host` process door | **AD-6 one journal / `journal_seq` / sole writer** | AD-6 DAG | C2 barrier treated as host-verb law, or host verbs treated as store-list law |
| AD-4 pairing record vs proof | AD-4 (different subject) | AD-4 Board vs graph | Origin-revoke barrier mistaken for an unrelated parent AD-4 |

Keep `QMA AD-n` / `parent AD-n` / `local AD-n` on every factory sentence. C1 is a QMA AD-5 / AM-15 channel question, not local AD-5. C2 is a QMA AD-6 `journal_seq` question, not local AD-6.

---

## Especially checked (required holds)

### 1. AM-10 names `recover-control` — HOLD

**AM-10 proposed text (live):** add group `host`: `start`, `status`, `stop`, `configure pairing-ttl`, `pair <code>`, `pair revoke --session|--origin`, `rotate-control`, **`recover-control`**. Human-gate: running-daemon verbs are operator-only via `host_control`. `recover-control` is OS-owner of a **stopped** root and does not present the lost token. **Only** host-control may write `registry:pairing.session_ttl`; CT-40 `variable.set` of that key refuses.

Also named on: local AD-6 verb list; local AD-17 lost-token paragraph; `HOST-LIFECYCLE.md` trust-root + verbs + T-H-02/04; TRACE T-BE-27/28/29; UI `BOOTSTRAP-AND-AUTH.md` §12; `DEPENDENCY-MAP.md` host rows.

**Ruling:** C1 is not an unnamed CLI add. Parent AD-21 (QMB is the only operator CLI) is preserved: `host` is a new **group**, not a new COMP and not `qma-cli`. QMA AD-24 human-gate list is named on the AM-10 inherited cell, not silently extended.

### 2. Recover-control is not a second unauthenticated 8765 bind — HOLD

**Parents:**

- QMA AD-5: loopback default; every client authenticates with a Credential-Broker-resolved credential before protocol bytes; **an unauthenticated bind is a hard startup refusal**; the daemon’s own listener is the **single inbound port**.
- QMA AD-15: this reaches the proxy only; **the daemon’s own listener is never unauthenticated**.
- QMA AD-24 transport custody: authenticate before protocol; never offers an unauthenticated bind; client credential is a broker-resolved reference.
- Story 41.4: plaintext non-loopback or unauthenticated bind → hard startup refusal; credential_ref authenticates first; daemon never dials in; daemon listener is the single inbound port.

**Child (live):**

| Path | Auth | Named? |
| --- | --- | --- |
| `POST /pair/start`, `POST /pair/confirm`, CORS OPTIONS on the AD-15 HTTP catalogue | unauthenticated HTTP on **8765** | AM-01 / local AD-5 |
| `POST /pair/renew`, snapshot GET, PUT `/artifacts/stage`, GET `/artifacts/<fp1>`, JSON-RPC WS | authenticated on **8765** | AM-13 / AM-05 / AM-01 remainder |
| Live host-control (`pair`, `configure`, `rotate-control`, …) | token-gated loopback **outside 8765**, not CT-40, not `/pair/*` | AM-15 / local AD-15 / AD-17 |
| `qmb host recover-control` | OS owner of `QMA_DAEMON_ROOT`; **daemon stopped**; **no** lost token; **no** 8765 | AM-10 + AD-17 / HOST |

Local AD-15 freezes the negative: host-control is “**not** a second unauthenticated 8765 bind, not pairing HTTP.” Spine Deferred freezes host-control IPC as “Token + loopback + **not port 8765** + not CT-40”; HTTP vs named pipe vs file drop remains a story **under that freeze**.

Recover cannot be AM-01: AM-01’s unauthenticated set is start / confirm / OPTIONS only. Recover cannot be a live listener: HOST / AD-17 refuse recover against a live daemon (T-H / T-BE-29: use `rotate-control` if the token is still held).

**Ruling:** C1 does not punch a third unauthenticated family on 8765. A factory unit that auto-starts the daemon and serves `POST /host/recover` (or any recover route) on 8765 without a token **conflicts** with AM-10, AM-15, local AD-15, and QMA AD-5. That product is out of law, not an allowed reading.

**Residual (F-1):** who **journals** the new `host_control_fp1` while the daemon is stopped is not named. See Findings. That is QMA AD-6 sole-writer / parent AD-2, not QMA AD-5 bind.

### 3. Origin-revoke barrier does not rewrite QMA AD-6 `journal_seq` — HOLD

**Parents:**

- QMA AD-6 **One journal:** a single append-only journal with a global monotonic `journal_seq` is the only durable append target for daemon-owned events; `journal_seq` is the **single total order**.
- **Fold contract:** stream, ordering key `journal_seq`, knowledge-time `as_of` over `recorded_at`, equal instants disposed by **ascending `journal_seq`**, never by timestamp. A new fold is a spine amendment.
- **Sole writer:** no process other than the daemon writes the journal or sqlite. QMB never opens daemon sqlite (parent AD-2).
- **Never trimmed.** Revocation is a later event, not a rewrite of earlier bytes.
- QMA AD-5: wire `seq` is the per-scope projection index; **`journal_seq` never appears on the wire as `seq`** and is opaque to clients. Wire-command idempotency is first-append-wins on `producer_id` + `id`. That is **not** the journal’s total-order law.

**Child (live) C2:**

`--origin` is an administrative **barrier**. When that event is durable at `journal_seq` R, every `pairing_session` and `pairing_pending` for that Origin with `journal_seq` < R is revoked, including confirmed-unconsumed pendings **and a renew that committed earlier**. Origin-revoke is never discarded because a renew appended first. `--session` is that `pairing_record_id` only (after renew, old id is a recorded no-op; new proof stays live). HOST: does **not** delete journal history.

Serialized outcomes (PAIRING + T-BE-30/31 + T-P-11/12):

1. Renew durable first (seq < R), then `--origin` → new proof revoked; WS closed. Not a CAS no-op loser.
2. `--origin` durable first, then `/pair/renew` with the old proof → typed refuse.

AM-03 (live) already adds `pairing_pending` / `pairing_session` to the closed projection list and copies the parent four-part fold: stream `noun.verb`, ordering `journal_seq`, knowledge-time `as_of` over `recorded_at`, equal-instant ascending `journal_seq`. Live shape is unrevoked pairing rows. C2 is fold semantics over those projections, not a sixth sqlite name.

CLOSURE-C1-C2: “Journal order still serializes appends. Origin-revoke is not a CAS loser.” That is the correct parent move: do **not** apply QMA AD-5 wire first-append-wins to an administrative host-control append.

**Ruling:** R **is** the origin-revoke event’s announcement `journal_seq`. Comparison is on pairing rows’ announcement `journal_seq` (QMA AD-6 record law). History is kept. No pairing-local sequence is minted. Confirm/renew HTTP still does not carry `journal_seq` as wire `seq` (confirm body remains `{pairing_record_id, pairing_proof, expires_at}`). Equal-instant disposition remains ascending `journal_seq`.

A factory unit that (a) stores a sqlite high-water flag **without** a journal event at R, (b) uses per-scope derived `seq` as R across `pairing_pending` and `pairing_session`, (c) renumbers historical `journal_seq`, or (d) drops the later origin-revoke because a renew already appended, **conflicts** with QMA AD-6 / this sitting. Those products are out of law.

**Residual (F-2, F-3):** the origin-revoke `noun.verb` is not named; “after R, `/pair/confirm` cannot issue” vs client “re-pair” is not unique. Neither redefines `journal_seq`. See Findings.

---

## AM-10 / AM-03 / AM-15 tagging (C1/C2 only)

| ID | Inherited cell | Covers the live C1/C2 rule? | Silent override? |
| --- | --- | --- | --- |
| AM-10 | parent AD-21 `COMMAND_GROUPS`; QMA AD-24 human-gate; QMA AD-26 `variable.set` | **Yes** for the verb name, stopped-root recover, `--origin` / `--session`, exclusive TTL writer. Recover is explicitly **not** “present the lost token.” | No. Residual: AM-10 does not name the **writer process** for the recover journal append (F-1). |
| AM-03 | QMA AD-6 / AD-8 / FR-Q23 / Story 42.2; parent AD-16 | **Yes** for `local_operator` (C1 preserves this row; does not remint) and pairing projections (C2 folds into them). Four-part fold template matches QMA AD-6. | No silent rewrite of `journal_seq`. Residual: origin-revoke stream name omitted (F-2). |
| AM-15 | **QMA AD-5 single inbound port**; QMA AD-15/AD-24; Story 41.4 never unauthenticated bind; human-gate | **Yes** for live host-control: token-gated, **outside port 8765**, broker allowlist not widened. Inherited cell now cites QMA AD-5 single-port (J1–J5 F-4 spent). | No 8765 recover route. Residual: proposed text still says “token-gated” and does not mention the AM-10 recover exception (F-1 sibling). Coverage is split, not missing. |

AM-01 is unchanged and does **not** list recover-control. That is correct: recover is not pairing HTTP.

The Inherited table still does not copy AM text in as already-true parent law. That half of the tagging rule holds.

---

## C1 vs parents (lost `host_control`)

**Required by the closure review:** recovery under the already-chosen OS-user trust root; owner-verified **offline** replacement while the daemon is stopped; preserve `local_operator` and journals; invalidate the previous token; do not silently remint an operator; do not require deleting the data root; traces for lost-file + restart, unauthorized local user, and normal rotation.

**Landed:**

| Path | When | Proof | Result |
| --- | --- | --- | --- |
| `rotate-control` | Token still held; daemon live | Current `host_control` | New file; old `host_control_fp1` dead; same `local_operator` (T-H-01 / T-BE-29) |
| `recover-control` | File missing or unreadable; daemon **stopped** | OS user owns `QMA_DAEMON_ROOT`; **no** lost token | New owner-only file; old fingerprint dead; `local_operator` and journals **preserved** (T-H-02 / T-BE-27) |

Negatives: live daemon → refuse (stop first). Other OS user → refuse; root untouched (T-H-04 / T-BE-28). Readable token file still present → refuse (use rotate-control). T-H-03: lost file + restart **without** recover → host-control verbs refuse; pairing proofs still valid until TTL; **no second principal**.

QMA AD-27 backup/restore is **not** this path (CLOSURE: later ops story). Broker allowlist is not widened (AM-15 / local AD-12). First-start empty-root mint remains the only principal mint.

**Parent conflicts named:** extra loopback channel outside 8765 (AM-15 + QMA AD-5 single-port); QMB `host` group including recover (AM-10); `local_operator` projection (AM-03).

**Unnamed (F-1):** AD-17 says recover **journals** the new fingerprint while the daemon is **stopped**. QMA AD-6 sole writer + parent AD-2 + local AD-6 “QMB never writes daemon sqlite” forbid QMB opening that sqlite. HOST restates “sole-writer and lock-release invariants hold.” The legal reading is: QMB is the **door**; a daemon process that does **not** bind 8765 is the **writer**. That reading is implied, not sentenced.

---

## C2 vs parents (origin-revoke vs renew)

**Required by the closure review:** renew first then origin-revoke must revoke the newly issued proof; origin-revoke first makes renewal with the old proof refuse; single-record revocation is a different scope; both orderings traced; journal ordering alone is not a reason to discard the later valid administrative command.

**Landed:** AD-4 + PAIRING lifecycle + HOST `--origin` / `--session` split + T-BE-30/31 + T-P-11/12/13. UI BOOTSTRAP §12 matches: `--origin` is the barrier including a renew that committed earlier; `--session` is that record only.

**Parent:** this is pairing-fold policy over AM-03 projections, serialized by QMA AD-6’s already-single writer (one sqlite connection, one thread). There is no distributed CAS. “Not a CAS loser” means: always **append** the origin-revoke event; then fold. That is how AD-6 already works. Wire first-append-wins (QMA AD-5 producer+id) is the wrong tool and is correctly refused here.

**Does not rewrite:**

- Global monotonic `journal_seq` as the only total order.
- Knowledge-time `as_of` over `recorded_at` (R is event applicability, not a replacement clock).
- Equal-instant ascending `journal_seq`.
- Append-only / never-trim (HOST: does not delete journal history).
- `journal_seq` opacity on the wire as `seq`.
- Closed store list (no extra sqlite class; barrier is not a new AM-03 name).

---

## Findings

### High

None. C1 is not an unauthenticated 8765 bind. C2 does not mint a second sequence or apply wire CAS to drop a later origin-revoke. AM-10 names `recover-control`. J3/J4/J5 are not disturbed.

### Medium

#### F-1 — Recover-control’s journal writer is unnamed (QMA AD-6 sole writer / parent AD-2)

**Where:** local AD-17 “journals the new fingerprint and the invalidation of the previous one”; local AD-6 “QMB never writes daemon sqlite”; HOST recover-control (daemon stopped) + “sole-writer … invariants hold”; AM-10 (verb + OS-owner, no writer process); AM-15 (live channel is token-gated outside 8765).

**Parents:** QMA AD-6 sole writer — no process other than the daemon writes the journal or sqlite. Parent AD-2 — QMB never opens daemon sqlite. QMA AD-5 — unauthenticated bind / single inbound port (must not be “solved” by opening 8765 to journal).

**What:** three conforming units, one of which is a parent miss:

- **Unit A — illegal.** `qmb` opens the stopped daemon’s sqlite/journal and writes `host_control_fp1`. Violates QMA AD-6, parent AD-2, and local AD-6.
- **Unit B — parent-preserving.** `qmb host recover-control` is the door. It invokes `qma-daemon` as a **stopped-listener sole writer** (acquire `.daemon_writer`, append the `local_operator` fold event, mint the owner-only file, exit). **Does not bind 8765.** Does not present the lost token. OS-owner check is the AM-10 gate.
- **Unit C — delayed journal.** Recover writes only the file; next `start` journals the fingerprint. Conflicts with AD-17’s letter (“recover … journals”) and with T-H-03 (start without recover is a different path).

AM-15’s “token-gated loopback channel” describes the **live** host-control path. Recover is the named AM-10 exception (no token, daemon stopped). A 41.4-only reader of AM-15 who then “helps” recover by adding an unauthenticated HTTP route on 8765 is the product this bar forbids.

**Action:** apply if this packet is touched. One sentence on AM-10 / AD-17 / HOST: recover-control is a QMB **door**; the daemon process is the **sole writer**; listener stays down; **not** port 8765; **not** AM-01; QMB still does not open sqlite. Do not implement Unit A. Do not implement recover as unauthenticated HTTP.

### Low

#### F-2 — Origin-revoke `noun.verb` is a template, not a name

AM-03 says each fold’s stream is `noun.verb`. C2 never names the origin-revoke event (`pairing.origin_revoked` or sibling). Two units can both “obey AM-03” with different streams and still fold on `journal_seq`. That is not a rewrite of `journal_seq` rules. Cheap: name the stream on AM-03 / PAIRING and keep ordering `journal_seq`.

#### F-3 — “After R, `/pair/confirm` cannot issue” vs client “re-pair” is not unique

AD-4 / PAIRING: rows with `journal_seq` < R are revoked; after R, `/pair/renew` and `/pair/confirm` refuse; client column says all tabs **re-pair**.

- **Unit A (cutoff):** a **new** `/pair/start` after R (seq > R) + fresh `qmb host pair` + `/pair/confirm` issues. “Cannot issue” applies to pre-R pendings and to renew of pre-R proofs. Matches “re-pair” and `journal_seq` < R.
- **Unit B (sticky):** Origin cannot issue again until an unnamed lift. `journal_seq` < R is then incomplete (later seq also dead).

This is pairing-policy uniqueness, **not** a silent change of how `journal_seq` is allocated. Do not implement the sticky reading as a sqlite flag with no journal event. If touching PAIRING: bind Unit A (new pending after R is the re-pair path) unless the operator wants an explicit lift verb.

#### F-4 — Do not leak `journal_seq` onto the wire as `seq`

QMA AD-5 opacity is currently upheld (confirm body has no `journal_seq`; `qmb host status` prints record ids, not R). Residual only: keep R off CT-40 `seq` and off browser JSON.

---

## Non-conflicts (do not treat as silent overrides)

- **AM-10 names `recover-control`.** Required bar holds.
- **Recover-control is not AM-01 and not a second 8765 bind.** Required bar holds. Live host-control remains AM-15 (outside 8765, token-gated). Pairing unauth HTTP remains start / confirm / OPTIONS only.
- **C2 uses parent `journal_seq` as total order.** Required bar holds. Not a pairing-local seq. Not wire `seq`. Not a trim. Not a CAS that drops the later administrative append.
- **`local_operator` is on AM-03.** C1 preserves it; does not remint; does not wipe the data root.
- **`--session` ≠ `--origin`.** T-P-13: `--session` of an already-renewed id is a recorded no-op; new proof stays live.
- **Rotate vs recover.** Token held → `rotate-control`. Token lost → stop, then `recover-control`. T-BE-29 forbids recover on a live daemon.
- **QMA AD-27** is not replaced by recover-control.
- **Broker allowlist** not widened. No `cred://operator/`. Forged provider ref is still not login (T-P-08 / T-BE-23).
- **QMB remains the only operator CLI.** `host` is a group (AM-10), not a sixth COMP.
- **J3/J4/J5** (daemon draft issuer, `publish_editor_draft` then parent AD-30 enable, reachable TLS + dest `transfer_complete`) are not edited by this correction.
- **JobHandle states, `copilot_profile` sibling, Envelope `instance_id` required, cookies / `localStorage` forbidden for the proof** — unchanged.

---

## What this lens blesses / will not bless

**Blessed for C1/C2 parent bars:**

- AM-10’s `recover-control` name and stopped-root / no-lost-token rule.
- AM-15 + local AD-15: host-control (including recover) is not an unauthenticated 8765 bind.
- C2 barrier as an append at `journal_seq` R plus fold of pairing rows with announcement `journal_seq` < R, history kept, both orderings traced.

**Not blessed (residuals only):**

- QMB as sqlite writer during recover (illegal even if someone ships it).
- Recover HTTP on 8765.
- Origin-revoke as wire first-append-wins CAS, as derived per-scope `seq`, or as a sqlite flag with no journal event.

---

## Reviewer action for the sitting

Do **not** return C1/C2 as a parent override of QMA AD-5 or QMA AD-6.

If the packet is touched before Documentation Factory, cheap:

1. AM-10 / AD-17 / HOST: recover-control = QMB door + daemon sole writer with **listener down**; not 8765; QMB does not open sqlite.
2. Name the origin-revoke `noun.verb`; keep ordering `journal_seq`.
3. PAIRING: after R, re-pair is a **new** `/pair/start` + QMB pair + confirm (seq > R); `/pair/confirm` of pre-R pendings cannot issue; `/pair/renew` of pre-R proofs refuses.

Do not implement. Do not run Documentation Factory. Do not rewrite epics. Do not widen the broker allowlist. Do not add recover to AM-01. Do not put `journal_seq` on the wire as `seq`.
