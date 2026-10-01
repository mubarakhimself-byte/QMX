# Independent causal numeric review

Reviewer: GPT 6.1 Sol; inspected numeric commit `a400f334bb9e86c9dd1ad4ac14afd1045af934af`.
Governing documentation: `origin/main` at `c3e8ec5ef33d0b38cdf7f5dbdd48a6fc70ac33cf`,
especially CT-16 earliest contributing-input knowledge time and CT-17 lifecycle law.
Read project CLAUDE.md, docs/AGENTS.md, packet 07 and the relevant renewed audit
numeric findings. Environment: Linux, release checkout `.venv`, CPython 3.14.7.

## Verdict: approved after independent correction

Corrective commit `24511efbb103163b6526fc2a6d30628956072013` uses explicit
dependency positions, so MOM/ROC use only their endpoints. Source review and an
independent rerun of the actual-kernel held-out probe now return the expected
presence and times at indices 2–4. The final committed MOM/ROC regressions pass
2/2 (`.venv/bin/python -m pytest -q -p no:cacheprovider packages/qmf-indicators/tests/test_batch_mode.py -k 'mom or roc'`).
NF01–NF06 are approved within the source/synthetic contract scope; this does not
establish a release-wide gate or deployed consumer.

P2: MOM and ROC metadata incorrectly treats all samples between the period-back
sample and the current sample as contributing dependencies. TA-Lib MOM/ROC depend
only on the two endpoints. `_support_start` selects a contiguous interval, which
cannot represent their sparse support. This causes unnecessary provisional presence
and knowledge time later than the earliest contributing-input availability.

Held-out reproduction used the actual `compute_batch` and `ReferenceKernel`, with
the existing configuration fixture, period 2, warm-up 2, values
`[100,200,300,400,500]`, provisional index 1 only, and knowledge instants
`[1,100,3,4,5]`. For both MOM and ROC, output index 2 is **provisional, knowable
100**; expected **present, knowable 3**, since its dependencies are indices 0 and
2. Index 3 correctly remains provisional/knowable 100 and index 4 correctly
becomes present/knowable 5. Arithmetic was not changed or challenged by this
finding. The implementer/coordinator received the defect before acceptance.

The same actual-kernel probes verify SMA/WMA period 2 retain index 1 taint only
while it belongs to the rolling window; EMA and RSI retain recursive prior-input
taint and knowledge time. Unsupported/custom formula fallback remains conservative;
this is not certification of all extension dependency semantics.

## Independent checks

Held-out direct production-function assertions passed for:

- all four parent/child stale/future cascade-horizon mismatches, with no predicate
  invocation;
- equal confirmation/invalidation times, invalidation without confirmation,
  unsorted repeated confirmations, and historical reads hiding later confirmation;
- invalid foreign, reversed, and duplicate observations after an apparent first
  swing confirmation match;
- empty interval symmetry, empty/empty, and negative-time boundary positions.

Source inspection confirms lifecycle ordering applies to visible facts after
filtering at the read horizon, swing admission validates the complete supplied
sequence before its match loop, and cascade mismatch refuses before the predicate.

Independent command:

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider packages/qmf-core/tests/test_ct01_exact.py packages/qmf-core/tests/test_ct02_chrono.py packages/qmf-core/tests/test_ct05_fingerprint.py packages/qmf-core/tests/test_exact_examples.py packages/qmf-core/tests/test_time_examples.py packages/qmf-core/tests/test_fingerprint_examples.py packages/qmf-indicators/tests packages/qmf-structure/tests
```

Result: **726 passed in 2.38s**. This is an overlapping reviewer rerun, not an
additional acceptance total. Passing existing suites does not resolve the held-out
MOM/ROC defect. No deployed consumer, provider, Windows, full release gate, or
power-loss behavior is established. The final corrective commit was rereviewed
as recorded above.

## Independent data persistence review

Reviewed final commit `4c706d1a` for DF01–DF03 after inspecting packet 06,
the data engine, registry commit/read paths, and QMB immutable fragment paths.
Verdict: **approved within the source/synthetic contract scope**.

The first candidate had a P1 pending-intent retry defect: an append refusal after
intent persistence allowed a competing supersedes edge to commit, then exact
retry skipped the room-wide guard and exposed a fork. Reported to implementer
and coordinator; the final candidate reruns the guard while permitting only the
exact intent-covered edge identity to lack a witness during reconciliation.
Independent restart probes for incoming forks, outgoing forks, and cycles now
refuse the pending retry while the winning competing edge remains readable.
Ordinary readers still require integrity witnesses; unrelated witnessless lines
cannot receive manufactured witnesses through this recovery path.

Source inspection and a held-out direct low-level engine probe confirm append
uncertainty reconciliation occurs before both identity lookup and another
append. A partial failed append at rotation followed by direct retry returns
ordinal 1, byte offset 0, sequence 1 and ordinary readback of exactly the two
intended records. The recovery scanner preserves valid committed prefixes and
refuses malformed newline-terminated corruption.

A held-out mixed mapping/list/tuple graph confirms deep input mutations cannot
change RegistryFragment identity/fingerprint, and deep returned-output mutation
raises TypeError. ConfigFragment uses the same recursive container semantics and
its delivery path is included in the affected tests.

Independent command:

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider packages/qmf-data/tests packages/qmf-registry/tests qmb/tests/test_registryread.py qmb/tests/test_config_fragments.py qmb/tests/test_deep_fragment_immutability_contracts.py
```

Result: **757 passed in 8.85s**. An initial command used nonexistent QMB test
filenames and collected no tests; the corrected command above completed.
These overlap the implementer's runs and are not additional acceptance totals.
Final commit inspection confirms the reviewed files are committed with no
remaining working changes in those source paths.

DF04 explicitly remains deferred before adoption: extra-write callbacks remain
in memory, with no production caller found. A future application owner must
persist intent/completion or refuse resume until reconciliation. This review
does not certify multi-room restart completion, power loss, Windows filesystem
semantics, deployed storage, or full workspace release gates. See `data.md` for
the implementer's broader QMB failures and compatibility limits, including
pre-existing witnessless edges without an intent requiring operator recovery.
