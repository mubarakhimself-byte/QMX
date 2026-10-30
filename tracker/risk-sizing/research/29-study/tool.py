"""The receipts arm's only number source. Every call prints JSON with a receipt id
and appends {receipt, args, output} to receipts.jsonl beside data.csv.
In QMX the engine ledger would record this; here the log stands in.

usage: python -I tool.py stats [--from HH:MM] [--to HH:MM]
       python -I tool.py regime
       python -I tool.py rows --from HH:MM --to HH:MM
"""
import csv, datetime as dt, hashlib, json, math, os, sys

HERE = os.getcwd()


def bars():
    with open(os.path.join(HERE, "data.csv")) as f:
        r = csv.reader(f); next(r)
        return [(dt.datetime.strptime(x[0], "%Y-%m-%dT%H:%MZ"), *map(float, x[1:5])) for x in r]


def arg(name, default):
    a = sys.argv
    return a[a.index(name) + 1] if name in a else default


def hm(s):
    h, m = s.split(":"); return int(h) * 60 + int(m)


def select(bs):
    lo, hi = hm(arg("--from", "00:00")), hm(arg("--to", "23:59"))
    return [b for b in bs if lo <= b[0].hour * 60 + b[0].minute <= hi], lo, hi


def stats(bs):
    sel, lo, hi = select(bs)
    if not sel:
        return {"bars": 0, "note": "no bars in window"}
    h = max(sel, key=lambda b: b[2]); l = min(sel, key=lambda b: b[3])
    have = {b[0].hour * 60 + b[0].minute for b in sel}
    missing = [m for m in range(lo, hi + 1) if m not in have]
    runs = []
    for m in missing:
        if runs and m == runs[-1][1] + 1:
            runs[-1][1] = m
        else:
            runs.append([m, m])
    fmt = lambda m: f"{m // 60:02d}:{m % 60:02d}"
    return {"bars": len(sel), "open": sel[0][1], "high": h[2], "low": l[3], "close": sel[-1][4],
            "time_of_high_utc": h[0].strftime("%H:%M"), "time_of_low_utc": l[0].strftime("%H:%M"),
            "range": round(h[2] - l[3], 6), "missing_minutes": len(missing),
            "missing_runs": [f"{fmt(a)}-{fmt(b)}" for a, b in runs]}


def regime(bs):
    c5 = [b[4] for b in bs if b[0].minute % 5 == 4]
    path = sum(abs(a - b) for a, b in zip(c5[1:], c5[:-1])) or 1e-12
    r1 = [math.log(b[4] / a[4]) for a, b in zip(bs[:-1], bs[1:])]
    rq = [math.log(bs[i + 15][4] / bs[i][4]) for i in range(0, len(bs) - 15, 15)]
    vr = (sum(x * x for x in rq) / len(rq)) / (15 * sum(x * x for x in r1) / len(r1))
    return {"efficiency_ratio_5m": round(abs(bs[-1][4] - bs[0][1]) / path, 4), "variance_ratio_15": round(vr, 3),
            "meaning": "efficiency near 0 = choppy, near 1 = one-way; variance ratio below 1 = reverting, above 1 = trending"}


def rows(bs):
    sel, _, _ = select(bs)
    return {"rows": [[b[0].strftime("%H:%M"), *b[1:]] for b in sel[:240]], "truncated": len(sel) > 240}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"stats": stats, "regime": regime, "rows": rows}.get(cmd)
    if fn is None:
        print(__doc__); sys.exit(2)
    out = fn(bars())
    body = json.dumps({"args": sys.argv[1:], "output": out}, sort_keys=True)
    rid = "R" + hashlib.sha256(body.encode()).hexdigest()[:8]
    with open(os.path.join(HERE, "receipts.jsonl"), "a") as f:
        f.write(json.dumps({"receipt": rid, "args": sys.argv[1:], "output": out}) + "\n")
    print(json.dumps({"receipt": rid, **out}))
