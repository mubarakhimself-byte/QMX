import json,sys
src,out=sys.argv[1],sys.argv[2]
with open(src,encoding='utf-8') as f, open(out,'w',encoding='utf-8') as o:
    for line in f:
        try: r=json.loads(line)
        except: continue
        if r.get('type')!='user' or r.get('isMeta') or r.get('isSidechain'): continue
        c=r['message'].get('content')
        if isinstance(c,list):
            if any(b.get('type')=='tool_result' for b in c): continue
            c='\n'.join(b.get('text','') for b in c if b.get('type')=='text')
        if not c.strip() or c.startswith('<task-notification') or '<system-reminder>' in c[:50]: 
            if c.startswith('<task-notification'): o.write(f"\n--- {r.get('timestamp')} [task-notification]\n")
            continue
        o.write(f"\n=== {r.get('timestamp')}\n{c[:6000]}\n")
