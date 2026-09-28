# Unattended Reticle gate

Reticle's dev-only SDK connects the app to a local daemon over WebSocket. The
factory reaches that same daemon over MCP's HTTP/SSE transport. A POST is only
an acknowledgement; the matching JSON-RPC result arrives on the SSE stream.
The gate uses an owned headless lease so an operator's tab and browser focus
are unnecessary. It explicitly releases that lease on both success and failure.

This host pins the browser SDK and Vite plugin to 2.14.0. Use the matching
`@reticlehq/server@2.14.0` daemon and Node 22.12.0 / pnpm 10.18.3. The checker
refuses version skew. Do not mix an unpinned `npx ...@latest` with pinned SDKs.
`npx @reticlehq/server@2.14.0 doctor` diagnoses wiring; its exit code alone is
not proof of a connected app or a successful journey.

For initial setup, run the pinned `init` from `apps/qmx-ui`, then start the
app's own `pnpm dev` script. A changed Vite config requires a server restart.
`.reticle.json`, the plugin and saved flows all use the stable `qmx-ui`
project ID. The app must serve its full candidate SHA. If another checkout
occupies 5173, start this checkout with `pnpm dev --port <free-port>` and pass
that exact URL; do not accept an unrelated server or terminate its owner.

The normal gate is `pnpm test:reticle` (or the factory's `ui-reticle` profile).
It runs the checked-in Node launcher, not `npx verify`. The latter starts a
separate engine and conflicts with an already-running MCP daemon. No package
download or agent reasoning occurs in the verification loop.

Environment:

- `RETICLE_VERIFY_URL`: this candidate's running app URL (default
  `http://127.0.0.1:5173/`).
- `RETICLE_DAEMON_URL`: local daemon URL (default config port, 4400).
- `QMX_CANDIDATE_SHA`: full SHA supplied by the factory; standalone checks use
  the current Git HEAD.
- `RETICLE_RESULT_FILE`: retained JSON output; the factory assigns a path in
  its unit log directory. Standalone default: `.reticle/latest-result.json`.
- `RETICLE_TOTAL_TIMEOUT_MS`: may shorten the 60-second budget, never extend it.
- `RETICLE_CALL_TIMEOUT_MS`: 15 seconds by default, capped at 20 seconds.

Each assertion waits at most five seconds. Lease cleanup gets at most three
seconds. The parent kills its own worker after the total budget plus 1.5 seconds
even if the worker's event loop hangs. The quality profile has a 65-second outer
deadline. It records failures rather than throwing away the evidence. It never
terminates the shared daemon, someone else's server or someone else's lease.
If a acquire request is lost before its lease ID arrives, immediate release
cannot be confirmed; the daemon's lease TTL reclaims it. No success is reported.

The current saved flow uses testid anchors and starts at `/`. Unsupported
recorded forms or missing consequence predicates fail explicitly. It verifies
the loading skeleton and the app's `qmx-bootstrap.chromeState`, then asserts
the candidate SHA from the app and a clean console. Only real
`reticle_act_and_wait` / `reticle_assert` results of `verified: yes` pass.
The dev-only store receives the component's actual state transitions and is
registered with a subscription, so Reticle can observe state changes as well
as read the current value. Production excludes the instrumentation.

Exit 0 means the live check passed and lease release was confirmed. Exit 1 is
a Reticle `no`; exit 2 is incomplete/unknown/infrastructure failure. A previous
success is erased before starting. A caller-written yes sidecar is ignored;
user-facing runtime checks are rerun rather than accepted from cache.

A timeout, unavailable daemon, expired/unconnected lease, version mismatch or
unknown verdict stops the unit with retained evidence. It must not launch an
application repair loop or repeatedly wait on the same check. Playwright is a
separate useful check; it does not turn an unproved Reticle gate into success.

References: [architecture](https://docs.reticle.sh/architecture),
[HTTP transport](https://docs.reticle.sh/http-transport),
[leases](https://docs.reticle.sh/multi-agent-testing),
[troubleshooting](https://docs.reticle.sh/troubleshooting),
[predicates](https://docs.reticle.sh/predicates).
