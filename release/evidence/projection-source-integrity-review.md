# Projection source integrity diagnosis

Status: FAIL on current source inspected 2026-10-01; independent regression `qmb/tests/test_analysis_source_integrity.py` reproduces substituted source admission. Product source unchanged; root-only Git.

A genuine CT32 local recorded-result fixture with one hour-10 trade projects one match for hours 8–16. Replacing its supplied CT29 stream with an hour-18 trade of PnL 999999 is accepted and projects zero matches while inheriting the original CT29 citation and canonical saved-view identity. Public API regression: `.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_analysis_source_integrity.py` — **1 failed**, genuine positive passed before the assertion.

`qmb/src/qmb/analysis/project.py:1124` returns the artifact's first trade reference without checking supplied rows. `_resolve_source_ct29` also accepts bare Fingerprint/string references without checking pairing; explicitly cited mappings check reference membership but do not authenticate their rows.

The citation has precise existing semantics: `qmb/src/qmb/results/ct32.py:415` documents `ct-13:ct-29:<binding fingerprint>` as a run's stream locator, and `:430` emits it. It is not a content digest of supplied ClosedTrade rows. Individual actual CT29 ExitRecords are content-fingerprinted, and `qmb/src/qmb/results/ct29.py` already verifies exact journal exit-record references against resolved records. CT29 contract (`docs/contracts/ct-29-exit-record.yaml:18`, `:28`, `:35`) requires projection over the cited stream, binding-epoch and knowledge-time boundaries, and immutable persisted records.

Repair needs a trusted durable resolver/readback boundary for that binding and as-of, or verified record/journal provenance before using supplied rows. Merely hashing untrusted rows and comparing to the binding locator would invent incorrect semantics. Canonical saved views must remain reference-only. Refuse foreign references and unverified substituted records; retain actual durable matching-source positive and genuine read-only predicate filtering. Fixture helper is explicitly local evidence, not provider proof. Finding and exact regression sent data owner for its next source slot; no source repairs or commits performed.

## 57c99cb9 durable-source corrective review

Candidate `57c99cb9157bdad6a58397d8ec488e7c6263d831`: original naked row/cite substitution is refused and actual durable source positive reopens CT13/CT29. Reviewer focused projection suites: **44 passed**. Full acceptance remains CHANGES REQUIRED.

Independent `/tmp/review_projection_lineage.py` creates the actual durable close fixture, retains its stream locator and exact count/net/fees, and changes CT32 ResultLabel.input_fingerprints[0] (run configuration identity) to a foreign fingerprint while preserving the registry-as-of input. Projection still admits one match. `_resolve_source_ct29` checks world/account role, binding locator and aggregate economics but never joins CT32 run configuration/Book/BMS/Bot/source pins to the actual durable open/close lineage. The positive fixture itself mints CT32 using a separate config and overrides the stream locator, so it does not establish this complete pairing.

Require authoritative run-config/expected-artifact lineage compatibility at durable resolution before economics comparison; identical aggregate totals cannot authenticate source identity. Do not invent equality between locator and content hash. Exact reproduction sent data/root. CLI trusted-runtime query integration remains pending; source unchanged.
