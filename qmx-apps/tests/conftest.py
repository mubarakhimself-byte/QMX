"""Import the standalone headless example without installing it as a package."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples/apps/mql5-articles"))
