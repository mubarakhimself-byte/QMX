# Independent Sol review — partial financing

Candidate `784c75c7f2a3c9f64335e5c40088ee62c538dd19`. **Changes required: financing cash-to-cost sign.** Independent Book suite passes24 tests; passing fixture assertions do not establish correct signed economics.

Actual quantity2 of planned5 is exposed before entry terminalization. Its declared rollover emits one CT13 financing event, a repeated identical frontier emits no additional row, and the recorded stop terminalizes/rebases and closes actual quantity2. Closed/recovered positions retain one financing cost and one rollover fingerprint. The one-line marker preservation change is correct.

Held-out production/recovery trace `/tmp/review_finance.py` reads gross PnL -200 USD, commission cost+4 USD and financing amount -200 at scale2, i.e. signed cashflow **-2 USD**. Current financing bridge copies that signed cashflow into CostComponent unchanged; CT29 `net_realized_pnl()` subtracts costs. The actual resulting net is **-202 USD**, R **-101/100**, crediting the debit. Correct economics are **-206 USD**, R **-103/100** with frozen actual R200 USD. Preserve signed CT13 cashflow, but convert it to the opposite signed cost at the financing/CostComponent bridge; positive cash credits must likewise reduce cost. Keep recovery sign/identity consistency. The owner test recomputes the same subtraction loop, so its assertion mirrors the defect.

Findings and exact script sent to root/data. Independent command `.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_book_handler.py` passed24. No product edits. No full economic acceptance.
