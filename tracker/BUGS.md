# QMX bug list

One list for every session. Add a line when you find a bug. Don't fix another session's bug mid-run: write it here, and the session that owns triage sends it to the right build.

Each entry says what goes wrong for him, how to repeat it, the evidence, and how sure we are. Level 2 means the line was read, level 3 means the case was walked through the code, and level 4 means it was run.

## Open

### B-001: the test trade's exit price is its stop price, not the real close (CONFIRMED)

- **Confirmed 9 November against cTrader's own history.** His cTrader app's history for the USD demo account (`10105809` in his app, `48481513` in the Open API) shows EURUSD Buy 0.01 lot, entry 1.12188, closing price **1.12187**, closed at 22:44:35.857, net -0.07 USD. The node reported exit **1.11688**, which is the stop price. The close itself was right, and the price QMX recorded for it is wrong. Level 4 now.

- **What goes wrong for him.** The node's demo test trade reports `exit` equal to its stop price. If the close price is recorded wrongly here, it may be wrong in his trade records too.
- **Evidence.** First real start, 9 November, account `48481513`, run log `D:/QMX-worktrees/first-start/run-20261109-224420.log`: `entry 1.12188, stop 1.11688, exit 1.11688`. The stop sat 50 points below entry and the whole run took 28.8 s, so the stop is unlikely to have been hit. `exit` comes from `CTraderVenue.test_trade` (`qmn/src/qmn/venue/ctrader_account.py:1753`, `exit=done.price`, from `self.closed(name)`).
- **How to confirm.** In his cTrader app, open that account's history and read the close price of the EURUSD trade at about 22:44 local on 9 November. If it is not 1.11688, the node reads the wrong price. Then trace `closed()`.
- **Level.** 4, confirmed against cTrader's history (see above).
- **Cause, read in the code (level 3).** When the close event arrives, `qmn/src/qmn/venue/ctrader_account.py:1424-1427` reads the price from `deal.executionPrice`. If it can't read it, it falls back without saying so: `price = held.stop or held.entry`. Here it fell back, so the stop price was written as the close price. This was not latency: latency moves a price by a point or two, and the gap here, 0.00499, is exactly the stop distance. Two things to find: why `executionPrice` was not read from cTrader's close event, and whether the silent fallback should be a named "close price unknown" instead. Real trades go through the same path, so this affects his real records, not only the test.

### B-002: when already signed in, the first-start check lists no accounts

- **What goes wrong for him.** With two demo accounts and a grant already held, `tools/first_real_start.py` fails with `name one demo account with --account; cTrader lists []`, so he cannot see which numbers to give.
- **Evidence.** Run log `run-20261109-224010.log`. The code path is `_sign_in` (a held grant lists none) and then `_account_to_bind` in `tools/first_real_start.py`.
- **Fix direction.** List the held grant's accounts from the node.
- **Level.** 4, it ran.

### B-003: the check shows cTrader's internal account IDs, not the numbers his app shows

- **What goes wrong for him.** It names `47038115` and `48481513`, which are Open API `ctidTraderAccountId`s. His cTrader app shows `traderLogin` (`9984338`, `10105809`), so he cannot tell the accounts apart. The node already keeps both (`GrantAccount.login` in `qmn/src/qmn/app/grants.py`).
- **Fix direction.** Show the app's number, the broker, and demo or live, and let him pick from a list.
- **Level.** 4, it ran. cTrader's docs confirm the two numbers have no formula between them.

### B-004: the app secret prompt shows nothing as he types

- **What goes wrong for him.** `getpass` in `tools/first_real_start.py` shows no characters, so he cannot tell whether his paste landed. He wants asterisks.
- **Level.** 4, it ran. This is a usability bug, for the installer work.

## Fixed

(none yet)
