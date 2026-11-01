import random, math
random.seed(7)
def sim(f, p=0.55, win=1.0, n=500, runs=4000, floor=0.6):
    hit=0; finals=[]
    for _ in range(runs):
        w=1.0; touched=False
        for _ in range(n):
            if random.random()<p: w*=1+f*win
            else: w*=1-f
            if w<=floor: touched=True
        hit+=touched; finals.append(w)
    finals.sort()
    return hit/runs, finals[len(finals)//2]
# edge: p=0.55 at 1:1 => mean 0.1R, sd ~0.995R ; full Kelly f=0.1
for f in (0.005,0.01,0.025,0.05,0.08,0.10):
    h,m=sim(f)
    print(f"risk {f*100:.1f}%  P(touch -40% in 500 trades)={h:.3f}  median end x{m:.2f}")
# if true edge is half (p=0.525)
for f in (0.01,0.05,0.08):
    h,m=sim(f,p=0.525)
    print(f"[edge halved] risk {f*100:.1f}%  P(touch -40%)={h:.3f}  median end x{m:.2f}")
# losing streak drawdown
for k in (5,7,10):
    print(k, "losses at 8%:", round(1-0.92**k,3), "at 1%:", round(1-0.99**k,3))
