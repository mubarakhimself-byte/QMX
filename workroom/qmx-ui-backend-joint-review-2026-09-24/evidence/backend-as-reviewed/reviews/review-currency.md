# Review — Currency / inspect-honesty (UI backend-delta)

**Spine:** `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/ARCHITECTURE-SPINE.md` (draft 2026-09-24, local AD-1..AD-16)
**Evidence consulted:** `research/00-inspect-and-sources.md`, `START-HERE.md`, companions’ “Honesty at inspect” sections
**Lens:** committed inspect facts and cited primary sources must be reality-checked, not asserted from training data. Frontend pins must not become required backend pins. CPython 3.14 is inherited.
**Brownfield cite:** `integration@34c148be` via `.worktrees/integration-inspect`
**Reviewer gate date of checks:** 2026-09-24

Web (primary sources, this sitting): RFC 6455 §10.1 and §1.3 (datatracker); WHATWG WebSockets Living Standard (last updated 15 March 2026); HTML Web storage Living Standard (last updated 22 September 2026); RFC 9110 §9.3.4 PUT, §14.5 Partial PUT, §8.6 Content-Length; Fetch CORS table (`credentials` × `Access-Control-Allow-Origin`); python.org Latest Python 3.14.7 (released 2026-08-05).

Code (inspect worktree, this sitting): `git rev-parse HEAD` = `34c148be404a375cbfd79fd4ce6997452e4f1d20` (same as `integration`). Files read: `qma/daemon/process.py`, `qma/wire/vocabulary.py`, `qma/core/ports/mailbox.py`, `qmb/doors/cli/tree.py`, plus `qma/wire/auth.py`, `qma/core/ports/jobs.py`, `qma/core/plugins/manifest.py`, `qma/daemon/envs/jobs.py`, `qma/daemon/__main__.py`.

Nothing below is from training data. Every inspect “exists / absent” claim was read at `34c148be`. Every RFC/WHATWG/HTML sentence was fetched on 2026-09-24.

---

## Verdict

**PASS.**

Inspect SHA `34c148be` facts hold. `DaemonProcess` binds loopback TCP and discards bytes. `send_message` is in the seed command vocabulary. `list_mailbox`, `cancel_job`, pairing HTTP, `copilot_profile`, `caller_kind`, `originating_psess`, and Envelope `product_session_id` are absent. QMB `COMMAND_GROUPS` has no `host`. Cited primary sources exist at the named sections; none is an invented version pin. Stack inherits CPython 3.14 and does not mint frontend pins as required backend pins.

One informational wording nit: Structural Seed labels `process.py` “live HTTP + WS (today discards bytes)”. Inspect is a TCP `asyncio.start_server` that swallows octets. START-HERE and research 00 are the honest present tense. Not a fail.

---

## 1. Inspect SHA `34c148be` — required facts

Worktree `.worktrees/integration-inspect` HEAD = `34c148be404a375cbfd79fd4ce6997452e4f1d20`. Same as workspace `integration`. Commit subject: `story 59.5: grant refuses the wrong instance or config revision`.

