"""BAND-IQ 011: source-exact sampled motion stills, never a finished movie.

The same local raster function used by VidMage's source-aware renderer is
sampled at known real frame indices. Every sample belongs to a sealed
human-authored Storytable and pinned native Toaster observation. It has no
camera lens selected, sound track, moving-picture performance or KEEP.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path

import cv2

from . import band_iq as iq
from . import band_iq_donors as donors
from . import band_iq_next_question as nxt
from . import scene_card_film as film

SCHEMA="vidmage/band-iq-011-local-filmstrip-sketch/v1"
MAX_WINDOWS=36
POSITIONS=(0.12,0.50,0.88)

def need(ok,msg):
    iq.require(ok,msg)

def authorize(body, story):
    need(isinstance(body,dict) and set(body)=={
         "storySha256","makeLocalSketch","acknowledgeSketchNotFilm",
         "allowNetworkUpload","allowPaidProviders","allowPublication"},
         "filmstrip accepts only exact nonpublishing sketch authorization")
    need(body["storySha256"]==story["storySha256"] and
         body["makeLocalSketch"] is True and
         body["acknowledgeSketchNotFilm"] is True and
         body["allowNetworkUpload"] is False and
         body["allowPaidProviders"] is False and
         body["allowPublication"] is False,
         "no filmstrip without explicit same-story local sketch-only consent")
    return body

def selected_indices(count):
    need(type(count)==int and 1<=count<=256,"native shot count must be bounded")
    if count<=MAX_WINDOWS:
        return list(range(count))
    # Deterministic, full-song spread. Never automatically claim
    # the omitted shots are artistically less important.
    return [int(i*(count-1)/(MAX_WINDOWS-1)) for i in range(MAX_WINDOWS)]

def sample_times(shot,total_frames):
    start,end=float(shot["start"]),float(shot["end"])
    need(math.isfinite(start) and math.isfinite(end) and end>start,
         "native shot timing must be valid")
    eligible=[n for n in range(max(0,math.ceil(start*film.FPS-1e-8)),
                              min(total_frames,math.ceil(end*film.FPS-1e-8)))
              if start-1e-8<=n/film.FPS<end-1e-8]
    need(bool(eligible),"cannot sample a shot with no video frame")
    ids=[eligible[min(len(eligible)-1,
                      int(round((len(eligible)-1)*fraction)))]
         for fraction in POSITIONS]
    return [(n,round(n/film.FPS,6)) for n in ids]

def build(story,plan,cards,observation,audio,asset_root,destination):
    """Explicit local operation. Output is an immutable source-hashed sketch."""
    need(story.get("schema")=="vidmage/band-iq-010-human-storytable/v1" and
         story["storySha256"]==iq.digest({k:v for k,v in story.items()
                                        if k!="storySha256"}) and
         story["renderAuthorized"] is False and
         story["published"] is False and
         story["authoredCardsSha256"]==iq.digest(cards) and
         story["originalPaperPlanSha256"]==iq.digest(plan),
         "only intact human source arrangement can be sketched")
    audio=Path(audio).resolve(strict=True)
    need(donors.sha_file(audio)==observation["sourceAudioSha256"] if
         "sourceAudioSha256" in observation else audio.is_file(),
         "source audio changed")
    duration,assets,lanes=film.validate(plan,cards,observation,asset_root)
    need("raw-energy-envelope" in lanes,"native Toaster energy must be available")
    total_frames=round(duration*film.FPS)
    shots=plan["shots"]
    selected=selected_indices(len(shots))
    need([cards["shots"][i]["shotId"] for i in range(len(shots))]==
         [s["id"] for s in shots],
         "authored shot arrangement no longer covers exactly this song")
    dest=Path(destination).resolve()
    need(not dest.exists(),"preview is create-only: no overwrite or rerender on reopening")
    dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    rows=[]
    # All photographs must remain from the exact bytes the artist signed.
    for r in story["shotAssignments"]:
        need(r["sourceSha256"] in story["sourceOwnedPhotosSha256"].values(),
             "story references a photo from outside original owned material")
    need({key:source["sha256"] for key,source in assets.items()}==
         story["authoredImageBindings"],
         "actual raster source bytes changed since the human story seal")
    with tempfile.TemporaryDirectory(prefix=".partial-filmstrip-",dir=dest.parent) as tmp:
        folder=Path(tmp)
        for i in selected:
            native_shot=shots[i]
            choice=cards["shots"][i]
            source=assets[choice["assetId"]]
            stills=[]
            for j,(frame_no,at) in enumerate(sample_times(native_shot,total_frames)):
                fraction=max(0.,min(1.,(at-native_shot["start"])/
                               max(.00001,native_shot["end"]-native_shot["start"])))
                energy=film.value(lanes["raw-energy-envelope"],at)
                # 009's initial films are NOT kinetically selected; match
                # source-plain raster behavior without cinematic lens passes.
                actual=film.frame_for(source,fraction,energy,0.)
                need(actual.shape[:2]==(film.HEIGHT,film.WIDTH),
                     "local sampled raster dimensions changed")
                name="shot-%03d-frame-%d.jpg"%(i+1,j+1)
                output=folder/name
                ok=cv2.imwrite(str(output),actual,[cv2.IMWRITE_JPEG_QUALITY,90])
                need(ok and output.stat().st_size>200,
                     "failed to generate actual local raster preview")
                stills.append({
                    "file":name,
                    "sha256":donors.sha_file(output),
                    "actualFrameIndex":frame_no,
                    "atSeconds":at,
                    "samplePosition":POSITIONS[j],
                })
            authored=story["shotAssignments"][i]
            need(authored["shotId"]==native_shot["id"] and
                 authored.get("crossedImageSha256",authored["sourceSha256"])==source["sha256"],
                 "sampled timeline differs from human source choice")
            rows.append({
                "shotIndex":i,
                "shotId":native_shot["id"],
                "start":native_shot["start"],"end":native_shot["end"],
                "sourceAssetId":authored["sourceAssetId"],
                "sourceSha256":authored["sourceSha256"],
                "focus":authored["focus"],"protectText":authored["protectText"],
                "frames":stills,
            })
        base={
            "schema":SCHEMA,
            "status":"source-real-still-sketch-not-movie",
            "sourceStorySha256":story["storySha256"],
            "sourcePaperPlanSha256":iq.digest(plan),
            "sourceAuthoredCardsSha256":iq.digest(cards),
            "sourceNativeToasterObservationSha256":iq.digest(observation),
            "sourceAudioSha256":donors.sha_file(audio),
            "durationSeconds":duration,
            "nativeFrameRate":film.FPS,
            "imageSize":[film.WIDTH,film.HEIGHT],
            "sampledShotIndices":selected,
            "totalNativeShotCount":len(shots),
            "sampledWindowCount":len(rows),
            "framesPerSampledShot":len(POSITIONS),
            "sampledActualRasterShots":rows,
            "samplingRule":"12%-50%-88% of frame indices within each chosen native window",
            "sampledWindowPolicy":"all native windows up to 36; evenly spread 36 for larger song",
            "omittedWindowsAreNotRejected":True,
            "frameSource":"same local VidMage scene_card_film.frame_for without cinematic or kinetic passes",
            "movieGenerated":False,
            "audioRemixed":False,
            "filmKeep":False,
            "published":False,
            "allowPaidProviders":False,
            "allowNetworkUpload":False,
            "laws":["SKETCH != MOVIE","SAMPLED != COMPLETE COVERAGE",
                    "ONE STILL != CAMERA MOVEMENT","SOURCE != PUBLIC RELEASE",
                    "AUTHORSHIP != AUTOMATIC FILM SELECTION"],
        }
        record={**base,"filmstripSha256":iq.digest(base)}
        (folder/"filmstrip.json").write_text(
            json.dumps(record,indent=2,sort_keys=True,ensure_ascii=False)+"\n",
            encoding="utf8")
        # Same-directory atomic move: do not leave half-built previews
        # under the public fixed preview path on failure.
        need(not dest.exists(),"cannot overwrite an already generated filmstrip")
        folder.rename(dest)
    return verify(dest,story,plan,cards,observation,audio,asset_root)

def verify(destination,story,plan,cards,observation,audio,asset_root):
    root=Path(destination).resolve(strict=True)
    saved=nxt.ensure_record(json.loads((root/"filmstrip.json").read_text("utf8")),
                            SCHEMA,"filmstripSha256")
    need(saved["sourceStorySha256"]==story["storySha256"] and
         saved["sourcePaperPlanSha256"]==iq.digest(plan) and
         saved["sourceAuthoredCardsSha256"]==iq.digest(cards) and
         saved["sourceNativeToasterObservationSha256"]==iq.digest(observation) and
         saved["sourceAudioSha256"]==donors.sha_file(audio) and
         saved["durationSeconds"]==plan["durationSeconds"] and
         saved["nativeFrameRate"]==film.FPS and
         saved["imageSize"]==[film.WIDTH,film.HEIGHT] and
         saved["movieGenerated"] is False and
         saved["filmKeep"] is False and saved["published"] is False and
         saved["allowNetworkUpload"] is False and
         saved["allowPaidProviders"] is False and
         saved["omittedWindowsAreNotRejected"] is True and
         saved["totalNativeShotCount"]==len(plan["shots"]) and
         saved["sampledShotIndices"]==selected_indices(len(plan["shots"])),
         "local sketch does not belong to exact author source or false film authority")
    _,assets,_=film.validate(plan,cards,observation,asset_root)
    need({key:source["sha256"] for key,source in assets.items()}==
         story["authoredImageBindings"],
         "source image changed after preview")
    need(len(saved["sampledActualRasterShots"])==
         len(saved["sampledShotIndices"])==saved["sampledWindowCount"] and
         saved["framesPerSampledShot"]==3,
         "actual sampled source windows count mismatch")
    names=set()
    for row,index in zip(saved["sampledActualRasterShots"],
                         saved["sampledShotIndices"]):
        original=plan["shots"][index]
        owner=story["shotAssignments"][index]
        need(row["shotIndex"]==index and
             row["shotId"]==original["id"]==owner["shotId"] and
             row["start"]==original["start"] and row["end"]==original["end"] and
             row["sourceAssetId"]==owner["sourceAssetId"] and
             row["sourceSha256"]==owner["sourceSha256"] and
             row["focus"]==owner["focus"] and
             row["protectText"]==owner["protectText"] and
             len(row["frames"])==3,"source shot metadata changed")
        expected=sample_times(original,round(saved["durationSeconds"]*film.FPS))
        for j,(image,(frame_num,t)) in enumerate(zip(row["frames"],expected)):
            name="shot-%03d-frame-%d.jpg"%(index+1,j+1)
            need(image["file"]==name and name not in names and
                 image["actualFrameIndex"]==frame_num and
                 image["atSeconds"]==t and
                 image["samplePosition"]==POSITIONS[j],
                 "preview time index changed")
            names.add(name)
            path=(root/name).resolve(strict=True)
            need(path.is_relative_to(root) and path.is_file() and
                 donors.sha_file(path)==image["sha256"],
                 "actual sampled frame bytes changed")
    need(len(names)==saved["sampledWindowCount"]*3,
         "preview frame count changed")
    return saved

def image_at(root,receipt,index,subframe):
    """Only fixed numbered author-preview frame routes are allowed."""
    need(type(index)==int and type(subframe)==int and
         0<=index<len(receipt["sampledActualRasterShots"]) and
         0<=subframe<3,
         "unknown filmstrip sample")
    frame=receipt["sampledActualRasterShots"][index]["frames"][subframe]
    name=frame["file"]
    need(name.startswith("shot-") and name.endswith(".jpg") and "/" not in name,
         "unknown sourced preview image")
    file=(Path(root)/name).resolve(strict=True)
    need(file.is_relative_to(Path(root).resolve(strict=True)) and
         donors.sha_file(file)==frame["sha256"],
         "local preview image was changed or substituted")
    return file
