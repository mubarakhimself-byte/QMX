# Adversary lens — two units that obey every AD and still build incompatibly

Verdict: **five holes found; four closed by tightened ADs, one surfaced as a conflict with a parent.**

| # | Attack | Hole | Closed by |
| --- | --- | --- | --- |
| 1 | Unit A (Strategies bench) compiles setups with the Book/BMS it finds on the bot; unit B (Pods bench) compiles pods to fragments. A bot with no pod yet gets a setup that QMB refuses (no Book) or a silent workspace default. | AD-5 named no default composition | AD-5 now: the bot's `uses → pod` else `settings.lab.default_pod`; no composition, no compile |
| 2 | Unit A memoises `qmb.run` by the engine memo; unit B also memoises through `ControlService.memoized_backtest` (hp17) and the Library `memo` table. Two caches, two answers after a data release. | a second cache was possible | Conventions › Reads: the engine memo is the only Lab-level cache; QMB reproducibility is not a cache |
| 3 | Unit A (training) places `ml.train` on a Modal box with the full dataset; unit B (robustness) keeps the sealed year local. The sealed year leaks to the cloud and the family's holdout is void. | AD-8 said results are exploration-only but not that sealed data stays home | AD-8 now: remote placements get split-governed exports without the sealed segment; sealed evaluation and holdout touch run local |
| 4 | Unit A (Lab Pods) and unit B (Portfolio Pod panel) both edit pod versions; B's Save could move a trading pod to a new version that never saw a test. | AD-10 did not say who moves the stage | AD-10 now: Portfolio edits go through `pods.patch/save` and mint a `draft`; stage moves only through Lab runs |
| 5 | Unit A (Library migrator) imports CT-22 records as `pod` objects with `identity: ct06`; unit B (Lab) writes `pod` objects as stacks of blocks with `identity: manifest`. One kind, two shapes. | the Library spine's mapping rows and the UI's pod disagree | surfaced: AD-11 reads the rows as `book`/`bms` kinds; DOC-CHANGES and HEADLESS-RESULT carry the conflict for the Library agent |

Attacks that did not find a hole: two agents editing one pod (library AD-7 refs); a sweep run twice on two machines (one qmb invocation per placement, cells keyed by run-config fp1); a copilot tool not in the pack (AD-14 "not a Lab tool"); a paper run started by a template (OPEN-3 keeps MANAGE); a block that reads the clock (FM-7 purity check at save); the Runs table reading only `main` (Conventions › Reads).
