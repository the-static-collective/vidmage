"""BAND-IQ 013 Grab/Cross Bits — bounded, source-pinned pixel fragments.

Grab a rectangular patch from an ORIGINAL prepared owned photograph; Cross the
patch onto a second owned photograph, without changing either. Pure raster
preview returns only bytes; a final Storytable seal may materialize create-only
derived PNGs and pin them in the author-signed card/receipt. No film authority.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import cv2
import numpy as np

from . import band_iq as iq
from . import band_iq_donors as donors

SCHEMA="vidmage/band-iq-013-owned-source-cross-bit/v1"
MAX_BITS_PER_SHOT=1
MAX_CROSSES_PER_STORY=36

def need(ok,msg):iq.require(ok,msg)

def normalized_rect(box,*,label):
    need(type(box)==list and len(box)==4 and
         all(type(x) in (float,int) and math.isfinite(x) for x in box),
         label+" must be four finite normalized numbers")
    x,y,w,h=box
    need(0<=x<=.95 and 0<=y<=.95 and .05<=w<=.85 and .05<=h<=.85 and
         x+w<=1.0000001 and y+h<=1.0000001,
         label+" needs a bounded rectangle inside the picture")
    return [round(float(v),3) for v in box]

def checked_bit(bit,owned):
    need(type(bit)==dict and set(bit)=={
        "sourceAssetId","crop","place","opacity"},
        "one exact source bit, crop rectangle, placement rectangle and opacity required")
    aid=bit["sourceAssetId"]
    need(type(aid)==str and aid in owned,
         "the grabbed bit must come from an actual owner-supplied image")
    opacity=bit["opacity"]
    need(type(opacity) in (float,int) and math.isfinite(opacity) and
         .1<=opacity<=1.0,"bit opacity must be explicit and bounded")
    return {
        "sourceAssetId":aid,
        "crop":normalized_rect(bit["crop"],label="grab"),
        "place":normalized_rect(bit["place"],label="cross"),
        "opacity":round(float(opacity),3),
    }

def source_paths(base_asset_id,bit,owned,root):
    root=Path(root).resolve(strict=True)
    need(base_asset_id in owned,"unknown target owned image")
    sources=[]
    for key in (base_asset_id,bit["sourceAssetId"]):
        row=owned[key]
        target=(root/row["path"]).resolve(strict=True)
        need(target.is_relative_to(root) and target.is_file(),
             "selected owned image cannot escape private preparation folder")
        actual=donors.sha_file(target)
        sources.append((target,actual))
    return sources

def compose(base_asset_id,bit,owned,root):
    """Return metadata and actual PNG bytes; no disk mutation."""
    bit=checked_bit(bit,owned)
    (base,bsha),(fragment,fsha)=source_paths(base_asset_id,bit,owned,root)
    base_image=cv2.imread(str(base),cv2.IMREAD_COLOR)
    fragment_image=cv2.imread(str(fragment),cv2.IMREAD_COLOR)
    need(base_image is not None and fragment_image is not None,
         "only real decodable owner prepared pictures are allowed")
    need(base_image.shape[:2]==(360,640) and
         fragment_image.shape[:2]==(360,640),
         "cross bits require the owner's bounded 640x360 prepared pictures")
    crop=bit["crop"];place=bit["place"]
    x,y,w,h=crop
    x0=min(639,int(x*640));y0=min(359,int(y*360))
    x1=min(640,max(x0+1,int(round((x+w)*640))))
    y1=min(360,max(y0+1,int(round((y+h)*360))))
    part=fragment_image[y0:y1,x0:x1]
    px,py,pw,ph=place
    tx=min(639,int(px*640));ty=min(359,int(py*360))
    tw=min(640-tx,max(1,int(round(pw*640))))
    th=min(360-ty,max(1,int(round(ph*360))))
    resized=cv2.resize(part,(tw,th),interpolation=cv2.INTER_AREA)
    result=base_image.copy()
    alpha=bit["opacity"]
    # Feathered boundary retains a visible fragment without harsh seams.
    falloff=max(1,min(10,tw//7,th//7))
    yy,xx=np.mgrid[0:th,0:tw]
    fade=np.minimum.reduce([xx+1,yy+1,tw-xx,th-yy]).astype(np.float32)
    mask=np.minimum(1.,fade/falloff)*alpha
    region=result[ty:ty+th,tx:tx+tw]
    result[ty:ty+th,tx:tx+tw]=np.clip(
        region.astype(np.float32)*(1-mask[...,None])+
        resized.astype(np.float32)*mask[...,None],0,255).astype(np.uint8)
    ok,encoded=cv2.imencode(".png",result)
    need(ok,"crossed owner image could not be encoded")
    png=encoded.tobytes()
    need(1024<len(png)<4*1024*1024,
         "crossed owner source composite outside bounded local size")
    provenance={
        "schema":SCHEMA,
        "baseSourceAssetId":base_asset_id,
        "baseSourceSha256":bsha,
        "grabbedSourceAssetId":bit["sourceAssetId"],
        "grabbedSourceSha256":fsha,
        "crop":bit["crop"],
        "place":bit["place"],
        "opacity":bit["opacity"],
        "rasterRule":"prepared-owner-images/640x360/feathered-local-layer/v1",
        "composedImageSha256":hashlib.sha256(png).hexdigest(),
        "originalsModified":False,
        "publicationAuthorized":False,
    }
    receipt={**provenance,"bitSha256":iq.digest(provenance)}
    return receipt,png

def derived_path(receipt):
    need(receipt.get("schema")==SCHEMA and iq.sha(receipt.get("bitSha256")),
         "only verifiable cross source receipt may identify new working asset")
    return "cross-bits/"+receipt["bitSha256"]+".png"

def materialize(receipt,png,root):
    """Create only at SEAL, verified against the exact in-memory raster bytes."""
    need(hashlib.sha256(png).hexdigest()==receipt["composedImageSha256"],
         "materialization bytes differ from source-bound bit")
    root=Path(root).resolve(strict=True)
    target=root/derived_path(receipt)
    target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    if target.exists():
        need(donors.sha_file(target)==receipt["composedImageSha256"],
             "existing composed owner image changed")
        return target
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"wb") as stream:
        stream.write(png)
        stream.flush()
        os.fsync(stream.fileno())
    return target

def verify_derived(receipt,owned,root):
    from . import band_iq_next_question as nxt
    nxt.ensure_record(receipt,SCHEMA,"bitSha256")
    expected,png=compose(receipt["baseSourceAssetId"],{
        "sourceAssetId":receipt["grabbedSourceAssetId"],
        "crop":receipt["crop"],"place":receipt["place"],
        "opacity":receipt["opacity"],
    },owned,root)
    need(expected==receipt,"crossed bit must still come from exact originals")
    target=Path(root)/derived_path(receipt)
    need(target.is_file() and donors.sha_file(target)==receipt["composedImageSha256"],
         "materialized crossed image is missing or changed")
    return target

def validate_draft_shots(shots,owned):
    """Exact in-memory multi-shot candidate validation, no save operation."""
    need(type(shots)==list and 1<=len(shots)<=256,
         "candidate tray needs a bounded collection of authored shots")
    use=0
    canonical=[]
    for shot in shots:
        need(type(shot)==dict and set(shot) in (
            {"shotId","sourceAssetId","focus","protectText"},
            {"shotId","sourceAssetId","focus","protectText","crossBit"}),
            "candidate shots must not carry hidden execution fields")
        need(type(shot["shotId"])==str and shot["sourceAssetId"] in owned,
             "candidate cannot invent a song shot or source")
        focus=shot["focus"]
        need(type(focus)==list and len(focus)==2 and all(
             type(v) in (float,int) and math.isfinite(v) and 0<=v<=1
             for v in focus),"candidate focal points must remain bounded")
        need(type(shot["protectText"])==bool,
             "candidate writing protection must be a boolean")
        clean={**shot,"focus":[round(float(v),3) for v in focus]}
        if "crossBit" in shot:
            clean["crossBit"]=checked_bit(shot["crossBit"],owned)
            use+=1
        canonical.append(clean)
    need(use<=MAX_CROSSES_PER_STORY,
         "too many composed source bits in one small candidate story")
    return canonical
