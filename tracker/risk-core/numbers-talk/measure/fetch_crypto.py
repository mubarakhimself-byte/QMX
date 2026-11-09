"""Download crypto 1-minute candles and live order-book snapshots.

Sources (all public, no key):
  - Hyperliquid info API candleSnapshot: 1m (only the latest 5000 candles exist, about 3.5 days)
    and 5m (about 17 days). Used as the real venue's own view and to check the proxy.
  - Binance USD-M perpetual klines (fapi.binance.com): 1m history for both periods.
    PROXY: Hyperliquid's API does not serve 1m history older than ~3.5 days, so the
    90-day and year-ago move statistics for BTC/ETH/SOL come from Binance perps.
  - Hyperliquid l2Book: a few live snapshots of best bid/ask (spread is a snapshot, not history).

Usage: python -I fetch_crypto.py [candles|book|all]
Writes into data/.
"""
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
HL = "https://api.hyperliquid.xyz/info"
BINANCE = "https://fapi.binance.com/fapi/v1/klines"
COINS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
PERIODS = {"a": ("2026-08-11", "2026-11-09"), "b": ("2025-11-01", "2026-03-01")}


def ms(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def post(body: dict):
    req = urllib.request.Request(HL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def get(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def binance_1m(symbol: str, start: int, end: int, out: Path):
    rows, t = [], start
    while t < end:
        batch = get(f"{BINANCE}?symbol={symbol}&interval=1m&startTime={t}&endTime={end - 1}&limit=1500")
        if not batch:
            break
        rows += batch
        t = batch[-1][0] + 60_000
        time.sleep(0.35)  # stay far below Binance's request-weight limit
    with out.open("w") as f:
        f.write("ts,open,high,low,close,volume\n")
        for k in rows:
            f.write(f"{k[0]},{k[1]},{k[2]},{k[3]},{k[4]},{k[5]}\n")
    print(f"{out.name}: {len(rows)} bars")


def hl_candles(coin: str, interval: str, out: Path):
    now = int(time.time() * 1000)
    span = {"1m": 5000 * 60_000, "5m": 5000 * 300_000}[interval]
    rows = post({"type": "candleSnapshot", "req": {"coin": coin, "interval": interval, "startTime": now - span, "endTime": now}})
    with out.open("w") as f:
        f.write("ts,open,high,low,close,volume\n")
        for c in rows:
            f.write(f"{c['t']},{c['o']},{c['h']},{c['l']},{c['c']},{c['v']}\n")
    print(f"{out.name}: {len(rows)} bars")


def hl_books(snapshots: int = 5, pause_s: float = 20.0):
    out = DATA / "hl_l2book_snapshots.jsonl"
    with out.open("a") as f:
        for i in range(snapshots):
            for coin in COINS:
                book = post({"type": "l2Book", "coin": coin})
                bid, ask = float(book["levels"][0][0]["px"]), float(book["levels"][1][0]["px"])
                rec = {"coin": coin, "time": book["time"], "bid": bid, "ask": ask,
                       "bid_sz": float(book["levels"][0][0]["sz"]), "ask_sz": float(book["levels"][1][0]["sz"])}
                f.write(json.dumps(rec) + "\n")
                print(rec)
            if i < snapshots - 1:
                time.sleep(pause_s)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    DATA.mkdir(exist_ok=True)
    if what in ("candles", "all"):
        for coin, sym in COINS.items():
            hl_candles(coin, "1m", DATA / f"hl_{coin}_1m_recent.csv")
            hl_candles(coin, "5m", DATA / f"hl_{coin}_5m_recent.csv")
            for p, (a, b) in PERIODS.items():
                binance_1m(sym, ms(a), ms(b), DATA / f"binance_{coin}_{p}.csv")
    if what in ("book", "all"):
        hl_books()
