# QML pure distribution and application filesystem support

Reproduced `pytest qa/tests/epic_12/test_l0_static.py -q`: FAIL, one impurity
in `qml.host.research_store` (os/pathlib). Before moving it, the five existing
save/reopen/canonical-byte/ownership tests PASS.

The ratified pure one-distribution QML boundary remains authoritative
(`docs/components/qml.md`, DEC-0171). Filesystem support now lives in the existing
application host at `qmb.host.research_store`; QML still authors and validates the
hypothesis bytes and stamps authoring values. This adapter persists those bytes;
QMB does not acquire authority to invent research meaning or author bots.
The moved application adapter reexports the pure envelope functions so the host
can compose registration and persistence. Its existing five tests moved to QMB,
where the declared QML dependency permits the application integration.

Migration: persistence callers import `qmb.host.research_store`, not `qml.host`.
Pure QML callers require no filesystem support. No new distribution or COMP was
introduced; ADR-0023 remains provisional, not ratified by this repair.

Post-change storage, seed-cite, generation, graduation and unchanged purity
regressions: 35 PASS. Scoped Pyright: zero errors. This is a characterized
boundary repair, not full research or release acceptance. The historical QML
module-home gate still reports newer generation/research/host APIs; no test was
weakened to ratify those provisional surfaces.
