# Bounded daemon startup and local-control quality repair

Starting source: `8873a4a5774c858081f145e7d1c24866fc6a96e4`. This is a local
implementation-evidence record, not a new architecture ruling or release acceptance.

Reuse `COMP-QMA-DAEMON` and its existing process/local-control boundaries. The
component inventory is `docs/architecture/dependencies.yaml`; governing behavior
is in `docs/components/qma-daemon.md`, CT-04, ADR-0026 and SCN-0030. DEC-0494/0503
keep host control token gated and recovery stopped, OS-owned, single-principal.
No new component, contract, registry default, workflow runtime or provider is added.
65535 is the socket protocol limit rather than a chosen operational setting.

The adversarial red run produced 11 failures and 16 passes. Concrete defects:

- A listener port above 65535 passed composition, created durable bootstrap state
  and escaped as `OverflowError`. Validate the full socket range before opening
  the persistence substrate.
- Invalid UTF-8 local-control files escaped the public result boundary. Return
  typed storage refusals and preserve the corrupt bytes for explicit stopped
  recovery. Do not silently remint an established principal or held token.
- An OS-owned bind file accepted a remote host or impossible port, allowing a
  public local-control client to transmit its token to the corrupt address.
  Validate loopback/range/reserved-port constraints on both read and write, before
  opening a socket; an invalid write preserves the previous valid address.
- An interrupt after real listener binding ran synchronous cleanup after
  `asyncio.run` had destroyed the Windows event loop. Close both listeners and
  persistence asynchronously while the loop still exists, retaining final
  idempotent synchronous cleanup.

The tests execute `python -m qma.daemon` with this checkout's source imports and
exercise structured configuration refusals, denied OS reads, occupied-port
rollback, cross-process writer contention, authenticated stop/restart, corrupted
control-file recovery, and stale-token denial. A lost-token recovery attempt while
live must leave the token absent and the writer bytes unchanged. Durable readback
proves exactly one operator and one recovery event. The interrupt fault is injected
at the serve boundary after real socket binds; both sockets must be closed and the
same root must compose again. Corrupt remote binds use a network sentinel: any
socket opening fails the test. These tests perform no external service calls.

Initial process tests exposed a fixture mistake: a Windows venv launcher PID may
be a redirector. Read status PID against the actual writer-lock PID. Fixture
cleanup first tries authenticated stop; forced cleanup validates exact owned
root/machine/boot identity before terminating the actual fixture child.

The first measured focused run passed all 27 behavioral tests and measured daemon
`__main__.py` at 100% line-and-branch coverage. Its aggregate coverage was only
26.39%, and the unchanged 80% gate correctly failed. Final tests include three
legal loopback roundtrips and the strengthened live-lost-token negative. Consult
the external D-local delivery acceptance record for final-SHA complete-QMA results.
Focused results never substitute for aggregate or per-package acceptance.

The old D-local environment omitted the installed coverage subprocess `.pth`
startup hook while borrowing dependency directories. The quality environment
installs that same hook after its own-source path manifest. This repairs child
measurement without changing coverage configuration, source inventory, package
floors, exclusions or tests. Coverage changes include this measurement correction;
they must not all be attributed to new behavioral tests.

Documentation/release scope: strict documentation validation reproduced 25
inherited errors (23 stale verification stamps and two provisional documents).
Ledger, registry, citations and inventory validators pass with their existing
warnings. Current source evidence does not justify restamping unrelated component
or operational scenarios or promoting provisional material. Historical fixed-SHA
claims in the corpus/release records remain historical. Existing release,
coverage-inventory, isolated-build-validator and factory-validator regression
suites passed 237 tests with one Windows symlink-permission skip. That verifies
validator behavior, not fresh installation, actual isolated builds, artifact
inventories, external connectivity, UI acceptance, deployment or a whole release.

Required static checks also found an inherited ambient entropy finding at
`qmb/src/qmb/host/_windows_research.py:308` (`uuid.uuid4`). Its source is unchanged
from the starting pin; correcting that separate filesystem lifecycle contract is
outside this bounded daemon repair. No scanner is weakened. Final delivery records
all failed, skipped and unrun stages, source hashes and independent review scope.
