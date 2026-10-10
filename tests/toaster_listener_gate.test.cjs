const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {capture}=require('../bridge/toaster_listener_gate.cjs');
const donor=process.env.VIDMAGE_TOASTER_ROOT;
if(!donor)throw Error('VIDMAGE_TOASTER_ROOT required: use exact pinned donor checkout');
test('plain lyrics do not impersonate human-timed vocals',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'vidmage-listener-'));
 try{
  const file=path.join(dir,'plain.txt');
  fs.writeFileSync(file,'[Verse 1]\nRosemary roses\nBlooming blue\n');
  const x=capture(donor,file,12);
  assert.equal(x.timed,false);
  assert.equal(x.requiresManualTiming,true);
  assert.equal(x.userAccepted,false);
  assert.equal(x.mode,'evenly-distributed');
  assert.deepEqual(x.cues,[]);
  assert.equal(x.cueCount,2);
 }finally{fs.rmSync(dir,{recursive:true,force:true})}
});
test('actual timecoded LRC is accepted as timed input, not automatic KEEP',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'vidmage-listener-'));
 try{
  const file=path.join(dir,'timed.lrc');
  fs.writeFileSync(file,'[00:01.00]First line\n[00:04.50]Second line\n');
  const x=capture(donor,file,12);
  assert.equal(x.timed,true);
  assert.equal(x.mode,'timestamped-lrc');
  assert.equal(x.cues.length,2);
  assert.equal(x.cues[1].start,4.5);
  assert.equal(x.userAccepted,false);
 }finally{fs.rmSync(dir,{recursive:true,force:true})}
});
