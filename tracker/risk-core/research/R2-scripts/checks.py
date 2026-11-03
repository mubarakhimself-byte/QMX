import math, random
random.seed(7)
# 1. SPRT: H0 mu=0 vs H1 mu=0.1R, sd 1R, alpha=beta=0.05
a=b=0.05
A=math.log((1-b)/a); B=math.log(b/(1-a))
def sprt(mu, n=4000):
    out=[]
    for _ in range(n):
        s=0.0; k=0
        while B<s<A and k<20000:
            x=random.gauss(mu,1.0); k+=1
            s+=0.1*(x-0.05)
        out.append((k, s>=A))
    ks=sorted(k for k,_ in out)
    return sum(k for k,_ in out)/n, ks[len(ks)//2], ks[int(.9*len(ks))], sum(1 for _,acc in out if acc)/n
print("SPRT A,B", round(A,3), round(B,3))
for mu in (0.1,0.0,0.05):
    m,med,p90,acc=sprt(mu)
    print(f"mu={mu}: mean trades {m:.0f}, median {med}, p90 {p90}, share deciding 'edge 0.1' {acc:.2f}")
# Wald approx
e1=0.1*0.05
print("Wald approx E[N|H1]", ((1-b)*A + b*B)/e1)
# 2. breadth ceiling
s=0.05
for N in (1,10,100,1000,2000):
    for rho in (0.0,0.01,0.05,0.2):
        neff=N/(1+(N-1)*rho)
        print(f"N={N} rho={rho}: Neff={neff:.1f} Sharpe={s*math.sqrt(neff):.3f}")
print("ceiling s/sqrt(rho) rho=.05:", s/math.sqrt(.05), " rho=.01:", s/math.sqrt(.01))
# 3. vol-target sizing per unit with N units, total target T=1
for N,rho in ((1,0),(10,0),(10,0.3),(50,0),(50,0.3)):
    r=1/math.sqrt(N*(1+(N-1)*rho))
    print(f"N={N} rho={rho}: each unit risk = {r:.3f} of total budget; 1/N would be {1/N:.3f}")
# 4. drawdown at a random time for drift 0.05R, sd 1R: P(DD>d)=exp(-2 mu d)
mu=0.05
for p in (0.5,0.2,0.05,0.01):
    print(f"P={p}: DD level {-math.log(p)/(2*mu):.1f}R")
# simulate max DD over 2000 trades, mu .05
mx=[]
for _ in range(2000):
    eq=0;pk=0;m=0
    for _ in range(2000):
        eq+=random.gauss(mu,1); pk=max(pk,eq); m=max(m,pk-eq)
    mx.append(m)
mx.sort()
print("maxDD over 2000 trades: median",round(mx[1000],1),"p95",round(mx[1900],1))
# loss streaks at 55% win: P(at least one run of >=k losses in n trades)
def p_run(n,k,q):
    # prob of a run of >=k losses with loss prob q, DP
    import functools
    dp=[0.0]*(k); dp[0]=1.0; hit=0.0
    for _ in range(n):
        nd=[0.0]*k
        for j,pv in enumerate(dp):
            nd[0]+=pv*(1-q)
            if j+1>=k: hit+=pv*q
            else: nd[j+1]+=pv*q
        dp=nd
    return hit
for k in (6,8,10):
    print(f"55% win, 500 trades, P(run>={k} losses)={p_run(500,k,0.45):.2f}")
# 5. LCB sizing: edge .05R, n trades, z=1.645
for n in (100,300,1000,3000):
    se=1/math.sqrt(n); lcb=0.05-1.645*se
    print(f"n={n}: se={se:.3f} LCB={lcb:.3f} -> size factor vs point Kelly {max(lcb,0)/0.05:.2f}; shrink t2/(1+t2)={(0.05/se)**2/(1+(0.05/se)**2):.2f}")
