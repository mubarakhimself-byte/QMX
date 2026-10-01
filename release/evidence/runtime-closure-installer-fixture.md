# Offline installer mechanics: mixed intermediate fixture

PASS within this fixture only. This is not a release candidate: product wheels are from `1c4c73b1e51e9194464601830e7543ecd1108b6d`, while installer and runtime closure helper are held later source. No final acceptance or complete source identity is implied.

The actual pinned Ubuntu 24.04.4 community CI image `sha256:62d572b92f9f32d3427b6d220ad1f9dca9c7b6ffad37d295425037dbff78abaf` ran CPython 3.14.7 with `--network none`, read-only bundle/runtime mounts, no source checkout mount, and a new destination `/workspace/qmx-ubuntu-runtime/runtime-closure-fixture` outside all checkouts. No external wheelhouse or pip environment override was supplied.

Commands were `DOCKER_CONFIG=/workspace/qmx-docker-anonymous-config docker run --rm --network none` with mounts for `/opt/cpython`, `/bundle`, `/proof`, invoking `/opt/cpython/bin/python3.14 -I /bundle/install.py /proof/runtime-closure-fixture`, then installed `/proof/runtime-closure-fixture/venv/bin/python -I /checks/runtime-smoke.py` with the driver mounted read-only. Full traces: `/workspace/qmx-runtime-closure-fixture-install.log`, `/workspace/qmx-runtime-closure-fixture-lifecycle.log`. Driver: `/workspace/qmx-runtime-closure-fixture-smoke.py`. Component proof: `/workspace/qmx-runtime-closure-fixture-inputs.json`.

Actual installer used its bundled 24 exact hash-locked runtime wheels, installed all 14 non-editable product distributions, and passed `pip check`. Installed-only origins and all 40 mandatory pack files matched inventory; no factory tools were installed. Actual launcher start/status/stop/stopped/restart with a distinct PID on the same durable root/final stop all returned zero. The fixture acceptance manifest explicitly marks the mixed scope and has empty acceptance checks.

Component hashes:

- `install.py`: `84a53d7544455b3ccdeb23d11a62bdf83b317b3bb561dcdfbca9dd1f8b93a921`
- `runtime_wheels.py`: `07ef6d269e5b3fe17992d952477401e67219dfc03a24dd554931dc9673e0bf74`
- `runtime-wheels.tar.gz`: `6075b48e2fd7ee5d6279438c01cac311911cb249d4cec0d8e8d4d19386f7b60f`
- `runtime-wheelhouse.json`: `400a94f6bf30054856c3d34a1a69ca687d3af698d49886976e2c333764cce499`

Strict validator review remains FAIL pending duplicate-inventory and compressed-tag corrections (`runtime-closure-review.md`); neither affects these actual 24 wheels. Repeat actual installation after corrections and again with complete final reviewed product source. Native Windows, native recovery, provider connectivity and image/security verification remain pending.
