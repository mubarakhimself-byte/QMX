"""Stands in for the step before the check: prints the example output beside this script."""

from pathlib import Path

print((Path(__file__).parents[1] / "fixtures" / "output.json").read_text("utf-8"))
