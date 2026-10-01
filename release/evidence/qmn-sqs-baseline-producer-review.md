# SQS producer2 independent review — FAIL

2026-10-01. Independent Sol ordinary exact arithmetic and durable content/source-contract review. Both frozen hashes matched entry, diagnostic exit and final report census. No product/test edits, commits, credentials/providers or security testing. This review does not claim actual LIVE acquisition, warm-up, admission or full node readiness.

## P2 — lawful exact statistic refuses after writing because readback scale differs

`produce_sqs_baseline` compares the final independently recomputed `PriceDelta` with the reopened artifact by raw dataclass equality (`recomputed.value != reopened.value.artifact.average_spread`). `PriceDelta` has a canonical exact identity independent of the input decimal representation, and the artifact reader reconstructs a representable reduced scale. Two equal quantities therefore need not have identical value/scale fields.

The finite positive uses actual official `register_forex_17ny`, its venue registration, two real locally admitted LIVE-labelled CT-10 bid/ask pairs, physical source read and mean declaration. Spreads **20 and 40 at scale 5** yield **30 × 10^-5 = 3/10000** exactly. The producer's source-scale representation is 30/scale5; the reader's canonical reconstruction is 3/scale4. It writes CT-11, then refuses at `baseline_recompute` despite equal quantity/canonical identity. The file census changes before the refusal. This is a legitimate simple mean, not bad source metadata or an unsupported decimal, and the existing mean15 case hides the representational difference.

Required correction: compare complete canonical typed quantity identities (including instrument) or exact rational quantity equality on readback, rather than incidental scale/value representation. Preserve exact arithmetic and revalidation; do not round or weaken source identity. Add a meaningful lawful nonuniform mean with trailing decimal factor, physically fresh readback and expected exact value, and ensure success/receipt follows verified content. A later owner edit is a new slice and does not change this FAIL on held bytes.

## Calculation controls that passed

Root cwd: `uv run --no-sync pytest -q -p no:cacheprovider qmn/tests/test_qmn_sqs_baseline_producer.py qmn/tests/test_qmn_admission_artifacts.py` — **8 passed in 1.37s**.

The finite official calendar/physical CT-10 controls go beyond the current integer mean test: spreads1/2 at scale5 produce fractional mean **3/200000**; odd median1/2/9 gives **1/50000**; even median1/2/5/8 gives **7/200000**. All physically fresh-store reopen and retain identical canonical artifact/value, source refs and unverified status. A nondecimal mean of1/1/2 (4/3 at quote scale) refuses with the whole file census unchanged; undeclared quantile likewise refuses before write. Existing tests additionally cover foreign instrument, DEMO key, official closed session and declared calendar/config/refit identity. All fixtures use a real CT-02 registration and physical QMF storage, but their quotes are explicit local conformance doubles with LIVE labels, not a real authenticated live connection.

## Durable source-derived production contract remains incomplete

This source genuinely calculates from physical selected CT-10 facts in the producer call: exact paired spread grouping, declared mean/median/no-rounding, calendar session-window lookup for every event instant, artifact write/readback, source re-read/re-fit, and session-window re-query. This is stronger than a test independently computing the mean of a supplied value. It still does not provide a **durable producer receipt and read-time verification contract**.

`SqsBaselineProduction` contains sample_count, statistic/session id/rounding, calendar-registration fp and checked actual session-occurrence fingerprints only in the returned in-memory dataclass. Persistence delegates to existing `persist_sqs_baseline`, which retains the baseline artifact/source archive refs/calendar identity, conditioned session-id string embedding the registration digest, statistic+rounding label and refit labels. The actual session-window occurrence set, canonical registration/binding/provider recipe and full production/evaluator receipt are not durably retained there. `read_sqs_baseline` reopens the typed baseline and every cited LIVE quote but does **not** re-pair/re-fit the statistic or resolve/reverify those official session occurrences. It returns `derivation_verified=False` and `unverified-input-artifact`, correctly. A fresh reader cannot independently distinguish an actual producer-backed fit from the older supplied input-artifact path using this evidence alone.

