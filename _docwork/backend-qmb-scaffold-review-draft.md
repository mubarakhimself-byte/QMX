Independent QMB runtime repair review — 2026-10-04

Verdict: BLOCK 8d76250280b4566cb4fe61a3528f3d7eccc4de5c as submitted.
Base: 33165e84146b2a6da32c7e536b698c4fa609be3f.
Two confirmed scaffold-gate defects have been repaired on an isolated branch.
Separate peer verdict: ACCEPT faf79b93499056fe9f999be51c13b48f5aff40a7 for that
bounded fix, compared with the original candidate. No self-signoff of my fix.
Branch: review/qmb-scaffold-read-proof in task-19/qmb-review.
Original task-16 checkout and integration worktree were not changed.

Review scope
Read task-16/FINAL-QMB-RUNTIME-HANDOFF.md, recorded evidence and review drafts,
the full 13-Python-file patch, and surrounding native adapter, host store,
occurrence, scanner, execution-boundary and analysis-source code/tests. Reviewed
the native ABI declarations/layout, access/options, no-follow relative opens,
ownership transfer/closure, write loops, rename/no-clobber, retry/winner flushing,
verification and cleanup. No risk policy, production routing, parser, Study
fixture or shared CT47/public projection implementation was changed.

Blocking findings in the submitted candidate

1. P2 — The new CLI read exception accepts writes, custom openers and nested code.
   qmb/tests/test_qmb_scaffold.py::_is_cli_claim_open checks one claim_path
   positional argument but ignores keywords and recursively walks nested scopes.
   Consequently open(claim_path, mode='w'), mode='a', mode='r+', **options,
   opener=custom_opener, and calls in nested unrelated functions pass the source
   gate. This weakens the promised narrow existing claim-read exception even
   though the actual shipped call currently uses default read mode and UTF-8.
   The fix permits only omitted/default read mode and literal encoding='utf-8'
   within the direct backtest_run function scope; unknown keywords fail closed.

2. P2 — Receipt type proof survives reassignment in its own guard condition.
   qmb/tests/test_qmb_scaffold.py::_vocabulary_violations adds a nominal proof
   and immediately continues before checking assignments in that statement.
   `if type(receipt.store_receipt) is not StoreReceipt or (receipt := other)
   is None: return False` can fall through with a non-None replacement receipt,
   then whitelist that replacement's store.engine and diagnostic 'engine' key.
   The same defect exists on the isinstance path. The fix refuses narrowing
   from guards containing an assignment expression, preserving later rebinding
   checks. It does not relax the vocabulary gate or alter any runtime types.

Both new regression tests failed before repair (2 failed), then passed. Fix
faf79b93499056fe9f999be51c13b48f5aff40a7 changes only the scaffold test file,
53 insertions and 1 deletion. The new tests exercise actual helper decisions,
including malicious syntax, rather than merely checking implementation text.

Native observations and required wording qualifications

No blocking clobber or replacement-target write was established in the native
runtime repair. Additional probes used clean task-19 source paths, fresh local
fixtures, and the supported require_escalated approval route, without modifying
security settings or enabling privileges.

* An empty directory held by an attribute-only anchor CAN be renamed. A control
  rename without the anchor also succeeds. The candidate's existing test attacks
  only after a writable child temp exists, which can cause the directory rename
  denial; it does not establish the anchor itself denies deletion/rename.
* Public write with the root renamed before temp creation and its pathname replaced
  by an outside junction acknowledges bytes in the held original/moved directory.
  The outside junction target remains empty. This matches the explicit existing
  POSIX pinned-descriptor write contract; it is not a redirected-target write.
* Existing canonical outside hardlinks are accepted for read and retry-save.
  An outside alias can be added to a held temporary file, even in the diagnostic
  forced-share-zero case. No external existing object's contents were clobbered.
  The adapter is not hardlink-free confinement. Adding an unestablished nlink
  policy or weakening publication guards to green this probe is not warranted.
* A preexisting writable mapping makes the retry refuse before acknowledging;
  the diagnostic's attempted after-read mutation never ran, and bytes remained
  canonical. This is evidence of refusal for this case, not every mmap scenario.
* A deterministic completed race winner is compared and flushed before the loser
  acknowledges; two fsync calls are observed and only the final leaf remains.
* FSCTL_SET_REPARSE_POINT can mutate the held attribute-only root after its initial
  check. The subsequent handle-relative temporary open refuses with WinError1921
  / errno22, and the outside target remains empty. The operation does not succeed
  by following the new reparse destination.
* Fresh-process reopen, no-clobber/conflicts, junction refusal, held-temp mutation
  denial, read mutation denial, traversal/ADS rejection, prepublication cleanup,
  postpublication retention and mandatory retry flush all execute natively.

