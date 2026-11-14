---
name: slice-review
description: Read part of a QMX checkpoint and write proved findings to a notes file. Used by every reader the checkpoint review spawns (an element reader, the chain reader, the fault walk, the operations walk). Passes collect candidates, a proof pass at the tip keeps or drops each one, and triage tags what survives as Important, Nit or Pre-existing. Use when a checkpoint review brief names a checkpoint, a tip, a map and a notes path.
---

# Checkpoint reading

You decide one thing for your part of the checkpoint: what stops it merging, with proof. No AI read these slices before they landed, so you judge inside each slice as well as across them. Everything else you write must help him at no cost to the run.

The standard lives in two files in the standing folder, two levels above this skill. `REVIEW.md` holds what failure looks like, the blockers, the severity rule, the fault kinds, the tags and the verdict shape. `PROJECT-RULES.md` holds the fixed lines and the traps. This skill is the method. Where they differ, `REVIEW.md` wins.

## Words

- **Candidate.** Something a pass noticed. It lives in your ledger and never reaches your notes as it is.
- **Finding.** A candidate that survived the proof pass. Only findings reach your notes.
- **Proof.** The `file:line` at the tip with the quoted line, plus the output of a command you ran at the tip wherever a run is cheap. An Important needs the run.
- **Ledger.** Your working list in context. One row per candidate: the pass that raised it, the claim, and its state (open, proved or dropped).
- **Check folder.** The detached checkout at the tip that your brief names. Run everything there.
- **Notes file.** The path your brief gives. Write to it as you go, so a rerun after a power cut can skip what is done. Its last line is `DONE` only when you have finished.

Zero findings is a normal result. Report what the proof supports.

## Step 0: Load and state the intent

1. Read what your brief lists: `REVIEW.md`, `PROJECT-RULES.md`, the map (`MAP.md`), and for each slice in your part its brief, its chain packet (`CHAIN.md`), its landed diff and its checks summary.
2. Write for yourself one paragraph per slice: what it must make true (brief sections 1 and 5, and the plan lines its `Chain:` cites) and the one fact it is safe because of (section 8).
3. List the section 5 items, section 6 test rows, section 7 must-nots, section 7a edge cases and section 9 done-lines.
4. List the seams in your part: every value, word, contract, registry, element, edge case or file that two slices share.

Done when the intent paragraphs and the lists exist. The scripts already proved some things: files inside the brief, the `TRACE:` line, lint, types, touched tests, fail-at-parent, Vulture and Skylos with no new finding, and the SAFETY fact at each slice head. Read their output and build on it.

## The passes

Run them in order, one at a time, each to its done line. A pass only adds candidates to the ledger. Proof and tags come later. A walk your brief names (the chain walk, the fault walk, the operations walk) replaces the passes below with the steps `STOP-REVIEW.md` gives it, and still uses this skill's proof pass, triage and notes.

### Pass 1: Correctness and blast radius

For each symbol your slices add, change or delete:

1. Say what it now does differently, including what the diff does not spell out.
2. Find every caller and reader at the tip with `git -C <check folder> grep -n`. Then look where grep stops: JSON and wire shapes, stored columns, config keys, a census or pinned count, another package reading the same bytes, and tests that pin a moved value.
3. For deleted or replaced code, ask whether it carried a contract the change neither re-establishes nor retires on purpose, and whether it rebuilds a removed row.
4. Check each fixed line and trap in `PROJECT-RULES.md` the diff comes near: exits, money arithmetic, agent paths toward money, keys, dependency direction, censuses and counts, `COMPILER_FORMAT_VERSION`, app version bumps.

Done when every caller of every changed symbol is marked fine or has a candidate.

### Pass 2: Tests that cannot fail

Load the `principle-test-behavior-not-implementation` skill. For each test your slices add or change, and each section 6 row and 7a edge case:

- Apply its undefined check and its five shapes.
- Read that test's fail-at-parent line in the checks summary. Only a failed assertion counts.
- Does each scenario test drive the failure (the part raises, returns an extreme value, goes quiet, the host stops halfway), or only the working path? Only the working path is a candidate.
- Compare every fake with the real neighbour it replaces. A kinder fake is a candidate, and so is a test that passes only because the neighbouring slice's code is faked.

Then work the other way. For each behaviour pass 1 found changed, name the smallest realistic regression at its nearest consumer: flip the branch, drop the default, omit the field. Find the test whose assertion would fail on it. Search by symbol and by import before you claim none exists.

Done when every changed test, section 6 row and edge case has a judgement, and every changed behaviour has a test that would fail or a candidate.

### Pass 3: Scope and the seams