Thus calculation scope has meaningful positives, but durable derivation/admission acceptance is **pending**, even after the P2 arithmetic correction. Keep the old generic input-artifact reader's false flag. Complete the source producer contract by persisting an explicitly versioned private recipe/production receipt over exact source refs, key, statistic/arithmetic implementation, calendar registration and actual checked session occurrences, sample grouping/count, exact result/refit identity. A typed read/verify owner API must physically re-open those facts/receipt, resolve the pinned official registration, reproduce session grouping and exact fit, and compare the whole canonical binding. No guessed public field/kind or new CT-13 promotion flag is needed; the owner must define its private durable artifact and lawful application integration. Only that checked receipt can support a later explicitly named derivation assertion; it still does not prove an authenticated LIVE provider, minimum warm-up window, freshness, fresh capability or admission readiness.

Session id is currently an explicit label combined with the calendar-registration digest. Every quote must fall in an open official SessionWindow, and the returned occurrence list distinguishes dates. That label is not itself a declared intraday session selector; do not advertise it as proof of another time band or fabricate a window from civil time. Actual support caps quote/result scale at18, whereas qmf-core MAX_SCALE is72; the implementation's narrower range must be stated rather than described as all core-supported decimal scales.

A separate finite ordinary correction-annotation case was retained: original spreads10/20 plus a CT-10 correction pair for the first native occurrence with spread60 reaches fit/write and subsequently the same scale-comparison refusal. `_read_quotes` does not check `correction_of`, and grouping includes revision as a new sample. This case is not evidence that unresolved corrections are refused at the source boundary. Main CT-10 corrections are annotations, and QMB's existing replay source reader explicitly blocks them until a governed resolution fold exists. The SQS owner should likewise refuse unresolved correction refs before fitting/effects, or implement its exact governed correction policy with immutable lineage; silently treating old and revised quotes as independent samples is not a proven source-fit recipe. This observation is kept separate from the concrete lawful no-correction P2 above; no corrected-source acceptance is claimed.

## Exact binding and retained diagnostics

```text
296dff8683170a49479f7bdc43ad69ab855429c484c9f6104f41e99cfdff1b61 qmn/src/qmn/host/sqs_baseline_producer.py
5f6d166616918ac1f13f2a1f72f8e2cb76e2840e7732ff5235551c676e8c71ed qmn/tests/test_qmn_sqs_baseline_producer.py
```

Supporting unchanged dependencies inspected, read-time only:

```text
38f4d6d326988acb0bc75947a3b628289ff91b0d8d667c897980dfa22df83006 qmn/src/qmn/host/admission_artifacts.py
87c88ebb3c3e4ba226cca9e709a6fe53b2abdfac7bf042210968f2b077ec2d9e qmn/src/qmn/mis/catalog.py
b02c3b294c5e768689a0c2f165db67a9a5d86e97c3835b1c630f5521de1a1ce4 packages/qmf-core/src/qmf/core/exact.py
6960c098239d05bb5b9844ac70f4495e3acf6f579c1775c68cb1786c7990d540 packages/qmf-data/src/qmf/data/source_boundary.py
```

Diagnostic root command: `uv run --no-sync python /workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics/review_sqs_producer_statistic.py` — exit0, factual results above. Two initial diagnostic constructor setup errors were corrected to the official MarketDataContext.try_create field contract; failed copies are retained and not counted as product tests.

```text
699aa842f46400a9ada8afc7045f85f4f271923d7675adb810f99365a72d7879 review_sqs_producer_statistic.initial-constructor-error.py
af893cd12af86a6ae6ff1fc3faefa9be6c219bea8dd247ace33706e1d6f1b976 review_sqs_producer_statistic.initial-row-fields-error.py
61174de51e215b0ab28f408b6dc6d9f79823ce957e0f659c7d728e842efffc0f review_sqs_producer_statistic.notes.json
aaa876e50528a61568fd245c2db832b010ce697c01eaec3b5c1c56ffe5154ea8 review_sqs_producer_statistic.py
e76c313749ce55512f9a1da1bbfa4a04d98cdeb22496a37025db8457978054de review_sqs_producer_statistic.results.json
```

Coordinator/Numeric were notified before repair. Keep the freeze until explicit release, then bind any correction to a fresh exact review. Ordinary arithmetic/contract findings do not authorize provider/security or full release acceptance.
