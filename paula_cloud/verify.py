"""Verify Paula cloud receipts; optionally compare exact rendered MP4 bytes.

Content-hash only proof is weaker than verifying server-local HMAC. Neither
establishes third-party consent or aesthetic quality.
"""
from __future__ import annotations
import argparse
import hashlib
import hmac
import json
from pathlib import Path
from paula.receipt import canonical,digest
from paula_cloud.engine import sha_file

class InvalidCloudReceipt(ValueError):pass

def verify(data:dict,secret:bytes|None=None,media:Path|None=None):
    if not isinstance(data,dict) or data.get('format')!='vidmage/paula-cloud-export/v1':
        raise InvalidCloudReceipt('Invalid export envelope')
    receipts=data.get('receipts');pid=data.get('project_id')
    if not isinstance(receipts,list) or not isinstance(pid,str) or len(receipts)>300:
        raise InvalidCloudReceipt('Invalid export identity or size')
    prev=None
    allowed={'POCKET_STORY_RECEIVED','SOURCE_ASSET_RECEIVED','RENDER_REQUESTED','LOCAL_MP4_VERIFIED','RENDER_FAILED'}
    verified=[]
    for i,r in enumerate(receipts):
        if not isinstance(r,dict) or set(r)!={'format','event','created_at','previous_sha256','payload','sha256','hmac_sha256'}:
            raise InvalidCloudReceipt(f'Invalid fields at {i}')
        if r['format']!='vidmage/paula-cloud-receipt/v1' or r['event'] not in allowed or r['previous_sha256']!=prev:
            raise InvalidCloudReceipt(f'Invalid ancestry or event at {i}')
        if not isinstance(r['payload'],dict) or not isinstance(r['sha256'],str):raise InvalidCloudReceipt('Invalid payload')
        core={key:r[key] for key in ('format','event','created_at','previous_sha256','payload')}
        if digest(core)!=r['sha256']:
            raise InvalidCloudReceipt(f'Hash mismatch at {i}')
        if secret is not None:
            expected=hmac.new(secret,canonical({**core,'sha256':r['sha256']}),hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected,str(r['hmac_sha256'])):
                raise InvalidCloudReceipt(f'Server HMAC mismatch at {i}')
        prev=r['sha256'];verified.append(r['event'])
    film=[r for r in receipts if r['event']=='LOCAL_MP4_VERIFIED']
    media_status='not independently checked'
    if media is not None:
        if not film:raise InvalidCloudReceipt('No media witness receipt')
        actual=sha_file(media)
        if actual!=film[-1]['payload'].get('sha256'):
            raise InvalidCloudReceipt('MP4 bytes differ from the latest render receipt')
        media_status='exact media SHA-256 matches last verified render claim'
    return {'project_id':pid,'events':verified,'receipt_count':len(verified),'head':prev,
            'HMAC_verified':secret is not None,'media_verification':media_status,
            'caution':'Content hashes do not prove who approved the film or provider output'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('receipts',type=Path)
    parser.add_argument('--secret',type=Path,help='Private server key; do not publish or upload')
    parser.add_argument('--media',type=Path,help='Check actual local MP4 bytes against last render receipt')
    a=parser.parse_args()
    if a.receipts.stat().st_size>3_000_000:parser.error('Receipt export too large')
    try:
        result=verify(json.loads(a.receipts.read_text()),a.secret.read_bytes() if a.secret else None,a.media)
    except (InvalidCloudReceipt,OSError,ValueError) as err:parser.error(str(err))
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
