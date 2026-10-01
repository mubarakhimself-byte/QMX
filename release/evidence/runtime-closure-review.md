# Independent runtime closure packaging review

Reviewed 2026-10-01 by the attended independent GPT 6.1 Sol review lane in `/workspace/QMX-release`. Governing inputs supplied by the coordinator: ratified main documentation `c3e8ec5`, backend `a0e8769`, UI `f6ffaddf`; mutable worktree HEAD at initial review `4cb55304`. Read `CLAUDE.md`, `docs/AGENTS.md`, the relevant packaging/runtime laws and stack, held implementation/tests, and release README. This report concerns ordinary packaging correctness and reproducibility. No implementation/test files, assertions, factory rules or acceptance checks were changed. No network, credentials, provider calls, push, merge, deployment or service activation occurred.

**Current 24-wheel positive closure: PASS. Strict validator review: FAIL, with two reproduced correctness findings below.** Neither finding changes the positive result for the actual 24 simple-tag, unique-distribution wheels reviewed. This is mutable held-source evidence, not final candidate acceptance.

## Held source identity

All six hashes matched before tests and after independent review:

| File | SHA256 |
| --- | --- |
| `tools/build_release.py` | `af750ddd0734b56723b24d7031851ce3a2a8e9a67e2da9e2bbbaa39a2611a2ae` |
| `release/install.py` | `84a53d7544455b3ccdeb23d11a62bdf83b317b3bb561dcdfbca9dd1f8b93a921` |
| `release/README.md` | `d5bf64a19369c64e991b6bf24bec32b20990606abd64600ea3a01fb6fd734cce` |
| `release/runtime_wheels.py` | `07ef6d269e5b3fe17992d952477401e67219dfc03a24dd554931dc9673e0bf74` |
| `tools/tests/test_release_install.py` | `1c7981ec31057586cc6332bb049772d323796b99637823496d944cf760bc3992` |
| `tools/tests/test_runtime_wheel_closure.py` | `ae13280263c2364e36acbea86a28efd7ecf973aed671263e436d3714282b0ffd` |

## Verification

| Check | Result | Evidence and limits |
| --- | --- | --- |
| Exact existing test command | PASS | `uv run --no-sync pytest -q -p no:cacheprovider tools/tests/test_release_install.py tools/tests/test_runtime_wheel_closure.py`: 22 passed in 0.24s. Positive installer subprocess/venv controls are mocked. |
| Local locked exports | PASS | Both actual `uv export --locked --offline --no-default-groups --no-emit-local --no-header` commands (root packages `qmb`, `qmn`, `qmf-calendar-forex`; nested `--project qmx-agents --all-packages`) completed. Their concatenation is byte-identical to the supplied published requirements lock. |
| Linux marker closure | PASS | Independent `packaging.Requirement` marker evaluation and pin/hash intersections equal helper output: exactly 24 active distributions. Windows-only colorama is excluded. |
| Actual wheel package/version/hash | PASS | Independent PEP 427 filename parsing, ZIP METADATA/WHEEL reading, and SHA256 checks match every package-specific allowed lock hash and inventory entry. Full row inventory follows. |
| Two local closure builds | PASS | `_runtime_closure` run twice against the actual local wheelhouse and published lock produced identical archive and inventory bytes. This verifies this helper, not the two complete final-candidate product builds. |
| Archive normalization | PASS | Exactly 24 sorted file members; each member has mtime/uid/gid 0, mode 0644, empty owner/group names, no PAX headers. Gzip timestamp bytes are zero. The source cache inventory and py2 tzdata alias are excluded. |
| Compatible runtime target | PASS | Linux x86_64 CPython 3.14.7 on glibc 2.41; inventory floor 2.34 equals maximum compatible wheel floor (cryptography). Each selected wheel has a compatible pure-Python, CPython 3.14, or abi3 manylinux tag. This checks declared tags, not binary ABI certification on all hosts. |
| Offline pip command and preflight ordering | PASS, bounded | Source review and existing controls confirm runtime pip uses `--isolated install --require-hashes --no-index --find-links` and a private verified extraction. Product wheels use isolated pip with explicit wheel paths and `--no-deps`; then isolated `pip check`. Both original and verified-snapshot manifests are validated before `venv.EnvBuilder.create`. Existing invalid-bundle controls assert no destination, venv, or pip call. Actual installation is a separate coordinator-owned lane. |
| Factory/runtime dependency separation | PASS | Export explicitly disables default groups and emits no local packages. No pytest, coverage, Hypothesis, ruff, pyright, poethepoet, mypy or uv-build factory distributions appear in the active closure. Actual TA-Lib 0.7.1 wheel METADATA requires `build` and `numpy`; actual build 1.5.0 METADATA requires `packaging >=24.0` and `pyproject_hooks`. Build and pyproject-hooks therefore legitimately belong to this runtime closure. |

