"""Bounded, owner-scoped Kling MP4 handoff and FFmpeg cut tests."""
import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from paula_cloud.auth import AuthConfig
from paula_cloud.kling import inspect_clip, render_clip_cut
from paula_cloud.server import Settings, create_app
from paula.receipt import digest


def make_clip(path, seconds=1.2):
    subprocess.run([
        "ffmpeg","-hide_banner","-nostdin","-loglevel","error","-y",
        "-f","lavfi","-i","color=c=orange:s=96x96:r=24",
        "-t",str(seconds),"-an","-c:v","libx264","-pix_fmt","yuv420p",str(path)],
        check=True, timeout=20)
    return path


def owner_project():
    obj={'format':'vidmage/paula-pocket-project/v1',
         'projectId':'pocket-0123456789abcdef0123456789abcdef',
         'title':'The little red bicycle','story':'A morning at the porch.',
         'duration':3,'mood':'Gentle family','characters':'','endTitle':'',
         'scenes':[{'id':'shot-1','time':'0–3','title':'Morning',
                    'action':'Sun touches a little red bicycle.','dialogue':''}],
         'receipts':[]}
    witness={'format':'vidmage/paula-pocket-receipt/v1',
             'event':'STORYBOARD_APPROVED','created_at':'2026-10-13T00:00:00Z',
             'previous_sha256':None,'payload':{
                 'project':{'project_id':obj['projectId'],
                            'title':obj['title'],'duration_seconds':obj['duration'],
                            'mood':obj['mood'],'story':obj['story'],
                            'characters':obj['characters'],'end_title':obj['endTitle'],
                            'scenes':copy.deepcopy(obj['scenes'])},
                 'authority':'owner-approved-storyboard','media_status':'not-rendered'}}
    witness['sha256']=digest(witness)
    obj['receipts']=[witness]
    return obj


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),
                    reason='FFmpeg executable required')
def test_uploaded_clips_are_private_and_cut_bytes_are_verified():
    with tempfile.TemporaryDirectory() as root:
        base=Path(root)
        clip=make_clip(base/'test-clip.mp4')
        c=TestClient(create_app(Settings(base/'data',AuthConfig('local'))))
        headers={'X-Paula-Intent':'yes'}
        pid=owner_project()['projectId']
        created=c.post('/api/projects',json={'project':owner_project()},headers=headers)
        assert created.status_code==200,created.text
        # Cross-site uploads and unapproved cut requests are denied.
        blocked=c.post(f'/api/projects/{pid}/kling-clip',files={
            'media':('test.mp4',clip.read_bytes(),'video/mp4')})
        assert blocked.status_code==403
        denied=c.post(f'/api/projects/{pid}/kling-cut',
                      json={'portrait':True,'confirm_render':False},headers=headers)
        assert denied.status_code==400
        bad=c.post(f'/api/projects/{pid}/kling-clip',files={
            'media':('fake.mp4',b'not actually a video','video/mp4')},headers=headers)
        assert bad.status_code==422
        for i in range(2):
            r=c.post(f'/api/projects/{pid}/kling-clip',files={
                'media':(f'kling-shot-{i}.mp4',clip.read_bytes(),'video/mp4')},
                headers=headers)
            assert r.status_code==200,r.text
            assert r.json()['sha256']==hashlib.sha256(clip.read_bytes()).hexdigest()
        res=c.post(f'/api/projects/{pid}/kling-cut',
                   json={'portrait':True,'confirm_render':True},headers=headers)
        assert res.status_code==200,res.text
        job_id=res.json()['job_id']
        for _ in range(100):
            job=c.get(f'/api/jobs/{job_id}').json()
            if job['status'] not in ('QUEUED','RENDERING'):
                break
            time.sleep(.1)
        assert job['status']=='COMPLETED',job
        assert job['result']['clip_count']==2
        assert job['result']['renderer']=='paula-kling-clip-cut/v1'
        assert job['result']['provider_provenance']=='creator-reported; not API-verified'
        movie=c.get(f'/api/jobs/{job_id}/movie')
        assert movie.status_code==200
        assert movie.content[4:8]==b'ftyp'
        assert hashlib.sha256(movie.content).hexdigest()==job['result']['sha256']
        receipt=c.get(f'/api/projects/{pid}/receipts').json()
        events=[r['event'] for r in receipt['receipts']]
        assert events.count('EXTERNAL_CLIP_IMPORTED')==2
        assert 'IMPORTED_CLIPS_CUT_VERIFIED' in events


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),
                    reason='FFmpeg executable required')
def test_bounded_duration_and_zero_external_api_credits():
    with tempfile.TemporaryDirectory() as d:
        clip=make_clip(Path(d)/'shot.mp4',1.3)
        result=render_clip_cut([clip],None,Path(d)/'out',width=1280,height=720)
        assert result['clip_count']==1
        assert result['native_clip_audio']=='muted'
        assert result['external_ai_credits']==0
        assert result['duration_seconds']>=1
        assert result['sha256']==hashlib.sha256(Path(result['path']).read_bytes()).hexdigest()


def test_kling_is_manual_no_credential_leak_and_requires_access():
    repo=Path(__file__).resolve().parents[1]
    text=(repo/'paula_cloud/kling.py').read_text()
    assert 'api-singapore.klingai.com' not in text
    assert 'Bearer ' not in text
    page=(repo/'deploy/portal/index.html').read_text()
    assert 'https://kling.ai/' in page
    assert 'not automatically' in page
    phone=(repo/'paula/index.html').read_text()
    assert 'KLING_HANDOFF_PREPARED' in phone
    assert 'Copy Kling scene prompt' in phone
