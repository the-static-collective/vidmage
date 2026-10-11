"""BAND-IQ 003: source-locked actual Playdeck/Remotion performance.

Uses the native Playdeck 011 PlaydeckComposition and frankenCinematicState.
This is not a reimplementation of Playdeck's renderer, a Playdeck KEEP,
an assertion of pixel equivalence, or an automatic film publication.
"""
from __future__ import annotations
import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from . import band_iq as iq
from . import band_iq_donors as donors
from . import band_iq_film_loop as band

PLAYDECK_SHA="012186fd67f4c4ef1c6591fc5e29cb559b5a80d0"
SCHEMA="vidmage/band-iq-native-playdeck-film/v1"
PAIR_SCHEMA="vidmage/band-iq-dual-renderer-comparison/v1"
GRAMMAR_FIELDS=("cameraMode","topology","cutRhythm","relationMode","memoryMode")
GRAMMAR={
  "landscape":("survey","terrain-bands","long-breath","parallel-drift","erosion"),
  "architecture":("hinge-orbit","corridor","measured-cuts","axial-lock","room-trace"),
  "organism":("pulse-dolly","cellular-cluster","elastic-pulse","attraction-repulsion","scar-recall"),
  "sigil":("snap-frame","glyph-grid","syncopated-cuts","stroke-link","overwrite-ghost"),
  "weather":("wind-eye","particle-field","gust-bursts","swarm","wake"),
  "dimensional-space":("parallax-orbit","nested-planes","folded-time","orbit-crossing","nested-afterimage"),
}

def need(ok,msg):
    iq.require(ok,msg)

def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def check_playdeck_checkout(repo_root):
    root=Path(repo_root).expanduser().resolve(strict=True)
    actual=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],
                          text=True,capture_output=True,check=True).stdout.strip()
    need(actual==PLAYDECK_SHA,"Playdeck source checkout changed or unpinned")
    need((root/"packages"/"render-remotion"/"src"/"Root.tsx").is_file() and
         (root/"packages"/"render-remotion"/"src"/"frankenCinematic.ts").is_file(),
         "native Playdeck Remotion and Studio 011 grammar unavailable")
    return root

