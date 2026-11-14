# Plan: ci-green (plan v1)

Every line carries its ask's verdict (`CHALLENGE.md`). Core lines build stop A, whose proof is the core sentence: "With the fix in, a deep CI run on engine/base ends green on Linux and Windows, with no check switched off or silenced." Later lines wait for stop B, briefed after stop A merges (his answer, D1).

## S1 (core): make the deep run green

- **S1.a** [core] Today's behaviour of the two Windows credential calls the typing fix has to touch, reading and deleting the node's grant entry, is pinned by tests that run on Linux and Windows alike, through a fake that keeps the Windows API's contract (a zero return means failure and the reason is the last-error code; 1168 means not found). They pass before and after the fix. They exist because the deep run mutates every function a change touches, on Linux, and these two have no Linux test today (`GROUND.md`, "Found after the challenge").
- **S1.b** [core] The qmn Linux type check (`qmn-lane`: pyright for Linux over `qmn/src` and `qmn/deploy`) reports 0 errors, down from 107, with no ignore marker, no rule turned down and no platform setting changed; on Windows the same files still type clean. The only functions whose lines change are the two pinned in S1.a.
- **S1.c** [core] The qmx-apps test file that ends in eight extra blank lines passes the format check, so the `lint` job is green.
- **S1.d** [core] Windows behaviour is unchanged: the Windows suite's credential-store and deployment-reader tests and the S1.a pins pass at the head, and off Windows the credential store still refuses to start and the grant still goes to the owner-only file.

## S2 (later): the 57 baselined rows

- **S2.a** [later] The 31 qmx-home rows from Windows-only code (`backup/restore.py`, `files.py`, `tests/test_backup_plan.py`) are gone from `ci/baselines/pyright.txt`, through platform conditions pyright reads and no suppression; the kit's merge prune drops the rows.
- **S2.b** [later] The 12 qma-harness rows (`launcher.py`, `harness/procs.py`) are gone the same way.
- **S2.c** [later] The 7 test-only rows in qmx-host (`tests/test_vault_acl.py`), qmx-apps (`tests/test_data_reads.py`) and qmx-engine (`tests/test_zones.py`) are gone the same way. The 7 rows in his guarded parts (`qmx_engine/nodes/script.py`, `qmx_apps/supervisor.py`) stay in the baseline unless he says otherwise when stop B is briefed.
