# Reviewer gate for the 2026-10-18 amendment (after the first build run)

Run inline and in sequence by the amending architect: the brief forbade sub-agents, so this is the skill's no-sub-agent fallback. It is not an independent review; the Fable review of the stacked PRs that he asked for after TP4 is the independent read.

## Lint

`lint_spine.py --workspace .`: 0 findings after every batch (placeholders, AD ids, Binds/Prevents/Rule, Stack pins). AD-1..AD-35 keep their ids; AD-36 and AD-37 are appended at the end.

## Rubric walker (good-spine checklist)

- Divergence points for the level below: every SECURITY and SPEC-GAP row of `methodology/34` maps to an AD rule (18 SECURITY rows, 26 SPEC-GAP rows; table in `methodology/35` §3). Pass.
- Enforceable rules: each new rule names its check (E33-E41) or its lint; the scan (AD-36) and redaction (AD-37) each name one module and one seam. Pass.
- Deferred: port kinds beyond `data`, a `switch` kind, the later packets, a money-scan allow-list and a Contabo host tier are deferred with a reason; none lets two units diverge on v1 documents. Pass.
- Brownfield ratification: port names, the five-value effect enum, the local worker shape, the loop ports and the import graph are ratified from `engine/tp4` rather than reinvented. Where the built code is wrong (zone location, interpreter, lint scope, CLI live mode, runaway defaults, Fable row, test model) the spine says so and names the backlog row. Pass.
- Operational envelope: `zones_root` per host (PC and Contabo), Docker-off behaviour, the start-up sweep, the probe that can switch `host_confined` off. Pass.

## Verification lens (named technology checked, not asserted)

| Claim | Label | Source |
| --- | --- | --- |
| AppContainer isolates credentials, files, network, processes and windows | retrieved | learn.microsoft.com, "AppContainer isolation" |
| `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` terminates every process in the job when the last handle closes; `JOB_OBJECT_LIMIT_ACTIVE_PROCESS` caps active processes | retrieved | learn.microsoft.com, `JOBOBJECT_BASIC_LIMIT_INFORMATION` |
| The PC is Windows 11 Home, so no Windows Sandbox | retrieved | this session's environment block |
| `descriptors.name_money_act` / `description_money_act` behaviour on the sample names and sentences | retrieved | scratchpad probe over `engine/tp4` `qma-core` |
| CredRead of the user's generic credentials fails inside an AppContainer; loopback is blocked by default | remembered | not verified; live check E33 decides, and a failing row switches `host_confined` off |
| `sys.addaudithook` exists and cannot be removed from Python code | remembered (PEP 578) | a tripwire only; the OS boundary is the guarantee |
| `docker run --init` | remembered | standard Docker flag |

No new library is bound: Win32 calls go through `ctypes` (stdlib); the Stack table is unchanged.

## Adversary (two units that obey every AD yet clash)

Found and fixed in the spine:

1. "Every file a script reads is shipped" cannot be checked, so two builders would pick different file sets. Fixed: provenance is "every `.py` file in the folder is byte-identical to the manifest", and `exec`, `eval`, `compile`, `runpy`, `pickle`, `marshal` and `shelve` are refused in `host_confined` scripts so a data file cannot smuggle code (AD-24, AD-36).
2. Redaction before commit could make a live run (in-memory value) and its replay (stored value) diverge. Fixed: the core reads outputs only from committed events, and output hashes are taken after redaction (AD-37).
3. A Job object that allows breakaway would let a grandchild survive the engine. Fixed: no breakaway (AD-24).
4. "Live runs start only by a user or the scheduler" left `subworkflow` children of live runs undefined. Fixed: a child inherits its parent's mode (AD-11).

Open, surfaced to him:

5. AD-24's fallback for agent chats (an ask the engine rejects) is likely not to fire today: the EP14 resumed chat ran `Bash` without an ask [retrieved B-69, B-70]. If E35 confirms that, agent nodes on the PC are held until H2 is granted. Surfaced as OPEN-DECISIONS D, with H2 first in HG3.
6. `engine_view` reads ride on the `library` node kind, whose executor is not built yet; RV's `week.py` keeps its current reads until that packet lands (SOLUTION-DESIGN §25).

## Ad-hoc security lens (money and logins)

- Plan login, keyring (broker, control token, GPT sign-in) and loopback: three independent guards for shipped scripts (zone placement, AppContainer, script runtime without the libraries), the container for everything else. A failure of the AppContainer probe degrades to "everything in a container", never to a bare host process.
- Money: the scan uses the harness gate's own matcher, so the engine and the harness cannot disagree; broker refs are refused by allow-list and deny-list in three places (lint, Settings validator, resolver); the vault never replicates broker credentials (AD-28, unchanged); Contabo never holds one (AD-25, unchanged).
- Residual risk accepted and written down: prose false positives fail closed (rewording fixes them); a shipped script with `network: true` can still send what it legitimately read to the internet, which is why shipped scripts read only public data and hold no credential unless a tool row allows it.
