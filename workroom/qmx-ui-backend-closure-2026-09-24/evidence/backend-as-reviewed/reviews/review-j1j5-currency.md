---
name: J1–J5 currency / inspect-honesty review
sitting: architecture-QMX-UI-BACKEND-2026-09-24
date: 2026-09-24
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
worktree: C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect
status: independent review — not operator-accepted
scope: committed J1–J5 decisions in live law only; first-pass reviews/ are historical and were not edited
tests: unexecuted
---

# Review — J1–J5 currency / inspect-honesty

**Question.** Was every committed J1–J5 decision reality-checked against inspect SHA `34c148be` and the cited RFCs/WHATWG text, or asserted from training data?

**Live law.** `ARCHITECTURE-SPINE.md` AD-3..AD-17 (J1–J5 bind AD-4, AD-6, AD-9, AD-11, AD-12, AD-14, AD-17 plus mailbox/cancel `_ref` reconciliations). Companions: `CLOSURE-J1-J5.md`, `HOST-LIFECYCLE.md`, `PAIRING-AND-ADMISSION.md`, `PACK-UI-AND-AUTHORING.md`, `ARTIFACTS-AND-TRANSFER.md`, `PROVIDER-AND-COMPAT.md`, `MAILBOX-AND-DELIVERY.md`, `CANCEL-AND-HANDLES.md`, `PARENT-AMENDMENT-MAP.md` AM-14.

**Not in scope.** Implementation. Documentation Factory. Epic rewrite. Editing first-pass `reviews/`. Treating planned names as delivered (DEC-0286).

Nothing below is from training data. Inspect claims were re-read at `.worktrees/integration-inspect` HEAD `34c148be404a375cbfd79fd4ce6997452e4f1d20`. RFC/WHATWG sentences were fetched 2026-09-24.

---

## Verdict

**PASS.**

J1–J5 live law classifies inspect types as **absent / planned adds**, not e2e (AD-2, DEC-0286). Named commands and the `qmb host` CLI group are absent. Envelope has no `product_session_ref`. JobHandle has no `originating_product_session_ref`. Broker allowlist prefixes are unchanged. `authenticate_before_protocol` is shape-only. Cited RFC 6750 §1.2, RFC 6455 token charset, HTML sessionStorage copy-over, and RFC 9110 PUT / §14.5 / §8.6 exist at the named sections. No invented RFC edition.

One Low wiring nit (L-1): J2 correctly cites RFC 6750 **§1.2** (possession authorizes) but the committed header form `Authorization: Bearer pairing:<proof>` is not RFC 6750 §2.1 `b64token` (colon is excluded). That is a factory bind, not an inspect-honesty fail.

---

## Method

| Check | How |
| --- | --- |
| SHA | `git -C .worktrees/integration-inspect rev-parse HEAD` = `34c148be404a375cbfd79fd4ce6997452e4f1d20`. Subject: `story 59.5: grant refuses the wrong instance or config revision`. |
| Inspect files | `qma/daemon/process.py`, `qma/daemon/__main__.py`, `qma/wire/auth.py`, `qma/wire/vocabulary.py`, `qma/core/ports/mailbox.py`, `qma/core/ports/jobs.py`, `qma/core/barriers/credential_allowlist.py`, `qma/core/plugins/credential.py`, `qma/core/plugins/manifest.py`, `qma/daemon/envs/jobs.py`, `qma/daemon/sessions/product_session.py`, `qmb/doors/cli/tree.py`, `qmb/host/__init__.py` |
| Name absences | ripgrep over `qmx-agents/**/*.py` for the J1–J5 addable names |
| Parent `_ref` law | `architecture-QMA-2026-08-28/ARCHITECTURE-SPINE.md` Consistency Conventions (Data & formats) |
| RFCs | datatracker RFC 6750 (Oct 2012); RFC 6455 (Dec 2011) §4.1 / §11.3.4 + RFC 2616 token; RFC 9110 (June 2022) §9.3.4 / §14.5 / §8.6 |
| HTML | `https://html.spec.whatwg.org/multipage/webstorage.html` Living Standard — Last Updated **22 September 2026** (still that date on 2026-09-24) |

---

## 1. Inspect SHA `34c148be` — required facts

### 1.1 DaemonProcess discards TCP

