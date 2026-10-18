import importlib.util
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "textutil.py"
if not path.exists():
    sys.exit("textutil.py missing")
spec = importlib.util.spec_from_file_location("textutil_under_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if not hasattr(module, "slugify"):
    sys.exit("slugify missing")
cases = {
    "  Hello, World! 2026 ": "hello-world-2026",
    "A--B": "a-b",
    "--x__y--": "x-y",
    "Q4 Report.PDF": "q4-report-pdf",
}
bad = {text: module.slugify(text) for text, want in cases.items() if module.slugify(text) != want}
if bad or module.shout("hi") != "HI!":
    sys.exit(f"wrong results: {bad}")
