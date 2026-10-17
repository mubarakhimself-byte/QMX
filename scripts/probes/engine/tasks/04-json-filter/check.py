import sys
from pathlib import Path

path = Path(sys.argv[1]) / "emails.txt"
if not path.exists():
    sys.exit("emails.txt missing")
got = path.read_text(encoding="utf-8").split()
if got != ["aaron@example.com", "ada@example.com", "cy@example.com"]:
    sys.exit(f"wrong emails: {got}")
