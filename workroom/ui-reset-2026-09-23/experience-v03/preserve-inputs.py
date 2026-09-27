from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).parent
dst=root/'references';dst.mkdir(exist_ok=True)
inputs=[
('676cbd01-e09c-42ba-93fa-16a505eb7c36','01-workspace-preview.png','Codex conversation beside study 02 in a right-hand browser tab. User rejects the study styling.'),
('3d27cfa3-aece-4517-987f-a02ff751de16','02-tabbed-subagents.png','Same right-hand area hosts a Subagents tab beside a browser tab; composer has image thumbnails.'),
('d6fed9a7-239f-48e1-8bd5-30bb9578dba1','03-task-context-panel.png','Task context popover: project/branch, subagents and sources. Does not show plugin attachment semantics.'),
('6e4eb698-0e57-462a-8a8c-37f67e368e74','04-work-area-launcher.png','Right-hand work-area launcher lists Review, Terminal, Browser, Files and Side chat.'),
('7b27ad67-14ea-486e-b744-8ebe6151b781','05-conversation-navigator.png','Red circle identifies left-side conversation markers with hover-style earlier-exchange preview and bookmark icon; exact interaction not tested.')]
records=[]
for uid,name,description in inputs:
    src=Path('C:/Users/Mubarak/AppData/Local/Temp')/('codex-clipboard-'+uid+'.png')
    shutil.copy2(src,dst/name)
    data=(dst/name).read_bytes()
    records.append({'file':name,'original':str(src),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'observation':description,'evidence':'User-supplied screenshot; not live computer-use verification'})
(dst/'manifest.json').write_text(json.dumps({'captured':'User supplied 2026-09-23','plusMenu':'None of these screenshots shows the expanded plus menu. No menu contents inferred.','images':records},indent=2)+'\n',encoding='utf-8')
print('Preserved five original screenshots and their hashes.')
