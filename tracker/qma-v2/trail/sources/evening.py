import json,sys
src,odlg,oag,oskill=sys.argv[1:5]
START='2026-10-13T15:50'
dlg=open(odlg,'w',encoding='utf-8'); ag=open(oag,'w',encoding='utf-8'); sk=open(oskill,'w',encoding='utf-8')
dlg.write('# Planning session 2026-10-13 evening: operator messages and Claude replies\n\nExtracted from the session transcript (2cf20068). Times are UTC (local is UTC+3). Tool calls are listed by name only; agent briefs are in agent-briefs.md.\n')
ag.write('# Agent briefs used on 2026-10-13 evening\n\nEvery Agent call, in order, with its model and full prompt. Reuse these as templates; adapt paths and drop OpenAI-engine parts for the one-engine re-plan.\n')
sk.write('# Skill and command calls on 2026-10-13 evening\n\n| time (UTC) | tool | what |\n|---|---|---|\n')
n=0
for line in open(src,encoding='utf-8'):
    try:r=json.loads(line)
    except:continue
    ts=r.get('timestamp','')
    if ts<START or r.get('isSidechain'): continue
    t=r.get('type'); m=r.get('message',{})
    if t=='user':
        c=m.get('content')
        if isinstance(c,list):
            if any(b.get('type')=='tool_result' for b in c): continue
            c='\n'.join(b.get('text','') for b in c if b.get('type')=='text')
        if not c or c.startswith('<task-notification') or c.startswith('<system-reminder') and 'agent-message' in c: 
            if c and 'Subagent hand-back' in c: dlg.write(f'\n\n--- {ts} [agent report arrived]\n')
            continue
        if 'Subagent hand-back' in c: dlg.write(f'\n\n--- {ts} [agent report arrived]\n'); continue
        dlg.write(f'\n\n## OPERATOR {ts}\n\n{c}\n')
    elif t=='assistant':
        c=m.get('content')
        if not isinstance(c,list): continue
        txt='\n'.join(b.get('text','') for b in c if b.get('type')=='text').strip()
        tools=[b for b in c if b.get('type')=='tool_use']
        if txt: dlg.write(f'\n\n### CLAUDE {ts}\n\n{txt}\n')
        for b in tools:
            nm=b['name']; inp=b.get('input',{})
            if nm=='Agent':
                n+=1
                ag.write(f"\n\n## {n}. {inp.get('description')} | model {inp.get('model','(default)')} | type {inp.get('subagent_type')} | {ts}\n\n```text\n{inp.get('prompt','')}\n```\n")
                dlg.write(f"\n[Agent: {inp.get('description')} on {inp.get('model')}]\n")
            elif nm in('Skill','AskUserQuestion','TaskStop'):
                what=inp.get('skill') or (inp.get('task_id') if nm=='TaskStop' else '; '.join(q.get('header','') for q in inp.get('questions',[])))
                sk.write(f'| {ts} | {nm} | {what} |\n'); dlg.write(f'\n[{nm}: {what}]\n')
print(n)
