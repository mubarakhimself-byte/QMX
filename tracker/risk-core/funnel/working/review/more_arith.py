"""Reviewer's small arithmetic. Standard library only. Run: python -I more_arith.py"""
import math,random
from statistics import NormalDist
Z=NormalDist().inv_cdf
print("A. His 'about three' scaled to own p99 run length (X3-H05): the run length that fires on 1 % of days")
def p_run(k,n,q):
    # P(at least one run of k losses in n trades)
    st=[1.0]+[0.0]*(k-1); hit=0.0
    for _ in range(n):
        new=[0.0]*k
        new[0]=sum(st)*(1-q)
        for j in range(k-1): new[j+1]=st[j]*q
        hit+=st[k-1]*q
        st=new
    return hit
for pw in (0.55,0.70):
    for n in (4,10,16,40):
        q=1-pw
        k=1
        while p_run(k,n,q)>0.01: k+=1
        print(f"  win {int(pw*100)}% at {n:>2}/day: own p99 run length = {k} straight losses  (P(3 in a row) {p_run(3,n,q)*100:4.1f}%)")
print("B. Baseline r against the minimum lot (D=$200, s=0.87, eps 1%, 20 days, rho 0.3). 1 micro lot on a 5-pip EURUSD stop = $0.50")
z=Z(0.995)
for N in (1,3,5,10):
    B=math.sqrt(N*(1+(N-1)*0.3))
    row=[]
    for n in (2,4,10,40):
        r=200/(0.87*z*math.sqrt(n*20)*B)
        darkD=0.5*(0.87*z*math.sqrt(n*20)*B)
        row.append(f"n={n}: ${r:5.2f}, L1 share {min(1,0.5/r)*100:3.0f}%, dark below D=${darkD:4.0f}")
    print(f"  N={N:<2} B={B:4.2f} | "+" | ".join(row))
print("C. Survivors' size after a correlated day: 3 of 10 units benched, cushion down 10%, N falls at the next anchor")
B10=math.sqrt(10*3.7);B7=math.sqrt(7*2.8)
print(f"  B10={B10:.2f} B7={B7:.2f}: survivor r changes by {0.9*B10/B7-1:+.0%} the next morning (if N counts live units)")
print("D. Trades to the e-bars (X5 §9: +0.10R e10 335, e20 485, e50 641, e100 750). Time scales with 1/edge^2.")
for edge in (0.10,0.05,0.03):
    sc=(0.10/edge)**2
    row=[]
    for n in (2,4,10,40):
        row.append(f"{n}/day: e20 {485*sc/n:5.0f}d, e100 {750*sc/n:6.0f}d")
    print(f"  +{edge:.2f}R: e10 {335*sc:6.0f} trades, e20 {485*sc:6.0f}, e50 {641*sc:6.0f}, e100 {750*sc:6.0f} | "+" | ".join(row))
print("E. The cut assumption (F1). 55% raw, 1:1, cost 0.16R. Half of losers cut at -0.35R, and a share w of would-be winners also cut at -0.35R")
for w in (0.0,0.1,0.2,0.3,0.4):
    p=0.55
    wins=p*(1-w); cutw=p*w
    loss_full=(1-p)*0.5; loss_cut=(1-p)*0.5
    ev=wins*1 - cutw*0.35 - loss_full*1 - loss_cut*0.35 - 0.16
    print(f"  winners also cut {int(w*100):>2}%: net EV {ev:+.3f}R")
print("F. Same at p=0.60 and at half of losers cut at -0.5R")
for p,cs in ((0.60,0.35),(0.55,0.5),(0.60,0.5)):
    for w in (0.0,0.2):
        ev=p*(1-w)-p*w*cs-(1-p)*0.5-(1-p)*0.5*cs-0.16
        print(f"  p={p} cut at -{cs}R, winners cut {int(w*100)}%: net EV {ev:+.3f}R")
