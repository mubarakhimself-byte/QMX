const fs=require('fs');
const lz=require('../../../../.scratch/qmx-storyboard-tools/node_modules/lz-string');
const source='C:/Users/Mubarak/Documents/brain/brain/Excalidraw/qmx-ui-storyboard.md';
const md=fs.readFileSync(source,'utf8');
const block=md.match(/```compressed-json\s+([\s\S]*?)```/);
if(!block) throw Error('Compressed drawing missing');
const scene=JSON.parse(lz.decompressFromBase64(block[1].replace(/\s+/g,'')));
fs.writeFileSync(__dirname+'/scene.json',JSON.stringify(scene,null,2));
fs.writeFileSync(__dirname+'/markdown-prose.md',md.split('%%')[0]);
const links=[...md.matchAll(/([a-f0-9]{40}): \[\[([^\]]+)\]\]/g)].map(m=>({fileId:m[1],name:m[2],path:'C:/Users/Mubarak/Documents/brain/brain/'+m[2]}));
fs.writeFileSync(__dirname+'/attachments.json',JSON.stringify(links,null,2));
const nondeleted=(scene.elements||[]).filter(e=>!e.isDeleted);
const texts=nondeleted.filter(e=>e.type==='text').map(e=>({id:e.id,x:e.x,y:e.y,text:e.text,groupIds:e.groupIds||[],boundElements:e.boundElements||[],containerId:e.containerId||null}));
fs.writeFileSync(__dirname+'/scene-text.json',JSON.stringify(texts,null,2));
console.log(JSON.stringify({markdownBytes:Buffer.byteLength(md),markdownProse:md.split('%%')[0].length,sceneElementCount:(scene.elements||[]).length,nondeleted:nondeleted.length,types:nondeleted.reduce((a,e)=>(a[e.type]=(a[e.type]||0)+1,a),{}),textCount:texts.length,attachments:links,images:nondeleted.filter(e=>e.type==='image').map(e=>({id:e.id,fileId:e.fileId,x:e.x,y:e.y,width:e.width,height:e.height})),deleted:(scene.elements||[]).filter(e=>e.isDeleted).map(e=>({id:e.id,type:e.type,text:e.text}))},null,2));

