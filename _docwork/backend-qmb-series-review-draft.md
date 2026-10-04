# Independent bounded QMB runtime review

Verdict: **hold the seven-commit series as a complete accepted increment**. There is one independently reproduced native publication/authority blocker. The remaining bounded edits have no material blocker identified in this review; the documented Study ingress failure remains unresolved. No source was changed in either candidate, no commits were applied, and no broad suite was rerun.

## Exact reviewed identity and scope

Read-only source: `C:/Users/Mubarak/Documents/Codex/2026-10-04/task-16/qmb-runtime`, branch `fix/qmb-native-runtime`, HEAD `8d76250280b4566cb4fe61a3528f3d7eccc4de5c`, base `33165e84146b2a6da32c7e536b698c4fa609be3f`. Git status was empty before and after review. Every Git call supplied the exact per-command safe.directory; no global configuration was changed.

Ordered series:

1. `2f7eb957f2fab7f2e916816e6860dc368d5751f0` native store/access/durability
2. `c5107b0fc144978f71633654eaab547d23c633e2` immutable declarations and scaffold proofs
3. `2f190f26fcdbf230cb4562e31ce0e36bdfbb9ae5` bot sandbox structural assertion
4. `9e335fbefe69bc78bffaf705eb5f3779337512f8` Windows diagnostic text assertion
5. `9406004be7f6f6ae266ba47b06aff6a6dc7ab1ad` durable analysis examples
6. `423241e5941fad825c0e1d749dc1f2f72d2a70f1` Study ingress diagnosis
7. `8d76250280b4566cb4fe61a3528f3d7eccc4de5c` handoff/draft ledger/documentation

Inspected complete source/test/example delta and drafts, plus `task-16/FINAL-QMB-RUNTIME-HANDOFF.md`. `git diff --name-only 9406004b..8d762502 -- qmb` is empty: the author's full-QMB evidence applies to the final runtime tree. Only QMB and draft documentation paths changed; no QMA/QMN/UI/manifests/lock/public-projection implementation delta was present.

## Blocker B1: attribute-only directory anchors do not provide the claimed sharing authority

Locations: `qmb/src/qmb/host/_windows_research.py:135` (`access = 0x80 if directory ...`), `_root:179`, `write_blob:297`; `qmb/tests/test_research_windows.py:143` exercises the move too late.

The repaired adapter retains every directory handle with FILE_READ_ATTRIBUTES only and ShareAccess=FILE_SHARE_READ. This does not enforce the claimed directory delete/write sharing exclusion before a data-access leaf handle exists. The existing ancestor replacement test injects at `_rename`, after the writable temporary leaf has opened; that leaf already blocks directory replacement on this NTFS host. It does not cover the gap between acquiring the directory anchors and opening the first leaf.

Independent real-NTFS attack: after `_root` has acquired and checked all anchors, intercept `_flush_existing` before its first file open and rename the admitted research directory to a disposable sibling outside the declared research_root path. The original adapter continues handle-relative creation and publication in the moved directory and acknowledges success. The corresponding read attack moves the directory immediately before the first leaf open and still succeeds.

The public API was also exercised with an actual QML-authored canonical Stage-0 hypothesis and its matching research fingerprint: `persist_research_blob` returns Ok, `Ok.value.path.exists()` is false, and the admitted canonical bytes are present under the moved outside directory. This is not fabricated provenance, a mocked filesystem, a synthetic success result, or a provider call. Only deterministic scheduling seams are monkeypatched; NTFS performs the actual opens, directory moves, writes, rename, flush, and readback.

This proves a discrepancy with the Windows adapter's asserted namespace pinning and returned publication path. Handle-relative operations still reference the original admitted object: the experiment does **not** prove that a swapped foreign leaf or reparse target can substitute its bytes. Existing POSIX tests deliberately permit moving a held root and operate on its admitted inode; they do not establish the stronger Windows deny-sharing claim or make a nonexistent returned path a proof of Windows pathname containment. Keep that distinction explicit when reconciling the contract.

Both restricted `desktop-lagn1js\\codexsandboxoffline` and normal `desktop-lagn1js\\mubarak` tokens reproduce the two low-level gaps. The public-API reproduction ran under the normal Mubarak token. Exact imported source was asserted to task-16; adapter SHA-256 is `380bdeeac9c79af668aaadbe02858a68f966789d192d4f2ddcce114226c567e0`.

Evidence under `task-12/evidence/qmb-native-independent`:

- `probe_preleaf.py`, `run.ps1`: reproducible scheduling attack and isolated runner; borrowed recorded pinned dependencies, task-16 sources first, bytecode disabled.
- `probe-preleaf.txt` / `.exit`: original sandbox run; two containment failures; Python exit 1.
- `normal-token.txt`, `normal-probe-preleaf.txt` / `.exit`: normal-token reproduction; Python exit 1.
- `normal-public-token.txt`, `normal-public-probe-preleaf.txt` / `.exit`: actual public canonical-byte persistence succeeds despite missing returned path; same two low-level failures; Python exit 1.
- `disposable-*`: retained disposable fixtures, entirely under task-12, including moved published blobs. No global or original-worktree data was removed.