| Claim (task / sitting) | Evidence at inspect | Honesty |
| --- | --- | --- |
| `DaemonProcess` discards bytes | `process.py` `DEFAULT_BIND_PORT = 8765`. `bind()` uses `asyncio.start_server(self._handle_client, host=self._posture.host, port=self._bind_port)`. `_handle_client` loops `await reader.read(65536)` and never writes protocol bytes; `finally` closes the writer. | **Match.** Loopback TCP swallow. Not JSON-RPC, not HTTP, not WebSocket. |
| `send_message` in vocab | `WireCommand.SEND_MESSAGE = "send_message"` among nine seed commands. `SEED_COMMAND_COUNT = 9`. `stop_run` also present. | **Match.** Name exists. Socket dispatch of that name is still absent (MAILBOX honesty section). |
| `list_mailbox` / `cancel_job` absent | Zero hits for `list_mailbox`, `cancel_job`, `stage_artifact`, `transfer_artifact` under the inspect tree. Queries are the seven seed plus `list_mission_hooks`, `plugin_install_preflight`, `facade_search`, `facade_get`. | **Match.** Addable, not delivered. |
| pairing absent | Zero `/pair/start` / `pairing_session` in inspect Python. `auth.py` `authenticate_before_protocol` takes `credential_ref` + `principal_class` (`operator` \| `machine`). `FORBIDDEN_SECRET_SURFACE_KEYS` includes `token` / `bearer`. No pairing map. | **Match.** PAIRING companion: `/pair/*`, Bearer pairing, WS subprotocols, CORS **absent**. |
| `copilot_profile` absent | `PluginManifest` fields: `id`, `version`, `qma_api`, `desk`, `entrypoint`, `dependencies`, `contributions`, `permissions`, `migrations`, `rollback`, `contributes`. Zero `copilot_profile` in inspect Python. | **Match.** |
| `caller_kind` absent | Zero hits in inspect Python. | **Match.** Specified Epic 60; not on the wire types. |
| `originating_psess` absent | `JobHandle` fields: `job_id`, `owner`, `state`, `task_id`, `wake_mailbox`, abort/unknown/correlation, `logical_run_id`, `attempt_id`, `artifacts`, `later_commands`. No `originating_psess`. `JobHandleStore` is an in-memory dict. | **Match.** |
| Envelope has no `product_session_id` | `ENVELOPE_REQUIRED_FIELDS`: `msg_id`, `from`, `to`, `kind`, `correlation_id`, `body`, `priority`, `created_at`. Optional: `mission_ref`, `task_ref`, `reply_to_ref`, `causation_id`. `artifact_refs` extra. Dataclass matches. No `product_session_id`. | **Match.** (`product_session_id` does appear on **other** types: view presentation, contribution listing, product-session service. Sitting correctly scopes the absence to the mailbox Envelope.) |
| QMB `COMMAND_GROUPS` has no `host` | `COMMAND_GROUPS = ("backtest", "data", "optimize", "sweep", "robustness", "ledger", "library", "analysis", "config")`. `_COMMAND_TREE` has no `host` group. | **Match.** Package `qmb.host` exists as CT-33 bot hosting — a different noun. Sitting cites the CLI tree, not that package. Honest. |

Additional inspect facts the sitting states and this pass re-read:

| Sitting locus | Claim | Check |
| --- | --- | --- |
| START-HERE honesty table | Live CT-40 server **No**; `send_message` name **Yes**; pairing / `list_mailbox` / `cancel_job` / `qmb host` **Absent** | Matches files above. |
| HOST-LIFECYCLE | `python -m qma.daemon` exists; default root cwd-relative `"qma-daemon-data"` is **not** the shipped product root | `__main__.py` `QMA_DAEMON_ROOT` default `"qma-daemon-data"`. Honest. |
| ARTIFACTS | PUT `/artifacts/stage` **absent**; cite-copy through `before_artifact_register` present | Zero PUT path. Honest. |
| AD-2 / research 00 | Class/fixture existence is not delivery (DEC-0286) | Spine forbids treating inspect types as e2e. Honest. |
| CLOSURE-EVIDENCE | No live daemon, no tests executed | This pass did not start the daemon. Sitting does not claim runtime observation. |

**No spine or companion sentence treats `34c148be` types as a live protocol.** Candidate ADs describe **adds**. Companions end with “Honesty at inspect”. START-HERE is the present-tense table.

---

## 2. Primary sources cited — no invented version pins

Spine `sources:` `RFC-6455`, `WHATWG-WebSockets`, `HTML-webstorage-2026-09-22`, `RFC-9110`. Research 00 table checked against live specs today.

