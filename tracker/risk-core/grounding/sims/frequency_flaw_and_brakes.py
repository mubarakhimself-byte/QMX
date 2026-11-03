"""Where 'ten units at full size, same floor odds' breaks, and how trade count changes brakes.
Same setup as units_split.py: $500 seed, $300 floor, 60 days, 4 trades a day per unit, 1:1 payoff, no costs."""
import numpy as np
rng=np.random.default_rng(11)
SEED,FLOOR,DAYS,TPD,PATHS=500,300,60,4,20000
def run(n,r,p,rho=0.0):
    eq=np.full(PATHS,SEED,float); hit=np.zeros(PATHS,bool); thr=np.quantile(rng.standard_normal(400000),p)
    for _ in range(DAYS*TPD):
        z=np.sqrt(rho)*rng.standard_normal(PATHS)[:,None]+np.sqrt(1-rho)*rng.standard_normal((PATHS,n))
        pnl=np.where(z<thr,1,-1).sum(1)*r
        eq=np.where(hit,eq,eq+pnl); hit|=eq<=FLOOR
    return hit.mean()*100,np.median(eq)
print("Part 1: floor odds when the edge is smaller than believed")
rows=[("1 unit, $10",1,10),("10 units, $10 each",10,10),("10 units, $1 each",10,1)]
for p,label in [(0.55,"55% (edge as believed)"),(0.525,"52.5% (half the edge)"),(0.50,"50% (no edge)")]:
    print(" ",label)
    for name,n,r in rows:
        h,m=run(n,r,p); print(f"    {name:20s} touch $300 {h:5.1f}%  typical end ${m:,.0f}")
print("\nPart 2: how often count brakes fire on a HEALTHY unit, by trades per day (share of days)")
def brake_days(tpd,p,days=200000):
    w=rng.random((days,tpd))<p; losses=(~w).sum(1)
    two=(losses>=2).mean()*100
    run3=np.zeros(days,bool); c=np.zeros(days,int)
    for k in range(tpd):
        c=np.where(~w[:,k],c+1,0); run3|=c>=3
    return two,run3.mean()*100
for p in (0.55,0.70):
    print(f"  win rate {int(p*100)}%")
    for tpd in (2,4,8,16,40):
        two,r3=brake_days(tpd,p)
        print(f"    {tpd:3d} trades/day: '2 full stops' fires {two:5.1f}% of days, '3 losses in a row' {r3:5.1f}%")
