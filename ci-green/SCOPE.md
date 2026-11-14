# Scope: ci-green

Ask as given: "Make QMX's CI deep run go green on Linux and Windows by fixing the Linux type-check and format failures in product code (issue T-22)." (the lead, U19 planner brief, 2026-11-14, from his yes to the factory design's call H8)
Expand depth: light, because the ask is one known CI defect (T-22) in code that exists, with the failing run's logs in hand.

## Restatement

His goal: the CI he has now (GitHub Actions, `qmx-ci.yml`) can pass. Today no deep run on `engine/base` can be green, so the gate refuses every pull request into `engine/base` and nothing can ship through the factory. The factory design asked him (call H8) to merge PR #1, the CI, and to make the first build through the factory the real fix for the Linux typing errors (T-22 in `tracker/ci/ISSUES-2026-11-12.md`). He said to go with the recommendation. PR #1 is merged (`773952ce`) and the types ratchet is in. What is left is the fix itself: Windows-only code that pyright on Linux cannot type, and one format error.

The problem in plain words: QMX runs on Windows first. Some of its code calls Windows-only parts of Python (the Windows DLL loader, Windows process flags, the Windows credential store). CI also checks the code's types as if it ran on Linux, and those Windows-only calls fail that check because nothing tells the checker they only run on Windows. The fix tells the checker, without changing what the code does on Windows.

This is the contained door (the lead's call, 14 Nov): one area (CI typing), behaviour on Windows must not change, and it touches the credential store, which sits on a fixed line (keys), so it is not the mechanical door the design first named for U19.

To confirm with him: nothing. The restatement and the light depth follow from his yes to H8, the lead's brief and T-22; he asked not to be asked about CI ("this is not my cup of tea", see S1's source). No open decision for him.

## Destination

> "Now H8, merge PR1, the CI. I don't know, man. Go with the recommendation if you see fit." (dd8f4ab2:L7041 (Shipping rate and agent orchestration, 2026-11-13))

Done when:
- a deep run of `qmx-ci.yml` on `engine/base` passes the `lint` and `qmn-lane` jobs, so its `deep-verdict` can run;
- the rows of `ci/baselines/pyright.txt` that come from Windows-only code are gone from it, and Windows behaviour is unchanged (the Windows suite's tests of that code still pass).

## His asks

- **S1.** "Now H8, merge PR1, the CI. I don't know, man. Go with the recommendation if you see fit." (dd8f4ab2:L7041 (Shipping rate and agent orchestration, 2026-11-13))

Verdicts and the PR budget are in `CHALLENGE.md`.

## Decisions so far

- CI is the merge gate; merging on a local gate is a no. His: "What's the point of CI if we are merging locally?" (dd8f4ab2:L7041 (Shipping rate and agent orchestration, 2026-11-13))
- H8 is yes: merge PR #1, then the Linux typing fix is the first program through the factory. Agent note of his answer (`tracker/shipping-method/FACTORY-CALLS-2026-11-13.md`, row H8; `tracker/shipping-method/FACTORY-DESIGN-2026-11-13.md`, U19).
- A new `# type: ignore`, `# pyright: ignore` or `# noqa` marker, or a pyright or ruff rule turned down in a pyproject, counts as baseline growth and blocks at the gate. Agent (lead decision D-L17, `tracker/shipping-method/BUILD-LOG-2026-11-13.md`). So the fix is real platform guards and typing, never a suppression.
- Door: contained, kind `feature`, light depth. Agent (the lead's U19 brief, 14 Nov). Conflicts with the design's first plan for U19 ("a mechanical-door sweep", `FACTORY-DESIGN-2026-11-13.md` U19 row); the lead's call stands because the credential code sits on fixed line 5 (keys).
- PR #1's five product edits get a second look in this program's verdict. Fable (`FACTORY-DESIGN-2026-11-13.md`, section on SYSTEM-AUDIT item 5). Taken here as proposal P1, not as part of S1.

## Proposals

Agent ideas beyond his asks. Each waits for his yes at plan review; anything he does not pick is parked.

- **P1.** Second look at the five product and test edits PR #1 carried (`qmn/src/qmn/host/qa_debt_matrix.py`, `qmn/tests/test_qmn_deploy_switch.py`, `tools/tests/test_readiness_gate.py`, `tools/tests/test_ci_driver.py`, and the deleted `tools/tests/test_mutation_workflow.py`). Why: Fable decided they are reviewed by this program's verdict rather than waved through with PR #1. Would serve: none (none of them is red at the tip).
- **P2.** A Linux pyright check of the five qmx-agents packages that blocks on its own (as `qmn-lane` does for qmn), once their rows are gone, so Windows-only code cannot slip back in through the baseline. Why: today the rows only sit in the ratchet; a new Windows-only call in a file already listed adds a row the ratchet calls new, but nothing names the cause. Would serve: S1.

## Not yet specified

Nothing: every part of S1 is grounded in `GROUND.md`.

## Out of scope

- The 11 baseline rows in `qmx-host` that are ordinary type errors, not Windows-only code (`host.py` costs and funding, `app_logs.py`, `tests/test_app_logs.py`, `tests/test_heartbeats_loop.py`). Why: they are not the Linux typing fix; the held risk stack (`build/rc-35`) already edits `host.py` and `app_logs.py`.
- Known red tests and flaky tests (`ci/baselines/known-reds.txt`, `flaky.txt`), the Skylos whole-repo time limit (U37), coverage floors (T-24), the old-repo git pins (T-21), the mutmut walk, the `pull_reds` skipped-job count, untyped host responses. Why: the lead's brief: "out of scope: anything that isn't making the deep run green on these failures."
- Turning Linux typing off (setting `pythonPlatform = "Windows"` in the five package configs, or dropping `--pythonplatform Linux` from `qmn-lane`). Why: it hides the errors instead of fixing them; his yes was to the real fix.
