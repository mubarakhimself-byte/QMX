# Review: adversary lens (configured reviewer 2)

Part A, 31 Oct 2026. The `bmad-architecture` configured lens: "construct two units one level down that each obey every AD to the letter yet still build incompatibly". Run by the part's author in sequence after the spine was written (the brief bars sub-agents; the reviewer gate's fallback is to run each lens in sequence and write its file first). Every pair found was closed in the spine before this file was written; the fix is named.

**Verdict.** Five holes found, all closed; none left open.

| # | Two builders who obey every AD and still diverge | Hole | Fix applied |
| --- | --- | --- | --- |
| 1 | QMB's runner (Part B) feeds `own_journal` with every closed trade of the run; the node (Part C) feeds every paper and live trade the unit ever closed on that account | the calibrator sees different trade sets in replay and live, so `min_trend_strength` moves differently and L0 AD-5 breaks | AD-103 and `CONTRACTS.md` §4.5: the calibrator's sufficient statistics live in the unit state; hosts feed only the trades the hosted unit closed in its own run or deployment after the starting watermark; the deployment carries the starting state (LC-A1-23) |
| 2 | This PC compiles with the default port quantum; a server's settings carry another quantum; both get the same compiled fingerprint | decisions can differ under one fingerprint, so the node's "fingerprint equals tested" rule (L0 AD-38) proves nothing | AD-106: compiler options that can change a decision enter the compiled fingerprint; the trace level does not (LC-A1-10) |
| 3 | The host writes his "resume" click with This PC's clock; the node writes a later risk stop with its own clock, which runs 400 ms behind | ordering by time lets the earlier click clear the later stop, which breaks standing order 7 | AD-115 and §8: a move out of `stopped` names the stop it clears; the fold applies it only when it names the latest stop (LC-A1-25) |
| 4 | Part B's judge diffs two documents with its own code to count tries; the Lab diffs them with its own | two "is this a new unit" answers, the failure L0 AD-23 exists to stop | AD-115: the judge and the Lab call `qml.identity.classify`; the table is one setting |
| 5 | QMB numbers decision rows from 1 per run; the node numbers them from 1 per deployment; a unit runs on two accounts | journal ids collide across deployments and reruns write new ids | AD-107 and §4.2: row ids are fp1 over the host's scope id, the instant and the ordinal (LC-A1-24) |

**Checked and held.**
- Two checker doors with different entry snapshots: pins resolve exactly, so the verdict cannot differ; only the "nearest" hints may (AD-110).
- Two hosts computing the compiled fingerprint: one function in QML (AD-106), and records are not an input, so a broker spec change is Part C's stand-down, not a silent fingerprint change.
- Two loaders: impossible by L0 AD-47 and AD-109; the scan bans `exec` and `importlib` in agent blocks.
- Two data-level vocabularies (this part's and Part C's records): named as contract change 6 in `CONTRACTS.md`; R1 checks that Part C uses `qmx.data-level/1`.
