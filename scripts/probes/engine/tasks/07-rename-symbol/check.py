import subprocess
import sys
from pathlib import Path

work = Path(sys.argv[1])
files = [work / "app.py", work / "helpers.py"]
if not all(f.exists() for f in files):
    sys.exit("app.py or helpers.py missing")
text = "".join(f.read_text(encoding="utf-8") for f in files)
if "old_total" in text or "def grand_total" not in text:
    sys.exit("rename incomplete")
out = subprocess.run(
    [sys.executable, "app.py"], capture_output=True, text=True, timeout=30, cwd=work
)
if out.stdout.strip() != "16":
    sys.exit(f"wrong output: {out.stdout!r} {out.stderr[-200:]!r}")