`qma-daemon/src/qma/daemon/process.py`: `DEFAULT_BIND_PORT = 8765`. `bind()` calls `asyncio.start_server(self._handle_client, host=self._posture.host, port=self._bind_port)`. `_handle_client` loops `await reader.read(65536)` and never writes protocol bytes; `finally` closes the writer.

**Match.** Loopback TCP swallow. Not HTTP, not WebSocket, not JSON-RPC. Spine Structural Seed now says `inspect: discards TCP bytes. This sitting names the live HTTP+WS contract.` (first-pass I-1 wording is closed in live seed).

`__main__.py`: `QMA_DAEMON_ROOT` default `"qma-daemon-data"`. HOST-LIFECYCLE’s “inspect cwd-relative default is not the product root” is honest.

### 1.2 No `qmb host` CLI group

`qmb/src/qmb/doors/cli/tree.py`:

```
COMMAND_GROUPS = ("backtest", "data", "optimize", "sweep", "robustness",
                  "ledger", "library", "analysis", "config")
```

Zero `host` group. Package `qmb.host` exists as **CT-33 bot hosting** (`qmb/src/qmb/host/__init__.py`: “QMB composition-root hosting for conformant CT-33 bots”). Different noun. Sitting cites the CLI tree. Honest.

J1 verbs (`qmb host start|status|stop|pair|configure|rotate-control`) are **planned** (AM-10 / AD-6 / AD-17). Until they exist, HOST-LIFECYCLE says UI Start local is setup copy. Honest.

Zero hits in inspect Python for `host_control`, `/pair/`, `pairing_proof`, `pairing_pending`.

### 1.3 Envelope has no `product_session_ref`

`qma/core/ports/mailbox.py`:

- Required: `msg_id`, `from`, `to`, `kind`, `correlation_id`, `body`, `priority`, `created_at`
- Optional refs: `mission_ref`, `task_ref`, `reply_to_ref`, `causation_id`
- Extra: `artifact_refs`
- `ENVELOPE_FP1_EXCLUDED_FIELDS` = `{correlation_id, causation_id}` only
- Dataclass `Envelope` matches. **No** `product_session_ref`. **No** `product_session_id` on Envelope.

`ProductSession.product_session_id` **does** exist on the product-session row (`sessions/product_session.py`, sqlite PK). AM-14 / AD-7 correctly keep own identity as `product_session_id` and add the Envelope **pointer** as `_ref`. Absence is scoped to Envelope. Honest.

### 1.4 JobHandle has no `originating_product_session_ref`

`qma/core/ports/jobs.py` `JobHandle` fields: `job_id`, `owner`, `state`, `task_id`, `wake_mailbox`, abort/unknown/correlation, `logical_run_id`, `attempt_id`, `artifacts`, `later_commands`. **No** `originating_product_session_ref`. **No** `originating_psess`.

`JobHandleStore` (`daemon/envs/jobs.py`) is an in-memory `dict`. Docstring says “Durable”; persistence is still planned (Epic 57). Class existence ≠ delivery (DEC-0286). CANCEL honesty (“`later_commands` exists. Session pointer absent.”) matches.

### 1.5 Credential allowlist is not widened

`qma-core/src/qma/core/barriers/credential_allowlist.py` `ALLOWED_CREDENTIAL_REF_PREFIXES`:

```
cred://models/  cred://inference/  cred://compute/  cred://sandbox/
cred://corpus/  cred://knowledge/  cred://telemetry/
```

Out-of-scope: `cred://venue|broker|exchange|trading-node|platform-registry/`.

**No** `cred://operator/`, `cred://pairing/`, `cred://host_control/`. `assert_allowlist_not_widenable` refuses supersets. AD-12 / AM-15 / PROVIDER “allowlist not widened” is file-true at inspect.

Inspect **tests/examples** use shape strings `cred://operator/ui` and `cred://operator/desk` (`qma-wire` tests). Those are **not** allowlist prefixes. `parse_credential_ref` is opaque-shape, not broker classification. Sitting does not mint an operator-login family. Honest.

### 1.6 `authenticate_before_protocol` is shape-only

`qma/wire/auth.py`:

- `authenticate_before_protocol(credential_ref, *, principal_class)` → `parse_credential_ref` + `parse_principal_class` (`operator` | `machine`). **Does not** call the broker. **Does not** consult the allowlist.
- `AuthenticatedWireSession` fields: `credential_ref`, `principal_class`, `authenticated_before_protocol`. **No** `pairing_record_id`. **No** Origin.
- `FORBIDDEN_SECRET_SURFACE_KEYS` includes `token`, `bearer`, `secret`, `password`, `api_key`, `access_token`, `refresh_token`, `credential_value`, `resolved_credential`.

