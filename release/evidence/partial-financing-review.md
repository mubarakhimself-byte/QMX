# Independent Sol review — partial financing

Candidate `784c75c7f2a3c9f64335e5c40088ee62c538dd19`. **Changes required: financing cash-to-cost sign.** Independent Book suite passes24 tests; passing fixture assertions do not establish correct signed economics.

Actual quantity2 of planned5 is exposed before entry terminalization. Its declared rollover emits one CT13 financing event, a repeated identical frontier emits no additional row, and the recorded stop terminalizes/rebases and closes actual quantity2. Closed/recovered positions retain one financing cost and one rollover fingerprint. The one-line marker preservation change is correct.

Held-out production/recovery trace `/tmp/review_finance.py` reads gross PnL -200 USD, commission cost+4 USD and financing amount -200 at scale2, i.e. signed cashflow **-2 USD**. Current financing bridge copies that signed cashflow into CostComponent unchanged; CT29 `net_realized_pnl()` subtracts costs. The actual resulting net is **-202 USD**, R **-101/100**, crediting the debit. Correct economics are **-206 USD**, R **-103/100** with frozen actual R200 USD. Preserve signed CT13 cashflow, but convert it to the opposite signed cost at the financing/CostComponent bridge; positive cash credits must likewise reduce cost. Keep recovery sign/identity consistency. The owner test recomputes the same subtraction loop, so its assertion mirrors the defect.

Findings and exact script sent to root/data. Independent command `.venv/bin/python -m pytest -q -p no:cacheprovider qmb/tests/test_book_handler.py` passed24. No product edits. No full economic acceptance.

# Corrective bounded approval — `80647b977f6e2fe40923ca9279295f60d3a3d53b`

Independent actual partial-exposure/stop/recovery debit and credit traces now establish the correct signs. Gross -200 USD plus commission4 USD and signed cash debit-2 USD produces cost+2, net **-206 USD**, R **-103/100**. Signed cash credit+2 USD produces cost-2, net **-202 USD**, R **-101/100**. The physical CT13 financing event retains original signed cash (-2/+2); only the Book subtractive cost is inverted. Recovery uses the same conversion, and the closed/reopened position retains one financing cost/date. The repeated rollover frontier produces no extra transition. Conversion happens before journaling/memory advancement, and mismatched signed amount or foreign-currency cash/component pairs refuse.

`/tmp/review_finance_corrected.py` invokes both actual fixture cases, independently reads physical CT13 and recovered CT29 amounts, and probes sign/currency mismatch. Independent Book suite passes **25**. This approves the bounded correction; earlier public resolved-source/request identity blockers remain separate. No product source changes.
