# How a QMX checkpoint is reviewed

There is no AI reviewer per slice. Scripts gate each slice: files inside the brief, the `TRACE:` line, the brief's facts, lint, types, touched tests, fail-at-parent, Vulture and Skylos with no new finding, and the SAFETY fact at the head. All AI review happens here, in the checkpoint review session, every 5 to 8 slices. So the blockers below cover what a slice reviewer used to judge as well as what only a whole batch shows.

Every reader reads this file, `PROJECT-RULES.md` and its prompt, and follows `skills/slice-review/SKILL.md`, the method for applying this file. Where they differ, this file wins.

## What failure looks like in QMX

- An exit blocked, delayed or made to depend on something it must not read.
- Money reached: an agent path to orders, promotion, kill levels or the floor; a binary float on a quantity, price, P&L or balance; a key read or printed.
- A brake that closes a trade, or a brake that fails open.
- A part on a fixed line's path that fails, and the fixed line quietly breaks. Four of the six high bugs of 12 November were this shape.
- Two slices that use one word, value or contract for two things.
- A test that cannot fail: it passes at the parent, asserts nothing a user would see, drives only the working path, or leans on a fake kinder than the real neighbour.
- A value moved without its tests, pins, counts or census rows.
- Code that serves no ask, or rebuilds something a removed row says is gone.
- A record that lies: a ledger, report or verdict that says CLEAN while a finding stands.

## Blockers

A finding blocks only when it is one of these. Tag it **Important**.

1. A red check: a FAIL line in a slice's `checks/<id>/<head8>/summary.txt`, in the deep run (`ship nightly`), or in `ship quality`.
2. The brief not met: a done-line item with no evidence at the tip, a brief literal not asserted, or a plan line ("what is true when done") that a run at the tip shows false.
3. A test that cannot fail.
4. A change the brief's files do not cover: a caller, pin, count or census row that should have moved and did not, or behaviour placed in a listed file that belongs elsewhere.
5. A broken fixed line (exits, the kill switch, agents reaching money, keys), a cell of the fault walk that ends in a failure, or a self-recovery promise in the architecture's `## Operations` with no test or probe that proves it.
6. Scope creep or a rebuilt removal: a commit with no chain, code that serves no `SCOPE.md` ask, or code that rebuilds a removed row (`REMOVED.md` in the program, or `C:/Users/Mubarak/Desktop/QMX/tracker/REMOVED.md`).
7. Slices that disagree: two slices give one value, word, contract or registry two meanings, or a test passes only because a neighbour is faked.
8. A diff too large to follow: you cannot trace each changed line to a brief.

**Severity rule.** A proved finding on exits, brakes, the kill switch, money or keys is Important, never a Nit. Two of the six high bugs were filed as lows; this rule exists so that cannot happen again.

## The fault kinds

The fixed-line fault walk asks each of these of every part on a fixed line's path. The list grows when a review finds a new kind.

1. It raises.
2. It returns an extreme but allowed value.
3. It is missing or quiet (no data, no reply, a quiet minute).
4. The host fails between two of its steps.
5. It restarts halfway.

Each cell ends one of three ways: a named test in the scenario ledger passes, a probe run at the tip shows the line holds, or it is an Important finding.

## Tags

- **Important.** One of the blockers above. Blocks the merge.
- **Nit.** Anything else the checkpoint introduced that changes behaviour, safety or what the next builder must understand. Never blocks. Style (formatting, naming taste, comment wording, anything a linter owns) and the wording of evidence files and PR bodies are not findings.
- **Pre-existing.** A flaw or red the checkpoint did not introduce, including quality findings already in the baseline and unfinished work a later checkpoint fills in. Never blocks; it goes to the next plan.

Every finding names a file and line (`qml/src/qml/fold.py:88`) and the evidence: the command you ran at the tip and its output, or the quoted line. An Important needs a run at the tip wherever a run is cheap. A finding without proof is dropped.

If a finding would recur, add a line under "Fix at the source": the lint rule, script check or `PROJECT-RULES.md` line that would catch it.

## Findings first, then one fix batch

Readers only collect. Nobody fixes anything while the review runs. When every reader is done and the deep run has finished, the session writes one verdict. Every Important becomes a slice of one fix batch, each brief citing the chain ids it repairs and starting with a test that fails on the finding.

## Round 2

Round 2 reads round 1's verdict, the fix batch's run report and the fix diff. It judges only two things: is each round-1 Important fixed (rerun its evidence at the new tip), and does the fix diff add a new Important. Code round 1 passed is not reopened. There is no third round.

## The verdict file

The session writes it to the path its prompt gives. Shape:

```
# Review of checkpoint <X> at <tip8>, round <n>

<count first: "2 Important, 1 Nit, 0 Pre-existing." or "Nothing needs fixing.">

## Important
- I1 <file>:<line> <what is wrong> (blocker <number>; chain <ids>). Evidence: <command and output, or quoted line>.

## Nits
- N1 <file>:<line> <what>. Evidence: <...>.

## Pre-existing
- P1 <file>:<line> <what>. Evidence: <...>.

## Deep run
<ship nightly and ship quality lines, and "Linux: not run" until CI runs it>

## Builder decisions
<each DECISION line: cleared ("the builder decided X because Y"), Important, or listed for him with a recommendation>

## Walks
<each walk, one line: what it covered and its result>

## Fix at the source
<lint, script or rule line, or "none">

VERDICT: <CLEAN or BLOCKED>
END <full 40-character tip sha> checkpoint-<X>-round-<n>
```

- `VERDICT: BLOCKED` when any Important stands or the deep run has a new red; else `VERDICT: CLEAN`. That line appears once in the file and nowhere else, not even as a quote.
- The last non-blank line is the END line, with the full tip sha. Write it last.
- Empty sections say "none".
