# Open decisions (five; the design proceeds on the recommendation)

Closed on 2026-10-16 night and folded into the spine: **OPEN-1** home (PC now, server later by config, AD-19; ruling 56); **OPEN-6** auto-merge (nothing waits for him, AD-18; ruling 57); the old **OPEN-5** transport (tailnet-first with per-run tokens, AD-11; file 32).

| # | Decision | Recommendation | If ruled the other way |
| --- | --- | --- | --- |
| OPEN-2 | Governed trading records (bots, pods, bindings, results): does the Library *mirror* the QMF registry room or *replace* it? | **Mirror.** Verbatim copy under the same fp1 (AD-2); the registry room on the node stays the governed evidence copy with world isolation and the human-signed promotion path (DEC-0188); an importer keeps them in sync; divergence is a collision alarm. | Replace: CT-09 world rooms and the node's trust boundary are re-derived; TN-3/TN-20 change. Large doc blast radius, no functional gain. |
| OPEN-3 | Encrypt the bucket copy of every Library object? | **Yes, one rule**: rclone's crypt backend keyed from the escrowed `qmx/backup-payload-key`; the server replica stays plaintext (it is his machine). | Plaintext for ungoverned kinds: two code paths and a per-kind decision; saves CPU, not money. |
| OPEN-4 | Ship dense (semantic) retrieval in v1? | **Yes, optional and rebuildable**: sqlite-vec 0.1.9 plus a small local embedding model behind a settings flag, re-ordering only (AD-8). | Text + graph only first; add later with no schema change. |
| OPEN-5 | Open a public HTTPS listener on the Library Hub for providers that cannot join the tailnet (E2B Cloud, Modal)? | **Off by default.** Tailnet-first covers the PC, his server, Amp runners and orbs (OIDC workload identity). Enable the public listener per provider in Settings only when he actually buys burst compute there; run tokens are required either way. | On from day one: a public surface to patch and watch for a provider he has not paid for. |
| OPEN-7 | Do **copilot-chat** merges of governed kinds (`unit`, `bot`, `pod`, `workflow`, `mini-app`, `skill`) into `main` still ask him (MANAGE), now that workflows never wait? | **Yes, keep the ask in chats.** He is present in a chat, the harness already asks for MANAGE, and ruling 57 is about unattended workflows. A workflow he starts from the chat lands under its own `publish` rule. | Extend ruling 57 to chats: `library_merge` becomes DOMAIN_WRITE for every kind; one harness effect-table row changes; nothing else. |

Recorded in `.memlog.md` as `question` entries.
