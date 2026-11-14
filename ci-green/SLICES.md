# Slices: ci-green

2 slices for 2 asks, because S1 needs a pin before its fix (the deep run mutates every touched function on Linux, and the two credential functions have no Linux test: lead decision D-L27), and S2 is later and deferred, so it has no slices yet. One slice per piece he can see would be one PR; the pin is the one extra a seam forces.

Checkpoints: A: 2 slices (core, the proof of the core sentence); B: deferred (later, S2, up to 3 slices, briefed after A merges). Lanes: one lane, L1: cg-02 depends on cg-01's pins, so one builder works them in order; their files do not overlap.

Growth: 2 asks -> 7 plan lines -> 5 elements -> 2 slices now (3 more at stop B, inside the later budget).

| id | name | ask | stop | lane | kind | depends on | files | size |
|---|---|---|---|---|---|---|---|---|
| cg-01 | Pin the Windows credential calls on Linux | S1 | A | L1 | pin | - | qmn/tests/test_app_grants_windows_calls.py | S |
| cg-02 | Type the Windows-only qmn code for Linux and fix the qmx-apps format | S1 | A | L1 | refactor | cg-01 | qmn/src/qmn/app/grants.py, qmn/src/qmn/host/_windows_deployment.py, qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py | S |
