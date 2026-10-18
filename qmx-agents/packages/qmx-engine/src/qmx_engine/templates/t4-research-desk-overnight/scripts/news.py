"""The zero-token pre-check: the news since the last desk run. The monitor that runs this wakes the
desk only when something new arrived.

Live, it reads the free press-release feeds of the Fed, the ECB and the Bank of Japan from the last
24 hours, and today's high-impact releases from the free calendar at nfs.faireconomy.media as
tier-one scheduled items. A feed that fails is named in `could_not_check`; the others still count.
A run started with `{"fixture": true}` replays `fixtures/news.json` instead; the replay carries the
run id so every test run is a change.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen

FEEDS = {
    "https://www.federalreserve.gov/feeds/press_all.xml": "USD",
    "https://www.ecb.europa.eu/rss/press.html": "EUR",
    "https://www.boj.or.jp/en/rss/whatsnew.xml": "JPY",
}
CALENDAR = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
HOURS = 24


def fetch(url):
    request = Request(url, headers={"User-Agent": "QMX research desk"})  # noqa: S310
    with urlopen(request, timeout=60) as reply:  # noqa: S310
        return reply.read()


inputs = json.load(sys.stdin).get("in") or {}
if isinstance(inputs, dict) and inputs.get("fixture"):
    found = json.loads((Path(__file__).parents[1] / "fixtures" / "news.json").read_text("utf-8"))
    run = os.environ.get("QMX_IDEMPOTENCY_KEY", "").split(":")[0]
    print(json.dumps(found | {"source": "fixture", "run": run, "could_not_check": []}))
    raise SystemExit(0)

now = datetime.now(UTC)
since = now - timedelta(hours=HOURS)
items, missing = [], []
for url, currency in FEEDS.items():
    try:
        root = ET.fromstring(fetch(url))  # noqa: S314
    except Exception as error:
        missing.append(f"rates feed {url}: {type(error).__name__}")
        continue
    for entry in root.iter("item"):
        title = (entry.findtext("title") or "").strip()
        when = entry.findtext("pubDate")
        try:
            published = parsedate_to_datetime(when).astimezone(UTC) if when else None
        except TypeError, ValueError:
            published = None
        if not title or published is None or published < since:
            continue
        items.append(
            {
                "id": f"{currency}-{published:%m%d%H%M}-{len(items)}",
                "beat": "rates",
                "currencies": [currency],
                "tier1": False,
                "sentiment_sd": None,
                "published": published.isoformat(),
                "link": (entry.findtext("link") or url).strip(),
                "title": title,
                "text": (entry.findtext("description") or title).strip(),
            }
        )
try:
    week = json.loads(fetch(CALENDAR))
except Exception as error:
    week = []
    missing.append(f"calendar {CALENDAR}: {type(error).__name__}")
for row in week:
    when = datetime.fromisoformat(row["date"]).astimezone(UTC)
    if when.date() != now.date() or row.get("impact") != "High":
        continue
    items.append(
        {
            "id": f"{row['country']}-{when:%H%M}-cal",
            "beat": "calendar",
            "currencies": [row["country"]],
            "tier1": True,
            "sentiment_sd": None,
            "published": when.isoformat(),
            "link": CALENDAR,
            "title": f"{row['country']} {row['title']} is released today at {when:%H:%M} UTC",
            "text": f"{row['title']} ({row['country']}) is a high-impact release today at "
            f"{when:%H:%M} UTC; forecast {row.get('forecast') or 'none'}.",
        }
    )
print(
    json.dumps(
        {
            "date": now.date().isoformat(),
            "items": items,
            "source": "feeds",
            "could_not_check": missing,
        }
    )
)
