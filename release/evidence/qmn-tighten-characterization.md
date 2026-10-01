# TIGHTEN_STOP refusal characterization

Bounded test-only PASS at qmn/tests/test_qmn_seat_tunnel.py SHA256 `20eb8e426d9d4b3ac55a330bada78a1ea0b95f9f9f2469293c173de33941711a`. Independent `.venv/bin/python -m pytest -q -p no:cacheprovider qmn/tests/test_qmn_seat_tunnel.py -k configured_decision_root`: **1 passed, 23 deselected in 1.58s**.

The new typed TightenProtectiveStop is formed for the real opened position in the existing admitted fixture and sent through dispatch_hosted_intents; it returns a typed exit_intent refusal with unchanged checked CT13 decisions/projections, command ordinal, virtual ledger records and venue-double observations. This is an admitted-seat dispatch helper control, not a TIGHTEN callback through HostedDecisionRoot.run_slice. The subsequent actual-root FULL_CLOSE PID44 positive, durable projection/transcript reopen, and position remaining OPEN after venue ACK remain intact.

No product TIGHTEN implementation, amend_protection support, production/provider readiness or whole Node approval is claimed. Local venue observations are a labeled conformance double. Product source unchanged by reviewer.
