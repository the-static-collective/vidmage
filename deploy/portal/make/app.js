'use strict';
// Browser-only. This page contains NO external requests, analytics, cookies, or provider API keys.
const FORMAT='vidmage/paula-shotkit/v1';
const POCKET='vidmage/paula-pocket-project/v1';
const KEY='vidmage-paula-shotkit-v1';
const $=id=>document.getElementById(id);
const safe=x=>String(x??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const clipLength=n=>Math.max(1,Math.min(30,Math.round(Number(n)||5)));
const limit=(v,n)=>String(v??'').slice(0,n);
const identifier=()=>{const bytes=new Uint8Array(12);crypto.getRandomValues(bytes);return 'shot-'+Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('')};
function shot(){return {id:identifier(),name:'A new moment',action:'',camera:'A gentle, steady camera move',seconds:5,downloaded:false}}
function fresh(){return {format:FORMAT,title:'My Little Movie',story:'',characters:'',mood:'Gentle family',ratio:'9:16',shots:[shot()],updatedAt:new Date().toISOString()}}
function normalized(x){
 if(!x||x.format!==FORMAT||!Array.isArray(x.shots)||x.shots.length<1||x.shots.length>12)throw Error('Not a valid Paula shot-kit backup');
 if(x.shots.some(s=>!s||typeof s!=='object'))throw Error('Invalid shot cards');
 const used=new Set();
 return {format:FORMAT,title:limit(x.title,120),story:limit(x.story,5000),
  characters:limit(x.characters,1800),
  mood:['Gentle family','Christian romance','Joyful storybook','Quiet and hopeful','Other cinematic'].includes(x.mood)?x.mood:'Gentle family',
  ratio:['9:16','16:9','1:1'].includes(x.ratio)?x.ratio:'9:16',
  shots:x.shots.map(s=>{
   const id=typeof s.id==='string'&&/^shot-[a-f0-9]{24}$/.test(s.id)&&!used.has(s.id)?s.id:identifier();
   used.add(id);
   return {id,name:limit(s.name,110),action:limit(s.action,1600),camera:limit(s.camera,180),seconds:clipLength(s.seconds),downloaded:s.downloaded===true}
  }),updatedAt:new Date().toISOString()};
}
let kit;
let noticeTimeout;
function flash(msg){
 $('notice').hidden=false;$('notice').textContent=msg;
 clearTimeout(noticeTimeout);noticeTimeout=setTimeout(()=>$('notice').hidden=true,5000);
}
function persist(){
 kit.updatedAt=new Date().toISOString();
 try{localStorage.setItem(KEY,JSON.stringify(kit))}
 catch(e){flash('Safari storage unavailable. Download a backup before leaving.')}
}
function syncFields(){
 for(const field of ['title','story','characters','mood','ratio'])$(field).value=kit[field];
}
function getDuration(){return kit.shots.reduce((acc,s)=>acc+clipLength(s.seconds),0)}
function updateCounters(){
 const count=kit.shots.length,total=getDuration();
 $('count').textContent=count+' of 12 scenes';
 $('add').disabled=count>=12;
 $('total').textContent=total+' sec planned · '+kit.shots.filter(s=>s.downloaded).length+' clips marked downloaded'+(total>90?' · Trim below 90 sec for the local cut':'');
 $('total').style.color=total>90?'#9b2833':'';
}
function renderShots(){
 const region=$('shots');region.replaceChildren();
 kit.shots.forEach((s,index)=>{
  const card=document.createElement('article');
  card.className='shot';card.dataset.id=s.id;
  card.innerHTML=
  '<div class="shot-head"><span class="shot-number">Scene '+(index+1)+'</span>'+
   '<div class="row"><button type="button" data-act="up" aria-label="Move scene up"'+(index===0?' disabled':'')+'>↑</button>'+
   '<button type="button" data-act="down" aria-label="Move scene down"'+(index===kit.shots.length-1?' disabled':'')+'>↓</button>'+
   '<button type="button" data-act="remove" aria-label="Delete scene">Delete</button></div></div>'+
   '<label>Scene name <input data-field="name" maxlength="110" value="'+safe(s.name)+'"></label>'+
   '<label>What happens? <textarea data-field="action" maxlength="1600" placeholder="One action in one continuous camera shot…">'+safe(s.action)+'</textarea></label>'+
   '<label>Camera movement <input data-field="camera" maxlength="180" value="'+safe(s.camera)+'"></label>'+
   '<div class="cols"><div><label>Approximate length (seconds) <input class="duration" data-field="seconds" type="number" min="1" max="30" step="1" value="'+s.seconds+'"></label></div>'+
   '<div><label class="checkbox" style="margin-top:27px"><input data-field="downloaded" type="checkbox"'+(s.downloaded?' checked':'')+'> I saved the MP4 to Files</label></div></div>'+
   '<div class="row"><button type="button" class="primary" data-act="copy">Copy this Kling prompt</button>'+
   '<a class="button" href="https://kling.ai/" target="_blank" rel="noopener noreferrer">Open Kling ↗</a></div>';
  region.append(card);
 });
 updateCounters();
}
function promptFor(s,index){
 const total=kit.shots.length;
 return [
  'VIDEO SHOT '+(index+1)+' OF '+total+' — '+(kit.title||'Untitled little movie'),
  'Create ONE continuous, cinematic '+clipLength(s.seconds)+'-second shot. Frame: '+kit.ratio+'.',
  'Overall story: '+(kit.story||'A small hopeful moment.'),
  'Tone: '+kit.mood+'.',
  'Maintain character and prop continuity across the film: '+(kit.characters||'Consistent people, clothes, setting and lighting.'),
  'Scene title: '+(s.name||'A new moment')+'.',
  'On-screen action: '+(s.action||'A gentle moment unfolds.')+'.',
  'Camera: '+(s.camera||'A natural, gentle camera move')+'.',
  'Realistic movements and hands. Keep the same cast across shots. No random cutaways, extra people, unwanted logos, subtitles or text.',
  'Only this shot—not the entire movie. Add your own reference image inside Kling if needed.'
 ].join('\n');
}
async function copyText(text){
 try{await navigator.clipboard.writeText(text);flash('Prompt copied. Paste it into Kling.');return}
 catch(e){}
 const t=document.createElement('textarea');t.value=text;t.style.position='fixed';t.style.left='-9999px';document.body.append(t);t.select();
 const ok=document.execCommand('copy');t.remove();
 if(ok){flash('Prompt copied. Paste it into Kling.')}
 else window.prompt('Select and copy the Kling prompt:',text);
}
function saveJSON(name,value){
 const data=JSON.stringify(value,null,2);
 const url=URL.createObjectURL(new Blob([data],{type:'application/json'}));
 const link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),15000);
 flash('Backup saved. Check Files / Downloads on your phone.');
}
function pocketProject(){
 const total=getDuration();
 const length=total<=20?20:total<=60?60:90;
 let start=0;
 const scenes=kit.shots.map((s,i)=>{
  const time=start+'–'+Math.min(length,start+clipLength(s.seconds));start+=clipLength(s.seconds);
  return {id:'shot-'+(i+1),time,title:s.name||'Scene '+(i+1),action:s.action||'A gentle moment unfolds.',dialogue:''};
 });
 return {format:POCKET,projectId:'pocket-'+identifier().slice(5),title:kit.title,story:kit.story,
  characters:kit.characters,duration:length,mood:kit.mood,scenes,endTitle:'',promptDraft:'',flowLink:'',reviewNote:'',
  receipts:[],updatedAt:new Date().toISOString()};
}
function init(){
 try{const saved=localStorage.getItem(KEY);kit=saved?normalized(JSON.parse(saved)):fresh()}
 catch(e){kit=fresh();flash('Old notebook could not be read; start fresh or restore a backup.')}
 syncFields();renderShots();persist();
}
for(const key of ['title','story','characters','mood','ratio']){
 $(key).addEventListener('input',e=>{kit[key]=e.target.value;persist()});
}
$('shots').addEventListener('input',e=>{
 const card=e.target.closest('[data-id]');if(!card)return;
 const field=e.target.dataset.field;
 if(!['name','action','camera','seconds','downloaded'].includes(field))return;
 const s=kit.shots.find(s=>s.id===card.dataset.id);if(!s)return;
 s[field]=field==='downloaded'?e.target.checked:field==='seconds'?clipLength(e.target.value):e.target.value;
 persist();if(field==='seconds'||field==='downloaded')updateCounters();
});
$('shots').addEventListener('click',async e=>{
 const button=e.target.closest('button[data-act]'),card=e.target.closest('[data-id]');
 if(!button||!card)return;
 const index=kit.shots.findIndex(s=>s.id===card.dataset.id);
 if(index<0)return;
 switch(button.dataset.act){
  case 'copy':await copyText(promptFor(kit.shots[index],index));break;
  case 'remove':if(kit.shots.length<2){flash('Keep at least one scene.');return}
   if(!confirm('Remove this scene from your notebook?'))return;
   kit.shots.splice(index,1);persist();renderShots();break;
  case 'up':case 'down':{
   const dest=index+(button.dataset.act==='up'?-1:1);
   if(dest<0||dest>=kit.shots.length)return;
   [kit.shots[index],kit.shots[dest]]=[kit.shots[dest],kit.shots[index]];
   persist();renderShots();break;}
 }
});
$('add').addEventListener('click',()=>{
 if(kit.shots.length>=12)return flash('This first cut supports up to 12 scenes.');
 kit.shots.push(shot());persist();renderShots();
});
$('save').addEventListener('click',()=>saveJSON('paula-kling-shotkit.json',kit));
$('copyAll').addEventListener('click',()=>copyText(kit.shots.map(promptFor).join('\n\n'+ '-'.repeat(32)+'\n\n')));
$('import').addEventListener('click',()=>$('importFile').click());
$('importFile').addEventListener('change',async e=>{
 const f=e.target.files?.[0];if(!f)return;
 try{
  if(f.size>100000)throw Error('Backup is too large');
  const incoming=normalized(JSON.parse(await f.text()));
  if(!confirm('Replace the current shot notebook with this backup? Download your current version first if needed.'))return;
  kit=incoming;syncFields();persist();renderShots();flash('Shot-kit backup restored.');
 }catch(err){flash('Restore refused: '+err.message)}finally{e.target.value=''}
});
$('exportPocket').addEventListener('click',()=>{
 if(getDuration()>90)return flash('Shorten the plan to at most 90 seconds before exporting to Vidmage.');
 saveJSON('paula-vidmage-story-draft.json',pocketProject());
});
init();
