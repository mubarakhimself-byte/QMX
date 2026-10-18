# Reviewer gate, unlock pass (ruling 118), 2026-10-18

Run inline by the architect (no sub-agents allowed in this pass). Full reasoning in `research/methodology/43-whole-app-unlocked.md` §12.

**Verdict:** pass after one fix.

| Lens | Result |
| --- | --- |
| `lint_spine.py` (engine, Library, Lab) | 0 findings each |
| Rubric walker | AD-52 to AD-60 each carry Binds, Prevents and an enforceable Rule; each closes a divergence two builders would otherwise create; the operational envelope (one process per machine, `--role node` on Contabo, desktop supervision) is covered. **Fixed:** AD-52 overstated direct `settings.toml` readers (eleven claimed; the code shows `qma.boot` by design and `qmx_broker/service.py:117` only). |
| Currency (configured reviewer 1) | no new library bound; SDK facts read from claude-agent-sdk 0.2.166 as installed (`settings` path, `toggle_mcp_server`, `fork_session`, `AgentDefinition.model` and `effort`, `PermissionMode`); unproven behaviour is a named probe (P-PERM, P-PL, P-TG, P-SET) |
| Adversary (configured reviewer 2) | seven clash pairs checked and closed: pack tools served twice (AD-55 strips `.mcp.json`), two home owners (AD-35), two chat-slot counters (AD-58), a policy allow lifting a floor row (AD-53 order, AD-54), two pass minters (AD-56), two app schedulers (AD-57), pack hooks on engine chats (AD-55, AD-34) |

**Open after the gate (owners named in 43 §12):** Library and Lab HLD/LLD not re-projected; HARDENING-PLAN and DELETION-PLAN to be edited by the planning lead from 43 §10; probes not run (build-time gates).