`parse_credential_ref` (`qma/core/plugins/credential.py`) accepts any non-empty opaque string ≤256 chars that does not look like `secret=` / `password=` / `token=` / `bearer `. **`pairing:<proof>` would pass this gate.** That inspect fact is why AM-11 exists (do not pass the proof to `parse_credential_ref`; browser session carries `pairing_record_id` + operator principal, **no** `credential_ref`). Reality-checked, not invented.

PAIRING / AM-11: surface scan extended by **value class** (raw proofs), not only key spelling. Inspect scan is key-name + inline prefix. Candidate add. Honest.

### 1.7 QMA `_ref` law / exception list

Parent `architecture-QMA-2026-08-28` Consistency Conventions (Data & formats): own identity is `id` or `_id`; cross-store pointers are `_ref`; **exactly ten** named exceptions:

`correlation_id`, `causation_id`, `producer_id`, `attempt_of`, `approval_route`, `scope_path`, `from`, `to`, `authored_by`, `proposer`.

AM-14: Envelope/handle pointers named `product_session_id` / `originating_psess` would fail that validator. Use `product_session_ref` and `originating_product_session_ref`. Do **not** add the old names to the exception list. ProductSession own id stays `product_session_id`.

**Match** against the live parent spine. Exception list unchanged. This is parent-law currency, not inspect delivery.

### 1.8 Named commands / queries absent

ripgrep of `integration-inspect/qmx-agents/**/*.py`: **zero** matches for

`list_mailbox`, `cancel_job`, `publish_editor_draft`, `get_pack_ui_request`, `transfer_complete`, `save_editor_draft`, `transfer_artifact`, `stage_artifact`.

Wire vocabulary at inspect: nine seed commands including `send_message` and `stop_run`; queries = seven seed + `list_mission_hooks`, `plugin_install_preflight`, `facade_search`, `facade_get`.

`PluginManifest` fields: `id`, `version`, `qma_api`, `desk`, `entrypoint`, `dependencies`, `contributions`, `permissions`, `migrations`, `rollback`, `contributes`. **No** `copilot_profile`.

J3/J4/J5 names are addable (AM-09 / AM-16), not present. Companions’ “Honesty at inspect” footers match.

`send_message` **name** exists. Socket dispatch of that name is still absent (MAILBOX honesty). DEC-0286.

---

## 2. RFC / WHATWG — no invented versions

### 2.1 RFC 6750 §1.2 — bearer definition (J2)

Fetched 2026-09-24: RFC 6750, October 2012.

§1.2 Terminology:

> Bearer Token — A security token with the property that any party in possession of the token (a "bearer") can use the token in any way that any other party in possession of it can. Using a bearer token does not require a bearer to prove possession of cryptographic key material (proof-of-possession).

AD-4 / PAIRING §1 / CLOSURE-J1-J5 J2: `pairing_proof` is a bearer; possession authorizes; journal stores `proof_fp1` only. **That property is the real §1.2 sentence.** Not a forged clause. RFC is not “6750bis”.

PAIRING also forbids query-string proofs. RFC 6750 §2.3 / §5.3: URI query transport is not recommended; “Don't pass bearer tokens in page URLs.” Match.

Cookies refused. RFC 6750 §5.3: do not store bearer tokens in cookies that can be sent in the clear. Sitting is stricter (no cookies at all). Overlay, not a fake cite.

**L-1 (Low) — header ABNF not checked against §2.1.** RFC 6750 §2.1:

```
b64token    = 1*( ALPHA / DIGIT /
                  "-" / "." / "_" / "~" / "+" / "/" ) *"="
credentials = "Bearer" 1*SP b64token
```

Colon `:` is **not** in `b64token`. Live form `Authorization: Bearer pairing:<proof>` is a QMX discriminator sitting on Bearer. It is **not** §2.1 ABNF-legal. J2 cites §1.2 (possession), not §2.1 (header syntax). First-pass `review-currency.md` never fetched RFC 6750 at all.

Factory bind (not a sitting fail): the proof alphabet must be token68/b64token-legal **and** RFC 6455 token-legal. Do not put `:` in the Bearer token68 string. Discriminator is already the `Bearer` scheme plus the pairing table; or use RFC 9110 `auth-param` form. WS form `qmx.pair.<proof>` correctly does **not** embed `pairing:`.

