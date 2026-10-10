#!/usr/bin/env python3
"""Observation-only Toaster L BRANCH -> native Blender Paper Director.
Uses donor code from a pinned checkout on PYTHONPATH; never imports private media into Git.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from haunted_blender import paper_director, scene_growth

SCHEMA = 'vidmage/lbranch-paper-director-proposal/v1'
TOASTER_PIN = '3652c2a96b6b287cda316d1c92daadf7c7417eaf'
ALLOWED = {'breath-led', 'pressure-counterpoint', 'atmosphere-recoil', 'braided-triad'}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def validate(obs):
    if obs.get('schema') != 'vidmage/toaster-lbranch-observation/v1':
        raise ValueError('Wrong observation schema')
    if obs.get('donor', {}).get('commit') != TOASTER_PIN:
        raise ValueError('Wrong Toaster source pin')
    if obs.get('status') != 'observation-only' or any(obs.get('authority', {}).values()):
        raise ValueError('Observation cannot grant creative authority')
    d = obs.get('durationSeconds')
    if not isinstance(d, (float, int)) or not math.isfinite(d) or d <= 0:
        raise ValueError('Bad duration')
    if not isinstance(obs.get('sourceAudioSha256'), str) or len(obs['sourceAudioSha256']) != 64:
        raise ValueError('Missing audio identity')
    bank = obs.get('laneBank', {})
    if bank.get('schema') != 'haunted-toaster/lane-bank/v1' or bank.get('sourceWitnessSha256') != obs.get('responseWitnessSha256'):
        raise ValueError('Bad lane ancestry')
    if not isinstance(bank.get('laneBankHash'), str) or len(bank['laneBankHash']) != 64:
        raise ValueError('Missing Toaster lane-bank identity')
    lanes = bank.get('lanes')
    if not isinstance(lanes, list) or not 1 <= len(lanes) <= 3:
        raise ValueError('Invalid lanes')
    seen = set()
    for lane in lanes:
        key = lane.get('id')
        if key not in {'raw-energy-envelope', 'transient-pressure', 'vocal-salience'} or key in seen:
            raise ValueError('Unknown or duplicate lane')
        seen.add(key)
        if not lane.get('sourceEvidenceHash') or not isinstance(lane.get('knots'), list):
            raise ValueError('Missing lane evidence')
        previous = -1.0
        for knot in lane['knots']:
            at, value = knot.get('atSeconds'), knot.get('value')
            if (not isinstance(at, (float, int)) or not isinstance(value, (float, int))
                or not math.isfinite(at) or not math.isfinite(value)
                or at < previous or at < 0 or at > d + 0.1 or not 0 <= value <= 1):
                raise ValueError('Invalid lane knot')
            previous = at
    if 'raw-energy-envelope' not in seen or 'vocal-salience' in seen:
        raise ValueError('v0 requires energy and refuses untimed vocal evidence')
    if sorted(seen) != sorted(bank.get('laneIds', [])):
        raise ValueError('Lane inventory disagrees')
    sections = obs.get('sections')
    if not isinstance(sections, list) or not 1 <= len(sections) <= 64:
        raise ValueError('Bad sections')
    cursor = 0
    for section in sections:
        start, end = section.get('start'), section.get('end')
        if (not isinstance(start, (int,float)) or not isinstance(end, (int,float))
            or not math.isfinite(start) or not math.isfinite(end)
            or abs(start - cursor) > 0.02 or end <= start or end > d + 0.02):
            raise ValueError('Noncontiguous section gates')
        cursor = end
    if abs(cursor-d) > 0.02:
        raise ValueError('Song not fully covered')
    return bank, sections, d

def level(knots, at):
    if not knots: return 0.0
    if at <= knots[0]['atSeconds']: return knots[0]['value']
    if at >= knots[-1]['atSeconds']: return knots[-1]['value']
    for left, right in zip(knots, knots[1:]):
        if left['atSeconds'] <= at <= right['atSeconds']:
            t = (at-left['atSeconds'])/max(1e-8, right['atSeconds']-left['atSeconds'])
            return left['value']*(1-t)+right['value']*t
    return 0.0

def propose(obs, strategy='breath-led', max_shot_seconds=7):
    bank, sections, d = validate(obs)
    if strategy not in ALLOWED: raise ValueError('Unknown or unsupported L BRANCH strategy')
    track = {'schemaVersion':'0.1', 'id':'vidmage-observed-audio', 'duration':d,
             'gates':[{'id':f'energy-{i:02d}', 'at':round(s['start'], 6),
                       'kind':'section', 'label':s['label']} for i,s in enumerate(sections)]}
    timing = scene_growth.normalize_timing(track)
    plan = paper_director.plan(timing, max_shot_seconds=max_shot_seconds)
    lanes = {r['id']:r['knots'] for r in bank['lanes']}
    shots = []
    for i, old in enumerate(plan['shots']):
        row = dict(old)
        at = (row['start'] + row['end']) / 2
        e = level(lanes['raw-energy-envelope'], at)
        p = level(lanes.get('transient-pressure', []), at)
        if i == 0: kind='ESTABLISH'
        elif i == len(plan['shots'])-1: kind='RETURN'
        elif strategy == 'breath-led':
            kind='WIDE' if e < 0.37 else ('SPEAKER' if e < 0.69 else 'CLOSE_UP')
            if p > 0.68 and e > 0.5: kind='REACTION'
        elif strategy == 'pressure-counterpoint':
            kind='REACTION' if p > 0.40 else ('LYRIC_WORLD' if e < 0.42 else 'WIDE')
        elif strategy == 'atmosphere-recoil':
            kind='WIDE' if e > 0.64 else ('CLOSE_UP' if e < 0.33 else 'SPEAKER')
        else:
            kind='CLOSE_UP' if p > 0.50 else ('WIDE' if e < 0.48 else 'TWO_SHOT')
        row['type'] = kind
        row['reason'] = 'VIDMAGE provisional view from native Toaster lane observations'
        row['toasterEvidence'] = {'laneBankHash':bank['laneBankHash'], 'energy':round(e, 5),
                                  'transient':round(p, 5), 'vocal':'unavailable: untimed lyrics'}
        shots.append(row)
    plan = dict(plan)
    plan['shots'] = shots
    plan['shotTypeCounts'] = {k:sum(s['type']==k for s in shots) for k in sorted(set(s['type'] for s in shots))}
    plan['id'] = 'paper-director-plan:' + digest({k:v for k,v in plan.items() if k!='id'})[:24]
    core = {'schema':SCHEMA, 'status':'proposal-only', 'selectedForRender':False,
            'sourceAudioSha256':obs['sourceAudioSha256'], 'toasterDonorCommit':TOASTER_PIN,
            'laneBankHash':bank['laneBankHash'], 'responseWitnessSha256':obs['responseWitnessSha256'],
            'strategySource':'Toaster L BRANCH vocabulary, not admitted Toaster Mix Plan',
            'chosenProposalStrategy':strategy, 'unavailableLanes':bank['absentLaneIds'],
            'timing':timing, 'paperDirectorPlan':plan, 'noAutomaticLyricTiming':True,
            'noAutomaticAcceptance':True, 'proposedAuthority':{'render':False, 'publish':False, 'edit':False},
            'laws':['AUDIO EVIDENCE != LYRIC TIMING', 'LANE BANK != CANONICAL MIX EXECUTION',
                    'PROPOSAL != KEEP', 'CAMERA VIEW != SOURCE REALITY']}
    return {**core, 'proposalSha256':digest(core)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('observation')
    p.add_argument('output')
    p.add_argument('--strategy', choices=sorted(ALLOWED), default='breath-led')
    p.add_argument('--max-shot-seconds', type=float, default=7)
    args = p.parse_args()
    output = Path(args.output)
    if output.exists(): raise FileExistsError(output)
    proposal = propose(json.loads(Path(args.observation).read_text()), args.strategy, args.max_shot_seconds)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(proposal, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'proposal':str(output), 'shotCount':proposal['paperDirectorPlan']['shotCount'],
                      'laneBankHash':proposal['laneBankHash'], 'proposalSha256':proposal['proposalSha256']}))
if __name__ == '__main__': main()
