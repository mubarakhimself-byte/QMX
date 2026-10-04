Independent bounded QMB scaffold fix review

Verdict: ACCEPT faf79b93499056fe9f999be51c13b48f5aff40a7
Compared against: 8d76250280b4566cb4fe61a3528f3d7eccc4de5c
Reviewer: delegated peer /root/review_scaffold_fix (not fix author)
Reviewed checkout: C:\Users\Mubarak\Documents\Codex\2026-10-04\task-19\qmb-review
Scope: the complete one-file fix diff, surrounding scanner implementation and
controls, plus interpretation/reproduction of the requested native observations.
Repository was clean at the exact reviewed SHA before and after verification.
No repository file was edited by this reviewer.

Findings: no blocking defect in the bounded fix.
The change restricts the CLI claim-read exception to a single claim_path argument,
omitted/default read mode, only literal encoding='utf-8' keywords, and the direct
backtest_run function scope. It rejects write/update/append modes, custom openers,
keyword expansion, dynamic encoding, and nested function/lambda/class scopes.
The receipt proof scanner no longer accepts a guard containing an assignment
expression, so falling through cannot retain a proof invalidated by rebinding
the checked subject. Existing nominal import/type/scope/rebinding controls pass.
These changes tighten test gates; they do not change runtime code, durability,
risk policy, production routing, fixture authority, skips, or xfails.

Independent verification (supported local approval route; exit zero each):
1. .\run-review.ps1 -Label scaffold-fix-independent-review -TestArgs @('qmb/tests/test_qmb_scaffold.py')
   13 passed, 6.00 seconds.
2. .\run-review.ps1 -Label structural-fix-independent-peer -TestArgs @('qmb/tests/test_qmb_scaffold.py','qmb/tests/test_sandbox.py','qmb/tests/test_cli_host.py')
   76 passed, 4 existing Windows chmod skips, 23.45 seconds.
3. .\run-review.ps1 -Label scaffold-controls-independent-peer -Probe C:\Users\Mubarak\Documents\Codex\2026-10-04\task-19\peer-scaffold-probe.py
   Independently extracted helper ASTs from both exact Git commits. Reproduced
   original write-mode/custom-opener/expanded-keyword/dynamic-encoding/nested-scope
   exemptions and stale nominal/isinstance receipt proofs after walrus rebinding.
   All 15 fixed-commit controls passed, including accepted default read and UTF-8.
4. .\run-review.ps1 -Label native-observations-independent-peer -Probe C:\Users\Mubarak\Documents\Codex\2026-10-04\task-19\adversarial-review.py
   Independently reproduced native observations in fresh unique local fixtures.
   Empty attribute-only anchor could be renamed. Public root rename+junction swap
   succeeded on the held moved root and left the junction target empty. Ordinary
   hardlinks were accepted, and outside aliases could be added to an already-held
   temp, including the share-zero diagnostic; forced share-zero publication refused.
   Completed race-winner retry acknowledged after two observed flush calls.
   Preexisting writable-mapping diagnostic refused and canonical bytes remained.

Each evidence/<label>/ directory contains command.json, provenance.json, pytest.txt
and pytest.exit. CPython 3.14.7 and pinned borrowed dependencies are recorded.
Parent and child workspace modules resolve to task-19/qmb-review only. This is not
a fresh dependency installation, coverage gate, or complete platform test run.

Native interpretation: these observations do not independently establish a
content overwrite, replacement-target write, or a violation of the existing
descriptor/handle-pinned contract. The preexisting POSIX source test explicitly
accepts publication to the moved admitted root after its pathname is swapped;
the reproduced Windows public case has the same result. The handoff should not
claim all held empty anchors cannot be renamed. It should state that directory
identity is pinned and publication stays relative to the admitted handle even
when the original spelling is redirected. Requested share flags are not proof
that attribute-only directory handles enforce rename denial.

Hardlink-free confinement is not implemented and is not an established contract
in the reviewed material. An alias created by another filesystem actor is not,
by itself, proof that this writer followed an outside pathname or overwrote an
outside object's contents. Document hardlink behavior and do not claim universal
alias isolation. The current evidence gives no reason to weaken/share-zero the
store or add a broad hardlink policy just to make this diagnostic green.

Primary references checked:
https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_link_information
  Microsoft documents that setting FILE_LINK_INFORMATION needs no specific
  access rights. This supports the observed share-zero alias behavior; it does
  not itself prove every imaginable hardlink race harmless.
https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information
  Microsoft documents handle-relative RootDirectory rename targeting and
  ReplaceIfExists=FALSE failure on an existing target.
https://docs.python.org/3/library/functions.html#open
  CPython documents open's default read mode and custom opener capability.

Limits/blockers preserved: this acceptance concerns the bounded scaffold fix
and the above native-observation interpretation, not a new independent review
of every original 13-file repair. No Linux execution, physical power-cut test,
hardware-cache durability experiment, coverage floor, fresh full-QMB run, or
full-platform acceptance is claimed. Original 1460 passed/19 skipped/1 Study
failure is inherited author evidence. The Study production routing/envelope/
parser integration remains an integrator-owned blocker and was not changed.
