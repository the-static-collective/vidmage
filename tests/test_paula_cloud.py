import copy
import hashlib
import io
import json
import os
import tempfile
import time
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
from paula_cloud.auth import AuthConfig
from paula_cloud.server import Settings, create_app
from paula.receipt import digest


def sample():
    obj={
       'format':'vidmage/paula-pocket-project/v1',
       'projectId':'pocket-0123456789abcdef0123456789abcdef',
       'title':'A fictional fall morning','duration':3,'story':'A paper bird comes home.',
       'characters':'', 'mood':'Gentle', 'endTitle':'Dream kindly',
       'scenes':[{'id':'1','time':'0–3','title':'A morning','action':'The paper bird alights on the old porch rail.','dialogue':''}],
       'receipts':[]}
    approved={'format':'vidmage/paula-pocket-receipt/v1','event':'STORYBOARD_APPROVED',
              'created_at':'2026-10-13T00:00:00Z','previous_sha256':None,
              'payload':{'project':{
                'project_id':obj['projectId'],'title':obj['title'],'duration_seconds':obj['duration'],
                'mood':obj['mood'],'story':obj['story'],'characters':obj['characters'],
                'end_title':obj['endTitle'],'scenes':copy.deepcopy(obj['scenes'])},
                 'authority':'owner-approved-storyboard','media_status':'not-rendered'}}
    approved['sha256']=digest(approved)
    obj['receipts']=[approved]
    return obj


def client(tmp):
    return TestClient(create_app(Settings(tmp,AuthConfig('local'))))

def write(c,url,data=None):
    if isinstance(data,dict):return c.post(url,json=data,headers={'X-Paula-Intent':'yes'})
    return c.post(url,headers={'X-Paula-Intent':'yes'})

def test_private_auth_and_origin():
    with tempfile.TemporaryDirectory() as d:
        locked=TestClient(create_app(Settings(Path(d),AuthConfig('cloudflare'))))
        assert locked.get('/api/health').status_code==503
        c=client(Path(d))
        assert c.post('/api/projects',json={'project':sample()}).status_code==403
        assert c.post('/api/projects',json={'project':sample()},headers={'X-Paula-Intent':'yes','Origin':'https://attacker.net'}).status_code==403
        assert c.get('/').status_code==200
        assert c.get('/studio/').status_code==200
        assert 'Send' not in c.get('/api/health').text

def test_receipt_guard_and_import():
    with tempfile.TemporaryDirectory() as d:
        c=client(Path(d));obj=sample()
        obj['receipts']=[]
        assert write(c,'/api/projects',{'project':obj}).status_code==422
        obj=sample();obj['scenes'][0]['action']='different'
        assert write(c,'/api/projects',{'project':obj}).status_code==409
        obj=sample();obj['receipts'][0]['sha256']='0'*64
        assert write(c,'/api/projects',{'project':obj}).status_code==422
        obj=sample();r=write(c,'/api/projects',{'project':obj})
        assert r.status_code==200,r.text
        pid=obj['projectId']
        rs=c.get(f'/api/projects/{pid}/receipts').json()['receipts']
        assert len(rs)==1 and rs[0]['event']=='POCKET_STORY_RECEIVED'
        assert len(rs[0]['hmac_sha256'])==64
        assert c.get('/api/projects').json()['projects'][0]['id']==pid
        assert write(c,'/api/projects/'+pid+'/render',{'confirm_render':False}).status_code==400
        assert write(c,'/api/flow/browser',{'confirm_session':True}).status_code==501
        assert c.get('/api/jobs/'+('0'*32)+'/movie').status_code==404

def test_real_ffmpeg_and_file_integrity():
    with tempfile.TemporaryDirectory() as d:
        c=client(Path(d));p=sample();pid=p['projectId'];r=write(c,'/api/projects',{'project':p});assert r.status_code==200,r.text
        im=Image.new('RGB',(300,400),(120,82,69));buf=io.BytesIO();im.save(buf,'JPEG',exif=b'Exif\0\0' + b'x'*30)
        media=c.post(f'/api/projects/{pid}/asset',files={'media':('synthetic.jpg',buf.getvalue(),'image/jpeg')},headers={'X-Paula-Intent':'yes'})
        assert media.status_code==200,media.text
        sha=media.json()['sha256'];assert len(sha)==64
        req=write(c,f'/api/projects/{pid}/render',{'portrait':True,'confirm_render':True});assert req.status_code==200,req.text
        jid=req.json()['job_id']
        deadline=time.time()+70
        job={}
        while time.time()<deadline:
            job=c.get('/api/jobs/'+jid).json()
            if job['status'] in ('COMPLETED','FAILED'):break
            time.sleep(0.2)
        assert job['status']=='COMPLETED',job
        movie=c.get('/api/jobs/'+jid+'/movie')
        assert movie.status_code==200
        assert movie.headers['content-type'].startswith('video/mp4')
        assert movie.content[4:8]==b'ftyp'
        assert hashlib.sha256(movie.content).hexdigest()==job['result']['sha256']
        assert 2.4<float(job['result']['duration_seconds'])<4.0
        rs=c.get(f'/api/projects/{pid}/receipts').json()['receipts']
        assert [x['event'] for x in rs]==['POCKET_STORY_RECEIVED','SOURCE_ASSET_RECEIVED','RENDER_REQUESTED','LOCAL_MP4_VERIFIED']
        for i,r in enumerate(rs):
            core={k:r[k] for k in ('format','event','created_at','previous_sha256','payload')}
            assert digest(core)==r['sha256']
            assert r['previous_sha256']==(rs[i-1]['sha256'] if i else None)
        # Tampering with a real media file must refuse download.
        paths=list((Path(d)/'projects'/pid/'renders'/jid).glob('movie.mp4'))
        assert len(paths)==1
        paths[0].write_bytes(b'not the film')
        assert c.get('/api/jobs/'+jid+'/movie').status_code==409

if __name__=='__main__':
    import pytest
    raise SystemExit(pytest.main([__file__,'-v']))

def test_cloud_receipt_independent_verifier():
    from paula_cloud.verify import verify,InvalidCloudReceipt
    with tempfile.TemporaryDirectory() as d:
        tmp=Path(d);c=client(tmp);pid=sample()['projectId']
        assert write(c,'/api/projects',{'project':sample()}).status_code==200
        doc=c.get(f'/api/projects/{pid}/receipts').json()
        original=copy.deepcopy(doc)
        verified=verify(doc,(tmp/'receipt-secret.key').read_bytes())
        assert verified['receipt_count']==1 and verified['HMAC_verified']
        doc['receipts'][0]['payload']['status']='VERIFIED'
        try:verify(doc,(tmp/'receipt-secret.key').read_bytes())
        except InvalidCloudReceipt:pass
        else:assert False,'Tampered receipt was accepted'
        original['receipts'][0]['hmac_sha256']='0'*64
        try:verify(original,(tmp/'receipt-secret.key').read_bytes())
        except InvalidCloudReceipt:pass
        else:assert False,'Forged HMAC was accepted'
