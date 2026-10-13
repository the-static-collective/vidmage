"""A real zero-AI-credit picture/story → MP4 local renderer.

This is a bounded portable renderer, not the native BAND-IQ 010-013 compositor.
It never silently sends images or stories to remote model services.
"""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw, ImageFont, ImageOps

MAX_DURATION = 90
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def validate_plan(project: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(project, dict):
        raise ValueError('Missing project')
    raw = project.get('scenes')
    if not isinstance(raw, list) or not 1 <= len(raw) <= 16:
        raise ValueError('Please make 1–16 scene cards first')
    duration = project.get('duration', project.get('duration_seconds', 20))
    if isinstance(duration, bool) or not isinstance(duration, (float, int)) or not 3 <= duration <= MAX_DURATION:
        raise ValueError('Length must be from 3 to 90 seconds')
    scenes = []
    for i, s in enumerate(raw):
        if not isinstance(s, dict):
            raise ValueError('Invalid scene card')
        action = str(s.get('action', '')).strip()
        if not 1 <= len(action) <= 1500:
            raise ValueError(f'Scene {i+1} needs an action')
        scenes.append({'title':str(s.get('title','Scene'))[:100],
                       'action': action, 'dialogue':str(s.get('dialogue',''))[:350]})
    return {'title':str(project.get('title', 'My little movie'))[:120],
            'duration':float(duration), 'scenes':scenes,
            'ending':str(project.get('endTitle',project.get('end_title','')))[:240]}


def _font(size:int,bold=False):
    location=FONT_BOLD if bold else FONT
    return ImageFont.truetype(location,size) if Path(location).is_file() else ImageFont.load_default()


def _wrap(text: str, draw: ImageDraw.ImageDraw, font, limit: int, maxlines=9) -> list[str]:
    lines = []
    for chunk in text.split('\n'):
        acc=''
        for word in chunk.split():
            candidate=f'{acc} {word}'.strip()
            if draw.textbbox((0,0),candidate,font=font)[2]>limit and acc:
                lines.append(acc);acc=word
            else: acc=candidate
        if acc: lines.append(acc)
    return lines[:maxlines]


def make_card(out:Path, title:str, action:str, number:int, total:int, photo:Path|None,
              width:int=720,height:int=1280,ending:str='') -> None:
    bg=Image.new('RGB',(width,height),'#233126')
    if photo:
        with Image.open(photo) as opened:
            still=ImageOps.fit(opened.convert('RGB'), (width,height), method=Image.Resampling.LANCZOS)
        bg.paste(still)
    # Controlled darkening ensures the copy remains readable over any photograph.
    shade=Image.new('RGB',(width,height),'#111c19')
    bg=Image.blend(bg,shade,0.50 if photo else 0.1)
    draw=ImageDraw.Draw(bg)
    m=int(width*.07)
    titlefont=_font(max(23,int(width*.046)),True)
    bodyfont=_font(max(20,int(width*.038)))
    microfont=_font(max(16,int(width*.027)))
    draw.text((m,m),f'PAULA’S LITTLE MOVIE  •  {number:02d}/{total:02d}',font=microfont,fill='#ffdfa2')
    block_y=int(height*.58)
    draw.rounded_rectangle([m-12,block_y-30,width-m+12,height-m],radius=20,fill='#17211c')
    y=block_y
    for line in _wrap(title,draw,titlefont,width-2*m-12,maxlines=2):
        draw.text((m,y),line,font=titlefont,fill='#f4d4ab');y+=int(width*.065)
    y+=15
    for line in _wrap(action,draw,bodyfont,width-2*m-12,maxlines=8):
        if y>height-m-80:break
        draw.text((m,y),line,font=bodyfont,fill='#f6f1e8');y+=int(width*.060)
    if ending and number==total:
        draw.text((m,height-m-45),ending[:60],font=microfont,fill='#f4d4ab')
    bg.save(out,format='PNG')


def run(cmd:list[str],timeout:int=180):
    try:
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         timeout=timeout,check=False,text=True)
    except subprocess.TimeoutExpired as ex:
        raise RuntimeError('Rendering took too long') from ex
    if p.returncode:
        raise RuntimeError(f'Media engine error ({p.returncode}): {p.stderr[-1200:]}')
    return p.stdout


def probe(media: Path) -> dict[str,Any]:
    out=run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,codec_name,width,height',
             '-of','json',str(media)],30)
    return json.loads(out)


def render(project:dict[str,Any],assets:list[Path],audio:Path|None,outdir:Path,
           *,width=720,height=1280) -> dict[str,Any]:
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise RuntimeError('FFmpeg and ffprobe must be installed on render server')
    plan=validate_plan(project)
    if width not in (360,720,1280) or height not in (640,720,1280):
        raise ValueError('Unsupported resolution')
    if (width,height) not in {(360,640),(720,1280),(1280,720)}:
        raise ValueError('Use portrait or landscape resolution')
    outdir.mkdir(parents=True,exist_ok=True)
    seconds=plan['duration']/len(plan['scenes'])
    listfile=outdir/'frames.ffconcat'
    lines=['ffconcat version 1.0']
    frame_names=[]
    for i,scene in enumerate(plan['scenes']):
        path=outdir/f'scene-{i+1:03}.png'
        photo=assets[i % len(assets)] if assets else None
        make_card(path,scene['title'],scene['action'],i+1,len(plan['scenes']),photo,
                  width,height,plan['ending'])
        lines.extend([f"file '{path.name}'",f'duration {seconds:.9f}'])
        frame_names.append(path.name)
    # Concat demuxer uses final repeated frame to honor the final duration.
    lines.append(f"file '{frame_names[-1]}'")
    listfile.write_text('\n'.join(lines)+'\n',encoding='utf8')
    result=outdir/'movie.mp4'
    cmd=['ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y',
         '-f','concat','-safe','0','-i',str(listfile)]
    if audio:
        cmd.extend(['-stream_loop','-1','-i',str(audio)])
    cmd.extend(['-vf',f'fps=24,scale={width}:{height},format=yuv420p',
                '-c:v','libx264','-preset','ultrafast','-crf','25','-movflags','+faststart'])
    if audio:
        cmd.extend(['-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','128k','-af','afade=t=in:st=0:d=0.2',
                    '-t',str(plan['duration'])])
    else:
        cmd.extend(['-an','-t',str(plan['duration'])])
    cmd.append(str(result))
    run(cmd,180)
    report=probe(result)
    video=next((x for x in report.get('streams',[]) if x.get('codec_type')=='video'),None)
    if not video or result.stat().st_size<1024:raise RuntimeError('Output video not independently verified')
    measured=float(report['format']['duration'])
    if abs(measured-plan['duration'])>1.5:raise RuntimeError('Output duration does not match plan')
    return {'path':str(result),'sha256':sha_file(result),'bytes':result.stat().st_size,
            'duration_seconds':measured,'width':video.get('width'),'height':video.get('height'),
            'media_kind':'real-local-ffmpeg-mp4','renderer':'paula-cloud-cards/v1',
            'scene_card_sha256':[sha_file(outdir/f) for f in frame_names]}
