---
title: Connect a server, GPU or key-based compute
type: grilling
mode: AFK
status: closed
blocked_by: [connect-dialog]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

What are the steps of the compute kinds, built on `qmx node setup` and the place rows that exist?

## Resolution

**A server (Contabo, Hetzner, any Linux machine he pays for):**

- **His cards:**
  - Choose and pay for a server.
  - Give its address.
  - Let it join his Tailscale network. A one-off auth key made for that machine lets it join without a browser (`sources/tailscale-auth-keys.md`).
  - Type the server's password in the terminal QMX opens, never into chat.
  - Approve the firewall step.
- **QMX's steps,** each given a check:
  - the existing `qmx node setup` sequence (`QX/node.py:616-652`, today one blocking command): bootstrap, recovery script and its conf, firewall close with the fresh-SSH check, host install, pairing, key copy;
  - then the place row with `can = ["run", "keep"]`;
  - then the built status ladder `available → configured → authorized → reachable → healthy`, giving `PK/qmx-engine/src/qmx_engine/triggers/preflight.py:231` its first caller;
  - then a one-node smoke test, run by the server's own engine;
  - then `qmx-recover status` in plain words (R139).
- **Then his choices, each on its own screen:** whether deep logs go there, whether it is a storage, and which datasets it keeps (design F1, D4).

**Key-based compute (Modal, E2B, and later GPU providers):**

- His card: type the key through the write-only key route.
- QMX's steps: one provider test call, then the place row (`provider = modal|e2b`, keys in the vault, `PK/qmx-remote/src/qmx_remote/models.py:100-121`).
- A GPU on Modal is the same kind with a GPU type. No AWS, RunPod or Colab adapter exists (machines #2); each new provider is a new kind on the same dialog, not new machinery.

**Never:** a server step on the first start (R142), or a server as the main copy (R136).

**Not here:** making PC-started work actually run on a named place (machines #14, "needs a ruling"). That is engine dispatch for the stand-in round, so this map lists it as out of scope. The connect dialog proves the place answers and runs a test with its own engine.

## Evidence

His words: "whether it's compute, storage, GPU, bloody hell, anything, but it sets itself up" (`words:219`). R144, R145, R139. Design F1 (`design:405-412`). Machines gap map rows 1 to 7 (`align:` A5).
