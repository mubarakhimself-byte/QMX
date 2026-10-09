import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from macro_bias import latest, refresh


class BiasTests(unittest.TestCase):
    def test_recorded_agent_writes_persistent_bias(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict(os.environ, {"QMX_STAGE": "tests"}),
        ):
            volume = Path(temporary)
            result = asyncio.run(refresh(volume))
            self.assertEqual(latest(volume), result)
            self.assertEqual(result["bias"], "neutral")
            self.assertEqual(result["source"], "recorded")
            self.assertIn("coverage", result["rationale"])
            self.assertEqual(json.loads(json.dumps(result)), result)
