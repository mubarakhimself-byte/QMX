"""Ends the run as failed when the check before it failed, so a test run that made a bad output
never reads as passed. The failure message is the check's feedback."""

import json
import sys

graded = json.load(sys.stdin)["in"]
feedback = graded.get("feedback") if isinstance(graded, dict) else graded
sys.stderr.write(f"the output failed its checks: {json.dumps(feedback)[:250]}")
raise SystemExit(1)