Published lock: `/workspace/qmx-bundle-replay-candidate/requirements.lock`, SHA256 `1942a471a9f4cfeec8194b71af952eb78f68f22176de5782db6759b95d60f085`. Source wheelhouse: `/workspace/qmx-runtime-wheelhouse`. Independent structured positive result: `/workspace/qmx-runtime-closure-independent.json`.

Local closure artifact SHA256:

- `runtime-wheels.tar.gz`: `6075b48e2fd7ee5d6279438c01cac311911cb249d4cec0d8e8d4d19386f7b60f`
- `runtime-wheelhouse.json`: `400a94f6bf30054856c3d34a1a69ca687d3af698d49886976e2c333764cce499`

## Reproduced correctness findings

1. **P2 — duplicate inventory rows are silently accepted** (`release/runtime_wheels.py:392`, assignment at line 419). `wheels` is keyed by normalized distribution, but duplicate detection checks the filename against those keys. Appending an exact copy of the first real inventory row produces 25 input rows and 24 returned distributions without any exception. The archive remains a valid 24-wheel closure; the failure is that the validator does not enforce its promised one-row-per-wheel exact inventory. Check both seen filenames and normalized distribution keys before insertion. No supplied inventory has duplicates.

2. **P2 — compressed wheel tags lose compatible platforms** (`release/runtime_wheels.py:221`, intersection at line 267). Splitting the complete joined tag on `.` does not expand the Cartesian product of Python, ABI and platform fields. A valid fixture named `example-1.0.0-cp314-cp314-manylinux_2_34_x86_64.manylinux_2_17_x86_64.whl`, with both corresponding WHEEL tags, yields only the 2.34 tag. Independent `packaging.utils.parse_wheel_filename` yields both tags and minimum glibc 2.17. The helper thus overstates the minimum host requirement and may reject otherwise compatible distributions. Expand each compressed field independently. No selected actual wheel uses compressed filename tags, so actual closure floor 2.34 is still correct.

These are in-memory/local metadata correctness probes; no installed product or source file was modified. Both were sent to the coordinator. Direct delivery to `/root/data` was unavailable with an agent-thread-limit error; coordinator was asked to forward the findings.

## Actual verified closure

