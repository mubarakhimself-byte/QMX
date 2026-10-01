# Node deployment asset packaging

Actual inspection of the 480d3bf8 provisional bundle found **zero** `deploy`
entries in both `qmn-0.1.0-py3-none-any.whl` and `qmn-0.1.0.tar.gz`. The
standalone node operations toolkit, systemd templates and observability
configuration would therefore be absent from that installed bundle.

Candidate builder now archives `qmn/deploy` from the same immutable registered
candidate worktree into checksum-bound `qmn-deploy.tar.gz`. The installer
requires this archive and README, checks its safe regular-file paths and
mandatory operations/template entrypoints before creating any environment,
and extracts it into the new installation's `qmn/deploy`. On Linux, a local
`.venv -> venv` alias preserves the source systemd templates' declared Python
path. Windows QMN placement remains separately unresolved. This installs no
services, changes no system deployment paths and invokes no operations script,
provider or trading act.

`uv run --no-sync python -m pytest tools/tests/test_release_install.py tools/tests/test_release_gate.py -q`
PASS 128. Positive installer test uses explicitly mocked venv/pip and actual
archive extraction. Negative controls reject traversal, absolute/Windows-root
paths and hash-valid missing mandatory template before environment creation.
Ruff and scoped Pyright PASS; log `/workspace/qmx-deploy-packaging-tests.log`,
`/workspace/qmx-deploy-packaging-types.log`. Independent review and real
immutable bundle rebuild/install after this change remain NOT RUN. Prior
35-artifact reproducibility evidence applies only to its recorded older SHA,
not this expanded candidate inventory.

Independent Sol review found a post-preflight node archive replacement could
be extracted after venv/pip setup. Installer now copies every inventoried
input into a private temporary snapshot, rechecks every hash and reruns
complete preflight there before environment creation. Pip, archives, README,
launcher and recorded manifests use that verified snapshot only. Source refs
are now bundled and copied as `source-manifest.json`.

Regression controls cover replacement before snapshot (refusal, no destination)
and during environment creation (original verified contents installed). The
positive mocked wheel-install control checks all 14 actual input byte hashes,
not their original directory location. Focused installer/gate suite PASS 130;
Ruff and scoped Pyright PASS 0 diagnostics. Independent Sol mutation controls
also passed for all original bundle assets replaced after snapshot, including
lock and wheels, and for lock replaced before snapshot. Real expanded bundle
build/install and stable-commit review binding remain pending.


Actual immutable build/install verification (2026-10-01): candidate
`88fa98073263e9a4569129c7572bb47a6182381a` built from registered detached
`/workspace/QMX-package-assets` into `/workspace/qmx-bundle-assets-candidate`.
A second build into `/workspace/qmx-bundle-assets-repeat` produced the same
38 inventoried artifacts with every SHA-256 identical (PASS;
`/workspace/qmx-reproducibility-assets.json`). Commands used the release venv
Python with `tools/build_release.py <destination>`; logs
`/workspace/qmx-bundle-assets-build.log` and
`/workspace/qmx-bundle-assets-repeat.log`.

The bundled installer ran outside the checkout:
`/workspace/QMX-release/.venv/bin/python /workspace/qmx-bundle-assets-candidate/install.py /workspace/qmx-installed-assets-candidate`.
PASS: all 14 product wheels installed non-editably, locked dependencies and
`pip check` succeeded. QMB/QMN/QML imports resolve inside installed site-packages.
The installed `qmn/deploy` tree contains 62 paths, source-manifest.json exists,
and the Linux `venv` alias resolves to `.venv`. Log:
`/workspace/qmx-assets-install.log`.

Actual installed launcher and `qmb host` commands ran from `/workspace` against
fresh state `/tmp/qmx-bundle-assets-wjnw70tg` and loopback port 57129:
start → status → stop → stopped status → restart → status → final stop all PASS.
Process ids were 52414 and 52474. Reproducible smoke script:
`/workspace/qmx-assets-candidate-smoke.py`; exact commands/output:
`/workspace/qmx-assets-candidate-smoke.log`. This verifies packaging and local
host lifecycle for that recorded SHA, not later source repairs or full release
acceptance. No deployment script, system service or provider act was invoked.
Native Windows and connected product execution remain pending.
