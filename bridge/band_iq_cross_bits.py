"""BAND-IQ 013: bounded borrowed photo rectangles, with traceable owner-local pixels.

No segmentation claims: a "bit" is an actual rectangular source crop. No source
file is overwritten; final composites are create-only derived PNG assets.
"""
from __future__ import annotations
import hashlib
import math
from pathlib import Path
import cv2
from . import band_iq as iq
from . import band_iq_donors as donors
from . import band_iq_film_loop as loop
from . import scene_card_film as film
from . import band_iq_contact_sheet as contact
from . import band_iq_living_filmstrip as strip

MAX_BITS=3
SCHEMA="vidmage/band-iq-013-crossed-bits-contact/v1"

def need(ok,msg):iq.require(ok,msg)
def finite(v):return type(v) in (int,float) and math.isfinite(v)

def validate_bits(bits,original_assets):
    need(type(bits)==list and len(bits)<=MAX_BITS,
         "up to three explicit rectangular borrowed pieces per shot")
    output=[]
    for b in bits:
        need(type(b)==dict and set(b)=={"sourceAssetId","grab","place","opacity"},
             "crossing only accepts named owned source, grab, place, opacity")
        need(type(b["sourceAssetId"])==str and b["sourceAssetId"] in original_assets,
             "borrowed bit must originate from an existing owned photograph")
        for name in ("grab","place"):
            box=b[name]
            need(type(box)==list and len(box)==4 and all(finite(x) for x in box),
                 "grab/place must be finite normalized x,y,width,height rectangles")
            x,y,w,h=box
            need(0<=x<=1 and 0<=y<=1 and .05<=w<=1 and .05<=h<=1
                 and x+w<=1.0000001 and y+h<=1.0000001,
                 "grabbed and placed rectangles must fit within original image")
        need(finite(b["opacity"]) and .1<=b["opacity"]<=1,
             "cross-bit opacity must be explicitly between 0.1 and 1")
        output.append({
            "sourceAssetId":b["sourceAssetId"],
            "grab":[round(float(x),4) for x in b["grab"]],
            "place":[round(float(x),4) for x in b["place"]],
            "opacity":round(float(b["opacity"]),3),
        })
    return output

def source_images(assets,root,expected):
    actual=loop.exact_asset_bindings({"assets":assets},root)
    need(actual==expected,"prepared original photo pixels changed since owner's consent")
    out={}
    for key,entry in assets.items():
        path=(Path(root)/entry["path"]).resolve(strict=True)
        need(path.is_relative_to(Path(root).resolve(strict=True)),
             "cross source cannot leave the private owned photo root")
        img=cv2.imread(str(path))
        need(img is not None and img.ndim==3 and img.shape[2]==3,
             "cross source is not an actual decodable owned RGB image")
        out[key]=img
    return out

def _rect(box,width,height):
    x,y,w,h=box
    x0=min(width-1,max(0,round(x*width)))
    y0=min(height-1,max(0,round(y*height)))
    x1=max(x0+1,min(width,round((x+w)*width)))
    y1=max(y0+1,min(height,round((y+h)*height)))
    return x0,y0,x1,y1

def compose(base_asset,bits,original_images):
    need(base_asset in original_images,"cross target is not an owned photo")
    canvas=original_images[base_asset].copy()
    h,w=canvas.shape[:2]
    for bit in bits:
        source=original_images[bit["sourceAssetId"]]
        sh,sw=source.shape[:2]
        sx,sy,ex,ey=_rect(bit["grab"],sw,sh)
        px,py,qx,qy=_rect(bit["place"],w,h)
        patch=source[sy:ey,sx:ex]
        patch=cv2.resize(patch,(qx-px,qy-py),interpolation=cv2.INTER_AREA)
        current=canvas[py:qy,px:qx]
        alpha=bit["opacity"]
        canvas[py:qy,px:qx]=cv2.addWeighted(patch,alpha,current,1-alpha,0)
    return canvas

def encoded_png(image):
    ok,buf=cv2.imencode(".png",image,[cv2.IMWRITE_PNG_COMPRESSION,3])
    need(ok,"could not encode borrowed pixels to local PNG")
    return buf.tobytes()

def expected_cross(base_asset,bits,original_assets,root,expected):
    allowed=validate_bits(bits,original_assets)
    source=source_images(original_assets,root,expected)
    content=encoded_png(compose(base_asset,allowed,source))
    return allowed,content,hashlib.sha256(content).hexdigest()

