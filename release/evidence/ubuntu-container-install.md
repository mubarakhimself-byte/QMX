# Ubuntu container installation and lifecycle

Intermediate PASS for earlier snapshot `1c4c73b1e51e9194464601830e7543ecd1108b6d`, not final candidate acceptance or native Windows recovery. Host remains Debian 13. This test runs Ubuntu 24.04.4 userspace in a community CI container; it does not prove native systemd, hardware recovery, provider connectivity or browser journeys.

## Environment and acquisition

Anonymous acquisition succeeded with `DOCKER_CONFIG=/workspace/qmx-docker-anonymous-config docker pull ghcr.io/catthehacker/ubuntu:act-24.04`. The explicitly empty configuration avoids account credential access. Immutable image digest: `sha256:62d572b92f9f32d3427b6d220ad1f9dca9c7b6ffad37d295425037dbff78abaf`. Image labels identify source `https://github.com/catthehacker/catthehacker/docker_images`, revision `e2f8efe464c82732f78e967ee709c00b6af53643`, created 2026-08-15. Logs: `/workspace/qmx-ubuntu-ghcr-ci-image.log`, `/workspace/qmx-ubuntu-ci-image-provenance.json`, `/workspace/qmx-ubuntu-ci-os-release.log`. Actual `/etc/os-release` reports Ubuntu 24.04.4 LTS, `VERSION_ID=24.04`.

Further official cloud-server, Ubuntu Base and Canonical Core HEAD requests returned HTTP 403, exit 22. Exact endpoints and responses are retained in `/workspace/qmx-ubuntu-cloud-server-access.log`, `/workspace/qmx-ubuntu-canonical-base-access.log`, `/workspace/qmx-ubuntu-canonical-core-access.log`. The official Docker image manifest was fetched from `https://raw.githubusercontent.com/docker-library/official-images/master/library/ubuntu`; it pins current Noble amd64 source `4fde35ab880af6a7c67aa9802ea978137542dc35` on Launchpad. Anonymous `git ls-remote` of that source failed with CONNECT-tunnel 403, recorded in `/workspace/qmx-ubuntu-official-oci-source-ref.log`. The legacy GitHub image repository has no Noble tree at its current amd64 branch; it was not substituted for Ubuntu 24.04.

## Installation

CPython 3.14.7's standalone runtime is mounted read-only at `/opt/cpython`; the checksum-bound earlier bundle is mounted read-only at `/bundle`. The fresh destination is `/proof/candidate-offline`, backed by `/workspace/qmx-ubuntu-runtime/candidate-offline`, outside all source checkouts.

Initial invocation against an already-created destination refused before installation (`/workspace/qmx-ubuntu-replay-install.log`). Corrected fresh-destination online installation failed on container DNS (`/workspace/qmx-ubuntu-replay-install-corrected.log`). A host-network public-PyPI download also failed to find the pinned Alembic version (`/workspace/qmx-ubuntu-runtime-dependency-download.log`). Neither failure was hidden or repaired by changing dependency pins.

Twenty-four runtime wheel archives already cached by earlier installation were recovered only when their complete SHA256 matched an allowed hash in the bundle's existing `requirements.lock`. Inventory: `/workspace/qmx-runtime-wheelhouse/cached-wheel-inventory.json`. Only wheel filenames were reconstructed from their own WHEEL/METADATA; archive bytes and hashes were unchanged. The dual Python-tag tzdata wheel received an additional valid `py3-none-any` filename for CPython 3.14 compatibility. No factory dependency group was installed.

The successful invocation uses the pinned image, `--network none`, read-only bundle/runtime/wheelhouse mounts, `PIP_NO_INDEX=1`, `PIP_FIND_LINKS=/wheelhouse`, and `/opt/cpython/bin/python3.14 /bundle/install.py /proof/candidate-offline`. The installer retained `pip --require-hashes`, installed all 14 non-editable product distributions and reported no broken requirements. Actual trace: `/workspace/qmx-ubuntu-replay-offline-install.log`. The external wheelhouse is a setup input, not yet part of a final portable artifact inventory; final packaging must retain the exact dependency closure or genuinely prove fresh retrieval.

## Installed execution

`/workspace/qmx-ubuntu-runtime-smoke.py` ran with installed `/proof/candidate-offline/venv/bin/python -I` from `/tmp`, no source checkout mount and no networking. It verified all 14 distribution versions, installed origins for QMF/QML/QMB/QMN/QMA, mandatory bundled-pack file hashes, and absence of pytest/ruff/mypy/pyright/poethepoet/factory project from the product environment. Installed launcher start, running status, clean stop, stopped status, restart with a distinct PID using the same durable root, and final clean stop all passed. Trace: `/workspace/qmx-ubuntu-installed-lifecycle.log`.

Final source is still under repair. Repeat installation and required journeys against the final frozen reviewed SHA. Native Windows installation/recovery remains NOT RUN; native Ubuntu systemd/recovery and image security verification remain incomplete.