| Cite | Sitting’s used fact | Live 2026-09-24 | Invented pin? |
| --- | --- | --- | --- |
| RFC 6455 §10.1 | Non-browser clients can send fake Origin; servers must not assume Origin identifies the operator | §10.1 *Non-Browser Clients*: hosts “can therefore send fake \|Origin\| header fields, misleading the server. Servers should therefore be careful about assuming that they are talking directly to scripts from known origins.” | **No.** RFC is December 2011; no fake RFC number. “Operator identity” is a QMX overlay on “scripts from known origins”, not a forged clause. |
| RFC 6455 §1.3 / handshake | Server echoes **one** selected `Sec-WebSocket-Protocol` | §1.3: “The server selects one or none of the acceptable protocols and echoes that value in its handshake.” Example server handshake has a single `Sec-WebSocket-Protocol: chat`. | **No.** |
| WHATWG WebSockets | `new WebSocket(url, protocols)`; connection only if the server selects one offered subprotocol; browsers do not expose Authorization on the constructor | Living Standard — Last Updated **15 March 2026**. Constructor is `(url, optional protocols = [])`. “The connection will only be established if the server reports that it has selected one of these subprotocols.” No headers argument. RFC 6455 §4.1 step 12 still *allows* Authorization on the protocol for non-browser clients — sitting’s “constructor has no Authorization” is the WHATWG API fact, not a denial of the RFC MAY. | **No version pin.** Sitting does not date-stamp WHATWG as a frozen edition. |
| HTML Web storage | `sessionStorage` is per window/tab; after creating a new auxiliary browsing context, session storage is copied over | Living Standard — **Last Updated 22 September 2026**. Intro: each window has its own copy. §12.2.2: “After creating a new auxiliary browsing context and document, the session storage is copied over.” | **No invented spec version.** `HTML-webstorage-2026-09-22` is the living-standard snapshot date, still true today (2026-09-24). Not HTML5.4 or a fake numbered edition. |
| RFC 9110 PUT | PUT is idempotent; §14.5 defines partial PUT — v1 QMX does not use it | §9.3.4: “the intent of PUT is idempotent”. §9.3.4-12 points at §14.5. §14.5 *Partial PUT* exists (Content-Range request modifier; origin SHOULD 400 if unsupported). | **No.** RFC 9110 is June 2022. §14.5 is real. Sitting refuses it as product policy, which RFC allows. |
| RFC 9110 §8.6 | Content-Length describes request content; incomplete body is not a completed PUT | §8.6: Content-Length is the associated representation’s data length in octets; when transferring as content it “refers specifically to the amount of data enclosed” so it can delimit framing. | **No fake section.** “Incomplete body ≠ completed PUT” is QMX completeness policy built on that delimiter, not a forged RFC sentence. |
| Fetch CORS (research 00) | `credentials: 'omit'` + exact `Access-Control-Allow-Origin`; `*` incompatible with credentialed include; Authorization needs `Access-Control-Allow-Headers` | Fetch CORS table: omit + `*` ✅; include + `*` ❌ (“cannot be `*`”). Authorization is not a CORS-safelisted request header. | **No.** Pairing’s `credentials: 'omit'` + reflect-exact-Origin is a legal combination (omit + exact origin also ✅). |

**No invented version pins.** No “RFC 6455bis”, no “WebSockets 2026-09”, no HTML numbered edition, no RFC 9111-as-PUT.

---

## 3. Stack — CPython 3.14 inherited; no required frontend backend-pins

Spine Stack header: “Inherited runtime. This sitting adds no frontend pins.”

| Name | Spine | Check 2026-09-24 | Posture |
| --- | --- | --- | --- |
| CPython (daemon, QMB) | **3.14 (inherited; observed 3.14.6 at parent freeze)** | python.org Latest **3.14.7** (released 2026-08-05). Parent 09-18 spine: “observed 3.14.6 at 270e992”. UI 09-23 spine same inherited series. | **Correct.** Series pin inherited. Does not invent 3.14.8. Does not upgrade to 3.14.7 in this sitting. |
| qma-wire / qma-daemon / qma-core | packages at inspect `34c148be` plus named adds | Worktree SHA matches. Adds are named (`list_mailbox`, `cancel_job`, …), not claimed present. | Honest brownfield + delta |
| Default bind | `127.0.0.1:8765` | `DEFAULT_BIND_HOST = "127.0.0.1"`; `DEFAULT_BIND_PORT = 8765` | Match |
| Persistence | journal + sqlite under `QMA_DAEMON_ROOT` | `__main__.py` reads `QMA_DAEMON_ROOT` | Match as env; product per-user path is a named add (HOST-LIFECYCLE) |
| UI host | **out of scope here** — Svelte 5.57.1 + SvelteKit 2.70.3 **as UI AD-2** | Cited from UI sitting AD-2 / Stack. Explicitly not a backend requirement. UI currency review 2026-09-23 already recorded those npm tips exist. | **Not a required backend pin.** |

