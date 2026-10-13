import json,sys,os
src,out=sys.argv[1],sys.argv[2]
def txt(c):
    if isinstance(c,str): return c
    parts=[]
    for b in c or []:
        t=b.get('type')
        if t=='text': parts.append(b['text'])
        elif t=='tool_use':
            inp=b.get('input',{})
            s=json.dumps(inp,ensure_ascii=False)
            if b['name'] in ('Agent','Workflow','AskUserQuestion','Write','Edit'): lim=3000
            else: lim=300
            parts.append(f"[TOOL {b['name']}] {s[:lim]}")
        elif t=='tool_result':
            cc=b.get('content')
            if isinstance(cc,list): cc=' '.join(x.get('text','') for x in cc if isinstance(x,dict))
            parts.append(f"[RESULT] {str(cc)[:400]}")
    return '\n'.join(parts)
n=0
with open(src,encoding='utf-8') as f, open(out,'w',encoding='utf-8') as o:
    for line in f:
        try: r=json.loads(line)
        except: continue
        if r.get('type') not in ('user','assistant'): continue
        m=r.get('message',{}); role=m.get('role')
        t=txt(m.get('content'))
        if not t.strip(): continue
        n+=1
        o.write(f"\n### {n} {role.upper()} {r.get('timestamp','')}\n{t}\n")
print(n)
