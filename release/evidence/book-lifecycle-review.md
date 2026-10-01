# Independent Sol review — Book replay lifecycle

Candidates `d9298a1aaabe21e5fa254d5188c219530cd3ef87` and `0b40df75bb177a47324a4be91ef3af4fb0b13865`. **Changes required.** Focused Book/runloop/CT29 suite independently passed **31 tests**. This is not approval of CLI, provider execution or the complete economic result chain.

The selected-bot full-entry then later recorded bid protective-stop close positive runs actual Book fills, produces CT29 and checked recovery. Partial fills persist exact quantities/prices/costs; terminal finalization carries a typed reason, proportionally rebases R once and verifies exact lineage on recovery. Mid-partial recovery correctly refuses an unterminated fill reservation, rather than presenting it as an empty completed ledger. Cancellation/finalized-token tests preserve idempotent terminalization.

Two additional controls fail:

1. Actual partial entry fills quantity2 of planned5. Before entry terminalization, the next recorded bid109400 crosses the admitted109500 stop. `scheduled_position_event` returns Ok(None), with zero positions, one pending entry and zero closes, because it exits early when `_positions` is empty. Pending actual fills are real exposure and currently receive neither protective stop evaluation nor financing. The repair must protect actual filled quantity while the remainder is pending, cancel that remainder on a genuine stop trigger, then terminalize/rebase the actual quantity and close canonically. End-of-input forced closure is not a substitute.

2. A configured JournalWriter returning Ok(None) without writing the partial-fill event leads `execute_resting` to return a successful filled/nonterminal disposition and advance pending fill state. Actual checked recovery then returns an empty ledger/highwater0. The handler trusts non-refusal acknowledgments before updating exposure. Require typed complete exact CT13 event/store/raw physical-row acknowledgment before publishing fill, position, financing or close transitions. The partial-fill control is independently reproduced; other analogous source paths need owner checks.

Controls reused actual handler, exact execution adapters and filesystem stores from `test_book_handler.py`; only the acknowledgment method was replaced in the second negative. Source unchanged. Findings and concrete scripts sent to owner/root. Independent command: `.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_book_handler.py qmb/tests/test_event_slice_loop.py qmb/tests/test_results_ct29.py`.
