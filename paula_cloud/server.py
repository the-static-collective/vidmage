"""Private Vidmage phone-to-render server. Never publish without Access policy.

Launch with `python -m paula_cloud.server` and configure Cloudflare Tunnel.
Default auth is *fail closed* until Cloudflare Access is configured.
"""
from __future__ import annotations
import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request as HTTPRequest, urlopen
from typing import Any

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel

from .auth import AuthConfig, from_env, identity
from .engine import render, sha_file, validate_plan, probe
from paula.receipt import validate as validate_pocket, ReceiptRefused, digest, canonical

PROJECT_LIMIT=30
MAX_JSON=3_000_000
MAX_IMAGE=12_000_000
MAX_AUDIO=50_000_000

@dataclass
class Settings:
    data_dir:Path
    auth:AuthConfig
    cf_browser_account:str=''
    cf_browser_token:str=''
    node_label:str='Private studio'
    home_url:str=''
    aws_url:str=''

    @classmethod
    def environment(cls):
        return cls(Path(os.environ.get('PAULA_DATA_DIR','./paula-private-data')).resolve(),from_env(),
                   os.environ.get('PAULA_BROWSER_ACCOUNT_ID',''),
                   os.environ.get('PAULA_BROWSER_API_TOKEN',''),
                   os.environ.get('PAULA_NODE_LABEL','Private studio').strip()[:48],
                   os.environ.get('PAULA_HOME_URL','').strip(),
                   os.environ.get('PAULA_AWS_URL','').strip())

class ProjectModel(BaseModel):
    project:dict[str, Any]
class RenderModel(BaseModel):
    portrait:bool=True
    confirm_render:bool=False
class BrowserModel(BaseModel):
    confirm_session:bool=False


def now():return datetime.now(timezone.utc).isoformat()

