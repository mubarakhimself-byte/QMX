import random, statistics as st
def kelly(p,rr): return max(0,((rr+1)*p-1)/rr)*0.5
print("half-kelly p.6 rr1.5", kelly(.6,1.5), " p.55 rr1.2", kelly(.55,1.2), " p.5 rr1.1", kelly(.5,1.1))
def run(risk, p=0.6, rr=1.5, trades=12, days=250, dlim=0.10, seed=1, n=4000):
    rnd=random.Random(seed); finals=[]; dd50=0; stopped_days=0; mdds=[]
    for _ in range(n):
        eq=300.0; peak=eq; mdd=0
        for d in range(days):
            start=eq
            for t in range(trades):
                if (start-eq)/start >= dlim - 1e-12: stopped_days+=1; break
                r=eq*risk
                eq += r*rr if rnd.random()<p else -r
                peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak)
        finals.append(eq); mdds.append(mdd); dd50 += mdd>=0.5
    finals.sort(); mdds.sort()
    q=lambda a,x:a[int(x*(len(a)-1))]
    return dict(risk=risk,p5=round(q(finals,.05)),p50=round(q(finals,.5)),p95=round(q(finals,.95)),
                mdd_p50=round(q(mdds,.5),3),mdd_p95=round(q(mdds,.95),3),P_dd50=round(dd50/n,3),stopdays_per_yr=round(stopped_days/n,1))
for p,rr,lab in [(0.6,1.5,"strong edge +0.5R"),(0.55,1.2,"thin edge +0.21R"),(0.5,1.1,"near-zero edge +0.05R")]:
    print(lab)
    for risk in (0.005,0.01,0.02,0.08):
        print("  ",run(risk,p,rr,days=20 if False else 250, n=2000))
