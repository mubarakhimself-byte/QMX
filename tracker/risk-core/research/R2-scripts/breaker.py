from math import comb
def pmf(n,k,q): return comb(n,k)*q**k*(1-q)**(n-k)
def p_run(n,k,q):
    dp=[0.0]*k; dp[0]=1.0; hit=0.0
    for _ in range(n):
        nd=[0.0]*k
        for j,pv in enumerate(dp):
            nd[0]+=pv*(1-q)
            if j+1>=k: hit+=pv*q
            else: nd[j+1]+=pv*q
        dp=nd
    return hit
q=0.45
for n in (2,5,10,20,40):
    p2=1-pmf(n,0,q)-pmf(n,1,q)
    cum=0;p95=None;p99=None
    for k in range(n+1):
        cum+=pmf(n,k,q)
        if p95 is None and cum>=0.95: p95=k
        if p99 is None and cum>=0.99: p99=k
    print(f"trades/day={n}: P(>=2 losses)={p2:.2f}  P(2 in a row)={p_run(n,2,q):.2f}  P(3 in a row)={p_run(n,3,q):.2f}  95th pct losses={p95} 99th={p99}")
# with q for 70% win scalper
q=0.30
for n in (10,20):
    print(f"70% win, {n}/day: P(2 in a row)={p_run(n,2,q):.2f} P(3 in a row)={p_run(n,3,q):.2f}")
# FX fix arithmetic: 2.5bp each side; EURUSD at 1.10 -> pips
print("2.5bp of 1.10 in pips:", 1.10*2.5e-4/1e-4)
# daily-unit breadth example
import math
s_trade=0.05; tpd=10
s_day=s_trade*math.sqrt(tpd)
for N,rho in ((1,0),(10,0),(10,0.3)):
    neff=N/(1+(N-1)*rho)
    print(f"N={N} rho={rho}: daily Sharpe {s_day*math.sqrt(neff):.3f}, annual(250) {s_day*math.sqrt(neff)*math.sqrt(250):.2f}")
# Rej et al fits: ell5 = 2.14/SR^2 years, d5 = 1.5/SR (vol units)
for SR in (0.5,1.0,2.0):
    print(f"SR={SR}: 5% drawdown length {2.14/SR**2:.2f} yr, depth {1.5/SR:.2f} x annual vol")
