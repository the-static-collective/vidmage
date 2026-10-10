#!/usr/bin/env node
'use strict';
// VIDMAGE observation adapter. Calls pinned *native Toaster code*;
// neither preview focus nor lane inspection grants KEEP/render/publication.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const args = process.argv.slice(2);
function arg(flag) {
  const i = args.indexOf(flag);
  if (i < 0 || !args[i + 1]) throw Error('Missing ' + flag);
  return args[i + 1];
}
function sha256(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}
async function main() {
  const root = path.resolve(arg('--toaster-root'));
  const audio = path.resolve(arg('--audio'));
  const output = path.resolve(arg('--out'));
  if (output === audio || fs.existsSync(output)) throw Error('Will not overwrite an existing file');
  const src = path.join(root, 'src/full-measure/src');
  const { inspectAudio } = require(path.join(src, 'render/analyze.cjs'));
  const { deriveResponseWitness } = require(path.join(src, 'generation/nested-response.cjs'));
  const { buildLaneBank, STRATEGIES } = require(path.join(src, 'generation/l-branch.cjs'));
  const analysis = await inspectAudio(audio);
  const witness = deriveResponseWitness({
    energySamples: analysis.energySamples,
    sections: analysis.sections.map(s => ({ startSeconds:s.start, endSeconds:s.end, energy:s.energy })),
    durationSeconds: analysis.duration,
  });
  // A plain lyric sheet is NOT timed vocal-salience evidence.
  const bank = buildLaneBank({ responseWitness:witness, lyricTrack:null });
  const report = {
    schema:'vidmage/toaster-lbranch-observation/v1', status:'observation-only',
    donor:{ repository:'the-static-collective/the-haunted-toaster',
      commit:'3652c2a96b6b287cda316d1c92daadf7c7417eaf',
      implementation:'native inspectAudio + deriveResponseWitness + buildLaneBank' },
    sourceAudioSha256:sha256(audio),
    durationSeconds:analysis.duration,
    sectionSource:'audio-inferred; not lyrics or editorial acts',
    sections:analysis.sections.map(s => ({start:s.start,end:s.end,energy:s.energy,label:s.label})),
    responseWitnessSha256:witness.witnessSha256,
    laneBank:bank,
    strategyTemplates:STRATEGIES.map(s => ({id:s.id,sends:s.sends})),
    absentLaneIds:bank.absentLaneIds,
    authority:{camera:false,keep:false,render:false,publication:false},
  };
  fs.mkdirSync(path.dirname(output), {recursive:true});
  fs.writeFileSync(output, JSON.stringify(report,null,2)+'\n', {flag:'wx'});
  console.log(JSON.stringify({output,duration:analysis.duration,sections:report.sections.length,
    lanes:bank.laneIds,laneBankHash:bank.laneBankHash,strategies:STRATEGIES.length}));
}
main().catch(err => { console.error(err.stack || String(err)); process.exitCode=1; });
