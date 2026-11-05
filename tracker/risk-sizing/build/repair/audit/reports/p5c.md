VERDICT: REPAIR

## 1. What this part is for

This part starts QMX and connects a trading node. The host (`host.py`, `first_start.py`) opens the folder, makes the keys folder private, starts the apps listed for that folder, and proves the machine's clock on every heartbeat. The connect dialog's node kinds (`connect_node.py`) set up the node and the MIS on This PC or on a server, one rerunnable step at a time, with cards for the few things only he can do. Each server gets its own pass key, so a server can never speak as him. `tools/first_real_start.py` is the one command he runs after landing: it walks the setup, his demo sign-in, one test trade, the passport, the deploy and the journal rows, and prints PASS or FAIL per fact.

## 2. Counts

Files opened 21 of 21. Lines read about 13,450 (10,532 product, 2,925 test, the four `diff` files by diff). Test functions read 72. Hollow or deletable 2. Findings: must 1, should 4, leave 5. Lines that could go: 34. Plain version guess: about 9,500 of 10,532 product lines (my guess; most of these lines are old code the build kept, and I name no layer worth cutting).

## 3. Paths traced

**A. First real start, from his command to a trading node.** `main`, then `landed_refusal`, the bearer, `set_up`, the connect kind, the sign route, the key route, node `status`, sign-in, `bind`, `self_test`, `passport`, `/api/units/promote`, `deployments`, `/api/data/card`. Eight of the nine steps hold up, and the rehearsal log on a real host shows them working. The deploy step does not hold on a real folder. The dummy is a draft and only the judge can make it tested, so his click is refused (p5c-1). The rehearsal hides this by writing the G report and the judge's move as labelled fixture rows. The deploy line also passes at "compiling", before the node has decided (p5c-2). The landed check is sound, but it is tied to `origin/main` (p5c-4).

**B. Host start and restart.** `serve_forever`, `single_instance`, `owner_only`, `control_for`, the node link, `enable_apps`, `enable_first_party`. The vault is made private before any key is written, and a link stops the start with one line (tested). One failing app ends the start loop, so a broken QMB keeps the practice node down (p5c-3).

**C. A pass between machines.** `pair_place`, `pass_key_script`, `held_keys`, `mint_host_pass`, `verify_host_pass`, `speaks_for`, the host route, `forward_router`, the venue routes. Sound. Every minter and verifier I found takes per-host keys. A server's key cannot claim This PC or `operator` anywhere.

**D. A server setup.** `on_a_server`, `ServerApps`, keys window, sign window, chrony, OpenObserve, install, enable, passport, row. The logic is sound against a simulated host. Secrets stay on the server and stay off command lines. Nothing installs OpenObserve's programs (p5c-5). No real server has run it, which the plan holds until G-SERVER.

## 4. Sections

| Id | Origin | Verdict | Blast-radius fact | Held, level | Added: keep, fold, cut |
| --- | --- | --- | --- | --- | --- |
| C-01 | original | met | An older reader loads a newer heartbeat row | Held, 4: `read_row` loaded a row with unknown fields at both depths (`proof_start.py`); `test_clock_probe.py` passed | - |
| C-11 | original | met | The shipped connect kinds still register and run | Held, 4 for register (`test_connect.py` kinds node passed); run only by reading, see section 11 | - |
| C-32 | added | partly (two readers still read by path, p5c-6) | Every key the host reads today still reads | Held, 4 for `vault_key` and `vault_secrets` (`test_vault_acl.py` passed); 2 for `HomeSecret` and `HomeKeyStore`, which do not use the new reader | keep: without it a second Windows user can read the key that signs run passes |
| C-17 | original | partly (p5c-5; real server waits for G-SERVER) | C9: a pass minted on This PC parses at a paired server, refused unpaired | Held, 4 for host passes (`test_host_pass_keys.py`); 2 for run passes, see section 11 | - |
| C-28 | added | met | A pass from This PC verifies at a server; a pass minted on a server cannot claim This PC | Held, 4: `test_host_pass_keys.py` passed, covering operator, `host:pc`, another host, replay, old key | keep: it closes a real forgery between his machines, in small code |
| C-14 | original | partly (p5c-1, p5c-2, p5c-4) | Real mode refuses a checkout lacking main's commit | Held, 4: `test_first_real_start.py`, 14 passed, on real throwaway git repositories | - |

Departures I did not count as findings. The "button" in C-01 is a doctor line naming the step, because no UI code may be written. The block-source line-ending pin in C-17 was not needed: `test_the_dummy_compiles_to_one_fingerprint_from_a_windows_or_a_linux_checkout` passed. Deployment files through the hub while This PC is primary are ruled to C-19 (TR:12).

## 5. What is fine

