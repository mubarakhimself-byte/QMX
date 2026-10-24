# cTrader premise probes

The three premise probes of DATA-PLAN's PRB-CT (P-CTSCOPE, P-CTREFRESH, P-CT2CONN), engine AD-28 and AD-67, ruling 135. They run on a demo account after his one demo sign-in (gates G-LAND and G-CT), on the app's home as the `qmx` user, except P-CT2CONN's `hold` run, which runs on the PC. Logs go in the store's `evidence/prb-ct/` as `prb-ct-<slug>.log`.

The scripts were written in WU8 and have not run against cTrader. Each has a `--dry-run` that parses its inputs and exits with no network call.

| Probe | Verdict | Numbers | Fallback it triggers |
| --- | --- | --- | --- |
| P-CTSCOPE | not run | The demo grant's `permissionScope` from the account list, the accounts it lists and whether any is live; the MT5 investor login's `trade_allowed` if `--mt5-ref` is given; a Binance key's API restrictions if `--exchange-ref` is given. A half that does not run reads `not run` and its credential is labelled `trade`. | A credential that can trade is never labelled `read`; DR5A and DR5B label it `trade`. |
| P-CTREFRESH | not run | Whether the refreshed pair reads, whether the old access token is refused, the milliseconds for one refresh and reopen, and, with a second sign-in, whether the first grant still reads. | DR5B is skipped and parked, cTrader reads keep today's short sessions, and the finding goes to `QUESTIONS-FOR-OPERATOR.md`. |
| P-CT2CONN | not run | The `hold` run's unasked messages and whether its socket dropped; the `second` run's application auth answer (accepted, or refused with its error code). | When the first connection dies with no event, DR5B's health walk gains a liveness read every check, and the case becomes one of DR5B's lanes. |

## The facts DR5B's adapter declaration reads

Filled in from the rows above when the probes run.

- The read app's demo grant scope: not run.
- Whether a refresh kills the old pair at once: not run.
- Whether a second grant under the same app revokes the first: not run.
- Whether a second connection under the same app is refused or drops the first: not run.

## Order of the runs

1. `p_ctscope.py` on the server: `--home <server home> --machine contabo --protocol <pb> --tag <tag>`.
2. `p_ct2conn.py --role hold` on the PC, then, within its listen window, `p_ct2conn.py --role second` on the server.
3. `p_ctrefresh.py` on the server last, because it rotates the grant's pair.

## Departure

DATA-PLAN's P-CTSCOPE sends one minimum-size market order on the demo account and expects a refusal. This script sends no order. It reads the grant's `permissionScope` from cTrader's own account-list answer instead, because the wrap-up brief bars any code that submits an order and the broker transport admits only sign-in and read requests.
