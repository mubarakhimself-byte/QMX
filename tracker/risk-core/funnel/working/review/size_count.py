"""Reviewer's count of how much the funnel narrowed. Read-only over FUNNEL.md, HYBRID-FATES.md, ledger-merge.yaml.
Run: python -I size_count.py  (from funnel/working/review)"""
import re,io,sys
root="../../"
F=open(root+"FUNNEL.md",encoding="utf-8").read().split("\n")
# decision points
dp=[];cur=None
for i,l in enumerate(F):
    m=re.match(r"#### DP(\d+)\. (.*)",l)
    if m:
        cur={"n":int(m.group(1)),"t":m.group(2),"line":i+1,"opts":None,"pick":None,"scores":{}}
        dp.append(cur)
    if cur is None: continue
    if l.startswith("Options:") and cur["opts"] is None:
        cur["opts"]=l
    m=re.match(r"- \(([a-z])\) P(\d) S(\d) E(\d) A(\d) F(\d) C(\d)",l)
    if m: cur["scores"][m.group(1)]=tuple(map(int,m.groups()[1:]))
    m=re.match(r"\*\*Pick \(([a-z])\)",l)
    if m and cur["pick"] is None: cur["pick"]=m.group(1)
idre=re.compile(r"X\d-H?\d+|H\d\d")
tot=0
print("DP pick | ids in option (a) | ; parts in (a) | pick score P S E A F C | best rival total")
from collections import Counter
ecount=Counter()
for d in dp:
    o=d["opts"]
    a=o.split("(b)")[0]
    ids=set(re.findall(r"X\d-H?\d+",a))
    parts=a.count(";")+a.count(",")+1
    s=d["scores"].get(d["pick"])
    rivals=[sum(v) for k,v in d["scores"].items() if k!=d["pick"]]
    ecount[s[2]]+=1
    print(f"DP{d['n']:<3} ({d['pick']}) | {len(ids):>3} | {parts:>3} | {s} sum {sum(s)} | {max(rivals) if rivals else '-'}")
    tot+=len(ids)
print("picks that are option (a):",sum(1 for d in dp if d['pick']=='a'),"of",len(dp))
print("E score of picks:",dict(ecount))
print("ids named across option (a)s:",tot)
# fates
H=open(root+"HYBRID-FATES.md",encoding="utf-8").read().split("\n")
c=Counter()
for l in H:
    m=re.match(r"\| (X\d-H?\d+) \| (\w+) \|",l)
    if m: c[m.group(2)]+=1
print("fates by row:",dict(c),"total",sum(c.values()))
# ledger
Y=open(root+"ledger-merge.yaml",encoding="utf-8").read()
dups=len(re.findall(r"^  - keep: ",Y.split("aliases:")[0],flags=re.M))
merges=Y.split("merges:")[1].split("dies:")[0]
ab=sum(len([x for x in m.split(",") if x.strip()]) for m in re.findall(r"absorb: \[([^\]]*)\]",merges))
al=Y.split("aliases:")[1].split("merges:")[0]
alab=sum(len([x for x in m.split(",") if x.strip()]) for m in re.findall(r"absorb: \[([^\]]*)\]",al))
dies=Y.split("dies:")[1].split("rename:")[0]
dn=len(re.findall(r"- id:",dies)); keepn=len(re.findall(r"keep: true",dies))
print(f"ledger: duplicates {dups}, alias absorbs {alab}, merge absorbs {ab}, dies {dn} of which NOT dead {keepn}")
print("variables left about:",903-dups-alab-ab-(dn-keepn),"(status dropped keeps the row in some cases)")