def convert_to_native_props(cycle,before,selection,paper_plan,cards,
                            observation,audio,asset_root,baseline_movie):
    """Pure two-renderer source binding; native Remotion consumes returned props."""
    proposal,bindings,_=band.validate_selection(
        cycle,before,selection,paper_plan,cards,observation,audio,
        asset_root,baseline_movie)
    lens=proposal["lensId"]
    need(lens in GRAMMAR,"unsupported six-lens Playdeck hypothesis")
    grammar_tuple=tuple(proposal[k] for k in GRAMMAR_FIELDS)
    need(grammar_tuple==GRAMMAR[lens],"source proposal no longer has native Playdeck 011 grammar")

    duration=float(paper_plan["durationSeconds"])
    source_shots=paper_plan["shots"]
    authored_shots=cards["shots"]
    need(1<=len(source_shots)<=256 and len(source_shots)==len(authored_shots),
         "native output requires every source shot")
    deck_id="band-iq-deck:"+cycle["cycleSha256"][:24]
    track_id="band-iq-track:"+selection["audioSha256"][:24]
    world_id="band-iq-world:"+proposal["proposalSha256"][:24]
    deck_cards=[]
    gate_events=[]
    image_uri_by_asset={}
    for index,(shot,card_assignment) in enumerate(zip(source_shots,authored_shots)):
        aid=card_assignment["assetId"]
        need(aid in bindings and shot["id"]==card_assignment["shotId"],
             "selected shot lost exact material assignment")
        uri=f"asset://band-iq-003/{aid}"
        image_uri_by_asset[aid]=uri
        cid=f"card-{index+1:04d}"
        deck_cards.append({
            "id":cid,"source":uri,"front":{"source":uri},
            "traits":["author-selected-media"],"temperament":["trial-not-keep"],
            "permissions":{"flip":False,"fold":False,"fracture":False,"portal":False,
                           "awaken":False},
            "metadata":{"bandIqSourceAssetId":aid,"bandIqSourceSha256":bindings[aid],
                        "paperShotId":shot["id"],"paperShotStart":shot["start"],
                        "paperShotEnd":shot["end"],
                        "sourceOccurrenceNotNewMaterial":True},
        })
        gate_events.append({
            "id":f"arrival-{index+1:04d}",
            "at":float(shot["start"]),
            "duration":float(shot["end"])-float(shot["start"]),
            "type":"arrive","cards":[cid],
            "params":{"sourceAuthority":"editor-authored", "sourceShotId":shot["id"]},
        })

    grammar={k:proposal[k] for k in GRAMMAR_FIELDS}
    # Explicitly bounded event-only native Playdeck franken cinematic.
    # No plan.metadata.studioFranken: avoiding default whole-song camera motion.
    target_start=float(proposal["targetStart"])
    target_end=float(proposal["targetEnd"])
    need(0<=target_start<target_end<=duration+.02,"invalid elected window")
    grammar_event={
        "id":"band-iq-selected-window",
        "at":target_start,"duration":target_end-target_start,
        "type":"custom","cards":[],
        "params":{"franken":{
            "lensId":lens,
            "cinematic":{**grammar,
                        "shotIndex":0,"phase":0,
                        "framingScale":1.0,"motionAmplitude":18,
                        "relationStrength":0.5,"memoryOpacity":0.15},
            "producer":"BAND-IQ 003 explicit operator selection",
            "selectionSha256":iq.digest(selection),
        }},
    }
    # Existing TrackSpec source is a logical identity. Actual audio is staged later.
    audio_uri="asset://band-iq-003/source-audio"
    lane=next((x for x in observation["laneBank"]["lanes"]
               if x.get("id")=="raw-energy-envelope"),None)
    need(isinstance(lane,dict) and isinstance(lane.get("knots"),list)
         and len(lane["knots"])>=2,"actual Toaster native energy knots required")
    envelope=[]
    for knot in lane["knots"]:
        t=knot.get("atSeconds"); v=knot.get("value")
        need(iq.finite(t,0,duration+.03) and iq.finite(v,0,1),
             "invalid native audio observation knot")
        envelope.append([t,v,v,v])
    deck={"schemaVersion":"0.1","id":deck_id,"title":"BAND-IQ witnessed native trial",
          "cards":deck_cards,"order":[x["id"] for x in deck_cards],
          "metadata":{"bandIqCycleSha256":cycle["cycleSha256"],
                      "authorSelectedNotPublished":True}}
    track={"schemaVersion":"0.1","id":track_id,"title":"Source-audio witnessed trial",
           "source":audio_uri,"duration":duration,
           "gates":[{"id":f"gate-{index:04d}","at":float(s["start"]),
                     "kind":"verse","label":"Paper Director shot boundary (not a lyric)"}
                    for index,s in enumerate(source_shots)],
           "metadata":{"sourceAudioSha256":selection["audioSha256"],
                       "actualToasterObservationSha256":iq.digest(observation)}}
    world={"schemaVersion":"0.1","id":world_id,"physical":"postcard",
           "surface":"paper","transition":"bounded-cinematic-window",
           "laws":["MATERIAL != SEMANTIC SEGMENTATION","TRIAL != KEEP"]}
    plan={
        "schemaVersion":"0.1",
        "id":"band-iq-playdeck-plan:"+iq.digest({
            "cycle":cycle["cycleSha256"],"proposal":proposal["proposalSha256"],
            "sourcePlan":iq.digest(paper_plan),"cards":iq.digest(cards)})[:24],
        "deckId":deck_id,"trackId":track_id,"worldRuleId":world_id,
        "duration":duration,"fps":12,"width":640,"height":360,
        "gates":[{"id":f"gate-{i:04d}","at":float(shot["start"]),"kind":"verse"}
                 for i,shot in enumerate(source_shots)],
        "events":[*gate_events,grammar_event],
        "renderHints":{"preferredRenderer":"remotion","deterministic":True,
                       "notes":["Native Playdeck source-pinned separate renderer trial"]},
        "metadata":{"bandIqNativeComparison":{
             "schema":"vidmage/band-iq-playdeck-context/v1",
             "cycleSha256":cycle["cycleSha256"],
             "selectedProposalSha256":proposal["proposalSha256"],
             "targetStart":target_start,"targetEnd":target_end,
             "preservedNoCinematicBeyondSelectedWindow":True,
             "playdeckStudio011Grammar":True,
             "nativeRenderer":"@playdeck/render-remotion",
             "nativeToasterObservationSha256":iq.digest(observation),
             "editorialSceneCardsSha256":iq.digest(cards),
             "originalMovieSha256":before["sourceVideoSha256"],
        }},
    }
    bindings_logical={uri:bindings[aid] for aid,uri in image_uri_by_asset.items()}
    bindings_logical[audio_uri]=selection["audioSha256"]
    return {
        "deck":deck,"track":track,"worldRule":world,"plan":plan,
        "assets":{}, "envelope":envelope,"debug":False,
    },bindings_logical,image_uri_by_asset,audio_uri

