"""Put the app folder on the path, as the supervisor's bootstrap does, so `mis_core` imports."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
