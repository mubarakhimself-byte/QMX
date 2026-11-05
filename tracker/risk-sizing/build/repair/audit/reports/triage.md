# Triage of the build's old loose ends, at commit 50c83a4e

Every item has one result. A script checked that no item was missed or counted twice, and the lists came to about 1,200 items, not 1,300. It runs from D:/Temp/audit/triage/build.py.

## Counts by result

| List | fixed | duplicate | still real | not worth doing | idea | unknown | not reached | total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BACKLOG.md | 72 | 83 | 11 | 200 | 15 | 7 | 0 | 388 |
| lows.md | 17 | 38 | 7 | 512 | 0 | 0 | 0 | 574 |
| LOOSE-ENDS.md | 12 | 32 | 7 | 100 | 10 | 2 | 0 | 163 |
| IDEAS.md | 0 | 0 | 1 | 0 | 51 | 0 | 0 | 52 |
| QUESTIONS-FOR-OPERATOR.md | 10 | 3 | 0 | 4 | 7 | 0 | 0 | 24 |
| QUEUE.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| All | 111 | 156 | 26 | 816 | 83 | 9 | 0 | 1,201 |

The 26 "still real" items are nine problems, each reported several times across the lists. QUEUE.md is empty. FINDINGS.tsv was the yardstick for duplicates, so it is not counted here.

"Fixed" means I looked at the line at this commit, or the note says it rests on the earlier loose-ends audit and I did not re-read it. Most of the money and sign-in items were looked at. "Not worth doing" was mostly sorted by reading, so those 816 are a judgement, not a check.

## What matters

Nine items go forward, in findings/triage.tsv. All are graded `should`, because no verifier checks my rows. I believe the first five are worse than that.

1. triage-1. A stop moved past entry to lock in profit goes to the broker on the loss side. A long from 1.1000 tightened to 1.1020 is sent as 1.0980, and I ran the real sum. No shipped unit can send this yet, so it bites the day trailing stops are repaired (p1b-3, p1b-4). Repair them together.
2. triage-2. A backtest over any past holiday fails for a hole, because the calendars list closures for 2026 and 2027 only. Once real data reaches QMB (p0b-3), this stops most multi-year runs. That the data is empty on those days is my guess.
3. triage-3. An agent can put any record but a unit on the Library's main line with no click from him, including the instrument, venue and account records a real deploy reads as truth.
4. triage-5. Every running app writes a row to the control database four times a second for ever, and nothing deletes them. That is about a million rows a day. The build filed it as an idea. Size on disk was not measured.
5. triage-7. Once an app is installed on his folder, repairs to its own files never reach it, because nothing calls the update door. This one bears directly on the repairs ahead, from the second landing onward.
6. triage-4. The restart wait never resets, so an old crash count means a 5-minute wait on every later node crash.
7. triage-6. An agent can read a study's sealed months through journal_query. Repairing p0b-11 leaves this door open.
8. triage-8. A finished job can come back as a raw permission error under load on Windows.
9. triage-9. One bad number silently ends the log sender until the next host start.

Good news from the same lists. The three "must before he lands" items and most "must before the first real trade" items from the loose-ends audit are closed at this commit: gold prices, the vault lock, the enable hang, stale qmf code, partly filled entries, the old quote after a reconnect, the status word, and the cTrader stop amendment. Records on main are done for two markets, which is p5d-5.

## What I could not settle

One look did not settle these, so they are marked `unknown`. None is in the findings file.

- Whether Windows line endings change a unit's fingerprint enough that a server refuses the deploy (BACKLOG:270).
- Whether a node's correction to a frozen month stops the record pull from a server for good (BACKLOG:387).
- Whether This PC ever sees a node's risk stop on the unit's lifecycle (BACKLOG:401, LOOSE-ENDS F1).
- Whether a twin or foreign-position stand-down reaches him at all. It is on no push list, and I did not settle whether the morning digest names it (BACKLOG:408, :432, LOOSE-ENDS F6).
- Whether a late cTrader fill can hold one position twice (BACKLOG:480).
- Whether a position found by its label reads as a twin after a restart (BACKLOG:497).

Risk and sizing items are marked `not worth doing` for the risk session. Nothing went unreached.