The task-16 handoff and _docwork/qmb-native-store-review-draft.md should qualify
claims that all anchors deny write/delete sharing and that the temp is exclusive.
Requested share flags do not prove universal mutation denial for attribute-only
handles; share-read is not exclusive, and metadata alias operations can succeed.
Use: 'No-follow component opens pin directory identity; operations and atomic
no-clobber publication remain relative to those held handles. Ordinary blob data
writes/deletes are denied during held reads/writes. Empty-directory namespace
changes and hardlinks are not universally excluded; tested root swaps remain
pinned or refuse, with no writes to the replacement junction target.'
This is a correction to evidence wording, not a new hardlink-free product policy.
No original historical evidence was rewritten and no canonical docs were edited.

Other patch conclusions

The ctypes argtypes tuples are supported sequences and preserve every declaration;
Windows integer/pointer/layout sizes and the rename name-byte offset remain valid
on the tested 64-bit runtime. Directory anchors request attributes without
unneeded synchronous I/O rights; file descriptors retain synchronous/write-through
I/O. Open-existing-first avoids creation rights on existing ancestors. Flush errors
refuse, existing/racing content is never overwritten, and handle-only cleanup is
limited to unpublished owned temporaries. The declared NTFS write-through/flush
contract is supported by Microsoft documentation, not a physical power-cut test.

The occurrence sentinel now wraps a privately-created empty mapping, preserving
the missing-context semantics while preventing direct sentinel mutation. Four
occurrence tests pass. The Windows diagnostic assertion reads the actual reason
field rather than an escaped mapping repr. Sandbox assertions retain runner/worker
prohibitions and the existing honest V1 scope; filesystem ctypes is not bot
confinement. Analysis examples supply explicit trusted operator builders and real
durable reader locators; shipped examples do not import test modules. Projection
reopens and validates sources, and copied-row integrity refusals remain tested.

Fresh independent verification

At original candidate (all workspace imports, including child imports, task-19):
  native-independent: 26 passed, 5 existing POSIX-only skips.
  structural-independent: 74 passed, 4 existing chmod skips.
  analysis-independent: 47 passed, including both persisted examples and source
                        integrity/copy-row refusals.
  scaffold-new-controls-red: 2 failed, demonstrating both blocking findings.

At review fix:
  structural-fix-green: 76 passed, 4 existing chmod skips.
  native-fix-supported: 30 passed, 5 existing POSIX-only skips (adds occurrence).
  qmb-lint-reviewed: all QMB checks pass.
  strict-types-fix: zero errors/warnings/informations; Windows strict config,
                    explicit task-19 source/test paths and borrowed dependencies.
  thirteen-python-format-independent: all 13 changed Python files formatted.
  git diff --check: passes; checkout clean at exact fix SHA.
  Five known whole-QMB format files remain byte-identical to the base, verified
  with git diff --exit-code. Whole-QMB formatting is not represented as green.

Separate peer verification (see PEER-SCAFFOLD-REVIEW.txt):
  scaffold-fix-independent-review: 13 passed.
  structural-fix-independent-peer: 76 passed, 4 existing skips.
  scaffold-controls-independent-peer: 15 additional before/after controls pass.
  native-observations-independent-peer: fresh supported native diagnostic replay.
The peer reviewed the complete fix diff and did not edit repository files.

Evidence and delivery

Every test/probe label above has command.json, parent/child provenance.json,
pytest.txt and pytest.exit under task-19/evidence. Check labels have output.txt
and exit.txt. CPython3.14.7 and the pinned borrowed dependency paths are recorded;
this was not a new dependency freeze/install. Native supported runs confirm no
sandbox permission failure was mistaken for a security property.

qmb-scaffold-review-fix.bundle: verified bundle with original candidate prerequisite.
qmb-scaffold-review-fix.patch: format-patch; reverse apply check passes at fixed HEAD.
REVIEW-DELIVERABLES-SHA256.json: SHA256 manifest for review artifacts/evidence.
Integrate via local bundle/cherry-pick only when the parent integrator chooses;
no push, merge, live operation or external message was performed.

Remaining boundaries

The original full-QMB 1460 passed / 19 skips / 1 Study failure is inherited author
evidence, reviewed but not rerun in this lane. No full-suite result is claimed
for the fix. The enabled Study production dispatch/envelope/parser failure stays
integrator-owned and untouched; neither routing nor its fixture was changed.
No Linux runtime, coverage floor, fresh full workspace/platform gate, release
acceptance, power-cut or hardware-cache experiment is claimed. Tests use --no-cov.

Primary references checked

https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile
  Attribute/synchronous access/options, no-follow and handle-relative opens.
https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information
  Handle-relative rename and no-clobber ReplaceIfExists behavior.
https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
  NTFS write-through metadata (including rename), with hardware durability limits.
https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_link_information
  No specific access rights required for setting hardlink information.
https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-fsctl_set_reparse_point
https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-fsctl_get_reparse_point
  Documented reparse set/get IOCTLs; no privileges/settings enabled in this test.
https://docs.python.org/3.14/library/ctypes.html
  argtypes must be a sequence of C data types (tuples are supported).
https://docs.python.org/3.14/library/msvcrt.html
  Native-handle/CRT descriptor conversion.