Deferred: “Exact `websockets` / ASGI server class” is left as an implementation choice. QMA parent pinned `websockets` 17.1; this sitting does not restated-pin it. Correct for a backend-delta that has not chosen the live HTTP+WS class.

---

## Findings

### I-1 — Structural Seed “live HTTP + WS” is looser than inspect present tense (Informational)

- **Spine Structural Seed:** `process.py          # live HTTP + WS (today discards bytes)`
- **Inspect:** TCP `asyncio.start_server`; `_handle_client` reads and discards. `BoundListener` carries `websocket_url_prefix` / `query_url_prefix` as **posture fields**, not a speaking server.
- **START-HERE / research 00:** “discards TCP bytes” / “reads and discards bytes”. That is the honest present tense.
- **AD-15** is candidate law for what port 8765 *will* carry. Sequence diagram is intended flow after `qmb host start`. Those are fine as candidate.
- **Not a fail.** Desk fix if the seed comment is touched: `# TCP bind; discards bytes today; HTTP+WS is the named add`.

### Informational (not findings)

- `qmb.host` Python package is CT-33 bot hosting. Sitting’s “no `host` CLI group” is still true. Do not confuse the package with `qmb host start`.
- Envelope `product_session_id` is absent; the **string** appears on view-presentation / contribution-listing / product-session rows. Sitting scopes the gap to the mailbox Envelope. Correct.
- CPython **3.14.7** is the live stable tip; spine restates parent freeze 3.14.6. Inherited-series posture, same as kit/UI sittings. Optional to note “docs still 3.14.7; not upgraded here.”
- WHATWG WebSockets last updated **15 March 2026**; sitting did not freeze that date. Fine.
- HTML living standard last updated **22 September 2026** still holds on 2026-09-24.

---

## Training-data assertions

**None** for the inspect trio (TCP swallow, seed `send_message`, absences), the RFC/WHATWG/HTML/Fetch cites, or the CPython 3.14 inherited series. Those were file reads at `34c148be` and GETs of the named specs/python.org on 2026-09-24.

---

## Summary table

| Item | Claimed | Live / inspect 2026-09-24 | Posture |
| --- | --- | --- | --- |
| Inspect SHA | `34c148be` | `34c148be404a375cbfd79fd4ce6997452e4f1d20` | Match |
| Daemon listener | discards bytes | TCP read-loop, no protocol | Honest |
| `send_message` | seed command | `WireCommand.SEND_MESSAGE` | Honest (name only) |
| `list_mailbox` / `cancel_job` / pairing / `caller_kind` / `copilot_profile` / `originating_psess` | absent | 0 hits | Honest |
| Envelope `product_session_id` | absent | not on `Envelope` | Honest |
| QMB CLI `host` | absent | not in `COMMAND_GROUPS` | Honest |
| RFC 6455 §10.1 / §1.3 | fake Origin; one subprotocol echo | confirmed | Real RFC 2011 |
| WHATWG WebSockets | constructor + one selected protocol | confirmed; LS 15 Mar 2026 | No fake edition |
| HTML webstorage 2026-09-22 | auxiliary copy | LS last updated 22 Sep 2026; copy sentence present | Snapshot date, not a version |
| RFC 9110 PUT / §14.5 / §8.6 | idempotent PUT; partial PUT exists; Content-Length | confirmed | Real RFC 2022 |
| CPython | 3.14 inherited | 3.14.7 latest stable | Inherited series |
| Svelte 5.57.1 / Kit 2.70.3 | UI AD-2, out of scope | cited, not required here | Not a backend pin |

---

## Gate

Currency / inspect-honesty gate **PASS**. Required inspect facts are file-true at `34c148be`. Cited RFCs and living standards exist at the named sections; HTML `2026-09-22` is the living-standard last-updated date, not an invented edition. Stack inherits CPython 3.14 and does not promote UI frontend pins into required backend pins. I-1 is optional wording if Structural Seed is restated; it does not block freeze.
