# Installed candidate dependency audit

Partial security evidence, 2026-10-01. This does not approve the candidate's security lane.

The non-editable installation at `/workspace/qmx-installed-replay-candidate` was built from frozen commit `1c4c73b1e51e9194464601830e7543ecd1108b6d`. Command:

```text
uv tool run pip-audit --path /workspace/qmx-installed-replay-candidate/venv/lib/python3.14/site-packages --progress-spinner off --timeout 20 --format json --output /workspace/qmx-installed-replay-dependency-audit.json
```

Exit 0; 39 installed distributions inspected. The public vulnerability database reported no known vulnerabilities for 25 third-party distributions, including pip. The 14 private QMX distributions were not present on PyPI and were explicitly skipped; they are not security-verified by this result. Exact output: `/workspace/qmx-installed-replay-dependency-audit.json`; trace: `/workspace/qmx-installed-replay-dependency-audit.log`. The audit tool is separate tooling, not a product dependency. No automatic upgrades or lock changes were made.

Current working-tree money, ambient nondeterminism, mock-data and secret scans passed (`/workspace/qmx-current-{money,ambient,mock,secret}-scan.log`). These are intermediate scans, not immutable final-candidate evidence. Source authentication, authorization, persistence and installer reviews provide bounded evidence elsewhere; complete security verification and a same-final-candidate dependency audit remain pending.

The frozen published UI baseline's lock was audited separately with pinned Node 22.12.0/pnpm 10.18.3, an empty user npm config and ambient npm auth variables removed. Read-only `pnpm audit --json` exited 1: 340 dependencies, one low-severity advisory, no moderate/high/critical advisories. `@sveltejs/kit > cookie@0.6.0` is affected by GHSA-pxg6-pf52-xh8x (cookie name/path/domain validation; fixed in >=0.7.0). Exact output: `/workspace/qmx-ui-baseline-dependency-audit.json`; stderr: `/workspace/qmx-ui-baseline-dependency-audit.log`. UI repair ownership remains with the user's separate Claude work; a reviewed fix or evidence-based disposition and re-audit are pending. No UI source, lock or dependency versions were changed.
