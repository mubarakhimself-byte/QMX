import numpy as np
rng=np.random.default_rng(7)
SEED,FLOOR,DAYS,TPD,P=500,300,60,4,0.55   # 4 trades/day/unit, 55% wins at 1:1 -> EV 0.1R
PATHS=20000
def run(n_units,dollars_per_R,rho=0.0):
    eq=np.full(PATHS,SEED,float); hit=np.zeros(PATHS,bool)
    for _ in range(DAYS*TPD):
        common=rng.standard_normal(PATHS)[:,None]
        own=rng.standard_normal((PATHS,n_units))
        z=np.sqrt(rho)*common+np.sqrt(1-rho)*own
        win=z<np.quantile(rng.standard_normal(200000),P)  # P(win)=0.55, correlated across units
        pnl=np.where(win,1,-1).sum(1)*dollars_per_R
        eq=np.where(hit,eq,eq+pnl); hit|=eq<=FLOOR
    return hit.mean()*100,np.median(eq)
for name,n,r,rho in [("1 unit, $10 a trade",1,10,0),
                     ("10 units, $10 each, independent",10,10,0),
                     ("10 units, $1 each (one $10 split)",10,1,0),
                     ("10 units, $10 each, half-correlated",10,10,0.5),
                     ("10 units, $3 each, half-correlated",10,3,0.5)]:
    h,m=run(n,r,rho); print(f"{name:40s} touch $300: {h:5.1f}%   typical end: ${m:,.0f}")
