# Alternative Study ingress: registered-input evidence and integrator seam

Status: unresolved contract/wiring seam, not a repaired failure. The original
characterization test remains enabled and red. No QMA, CT47, public projection,
provider configuration, startup, UI or financial execution files were changed.
The task explicitly reserves shared CT47 flows for the integrator.

## What actually works

`evidence/study-library-and-transport-valid/pytest.txt`: 10 passed. These are
operator Study library tests and QMA transport-double tests; they do not prove
the composed CLI door. `probe-study.py` performs a separate registered fixture
probe. The final evidence is `evidence/study-real-registered-final/pytest.txt`.
Its parent/child provenance and the actual qmb executable child trace point
exclusively to task-16/qmb-runtime sources.

The probe writes an exact local operator binding, resolves its ActorId, verifies
that quant_for initially returns None, registers an actual Quant through
open_for_quant, and verifies the same lookup returns that Quant. It registers an
actual ExperimentSpec with a DispatchLease, its real CT12 split and resolved
config fingerprint, then resolves the registered dispatch owner. A source
fingerprint comes from persisted CT10 archives. The Study objective names the
actual registered interpreter's observed_frontier_count COUNT declaration.
The actual plan executes two provider-free trials, reads checked CT13/CT07
terminals, and reopens identically, including its occurrence witness.

This is explicit local fixture registration, not a claim of legitimate observed
provider authoring or production worker acceptance. No provider keys/spend,
exchange actions, operator security settings, or host external messages occur.

## Where the composed request stops

1. BacktestingService.preflight_registered_run builds optimize.run from those
   registered inputs. CliQmbDoorTransport with its production qmb entrypoint
   spawns the actual CLI. The child returns a prerequisites refusal for missing
   declaration, port, book_fragment, bms_fragment, run_spec, slices and output_root.
   optimize_run does not dispatch the trusted QMA envelope to the Study adapter.
2. Decoding the exact serialized door envelope (including _door_env's None
   operator_descriptor_fp1 default) separately refuses command=optimize.run.
   decode_qma_backtest_context currently fixes command to backtest.run.
3. Supplying the actual library's durable seven-field Study result to the QMA
   terminal parser is an explicit parser-only diagnostic control. Its Study
   schema/history validation succeeds, then unconditional validation of
   evidence_ref fails. The declared Study schema has neither evidence_ref,
   experiment_spec_fp1, split_manifest_fp1, job_id nor attempt_id. The latter
   unconditional checks would also fail after the first one was corrected.

Preflight creates no JobHandle and changes no terminal count. The parser control
does not claim a verified CLI completion. The first two diagnostic probes used
alternate argv0 values: QMA correctly returned Ok(None) because those are not
recognized production preflight entrypoints. Those setup-red logs are retained;
the final production-entrypoint probe supersedes them.

The failing characterization descriptor is insufficient evidence for a fix:
its private five-reference operator_binding has no durable roots, writers,
pinned builder bytes or registry ports; accepted_entry is not registered there;
its standalone Study fingerprint omits the plan's bound computation, rounding
and sampler provenance. It labels the preflight alternative, while QMA expects
alternative-study with study_fp1, operational_fp1, generation_count and batch_size.
Accepting this fixture would invent authority or weaken current guards.

## Concrete recommendation for the integrator

- Keep the existing registered optimize.run operation and CT47 identifier-only
  envelope. Extend its validated command discrimination narrowly to optimize.run,
  preserving dedicated-env agreement, exact fields, no caller roots/policies,
  and no arbitrary callbacks. Route it only to the Alternative Study composition.
- Define/review one complete private Study descriptor by extending the existing
  full Alternative operator identity and pinned builder-source contract. Select
  Book, Alternative or Study exclusively; malformed or ambiguous presence must
  refuse, never silently fall through. Derive Study fingerprints from actual
  typed registered ports and OperatorAlternativeStudyPlan.try_create.
- Pin the stable computation fingerprint in the descriptor. Derive the
  operational fingerprint after the descriptor is hashed; it includes that pin,
  invocation and durable roots. Embedding it in the descriptor creates a cycle.
- Emit QMA's existing exact alternative-study preflight schema. Keep seven-field
  Study results; validate placement via the expected original pinned invocation
  and durable occurrence witness, rather than inventing identity fields in the
  result. Move Book/Alternative result-only identifier checks into their branches.
- Add truly read-only Study verification: incomplete history or absent occurrence
  must refuse without running trials or recording a new witness. Calling
  run_operator_alternative_study for verification can complete missing generations
  and therefore is not a valid verify-only implementation.
- Reuse typed real persisted fixtures for the ingress test, plus negative tests
  for forged/missing refs, unregistered objective, wrong units, changed builder,
  nominal mutation, ambiguous descriptors, incomplete history and restart/crossowner
  recovery. Keep the current red characterization until the reviewed replacement
  proves the composed route. Do not convert it to a blanket skip or accept raw rows.

Public owner routing additionally requires the operator-bound Quant to exist in
the canonical lifecycle service. MailboxStore caches supplied Quant objects;
restore_from_journal explicitly does not reconstruct a Quant from ActorId.
That startup/actor restoration seam belongs to the integrator, not this runtime
repair. The probe isolates a registered owner so it cannot mask the CLI defects.