def render_native(*,cycle,before,selection,plan,cards,observation,audio,
                  asset_root,baseline_movie,playdeck_root,output):
    repo=check_playdeck_checkout(playdeck_root)
    output=Path(output).expanduser().resolve()
    need(not output.exists(),"native output must be create-only")
    need(not output.with_suffix(".receipt.json").exists(),
         "native receipt path already exists")
    props,hashes,uri_map,audio_uri=convert_to_native_props(
        cycle,before,selection,plan,cards,observation,audio,asset_root,baseline_movie)
    package=repo/"packages"/"render-remotion"
    need((repo/"node_modules"/".bin"/"remotion").exists() and
         (package/"node_modules"/"@remotion").exists() or
         (repo/"node_modules"/"@remotion").exists(),
         "native Playdeck dependencies not installed; run npm install in pinned repo")
    media_dir=package/"public"
    media_dir.mkdir(parents=True,exist_ok=True)
    chosen_dir=media_dir/("band-iq-003-"+uuid4().hex)
    chosen_dir.mkdir(mode=0o700)
    output.parent.mkdir(parents=True,exist_ok=True)
    try:
        for aid,uri in uri_map.items():
            original=(Path(asset_root).resolve(strict=True)/cards["assets"][aid]["path"]).resolve(strict=True)
            need(donors.sha_file(original)==hashes[uri],"source changed before native staging")
            new=chosen_dir/(f"image-{len(props['assets']):03d}"+original.suffix.lower())
            shutil.copyfile(original,new)
            need(donors.sha_file(new)==hashes[uri],"native staged media changed")
            props["assets"][uri]=f"{chosen_dir.name}/{new.name}"
        original_audio=Path(audio).resolve(strict=True)
        suffix=original_audio.suffix.lower()
        need(suffix in {".wav",".mp3",".m4a",".aac",".ogg",".flac"},
             "unsupported native audio container")
        target_audio=chosen_dir/("source-audio"+suffix)
        shutil.copyfile(original_audio,target_audio)
        need(donors.sha_file(target_audio)==hashes[audio_uri],
             "native stage audio changed")
        props["assets"][audio_uri]=f"{chosen_dir.name}/{target_audio.name}"
        # Asset names are temporary stage paths, not semantic source identity.
        with tempfile.TemporaryDirectory(prefix="band-iq-003-props-") as tdir:
            props_file=Path(tdir)/"native.props.json"
            props_file.write_text(json.dumps(props,sort_keys=True),encoding="utf8")
            command=[
                str(repo/"node_modules"/".bin"/"remotion"),
                "render","src/index.ts","Playdeck",str(output),
                "--props",str(props_file),
                "--concurrency","1","--log","error",
            ]
            proc=subprocess.run(command,cwd=package,text=True,capture_output=True,timeout=300)
            need(proc.returncode==0 and output.exists(),
                 "native Playdeck render failed: "+proc.stderr[-700:])
        # A real Playdeck output must contain the full audio and video.
        probe=json.loads(subprocess.check_output([
             "ffprobe","-v","error","-show_entries",
             "format=duration:stream=codec_type,codec_name,width,height",
             "-of","json",str(output)],text=True))
        observed=float(probe["format"]["duration"])
        need(abs(observed-float(props["plan"]["duration"]))<.14,
             "native Remotion did not cover whole source song")
        types={x["codec_type"] for x in probe["streams"]}
        need("video" in types and "audio" in types,"native Remotion missing soundtrack or picture")
        native_sha=donors.sha_file(output)
        body={
             "schema":SCHEMA,"status":"native-playdeck-trial-only",
             "nativePlaydeckSourceSha":PLAYDECK_SHA,
             "nativeComponent":"@playdeck/render-remotion/PlaydeckComposition",
             "nativePlaydeckRendering":True,"nativePlaydeckKeep":False,
             "sourceCycleSha256":cycle["cycleSha256"],
             "sourceVideoSha256":before["sourceVideoSha256"],
             "selectedProposalSha256":selection["proposalSha256"],
             "selectionSha256":iq.digest(selection),
             "studio011Lens":next(x["lensId"] for x in cycle["imagine"]
                                 if x["proposalSha256"]==selection["proposalSha256"]),
             "targetStart":props["plan"]["metadata"]["bandIqNativeComparison"]["targetStart"],
             "targetEnd":props["plan"]["metadata"]["bandIqNativeComparison"]["targetEnd"],
             "nativeCompositionPropsSha256":iq.digest(props),
             "nativePlanSha256":iq.digest(props["plan"]),
             "inputAssetSha256":hashes,
             "actualOutputSha256":native_sha,
             "observedSeconds":round(observed,6),
             "nativeStreams":probe["streams"],
             "externalProviderSpend":0,"publicMediaUploaded":False,
             "automaticKeep":False,"published":False,
             "laws":["SAME CREATIVE QUESTION != SAME PIXELS",
                     "REMOTION COMPOSITION != VIDMAGE CAMERA",
                     "RENDERED != KEPT","DURATION VERIFIED != AESTHETIC APPROVAL",
                     "TEMPORARY STATIC MEDIA != GITHUB UPLOAD"],
        }
        receipt={**body,"receiptSha256":iq.digest(body)}
        path=output.with_suffix(".receipt.json")
        with path.open("x",encoding="utf8") as stream:
            json.dump(receipt,stream,indent=2,sort_keys=True)
        return receipt,str(path)
    except Exception:
        output.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(chosen_dir,ignore_errors=True)

