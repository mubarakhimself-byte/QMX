# Independent protective ratchet domain review

Verdict: **FAIL** for general nonzero-offset ratchet correctness; meaningful local zero-offset root/OrderPath positive passes. Review is static domain/source plus existing tests, not security testing, provider, normal pump, installed, or full candidate approval. No product/test edits.

`uv run --no-sync pytest -q qmn/tests/test_qmn_seat_tunnel.py qmn/tests/test_qmn_protection_plan.py qmn/tests/test_qmn_protection_market.py`: **28 passed in2.00s**.

- `qmn/src/qmn/data/observation_sink.py`: `a9d36239302faa3439f750df2beda0868d62e216ab44e850ad698f5e07fed458`
- `qmn/src/qmn/host/decision_root.py`: `659ba0f896feaed0b3741b75b70f98eca3ce79780f7fb88c1d07d638e034d6bd`
- `qmn/src/qmn/ledger/protection_state.py`: `fd2631144f8fe6ca446d5f60ef0ff528b862d86cf100e0065c20e3ae7eaaebf4`
- `qmn/src/qmn/ledger/protection_market.py`: `7f4a066c0a338a99101fdb3331943ce5e821e784a5c8e33c212f3bc575e382e2`
- `qmn/src/qmn/ledger/protection_plan.py`: `1bbed3fa72ec0b2e14d09f0327aafd9c8105f4fdc78a2228fa2cb937846e879a`
- `qmn/src/qmn/seats/dispatch.py`: `3784011a2308543349c147b82547b23c64badf5dacd49efc1bde22c7ac01cfbc`
- `qmn/tests/test_qmn_seat_tunnel.py`: `2e3f381552f11c05e957d9ce4918fe98781d0e5eca8ff33444e5e706cb5860f6`
- `qmn/tests/test_qmn_protection_market.py`: `507e10c49ec7074de7580be87d81e11d960d7bb11d48103068baeb4d06a8a7cc`
- `qmn/tests/test_qmn_protection_plan.py`: `5780a8d9fdf9ee719a8be7f8480744d156fd3179c2dcc001819bfdf60f380d74`

## Domain blocker

Dispatch `_authorize_native_ratchet` calculates long current loss-direction distance as reference minus current stop, checks movement as current distance minus configured offset, and calls originate_breakeven_ratchet. That function sets ProtectionAmendment.new_distance to the configured offset. The actual native encoder (`packages/qmf-venue/src/qmf/venue/encode.py:876`) always computes level=reference_price.add(new_distance). Thus long reference100/currentstop90/offset2/bound8 is treated as movement8 at Book admission but encoded level102 is movement12. The actual root fixture has explicit offset0, masking this discrepancy. Positive short offset and positive long offset cannot share this unsigned loss-direction-to-signed-entry-relative mapping.

Resolve the existing authoritative distance/offset convention and convert explicitly at the Book/ratchet command boundary, retaining frozen original risk, intended level and direction/bound. Do not invent a new public grammar or amend QMF parent semantics by child assertion. Numeric/root received exact source refs and numerical example. No new diagnostic code was generated for this domain round.

## Meaningful bounded evidence

Actual authored compiled config row bodies (ratified Book-scoped status, exact values, full node config fp) resolve into immutable policy/source identity and are persisted with entry reference, original risk, command and CT28 epoch. Selected Bot/family/ExitPolicy source match is rechecked on reopen; checked current native stop and spot CT13→CT10/raw readbacks establish instrument/account/session/frontiers. Missing/wrong-unit and foreign instrument tests refuse without plan writes. The local admitted-root fixture reaches AMEND_PROTECTION PID44, carries BREAKEVEN_RATCHET authorization through OrderPath and retains virtual OPEN after accepted ACK. Frozen R remains original; min improvement is origination only and root KSA guard remains entry-only. These positives do not prove the nonzero-offset level/bound behavior, real provider, live operational pump, or full multi-Book production config loader.

## Frozen eleven-path signed-offset correction — PASS, bounded

Independent GPT 6.1 Sol ordinary domain re-review on 2026-10-01. Verified all eleven held source hashes at entry and after test/static review. This append closes the prior nonzero-offset sign finding for this exact snapshot. No product/test edits, commits, new probe programs, provider calls or security testing occurred.

