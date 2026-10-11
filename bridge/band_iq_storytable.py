"""BAND-IQ 010: owner-authored pre-render, exact-time source and framing table.

The original 009 Paper Director plan remains immutable. Its timing is borrowed,
never rewritten; the artist selects each shot's owned source and framing.
A separate, create-only, hash-bound receipt is required BEFORE 009's A/B render.
"""
from __future__ import annotations
import json
import math
from pathlib import Path

from . import band_iq as iq
from . import band_iq_film_loop as loop
from . import scene_card_film as film
from . import band_iq_cross_bits as cross

SCHEMA="vidmage/band-iq-010-human-storytable/v1"
MAX_SHOTS=256

def need(ok,msg):iq.require(ok,msg)

def author(form,paper_tray,plan,original_cards,asset_root):
    need(isinstance(form,dict) and set(form)=={
        "paperTraySha256","operatorAttestationId","decision",
        "shots","preserveOriginals","publish","allowPaidProviders",
        "allowNetworkUpload"},
        "storytable only accepts one explicit exact owner-authored shot map")
    need(form["paperTraySha256"]==paper_tray["paperTraySha256"] and
         form["decision"]=="SEAL_STORYTABLE" and
         form["preserveOriginals"] is True and
         form["publish"] is False and form["allowPaidProviders"] is False and
         form["allowNetworkUpload"] is False,
         "storytable is a human local arrangement, not permission to render or release")
    iq.bounded(form["operatorAttestationId"],
               "new named owner attestation required to seal story",256)
    need(plan.get("schema")=="haunted-blender/paper-director-plan/v1" and
         original_cards.get("schema")=="vidmage/editorial-scene-cards/v1" and
         paper_tray["paperPlanSha256"]==iq.digest(plan) and
         paper_tray["sceneCardsSha256"]==iq.digest(original_cards),
         "original Paper Director or initial card source moved")
    source=original_cards["assets"]
    old_shots=plan["shots"]
    choices=form["shots"]
    need(isinstance(choices,list) and 1<=len(choices)<=MAX_SHOTS and
         len(choices)==len(old_shots),
         "every actual Paper Director time window needs one owner's shot")
    need(set(source) and len(source)<=12,"story sources must be actual owned photos")
    expected=loop.exact_asset_bindings(original_cards,asset_root)
    need(expected==paper_tray["stillSha256"],
         "original prepared still source bytes changed")
    assets={}
    cards=[]
    history=[]
    for i,(timing,selection) in enumerate(zip(old_shots,choices)):
        need(isinstance(selection,dict) and
             set(selection) in ({"shotId","sourceAssetId","focus","protectText"},
                                {"shotId","sourceAssetId","focus","protectText","crosses"}),
            "one exact owned image, framing and optional bounded borrowed pieces required")
        sid=timing["id"];aid=selection["sourceAssetId"];focus=selection["focus"]
        need(selection["shotId"]==sid and aid in source,
             "authored shot ID or owned image choice unknown")
        need(isinstance(focus,list) and len(focus)==2 and all(
             type(k) in (float,int) and math.isfinite(k) and 0<=k<=1
             for k in focus),
             "framing focal point must be two finite 0–1 values")
        need(type(selection["protectText"])==bool,
             "protected writing is an explicit per-shot boolean")
        focus=[round(float(x),3) for x in focus]
        key="shot-asset-%04d"%(i+1)
        bits=cross.validate_bits(selection.get("crosses",[]),source)
        crossing=(cross.verify_cross(aid,bits,source,asset_root,expected,i)
                  if bits else None)
        # One shot alias may refer to a non-destructive, independently sourced
        # composite, with every borrowed crop traced to its original.
        assets[key]={
            "path":crossing["path"] if crossing else source[aid]["path"],
            "mode":"protect-text" if selection["protectText"] else "subject",
            "focus":focus,
        }
        cards.append({"shotId":sid,"assetId":key,"kineticSafe":False})
        record={
            "shotId":sid,"sourceAssetId":aid,
            "sourceSha256":expected[aid],
            "start":timing["start"],"end":timing["end"],
            "focus":focus,"protectText":selection["protectText"],
        }
        if bits:
            record["crosses"]=bits
            record["crossedImageSha256"]=crossing["sha256"]
            record["borrowedSources"]=crossing["sourceEvidence"]
        history.append(record)
    result_cards={"schema":"vidmage/editorial-scene-cards/v1",
                  "status":"proposal-only","assets":assets,"shots":cards}
    film.validate(plan,result_cards,
                  {"schema":"vidmage/toaster-lbranch-observation/v1",
                   "laneBank":{"schema":"haunted-toaster/lane-bank/v1",
                               "lanes":[{"id":"raw-energy-envelope",
                                         "knots":[{"atSeconds":0,"value":0},
                                                  {"atSeconds":plan["durationSeconds"],
                                                   "value":0}]}]}},
                  asset_root)
    actual=loop.exact_asset_bindings(result_cards,asset_root)
    need(all(actual["shot-asset-%04d"%(i+1)]==
             r.get("crossedImageSha256",r["sourceSha256"])
             for i,r in enumerate(history)),
         "authored shot does not reproduce source-pinned owned or crossed image bytes")
    body={
        "schema":SCHEMA,"status":"owner-authored-before-film",
        "sourcePaperTraySha256":paper_tray["paperTraySha256"],
        "originalPaperPlanSha256":iq.digest(plan),
        "originalProvisionalCardsSha256":iq.digest(original_cards),
        "sourceOwnedPhotosSha256":expected,
        "shotAssignments":history,
        "authoredCardsSha256":iq.digest(result_cards),
        "authoredImageBindings":actual,
        "operatorAttestationId":form["operatorAttestationId"].strip(),
        "renderAuthorized":False,"humanKeep":False,
        "published":False,"allowNetworkUpload":False,"allowPaidProviders":False,
        "laws":["PAPER TIME != MACHINE'S STORY",
                "ONE IMAGE != ONE FRAMING",
                "AUTHOR ARRANGEMENT != FILM EXECUTION",
                "PROTECT TEXT != CENSOR IMAGE",
                "PREPARED SOURCE != REWRITTEN ORIGINAL"],
    }
    return {**body,"storySha256":iq.digest(body)},result_cards

def verified(receipt_path,cards_path,paper_tray,plan,original_cards,asset_root):
    from . import band_iq_next_question as nxt
    saved=nxt.ensure_record(json.loads(Path(receipt_path).read_text()),
                            SCHEMA,"storySha256")
    authored=json.loads(Path(cards_path).read_text())
    selections=[{
        "shotId":x["shotId"],"sourceAssetId":x["sourceAssetId"],
        "focus":x["focus"],"protectText":x["protectText"],
        **({"crosses":x["crosses"]} if "crosses" in x else {}),
    } for x in saved["shotAssignments"]]
    form={
        "paperTraySha256":paper_tray["paperTraySha256"],
        "operatorAttestationId":saved["operatorAttestationId"],
        "decision":"SEAL_STORYTABLE",
        "shots":selections,
        "preserveOriginals":True,"publish":False,
        "allowPaidProviders":False,"allowNetworkUpload":False,
    }
    expected,cards=author(form,paper_tray,plan,original_cards,asset_root)
    need(expected==saved and cards==authored and
         iq.digest(authored)==saved["authoredCardsSha256"],
         "source-pinned human storytable or sealed snapshot changed")
    return saved,authored
