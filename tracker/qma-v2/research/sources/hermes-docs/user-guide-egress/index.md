<!--
source_url: https://hermes-agent.nousresearch.com/docs/user-guide/egress
source_file: https://github.com/NousResearch/hermes-agent/blob/6f46e2b98cd986c795ed0095a13b570f41cbf2c0/website/docs/user-guide/egress/index.md
fetched: 2026-10-18
fetched_by: research agent for study 37d (raw markdown from the docs source at the pinned commit)
-->

---
title: Egress proxy
sidebar_position: 1
---

# Egress proxy

Optional outbound credential-injection firewall for remote terminal sandboxes. The sandbox only ever holds opaque proxy tokens; real API keys never leave the host.

- [iron-proxy](./iron-proxy) — single-binary TLS-intercepting proxy from [ironsh/iron-proxy](https://github.com/ironsh/iron-proxy), lazy-installed and managed by `hermes egress`.