print("G. Cut-only stack on a normal morning and a bad afternoon (share of the bare sizer's number; [judgment] on each factor)")
norm=[("reserve (N-1/PML)",0.85),("cost denominator",0.85),("level (L3 of 5)",0.50)]
print("  normal, unit mid-ladder:",round(math.prod(x for _,x in norm),3))
bad=norm+[("brake half m at -3R of 5.3R",0.43),("REDUCING halve",0.5),("SQS graded shrink",0.8),("class caution",0.75)]
print("  bad afternoon, same unit:",round(math.prod(x for _,x in bad),3))
print("  weak unit at L1 before any brake:",round(0.85*0.85*0.10,3))
print("H. F1's scalper against DP11's admission gate: gross edge must reach k x stressed cost (X2-H39: k 2, 3 for negative skew).")
print("   Round trip 0.8 pips (the funnel's own 0.16R at 5 pips). Half of losers cut at -0.35R, no winner ever cut (F1's best case).")
for stop in (5,8,10,15):
    c=0.8/stop
    for p in (0.55,0.60):
        gross=p-(1-p)*0.675
        net=gross-c
        print(f"   stop {stop:>2} pips cost {c:.2f}R p={p}: gross {gross:+.3f}R net {net:+.3f}R | bar at k=2, no stress {2*c:.2f}R: {'pass' if gross>=2*c else 'REFUSED'} | k=2, cost stress 1.5x {3*c:.2f}R: {'pass' if gross>=3*c else 'REFUSED'} (point estimate, before the low end)")
print("I. Level-aware book swing: one unit at full size, nine at L1 (10 %), rho 0.3")
w=[1.0]+[0.1]*9
S2=sum(x*x for x in w);S=sum(w)
print(f"   B as written {math.sqrt(10*3.7):.2f}; book swing actually used {math.sqrt(0.7*S2+0.3*S*S):.2f}; the proved unit could be {math.sqrt(10*3.7)/math.sqrt(0.7*S2+0.3*S*S):.1f}x larger at the same book swing")
w=[0.1]*10
S2=sum(x*x for x in w);S=sum(w)
print(f"   all ten at L1: book runs at {math.sqrt(0.7*S2+0.3*S*S)/math.sqrt(10*3.7)*100:.0f} % of the allowed swing")
print("J. Ratchet share of each new high, idle money below the floor when equity doubles from $500 (floor $300)")
for g in (0,0.25,0.5):
    fl=300+g*500
    print(f"   share {g}: floor ${fl:.0f}, idle {fl/1000*100:.0f} % of equity, cushion ${1000-fl:.0f}")
print("K. How long the random-control certificate needs for an own-p1 money brake on one unit (FI scalper, 10/day, X3's regime world)")
rng=random.Random(5)
def yr():
    good=True;mr=0.0;rr=0.0
    for d in range(250):
        tr=[]
        for t in range(10):
            if rng.random()<(0.01 if good else 0.02): good=not good
            pw,pc=(0.455,0.2725) if good else (0.30,0.35)
            u=rng.random();tr.append(1.0 if u<pw else (-0.3 if u<pw+pc else -1.0))
        pnl=0.0;mt=None
        for i,x in enumerate(tr):
            pnl+=x
            if pnl<=-5.5: mt=i;break
        m=sum(tr[:mt+1]) if mt is not None else sum(tr)
        if rng.random()<0.031:
            j=rng.randrange(10);r=sum(tr[:j])
        else: r=sum(tr)
        mr+=m;rr+=r
    return mr-rr
ms=[yr() for _ in range(400)]
mean=sum(ms)/len(ms);sd=math.sqrt(sum((x-mean)**2 for x in ms)/(len(ms)-1))
print(f"   margin per unit-year {mean:+.2f}R, sd {sd:.2f}R; years of one unit's trades for z=2: {(2*sd/mean)**2 if mean>0 else float('inf'):.0f}")
