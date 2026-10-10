#!/usr/bin/env node
'use strict';
// Native Haunted Toaster lyric parser. Plain lyrics are NOT measured vocal time.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
function capture(toasterRoot, lyricFile, duration) {
  const { createLyricTrack }=require(path.resolve(toasterRoot,'src/full-measure/src/render/lyrics.cjs'));
  const bytes=fs.readFileSync(lyricFile);
  const track=createLyricTrack(bytes.toString('utf8'),duration);
  const timed=track.timed===true && track.mode.startsWith('timestamped-');
  return {
    schema:'vidmage/toaster-lyric-evidence/v1', status:'observation-only',
    donor:'the-static-collective/the-haunted-toaster@3652c2a96b6b287cda316d1c92daadf7c7417eaf',
    sourceSha256:crypto.createHash('sha256').update(bytes).digest('hex'),
    mode:track.mode, timed, cueCount:track.cues.length,
    // Toaster's evenly distributed lines are display guesses, not voice evidence.
    cues:timed ? track.cues : [],
    requiresManualTiming:!timed, userAccepted:false,
    law:'PLAIN LYRICS != PERFORMED VOCAL TIMING',
  };
}
if(require.main===module) {
  const args=process.argv.slice(2);
  if(args.length!==4) {
    console.error('Usage: node toaster_listener_gate.cjs TOASTER_ROOT LYRICS_FILE DURATION OUTPUT_JSON');
    process.exit(2);
  }
  const [root,lyrics,duration,out]=args;
  const dest=path.resolve(out);
  if(fs.existsSync(dest))throw Error('Will not replace lyric evidence');
  const result=capture(root,lyrics,Number(duration));
  fs.mkdirSync(path.dirname(dest),{recursive:true});
  fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({timed:result.timed,mode:result.mode,usableCues:result.cues.length,needsHuman:result.requiresManualTiming}));
}
module.exports={capture};
