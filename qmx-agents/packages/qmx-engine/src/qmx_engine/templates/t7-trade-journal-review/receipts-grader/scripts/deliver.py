"""Hands on the note that passed its receipts check, with how many numbers were checked, for the
calling template's `notes_write` step."""

import json
import sys

feedback = json.load(sys.stdin)["in"]["feedback"]
print(json.dumps({"note": feedback["note"], "numbers": feedback["numbers"]}))
