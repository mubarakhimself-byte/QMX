# Reviewed ratchet integration controls

Source commit `7e011f97`: root independently repeated the 31 signed-offset/plan/market/configured-path tests, all PASS in 2.35s (`/workspace/qmx-qmn-signed-ratchet-root.log`). Independent Sol repeated all 31 and reviewed the full 11-file hashes, bounded PASS in `qmn-ratchet-review.md`.

Root then ran:

```text
uv run --no-sync pytest -q -p no:cacheprovider qmn/tests/test_qmn_protection_state.py qmn/tests/test_qmn_protection_readback.py qmn/tests/test_qmn_protection_dispatch.py qmn/tests/test_qmn_protection_ksa.py qmn/tests/test_qmn_protection_windows.py qmn/tests/test_qmn_data.py qmn/tests/test_qmn_loop.py qmn/tests/test_qmn_protection_plan.py qmn/tests/test_qmn_protection_market.py qmn/tests/test_qmn_seat_tunnel.py qmn/tests/test_qmn_configured_hosted.py
```

**103 PASS in 2.48s**, `/workspace/qmx-qmn-ratchet-provenance-integration-root.log`. This combines current signed native intent/OrderPath tests with physical protection/readback, data intake, loop, KSA and window behavior. Local conformance doubles are labeled. No provider, normal installed pump, MIS baseline, native Windows or final release acceptance is implied.