RFC 6750 §5.3 “Always use TLS (https)” is **not** what J2 cites. v1 workstation loopback HTTP is a product overlay (AM-01 / AD-15). Do not claim RFC 6750 transport compliance for loopback pairing.

### 2.2 RFC 6455 — WebSocket subprotocol token charset (J2)

RFC 6455, December 2011. Not 6455bis.

§4.1 step 10 (normative): `Sec-WebSocket-Protocol` elements MUST be non-empty strings in U+0021..U+007E **not including RFC 2616 separator characters**. ABNF `1#token` per RFC 2616.

§11.3.4 / §4.3: `Sec-WebSocket-Protocol-Client = 1#token`.

RFC 2616 §2.2:

```
token      = 1*<any CHAR except CTLs or separators>
separators = "(" | ")" | "<" | ">" | "@"
           | "," | ";" | ":" | "\" | <">
           | "/" | "[" | "]" | "?" | "="
           | "{" | "}" | SP | HT
```

Colon, slash, and `=` are **separators**. Standard Base64 (`+/` and `=` padding) is **not** a legal subprotocol token. `qmx.pair.<proof>` is legal only if `<proof>` itself is token-safe (letters, digits, `-`, `.`, `_`, `~`, `+` are fine; `: / =` are not).

PAIRING: “High-entropy, unguessable, WebSocket-token-safe (RFC 6455 token charset).” CLOSURE-J1-J5 J2 deferral: entropy/length is an implementation story; must be unguessable and WS-token-safe. **Charset constraint is real RFC 6455/2616. Alphabet not minted. Honest deferral.**

§1.3: server echoes **one** selected `Sec-WebSocket-Protocol`. Unchanged from first-pass currency. Not re-litigated here.

### 2.3 HTML Web storage — sessionStorage tab-scoped, copied to clone (AD-14)

Living Standard — Last Updated **22 September 2026** (fetched 2026-09-24). Spine source `HTML-webstorage-2026-09-22` is that snapshot date, not an invented HTML edition.

§12.1: each window has its own copy of session storage.

§12.2.2: “After creating a new auxiliary browsing context and document, the session storage is copied over.”

`localStorage` “lasts beyond the current session.” Sitting forbids it for pairing proof (AD-14 / PARENT map §C). Cold start / closed tab empties sessionStorage. Cloned/auxiliary tab with copied storage is **existing proof**, not Origin-only issuance.

**Match** AD-14 / PAIRING §6 / CLOSURE-J1-J5 small reconciliation. Not training-data.

### 2.4 RFC 9110 — PUT completeness (J5)

RFC 9110, June 2022 (STD 97). Not 9111-as-PUT.

§9.3.4: “The PUT method requests that the state of the target resource be created or replaced with the state defined by the representation enclosed in the request message content.” Success is processing of that enclosed representation.

§9.3.4-12 points at §14.5 Partial PUT (Content-Range request modifier). §14.5 exists. v1 “no RFC 9110 §14.5 partial PUT” is product policy the RFC allows (origin SHOULD 400 if unsupported).

§8.6: `Content-Length` “indicates the associated representation's data length as a decimal non-negative integer number of octets.” When transferring as content it “refers specifically to the amount of data enclosed so that it can be used to delimit framing.”

Sitting: Content-Length required; completeness = daemon-recomputed fp1 **plus** byte count; interrupted v1 PUT refused and deleted. **fp1 + byte-count is QMX policy**, not an RFC sentence. Framing completeness (Content-Length delimits the enclosed representation; incomplete body is not a successful PUT) is the RFC substrate. Honest overlay. No ghost section.

---

## 3. J1–J5 decisions vs evidence

