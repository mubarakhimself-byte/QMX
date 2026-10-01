# Bounded Alternative operator review

Status: FAIL pending result/input/artifact coupling correction. No product edits, provider calls, or whole CLI/QMA approval.

Reviewed adapter SHA256 `aefa69ffa8024b46c38a41acc1704abb1a3629f6bb3a14e278df35a62eca2106`; test `deb08080e35e6ce66204762a8cf63b98c6edce3bfa15e7665b33eb0eacf70361`. Loader observed SHA `c7325245778b6ab3f2c90777ad55eeff9efa1e37397bb539ed70278bf17872c3`, test `ae563be72a483c0ddd78a27272de1eda7c1872b72b863887c54d65efe28891f0`; execution owner is actively adding verify-only functionality, so loader bytes are diagnostic rather than held approval.

Independent `.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_operator_alternative.py qmb/tests/test_operator_alternative_replay.py`: **6 passed in 0.88s**. Existing positive is actual persisted CT10/CT12, registered local interpreter, CT13 decision, CT07 terminal lineage and reopened Alternative terminal; no Book/BMS/Bot/CT32 R vocabulary. The interpreter is a local policy fixture, not external provider or completed financial policy grammar. Strict mints_ct32 True/int and foreign split controls refuse before CT13/terminal effects. Descriptor tests pin files but their builder intentionally returns None: they do not establish a successful descriptor-loader-to-actual-runtime chain.

Independent actual fixture capture wraps run_operator_alternative only to retain successful inputs/result and does not substitute execution. With original trusted inputs and actual terminal readback, separately changing top-level result source_fp1, composition_fp1, registry_fp1 to a foreign valid fingerprint, or policy_pair_identity to a foreign pair, all four return Ok. Artifact-to-input comparisons exist, but these duplicated result fields are never compared against either authoritative source. This is a concrete false-admission blocker.

A second control changes trusted inputs initial_accounting_state to a different lawful mapping and updates echoed operator_binding.initial_accounting_state_fp1 plus canonical operator_binding_fp1. The validator still accepts the original actual terminal artifact, whose persisted initial_accounting_state_fp1 belongs to the original state. Expected binding recomputation from new inputs is not evidence that the artifact used those inputs. Compare actual persisted initial state/trial/epoch/writer/interpreter lineage against the trusted runtime, and compare every duplicated result identity with the same authoritative artifact/input values. Owner notified of both failures.

No independent clean-commit recommendation for loader/CLI coupling: operator_alternative_replay imports current QmaBacktestContext/new discriminator and adapter, while active CLI/run/preflight/verify consumers are changing. Adapter library files can be reasoned about separately, but approval awaits the coupling correction and real positive trusted-input readback; loader success remains unproven by these six tests.


## Adapter correction — bounded PASS

Exact held adapter SHA256 `951d332e075c7afc56dd36622b830f1710de2c8d849eeb9d2c2b1464c06a3264`; test `0f64f83b5adf8a78346784187b77ac4b95f34837b536d834c96c95f239511a34`. Only these two paths are approved by this correction review. Active loader/CLI/verify/preflight files remain excluded.

Independent actual persisted fixture controls now reject all original source/composition/registry/Pair substitutions. Additional final-state/interpreter/terminal-reference/journal-reference substitutions refuse. The changed trusted initial state plus rehashed echoed binding cannot reuse the original actual terminal. Foreign epoch, lineage writer, descriptor and trial controls refuse; unchanged trusted inputs and actual reopened terminal continue to validate. Actual journal reference events are read_checked and their command owner epoch is compared with the trusted epoch. Persisted terminal values are compared to trusted source, registry-selected interpreter, seed, trial, journal and lineage writers, and every duplicate child-result value is compared with that artifact.

Independent scoped adapter pytest passes; genuine positive uses CT10/CT12, registered local policy interpreter, CT13 decisions, CT07 and Alternative terminal readback. Strict non-CT32 mode and foreign split before-effects controls remain green. No Book/BMS/Bot/CT32/R projection is introduced. The local registered policy fixture remains explicitly not provider connectivity or completion of financial example grammar.

This closes the two recorded false-admission blockers at the adapter result boundary. It does not prove a successful operator descriptor-loader chain, full CLI/QMA terminal observer, clean combined HEAD or final installed candidate. Runtime dependencies must be frozen and reviewed separately.

Root's combined adapter/active-loader diagnostic rerun: **6 PASS in 1.12 seconds**, `/workspace/qmx-atc-operator-identity-correction-root.log`. Exact adapter/test hashes match independent held approval. These files require the active QmaBacktestContext discriminator addition; they are held for the coupled source integration rather than committed against an incompatible older context. Root does not upgrade active loader/CLI approval from this suite.


## Verify-only materialization extension — residual occurrence rebinding FAIL

New held adapter SHA256 `cd111ff537213e0402f8acf88b0c50a41dc66ca0638f842fc7308c5462340fdb`; test `0bd77f7f61633ee3eb635a82fe1620d9cd819c1fac4ad2438d7ca53bfc693c0a`. This extension is not covered by the preceding bounded approval.

Actual genuine persisted fixture `test_operator_result_validator_rejects_book_or_context_substitution` was run while capturing successful inputs, without replacing execution. `validate_operator_alternative_result(None, inputs=replace(original, runtime_descriptor_fp1=foreign_valid_fp))` returns Ok and regenerates a new descriptor binding around the old terminal. Replacing context job_id with foreign-job and attempt_id with 9 likewise materializes the old terminal as the new delegated occurrence. The durable terminal does not store these operator/delegated occurrence pins; reconstructing them from current trusted inputs does not prove they governed the original execution. Existing non-None descriptor/context negative controls only reject an old echo mismatch, and do not close this None path. Owner/root notified.

Current materializer requires unique matching source/Pair/seed/trial/interpreter/writers and routes back through the strict validator; missing and two genuine matching run terminals have existing negative tests. That is useful but incomplete occurrence authority. It needs an actual durable operator-occurrence join for descriptor/delegated IDs, or typed refusal where historical execution cannot be bound, preserving no interpreter rerun. No new public CT is proposed by this finding. Loader/CLI remain active and excluded.