| Distribution | Version | Wheel filename | SHA256 | Declared compatible glibc floor |
| --- | --- | --- | --- | --- |
| `alembic` | `1.19.1` | `alembic-1.19.1-py3-none-any.whl` | `b39018cb3d9413a19cbd54cf3c02ad33998641f0538eb77413a488a21c3e14be` | `2.17` |
| `build` | `1.5.0` | `build-1.5.0-py3-none-any.whl` | `13f3eecb844759ab66efec90ca17639bbf14dc06cb2fdf37a9010322d9c50a6f` | `2.17` |
| `cffi` | `2.1.1` | `cffi-2.1.1-cp314-cp314-manylinux_2_17_x86_64.whl` | `b0431303acaea1089ad4b3e9ce4e6518193def1118d4073ca848635ee4ea2e96` | `2.17` |
| `click` | `8.4.2` | `click-8.4.2-py3-none-any.whl` | `e6f9f66136c816745b9d65817da91d61d957fb16e02e4dcd0552553c5a197b76` | `2.17` |
| `colorlog` | `6.12.0` | `colorlog-6.12.0-py3-none-any.whl` | `30d392604e9110045a2c2aeefc27d7a017abbab63f3a8aee594eac0801df784e` | `2.17` |
| `cryptography` | `50.0.1` | `cryptography-50.0.1-cp311-abi3-manylinux_2_34_x86_64.whl` | `51afcfceb15597cf2635068e4ac9a56b2abde622edde17f37d85fd7b5306497a` | `2.34` |
| `duckdb` | `1.5.5` | `duckdb-1.5.5-cp314-cp314-manylinux_2_26_x86_64.whl` | `fbf0f2d48b43c6c304d00463b463c27ead6c4b01c3c1816b750f728decf71afe` | `2.26` |
| `greenlet` | `3.5.5` | `greenlet-3.5.5-cp314-cp314-manylinux_2_24_x86_64.whl` | `182de51c6b572a705f2fafaab2e783bcf7d2760940229dfe73086cbae037af3e` | `2.24` |
| `mako` | `1.4.1` | `Mako-1.4.1-py3-none-any.whl` | `a359d9a94a541213958742b2698d0a7757bb83551767bc468a74b9905aba9617` | `2.17` |
| `markupsafe` | `3.0.3` | `MarkupSafe-3.0.3-cp314-cp314-manylinux_2_17_x86_64.whl` | `457a69a9577064c05a97c41f4e65148652db078a3a509039e64d3467b9e7ef97` | `2.17` |
| `numpy` | `2.5.2` | `numpy-2.5.2-cp314-cp314-manylinux_2_27_x86_64.whl` | `318b9a4c845dbea06708a29c84ee429cc3065048db34cdb799047643492050ee` | `2.27` |
| `optuna` | `4.9.0` | `optuna-4.9.0-py3-none-any.whl` | `f52f3be6148654850c92a5860d398fd88ec6b2c84ab68d9c3d07dcff02e7afee` | `2.17` |
| `packaging` | `26.3` | `packaging-26.3-py3-none-any.whl` | `d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c` | `2.17` |
| `prometheus-client` | `0.26.0` | `prometheus_client-0.26.0-py3-none-any.whl` | `fa93d06737aa02bacd05794768508bb97d2fbee28cb3bca04eaae92f0ca953d6` | `2.17` |
| `protobuf` | `7.36.0` | `protobuf-7.36.0-cp310-abi3-manylinux2014_x86_64.whl` | `70f5ec8eb0da81a44360c0dc0beac99a0d78071d21956a7076bae8bd2051841b` | `2.17` |
| `pyarrow` | `25.0.1` | `pyarrow-25.0.1-cp314-cp314-manylinux_2_28_x86_64.whl` | `9171748cdf796972d85a4b60157c279913e242992e350c90c7450182a9838b2a` | `2.28` |
| `pycparser` | `3.0` | `pycparser-3.0-py3-none-any.whl` | `b727414169a36b7d524c1c3e31839a521725078d7b2ff038656844266160a992` | `2.17` |
| `pyproject-hooks` | `1.2.0` | `pyproject_hooks-1.2.0-py3-none-any.whl` | `9e5c6bfa8dcc30091c74b0cf803c81fdd29d94f01992a7707bc97babb1141913` | `2.17` |
| `pyyaml` | `6.0.3` | `PyYAML-6.0.3-cp314-cp314-manylinux_2_17_x86_64.whl` | `c458b6d084f9b935061bc36216e8a69a7e293a2f1e68bf956dcd9e6cbcd143f5` | `2.17` |
| `sqlalchemy` | `2.0.52` | `SQLAlchemy-2.0.52-cp314-cp314-manylinux_2_17_x86_64.whl` | `812bae5138bfc0aa46fb0686da0fc7f581f68e2bbb05bc24c3713bebaedd1437` | `2.17` |
| `ta-lib` | `0.7.1` | `TA_Lib-0.7.1-cp314-cp314-manylinux_2_17_x86_64.whl` | `76cc90b7aecbdc5a3093c9e1ebc66517acbd7b372c6606483b9bcf3264b6f9bc` | `2.17` |
| `tqdm` | `4.70.0` | `tqdm-4.70.0-py3-none-any.whl` | `7f585706bfddbdebf89daac705b2dfcc16890130727d3197ca62c732b4310953` | `2.17` |
| `typing-extensions` | `4.16.0` | `typing_extensions-4.16.0-py3-none-any.whl` | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` | `2.17` |
| `tzdata` | `2025.2` | `tzdata-2025.2-py3-none-any.whl` | `1a403fada01ff9221ca8044d701868fa132215d84beb92242d9acd2147f667a8` | `2.17` |

## Pending lanes

- Final immutable source must resolve or explicitly track the two findings and rerun review against new source hashes; this held-source review does not approve later edits.
- Two complete builds and two installations from the same final candidate: NOT RUN by this reviewer; coordinator-owned pending acceptance work.
- Actual installer outside the checkout: NOT RUN by this reviewer; coordinator-owned separate evidence.
- Native Windows: NOT RUN. This optional closure supports Linux x86_64 CPython 3.14 only.
- Broader security verification: PENDING / unavailable in the separate lane as reported by the coordinator. This ordinary packaging review provides no complete security approval.
- Required factory/static/QA controls and final fail-closed release acceptance remain required. Linux local tests, successful packaging and installation do not fill missing execution, provider or security acceptance lanes.

## Corrected six-path independent re-review — PASS, bounded

Reviewed 2026-10-01 against the following frozen file hashes, verified both before and after execution. This append supersedes the two prior validator findings for this exact snapshot; the original report remains as historical evidence. No product/test edits or commits by reviewer.

| File | SHA256 |
| --- | --- |
| `tools/build_release.py` | `af750ddd0734b56723b24d7031851ce3a2a8e9a67e2da9e2bbbaa39a2611a2ae` |
| `release/install.py` | `84a53d7544455b3ccdeb23d11a62bdf83b317b3bb561dcdfbca9dd1f8b93a921` |
| `release/README.md` | `d5bf64a19369c64e991b6bf24bec32b20990606abd64600ea3a01fb6fd734cce` |
| `release/runtime_wheels.py` | `2332a76bddd610b1569b0adf29fb7125d6d3dd21ac442ea2aeb378caafc3b842` |
| `tools/tests/test_release_install.py` | `1c7981ec31057586cc6332bb049772d323796b99637823496d944cf760bc3992` |
| `tools/tests/test_runtime_wheel_closure.py` | `7e99c8976dc14cc569a336ee6cff20f8a5c77050791d4e0bf2a25d673cbde991` |

`uv run --no-sync pytest -q -p no:cacheprovider tools/tests/test_release_install.py tools/tests/test_runtime_wheel_closure.py`: **26 passed in 0.26s**. New controls cover compressed platform parsing, missing WHEEL tag refusal, duplicate filename and duplicate normalized distribution.

`PYTHONPATH=/workspace/QMX-release uv run --no-sync python /workspace/qmx-runtime-closure-corrected-independent.py`: **PASS**. Exact program and structured results are retained outside the repository in `/workspace/qmx-runtime-closure-corrected-independent.py` and `/workspace/qmx-runtime-closure-corrected-independent.json`. An initial invocation omitted PYTHONPATH and failed at importing the repository module; no review probe ran in that invocation.

- **Prior duplicate-inventory finding closed.** Source uses a separate filename set and checks the normalized distribution key before insertion. Actual 24-wheel inventory plus an exact duplicate refuses; the same distribution under a different filename and case/hyphen alias also refuses. Each was exercised through the actual installer function using a temporary copy of the labeled mixed installer fixture, with its outer inventory checksum correctly updated. Both raise the duplicate error before creating the destination and before any venv or subprocess call (zero calls). The venv/subprocess sentinels are explicit refuser controls, not real installation evidence.
- **Prior compressed-tag finding closed.** Each filename tag field expands with Cartesian product. Every expanded filename tag must appear exactly in WHEEL; extra WHEEL compatibility aliases are allowed. The valid compressed 2.34/2.17 platform fixture matches independent `packaging.utils.parse_wheel_filename`, and actual `_runtime_closure` now declares its correct minimum glibc 2.17. Existing SQLAlchemy/TZData WHEEL aliases remain accepted.
- **Actual 24-wheel closure retained.** Two fresh local `_runtime_closure` outputs against `/workspace/qmx-runtime-wheelhouse` and the published requirements lock are byte-identical. Each actual wheel is independently filename/METADATA/version/hash checked; exact active distribution inventory remains 24. Both artifact hashes match the initial successful real-wheel review: archive `6075b48e2fd7ee5d6279438c01cac311911cb249d4cec0d8e8d4d19386f7b60f`, inventory `400a94f6bf30054856c3d34a1a69ca687d3af698d49886976e2c333764cce499`. The actual supported target remains Linux x86_64 CPython 3.14, glibc floor 2.34.

**No remaining finding in this bounded correction review.** This approves only the listed six-path packaging correction and the observed closure/helper behavior. The coordinator-owned offline Ubuntu installation combines corrected helper with old `1c4c73b1` product wheels; it is an installer harness, not final-candidate evidence. Full two-build/two-install reproducibility from one final immutable SHA, native Windows, broader security, all required factory/static/QA and release acceptance lanes remain pending.
