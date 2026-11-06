"""Proves one Windows fact the status file leans on: os.replace onto a file another reader holds open.

SPINE AD-18 writes the status file "whole then replaced" (the move at runtime.py _write_snapshot) and 4.8 lets agent
tools and the screen read that file. Run with a scratch folder as its argument; writes only there.
"""
import os
import pathlib
import sys

folder = pathlib.Path(sys.argv[1])
folder.mkdir(parents=True, exist_ok=True)
status = folder / "risk-status.json"
status.write_text('{"rev": 1}', "utf-8")
temporary = status.with_suffix(".json.tmp")
temporary.write_text('{"rev": 2}', "utf-8")
reader = open(status, encoding="utf-8")  # a plain reader in any other thread or process, mid-read
try:
    os.replace(temporary, status)
    print("replace succeeded with a reader open")
except OSError as error:
    print(f"replace failed with a reader open: {type(error).__name__}: {error}")
finally:
    reader.close()
os.replace(temporary, status) if temporary.exists() else None
print("after the reader closed:", status.read_text("utf-8"))
