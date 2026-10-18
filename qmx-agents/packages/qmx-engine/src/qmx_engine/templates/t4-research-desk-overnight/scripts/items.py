"""Loads the watchlist and turns the night's news into analyst items: each item that touches a
watched currency, with the instruments it touches and the night it came from (its date and the
feeds that could not be read). Items on other currencies are left out here, so no analyst spends
tokens on them.

The watchlist stands in for the active units until the trading node exists.
"""

import json
import sys

WATCHLIST = {"EURUSD": ("EUR", "USD"), "USDJPY": ("USD", "JPY")}

news = json.load(sys.stdin)["in"]["value"]
night = {"date": news["date"], "could_not_check": news.get("could_not_check", [])}
items = []
for item in news["items"]:
    instruments = [pair for pair, legs in WATCHLIST.items() if set(item["currencies"]) & set(legs)]
    if instruments:
        items.append(item | {"instruments": instruments, "night": night})
print(json.dumps(items))
