"""BAND-IQ 012 — ephemeral human A/B contact sheet before Storytable seal.

Purely compares two explicit treatments of ONE existing, source-pinned shot.
Uses the exact VidMage raster function and source images in working memory.
No disk writes, signed story, film permission, provider, publication or KEEP.
"""
from __future__ import annotations
import hashlib
import math
from pathlib import Path

import cv2

from . import band_iq as iq
from . import band_iq_living_filmstrip as strip
from . import band_iq_film_loop as loop
from . import scene_card_film as film

SCHEMA="vidmage/band-iq-012-ephemeral-contact-sheet/v1"
POSITIONS=strip.POSITIONS

def need(ok,msg): iq.require(ok,msg)

def checked_choice(choice,assets):
    need(type(choice)==dict and set(choice)=={
        "sourceAssetId","focus","protectText"},
        "one side needs exact already-owned photo, two focus dials and writing protection")
    aid=choice["sourceAssetId"]
    need(type(aid)==str and aid in assets,
         "only original prepared owned photographs can be compared")
    focus=choice["focus"]
    need(type(focus)==list and len(focus)==2 and all(
        type(x) in (int,float) and math.isfinite(x) and 0<=x<=1
        for x in focus),
        "focus coordinates must be finite numbers in [0,1]")
    need(type(choice["protectText"])==bool,"protectText must be a boolean")
    return {"sourceAssetId":aid,
            "focus":[round(float(x),3) for x in focus],
            "protectText":choice["protectText"]}

def check_request(form,paper,plan,provisional):
    need(type(form)==dict and set(form)=={
        "paperTraySha256","shotId","left","right",
        "compareOnly","allowStorySeal","allowMovieRender",
        "allowNetworkUpload","allowPaidProviders","allowPublication"},
        "contact sheet needs exactly two bounded local candidate choices")
    need(form["paperTraySha256"]==paper["paperTraySha256"] and
         form["compareOnly"] is True and
         form["allowStorySeal"] is False and
         form["allowMovieRender"] is False and
         form["allowNetworkUpload"] is False and
         form["allowPaidProviders"] is False and
         form["allowPublication"] is False,
         "this is only a local comparison, never authoring or rendering authority")
    need(paper["paperPlanSha256"]==iq.digest(plan) and
         paper["sceneCardsSha256"]==iq.digest(provisional),
         "provisional shot plan and owned image order changed")
    shots=plan["shots"]
    sid=form["shotId"]
    need(type(sid)==str and len(sid)<=160,"native shot ID required")
    indices=[i for i,s in enumerate(shots) if s["id"]==sid]
    need(len(indices)==1,"contact sheet must reference exactly one native time window")
    assets=provisional["assets"]
    a=checked_choice(form["left"],assets)
    b=checked_choice(form["right"],assets)
    return indices[0],a,b

def comparison(form,paper,plan,provisional,observation,audio,asset_root):
    """Return (bounded private manifest, six JPEG bytes); no writes anywhere."""
    shot_index,left,right=check_request(form,paper,plan,provisional)
    duration,assets,lanes=film.validate(plan,provisional,observation,asset_root)
    bindings=loop.exact_asset_bindings(provisional,asset_root)
    need(bindings==paper["stillSha256"],
         "prepared stills have been replaced after native paper preparation")
    need(Path(audio).is_file() and
         film.sha(audio)==paper["audioSha256"],
         "prepared song changed after native paper preparation")
    need(iq.digest(observation)==paper["toasterObservationSha256"],
         "native observed audio changed")
    total_frames=round(duration*film.FPS)
    native_shot=plan["shots"][shot_index]
    samples=strip.sample_times(native_shot,total_frames)
    frames={}
    rows={}
    for side,choice in (("left",left),("right",right)):
        source=assets[choice["sourceAssetId"]]
        instance={**source,
                  "focus":choice["focus"],
                  "mode":"protect-text" if choice["protectText"] else "subject"}
        produced=[]
        for j,(frame_no,at) in enumerate(samples):
            progress=max(0.,min(1.,(at-native_shot["start"])/
                         max(.00001,native_shot["end"]-native_shot["start"])))
            energy=film.value(lanes["raw-energy-envelope"],at)
            pix=film.frame_for(instance,progress,energy,0.)
            need(pix.shape[:2]==(film.HEIGHT,film.WIDTH),
                 "source renderer returned an unexpected raster")
            ok,encoded=cv2.imencode(".jpg",pix,[cv2.IMWRITE_JPEG_QUALITY,89])
            need(ok,"source raster could not become a bounded JPEG")
            data=encoded.tobytes()
            need(100<len(data)<=700000,"sample pixel output exceeds safe bounds")
            frames[(side,j)]=data
            produced.append({
                "nativeFrameIndex":frame_no,"atSeconds":at,
                "samplePosition":POSITIONS[j],
                "imageSha256":hashlib.sha256(data).hexdigest(),
            })
        rows[side]={
            **choice,"sourceSha256":bindings[choice["sourceAssetId"]],
            "frames":produced}
    basis={
        "schema":SCHEMA,
        "status":"ephemeral-human-candidate-only",
        "sourcePaperTraySha256":paper["paperTraySha256"],
        "sourcePlanSha256":iq.digest(plan),
        "sourceProvisionalCardsSha256":iq.digest(provisional),
        "sourceToasterObservationSha256":iq.digest(observation),
        "sourceAudioSha256":film.sha(audio),
        "shotId":native_shot["id"],
        "shotIndex":shot_index,
        "shotStart":native_shot["start"],"shotEnd":native_shot["end"],
        "left":rows["left"],"right":rows["right"],
        "samplingMethod":"actual 12fps VidMage frame_for at 12/50/88 percent frame positions",
        "sourcePixelsReal":True,"framesInMemoryOnly":True,
        "sourceDraftModified":False,"humanStorySealed":False,
        "movieGenerated":False,"artisticJudgment":None,
        "humanKeep":False,"published":False,"allowNetworkUpload":False,
        "allowPaidProviders":False,
        "laws":["CONTACT != STORY","BEFORE != DEFAULT",
                "PIXELS != PREFERENCE","APPLY != SEAL",
                "PREVIEW != MOVIE","CANDIDATE != AUTOMATIC CHOICE"],
    }
    result={**basis,"comparisonSha256":iq.digest(basis)}
    return result,frames

def verified_image(receipt,images,sha,side,sample):
    """Return only image bytes currently held in the owner's local session."""
    need(type(sha)==str and sha==receipt["comparisonSha256"] and
         type(side)==str and side in ("left","right") and
         type(sample)==int and 0<=sample<3,
         "no active matching local comparison frame")
    image=images[(side,sample)]
    need(hashlib.sha256(image).hexdigest()==
         receipt[side]["frames"][sample]["imageSha256"],
         "contact frame changed while held in local memory")
    return image