def compare_native_pair(*,cycle,selection,vidmage_film_record,vidmage_movie,
                        playdeck_receipt,playdeck_movie,output_dir):
    iq.verify_cycle(cycle)
    proposal=[p for p in cycle["imagine"]
              if p["proposalSha256"]==selection["proposalSha256"]]
    need(len(proposal)==1,"unknown exact selected proposal")
    need(playdeck_receipt.get("schema")==SCHEMA and
         playdeck_receipt.get("receiptSha256")==
         iq.digest({k:v for k,v in playdeck_receipt.items() if k!="receiptSha256"}),
         "native Remotion receipt changed")
    need(playdeck_receipt["sourceCycleSha256"]==cycle["cycleSha256"] and
         playdeck_receipt["selectedProposalSha256"]==proposal[0]["proposalSha256"] and
         playdeck_receipt["selectionSha256"]==iq.digest(selection),
         "native Playdeck selection mismatch")
    need(playdeck_receipt["nativePlaydeckSourceSha"]==PLAYDECK_SHA and
         playdeck_receipt["nativePlaydeckRendering"] is True and
         playdeck_receipt["automaticKeep"] is False,
         "native renderer identity/authority false")
    need(playdeck_receipt["actualOutputSha256"]==donors.sha_file(playdeck_movie),
         "native output bytes changed")
    record=vidmage_film_record
    need(record.get("schema")==band.FILM_RECORD and
         record.get("filmRecordSha256")==
         iq.digest({k:v for k,v in record.items() if k!="filmRecordSha256"}),
         "VidMage performed-film record changed")
    need(record["sourceCycleSha256"]==cycle["cycleSha256"] and
         record["selectedProposalSha256"]==proposal[0]["proposalSha256"] and
         record["selectionSha256"]==iq.digest(selection) and
         record["performedVideoSha256"]==donors.sha_file(vidmage_movie),
         "VidMage output differs in source or selection")
    need(record["sourceVideoSha256"]==playdeck_receipt["sourceVideoSha256"] and
         record["actualAudioSha256"]==playdeck_receipt["inputAssetSha256"]["asset://band-iq-003/source-audio"],
         "not the same original audio or baseline")
    need(record["chosenLens"]==playdeck_receipt["studio011Lens"] and
         record["cameraMode"]==proposal[0]["cameraMode"] and
         abs(playdeck_receipt["targetStart"]-proposal[0]["targetStart"])<.001 and
         abs(playdeck_receipt["targetEnd"]-proposal[0]["targetEnd"])<.001,
         "native lens or time window mismatch")
    hashes=set(record["actualAssetSha256"].values())
    native_hashes={v for k,v in playdeck_receipt["inputAssetSha256"].items()
                   if k!="asset://band-iq-003/source-audio"}
    need(hashes==native_hashes,"different visual source material")
    need(record["performedVideoSha256"] != playdeck_receipt["actualOutputSha256"],
         "distinct renderer outputs must be kept separately")
    body={
         "schema":PAIR_SCHEMA,"status":"compared-authority-separated",
         "selectedProposalSha256":proposal[0]["proposalSha256"],
         "sourceCycleSha256":cycle["cycleSha256"],
         "selectionSha256":iq.digest(selection),
         "vidmageRenderer":"VIDMAGE OpenCV/FFmpeg selected-window camera",
         "playdeckRenderer":"native @playdeck/render-remotion",
         "vidmageFilmSha256":record["performedVideoSha256"],
         "playdeckFilmSha256":playdeck_receipt["actualOutputSha256"],
         "vidmageFilmReceiptSha256":record["filmRecordSha256"],
         "playdeckFilmReceiptSha256":playdeck_receipt["receiptSha256"],
         "sameSourceAudio":True,"sameSourceImageSet":True,
         "sameOperatorSelectedQuestion":True,
         "samePixelOutput":False,"aestheticallyEquivalent":None,
         "automaticallyKept":False,"published":False,
         "sourceAuthority":"owner-local",
         "laws":["SAME QUESTION != SAME ANSWER",
                 "TWO RENDERERS != TWO SOURCES",
                 "TECHNICAL COMPARISON != AESTHETIC SELECTION"],
    }
    result={**body,"comparisonSha256":iq.digest(body)}
    return result,iq.write_once(output_dir,result,"comparisonSha256")

