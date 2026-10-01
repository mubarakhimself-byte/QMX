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
