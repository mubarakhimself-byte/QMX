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