| Path | SHA256 |
| --- | --- |
| `qmn/src/qmn/data/observation_sink.py` | `a9d36239302faa3439f750df2beda0868d62e216ab44e850ad698f5e07fed458` |
| `qmn/src/qmn/host/decision_root.py` | `53ba37b04c31fc01f6124ea6f9ad335f91a9f5a4e709be865356bb2e3041c229` |
| `qmn/src/qmn/host/configured_hosted.py` | `d8b72e4fac93839ce26baacff5fd6f622dd2cfed51ca88223c728b6b15e922b2` |
| `qmn/src/qmn/ledger/protection_state.py` | `fd2631144f8fe6ca446d5f60ef0ff528b862d86cf100e0065c20e3ae7eaaebf4` |
| `qmn/src/qmn/ledger/protection_market.py` | `0518cef9fb4fb3979f888b6313d30cd29e4ff9153e09521b012ce4f3f8f8808a` |
| `qmn/src/qmn/ledger/protection_plan.py` | `e4db5c97f3a94c14203b806160c1ff73e5f84ad8a6bc193190aa1540692d2525` |
| `qmn/src/qmn/seats/dispatch.py` | `93b507bc3004a726d70a8a4f0ecf7364d6299d2a6194712c6e69bfe863a52014` |
| `qmn/tests/test_qmn_seat_tunnel.py` | `e0d60af26270aaf0cf724bc6dd4727b359f6bd1fd1a88cc6d8cb1b8c9044ba02` |
| `qmn/tests/test_qmn_protection_market.py` | `acc9858e8d8fcc4af5dac02c83f4e16799014e92c0ab4797b1c680ef0fa6ada7` |
| `qmn/tests/test_qmn_protection_plan.py` | `5780a8d9fdf9ee719a8be7f8480744d156fd3179c2dcc001819bfdf60f380d74` |
| `qmn/tests/test_qmn_configured_hosted.py` | `eeec93c63f2f5e1e1640103028b379353faa32d2f56a5a86f38a250e5145806b` |

From `/workspace/QMX-release`:

```sh
uv run --no-sync pytest -q -p no:cacheprovider qmn/tests/test_qmn_seat_tunnel.py qmn/tests/test_qmn_protection_market.py qmn/tests/test_qmn_protection_plan.py qmn/tests/test_qmn_configured_hosted.py
```

**31 passed in 2.30s.** Verification was the existing local tests plus static exact numeric and authority-path source review.

| Checked property | Result / evidence |
| --- | --- |
| LONG nonzero offset | PASS. Configured positive loss-direction offset is 2 at scale 5. Current native stop 109000 and reference 110000 give current loss distance 1000 and actual tighten movement 998. Book origination continues to check positive risk magnitude 2; CT-19 command carries signed distance −2, so reference + distance is 109998. |
| SHORT nonzero offset | PASS. Current native stop 111000 and reference 110000 likewise give loss distance 1000 and tighten movement 998. CT-19 distance +2 lands at 110002. Existing SHORT and LONG configured-root tests explicitly assert these signed distances and levels. |
| Bound refusal and equality | PASS, bounded. Existing fixture refuses bound 997 for required movement 998 and asserts unchanged native-projection journal, ordering ordinal, virtual ledger and conformance-double observations. Source `if moved > bound` admits equality 998; equality is established by exact static arithmetic, not a separate bound-998 execution test. Successful root fixture uses bound 2000. |
| Command identity and OrderPath | PASS. Signed amendment is built before Command fingerprint and RatchetCommandAuthorization. Root joins that full command identity to native position, account, venue, session, CT-28 epoch, selected Bot and source frontier, then uses BREAKEVEN_RATCHET origin in actual OrderPath. Existing local root tests submit AMEND_PROTECTION for native position 44, receive the labeled conformance-double accepted ACK, and retain virtual position OPEN. |
| Native encoder semantics | PASS by source. Unchanged `packages/qmf-venue/src/qmf/venue/encode.py` computes `reference_price.add(new_distance)` before emitting protection level. The tested levels exactly match this rule. This round did not call the real encoder/provider; root tests use ConformanceDouble. |
| Frozen R and explicit policy | PASS. Persisted admission plan retains original admitted risk, command, side, Bot/family and CT-28 identity. Favorable excursion and minimum improvement divide by this frozen original R. Loss-distance risk/non-widening/minimum policy uses the positive configured offset before converting only the final CT-19 amendment to a signed delta. This path resolves mandatory trigger/offset/minimum rows from actual full config and passes explicit values; it does not fall back to the existing optional defaults in the unchanged capital helper. Missing/wrong-unit/foreign-instrument plan tests refuse without writes. |
| Full assessed config before seal | PASS, bounded. `validate_assessed_path_config` requires the exact ResolvedNodeConfig, exact fingerprint identities, recomputed full value-bearing row identities for both actual and assessed configs, and equality of their declared/recomputed fp1. Matching, different-version, absent and stale-declared-identity controls pass. Invocation calls the guard before the resumed boot journal sink or sealed-hosted-runtime call. Guards are independently unit-tested; complete normal supervisor invocation remains separate. |
| Physical source join correction | PASS by source and existing positives. Observation sink and native protection reader retain exact nominal event/writer/sequence/instant/world/fingerprint checks, checked-reader and CT-10/raw fingerprint joins. Market/plan physical rows now compare QMF canonical bytes, allowing equivalent immutable versus serialized containers while retaining unique event/index linkage and typed refusal if canonicalization fails. Boolean sequence/format/rational-component lookalikes remain excluded by exact integer checks. This is ordinary static preservation review, not a new malformed-input/security probe campaign. |

**No remaining finding in the bounded signed-offset/config/physical-join correction review.** This is approval of the listed held slice only. It does not extend the old approval of a different source slice, certify all malformed inputs, or fill normal pump, real provider/native wire, complete MIS producer, multi-Book production composition, installed runtime, broader security or final release acceptance lanes. Numeric owner continues to own the new paths; final immutable candidate must rerun required factory/static/QA and execution checks.
