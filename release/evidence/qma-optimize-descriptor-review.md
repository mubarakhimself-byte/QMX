# QMA optimize descriptor2 bounded review — PASS for descriptor only

2026-10-01. Independent Sol ordinary operation-descriptor review. Frozen entry/end hashes:

```text
24eb86438115c27464bc964d72580a5eab24af186f77a20f59f9041fce606c68 qmx-agents/packages/qma-core/src/qma/core/operations/catalog.py
05c64569a428a4abfbe9738a08792b90dbd51dbd9c31feea395b62332a15793e qmx-agents/packages/qma-core/tests/test_operation_descriptor.py
```

`qmb.optimize.run` registers the existing documented optimize door as its own version-1 Capability Operation Interface. Main `c3e8ec5` QMB B-8/DEC-0163 defines optimize as a study over declared parameter spaces and generation-stepped sampler; the existing core `ports/qmb.py` already names `optimize.run` as a QMB run command. Main ADR-0024 DEC-0416 requires a per-operation versioned descriptor, and CT-47 retains the single QMB door/reference-only boundary. Main DEC-0436/SCN-0020 adopts a complete Alternative composition for optimization; registering this name does not create a new application or mandate Book/CT-32 outputs.

The descriptor is QMB-owned, one input/one JobHandle output, empty-policy refuse, worker placement, PLACE_RUN effect, `library.run` permission and run occupancy/environment requirement. It uses `run_fp1` with optional `as_of`/`evidence_ref`, matching the established CT-47 reference transport. It invents no raw space, objective, direction, batch, parameter binding or generation-count public JSON fields; those belong to resolved immutable owner artifacts/configs referenced by ExperimentSpec/run bindings. It retains shared typed refusal/progress/lifecycle vocabulary. Library, QMB CLI and QMA wire doors are declared per operation; QMN run_slice is correctly excluded for this study placement.

Command from `/workspace/QMX-release/qmx-agents/packages/qma-core`: `uv run --no-sync python -m pytest -q -p no:cacheprovider tests/test_operation_descriptor.py` — **13 passed in 0.11s**. Existing tests reconstruct the strict descriptor schema, catalogue and per-op door matrix; new assertions cover optimize ownership, effect, reference keys, resource needs and allowed doors. No additional probes or product/test edits were performed.

This is a **descriptor/schema PASS only**. The supported-door declarations are intended contract, not evidence that routes execute. Worker dispatch, public normal ingress, actual CLI Study selection, correct expected Study artifact/JobHandle terminal proof, private producer witness, durable reuse/restart/cancel and advertised live availability remain unaccepted until genuine persisted end-to-end routes pass. Catalogue membership must not be interpreted as healthy executable availability while integration is unfinished. No provider or complete security approval, whole coupled QMA acceptance, or candidate release acceptance is implied.
