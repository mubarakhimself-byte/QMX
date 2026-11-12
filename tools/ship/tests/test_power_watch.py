import sys
import tempfile
import unittest
from pathlib import Path

from ship import state as st
from ship.power_watch import on_mains, on_mains_linux, power_report, probe_network, step
from ship.settings import load_settings
from ship.tests.fixture import RepoCase, write


class PowerSteps(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = load_settings(self.program.dir)  # power_settle_s = 5 in the fixture
        self.net = []

    def go(self, mains, now):
        return step(self.program, self.settings, mains, now, lambda: self.net)

    def test_battery_holds_then_mains_settles_and_network_gates_the_clear(self):
        self.assertEqual(self.go(True, 0), "MAINS")
        self.assertEqual(self.go(False, 10), "HOLD on battery")
        self.assertTrue(self.program.hold.read_text("utf-8").startswith("power: on battery since"))
        self.assertEqual(self.go(False, 70), "BATTERY hold kept")
        self.assertEqual(self.go(True, 100), "MAINS back, waiting 5s before network checks")
        self.assertEqual(self.go(True, 103), "MAINS settling 3s of 5s")
        self.net = ["github: offline"]
        self.assertEqual(self.go(True, 106), "WAIT github: offline")
        self.assertTrue(self.program.hold.exists())
        self.net = []
        self.assertEqual(self.go(True, 107), "CLEAR hold removed; run recover before dispatching")
        self.assertFalse(self.program.hold.exists())
        kinds = [e["kind"] for e in st.load(self.program).events]
        self.assertEqual(kinds[-2:], ["hold", "clear"])

    def test_battery_blip_restarts_the_settle_wait(self):
        self.go(False, 0)
        self.go(True, 10)
        self.go(False, 12)
        self.assertEqual(self.go(True, 20), "MAINS back, waiting 5s before network checks")

    def test_manual_hold_is_left_alone(self):
        write(self.program.hold, "operator: stop\n")
        self.assertEqual(self.go(True, 0), "MAINS")
        self.assertEqual(self.program.hold.read_text("utf-8"), "operator: stop\n")

    def test_power_report_says_whether_a_watcher_runs_and_whether_to_wait(self):
        self.assertEqual(power_report(self.program, self.settings, now=1000.0),
                         (2, ["NO WATCHER: start `ship power_watch` in the background", "CLEAR"]))
        self.go(False, 10)
        mtime = self.program.power.stat().st_mtime
        rc, lines = power_report(self.program, self.settings, now=mtime + 60)
        self.assertEqual((rc, lines[0]), (1, "WATCHER running"))
        self.assertTrue(lines[1].startswith("HOLD power: on battery since"))
        self.assertEqual(power_report(self.program, self.settings, now=mtime + 301)[0], 2)

    def test_github_probe_reaches_the_real_remote(self):
        settings = load_settings(self.program.dir)
        failed = probe_network(self.program, settings)
        self.assertEqual([f for f in failed if f.startswith("github")], [])


class PowerSources(unittest.TestCase):
    def test_linux_sysfs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "AC" / "type", "Mains\n")
            write(root / "AC" / "online", "0\n")
            write(root / "BAT0" / "type", "Battery\n")
            write(root / "BAT0" / "status", "Discharging\n")
            self.assertFalse(on_mains_linux(root))
            write(root / "AC" / "online", "1\n")
            self.assertTrue(on_mains_linux(root))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(on_mains_linux(Path(tmp)), "a machine with no power supply entries is on mains")

    @unittest.skipUnless(sys.platform == "win32", "GetSystemPowerStatus is Windows only")
    def test_windows_reads_a_value(self):
        self.assertIn(on_mains(), (True, False))


if __name__ == "__main__":
    unittest.main()