- **The waiting-step runner.** `on_runner` is small and correct: a waiting step blocks only what names it, and every other step runs.
- **The keys step on This PC.** The secret is folded in and then deleted. A kill between the two writes converges on a rerun.
- **`vault_acl.py`.** The owner-only DACL, its inheritance, link and hard-link refusal and handle-based read are right. Tests read the result with `icacls`, not with the module itself.
- **Pass keys.** `verify_host_pass`, `speaks_for` and pairing with digest-checked reruns. Keys never reach a command line.
- **Clock probe.** The SNTP arithmetic, the origin check, no source answering, the mismatch week and the doctor rows are right and tested against a real UDP stub.
- **The host route.** The verbs are closed and the principal comes only from the pass.
- **Server secrets.** Keys and signature windows run on the server, and scripts arrive on quoted heredocs.
- **`first_real_start.py` on the rest of its job.** It talks only to REST and imports nothing from `qmx-agents`. Real mode refuses before it reads a credential, and a rerun needs no second sign-in or bind.

## 6. Must and should

- must p5c-1. On his real folder the deploy line FAILs with "his_click cannot move draft to paper", and nothing names the next step; the rehearsal hid it with fixtures.
- should p5c-2. The deploy line passes at "compiling", so all green can sit beside a node that refused the unit.
- should p5c-3. One app failing at host start stops the rest, so QMB can keep the practice node down.
- should p5c-4. Real mode is tied to `origin/main`, while his ruling says the target is never `main`.
- should p5c-5. Nothing installs OpenObserve on a server, so he gets an "install them there" card on every run.

## 7. Tests

These tests are worth having. Most run real supervisors, real ACLs, real git and real UDP, and assert literal values. 72 read, 2 could go, both step-name pins (p5c-10, 34 lines). They do not hide much, with one exception: `test_first_real_start.py` runs against a fake host written to the script's own expectations, and its deploy row never changes after "accepted". That is why p5c-2 survives. I ask for no new test beyond what fixing p5c-1 needs: a rehearsal variant with no fixture rows.

A stale line: the docstring at the top of `test_connect_node.py` says the node ships no `proofs/` folder, and it now does. No harm.

## 8. Golden and reference data

None in this part. `not-read.tsv` is empty, and every key, clock fact and venue in these tests is made at runtime.

## 9. Edge-case functions walked

1. `clock_probe.query` and `probe`
2. `clock_probe.mismatch_week`
3. `vault_acl.owner_only` with `_tree`
4. `vault_acl._read` (Windows)
5. `forward.verify_host_pass` with `speaks_for`
6. `connect_compute._pass_key_held` with `_pair_pass_key`
7. `connect_node.on_runner`
8. `connect_node._write_keys` with `_rotate`
9. `first_real_start.landed_refusal`
10. `first_start.enable_first_party`

Results: p5c-3, p5c-7, p5c-8 and p5c-9. The others were clean. One race noted, not filed: two server setups at the same moment could lose a key in `pair_place`, and a rerun heals it.

## 10. Set aside for him

- Should the first-start script itself prove the dummy through QMB and the judge, or do you run that first? I assumed you run it first and the script only names the step, because your ruling says QMB proves a unit before demo.
- Which branch will you land the stack on? I assumed it may not be `main`, per your ruling, so the script should take the branch as an option.

## 11. Needs a long run

All from `D:/QMX-worktrees/audit-head/qmx-agents/packages/qmx-host`, after `source D:/QMX-worktrees/audit-ship/tools/env.sh`:

- C-11's kill-at-each-step walk, about 4 minutes: `timeout 600 "$AUDIT_AGENTS_ENV" -m pytest tests/test_connect_node.py -q -x -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/p5c/long1`
- C-17's simulated server: `timeout 600 "$AUDIT_AGENTS_ENV" -m pytest tests/test_connect_node_server.py -q -x -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/p5c/long2`
- C9 between two real hosts (Linux or WSL only; it refuses Windows): `tools/lanes/two_hosts.py`, per `unit-ship/evidence/c17/owner-lanes.md`.
- C-14's real-mode bearer reader: `unit-ship/evidence/c14/owner-c14-bearer.log` is 0 bytes, so no recorded run proves it. I checked the struct layout and the target name by reading only. Command: `owner_lane_c14.py bearer <wt> 18941`, per `evidence/c14/owner-lanes.md`. It uses an entry outside `qmx/`.

## 12. Not read

Nothing in `files.tsv` was skipped. I read `promote.py`, `venue_records.py`, `host_route.py`, `forward.py`, `jobs.py` and `keys.py` only to trace paths, and left judging them to their own auditors. Part of `node.py` and `runtime.py` I read only by grep and line range.

## 13. Skills that changed a decision

- `blast-radius`: made me run a real promote click on a fresh dummy, instead of trusting the rehearsal's all-PASS log.
- `lens-verification-gap`: pointed at the rehearsal's fixture rows and the deploy read that stops at "compiling".
- `code-review`, Spec axis: raised the ruling above the plan line on `origin/main`, and cleared the hub gap under TR:12.
- `principle-test-behavior-not-implementation`: picked out the two step-name pins and kept the rest.
- `lens-edge-case-hunter`: found the start loop that stops at the first failing app.
- `principle-laziness-protocol` and `principle-minimize-reader-load`: I looked for a layer to cut and found none worth a row. `host.py` is one large file changed for many reasons (possible Divergent Change, a judgement call), but moving code would delete nothing.
- `principle-prove-it-works`: kept the bearer reader as unproven rather than calling it fine from reading.