1. Trace every changed hunk to a section 5 item and its ask. A hunk that serves neither is a candidate for blocker 6.
2. For each section 5 item and done-line, find the code and the test that meet it at the tip. A brief literal no test asserts is a candidate.
3. Confirm each section 7 must-not is untouched.
4. For each seam from step 0: do the slices agree on its meaning, value and contract at the tip? One word for two things (a `flatten` brake that never refuses entries while the fold says HALTED) is a candidate for blocker 7.
5. If you cannot trace each changed line to a brief, that is blocker 8.

Done when every hunk is traced or has a candidate, and every seam is agreed or has a candidate.

### Pass 4: Edge cases and the operations layer

1. For each edge case, walk the changed code path with its inputs and state. Does the code handle it? Does a test run it, and does that test pass at the tip (the scenario ledger in the map)? Each no is a candidate.
2. Where the diff special-cases some members of a fixed set (an enum, a status, a reason code, a flag), treat each other member as a scenario too.
3. Check the operations layer each brief's `Operations:` line promises: logging, monitoring, self-recovery (health check, retry or restart, safe fallback, an alarm when recovery fails). A self-recovery promise with no test or probe is a candidate for blocker 5.

Done when every edge case, implicit branch and operations promise is handled and tested, or has a candidate.

## The proof pass

Take each open candidate in ledger order:

1. Open the code at the tip, not the diff hunk. Read enough around it to judge reachability: the call sites, guards and validation outside the hunk.
2. Write the claim as an observable: what a command would print if the candidate is real.
3. Prove it at the cheapest level that settles it, at the tip.
   - Quote the `file:line`. Every finding needs this.
   - When the claim is about behaviour, run it through the wrapper in one shell call: `cd <check folder>/<package root> && python {SHIP} timed --program {PROGRAM} --slice review-{STOP} --log {PROGRAM}/stop-review/{STOP}/runs/<name>.log --timeout 600 -- uv run --no-sync <command>`. Read the log.
   - For "this test cannot fail", replace the subject in memory and run the one test through the wrapper:
     `python -c "import pytest, <pkg>.<mod> as m; hits = []; m.<fn> = lambda *a, **k: hits.append(1); rc = pytest.main(['-q', '-p', 'no:cacheprovider', '<test file>::<test name>']); print('mutant calls', len(hits), 'pytest rc', int(rc))"`
     `mutant calls` of 1 or more with `pytest rc 0` proves the test passes with its subject returning nothing. `mutant calls 0` means the patch missed: patch the name where the test's door imports it, and run again.
   - For a fault walk cell, make the part fail in memory the same way (raise, return the extreme value, return nothing) and run the scenario that crosses the fixed line.
   - For "this was there before the checkpoint", run `git -C <check folder> blame -L <n>,<n> <tip> -- <path>` and confirm the commit is an ancestor of the checkpoint's start (`git merge-base --is-ancestor <commit> <from>`).
4. Mark the candidate proved, keeping the command and output. Otherwise mark it dropped: the run disagrees, the code handles it outside the hunk, or nothing you can run or quote shows it.

Merge candidates that make the same claim and need the same fix. Done when no candidate is open.

## Triage

Tag each proved finding once, in this order:

1. **Pre-existing.** It was true before the checkpoint started, shown by blame or by the same line at the start commit. Also unfinished work a later checkpoint fills in, reds in `baseline-reds.txt`, and quality findings in the baseline.
2. **Important.** The checkpoint introduced it, and its proof matches the words of a blocker in `REVIEW.md`. Name the blocker and the chain ids it touches. The severity rule applies: a proved finding on exits, brakes, the kill switch, money or keys is Important, never a Nit.
3. **Nit.** The checkpoint introduced it, and it changes behaviour, safety, or what the next builder must understand. Style and paperwork are not findings.

A finding that would recur also gets a line under "Fix at the source".

## Write your notes

Write the notes file in this shape, then the line `DONE` last:

```
# <reader name>, checkpoint <X> at <tip8>

<count first: "2 Important, 1 Nit, 0 Pre-existing." or "Nothing needs fixing.">

## Important
- I1 <file>:<line> <what is wrong> (blocker <number>; chain <ids>). Evidence: <command and output>.

## Nits
- N1 <file>:<line> <what>. Evidence: <...>.

## Pre-existing
- P1 <file>:<line> <what>. Evidence: <...>.

## Covered
<what you read and checked, one line per slice, seam, plan line or fault-walk cell, so "none found" can be trusted>

## Fix at the source
<lint, script or rule line, or "none">

DONE
```

You fix nothing and write no verdict. The session collects every reader's notes and writes the one verdict.

## Stop

The reading ends when the passes (or your walk) have met their done lines, the ledger holds no open candidate, and every finding has a tag. Then write `DONE` and send the reply your brief asks for: the notes path and the counts.