| ID | Committed choice | Inspect / RFC | Honesty |
| --- | --- | --- | --- |
| **J1** | First operator = OS user of `QMA_DAEMON_ROOT` + daemon-minted `host_control` on loopback; not CT-40; not `/pair/*`; not a provider `cred://`; TTL before issue | No `host` CLI group; no `host_control`; allowlist has no operator family; `authenticate_before_protocol` is shape-only; default root `"qma-daemon-data"` | **Planned add.** Forged `cred://models/…` as login is a **candidate** refusal, not inspect behavior (shape gate would accept the string; allowlist is a different gate). Sitting does not claim inspect implements host-control. |
| **J2** | `pairing_proof` bearer vs `pairing_record_id`; hash-only journal; confirm once; rotate/expiry/revoke | RFC 6750 §1.2 real; pairing HTTP **absent**; `FORBIDDEN_SECRET_SURFACE_KEYS` is key-list; AM-11 needed because `parse_credential_ref("pairing:…")` succeeds | **Planned add** on real RFC property. L-1 on §2.1 header ABNF. RFC 6455 token charset real; alphabet deferred. |
| **J3** | Daemon sole durable `editor_draft_id`; UI `client_draft_correlation` only | `save_editor_draft`, `editor_draft_id` **absent** | **Planned add.** PACK-UI honesty matches. |
| **J4** | Addable `publish_editor_draft`; parent AD-30 enable remains compile identity | `publish_editor_draft`, `get_pack_ui_request` **absent**; `copilot_profile` absent on `PluginManifest` | **Planned add.** Does not treat inspect types as publication. |
| **J5** | Recorded TLS or `source_unreachable`; dest-authored `transfer_complete`; invoke waits | `transfer_artifact`, `transfer_complete`, PUT `/artifacts/stage` **absent**. RFC 9110 §14.5 real | **Planned add** on real PUT/partial-PUT sections. Completeness-as-fp1 is QMX. |
| Mailbox `_ref` | Envelope pointer `product_session_ref`; own id stays `product_session_id` | Envelope field absent; ProductSession own id present; parent ten-exception list unchanged | AM-14 parent-correct. Inspect absence honest. |
| Cancel `_ref` | Optional `originating_product_session_ref` | Field absent; `later_commands` present; `cancel_job` absent | Honest. |
| Allowlist | Not widened | Seven prefixes; `assert_allowlist_not_widenable` | File-true. |

DEC-0286 (workbench rider): class/test existence is not end-to-end demonstration. Spine AD-2 restates it. JobHandle types, Envelope types, and `send_message` as a vocab name are **not** a live pairing/mailbox/cancel/transfer protocol. Sitting does not claim otherwise.

---

## 4. Out of date (not live law)

| Locus | Drift | Disposition |
| --- | --- | --- |
| `research/00-inspect-and-sources.md` | Envelope absence still labelled `product_session_id`; cloned-tab sentence still says `pairing_session_id`; primary-sources table has **no RFC 6750** and **no RFC 6455 token charset** | Evidence-not-law. Inspect facts (fields absent) remain true under the new names. File was not re-stamped for J1–J5. **I-1.** |
| First-pass `reviews/review-currency.md`, `review-adversarial.md`, `review-rubric.md`, `review-parent-consistency.md`, `review-r2-closure.md`, `reconcile-inputs.md` | Pre-J2 nouns: `pairing_session_id`, Envelope `product_session_id`, `originating_psess`; first currency pass never fetched RFC 6750 | Historical. CLOSURE-EVIDENCE already says they were not rewritten. This review does not edit them. |
| `.memlog.md` | Early R2 lines use `pairing_session_id`; later J2 line uses `pairing_proof` | Log, not law. |

Live spine, companions, `CLOSURE-J1-J5.md`, `START-HERE.md` honesty table, and AM-14 use the J1–J5 names. Do not treat first-pass reviews as the candidate.

---

## Findings

### L-1 — `Bearer pairing:<proof>` is not RFC 6750 §2.1 `b64token` (Low)

- **Cite:** J2 / AD-4 / PAIRING §1: `Authorization: Bearer pairing:<proof>`.
- **RFC 6750 §2.1:** `credentials = "Bearer" 1*SP b64token`; `b64token` charset has no colon.
- **§1.2 possession cite is correct.** Header form was not reality-checked against the ABNF this sitting also implies by saying “RFC 6750 bearer”.
- **WS side is cleaner:** `qmx.pair.<proof>` never embeds `pairing:` and is constrained to RFC 6455/2616 `token` (no `: / =`).
- **Bind for implementers (not a spine rewrite here):** mint a token68- **and** RFC 6455-token-safe proof; present `Authorization: Bearer <proof>` (or RFC 9110 auth-param); keep `pairing:` out of both the Bearer token68 string and the subprotocol token.

### I-1 — `research/00-inspect-and-sources.md` not re-verified for J1–J5 RFCs/names (Informational)

