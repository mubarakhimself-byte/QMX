# Independent packaging, installation and source coverage review

Reviewer: GPT 6.1 Sol. Reviewed `tools/build_release.py`, `release/install.py`,
`release/launcher.py`, `tools/release_gate.py`, root coverage configuration and
`tools/coverage_report.py` against the release candidate working tree. Final
packaging commit and installed product acceptance remain pending. No product
source changes were made by this reviewer.

## Current findings and limits

- Installer originally verified only listed files but installed every globbed
  wheel, allowing an unlisted artifact to be consumed. The corrected candidate
  derives wheels from the checksum inventory and preflights required files and
  distributions before creating the environment. Source inspection verifies this
  correction; a synthetic incomplete manifest now refuses before install calls.
- Release gate trusts wheel filenames for distribution identity. Held-out zip
  `qmb-0.1.0-py3-none-any.whl` containing only
  `unrelated-0.1.0.dist-info/METADATA` with `Name: unrelated` produces no
  `_artifact_errors`. Required distribution names must match actual metadata;
  installability also requires WHEEL/RECORD rather than arbitrary metadata alone.
  Reported to coordinator and installer owner.
- Builder accepts arbitrary external `--ui-build` content with an index.html,
  assigns the current HEAD candidate, and does not prove that UI output was built
  from that candidate. Clean source status cannot establish arbitrary prebuilt
  asset provenance. Same-candidate build evidence or an internally performed
  pinned UI build is required before artifact acceptance.
- Root coverage explicitly measures package source directories, the calendar
  extension, QML/QMB/QMN and QMN deployment code; tests cannot pad those sources.
  The source inventory additionally rejects omitted tracked shipped source in
  the CLI enforcer. Nested QMA's test command still uses `--cov=qma` with
  `--cov-fail-under=0`; root coverage does not establish nested coverage floors.
  The source_coverage acceptance lane must separately establish nested shipped
  source measurement and its applicable gates.
- SOURCE_DATE_EPOCH and normalized UI tar metadata improve reproducibility, but
  build backend requirements remain a version range (`uv_build>=0.12,<0.13`),
  and the build tool environment is not artifact-bound. Repeated-build byte
  equality has not been established.
- Launcher invokes installed `qmb host start` and preserves its status. It does
  not establish UI serving, browser journeys, configuration completeness, or a
  functioning clean installation. These remain explicit acceptance checks.

The installer can install a candidate whose product acceptance checks remain
pending, and says so explicitly. Installation is not release acceptance; the
release gate requires all mandatory lanes to report PASS for the candidate and
artifact inventory. No release acceptance is claimed here.

## Independent checks

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider tools/tests/test_release_gate.py tools/tests/test_coverage_report.py
```

Result: **221 passed in 0.23s**. The wrong-distribution held-out described above
exposes a gap beyond that passing suite.

Separately exported the current root and nested runtime locks with:

```sh
uv export --locked --no-default-groups --no-emit-local --no-header --package qmb --package qmn --package qmf-calendar-forex
uv export --locked --no-default-groups --no-emit-local --no-header --project qmx-agents --all-packages
```

Comparing overlapping exact version entries found **no conflicting current
pins**. This does not certify cross-platform marker resolution, build dependency
reproducibility, clean installation, wheel-native dependencies, or Windows launch.

## Corrected candidate recheck

Builder now removes the external UI directory argument and rebuilds the actual
candidate in a disposable registered detached Git worktree with requested
Node 22.12.0, pnpm 10.18.3 and frozen installation. It emits checksum-inventoried
UI provenance. Gate now validates wheel distribution identity and WHEEL/RECORD,
and compares pack inventory against actual daemon wheel resource bytes. These
corrections address the corresponding initial findings by source inspection.

Further issues reported during review:

- Mandatory artifact checks still used suffix matching, permitting e.g.
  `xui-build.json` while exact provenance lookup was absent and skipped. Required
  files should be exact inventory keys and missing provenance must refuse.
- Backend wheels and pack inventory were built from live ROOT after a single
  initial cleanliness check; edits during construction could label modified
  bytes with HEAD. An immutable candidate snapshot or post-build source identity
  recheck is needed before writing the bound manifest.
- New installer requirement preflight initially rejected both actual builder
  `uv export` outputs: continuation backslashes on hash lines were checked before
  stripping. Reproduced by calling `_validate_lock` on actual root and nested
  exports; both raise `The product requirements lock has a malformed hash line`.
  Reported immediately to installer owner and coordinator.

Independent corrected gate/coverage suite: **223 passed in 0.25s**. Actual prior
uv-built wheels (seven under `/tmp/qma-wheel-check`) pass new installer archive
and metadata preflight. They are positive format controls, not final-candidate
installation acceptance. Final corrections and installed bundle check pending.

## Latest source verdict

Bounded packaging/gate/source-coverage delta is **approved pending final commit
identity**. Builder now constructs backend wheels, UI, both exported locks,
installer/launcher and pack inventory from the same detached candidate snapshot.
Mandatory gate files use exact keys and absent exact UI provenance refuses.
Nested coverage now declares all three QMA source roots, an 80% aggregate floor,
a JSON report, and a separate tracked-source/per-package 80% enforcer. QMF
exact/chrono remain required in the root enforcer; nested deliberately omits those
root-only contract modules through an explicit parameter.

Independent nested held-outs pass: omitting a daemon source refuses; adding
1,000 covered test lines cannot conceal a 10% daemon source; a fully covered
three-package source report passes. Repeated gate/coverage suite is **223 passed
in 0.22s**. This verifies enforcement, not actual achieved workspace coverage.

Installer owner corrected continuation parsing; both actual root and nested
`uv export` locks now pass independent `_validate_lock` calls. Clean bundle
installation, actual production launch/browser serving, achieved full-workspace
coverage floors, repeated-build byte equality and Windows remain unestablished
by this review. Runtime installation may require downloads; it is not certified
as offline. The final installer commit and its test evidence remain pending.

Root packaging/gate/coverage slice is now bound to reviewed commit
`c3821ea018641032adb7e10aa99c365664498807`. Independent installer tests now pass
**7/7 in 0.15s** after fixing accidental literal plus signs in its continuation
fixture. Actual generated export controls continue to pass; source installer
commit remains pending.

## Final bounded review binding

Installer final commit `ad24e8eb42ea0e44669d9ef67683ec8a086c1026` is inspected;
its independent committed suite passes **8/8 in 0.16s**. Together with root
packaging/gate/coverage commit `c3821ea018641032adb7e10aa99c365664498807`, the
bounded source changes are **approved**. The prior pending-commit wording above
records the review sequence. Product build/install/launch/coverage/Windows
acceptance limits remain as stated; source review cannot close those lanes.
