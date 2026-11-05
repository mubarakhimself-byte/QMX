"""A8 lane 4, the check after the chat: the throwaway folder's Library holds a unit draft that
trades XAUUSD only and checks with zero errors, and no `bot` or `strategy` item.

Run it after the chat has ended and the host has stopped, so this process may open the store.
Usage: python owner-lane4-verify.py <the throwaway QMX folder the chat ran on>
Prints one PASS or FAIL line per check and exits 1 on any FAIL.
"""

import sys
from pathlib import Path

from qmx_control.library import OPERATOR
from qmx_control.service import ControlService
from qmx_library.principal import MAIN, drafts_ref
from qmx_tools.unit_check import checked

root = Path(sys.argv[1]).resolve()
assert root.as_posix().startswith("D:/QMX-worktrees/unit-ship/homes/"), root
control = ControlService(root)
store = control.library.store
db = store.catalog.db
kinds = dict(db.execute("SELECT kind, count(*) FROM objects GROUP BY kind").fetchall())
print(f"kinds in the Library: {kinds}")
failed = 0
ok = not {"bot", "strategy"} & set(kinds)
failed += not ok
print(f"{'PASS' if ok else 'FAIL'} no bot or strategy item was written")
drafts = []
for (item,) in db.execute("SELECT DISTINCT item FROM objects WHERE kind = 'unit'").fetchall():
    head = store.head(item, drafts_ref(item))
    if head is None:
        continue
    fields = store.get(OPERATOR, head[0]).fields
    markets = [m.get("instrument_ref", {}).get("symbol") for m in fields.get("markets", [])]
    result = checked(store, fields)
    on_main = store.head(item, MAIN) is not None
    print(f"draft {item}: markets {markets}, errors {result['counts']['errors']}, main {on_main}")
    drafts.append((markets, result["counts"]["errors"], on_main))
ok = any(m == ["XAUUSD"] and e == 0 and not main for m, e, main in drafts)
failed += not ok
print(f"{'PASS' if ok else 'FAIL'} a unit draft trades XAUUSD only and checks with zero errors")
control.close()
sys.exit(1 if failed else 0)