Useful diagnostic, **not a completed fix**: an in-memory wrapper adds FILE_LIST_DIRECTORY to each directory DesiredAccess, producing 0x81 without SYNCHRONIZE. Under the restricted token this fails WinError 5 before attempting the move. Under Mubarak's token every ancestor is acquired, the malicious rename is blocked, and the read completes correctly. The write subsequently refuses WinError 32 during actual publication. Thus neither metadata-only fallback nor a blind 0x81 replacement earns acceptance; directory pinning and the native target-rename sharing relationship must be solved together.

Required bounded correction: preserve no-follow/type/reparse validation and real namespace authority from component admission through completion; refuse before effects when the host token cannot establish that authority. Add early-root/ancestor movement controls before first leaf acquisition and during component walking, alongside the existing later temporary/published-file controls. Test successful ordinary native write/read/restart under the legitimate normal token as well as adverse moves, reparse replacement, no-clobber races, and flush faults. Do not weaken the contract for restricted-token convenience. Update the native review, handoff, ledger proposal and unapplied canonical draft: their current statement that attribute-only anchors deny directory write/delete sharing is unsupported.

Microsoft's [CreateFileW documentation](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew) distinguishes attribute access from sharing-controlled data access and documents delete access as governing rename. [NtCreateFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile) describes separate directory access rights and native options. These official references were consulted during review; the decisive evidence is the host reproduction, not an inference from a numeric mask alone.

## Other bounded changes and durability review

The native code keeps no-clobber rename, exclusive writable temporary ownership, held-object identity/byte readback, synchronous file descriptors, write-through files, flush-before-publish and flush-after-publication. Existing/race-winner acknowledgement now checks equal bytes and fsyncs under one held writable handle; a sharing conflict refuses. Pre-publication cleanup deletes the owned temporary by handle; post-publication failure retains the final blob and refuses. These are useful corrections. They do not repair B1 or constitute power-cut/hardware-cache evidence. No path-following fallback or replacement rename was introduced. Native errno/winerror retention is narrowly diagnostic; the POSIX source delta is formatting-only.

The scaffold changes use supported immutable ctypes argtype tuples and an immutable empty mapping. The AST allowance for builtin open is scoped to the existing claim_path read in backtest_run, rather than exempting the entire CLI module. Exact nominal StoreReceipt-member guards, alias narrowing and assignment/rebinding invalidation are accompanied by adverse controls. The scanner is an approximate structural contract check, not a complete static authority proof. No runtime authority or vocabulary schema is widened.

The sandbox structural assertion now checks runner.py and worker.py, matching the stated bot execution boundary. Allowing the independent host filesystem adapter to use ctypes does not claim stronger bot OS confinement. Diagnostic assertions inspect the actual reason string instead of escaped mapping repr. No runtime diagnostic was suppressed.

The two analysis examples now accept an explicitly trusted operator builder and a CT29ProjectionSource locator, then let the existing project admission reopen and validate durable replay provenance. The shipped examples do not import test builders or treat copied trades as durable authority. The test-only builder creates real local persisted replay sources. Comparison/rerun toy input remains explicitly illustrative. The project example requires its documented two-close fixture shape; this is not a universal operator replay viewer or a new public projection/publication capability.

Independent focused verification: **5 passed in 27.29s, exit 0** with task-16 sources first, workspace-only cache/temp/evidence, and no coverage/full-suite invocation. Included existing late ancestor/temp attack, the new nominal receipt negative controls, runner/worker boundary check, and both actual persisted-source analysis examples. The late attack passing alongside the earlier independent reproduction demonstrates the coverage gap rather than cancelling the blocker. Exact command/head/status/PYTHONPATH and output are `evidence/qmb-native-independent/{pytest-command.json,pytest.txt,pytest.exit,run_tests.ps1}`.

## Study and broad acceptance limits

Disk evidence `task-16/evidence/qmb-full-reviewed/{pytest.txt,pytest.exit}` confirms **1460 passed, 19 skipped, 1 failed in 940.45s**, exit 1. The enabled failure is `test_optimize_atc_cli_ingress_characterization.py::test_backtest_preflight_selects_operator_bound_alternative_study_descriptor`. The recorded strict gate has zero diagnostics; lint passes; thirteen changed Python files are already formatted. Whole-QMB formatting remains red on five unchanged files. The run used --no-cov, borrowed pinned environments and existing platform skips; it establishes neither a new frozen installation nor coverage/release/platform acceptance. No broad gate was repeated here.

The Study diagnosis correctly separates actual local Quant/ExperimentSpec/source registration and library execution from authenticated provider authoring and composed production CLI admission. It preserves the malformed old characterization as red instead of promoting its five-reference placeholder to authority. The documented optimize.run envelope discrimination, complete exclusive private Study descriptor, durable expected-invocation result verification, stable-versus-operational fingerprint cycle and truly read-only verification concerns are coherent integrator seams. QMA result checks must branch by real result contract; verification must not complete missing trials or mint witnesses. Canonical actor restoration is still an independent lifecycle requirement. This series does not implement those joins.

Recommendation: accept the non-native bounded repairs/diagnosis only after normal commit dependency review, while keeping B1 explicitly blocked and native claims corrected. Do not label all seven commits reviewed-and-accepted, or use the 1460 passing tests as native publication/platform acceptance. The integrator owns application and the remaining CT47/public projection contract work.