def main():
    p=argparse.ArgumentParser(description="BAND-IQ 003 native Remotion witness and dual renderer comparison")
    sp=p.add_subparsers(dest="command",required=True)
    r=sp.add_parser("render-native")
    for name in ("cycle","before","selection","plan","cards","observation","audio","asset-root",
                 "baseline-movie","playdeck-root","output"):
        r.add_argument("--"+name,required=True)
    c=sp.add_parser("compare-pair")
    for name in ("cycle","selection","vidmage-record","vidmage-movie","playdeck-receipt",
                 "playdeck-movie","output-dir"):
        c.add_argument("--"+name,required=True)
    a=p.parse_args()
    if a.command=="render-native":
        _,path=render_native(cycle=read(a.cycle),before=read(a.before),
            selection=read(a.selection),plan=read(a.plan),cards=read(a.cards),
            observation=read(a.observation),audio=a.audio,asset_root=a.asset_root,
            baseline_movie=a.baseline_movie,playdeck_root=a.playdeck_root,output=a.output)
        print(json.dumps({"receipt":path,"authority":"trial-only"}))
    else:
        _,path=compare_native_pair(cycle=read(a.cycle),selection=read(a.selection),
            vidmage_film_record=read(a.vidmage_record),vidmage_movie=a.vidmage_movie,
            playdeck_receipt=read(a.playdeck_receipt),playdeck_movie=a.playdeck_movie,
            output_dir=a.output_dir)
        print(json.dumps({"comparison":path,"authority":"comparison-not-keep"}))

if __name__=="__main__":
    main()
