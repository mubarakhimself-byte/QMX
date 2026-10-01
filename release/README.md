# QMX candidate build and installation

This bundle is a release candidate under verification. Building or installing
it does not certify release acceptance. Read `acceptance.json` and the
repository `release/evidence` records for exact commits and PASS/FAIL/BLOCKED/
NOT RUN results. Native Windows, external provider connectivity, connected UI
journeys and incomplete security verification must not be inferred from Linux
unit tests or local doubles.

## Reproduce the bundle

Use a clean, registered checkout of the candidate commit recorded in
`acceptance.json`. CPython 3.14, Git, uv and npm must be available. The builder
uses an isolated registered Git worktree at that commit, both committed uv
locks, and Node 22.12.0/Pnpm 10.18.3 for the committed UI. It refuses dirty
product source and an existing nonempty output directory.

```sh
python3.14 tools/build_release.py /absolute/path/qmx-bundle
```

The bundle includes all 14 product wheels and source distributions, the UI
archive, hash-pinned third-party runtime requirements, installed pack resource
inventory, installer and launcher. Factory tooling is not a runtime dependency.
Build a second empty destination from the same commit and compare the hashes
in the two `acceptance.json` artifact inventories to test reproducibility.
The candidate is a full Git SHA; source refs are recorded in
`release/SOURCE_MANIFEST.json`.

## Install outside the checkout

Run the installer with CPython 3.14 and a new destination:

```sh
python3.14 /absolute/path/qmx-bundle/install.py /absolute/path/qmx-install
```

The installer validates inventory, checksums, wheel metadata, runtime lock and
UI archive before creating the private environment. It installs locked runtime
dependencies, installs bundled product wheels without resolving unrelated
packages of the same name, and runs `pip check`. The bundled lock still requires
access to its runtime package index; this is not an offline dependency cache.
Installation preserves an existing destination by refusing to overwrite it.

On Windows use `py -3.14` for the installer and `venv\Scripts\python.exe` /
`venv\Scripts\qmb.exe` inside the destination. These paths are documented
platform behavior, not evidence of native Windows verification.

## Configure and run the local host

Before starting, create `operator-config.json` in the daemon data root with a
`research_corpus_root_path` naming an existing readable corpus directory.
The root is `$XDG_STATE_HOME/qmx/qma-daemon` (or the documented default local
state directory) on Linux and `%LOCALAPPDATA%\qmx\qma-daemon` on Windows.
Product sessions additionally require explicit operator-owned `qmb_bindings`
to registered Quant identities and declared execution environments; consult
`release/UI_INTERFACE.md` and the governing host documentation. Secret values
must not be placed in this configuration or evidence.

```sh
/absolute/path/qmx-install/venv/bin/python /absolute/path/qmx-install/launcher.py
/absolute/path/qmx-install/venv/bin/qmb host status
/absolute/path/qmx-install/venv/bin/qmb host stop
```

Start failures name diagnostic logs. Restart reuses the configured data root.
The launcher starts the local QMA host; it does not create authority grants,
start a trading node, or certify job execution. QMN has its separate
`python -m qmn.host.supervise` entrypoint and explicit configuration/readiness
contract. Provider calls, trading and promotion require operator authorization.

## Acceptance and recovery

`uv run poe check-release` includes the mandatory fail-closed release evidence
gate. Product source and nested QMA source have independent coverage checks.
All required evidence must cite the same final candidate and actual artifact
hashes; skipped tests, doubles and intermediate versions cannot fill missing
acceptance lanes. Keep existing installations/data intact while testing a new
destination. Perform data migrations only under the governing backup-first,
dry-run, migrate, verify and restore discipline.