def materialize_for_form(form,original_assets,root,expected):
    """Separate local derivative step during explicit Storytable sealing ONLY."""
    shots=form.get("shots",[]) if isinstance(form,dict) else []
    need(type(shots)==list and len(shots)<=256,
         "bounded author selected shots needed for local crossing")
    prepared=[]
    for i,shot in enumerate(shots):
        if type(shot)!=dict or not shot.get("crosses"):continue
        base=shot.get("sourceAssetId")
        need(type(base)==str and base in original_assets,
             "cannot cross onto an unowned picture")
        bits,data,sha=expected_cross(base,shot["crosses"],original_assets,root,expected)
        prepared.append((i,data,sha))
    if not prepared:return
    destination=Path(root)/"crossed-bits"
    destination.mkdir(mode=0o700,exist_ok=True)
    for i,data,sha in prepared:
        path=destination/("shot-asset-%04d.png"%(i+1))
        if path.exists():
            need(donors.sha_file(path)==sha,
                 "existing sealed cross-bit pixels differ; refusing overwrite")
        else:
            flags=__import__("os").O_CREAT|__import__("os").O_EXCL|__import__("os").O_WRONLY
            import os
            fd=os.open(path,flags,0o600)
            with os.fdopen(fd,"wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())

def verify_cross(base_asset,bits,original_assets,root,expected,index):
    allowed,data,sha=expected_cross(base_asset,bits,original_assets,root,expected)
    path=Path(root)/"crossed-bits"/("shot-asset-%04d.png"%(index+1))
    need(path.is_file() and donors.sha_file(path)==sha,
         "cross-bit composition must reproduce exactly from owned original sources")
    return {"path":"crossed-bits/shot-asset-%04d.png"%(index+1),
            "sha256":sha,
            "sourceEvidence":[{
                "sourceAssetId":b["sourceAssetId"],
                "sourceSha256":expected[b["sourceAssetId"]],
                "grab":b["grab"],"place":b["place"],"opacity":b["opacity"],
            } for b in allowed]}

def preview(form,paper,plan,original,observation,audio,root):
    """Preview a single borrowed bit on a source shot using actual frame_for()."""
    need(type(form)==dict and set(form)=={
        "paperTraySha256","shotId","left","right",
        "compareOnly","allowStorySeal","allowMovieRender",
        "allowNetworkUpload","allowPaidProviders","allowPublication"},
        "cross contact requires exactly two choices and no execution rights")
    a=form["left"];b=form["right"]
    need(type(a)==dict and type(b)==dict and set(a)=={
         "sourceAssetId","focus","protectText","crosses"} and
         set(b)=={"sourceAssetId","focus","protectText","crosses"},
         "cross preview choices require exact source and borrowed pieces")
    need(form["paperTraySha256"]==paper["paperTraySha256"] and
         form["compareOnly"] is True and
         all(form[k] is False for k in (
             "allowStorySeal","allowMovieRender","allowNetworkUpload",
             "allowPaidProviders","allowPublication")),
         "a cross contact can never authorize a seal, movie or publication")
    need(paper["paperPlanSha256"]==iq.digest(plan) and
         paper["sceneCardsSha256"]==iq.digest(original) and
         paper["toasterObservationSha256"]==iq.digest(observation) and
         film.sha(audio)==paper["audioSha256"],
         "cross contact requires exact original music and native paper")
    index=[i for i,s in enumerate(plan["shots"]) if s["id"]==form["shotId"]]
    need(len(index)==1,"unknown native shot window")
    left=contact.checked_choice({k:a[k] for k in ("sourceAssetId","focus","protectText")},original["assets"])
    right=contact.checked_choice({k:b[k] for k in ("sourceAssetId","focus","protectText")},original["assets"])
    a_bits=validate_bits(a["crosses"],original["assets"])
    b_bits=validate_bits(b["crosses"],original["assets"])
    need(len(a_bits)+len(b_bits)<=2*MAX_BITS,"too many borrowed pieces")
    images=source_images(original["assets"],root,paper["stillSha256"])
    duration,_,lanes=film.validate(plan,original,observation,root)
    shot=plan["shots"][index[0]]
    times=strip.sample_times(shot,round(duration*film.FPS))
    frames={};rows={}
    for side,choice,bits in (("left",left,a_bits),("right",right,b_bits)):
        source={"image":compose(choice["sourceAssetId"],bits,images),
                "focus":choice["focus"],
                "mode":"protect-text" if choice["protectText"] else "subject"}
        results=[]
        for n,(frame_id,at) in enumerate(times):
            elapsed=max(0.,min(1.,(at-shot["start"])/max(.00001,shot["end"]-shot["start"])))
            pix=film.frame_for(source,elapsed,film.value(lanes["raw-energy-envelope"],at),0.)
            ok,data=cv2.imencode(".jpg",pix,[cv2.IMWRITE_JPEG_QUALITY,89])
            need(ok,"source cross thumbnail encoding failed")
            jpeg=data.tobytes()
            need(100<len(jpeg)<700000,"cross thumbnail exceeds private preview limit")
            frames[(side,n)]=jpeg
            results.append({"nativeFrameIndex":frame_id,"atSeconds":at,
                            "imageSha256":hashlib.sha256(jpeg).hexdigest()})
        rows[side]={**choice,"crosses":bits,"frames":results,
                    "sourceSha256":paper["stillSha256"][choice["sourceAssetId"]]}
    body={
        "schema":SCHEMA,"status":"ephemeral-cross-candidate-not-authorized-film",
        "sourcePaperTraySha256":paper["paperTraySha256"],
        "sourcePlanSha256":iq.digest(plan),"sourceToasterSha256":iq.digest(observation),
        "shotId":shot["id"],"shotIndex":index[0],
        "shotStart":shot["start"],"shotEnd":shot["end"],
        "left":rows["left"],"right":rows["right"],
        "sourceDraftModified":False,"humanStorySealed":False,
        "movieGenerated":False,"published":False,"artisticJudgment":None,
        "laws":["GRAB != CUT ORIGINAL","CROSS != KEEP","COMPARE != SEAL",
                "RECTANGLE != SEMANTIC SEGMENTATION"],
    }
    return {**body,"comparisonSha256":iq.digest(body)},frames
