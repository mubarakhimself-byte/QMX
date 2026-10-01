# Independent QML purity relocation review

Reviewer: GPT 6.1 Sol. Verdict: **bounded source relocation approved pending
final commit identity**. Reviewed existing ratified COMP-QML pure-distribution
boundary and QMB application-host ownership. No new distribution or research
ratification is implied.

Compared the original `qml.host.research_store` source from HEAD to the moved
`qmb.host.research_store`: filesystem behavior is unchanged. Differences are the
module description, importing/reexporting the pure envelope mint functions, and
module location. QML host no longer imports or exports the actual persistence
operations. The five existing storage tests moved to QMB rather than being
deleted or weakened. Pure research Stage 0 authoring remains in QML.

Held-out checks confirm:

- QMB's two envelope reexports are the exact QML-owned pure function objects;
- QML host has no persistence functions/class in attributes or `__all__`;
- moved-host save, repeated save and ordinary read preserve canonical bytes and
  research fingerprint.

Independent command:

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider qa/tests/epic_12/test_l0_static.py qmb/tests/test_research_host_store.py qml/tests/test_host_seed_cite.py qml/tests/test_generation_ownership.py qml/tests/test_generation_gaps_unfilled.py qml/tests/test_mill_graduation.py qml/tests/test_research_stage0.py qml/tests/test_research_ref.py
```

Result: **53 passed, 1 failed in 2.65s**. The unchanged QA12 purity gate and
moved storage tests pass. Failure is the existing generation-gap test asserting
that CT-33 documentation contains no literal `Filter`; governing documentation
contains that noun. The relocation changes neither that test nor those docs.
This observed failure remains visible and is not changed to ratify a provisional
research surface. Counts overlap implementer checks and are not additive.

Compatibility: filesystem callers migrate from `qml.host` to
`qmb.host.research_store`; pure QML callers retain their pure functions. Storage
format, canonical bytes and fingerprint recipes remain unchanged. Existing
storage behavior is characterized, not broadly certified. The earlier provisional
bundle installation predates this source move and cannot establish installed
module migration; a fresh final-candidate bundle remains required. No actual
installed application research workflow, full release acceptance or Windows
storage behavior is established here.
