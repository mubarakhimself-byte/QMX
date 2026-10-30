"""List weekdays in a 1m CSV with day stats, to pick the study day."""
import csv, sys, datetime as dt, math, collections

def load(path):
    days = collections.defaultdict(list)
    with open(path) as f:
        r = csv.reader(f); next(r)
        for row in r:
            ts = int(row[0]); o, h, l, c = map(float, row[1:5])
            d = dt.datetime.fromtimestamp(ts / 1000, dt.UTC)
            days[d.date()].append((d, o, h, l, c))
    return days

def stats(bars):
    o = bars[0][1]; c = bars[-1][4]
    h = max(b[2] for b in bars); l = min(b[3] for b in bars)
    closes5 = [b[4] for b in bars if b[0].minute % 5 == 4]
    path = sum(abs(a - b) for a, b in zip(closes5[1:], closes5[:-1])) or 1e-12
    er = abs(c - o) / path
    r1 = [math.log(b[4] / a[4]) for a, b in zip(bars[:-1], bars[1:])]
    q = 15
    rq = [math.log(bars[i + q][4] / bars[i][4]) for i in range(0, len(bars) - q, q)]
    v1 = sum(x * x for x in r1) / len(r1); vq = sum(x * x for x in rq) / len(rq)
    return o, h, l, c, er, vq / (q * v1)

if __name__ == "__main__":
    path, pip = sys.argv[1], float(sys.argv[2])
    days = load(path); keys = sorted(days)
    for i, k in enumerate(keys[:-1]):
        b = days[k]
        if k.weekday() > 4 or len(b) < 1400: continue
        o, h, l, c, er, vr = stats(b)
        nb = days[keys[i + 1]]
        nxt = "up" if nb[-1][4] > nb[0][1] else "down"
        print(k, len(b), f"range={(h-l)/pip:.1f} ret={(c-o)/pip:+.1f} er={er:.3f} vr15={vr:.2f} next={nxt}")