def db_connect(dbfile):
    conn=sqlite3.connect(dbfile,timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    return conn


def init_data(settings:Settings):
    settings.data_dir.mkdir(parents=True,exist_ok=True)
    (settings.data_dir/'projects').mkdir(exist_ok=True)
    secretfile=settings.data_dir/'receipt-secret.key'
    if not secretfile.exists():
        try:
            fd=os.open(secretfile,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as s:s.write(secrets.token_bytes(32))
        except FileExistsError:pass
    secret=secretfile.read_bytes()
    if len(secret)!=32:raise RuntimeError('Receipt key must be 32 bytes')
    dbfile=settings.data_dir/'studio.sqlite3'
    with db_connect(dbfile) as d:
        d.execute('''CREATE TABLE IF NOT EXISTS projects(
            id TEXT PRIMARY KEY,owner TEXT NOT NULL,story BLOB NOT NULL,created TEXT NOT NULL)''')
        d.execute('''CREATE TABLE IF NOT EXISTS assets(
            id TEXT PRIMARY KEY,project_id TEXT NOT NULL,owner TEXT NOT NULL,
            name TEXT NOT NULL,kind TEXT NOT NULL,path TEXT NOT NULL,sha256 TEXT NOT NULL,created TEXT NOT NULL)''')
        d.execute('''CREATE TABLE IF NOT EXISTS jobs(
            id TEXT PRIMARY KEY,project_id TEXT NOT NULL,owner TEXT NOT NULL,status TEXT NOT NULL,
            plan_sha256 TEXT NOT NULL,plan BLOB NOT NULL,result BLOB,error TEXT NOT NULL DEFAULT '',
            created TEXT NOT NULL,updated TEXT NOT NULL)''')
        d.execute('''CREATE TABLE IF NOT EXISTS receipts(
            id TEXT PRIMARY KEY,project_id TEXT NOT NULL,owner TEXT NOT NULL,
            event TEXT NOT NULL,body BLOB NOT NULL,created TEXT NOT NULL)''')
        d.execute('''CREATE TABLE IF NOT EXISTS browsers(
            owner TEXT NOT NULL,session_id TEXT NOT NULL,created TEXT NOT NULL,
            PRIMARY KEY(owner,session_id))''')
        # Jobs are explicitly stopped on restart, not assumed completed.
        d.execute("UPDATE jobs SET status='INTERRUPTED',error='Server restarted before verified completion' WHERE status IN ('QUEUED','RENDERING')")
        d.commit()
    return dbfile,secret


def create_app(settings:Settings|None=None)->FastAPI:
    settings=settings or Settings.environment()
    dbfile,secret=init_data(settings)
    app=FastAPI(title='Paula Pocket Studio',docs_url=None,redoc_url=None,openapi_url=None)
    app.state.dbfile=dbfile;app.state.settings=settings
    limiter=threading.Semaphore(1)
    repo=Path(__file__).resolve().parent.parent

    def get_owner(request:Request):return identity(request,settings.auth)
    def connect():return db_connect(dbfile)
    def pdir(pid):return settings.data_dir/'projects'/pid
    def project_get(pid:str,owner:str):
        with connect() as conn:row=conn.execute('SELECT * FROM projects WHERE id=? AND owner=?',(pid,owner)).fetchone()
        if row is None:raise HTTPException(404,'Project not found')
        return dict(row)
    def job_get(jid:str,owner:str):
        with connect() as conn:row=conn.execute('SELECT * FROM jobs WHERE id=? AND owner=?',(jid,owner)).fetchone()
        if row is None:raise HTTPException(404,'Job not found')
        return dict(row)
    def append_receipt(pid,owner,event,payload):
        with connect() as conn:
            prev=conn.execute('SELECT body FROM receipts WHERE project_id=? AND owner=? ORDER BY rowid DESC LIMIT 1',(pid,owner)).fetchone()
            head=json.loads(prev['body'])['sha256'] if prev else None
            body={'format':'vidmage/paula-cloud-receipt/v1','event':event,'created_at':now(),
                  'previous_sha256':head,'payload':payload}
            body['sha256']=digest(body)
            body['hmac_sha256']=hmac.new(secret,canonical(body),hashlib.sha256).hexdigest()
            conn.execute('INSERT INTO receipts VALUES(?,?,?,?,?,?)',(uuid.uuid4().hex,pid,owner,event,
                                                           json.dumps(body,ensure_ascii=False),body['created_at']))
            conn.commit()
        return body

    @app.middleware('http')
    async def protect(request:Request,call_next):
        # No cross-site write requests, no cookies or local untrusted headers as auth.
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin=request.headers.get('origin','')
            host=request.headers.get('host','')
            if origin:
                from urllib.parse import urlparse
                u=urlparse(origin)
                if (u.hostname or '').lower()!=(host.split(':')[0] or '').lower():
                    return JSONResponse({'detail':'Cross-origin write refused'},403)
            if request.headers.get('sec-fetch-site')=='cross-site':
                return JSONResponse({'detail':'Cross-site write refused'},403)
            if request.headers.get('x-paula-intent')!='yes':
                return JSONResponse({'detail':'Missing first-party action header'},403)
            if request.url.path=='/api/projects' and int(request.headers.get('content-length','0') or '0')>MAX_JSON:
                return JSONResponse({'detail':'Story too large'},413)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Content-Security-Policy']=("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                                                    "img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; "
                                                    "object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        return response

    @app.get('/')
    def home(owner:str=Depends(get_owner)):
        return FileResponse(repo/'paula'/'index.html',media_type='text/html')
    @app.get('/studio/')
    def studio(owner:str=Depends(get_owner)):
        return FileResponse(Path(__file__).with_name('studio.html'),media_type='text/html')
    @app.get('/nodes')
    def nodes(owner:str=Depends(get_owner)):
        return FileResponse(Path(__file__).with_name('nodes.html'),media_type='text/html')
    @app.get('/api/node')
    def node(owner:str=Depends(get_owner)):
        # These are links, never an automatic switchover or a claim of shared storage.
        def safe_https(u):
            from urllib.parse import urlparse
            v=urlparse(u)
            return u if v.scheme=='https' and v.hostname and not v.username and not v.password and not v.fragment else ''
        return {'label':settings.node_label,'home_url':safe_https(settings.home_url),
                'aws_url':safe_https(settings.aws_url),'storage':'node-local',
                'shared_projects':False,'automatic_failover':False}
    @app.get('/api/health')
    def health(owner:str=Depends(get_owner)):
        return {'status':'ready','identity':owner,'render_engine':'ffmpeg','flow_remote_browser':bool(settings.cf_browser_token and settings.cf_browser_account)}

    @app.post('/api/projects')
    def create_project(data:ProjectModel,owner:str=Depends(get_owner)):
        obj=data.project
        if obj.get('format')!='vidmage/paula-pocket-project/v1':raise HTTPException(422,'Not a Paula Pocket project')
        pid=obj.get('projectId')
        if not isinstance(pid,str) or not 8<=len(pid)<=120 or not all(x.isalnum() or x in '-_' for x in pid):
            raise HTTPException(422,'Invalid project ID')
        try:
            witness=validate_pocket(obj)
            validate_plan(obj)
        except (ReceiptRefused,ValueError) as exc:
            raise HTTPException(422,str(exc))
        approved=[r for r in obj.get('receipts',[]) if r.get('event')=='STORYBOARD_APPROVED']
        if not approved:
            raise HTTPException(422,'Approve your story scene cards first')
        latest=approved[-1]['payload']['project']
        if latest.get('scenes')!=obj.get('scenes') or latest.get('story')!=obj.get('story') or latest.get('duration_seconds')!=obj.get('duration'):
            raise HTTPException(409,'Scene cards changed since approval. Approve the current version again.')
        with connect() as conn:
            existing=conn.execute('SELECT owner,story FROM projects WHERE id=?',(pid,)).fetchone()
            if existing and existing['owner']!=owner:raise HTTPException(409,'Project ID already in use')
            count=conn.execute('SELECT COUNT(*) FROM projects WHERE owner=?',(owner,)).fetchone()[0]
            if not existing and count>=PROJECT_LIMIT:raise HTTPException(429,'Private project limit reached')
            if existing:
                conn.execute('UPDATE projects SET story=? WHERE id=? AND owner=?',(json.dumps(obj),pid,owner))
            else:
                conn.execute('INSERT INTO projects VALUES(?,?,?,?)',(pid,owner,json.dumps(obj),now()))
            conn.commit()
        pdir(pid).mkdir(parents=True,exist_ok=True)
        append_receipt(pid,owner,'POCKET_STORY_RECEIVED',{'project_id':pid,'pocket_head_sha256':witness['head_sha256'],
                       'project_sha256':digest(obj),'status':'HOLD','meaning':'Portable storyboard imported; no video yet'})
        return {'project_id':pid,'studio_url':f'/studio/?project={quote(pid)}',
                'intake_status':'HOLD','pocket_receipt_head':witness['head_sha256']}

    @app.get('/api/projects')
    def projects(owner:str=Depends(get_owner)):
        with connect() as conn:rows=conn.execute('SELECT id,story,created FROM projects WHERE owner=? ORDER BY created DESC LIMIT 40',(owner,)).fetchall()
        return {'projects':[{'id':r['id'],'title':json.loads(r['story']).get('title','My movie'),'created':r['created']} for r in rows]}
    @app.get('/api/projects/{pid}')
    def project(pid:str,owner:str=Depends(get_owner)):
        r=project_get(pid,owner)
        with connect() as d:
            items=d.execute('SELECT id,name,kind,sha256 FROM assets WHERE project_id=? AND owner=?',(pid,owner)).fetchall()
            jobs=d.execute('SELECT id,status,created,updated,error FROM jobs WHERE project_id=? AND owner=? ORDER BY created DESC LIMIT 15',(pid,owner)).fetchall()
        return {'project':json.loads(r['story']),'assets':[dict(i) for i in items],'jobs':[dict(j) for j in jobs]}

    @app.post('/api/projects/{pid}/asset')
    async def asset(pid:str,media:UploadFile=File(...),owner:str=Depends(get_owner)):
        project_get(pid,owner)
        data=await media.read(MAX_IMAGE+1 if (media.content_type or '').startswith('image/') else MAX_AUDIO+1)
        kind='image' if (media.content_type or '').startswith('image/') else 'audio' if (media.content_type or '').startswith('audio/') else ''
        if not kind:raise HTTPException(415,'Choose a photo or audio file')
        limit=MAX_IMAGE if kind=='image' else MAX_AUDIO
        if not data or len(data)>limit:raise HTTPException(413,'Asset too large')
        with connect() as conn:
            count=conn.execute('SELECT COUNT(*) FROM assets WHERE project_id=? AND kind=?',(pid,kind)).fetchone()[0]
            if count>=(12 if kind=='image' else 1):raise HTTPException(409,'Asset limit reached')
        aid=uuid.uuid4().hex
        directory=pdir(pid)/'assets';directory.mkdir(exist_ok=True)
        if kind=='image':
            try:
                with Image.open(io.BytesIO(data)) as opened:
                    if opened.width*opened.height>24_000_000:raise ValueError('Image dimensions too large')
                    img=ImageOps.exif_transpose(opened).convert('RGB')
                    img.thumbnail((1920,1920))
                    path=directory/f'{aid}.jpg'
                    img.save(path,'JPEG',quality=90,optimize=True)
            except (UnidentifiedImageError,OSError,ValueError) as err:
                raise HTTPException(422,'Unsupported or oversized photo') from err
        else:
            path=directory/f'{aid}.audio'
            path.write_bytes(data)
            try:
                info=probe(path)
                streams=[s for s in info.get('streams',[]) if s.get('codec_type')=='audio']
                length=float(info.get('format',{}).get('duration',0))
                if not streams or not 1<=length<=360:raise ValueError('Audio duration unavailable or over six minutes')
            except (RuntimeError,KeyError,ValueError):
                path.unlink(missing_ok=True)
                raise HTTPException(422,'Audio file cannot be decoded or is too long')
        sh=sha_file(path)
        with connect() as conn:
            conn.execute('INSERT INTO assets VALUES(?,?,?,?,?,?,?,?)',
                         (aid,pid,owner,str(media.filename or 'unnamed')[:150],kind,str(path),sh,now()))
            conn.commit()
        append_receipt(pid,owner,'SOURCE_ASSET_RECEIVED',{'asset_id':aid,'kind':kind,'sha256':sh,'bytes':path.stat().st_size,
                       'meaning':'Server received and verified a private source copy'})
        return {'id':aid,'kind':kind,'sha256':sh}

    def execute_render(jid,pid,owner,plan,assets,audio,w,h):
        with limiter:
            with connect() as conn:
                conn.execute("UPDATE jobs SET status='RENDERING',updated=? WHERE id=?",(now(),jid));conn.commit()
            try:
                folder=pdir(pid)/'renders'/jid
                report=render(plan,[Path(a['path']) for a in assets],Path(audio['path']) if audio else None,folder,width=w,height=h)
                # Original sources and actual bytes independently rechecked at render completion.
                for a in assets+([audio] if audio else []):
                    if sha_file(Path(a['path']))!=a['sha256']:raise RuntimeError('Input was altered during rendering')
                with connect() as conn:
                    conn.execute("UPDATE jobs SET status='COMPLETED',result=?,updated=? WHERE id=?",(json.dumps(report),now(),jid));conn.commit()
                append_receipt(pid,owner,'LOCAL_MP4_VERIFIED',{'job_id':jid,'plan_sha256':digest(plan),
                               'input_sha256':[a['sha256'] for a in assets]+([audio['sha256']] if audio else []),
                               **{k:v for k,v in report.items() if k!='path'},
                               'meaning':'Server rendered and verified actual MP4 bytes, not model-generated cinematic video'})
            except Exception as exc:
                with connect() as conn:
                    conn.execute("UPDATE jobs SET status='FAILED',error=?,updated=? WHERE id=?",(str(exc)[:500],now(),jid));conn.commit()
                append_receipt(pid,owner,'RENDER_FAILED',{'job_id':jid,'error':str(exc)[:300],
                                                              'meaning':'No complete verified film is claimed'})

    @app.post('/api/projects/{pid}/render')
    def render_request(pid:str,body:RenderModel,owner:str=Depends(get_owner)):
        if not body.confirm_render:raise HTTPException(400,'Confirm that Paula wants this video rendered')
        raw=json.loads(project_get(pid,owner)['story'])
        plan=validate_plan(raw)
        with connect() as conn:
            busy=conn.execute("SELECT COUNT(*) FROM jobs WHERE owner=? AND status IN ('QUEUED','RENDERING')",(owner,)).fetchone()[0]
            if busy>=2:raise HTTPException(429,'Already have two films in progress')
            count=conn.execute('SELECT COUNT(*) FROM jobs WHERE owner=?',(owner,)).fetchone()[0]
            if count>=100:raise HTTPException(429,'Render history limit reached')
            rows=conn.execute('SELECT * FROM assets WHERE project_id=? AND owner=? ORDER BY created ASC',(pid,owner)).fetchall()
            photos=[dict(r) for r in rows if r['kind']=='image'];audio=next((dict(r) for r in rows if r['kind']=='audio'),None)
        for item in photos+([audio] if audio else []):
            if sha_file(Path(item['path']))!=item['sha256']:
                raise HTTPException(409,'A source file changed after upload')
        jid=uuid.uuid4().hex
        with connect() as conn:
            conn.execute('INSERT INTO jobs(id,project_id,owner,status,plan_sha256,plan,result,error,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?)',
                         (jid,pid,owner,'QUEUED',digest(plan),json.dumps(plan),None,'',now(),now()))
            conn.commit()
        append_receipt(pid,owner,'RENDER_REQUESTED',{'job_id':jid,'plan_sha256':digest(plan),
                 'input_sha256':[a['sha256'] for a in photos]+([audio['sha256']] if audio else []),
                 'render_type':'local-picture-story-mp4','external_ai_credits':0})
        w,h=(720,1280) if body.portrait else (1280,720)
        threading.Thread(target=execute_render,args=(jid,pid,owner,plan,photos,audio,w,h),daemon=True).start()
        return {'job_id':jid,'status':'QUEUED','preview_url':f'/api/jobs/{jid}/movie'}

    @app.get('/api/jobs/{jid}')
    def get_job(jid:str,owner:str=Depends(get_owner)):
        row=job_get(jid,owner)
        return {k:row[k] for k in ('id','project_id','status','error','created','updated')}|({'result':{k:v for k,v in json.loads(row['result']).items() if k!='path'}} if row['result'] else {})
    @app.get('/api/jobs/{jid}/movie')
    def get_movie(jid:str,owner:str=Depends(get_owner)):
        row=job_get(jid,owner)
        if row['status']!='COMPLETED' or not row['result']:raise HTTPException(409,'Video not verified yet')
        result=json.loads(row['result']);path=Path(result['path'])
        if not path.is_file() or sha_file(path)!=result['sha256']:
            raise HTTPException(409,'Video bytes no longer match the receipt')
        return FileResponse(path,media_type='video/mp4',filename='paula-movie.mp4')
    @app.get('/api/projects/{pid}/receipts')
    def receipts(pid:str,owner:str=Depends(get_owner)):
        project_get(pid,owner)
        with connect() as conn:rs=conn.execute('SELECT body FROM receipts WHERE project_id=? AND owner=? ORDER BY rowid ASC',(pid,owner)).fetchall()
        return {'format':'vidmage/paula-cloud-export/v1','project_id':pid,'receipts':[json.loads(r['body']) for r in rs],
                'verification':'SHA-256 + server-local HMAC (HMAC key not exported)'}

    def cf_call(method,path,payload=None):
        if not settings.cf_browser_token or not settings.cf_browser_account:
            raise HTTPException(501,'Remote browser not configured; use Open Flow directly')
        uri='https://api.cloudflare.com/client/v4/accounts/'+quote(settings.cf_browser_account,safe='')+'/browser-run/devtools/'+path
        data=json.dumps(payload).encode() if payload is not None else None
        req=HTTPRequest(uri,data=data,method=method,headers={
            'Authorization':'Bearer '+settings.cf_browser_token,
            'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=35) as resp:return json.load(resp)
        except Exception as err:raise HTTPException(502,'Cloudflare browser unavailable or declined the session') from err

    @app.post('/api/flow/browser')
    def browser_start(body:BrowserModel,owner:str=Depends(get_owner)):
        if not body.confirm_session:raise HTTPException(400,'Confirm the temporary paid browser session')
        with connect() as conn:
            active=conn.execute('SELECT COUNT(*) FROM browsers WHERE owner=?',(owner,)).fetchone()[0]
            if active>=1:raise HTTPException(409,'Close your previous remote browser first')
        result=cf_call('POST','browser?keep_alive=600000&targets=true')
        # API may return a wrapper or an unwrapped response depending on version.
        result=result.get('result',result)
        sid=result.get('sessionId')
        if not isinstance(sid,str) or not sid:raise HTTPException(502,'Session ID missing')
        try:
            tab=cf_call('PUT',f'browser/{quote(sid,safe="")}/json/new?url='+quote('https://www.flowmusic.app/',safe=''))
            tab=tab.get('result',tab)
            target=tab.get('id')
            if not isinstance(target,str):raise ValueError('Target missing')
            view=cf_call('POST',f'browser/{quote(sid,safe="")}/live_view',{'mode':'tab','targetId':target,'expiresInMs':300000})
            view=view.get('result',view)
            url=view.get('devtoolsFrontendUrl','')
            if not isinstance(url,str) or not url.startswith('https://live.browser.run/'):
                raise ValueError('Unsafe or missing Live View URL')
        except Exception:
            try:cf_call('DELETE','browser/'+quote(sid,safe=''))
            except Exception:pass
            raise HTTPException(502,'Remote Flow tab could not start; try direct Flow access')
        with connect() as conn:
            conn.execute('INSERT INTO browsers VALUES(?,?,?)',(owner,sid,now()));conn.commit()
        return {'live_view_url':url,'note':'Sensitive five-minute access link. External Flow sign-in is manual. Not embedded in Vidmage.'}

    @app.post('/api/flow/browser/close')
    def browser_close(owner:str=Depends(get_owner)):
        with connect() as conn:
            rows=conn.execute('SELECT session_id FROM browsers WHERE owner=?',(owner,)).fetchall()
        for r in rows:
            try:cf_call('DELETE','browser/'+quote(r['session_id'],safe=''))
            except HTTPException:pass
        with connect() as conn:conn.execute('DELETE FROM browsers WHERE owner=?',(owner,));conn.commit()
        return {'status':'closed'}

    return app

app=create_app() if os.environ.get('PAULA_APP_AUTOCREATE')=='1' else None

if __name__=='__main__':
    import uvicorn
    host=os.environ.get('PAULA_HOST','127.0.0.1')
    settings=Settings.environment()
    if settings.auth.mode=='local' and host not in ('127.0.0.1','::1','localhost'):
        raise SystemExit('Local auth mode cannot bind to network. Use Cloudflare JWT auth.')
    uvicorn.run(create_app(settings),host=host,port=int(os.environ.get('PAULA_PORT','8768')),
                proxy_headers=False)
