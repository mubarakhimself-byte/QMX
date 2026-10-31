# Review: two units one level down that obey every AD and still build incompatibly

The second configured finalize reviewer of `bmad-architecture`. Run by agent A0 in sequence, 31 Oct 2026, against the first full draft of the spine. Each pair below is two Level 1 parts (or two builders) that could each follow every AD to the letter and still clash. Every hole found was closed in the spine before finalising; the AD that closes it is named.

## Verdict

**Nine holes found, nine closed.** Two more were examined and are not holes.

## Holes and how they were closed

| # | Two units that obey every AD | How they clash | Closed by |
| --- | --- | --- | --- |
| 1 | Level 1 A defines CT-23 format 3 in QML; Level 1 C defines what the node's door accepts | two shapes for one sized intent | conventions row: A defines the shape, C consumes; `01-connections.md` §5 one owner |
| 2 | The catalogue (A) defines reading cards; the MIS (C) defines its readings' cards | two card schemas | A owns the card schema; C owns the stamped readings and default packs (connections §5) |
| 3 | QMB's builder writes backtest calibration rows into the result; the journal builder writes them into partitions | two records of one run, which can disagree | AD-27, AD-35: a backtest run's unit journal lives inside its `backtest-result` |
| 4 | The QMB app's builder writes journal partitions directly; the node's builder writes through the writer library | two partition key mappings on one store | AD-27: both write only through P5's writer library, committed through the machine's market-data door (its single writer) |
| 5 | Two QMB runs land at the same moment | both update the family's try record; one update is lost | AD-25: one append-only try row per run; counts computed at read |
| 6 | The node's builder relies on the inner supervisor to heal; the mini-app core's breaker trips the app process | the app stays down until someone calls `restart`, so the node never heals itself | AD-33, AD-38: an opt-in restart with back-off per manifest, on for the node (ruling 46) |
| 7 | QMB replays a unit without the cross-unit hook; the node calls it live | research and live differ by construction (AD-5) | AD-24: the hook runs in whichever host drives the unit |
| 8 | The copilot starts a run through an `app:qmb` tool; a workflow starts one through the forwarding `backtest` row | one path lands through the core landing and counts a try; the other could land from the app | AD-34: every door lands only through the core landing; the QMB app holds no Library write grant |
| 9 | The PC compiles a unit for QMB; the node compiles the same document on a server with a different catalogue snapshot | the tested unit and the traded unit differ | AD-38: a deployment carries every pinned block; the node refuses a unit whose compiled fingerprint differs from QMB's |

## Examined and cleared

| Pair | Why it is not a hole |
| --- | --- |
| The PC's MIS instance and a trading machine's MIS instance both computing volatility state for EURUSD | AD-40: each series has one writer (key includes source and machine); the PC instance never recomputes a tier a trading machine publishes |
| Two nodes, one account, each obeying "one feed keeper per machine" | AD-8: deployments name one machine; client order ids carry the node id; reconcile refuses a foreign claimant |

## Left open, deliberately

- The node app inside the host's supervisor or as its own service (LC-A0-06): both obey every AD; the choice changes blast radius on a host crash, not compatibility.
- Per-market settings inside the unit document or as linked items (Level 1 A): the schema version step is the seam.
