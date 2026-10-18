"""Stands in for the calling template's headline step: prints the items in the fixture beside this
script."""

from pathlib import Path

print((Path(__file__).parents[1] / "fixtures" / "claims.json").read_text("utf-8"))
