import json,sys
src,out=sys.argv[1],sys.argv[2]
with open(src,encoding='utf-8') as f, open(out,'w',encoding='utf-8') as o:
    for line in f:
        try: r=json.loads(line)
        except: continue
        t=r.get('type')
        if t not in('user','assistant') or r.get('isSidechain'): continue
        c=r['message'].get('content')
        if t=='user':
            if isinstance(c,list):
                if any(b.get('type')=='tool_result' for b in c): continue
                c='\n'.join(b.get('text','') for b in c if b.get('type')=='text')
            if not c.strip() or c.startswith('<task-notification'): continue
            o.write(f"\n\n######## OPERATOR {r.get('timestamp')}\n{c}\n")
        else:
            if isinstance(c,str): txt=c
            else:
                txt='\n'.join(b.get('text','') for b in c if b.get('type')=='text')
                tools=[b for b in c if b.get('type')=='tool_use']
                for b in tools:
                    if b['name'] in('Agent','AskUserQuestion'):
                        txt+=f"\n[{b['name']}] "+json.dumps(b['input'],ensure_ascii=False)[:1500]
            if txt.strip(): o.write(f"\n--- CLAUDE {r.get('timestamp')}\n{txt}\n")
