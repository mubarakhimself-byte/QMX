import math, random
random.seed(1)
def exact(p,w,f): return p*math.log(1+f*w)+(1-p)*math.log(1-f)
def sim(p,w,f,paths=4000,cap=20000):
    ns=[];dd30=0;dd50=0
    for _ in range(paths):
        W=1.0;peak=1.0;worst=1.0;n=0
        while W<10 and n<cap:
            n+=1
            W*= (1+f*w) if random.random()<p else (1-f)
            peak=max(peak,W);worst=min(worst,W/peak)
        ns.append(n); dd30+=worst<=0.7; dd50+=worst<=0.5
    ns.sort(); return ns[len(ns)//2], dd30/paths, dd50/paths
for name,p,w in (("60% win, 1:1 (edge 0.2)",0.6,1.0),("55% win, 1:1 (edge 0.1)",0.55,1.0),("70% win, win 0.6R (edge 0.12)",0.7,0.6)):
    mu=p*w-(1-p); fk=(p*w-(1-p))/w
    for c in (1,0.5):
        f=c*fk
        print(f"{name} | {'full' if c==1 else 'half'} Kelly risk {f*100:.1f}% | formula trades {math.log(10)/exact(p,w,f):.0f} | sim median {sim(p,w,f)}")
