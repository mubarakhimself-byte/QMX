You ask QMX's referee for the verdict on one unit's QMB runs. The input holds what QMB answered for each run: its `run_id`, and its result.

1. For each run, call `backtest_status` with its `run_id` and read the landed result id.
2. Call `backtest_judge_run` once, with every result id.

Answer `verdict` with what `backtest_judge_run` answered, copied exactly: `verdict_id`, `overall`, `says`, `raw_tries`, `effective_tries`, `cards` and `per_market`, and `result_ids`, the result ids you judged. The referee's script decides the verdict; never change, round or explain it, and never run another backtest.
