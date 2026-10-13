import json,sys,os,glob
d,out=sys.argv[1],sys.argv[2]
rows=[]
for meta in sorted(glob.glob(os.path.join(d,'*.meta.json'))):
    aid=os.path.basename(meta).replace('.meta.json','')
    m=json.load(open(meta,encoding='utf-8'))
    jl=os.path.join(d,aid+'.jsonl')
    prompt='';last='';model='';first='';lastts='';n=0
    if os.path.exists(jl):
        for line in open(jl,encoding='utf-8'):
            try:r=json.loads(line)
            except:continue
            ts=r.get('timestamp','')
            if ts and not first:first=ts
            if ts:lastts=ts
            msg=r.get('message',{})
            if r.get('type')=='user' and not prompt:
                c=msg.get('content');prompt=c if isinstance(c,str) else ' '.join(b.get('text','') for b in c if b.get('type')=='text')
            if r.get('type')=='assistant':
                n+=1;model=msg.get('model',model)
                c=msg.get('content')
                if isinstance(c,list):
                    t='\n'.join(b.get('text','') for b in c if b.get('type')=='text')
                    if t.strip():last=t
    rows.append((first,aid,m,model,n,lastts,prompt,last,os.path.exists(jl)))
rows.sort()
with open(out,'w',encoding='utf-8') as o:
    for first,aid,m,model,n,lastts,prompt,last,has in rows:
        o.write(f"\n\n==================== {aid}\ndesc: {m.get('description')} | type: {m.get('agentType')} | model: {model} | depth: {m.get('spawnDepth')} | parent: {m.get('parentAgentId','main')} | turns: {n} | {first} -> {lastts} | transcript: {has}\n--- PROMPT (first 2500)\n{prompt[:2500]}\n--- FINAL OUTPUT (last 3000)\n{last[-3000:]}\n")
print(len(rows))
