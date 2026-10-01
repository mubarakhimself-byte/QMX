# Installer preflight evidence

The installer now checks the acceptance manifest shape and SHA-256 values,
requires all declared product artifact roles and all 14 product wheel
distributions, rejects unlisted wheels, checks wheel archive structure and
METADATA name/version, validates a pinned hashed requirements lock and pack
inventory, and inspects the UI tar paths and entry types before creating a
virtual environment. Archive extraction reuses the checksum-verified bytes.

Positive installation-flow coverage is explicitly mocked: tests replace the
venv builder and pip subprocess. They verify argument construction and output
placement only; they do not claim an installation, security review, or release
acceptance PASS. CPython 3.14 remains the required installer interpreter.

```text
uv run --no-sync pytest -q -p no:cacheprovider tools/tests/test_release_install.py
8 passed in 0.18s

uv run --no-sync ruff check release/install.py tools/tests/test_release_install.py
All checks passed!
```

Additional independent format controls used the actual root and nested lock
exports emitted by the current `uv export` commands and seven existing
uv-built wheels:

```text
uv export --locked --no-default-groups --no-emit-local --no-header --package qmb --package qmn --package qmf-calendar-forex
uv export --locked --project qmx-agents --all-packages --no-default-groups --no-emit-local --no-header
_validate_lock(root-export): valid
_validate_lock(nested-export): valid
_validate_wheels(/tmp/qma-wheel-check): 7 genuine wheels passed
```

The bundle tests verify missing distributions/artifact bindings, malformed
digests, modified wheel bytes, wheel METADATA mismatch, unhashed/unsupported
lock input, an unsafe `../` UI archive path, and unlisted wheels all refuse
before venv or pip invocation. These are preflight correctness controls, not a
security certification.
