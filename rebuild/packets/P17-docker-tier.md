# P17: Docker tier for nodes (T2)

## Goal
The same app definition runs as a Docker container on Linux servers, such as trading nodes in Singapore or New York, with enforced network rules.

## Read first
`rebuild/DESIGN.md` §7.5–7.7; `rebuild/research/research-memory-storage.md` §E and §C1 (Litestream on Linux).

## Build
- **Image builder:** from an app definition (`app.toml` + code + `uv.lock`), produce a pinned base image with `uv sync --frozen`, tagged with the definition hash.
- **Node supervisor mode:** start, stop and health-check the container.
  - The volume is a bind mount of `/apps/<id>`.
  - Network: default deny, plus the declared allow-list, using a Docker network with an egress proxy or iptables. Document which you use.
  - Logs, heartbeat and metrics stream to `qmx-control` on the node.
- **Optional Litestream sidecar:** for apps that need second-level recovery (order and fill records), using the settings in research §C1.
- **Remote access:** `qmx-control` on the node, reached over Tailscale with a per-node token.

## Tests
- builds and runs the example app in Docker (CI on Ubuntu)
- a blocked egress host is refused
- restarting the container keeps data
- restore from backup onto a fresh node
