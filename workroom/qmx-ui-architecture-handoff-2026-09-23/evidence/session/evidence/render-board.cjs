const fs=require('fs'),path=require('path');
const sharp=require('../../../.scratch/qmx-storyboard-tools/node_modules/sharp');
const scene=JSON.parse(fs.readFileSync(__dirname+'/scene.json'));
const assets=JSON.parse(fs.readFileSync(__dirname+'/assets.json'));
const files=Object.fromEntries(assets.map(a=>[a.fileId,'data:image/png;base64,'+fs.readFileSync(a.path).toString('base64')]));
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function draw(e){if(e.isDeleted)return ''; const {x,y,width:w,height:h}=e;const fill=e.backgroundColor==='transparent'?'none':e.backgroundColor||'none';const stroke=e.strokeColor||'#111';const style=`stroke="${stroke}" stroke-width="${e.strokeWidth||1}" fill="${fill}"`;let s='';
if(e.type==='image'&&files[e.fileId]) s=`<image x="${x}" y="${y}" width="${w}" height="${h}" href="${files[e.fileId]}"/>`;
if(e.type==='rectangle'||e.type==='embeddable') s=`<rect x="${x}" y="${y}" width="${w}" height="${h}" ${style}/>`;
if(e.type==='ellipse') s=`<ellipse cx="${x+w/2}" cy="${y+h/2}" rx="${w/2}" ry="${h/2}" ${style}/>`;
if(e.type==='diamond') s=`<polygon points="${x+w/2},${y} ${x+w},${y+h/2} ${x+w/2},${y+h} ${x},${y+h/2}" ${style}/>`;
if(['line','arrow','freedraw'].includes(e.type)) s=`<polyline points="${e.points.map(p=>[x+p[0],y+p[1]].join(',')).join(' ')}" ${style} ${e.type==='arrow'?'marker-end="url(#arrow)"':''}/>`;
if(e.type==='text')s=`<text fill="${stroke}" font-family="Arial" font-size="${e.fontSize||20}">${e.text.split('\n').map((l,i)=>`<tspan x="${x}" y="${y+(i+0.85)*(e.fontSize||20)*(e.lineHeight||1.25)}">${esc(l)}</tspan>`).join('')}</text>`;
return `<g opacity="${(e.opacity??100)/100}" transform="rotate(${(e.angle||0)*180/Math.PI} ${x+w/2} ${y+h/2})">${s}</g>`;}
const content=scene.elements.map(draw).join('');
const zones=[['shell',-4400,-5700,12500,2600],['agent-layouts',-4800,-2200,13500,8000],['alternate-layouts',-4700,6000,13200,7000],['settings',8500,-500,10500,6500],['annotated-dashboard',5700,14800,7400,5000]];
(async()=>{for(const [name,x,y,w,h] of zones){const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${Math.round(2000)}" height="${Math.round(2000*h/w)}" viewBox="${x} ${y} ${w} ${h}"><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#888"/></marker></defs><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="white"/>${content}</svg>`;await sharp(Buffer.from(svg)).png().toFile(__dirname+'/'+name+'.png');} console.log('Rendered five spatial evidence views; approximate shapes/fonts, original image placements.');})();
