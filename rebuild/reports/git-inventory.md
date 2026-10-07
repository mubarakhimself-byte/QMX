# Git and branch inventory

Snapshot: 2026-10-07T11:57:23+00:00. This report is a read-only cleanup proposal; none of the proposed commands were executed. Only this packet branch/worktree and report are created for delivery.

Counts: **154 QMX branch refs**, **24 recovery branch refs**, **24 backup branch refs**; **55 registered worktree entries** (32 QMX, 22 recovery, 1 backup), including two bare repositories; **7 dirty worktrees**; **17 PRs** (8 open, 9 merged). QMX recommendations: 14 archive, 94 delete, 46 keep.

## 1. Branches

Comparison anchor: `origin/integration` = `a0e8769772e469bf54bd312cc1e27e7995e16c3b`. Local `integration` = `fdc767033f0f6c3f94f0cbd9f1fd8d9aa17ace60` (different tip; both ancestry results are shown).
Ahead/behind counts are commits relative to that anchor. Date is the last commit committer date; identity is its author. Local and remote refs have separate rows because their tips may differ. `origin/HEAD` is a symbolic alias, not an extra branch. Worktree paths on remote rows identify the corresponding checked-out local branch; those tips may differ.

### QMX

| Ref | Tip | Last commit date | Author identity | Ahead/behind origin/integration | Merged into local integration | Merged into origin/integration | Open PR | Worktree path | Recommendation / reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| refs/heads/chore/ci-lint-hardening | ff99500fe7b3 | 2026-08-22T13:31:24+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/675 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chore/skylos-calibration | 082f130249b6 | 2026-08-22T13:47:29+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/674 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chore/skylos-d325-proto-test | 9beac11634ac | 2026-08-23T05:45:04+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/646 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chore/skylos-round3 | d33193a70e02 | 2026-08-22T14:12:31+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/673 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-27-repair | de0bd4f87a66 | 2026-09-03T00:49:38+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/260 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-60-gate | a2e8cf83bc01 | 2026-09-26T11:17:20+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/79 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-bench-d324 | c0b13edab849 | 2026-09-03T05:50:15+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/246 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-d215-rerun | 78e132f7e5b6 | 2026-09-15T02:27:04+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/216 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-d222-ai-defects | 2bdc643189b4 | 2026-09-14T19:01:01+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/230 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-d324-research-store | dddd87209ead | 2026-09-17T03:06:48+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/174 | yes | yes | — | C:/Users/Mubarak/Desktop/QMX-worktrees/chunk-skylos-d324-research-store | keep: Checked out; preserve working files and session state. |
| refs/heads/chunk/skylos-d325-gaps-test | 8510c032496b | 2026-09-15T13:32:20+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/201 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-data-download-d325 | f18a385f9876 | 2026-08-26T10:20:22+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/565 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-downstream-reads | c78f3148ff67 | 2026-08-26T15:39:44+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/558 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-isolated-d324 | 68e03fa611b3 | 2026-09-01T05:28:58+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/405 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-mis-io | 1b451a848d89 | 2026-09-04T13:01:30+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/245 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-orchestrator-paths | ff164f25a37e | 2026-08-25T02:49:29+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/587 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-qml-exec | 5d94d95b641d | 2026-08-24T13:03:31+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/607 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-qmn-deploy-d324 | 1529910ccf95 | 2026-09-01T14:16:48+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/355 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/chunk/skylos-qmn-namespace | 7b656ebbfa63 | 2026-09-01T04:11:09+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/418 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/codex/factory-enforcement-backend | a774cf7c89c3 | 2026-09-27T15:43:09+03:00 | Mubarak <himselfmubarak@gmail.com> | 4/60 | no | no | [#10](https://github.com/MubarakHimself/QMX/pull/10) | C:/Users/Mubarak/.codex/worktrees/factory-enforcement-backend/QMX | keep: Checked out; preserve working files and session state. |
| refs/heads/codex/factory-enforcement-test | 1400ccdce16e | 2026-09-27T15:20:51+03:00 | Mubarak <himselfmubarak@gmail.com> | 9/60 | no | no | — | C:/Users/Mubarak/.codex/worktrees/factory-enforcement-test/QMX | keep: Checked out; preserve working files and session state. |
| refs/heads/codex/factory-enforcement-ui | 49efa9e71245 | 2026-09-27T15:43:03+03:00 | Mubarak <himselfmubarak@gmail.com> | 10/60 | no | no | [#9](https://github.com/MubarakHimself/QMX/pull/9) | C:/Users/Mubarak/.codex/worktrees/factory-enforcement-ui/QMX | keep: Checked out; preserve working files and session state. |
| refs/heads/codex/plan-qmx-ui-design | 430fb7d2d089 | 2026-09-07T09:20:06+03:00 | Mubarak <himselfmubarak@gmail.com> | 1/713 | no | no | — | — | archive: Unmerged history; tag the exact tip before branch deletion. |
| refs/heads/codex/reticle-unattended | 40c24a0d6e72 | 2026-09-28T18:47:50+03:00 | Mubarak <himselfmubarak@gmail.com> | 14/60 | no | no | — | C:/Users/Mubarak/.codex/worktrees/reticle-unattended/QMX | keep: Checked out; preserve working files and session state. |
| refs/heads/deployment/fmt-check | de4ed64c276a | 2026-09-28T14:32:56+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/52 | yes | yes | — | C:/Users/Mubarak/Desktop/QMX-worktrees/backend-assurance-7b65732f | keep: Checked out; preserve working files and session state. |
| refs/heads/docs/node-veto-round | 8abe6c2ed54f | 2026-08-30T14:29:34+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/714 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/001-qmf-core | 30e5f560addf | 2026-08-22T01:04:24+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/699 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/002-qmf-registry | 1c4684fcce4d | 2026-08-22T11:15:51+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/681 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/003-qmf-data | 9dd3af8884fb | 2026-08-22T07:34:40+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/688 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/004-qmf-calendar-forex | dad7b3f470ab | 2026-08-22T15:43:02+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/670 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/005-qmf-data-backup | a888daf261ae | 2026-08-22T16:21:54+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/665 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/006-qmf-data-source-intake | b3c55c7eb06a | 2026-08-22T17:22:35+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/661 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/007-qmf-indicators | d92d812fb52d | 2026-08-23T21:01:11+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/638 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/008-qmf-venue | 1a4bbc0c2419 | 2026-08-23T04:58:37+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/647 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/009-qmf-structure | d219f7a74019 | 2026-08-23T03:12:09+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/656 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/010-qmf-risk | d668c5e0ac72 | 2026-08-23T22:53:01+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/623 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/011-qml-authoring | 6d61ed5a9483 | 2026-08-24T08:28:03+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/616 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/012-qml-protocol | 628acf68256e | 2026-08-24T12:27:57+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/608 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/013-qmb-substrate | 644d28118881 | 2026-08-24T16:40:46+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/602 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/014-qmb-run-loop | 12a0e88d0af3 | 2026-08-24T22:20:40+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/593 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/015-qmb-orchestrator | dbc10354837c | 2026-08-25T01:43:45+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/588 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/016-qmb-cli-doors | d7ee59471caf | 2026-08-25T06:11:40+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/581 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/017-qmb-execution-ports | 150d625175b4 | 2026-08-25T12:29:52+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/573 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/018-qmb-data-management | 12858d88ca3d | 2026-08-26T09:33:52+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/566 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/019-qmb-reports | a3492ae54fd4 | 2026-08-26T15:04:03+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/559 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/020-qmb-sweeps | 65f214d0b2b7 | 2026-08-26T20:28:05+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/553 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/021-qmb-optimization | 6b56efcb2a75 | 2026-08-27T00:36:44+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/547 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/022-qmb-robustness | 77ab7663e304 | 2026-08-27T03:43:51+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/542 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/023-qmb-synthetic-data | 2c8d4957ef29 | 2026-08-27T07:09:38+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/537 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/024-qmn-broker-boundary | a6b2bca3550f | 2026-09-01T03:51:12+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/420 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/025-qmn-vps-host | b03db49933a4 | 2026-09-01T12:47:29+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/373 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/026-qmn-capital-protection | 6f9c135d975d | 2026-09-02T06:21:54+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/308 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/027-qmn-evidence-replay | ca3c6695664c | 2026-09-02T15:01:57+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/282 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/028-qmn-paper-milestone | 7f9d936c4e91 | 2026-09-03T00:14:49+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/261 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/030-qmn-mis-training | d28a874714f3 | 2026-09-03T05:27:35+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/247 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/031-connect-fx-paper | f1a9f2ef90f1 | 2026-09-14T18:01:46+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/234 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/032-qma-continuation | 6754d755a69c | 2026-09-14T18:37:33+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/231 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/033-qmb-cli-coverage | 29e3186f6880 | 2026-09-14T15:57:57+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/241 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/034-qmb-library | dabdb6672008 | 2026-09-14T21:10:08+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/226 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/035-honest-whatif | 96e45112af86 | 2026-09-15T01:28:12+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/217 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/036-qma-qmb-door | 0a431addae76 | 2026-09-15T07:19:32+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/209 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/037-qma-procedures | 2599a6207c56 | 2026-09-15T09:53:59+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/205 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/038-qml-generation | 6927ca899b57 | 2026-09-15T12:43:56+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/202 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/040-qma-core-seed | 6e19f52d908e | 2026-09-01T00:48:50+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/434 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/041-qma-wire | 4b72e994ed29 | 2026-09-01T04:51:35+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/407 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/042-qma-daemon-journal | d9e1b8b6996c | 2026-09-01T08:00:29+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/399 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/043-qma-hooks-taskgraph | 3a0e96c62677 | 2026-09-01T13:06:32+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/358 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/044-qma-model-tools | 6d5aad7f4289 | 2026-09-01T22:40:38+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/344 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/045-qma-environments-compute | 34fd1ef46a61 | 2026-09-02T05:02:55+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/335 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/046-qma-ledgers-mailbox | 2c2d2769bc81 | 2026-09-02T11:07:49+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/301 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/047-qma-memory-knowledge | c3aa2676d321 | 2026-09-02T14:00:40+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/295 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/048-qma-plugin-packs | ebc180b34b45 | 2026-09-02T23:01:52+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/271 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/049-qml-research-seed | d81df5acaffa | 2026-09-17T00:15:30+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/194 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/049-skylos-qml-quality | 8f6e366825d2 | 2026-09-17T00:40:41+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/193 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/049-skylos-qml-quality-2 | fcbfca6595d4 | 2026-09-17T01:49:58+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/189 | yes | yes | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-049-skylos-qml-quality-2 | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/049-skylos-qml-quality-3 | 49eb1e04e53f | 2026-09-17T02:16:53+03:00 | Mubarak <himselfmubarak@gmail.com> | 2/184 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-049-skylos-qml-quality-3 | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/050-qml-research-identity | ddb8543ac8bf | 2026-09-17T02:22:43+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/181 | yes | yes | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-050-qml-research-identity | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/051-qml-graduation | 85ca51b204bb | 2026-09-17T03:29:15+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/172 | yes | yes | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-051-qml-graduation | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/051-skylos-mill-split | 270e992995c2 | 2026-09-17T05:36:15+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/169 | yes | yes | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-051-skylos-mill-split | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/052-federated-discovery | 938ca589ef25 | 2026-09-17T02:41:06+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/180 | yes | yes | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-052-federated-discovery | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/053-contribution-hit | 580b49aeb2d2 | 2026-09-20T00:10:00+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/165 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/054-invocation-envelope | cce9c8215adf | 2026-09-20T03:18:14+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/161 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/055-product-session | a409a1884eb8 | 2026-09-20T06:24:01+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/157 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/056-graph-dag | 30ba525a1c64 | 2026-09-20T08:50:18+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/153 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/057-task-graph-outbox | 27fc183124f2 | 2026-09-20T11:46:36+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/149 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/058-honesty-fixtures | e99d4e99f018 | 2026-09-20T15:57:49+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/142 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/058-skylos-d222 | 2e2349927a0a | 2026-09-20T16:42:39+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/141 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/059-safety-fixtures | 34c148be404a | 2026-09-20T20:01:29+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/135 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/060-host-sdk | 7223e1a673b7 | 2026-09-25T14:55:38+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/131 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/061-diagnosis-json-lines | 10ea659ef392 | 2026-09-26T13:53:38+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/75 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/062-host-retry | 23c4fcfce97e | 2026-09-26T16:36:17+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/71 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/063-nested-mission | b835eab4e11d | 2026-09-26T18:38:20+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/68 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/064-listing-health | 4845a328b47d | 2026-09-26T20:33:14+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/66 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/065-kit-journey-fixtures | 7b65732fc036 | 2026-09-27T00:02:06+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/60 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/067-host-lifecycle | b625cebe57b9 | 2026-09-29T03:33:41+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/43 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/068-pairing | 6fbe6c2dca11 | 2026-09-29T16:49:43+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/34 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/069-mailbox-session | 49e72693f7b8 | 2026-09-29T20:10:22+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/29 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/epic/070-artifacts | d54e1b4dbbe3 | 2026-09-30T10:32:18+03:00 | Mubarak <himselfmubarak@gmail.com> | 10/29 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-070-artifacts | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/071-editor-drafts | 478489bad85c | 2026-09-30T10:28:13+03:00 | Mubarak <himselfmubarak@gmail.com> | 9/29 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-071-editor-drafts | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/071-editor-drafts-sequential | c1f7331e28b4 | 2026-09-30T14:42:13+03:00 | Mubarak <himselfmubarak@gmail.com> | 8/19 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-071-editor-drafts-sequential | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/072-pack-ui-action-context | 478489bad85c | 2026-09-30T10:28:13+03:00 | Mubarak <himselfmubarak@gmail.com> | 9/29 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-072-pack-ui-action-context | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/072-pack-ui-action-context-sequential | 865fc1a445a4 | 2026-09-30T16:56:22+03:00 | Mubarak <himselfmubarak@gmail.com> | 4/11 | no | no | — | — | archive: Unmerged history; tag the exact tip before branch deletion. |
| refs/heads/epic/073-origin-cancel | d54e1b4dbbe3 | 2026-09-30T10:32:18+03:00 | Mubarak <himselfmubarak@gmail.com> | 10/29 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-073-origin-cancel | keep: Checked out; preserve working files and session state. |
| refs/heads/epic/073-origin-cancel-sequential | 111117b1c86d | 2026-09-30T18:23:34+03:00 | Mubarak <himselfmubarak@gmail.com> | 7/7 | no | no | — | C:/Users/Mubarak/.codex/worktrees/epic-072-pack-ui/QMX | keep: Checked out; preserve working files and session state. |
| refs/heads/factory-test/enforcement-20260927 | 1400ccdce16e | 2026-09-27T15:20:51+03:00 | Mubarak <himselfmubarak@gmail.com> | 9/60 | no | no | — | — | archive: Unmerged history; tag the exact tip before branch deletion. |
| refs/heads/fix/qa-round-1 | ef9bb253fc87 | 2026-08-28T14:39:55+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/446 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/integration | fdc767033f0f | 2026-09-30T10:07:10+03:00 | Mubarak <himselfmubarak@gmail.com> | 7/29 | yes | no | — | C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect | keep: Protected branch. |
| refs/heads/main | c3e8ec5ef33d | 2026-09-27T14:50:24+03:00 | Mubarak <himselfmubarak@gmail.com> | 11/713 | no | no | — | C:/Users/Mubarak/Desktop/QMX | keep: Protected branch. |
| refs/heads/park/skylos-mill-2026-09-26 | a2e8cf83bc01 | 2026-09-26T11:17:20+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/79 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/heads/rebuild/base | d95a977fcac4 | 2026-10-07T14:54:56+03:00 | Mubarak <himselfmubarak@gmail.com> | 433/0 | no | no | [#25](https://github.com/MubarakHimself/QMX/pull/25) | C:/Users/Mubarak/Desktop/QMX-worktrees/rebuild | keep: Protected branch. |
| refs/heads/rebuild/p01-green-baseline | 498203c91d69 | 2026-10-07T14:17:22+03:00 | Mubarak <himselfmubarak@gmail.com> | 431/0 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/p01-green-baseline | keep: Active rebuild lane; concurrent packet work. |
| refs/heads/rebuild/p01-green-test-baseline | 498203c91d69 | 2026-10-07T14:17:22+03:00 | Mubarak <himselfmubarak@gmail.com> | 431/0 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/p01-green-test-baseline | keep: Active rebuild lane; concurrent packet work. |
| refs/heads/rebuild/p03-git-inventory | d95a977fcac4 | 2026-10-07T14:54:56+03:00 | Mubarak <himselfmubarak@gmail.com> | 433/0 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/p03-git-inventory | keep: Active rebuild lane; concurrent packet work. |
| refs/heads/rebuild/p05-survival-map | fef6a1cf0038 | 2026-10-07T14:50:47+03:00 | Codex <codex@openai.com> | 432/0 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/p05-survival-map | keep: Active rebuild lane; concurrent packet work. |
| refs/heads/research/mql5-article-library | 430fb7d2d089 | 2026-09-07T09:20:06+03:00 | Mubarak <himselfmubarak@gmail.com> | 1/713 | no | no | — | C:/Users/Mubarak/Desktop/QMX/.worktrees/mql5-library | keep: Checked out; preserve working files and session state. |
| refs/heads/restore/epic-60-tip | 54f820dcc967 | 2026-09-26T12:03:47+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/78 | yes | yes | — | C:/Users/Mubarak/Desktop/QMX-worktrees/chunk-skylos-60-gate | keep: Checked out; preserve working files and session state. |
| refs/heads/ui | af6628888fb8 | 2026-08-21T19:26:24+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/716 | yes | yes | — | C:/Users/Mubarak/Desktop/QMX/.worktrees/ui | keep: Checked out; preserve working files and session state. |
| refs/heads/ui-epic/066-shell | f6ffaddf3f78 | 2026-09-28T21:47:13+03:00 | Mubarak <himselfmubarak@gmail.com> | 19/60 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/ui-epic-066-shell | keep: Checked out; preserve working files and session state. |
| refs/heads/ui-integration | f6ffaddf3f78 | 2026-09-28T21:47:13+03:00 | Mubarak <himselfmubarak@gmail.com> | 19/60 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/ui-factory | keep: Protected branch. |
| refs/heads/ui-review/repair | 1cc66208a6bd | 2026-10-04T17:02:53+03:00 | Mubarak <himselfmubarak@gmail.com> | 86/60 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair | keep: Protected branch. |
| refs/remotes/origin/chore/skylos-d325-proto-test | 9beac11634ac | 2026-08-23T05:45:04+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/646 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/remotes/origin/chunk/skylos-60-gate | a2e8cf83bc01 | 2026-09-26T11:17:20+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/79 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/remotes/origin/codex/factory-enforcement-backend | a774cf7c89c3 | 2026-09-27T15:43:09+03:00 | Mubarak <himselfmubarak@gmail.com> | 4/60 | no | no | [#10](https://github.com/MubarakHimself/QMX/pull/10) | C:/Users/Mubarak/.codex/worktrees/factory-enforcement-backend/QMX | keep: Checked out; preserve working files and session state. |
| refs/remotes/origin/codex/factory-enforcement-ui | 49efa9e71245 | 2026-09-27T15:43:03+03:00 | Mubarak <himselfmubarak@gmail.com> | 10/60 | no | no | [#9](https://github.com/MubarakHimself/QMX/pull/9) | C:/Users/Mubarak/.codex/worktrees/factory-enforcement-ui/QMX | keep: Checked out; preserve working files and session state. |
| refs/remotes/origin/deployment/fmt-check | de4ed64c276a | 2026-09-28T14:32:56+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/52 | yes | yes | — | C:/Users/Mubarak/Desktop/QMX-worktrees/backend-assurance-7b65732f | keep: Checked out; preserve working files and session state. |
| refs/remotes/origin/epic/007-qmf-indicators | 85c92b78b2a0 | 2026-08-23T07:33:28+03:00 | Mubarak <himselfmubarak@gmail.com> | 5/647 | no | no | — | — | archive: Unmerged history; tag the exact tip before branch deletion. |
| refs/remotes/origin/epic/008-qmf-venue | 95a3a50f1f62 | 2026-08-23T04:46:05+03:00 | Mubarak <himselfmubarak@gmail.com> | 9/661 | no | no | — | — | archive: Unmerged history; tag the exact tip before branch deletion. |
| refs/remotes/origin/epic/009-qmf-structure | d219f7a74019 | 2026-08-23T03:12:09+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/656 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/remotes/origin/epic/010-qmf-risk | 5d427ba97d06 | 2026-08-23T07:44:36+03:00 | Mubarak <himselfmubarak@gmail.com> | 6/647 | no | no | — | — | archive: Unmerged history; tag the exact tip before branch deletion. |
| refs/remotes/origin/epic/067-host-lifecycle | b625cebe57b9 | 2026-09-29T03:33:41+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/43 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/remotes/origin/epic/068-pairing | 6fbe6c2dca11 | 2026-09-29T16:49:43+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/34 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/remotes/origin/epic/069-mailbox-session | 49e72693f7b8 | 2026-09-29T20:10:22+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/29 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/remotes/origin/epic/070-artifacts | d54e1b4dbbe3 | 2026-09-30T10:32:18+03:00 | Mubarak <himselfmubarak@gmail.com> | 10/29 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-070-artifacts | keep: Checked out; preserve working files and session state. |
| refs/remotes/origin/epic/071-editor-drafts-sequential | c1f7331e28b4 | 2026-09-30T14:42:13+03:00 | Mubarak <himselfmubarak@gmail.com> | 8/19 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-071-editor-drafts-sequential | keep: Checked out; preserve working files and session state. |
| refs/remotes/origin/epic/072-pack-ui-action-context-sequential | 865fc1a445a4 | 2026-09-30T16:56:22+03:00 | Mubarak <himselfmubarak@gmail.com> | 4/11 | no | no | — | — | archive: Unmerged history; tag the exact tip before branch deletion. |
| refs/remotes/origin/epic/073-origin-cancel-sequential | 111117b1c86d | 2026-09-30T18:23:34+03:00 | Mubarak <himselfmubarak@gmail.com> | 7/7 | no | no | — | C:/Users/Mubarak/.codex/worktrees/epic-072-pack-ui/QMX | keep: Checked out; preserve working files and session state. |
| refs/remotes/origin/factory-recovery/007/490ccd862e65 | 46b67598d6cc | 2026-08-23T18:46:45+03:00 | Mubarak <himselfmubarak@gmail.com> | 8/647 | no | no | — | — | keep: Research or explicit recovery/checkpoint anchor. |
| refs/remotes/origin/factory-test/enforcement-20260927 | 1400ccdce16e | 2026-09-27T15:20:51+03:00 | Mubarak <himselfmubarak@gmail.com> | 9/60 | no | no | — | — | archive: Unmerged history; tag the exact tip before branch deletion. |
| refs/remotes/origin/fix/qa-round-1 | ef9bb253fc87 | 2026-08-28T14:39:55+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/446 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/remotes/origin/integration | a0e8769772e4 | 2026-09-30T18:45:04+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/0 | no | yes | — | C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect | keep: Protected branch. |
| refs/remotes/origin/main | c3e8ec5ef33d | 2026-09-27T14:50:24+03:00 | Mubarak <himselfmubarak@gmail.com> | 11/713 | no | no | — | C:/Users/Mubarak/Desktop/QMX | keep: Protected branch. |
| refs/remotes/origin/park/skylos-mill-2026-09-26 | a2e8cf83bc01 | 2026-09-26T11:17:20+03:00 | Mubarak <himselfmubarak@gmail.com> | 0/79 | yes | yes | — | — | delete: Tip is reachable from origin/integration; no worktree or active PR. |
| refs/remotes/origin/qmx-stop-checkpoint-2026-10-01 | 7b4ece09f3a4 | 2026-10-01T18:24:41Z | Mubarak <himselfmubarak@gmail.com> | 316/0 | no | no | — | — | keep: Research or explicit recovery/checkpoint anchor. |
| refs/remotes/origin/qmx-work-release-checkpoint-2026-10-01 | 01fed525af62 | 2026-10-01T17:07:49Z | Mubarak <himselfmubarak@gmail.com> | 288/0 | no | no | — | — | keep: Research or explicit recovery/checkpoint anchor. |
| refs/remotes/origin/quality/deployment-gates | 63088598b5fd | 2026-09-30T10:09:59+03:00 | MubarakHimself <161692548+MubarakHimself@users.noreply.github.com> | 2/29 | no | no | — | — | archive: Unmerged history; tag the exact tip before branch deletion. |
| refs/remotes/origin/rebuild/base | d95a977fcac4 | 2026-10-07T14:54:56+03:00 | Mubarak <himselfmubarak@gmail.com> | 433/0 | no | no | [#25](https://github.com/MubarakHimself/QMX/pull/25) | C:/Users/Mubarak/Desktop/QMX-worktrees/rebuild | keep: Protected branch. |
| refs/remotes/origin/rebuild/p05-survival-map | fef6a1cf0038 | 2026-10-07T14:50:47+03:00 | Codex <codex@openai.com> | 432/0 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/p05-survival-map | keep: Active rebuild lane; concurrent packet work. |
| refs/remotes/origin/review/backend-baseline-public-20261004 | 3a86eee0fd04 | 2026-10-04T19:14:17+03:00 | Mubarak <himselfmubarak@gmail.com> | 378/0 | no | no | [#20](https://github.com/MubarakHimself/QMX/pull/20) | — | archive: Superseded review stack (#25); archive exact tip before deletion. |
| refs/remotes/origin/review/backend-capabilities-public-20261005 | 5aed6d7fdee9 | 2026-10-05T02:55:41+03:00 | Mubarak <himselfmubarak@gmail.com> | 402/0 | no | no | [#23](https://github.com/MubarakHimself/QMX/pull/23) | — | archive: Superseded review stack (#25); archive exact tip before deletion. |
| refs/remotes/origin/review/backend-ci-public-20261004 | c738d707e25f | 2026-10-05T01:17:07+03:00 | Codex <noreply@openai.com> | 380/0 | no | no | [#22](https://github.com/MubarakHimself/QMX/pull/22) | — | archive: Superseded review stack (#25); archive exact tip before deletion. |
| refs/remotes/origin/review/backend-recovery-public-20261005 | da6955af024c | 2026-10-05T12:44:25+03:00 | Mubarak <himselfmubarak@gmail.com> | 414/0 | no | no | [#24](https://github.com/MubarakHimself/QMX/pull/24) | — | archive: Superseded review stack (#25); archive exact tip before deletion. |
| refs/remotes/origin/review/canonical-join-public-20261004 | 74ccf3bbf244 | 2026-10-04T22:50:40+03:00 | Mubarak <himselfmubarak@gmail.com> | 385/0 | no | no | [#21](https://github.com/MubarakHimself/QMX/pull/21) | — | archive: Superseded review stack (#25); archive exact tip before deletion. |
| refs/remotes/origin/ui-epic/066-shell | f6ffaddf3f78 | 2026-09-28T21:47:13+03:00 | Mubarak <himselfmubarak@gmail.com> | 19/60 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/ui-epic-066-shell | keep: Checked out; preserve working files and session state. |
| refs/remotes/origin/ui-integration | d3c6e1234b3d | 2026-09-27T13:22:49+03:00 | Mubarak <himselfmubarak@gmail.com> | 4/60 | no | no | — | C:/Users/Mubarak/Desktop/QMX-worktrees/ui-factory | keep: Protected branch. |

### Recovery repository

Location: `D:/Codex-Recovery/2026-10-04/integration-base.git`. Comparisons expose the QMX object directory through a process-local `GIT_ALTERNATE_OBJECT_DIRECTORIES` environment variable. No recovery/backup configuration, refs, or objects are written. This proves commit ancestry across the independent repositories rather than assuming it from matching production files.

| Ref | Tip | Last commit date | Author identity | Ahead/behind origin/integration | Merged into local integration | Merged into origin/integration | Open PR | Worktree path | Recommendation / reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| refs/heads/codex/ma01-discovery | 8465c03f0ec1 | 2026-10-05T20:53:44+03:00 | Mubarak <himselfmubarak@gmail.com> | 418/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/ma01-discovery/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/import/deepagents-reviewed | c56e3645b8e8 | 2026-10-04T21:24:32+03:00 | Mubarak <himselfmubarak@gmail.com> | 387/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/import/qmx-backend-quality | 448eb11442e4 | 2026-10-05T02:08:10+03:00 | Mubarak <himselfmubarak@gmail.com> | 397/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-artifact-cap | af4332467635 | 2026-10-05T18:41:58+03:00 | Mubarak <himselfmubarak@gmail.com> | 416/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/artifact-cap/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-authored-graphs | 11c4dbb56f30 | 2026-10-05T02:29:15+03:00 | Mubarak <himselfmubarak@gmail.com> | 399/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-04/authored-graphs/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-authored-quality-composed | 1531eecb4c05 | 2026-10-05T02:55:41+03:00 | Mubarak <himselfmubarak@gmail.com> | 402/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-04/authored-quality-composed/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-cold-start | c7f0ef603dc5 | 2026-10-05T20:39:39+03:00 | Mubarak <himselfmubarak@gmail.com> | 418/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/cold-start/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-composed-capabilities | 8873a4a5774c | 2026-10-05T01:34:15+03:00 | Mubarak <himselfmubarak@gmail.com> | 396/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-04/composed-capabilities/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-controlled-integration | 222c34ba5ace | 2026-10-04T22:50:40+03:00 | Mubarak <himselfmubarak@gmail.com> | 385/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-docs-ambient-quality | b858633c436c | 2026-10-05T05:22:33+03:00 | Mubarak <himselfmubarak@gmail.com> | 405/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/docs-ambient-quality/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-final-integration | ea65b50d1d4f | 2026-10-05T12:44:25+03:00 | Mubarak <himselfmubarak@gmail.com> | 414/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/final-integration/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-host-binding | 222c34ba5ace | 2026-10-04T22:50:40+03:00 | Mubarak <himselfmubarak@gmail.com> | 385/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-host-binding-bridge | 411f2454f482 | 2026-10-05T00:41:41+03:00 | Mubarak <himselfmubarak@gmail.com> | 386/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-04/task-27/host-binding-worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma02-candidates | 1c8e0b603984 | 2026-10-06T00:03:47+03:00 | Mubarak <himselfmubarak@gmail.com> | 425/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/ma02-candidates/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma03-validation | 41082c1805e3 | 2026-10-06T01:22:25+03:00 | Mubarak <himselfmubarak@gmail.com> | 426/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/ma03-validation/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma04-publication | 658802338ed4 | 2026-10-06T03:02:18+03:00 | Codex <codex@openai.com> | 427/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/ma04-publication/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma04-repair | 2dfa57d7f2a5 | 2026-10-06T03:44:15+03:00 | Mubarak <himselfmubarak@gmail.com> | 428/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/ma04-publication-repair/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma05-activity | 46e4b462e39e | 2026-10-06T04:39:27+03:00 | Mubarak <himselfmubarak@gmail.com> | 429/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-06/ma05-activity/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma05-defensive-repair | 8ef21bf8399f | 2026-10-06T10:35:13+03:00 | Mubarak <himselfmubarak@gmail.com> | 431/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-06/ma05-defensive-repair/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma05-log-repair | c153a94e9a7e | 2026-10-06T05:00:49+03:00 | Mubarak <himselfmubarak@gmail.com> | 430/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-06/ma05-log-repair/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-memory-provider-seam | b0cf4c46656c | 2026-10-05T00:09:32+03:00 | Mubarak <himselfmubarak@gmail.com> | 388/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-04/task-28/provider-seam-worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-miniapp-integration | 9843b5bb1bbf | 2026-10-05T22:14:02+03:00 | Mubarak <himselfmubarak@gmail.com> | 422/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/miniapp-integration/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-owner-reconciliation | d73aa3723ad4 | 2026-10-05T04:06:12+03:00 | Mubarak <himselfmubarak@gmail.com> | 404/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/owner-reconciliation/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-partition-retry | 5fe5b6d29497 | 2026-10-05T05:46:17+03:00 | Mubarak <himselfmubarak@gmail.com> | 406/0 | no | no | — (separate repository) | D:/Codex-Recovery/2026-10-05/partition-retry/worktree | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |

### Backup repository

Location: `C:/Users/Mubarak/Desktop/QMX-backups/integration-base-2026-10-07.git`. Comparisons expose the QMX object directory through a process-local `GIT_ALTERNATE_OBJECT_DIRECTORIES` environment variable. No recovery/backup configuration, refs, or objects are written. This proves commit ancestry across the independent repositories rather than assuming it from matching production files.

| Ref | Tip | Last commit date | Author identity | Ahead/behind origin/integration | Merged into local integration | Merged into origin/integration | Open PR | Worktree path | Recommendation / reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| refs/heads/codex/ma01-discovery | 8465c03f0ec1 | 2026-10-05T20:53:44+03:00 | Mubarak <himselfmubarak@gmail.com> | 418/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/import/deepagents-reviewed | c56e3645b8e8 | 2026-10-04T21:24:32+03:00 | Mubarak <himselfmubarak@gmail.com> | 387/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/import/qmx-backend-quality | 448eb11442e4 | 2026-10-05T02:08:10+03:00 | Mubarak <himselfmubarak@gmail.com> | 397/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-artifact-cap | af4332467635 | 2026-10-05T18:41:58+03:00 | Mubarak <himselfmubarak@gmail.com> | 416/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-authored-graphs | 11c4dbb56f30 | 2026-10-05T02:29:15+03:00 | Mubarak <himselfmubarak@gmail.com> | 399/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-authored-quality-composed | 1531eecb4c05 | 2026-10-05T02:55:41+03:00 | Mubarak <himselfmubarak@gmail.com> | 402/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-cold-start | c7f0ef603dc5 | 2026-10-05T20:39:39+03:00 | Mubarak <himselfmubarak@gmail.com> | 418/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-composed-capabilities | 8873a4a5774c | 2026-10-05T01:34:15+03:00 | Mubarak <himselfmubarak@gmail.com> | 396/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-controlled-integration | 222c34ba5ace | 2026-10-04T22:50:40+03:00 | Mubarak <himselfmubarak@gmail.com> | 385/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-docs-ambient-quality | b858633c436c | 2026-10-05T05:22:33+03:00 | Mubarak <himselfmubarak@gmail.com> | 405/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-final-integration | ea65b50d1d4f | 2026-10-05T12:44:25+03:00 | Mubarak <himselfmubarak@gmail.com> | 414/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-host-binding | 222c34ba5ace | 2026-10-04T22:50:40+03:00 | Mubarak <himselfmubarak@gmail.com> | 385/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-host-binding-bridge | 411f2454f482 | 2026-10-05T00:41:41+03:00 | Mubarak <himselfmubarak@gmail.com> | 386/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma02-candidates | 1c8e0b603984 | 2026-10-06T00:03:47+03:00 | Mubarak <himselfmubarak@gmail.com> | 425/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma03-validation | 41082c1805e3 | 2026-10-06T01:22:25+03:00 | Mubarak <himselfmubarak@gmail.com> | 426/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma04-publication | 658802338ed4 | 2026-10-06T03:02:18+03:00 | Codex <codex@openai.com> | 427/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma04-repair | 2dfa57d7f2a5 | 2026-10-06T03:44:15+03:00 | Mubarak <himselfmubarak@gmail.com> | 428/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma05-activity | 46e4b462e39e | 2026-10-06T04:39:27+03:00 | Mubarak <himselfmubarak@gmail.com> | 429/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma05-defensive-repair | 8ef21bf8399f | 2026-10-06T10:35:13+03:00 | Mubarak <himselfmubarak@gmail.com> | 431/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-ma05-log-repair | c153a94e9a7e | 2026-10-06T05:00:49+03:00 | Mubarak <himselfmubarak@gmail.com> | 430/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-memory-provider-seam | b0cf4c46656c | 2026-10-05T00:09:32+03:00 | Mubarak <himselfmubarak@gmail.com> | 388/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-miniapp-integration | 9843b5bb1bbf | 2026-10-05T22:14:02+03:00 | Mubarak <himselfmubarak@gmail.com> | 422/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-owner-reconciliation | d73aa3723ad4 | 2026-10-05T04:06:12+03:00 | Mubarak <himselfmubarak@gmail.com> | 404/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |
| refs/heads/work/qmx-partition-retry | 5fe5b6d29497 | 2026-10-05T05:46:17+03:00 | Mubarak <himselfmubarak@gmail.com> | 406/0 | no | no | — (separate repository) | — | keep: Recovery/backup history; preserve until recovery audit and restore are approved. |

Backup bundle: `C:/Users/Mubarak/Desktop/QMX-backups/integration-base-2026-10-07.bundle` has 24 branch heads matching every backup branch tip, plus HEAD. Keep both backups; matching tips do not by themselves prove a full restore.

## 2. Worktrees

Keep every registered working directory for now. Even a clean worktree can contain ignored environments, runtime data and ongoing agent state. Dirty entries need an owner to preserve/commit their files before any cleanup. No worktree removal is proposed.

| Repository | Path | Branch / detached tip | State | Recommendation |
| --- | --- | --- | --- | --- |
| QMX | C:/Users/Mubarak/Desktop/QMX | refs/heads/main | dirty (331 entries) | keep: preserve dirty files / owner review |
| QMX | C:/Users/Mubarak/.codex/worktrees/epic-072-pack-ui/QMX | refs/heads/epic/073-origin-cancel-sequential | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/.codex/worktrees/factory-enforcement-backend/QMX | refs/heads/codex/factory-enforcement-backend | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/.codex/worktrees/factory-enforcement-test/QMX | refs/heads/codex/factory-enforcement-test | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/.codex/worktrees/factory-enforcement-ui/QMX | refs/heads/codex/factory-enforcement-ui | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/.codex/worktrees/reticle-unattended/QMX | refs/heads/codex/reticle-unattended | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect | refs/heads/integration | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX/.worktrees/mql5-library | refs/heads/research/mql5-article-library | dirty (2 entries) | keep: preserve dirty files / owner review |
| QMX | C:/Users/Mubarak/Desktop/QMX/.worktrees/ui | refs/heads/ui | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/backend-assurance-7b65732f | refs/heads/deployment/fmt-check | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/chunk-skylos-60-gate | refs/heads/restore/epic-60-tip | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/chunk-skylos-d324-research-store | refs/heads/chunk/skylos-d324-research-store | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-049-skylos-qml-quality-2 | refs/heads/epic/049-skylos-qml-quality-2 | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-049-skylos-qml-quality-3 | refs/heads/epic/049-skylos-qml-quality-3 | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-050-qml-research-identity | refs/heads/epic/050-qml-research-identity | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-051-qml-graduation | refs/heads/epic/051-qml-graduation | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-051-skylos-mill-split | refs/heads/epic/051-skylos-mill-split | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-052-federated-discovery | refs/heads/epic/052-federated-discovery | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-070-artifacts | refs/heads/epic/070-artifacts | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-071-editor-drafts | refs/heads/epic/071-editor-drafts | dirty (2 entries) | keep: preserve dirty files / owner review |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-071-editor-drafts-sequential | refs/heads/epic/071-editor-drafts-sequential | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-072-pack-ui-action-context | refs/heads/epic/072-pack-ui-action-context | dirty (9 entries) | keep: preserve dirty files / owner review |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/epic-073-origin-cancel | refs/heads/epic/073-origin-cancel | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/p01-green-baseline | refs/heads/rebuild/p01-green-baseline | dirty (15 entries) | keep: preserve dirty files / owner review |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/p01-green-test-baseline | refs/heads/rebuild/p01-green-test-baseline | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/p03-git-inventory | refs/heads/rebuild/p03-git-inventory | dirty (1 entries) | keep: preserve dirty files / owner review |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/p05-survival-map | refs/heads/rebuild/p05-survival-map | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/pre-miniapps-270e992 | detached 270e992995c2 | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/rebuild | refs/heads/rebuild/base | dirty (1 entries) | keep: preserve dirty files / owner review |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/ui-epic-066-shell | refs/heads/ui-epic/066-shell | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/ui-factory | refs/heads/ui-integration | clean | keep: session/data ownership not yet confirmed |
| QMX | C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair | refs/heads/ui-review/repair | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-04/integration-base.git | bare repository | bare (no working files) | keep: preserve repository |
| recovery | D:/Codex-Recovery/2026-10-04/authored-graphs/worktree | refs/heads/work/qmx-authored-graphs | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-04/authored-quality-composed/worktree | refs/heads/work/qmx-authored-quality-composed | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-04/composed-capabilities/worktree | refs/heads/work/qmx-composed-capabilities | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-04/task-27/host-binding-worktree | refs/heads/work/qmx-host-binding-bridge | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-04/task-28/provider-seam-worktree | refs/heads/work/qmx-memory-provider-seam | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/artifact-cap/worktree | refs/heads/work/qmx-artifact-cap | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/cold-start/worktree | refs/heads/work/qmx-cold-start | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/docs-ambient-quality/worktree | refs/heads/work/qmx-docs-ambient-quality | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/final-integration/worktree | refs/heads/work/qmx-final-integration | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/ma01-discovery/worktree | refs/heads/codex/ma01-discovery | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/ma02-candidates/worktree | refs/heads/work/qmx-ma02-candidates | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/ma03-validation/worktree | refs/heads/work/qmx-ma03-validation | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/ma04-publication/worktree | refs/heads/work/qmx-ma04-publication | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/ma04-publication-repair/worktree | refs/heads/work/qmx-ma04-repair | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/miniapp-integration/worktree | refs/heads/work/qmx-miniapp-integration | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/owner-reconciliation/worktree | refs/heads/work/qmx-owner-reconciliation | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-05/partition-retry/worktree | refs/heads/work/qmx-partition-retry | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-06/ma05-activity/worktree | refs/heads/work/qmx-ma05-activity | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-06/ma05-defensive-repair/worktree | refs/heads/work/qmx-ma05-defensive-repair | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-06/ma05-log-repair/worktree | refs/heads/work/qmx-ma05-log-repair | clean | keep: session/data ownership not yet confirmed |
| recovery | D:/Codex-Recovery/2026-10-06/qmb-data-use-check/worktree | detached 2dfa57d7f2a5 | clean | keep: session/data ownership not yet confirmed |
| backup | C:/Users/Mubarak/Desktop/QMX-backups/integration-base-2026-10-07.git | bare repository | bare (no working files) | keep: preserve repository |

Codex root scan: all 5 directories under `C:/Users/Mubarak/.codex/worktrees/` contain registered QMX worktrees; no additional unregistered `.git` markers found. Checked `D:/Codex-Recovery/2026-10-04/integration-base.git` and both listed desktop backup artifacts. Status includes tracked changes and all untracked files, excludes ignored files, and used `--no-optional-locks` to avoid refreshing another session's index.

## 3. PRs

The packet identifies #20–#24 as superseded by #25 (same production code plus MA01–MA04). Their unmerged branch tips must still be archived before deleting them. #25 is an open draft explicitly titled “do not merge”; preserve it as the visibility umbrella. This packet PR is created after the snapshot and is not counted below.

| Number | Title | State | Base | Head | Recommendation |
| --- | --- | --- | --- | --- | --- |
| [#26](https://github.com/MubarakHimself/QMX/pull/26) | P05: QMA survival map and port boundaries | MERGED | rebuild/base | rebuild/p05-survival-map | keep: existing merged record |
| [#25](https://github.com/MubarakHimself/QMX/pull/25) | Draft: Aurelius backend baseline (MA04) for CI visibility — do not merge | OPEN | integration | rebuild/base | keep: visibility umbrella; do not merge |
| [#24](https://github.com/MubarakHimself/QMX/pull/24) | Add bounded owner and partition recovery with installed backend fixes | OPEN | review/backend-capabilities-public-20261005 | review/backend-recovery-public-20261005 | close: superseded by #25; preserve archived branch tips |
| [#23](https://github.com/MubarakHimself/QMX/pull/23) | Add host tool bindings, scoped memory and authored paths | OPEN | review/canonical-join-public-20261004 | review/backend-capabilities-public-20261005 | close: superseded by #25; preserve archived branch tips |
| [#22](https://github.com/MubarakHimself/QMX/pull/22) | ci: enable existing quality checks for reviewed backend stack | OPEN | review/backend-baseline-public-20261004 | review/backend-ci-public-20261004 | close: superseded by #25; preserve archived branch tips |
| [#21](https://github.com/MubarakHimself/QMX/pull/21) | Add bounded actor and Study canonical request integration | OPEN | review/backend-baseline-public-20261004 | review/canonical-join-public-20261004 | close: superseded by #25; preserve archived branch tips |
| [#20](https://github.com/MubarakHimself/QMX/pull/20) | Review backend baseline and CI repairs after the stopped checkpoint | OPEN | qmx-stop-checkpoint-2026-10-01 | review/backend-baseline-public-20261004 | close: superseded by #25; preserve archived branch tips |
| [#19](https://github.com/MubarakHimself/QMX/pull/19) | Epic 73: originating-session job cancellation | MERGED | integration | epic/073-origin-cancel-sequential | keep: existing merged record |
| [#18](https://github.com/MubarakHimself/QMX/pull/18) | Epic 72: durable Pack UI and host action context | MERGED | integration | epic/072-pack-ui-action-context-sequential | keep: existing merged record |
| [#17](https://github.com/MubarakHimself/QMX/pull/17) | Epic 71: durable editor draft publication | MERGED | integration | epic/071-editor-drafts-sequential | keep: existing merged record |
| [#16](https://github.com/MubarakHimself/QMX/pull/16) | Epic 70: complete artifact transfer | MERGED | integration | epic/070-artifacts | keep: existing merged record |
| [#15](https://github.com/MubarakHimself/QMX/pull/15) | Epic 69: mailbox session (FEAT-0067) | MERGED | integration | epic/069-mailbox-session | keep: existing merged record |
| [#14](https://github.com/MubarakHimself/QMX/pull/14) | Epic 68: browser pairing (FEAT-0066) | MERGED | integration | epic/068-pairing | keep: existing merged record |
| [#13](https://github.com/MubarakHimself/QMX/pull/13) | Epic 67: first operator starts the local daemon (FEAT-0065) | MERGED | integration | epic/067-host-lifecycle | keep: existing merged record |
| [#12](https://github.com/MubarakHimself/QMX/pull/12) | ci: format, Skylos annotate-only, Linux ctypes so factory prompts can land | MERGED | integration | deployment/fmt-check | keep: existing merged record |
| [#10](https://github.com/MubarakHimself/QMX/pull/10) | Gate backend factory promotion on exact candidate CI | OPEN | integration | codex/factory-enforcement-backend | keep: unresolved factory scope; operator review |
| [#9](https://github.com/MubarakHimself/QMX/pull/9) | Enforce immutable UI factory candidates and retained runtime proof | OPEN | ui-integration | codex/factory-enforcement-ui | keep: unresolved factory scope; operator review |

## 4. Proposed commands (not executed)

These PowerShell commands are proposals for a separately approved cleanup. Re-inventory first: concurrent agents can create branches/PRs or move tips after this snapshot. Do not run against changed tips or newly checked-out branches. Commands run in QMX without switching or modifying protected branches. Remote deletes use leases against the recorded SHA; archive tags retain the recorded objects and are pushed before remote deletion. Local deletes first use compare-and-delete on the expected SHA, then remove branch configuration. Stop on any error.

```powershell
Set-Location 'C:/Users/Mubarak/Desktop/QMX'
git fetch origin
git branch -a
git worktree list
gh pr list --repo MubarakHimself/QMX --state all --limit 100
```

Archive unmerged tips, then delete eligible branches:

```powershell
git tag 'archive/codex/plan-qmx-ui-design' 430fb7d2d08997085c28d717b25a1ff5c3c78e62
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/codex/plan-qmx-ui-design'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git update-ref -d 'refs/heads/codex/plan-qmx-ui-design' 430fb7d2d08997085c28d717b25a1ff5c3c78e62
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.codex/plan-qmx-ui-design'
# A missing branch config section is harmless.
git tag 'archive/epic/072-pack-ui-action-context-sequential' 865fc1a445a4c247fbc0300881e82c8ff241b36a
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/epic/072-pack-ui-action-context-sequential'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git update-ref -d 'refs/heads/epic/072-pack-ui-action-context-sequential' 865fc1a445a4c247fbc0300881e82c8ff241b36a
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/072-pack-ui-action-context-sequential'
# A missing branch config section is harmless.
git tag 'archive/factory-test/enforcement-20260927' 1400ccdce16e47e4a9fbb63ca25853814080a698
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/factory-test/enforcement-20260927'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git update-ref -d 'refs/heads/factory-test/enforcement-20260927' 1400ccdce16e47e4a9fbb63ca25853814080a698
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.factory-test/enforcement-20260927'
# A missing branch config section is harmless.
git tag 'archive/origin/epic/007-qmf-indicators' 85c92b78b2a0b28c1f53a1fc316f1f4d2843b42d
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/epic/007-qmf-indicators'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/epic/007-qmf-indicators:85c92b78b2a0b28c1f53a1fc316f1f4d2843b42d origin ':refs/heads/epic/007-qmf-indicators'
git tag 'archive/origin/epic/008-qmf-venue' 95a3a50f1f620ebd5d737ec521279ec772618158
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/epic/008-qmf-venue'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/epic/008-qmf-venue:95a3a50f1f620ebd5d737ec521279ec772618158 origin ':refs/heads/epic/008-qmf-venue'
git tag 'archive/origin/epic/010-qmf-risk' 5d427ba97d06dd6ef10b729539ba351a5514dd0b
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/epic/010-qmf-risk'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/epic/010-qmf-risk:5d427ba97d06dd6ef10b729539ba351a5514dd0b origin ':refs/heads/epic/010-qmf-risk'
git tag 'archive/origin/epic/072-pack-ui-action-context-sequential' 865fc1a445a4c247fbc0300881e82c8ff241b36a
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/epic/072-pack-ui-action-context-sequential'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/epic/072-pack-ui-action-context-sequential:865fc1a445a4c247fbc0300881e82c8ff241b36a origin ':refs/heads/epic/072-pack-ui-action-context-sequential'
git tag 'archive/origin/factory-test/enforcement-20260927' 1400ccdce16e47e4a9fbb63ca25853814080a698
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/factory-test/enforcement-20260927'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/factory-test/enforcement-20260927:1400ccdce16e47e4a9fbb63ca25853814080a698 origin ':refs/heads/factory-test/enforcement-20260927'
git tag 'archive/origin/quality/deployment-gates' 63088598b5fd5c75e5967e3c4db723c13f2e92a8
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/quality/deployment-gates'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/quality/deployment-gates:63088598b5fd5c75e5967e3c4db723c13f2e92a8 origin ':refs/heads/quality/deployment-gates'
git tag 'archive/origin/review/backend-baseline-public-20261004' 3a86eee0fd04a5ed79950517cd3be7256314919a
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/review/backend-baseline-public-20261004'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/review/backend-baseline-public-20261004:3a86eee0fd04a5ed79950517cd3be7256314919a origin ':refs/heads/review/backend-baseline-public-20261004'
git tag 'archive/origin/review/backend-capabilities-public-20261005' 5aed6d7fdee936687a6391be3639f37b31aa5133
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/review/backend-capabilities-public-20261005'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/review/backend-capabilities-public-20261005:5aed6d7fdee936687a6391be3639f37b31aa5133 origin ':refs/heads/review/backend-capabilities-public-20261005'
git tag 'archive/origin/review/backend-ci-public-20261004' c738d707e25fce73a0b7cb9911eaba69ddd23344
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/review/backend-ci-public-20261004'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/review/backend-ci-public-20261004:c738d707e25fce73a0b7cb9911eaba69ddd23344 origin ':refs/heads/review/backend-ci-public-20261004'
git tag 'archive/origin/review/backend-recovery-public-20261005' da6955af024cfd83d5b914f4c0c7c43bb347c56e
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/review/backend-recovery-public-20261005'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/review/backend-recovery-public-20261005:da6955af024cfd83d5b914f4c0c7c43bb347c56e origin ':refs/heads/review/backend-recovery-public-20261005'
git tag 'archive/origin/review/canonical-join-public-20261004' 74ccf3bbf2442be7ae4f529b73783f309d86d1d1
if ($LASTEXITCODE -ne 0) { throw 'Archive tag failed; stop' }
git push origin 'refs/tags/archive/origin/review/canonical-join-public-20261004'
if ($LASTEXITCODE -ne 0) { throw 'Archive push failed; stop' }
git push --force-with-lease=refs/heads/review/canonical-join-public-20261004:74ccf3bbf2442be7ae4f529b73783f309d86d1d1 origin ':refs/heads/review/canonical-join-public-20261004'
```

Delete tips already merged into integration:

```powershell
git update-ref -d 'refs/heads/chore/ci-lint-hardening' ff99500fe7b36f119d849742165568dd7959fd2d
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chore/ci-lint-hardening'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chore/skylos-calibration' 082f130249b6c492dce28b8470a1fab64c5978fa
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chore/skylos-calibration'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chore/skylos-d325-proto-test' 9beac11634ac4587c01c209003729a3da640a16d
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chore/skylos-d325-proto-test'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chore/skylos-round3' d33193a70e02a596d057b47354e1b495ca4878d4
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chore/skylos-round3'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-27-repair' de0bd4f87a668703b47db1291431f2b18461bfac
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-27-repair'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-60-gate' a2e8cf83bc01cb17fefc57647fcf96459218f158
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-60-gate'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-bench-d324' c0b13edab8497301a8d323d980fa9ca8d528a767
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-bench-d324'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-d215-rerun' 78e132f7e5b63ab480a35e1d1164aad6cbd269ed
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-d215-rerun'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-d222-ai-defects' 2bdc643189b45f4e2b3a37ab6eed4d69fbd82ea8
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-d222-ai-defects'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-d325-gaps-test' 8510c032496bb870824ecc5c4f807e8a4e4f167e
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-d325-gaps-test'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-data-download-d325' f18a385f9876d38885a7796e0ad7b7e82fad5537
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-data-download-d325'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-downstream-reads' c78f3148ff672eac191871400b121114f3e0e245
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-downstream-reads'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-isolated-d324' 68e03fa611b37ee3bf6495aa8cd555f80542c3cb
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-isolated-d324'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-mis-io' 1b451a848d897e42f6e2c7fd9f2ea86fab7295f2
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-mis-io'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-orchestrator-paths' ff164f25a37ebf420d68d70f440f82230b954c03
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-orchestrator-paths'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-qml-exec' 5d94d95b641d6aa8bf05254f1e308a586752b9ef
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-qml-exec'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-qmn-deploy-d324' 1529910ccf95b699a2d323a8bdd89bfa99cf5dc1
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-qmn-deploy-d324'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/chunk/skylos-qmn-namespace' 7b656ebbfa63bb283f19d14b219b680d0cd18c51
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.chunk/skylos-qmn-namespace'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/docs/node-veto-round' 8abe6c2ed54fcbb37e4af4132285a1157d3d9286
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.docs/node-veto-round'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/001-qmf-core' 30e5f560addf27a11e9177a4a2942064961e67ce
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/001-qmf-core'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/002-qmf-registry' 1c4684fcce4de31d4782c270219b3e181d832005
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/002-qmf-registry'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/003-qmf-data' 9dd3af8884fb0b36a4e14d129cb12c66b63e76bd
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/003-qmf-data'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/004-qmf-calendar-forex' dad7b3f470abff59a884210611c73d0d6e22d10d
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/004-qmf-calendar-forex'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/005-qmf-data-backup' a888daf261ae90b37840adf1b3b3065dd11d0b5b
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/005-qmf-data-backup'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/006-qmf-data-source-intake' b3c55c7eb06a7cc8102a5619d163b76418da825e
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/006-qmf-data-source-intake'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/007-qmf-indicators' d92d812fb52d2bfbe0cbd33d2995c6c7ecf50fb0
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/007-qmf-indicators'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/008-qmf-venue' 1a4bbc0c24192fd0aa09bfbc83f27b17ccc7600f
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/008-qmf-venue'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/009-qmf-structure' d219f7a74019e5ec1d778231a06147b5d5dc7754
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/009-qmf-structure'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/010-qmf-risk' d668c5e0ac727be56c9ef792b18fd08dcad6c19a
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/010-qmf-risk'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/011-qml-authoring' 6d61ed5a9483e156c52ae49268310d7481a31495
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/011-qml-authoring'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/012-qml-protocol' 628acf68256eb58c4f64eb2432ba85446b95944e
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/012-qml-protocol'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/013-qmb-substrate' 644d281188811fa2d919c5aa46f52ee73f3d0342
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/013-qmb-substrate'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/014-qmb-run-loop' 12a0e88d0af396ce01e1a68646c2df263f9222bb
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/014-qmb-run-loop'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/015-qmb-orchestrator' dbc10354837cde0fc8ea6fa36aa0657c7453ff11
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/015-qmb-orchestrator'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/016-qmb-cli-doors' d7ee59471caf142f3e45bc2b8902e7e147aa0d6d
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/016-qmb-cli-doors'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/017-qmb-execution-ports' 150d625175b4af655746ac376ec6950f8d888321
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/017-qmb-execution-ports'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/018-qmb-data-management' 12858d88ca3dbc848a65d9994bcd7001f11c2985
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/018-qmb-data-management'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/019-qmb-reports' a3492ae54fd4877e5804fd4c5f1925f98b807435
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/019-qmb-reports'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/020-qmb-sweeps' 65f214d0b2b758c3c56ae37fdcbf905450eedd90
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/020-qmb-sweeps'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/021-qmb-optimization' 6b56efcb2a75a2bbef408e3922b5a4cc60350fd1
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/021-qmb-optimization'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/022-qmb-robustness' 77ab7663e304f54ebb348f8822fbdffb22ce6663
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/022-qmb-robustness'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/023-qmb-synthetic-data' 2c8d4957ef29eacf5ca87fdc09598128f6c78d5b
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/023-qmb-synthetic-data'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/024-qmn-broker-boundary' a6b2bca3550fca710fa2f895feac3c6042c30a8c
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/024-qmn-broker-boundary'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/025-qmn-vps-host' b03db49933a4f6260db6c4a49f1a3a9988e38873
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/025-qmn-vps-host'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/026-qmn-capital-protection' 6f9c135d975d1fb07b418e0d400879d43fe73358
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/026-qmn-capital-protection'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/027-qmn-evidence-replay' ca3c6695664cd6f64186b222c252d6acf64d50ac
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/027-qmn-evidence-replay'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/028-qmn-paper-milestone' 7f9d936c4e9124b4e3604c363ccf3e76e8f95da3
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/028-qmn-paper-milestone'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/030-qmn-mis-training' d28a874714f374f0ba4796fe468a8d6feb809df8
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/030-qmn-mis-training'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/031-connect-fx-paper' f1a9f2ef90f178a44d02aa981323e9cd1bff59e2
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/031-connect-fx-paper'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/032-qma-continuation' 6754d755a69cf5c4dcf7bf157f461e62db2158be
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/032-qma-continuation'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/033-qmb-cli-coverage' 29e3186f6880aa33da5471af15cd9a6758a97f96
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/033-qmb-cli-coverage'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/034-qmb-library' dabdb66720089287c261c2e65bf93cc0f2dc5cda
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/034-qmb-library'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/035-honest-whatif' 96e45112af86d3306215c7e8635b5262caf453d3
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/035-honest-whatif'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/036-qma-qmb-door' 0a431addae76a1b8093c094159cd4cb59666e257
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/036-qma-qmb-door'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/037-qma-procedures' 2599a6207c563d346673271970bf7f143984b8e7
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/037-qma-procedures'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/038-qml-generation' 6927ca899b57ba5d519a3ab357f5d636ece6223e
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/038-qml-generation'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/040-qma-core-seed' 6e19f52d908e9ce772466830a5387eb2f874060d
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/040-qma-core-seed'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/041-qma-wire' 4b72e994ed29de4d899bc77b8830e362bf2e96c4
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/041-qma-wire'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/042-qma-daemon-journal' d9e1b8b6996c8c5a21b19b238de077b91bad0045
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/042-qma-daemon-journal'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/043-qma-hooks-taskgraph' 3a0e96c62677fbb247b907d4cb01b28b054e91d1
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/043-qma-hooks-taskgraph'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/044-qma-model-tools' 6d5aad7f4289bb4dbfc2e1752407053b32bd78ad
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/044-qma-model-tools'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/045-qma-environments-compute' 34fd1ef46a61106ffa1e23bcc270bc273373fd0c
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/045-qma-environments-compute'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/046-qma-ledgers-mailbox' 2c2d2769bc8153e2ddba73cc9c970a8a5a0757f8
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/046-qma-ledgers-mailbox'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/047-qma-memory-knowledge' c3aa2676d321cc392628a127274cc9302588d30a
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/047-qma-memory-knowledge'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/048-qma-plugin-packs' ebc180b34b45b21fef57e54a698f9eeeb4f7234f
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/048-qma-plugin-packs'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/049-qml-research-seed' d81df5acaffa8a376e4dae7fe7157387c1b817a4
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/049-qml-research-seed'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/049-skylos-qml-quality' 8f6e366825d20517e0d155c54d010dde9e43cd83
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/049-skylos-qml-quality'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/053-contribution-hit' 580b49aeb2d2d18c2073851a1695d3429d46c3d3
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/053-contribution-hit'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/054-invocation-envelope' cce9c8215adf0f948bbc69c1ad336d44d384fd83
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/054-invocation-envelope'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/055-product-session' a409a1884eb86a06077fc233f23f17e49b084e35
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/055-product-session'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/056-graph-dag' 30ba525a1c64adcde91e12e50ab57038d55440ae
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/056-graph-dag'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/057-task-graph-outbox' 27fc183124f21d992864724e828f542232f20fbf
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/057-task-graph-outbox'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/058-honesty-fixtures' e99d4e99f0183520dcc16579164473f3e96dd2fe
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/058-honesty-fixtures'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/058-skylos-d222' 2e2349927a0a979c3941c1ad11017b4955b13c85
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/058-skylos-d222'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/059-safety-fixtures' 34c148be404a375cbfd79fd4ce6997452e4f1d20
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/059-safety-fixtures'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/060-host-sdk' 7223e1a673b7986cf1ed06a0ae163efba2015491
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/060-host-sdk'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/061-diagnosis-json-lines' 10ea659ef3925c8a593d25dc5a6ce92d8a4ea261
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/061-diagnosis-json-lines'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/062-host-retry' 23c4fcfce97e2f745e908f60903b6c1658da1554
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/062-host-retry'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/063-nested-mission' b835eab4e11dc5facbb7e3ed96e7a93692b5a7f8
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/063-nested-mission'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/064-listing-health' 4845a328b47d92b29eb8b28dbf3ead0b647ff8c2
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/064-listing-health'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/065-kit-journey-fixtures' 7b65732fc03683476c3221889d62d23ae8ccf88e
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/065-kit-journey-fixtures'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/067-host-lifecycle' b625cebe57b9db55a16a57fc2fc7f8e3c77fc103
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/067-host-lifecycle'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/068-pairing' 6fbe6c2dca119270ea43331d25ac713926bb3949
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/068-pairing'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/epic/069-mailbox-session' 49e72693f7b8b33bbb995b410bbd5ec501e14999
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.epic/069-mailbox-session'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/fix/qa-round-1' ef9bb253fc87ec3a66d5c6a78f3cb95bb45c760c
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.fix/qa-round-1'
# A missing branch config section is harmless.
git update-ref -d 'refs/heads/park/skylos-mill-2026-09-26' a2e8cf83bc01cb17fefc57647fcf96459218f158
if ($LASTEXITCODE -ne 0) { throw 'Branch changed; stop' }
git config --remove-section 'branch.park/skylos-mill-2026-09-26'
# A missing branch config section is harmless.
git push --force-with-lease=refs/heads/chore/skylos-d325-proto-test:9beac11634ac4587c01c209003729a3da640a16d origin ':refs/heads/chore/skylos-d325-proto-test'
git push --force-with-lease=refs/heads/chunk/skylos-60-gate:a2e8cf83bc01cb17fefc57647fcf96459218f158 origin ':refs/heads/chunk/skylos-60-gate'
git push --force-with-lease=refs/heads/epic/009-qmf-structure:d219f7a74019e5ec1d778231a06147b5d5dc7754 origin ':refs/heads/epic/009-qmf-structure'
git push --force-with-lease=refs/heads/epic/067-host-lifecycle:b625cebe57b9db55a16a57fc2fc7f8e3c77fc103 origin ':refs/heads/epic/067-host-lifecycle'
git push --force-with-lease=refs/heads/epic/068-pairing:6fbe6c2dca119270ea43331d25ac713926bb3949 origin ':refs/heads/epic/068-pairing'
git push --force-with-lease=refs/heads/epic/069-mailbox-session:49e72693f7b8b33bbb995b410bbd5ec501e14999 origin ':refs/heads/epic/069-mailbox-session'
git push --force-with-lease=refs/heads/fix/qa-round-1:ef9bb253fc87ec3a66d5c6a78f3cb95bb45c760c origin ':refs/heads/fix/qa-round-1'
git push --force-with-lease=refs/heads/park/skylos-mill-2026-09-26:a2e8cf83bc01cb17fefc57647fcf96459218f158 origin ':refs/heads/park/skylos-mill-2026-09-26'
```

Close superseded PRs after preserving their branch tips:

```powershell
gh pr close 20 --repo MubarakHimself/QMX
gh pr close 21 --repo MubarakHimself/QMX
gh pr close 22 --repo MubarakHimself/QMX
gh pr close 23 --repo MubarakHimself/QMX
gh pr close 24 --repo MubarakHimself/QMX
```

No cleanup commands for protected branches, checked-out branches, recovery/backup repositories, worktrees, or other open PRs.

### Found, not fixed

- Dirty worktrees are retained above; their changes and ignored data require owner review.
- Factory enforcement PRs #9 and #10 remain open; deciding their place in the rebuild is outside P03.
- Recovery/backup refs have an independent history/object database. Cross-repository ancestry is measured above; retain all of them pending recovery ownership review.
- Backup branch/bundle tips match; a full restore test is outside this packet.

### Validation

- PASS: report has one row for all 202 non-symbolic branch refs across the three repositories.
- PASS: report has all 55 registered worktree entries and all 17 PRs returned by the required 100-result query.
- PASS: all 5 Codex worktree directories accounted for; backup bundle matches 24 backup branch tips.
- PASS: protected branches are keep; every unmerged QMX branch recommended for removal has an exact-tip archive tag command.
- No runtime/test commands are specified by P03. This documentation-only packet changes no application behavior; Reticle is not applicable.
