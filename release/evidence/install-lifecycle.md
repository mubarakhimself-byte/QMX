# Non-editable bundle and process lifecycle evidence

These are intermediate versions, not final release acceptance. No external
provider calls, credentials, or trading were used. Host: Debian 13 x86-64,
CPython 3.14.7; native Windows and Ubuntu 24.04 remain pending.

| Check | Commit | Result | Evidence |
| --- | --- | --- | --- |
| Full immutable-snapshot build: 14 wheels, 14 sdists, UI and support artifacts | ad24e8eb42ea0e44669d9ef67683ec8a086c1026 | PASS | /workspace/qmx-bundle-provisional-build.log |
| Independent second build: all 35 artifacts byte identical | ad24e8eb42ea0e44669d9ef67683ec8a086c1026 | PASS | /workspace/qmx-reproducibility-provisional.json |
| Real hash-locked non-editable installation and pip check | ad24e8eb42ea0e44669d9ef67683ec8a086c1026 | PASS | /workspace/qmx-installed-bundle-provisional.log |
| First installed process stop/status recovery | ad24e8eb42ea0e44669d9ef67683ec8a086c1026 | FAIL, repaired later | /workspace/qmx-bundle-lifecycle-smoke.py; /workspace/qmx-provisional-install-evidence.json |
| Rebuild after lifecycle fix | 480d3bf87e8502feac4d0a2393a9f4c119c583e0 | PASS | /workspace/qmx-bundle-lifecycle-build.log |
| Real locked installation of rebuilt bundle | 480d3bf87e8502feac4d0a2393a9f4c119c583e0 | PASS | /workspace/qmx-lifecycle-install.log |
| Installed launcher start, qmb running status, clean stop, truthful stopped status, restart same root, final clean stop | 480d3bf87e8502feac4d0a2393a9f4c119c583e0 | PASS | /workspace/qmx-lifecycle-candidate-smoke.py; /workspace/qmx-lifecycle-candidate-smoke.log |
| Full acceptance gate on provisional bundle | ad24e8eb42ea0e44669d9ef67683ec8a086c1026 | FAIL, mandatory lanes absent | /workspace/qmx-provisional-acceptance-gate.log |

Actual lifecycle commands ran from `/workspace`, outside all source checkouts,
using `/workspace/qmx-installed-lifecycle-candidate/venv/bin/python` with the
installed `launcher.py`, and the installed `venv/bin/qmb host status/stop`.
The reused state root was `/tmp/qmx-bundle-lifecycle-4t6euaer`; distinct started
processes 30283 and 30377 both stopped with exit 0. This proves host process
lifecycle only, not session reconnect, job cancellation or economic execution.

Ubuntu image setup is BLOCKED: `docker pull ubuntu:24.04` returned the Docker
Hub unauthenticated rate-limit error; the public ECR Ubuntu mirror returned
Forbidden. Logs `/workspace/qmx-ubuntu-image.log` and
`/workspace/qmx-ubuntu-mirror-image.log`. No account authentication attempted.
Native Windows installation and recovery are NOT RUN. A final immutable
build, repeated build, install and all acceptance lanes must target the same
final candidate commit after continuing implementation and review.
