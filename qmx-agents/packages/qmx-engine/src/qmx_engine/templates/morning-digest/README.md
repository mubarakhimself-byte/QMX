# Morning digest of everything since you last looked

The morning digest of K-32. It reads the Library log from the operator's "last look" cursor, which
is one row in control (`ControlService.last_look` and `mark_looked`), and it moves that cursor only
after the digest passed and was delivered.

## What it does

1. `Where his last look ended` reads the cursor. It is a Library log position, never a clock.
2. `What landed since` reads the log's entries after that position, and the runs that finished since
   the cursor's time, with the failed ones named.
3. `Write the digest` asks the `writer` role for the opening, the lines, what moved and what needs
   him. The prompt forbids numerals: the counts are on the card beside the text.
4. `Assemble the digest` builds the card and checks every line against what the collect step saw.
5. `Move his cursor forward` advances the cursor to the position the digest read.

A failed digest stops before the cursor moves, so the next run shows the same items instead of
hiding them.

## Run it

Cron at 07:00 Europe/London, plus manual. Installing the template only suggests the schedule;
enabling it is yours. A test run with `{"fixture": true}` replays the recorded digest.
