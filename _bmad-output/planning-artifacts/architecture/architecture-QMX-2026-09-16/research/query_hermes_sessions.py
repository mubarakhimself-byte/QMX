"""Read-only probe of Hermes state.db for STRATS session IDs."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path(r"C:\Users\Mubarak\AppData\Local\hermes\state.db")
IDS = (
    "20260824_121737_86f88c",
    "20260825_115530_94412f",
    "20260826_115355_ae94f7",
    "20260826_180446_36307b",
)


def main() -> None:
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    print("TABLES")
    for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY 1"):
        print(" ", r[0])
    print("\nSCHEMA snippets")
    for name in [
        "sessions",
        "session",
        "messages",
        "message",
        "conversation_messages",
    ]:
        row = cur.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone()
        if row:
            print(row[0][:800])
            print("---")
    # Try common session id columns
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    for table in tables:
        cols = [r[1] for r in cur.execute("SELECT * FROM pragma_table_info(?)", (table,))]
        joined = " ".join(cols).lower()
        if ("session" in joined or "id" in joined) and any(
            c.lower() in {"id", "session_id", "sessionid"} for c in cols
        ):
            idcol = next(c for c in cols if c.lower() in {"session_id", "sessionid", "id"})
            # SQLite identifiers cannot be parameters. Quote names obtained from
            # sqlite_master/pragma_table_info, escaping embedded double quotes.
            table_sql = '"' + table.replace('"', '""') + '"'
            idcol_sql = '"' + idcol.replace('"', '""') + '"'
            try:
                q = (
                    f"SELECT {idcol_sql} FROM {table_sql} WHERE "  # noqa: S608 -- escaped identifiers
                    f"{idcol_sql} LIKE ? OR {idcol_sql} LIKE ? OR "
                    f"{idcol_sql} LIKE ? OR {idcol_sql} LIKE ? LIMIT 20"
                )
                patterns = tuple(f"%{session_id.rsplit('_', 1)[1]}%" for session_id in IDS)
                hits = list(cur.execute(q, patterns))
                if hits:
                    print(f"HITS in {table}.{idcol}: {hits}")
            except sqlite3.Error as exc:
                print(f"skip {table}: {exc}")



if __name__ == "__main__":
    main()