Evidence file still talks `pairing_session_id` / Envelope `product_session_id` and omits RFC 6750 and the RFC 6455 token charset. Live law is current. Optional desk stamp if the evidence file is touched; not a fail.

### I-2 — RFC 6750 TLS MUST vs v1 loopback HTTP (Informational)

§5.3 “Always use TLS” is not the section J2 cites. Workstation-local pairing HTTP is an explicit product overlay (AD-5 / AD-15 / AM-01). Do not advertise RFC 6750 **transport** compliance. Query-string refusal still matches §2.3 / §5.3.

### Informational (not findings)

- `qmb.host` Python package is CT-33. “No `host` CLI group” remains true.
- Inspect examples `cred://operator/ui` are shape-gate fixtures, not allowlist widening.
- `JobHandleStore` docstring says “Durable”; store is an in-memory dict. DEC-0286.
- HTML living standard last-updated **22 September 2026** still holds on 2026-09-24.
- First-pass Structural Seed “live HTTP + WS” nit is already corrected in the live spine.

---

## Training-data assertions

**None** for the inspect set (TCP swallow, no `qmb host` group, Envelope/JobHandle field absences, allowlist prefixes, shape-only auth, `FORBIDDEN_SECRET_SURFACE_KEYS`, named-command absences, parent ten-exception `_ref` list, ProductSession own `product_session_id`).

**None** for RFC 6750 §1.2, RFC 6455/2616 token charset, HTML sessionStorage copy-over, RFC 9110 §9.3.4 / §14.5 / §8.6.

L-1 is a **missed ABNF check** on a form the sitting committed, not a hallucinated RFC.

---

## Summary table

| Item | Claimed (J1–J5 live law) | Live / inspect 2026-09-24 | Posture |
| --- | --- | --- | --- |
| Inspect SHA | `34c148be` | `34c148be404a375cbfd79fd4ce6997452e4f1d20` | Match |
| Daemon listener | discards TCP | `read(65536)` swallow | Honest |
| `qmb host` | absent; planned AM-10 | not in `COMMAND_GROUPS`; `qmb.host` is CT-33 | Honest |
| Envelope `product_session_ref` | absent; AM-02 add | not on `Envelope` | Honest |
| JobHandle `originating_product_session_ref` | absent; AM-04 add | not on `JobHandle`; in-memory store | Honest |
| Allowlist | not widened | seven `cred://` prefixes; no operator family | Honest |
| `authenticate_before_protocol` | shape-only | parse ref + principal; no broker | Honest |
| `FORBIDDEN_SECRET_SURFACE_KEYS` | includes `token`/`bearer` | yes; value-class scan is AM-11 add | Honest |
| QMA `_ref` exceptions | ten; unchanged | ten named in QMA 08-28 conventions | Parent-true |
| `list_mailbox` `cancel_job` `publish_editor_draft` `get_pack_ui_request` `transfer_complete` | absent | 0 hits in inspect Python | Honest |
| RFC 6750 §1.2 | possession authorizes | confirmed Oct 2012 | Real RFC |
| RFC 6750 §2.1 header | live form `Bearer pairing:<proof>` | colon not in `b64token` | **L-1** |
| RFC 6455 token charset | WS-token-safe proof | §4.1 / RFC 2616 separators; `: / =` illegal | Real; alphabet deferred |
| HTML sessionStorage | tab-scoped; auxiliary copy | LS 22 Sep 2026; §12.2.2 copy sentence | Real |
| RFC 9110 PUT / §14.5 / §8.6 | no partial PUT; Content-Length | confirmed June 2022 | Real; fp1 completeness is QMX |
| DEC-0286 | planned ≠ implemented | types/fixtures exist; no live protocol | Honest |

---

## Gate

J1–J5 currency / inspect-honesty **PASS**.

Required inspect facts are file-true at `34c148be`. Cited RFC 6750 §1.2, RFC 6455 token charset, HTML sessionStorage, and RFC 9110 PUT sections exist; none is an invented edition. Allowlist is not widened. Named J1–J5 commands/queries and `qmb host` are absent. Envelope/handle `_ref` fields are absent; ProductSession own `product_session_id` is present; parent exception list unchanged.

L-1 is a Low factory bind on Bearer ABNF (`pairing:` colon). I-1 is stale research-00 naming. Neither treats inspect types as delivered. Candidate ≠ operator acceptance. Tests unexecuted.
