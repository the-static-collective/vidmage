"""BAND-IQ 002 — explicitly selected lens -> actual local movie -> native Doctor comparison.

The six Playdeck Studio 011-derived camera grammars are executed as bounded
VIDMAGE OpenCV transforms, NOT as native Playdeck/Remotion code. Existing
Blender Paper Director plans, actual Toaster observations, author scene cards,
authorized source bytes and any Blender 008h -> 008l ancestry remain separate.
No automatic KEEP, provider work, publication, or external upload.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

from . import band_iq as iq
from . import band_iq_donors as donors
from . import scene_card_film as film

SELECTION="vidmage/band-iq-selected-film/v1"
LINEAGE="vidmage/band-iq-harvest-material-lineage/v1"
FILM_RECORD="vidmage/band-iq-performed-film/v1"
REVIEW_RECORD="vidmage/band-iq-film-compare/v1"

def need(ok, why):
    iq.require(ok, why)

def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def exact_asset_bindings(cards, asset_root):
    root=Path(asset_root).resolve(strict=True)
    rows={}
    for key, record in cards["assets"].items():
        need(isinstance(key,str) and 0<len(key)<=256,"invalid asset id")
        need(isinstance(record,dict) and isinstance(record.get("path"),str),
             "asset path required")
        actual=(root/record["path"]).resolve(strict=True)
        need(actual.is_relative_to(root) and actual.is_file(),"asset escaped authorized directory")
        rows[key]=donors.sha_file(actual)
    return rows

def check_lineage(lineage, actual_bindings):
    if lineage is None:
        return None
    need(isinstance(lineage,dict) and set(lineage)==
         {"schema","harvest","materialization","boundAssetId","selectedHarvestArtifactSha256"},
         "invalid native lineage envelope")
    need(lineage["schema"]==LINEAGE,"unknown lineage schema")
    harvest=lineage["harvest"]
    mat=lineage["materialization"]
    require_hash=lambda row,prefix: need(
        isinstance(row,dict) and isinstance(row.get("id"),str) and
        row["id"]==prefix+iq.digest({k:v for k,v in row.items() if k!="id"})[:24],
        "native donor identity mismatch")
    require_hash(harvest,"parts-harvest:")
    require_hash(mat,"materialized-asset:")
    need(harvest.get("schema")=="haunted-blender/parts-harvest/v1",
         "native 008h manifest required")
    need(mat.get("schema")=="haunted-blender/materialized-asset/v1",
         "native 008l receipt required")
    source=harvest.get("source") or {}
    need(iq.sha(source.get("sha256")) and
         donors.sha_file(Path(source["path"]).resolve(strict=True))==source["sha256"],
         "original owned video changed")
    sha=lineage["selectedHarvestArtifactSha256"]
    matches=[item for item in harvest.get("artifacts",[])
             if item.get("sha256")==sha and item.get("kind")=="still"]
    need(len(matches)==1,"a single exact native harvested still required")
    art=matches[0]
    need(art["sourceSha256"]==source["sha256"] and
         donors.sha_file(Path(art["path"]).resolve(strict=True))==sha,
         "harvested still bytes or ancestry changed")
    aid=lineage["boundAssetId"]
    need(aid in actual_bindings and mat.get("sourceSha256")==sha and
         donors.sha_file(Path(mat["sourcePath"]).resolve(strict=True))==sha and
         mat.get("outputSha256")==actual_bindings[aid] and
         donors.sha_file(Path(mat["outputPath"]).resolve(strict=True))==actual_bindings[aid],
         "materialization is not the bound selected image")
    need(mat.get("cost",{}).get("providerCredits")==0 and
         mat.get("cost",{}).get("usdMicros")==0,
         "local material donor claims paid effects")
    return {"harvestId":harvest["id"],"harvestSourceSha256":source["sha256"],
            "harvestedStillSha256":sha,"materializationId":mat["id"],
            "materialOutputSha256":mat["outputSha256"],"boundAssetId":aid,
            "harvestManifestSha256":iq.digest(harvest),
            "materialReceiptSha256":iq.digest(mat)}

def doctor_scene_attribution_plan(paper_plan, cards, asset_root):
    """Exact scene-card attribution for native 008f, NOT a native 008e plan claim.

    008f accepts the 008e plan *shape*. Its native implementation reads
    source-hash/time spans and the plan identity. This explicit adapter
    constructs those spans from the actual VidMage card-to-shot performance.
    It never claims 008e manufactured the movie.
    """
    need(paper_plan.get("schema")=="haunted-blender/paper-director-plan/v1",
         "native Paper Director plan required")
    bindings=exact_asset_bindings(cards,asset_root)
    shots=paper_plan.get("shots") or []
    need(1<=len(shots)<=256 and
         len(shots)==len(cards.get("shots") or []),"all scene cards must be addressable")
    cursor=0.
    slugs=[]
    for index,(shot,choice) in enumerate(zip(shots,cards["shots"])):
        start,end=shot.get("start"),shot.get("end")
        need(iq.finite(start,0) and iq.finite(end,0) and
             abs(start-cursor)<.02 and end>start,
             "source attribution must have contiguous shot windows")
        need(choice.get("shotId")==shot.get("id") and
             choice.get("assetId") in bindings,
             "source attribution lost exact authored shot binding")
        aid=choice["assetId"]
        slugs.append({"id":"vidmage-card-%04d"%(index+1),
                      "index":index+1,"durationSeconds":round(end-start,6),
                      "sourceAssetId":aid,
                      "sourceSha256":bindings[aid],
                      "recipe":"fit"})
        cursor=end
    need(abs(cursor-paper_plan.get("durationSeconds",0))<.02,
         "source attribution duration mismatches film")
    body={
        "schema":"haunted-blender/zero-dollar-film-plan/v1",
        "targetSeconds":round(cursor,6),
        "slugs":slugs,
        "vidmageAdapter":{
            "schema":"vidmage/band-iq-scene-attribution/v1",
            "nativeBlender008eExecution":False,
            "sourceClaim":"source-image SHA and editor-chosen time intervals only",
            "nativePaperPlanSha256":iq.digest(paper_plan),
            "sceneCardsSha256":iq.digest(cards),
            "assetSha256":bindings,
        },
    }
    return {**body,"id":"band-iq-scene-plan:"+iq.digest(body)[:24]}


def validate_selection(cycle, before, selection, plan, cards, observation,
                       audio, asset_root, base_movie, lineage=None):
    iq.verify_cycle(cycle)
    iq.validate_report(before)
    need(iq.digest(before)==cycle["sourceDoctorReportSha256"],
         "cycle does not bind actual source Doctor report")
    need(donors.sha_file(base_movie)==before["sourceVideoSha256"]==
         cycle["sourceVideoSha256"],"baseline actual movie identity changed")
    need(isinstance(selection,dict) and set(selection)=={
         "schema","cycleSha256","proposalSha256","operatorAttestationId",
         "decision","allowLocalExecution","allowPaidProviders","allowNetworkUpload",
         "sourceVideoSha256","paperPlanSha256","sceneCardsSha256",
         "audioObservationSha256","audioSha256","assetBindings"},
         "exact film selection structure required")
    need(selection["schema"]==SELECTION and selection["decision"]=="RENDER_TRIAL",
         "only explicitly selected local trial is allowed")
    need(selection["allowLocalExecution"] is True and
         selection["allowPaidProviders"] is False and
         selection["allowNetworkUpload"] is False,"no implicit cost or uploading authority")
    iq.bounded(selection["operatorAttestationId"],"explicit operator choice required")
    need(selection["cycleSha256"]==cycle["cycleSha256"] and
         selection["sourceVideoSha256"]==before["sourceVideoSha256"],
         "choice crossed the source identity boundary")
    selected=[p for p in cycle["imagine"]
              if p["proposalSha256"]==selection["proposalSha256"]]
    need(len(selected)==1,"exactly one existing cinematic proposal must be selected")
    proposal=selected[0]
    need(proposal["status"]=="proposal-only" and
         proposal["targetWindowId"] in cycle["relate"]["unprotectedObservedWindowIds"],
         "selected trial targets an unapproved or deliberately protected scene")
    need(proposal["cameraMode"] in film.CAMERAS,
         "selected Playdeck-derived camera lacks local renderer")
    need(isinstance(plan,dict) and plan.get("schema")=="haunted-blender/paper-director-plan/v1" and
         iq.finite(plan.get("durationSeconds"),.2,3600) and
         abs(plan["durationSeconds"]-before["targetSeconds"])<=.10,
         "real native Blender paper plan must preserve the song duration")
    need(selection["paperPlanSha256"]==iq.digest(plan) and
         selection["sceneCardsSha256"]==iq.digest(cards),
         "native plan or editor-authored scene cards changed")
    need(isinstance(observation,dict) and observation.get("schema")==
         "vidmage/toaster-lbranch-observation/v1" and
         selection["audioObservationSha256"]==iq.digest(observation),
         "missing actual versioned Toaster observation binding")
    iq.validate_audio(observation)
    need(selection["audioSha256"]==donors.sha_file(audio) and
         observation["sourceAudioSha256"]==selection["audioSha256"] and
         cycle["perceive"]["audioSha256"]==selection["audioSha256"],
         "observed audio, playable audio, and selected source differ")
    film.validate(plan,cards,observation,asset_root)
    asset_bindings=exact_asset_bindings(cards,asset_root)
    need(selection["assetBindings"]==asset_bindings,
         "editorial material source bytes changed")
    verified_lineage=check_lineage(lineage,asset_bindings)
    return proposal,asset_bindings,verified_lineage

def render_selected(cycle,before,selection,plan,cards,observation,audio,
                    asset_root,base_movie,output,*,lineage=None):
    proposal,bindings,provenance=validate_selection(
        cycle,before,selection,plan,cards,observation,audio,asset_root,base_movie,lineage)
    output=Path(output).resolve()
    need(not output.exists() and not output.with_suffix(".receipt.json").exists(),
         "create-only film output already exists")
    chosen={k:proposal[k] for k in ("lensId","cameraMode","proposalSha256")}
    chosen.update({"cycleSha256":cycle["cycleSha256"],
                   "operatorAttestationId":selection["operatorAttestationId"]})
    film_receipt=film.render(plan,cards,observation,audio,asset_root,output,kinetic=False,
                             cinematic=chosen)
    need(film_receipt["outputSha256"]==donors.sha_file(output) and
         film_receipt["cinematicSelection"]==chosen and
         film_receipt["humanKeep"] is False and
         film_receipt["providerCredits"]==0 and
         film_receipt["published"] is False,
         "selected film trial did not preserve custody")
    body={"schema":FILM_RECORD,
          "sourceCycleSha256":cycle["cycleSha256"],
          "sourceDoctorSha256":iq.digest(before),
          "sourceVideoSha256":before["sourceVideoSha256"],
          "performedVideoSha256":film_receipt["outputSha256"],
          "selectedProposalSha256":proposal["proposalSha256"],
          "chosenLens":proposal["lensId"],"cameraMode":proposal["cameraMode"],
          "selectionSha256":iq.digest(selection),
          "artistAttestationId":selection["operatorAttestationId"],
          "nativeBlenderPlanSha256":iq.digest(plan),
          "actualAudioSha256":selection["audioSha256"],
          "actualAssetSha256":bindings,
          "nativeHarvestMaterialLineage":provenance,
          "filmReceiptSha256":iq.digest(film_receipt),
          "executedWith":"native VIDMAGE scene_card_film OpenCV/FFmpeg",
          "playdeckDirectExecution":False,
          "doctorRescorePerformed":False,
          "technicalImprovementClaim":False,
          "humanKeep":False,"published":False,
          "laws":["SIX PROPOSALS != SIX PERFORMANCES",
                  "HUMAN RENDER SELECTION != KEEP",
                  "CAMERA MOTION != SOURCE MOTION",
                  "FILM RECEIPT != DOCTOR COMPARISON",
                  "NATIVE VIDMAGE CAMERA != NATIVE PLAYDECK RENDER"]}
    record={**body,"filmRecordSha256":iq.digest(body)}
    witness=iq.write_once(output.parent/"band-iq-film-evidence",record,"filmRecordSha256")
    return record,witness

def compare_selected(cycle,before,after,film_record,film_receipt,
                     performed_movie,output_dir,human_review=None):
    iq.verify_cycle(cycle)
    need(isinstance(film_record,dict) and film_record.get("schema")==FILM_RECORD and
         film_record.get("filmRecordSha256")==
         iq.digest({k:v for k,v in film_record.items() if k!="filmRecordSha256"}),
         "performed film record changed")
    need(film_record["sourceCycleSha256"]==cycle["cycleSha256"] and
         film_record["sourceDoctorSha256"]==iq.digest(before),
         "film is not this original observation")
    need(film_record["performedVideoSha256"]==donors.sha_file(performed_movie) and
         film_receipt.get("outputSha256")==film_record["performedVideoSha256"] and
         iq.digest(film_receipt)==film_record["filmReceiptSha256"] and
         film_receipt.get("humanKeep") is False,
         "performed media/receipt source mismatch")
    iq.validate_report(after)
    need(after["sourceVideoSha256"]==film_record["performedVideoSha256"],
         "trial Doctor report was not made from exact performed film")
    trial=iq.compare_trial(cycle,before,after,human_review)
    body={"schema":REVIEW_RECORD,"performedFilmRecordSha256":film_record["filmRecordSha256"],
          "baseVideoSha256":film_record["sourceVideoSha256"],
          "trialVideoSha256":film_record["performedVideoSha256"],
          "doctorComparison":trial,
          "automaticKeep":False,
          "sourceContinuity":"verified-with-native-008f-media-hashes",
          "laws":["DOCTOR REPORT != HUMAN APPROVAL","COMPARISON != PUBLICATION",
                  "SILENCE != ERROR","NUMERIC DELTA != ARTISTIC IMPROVEMENT"]}
    record={**body,"reviewSha256":iq.digest(body)}
    path=iq.write_once(output_dir,record,"reviewSha256")
    return record,path

def cli():
    p=argparse.ArgumentParser(description="BAND-IQ selected film and reviewed trial")
    sub=p.add_subparsers(dest="command",required=True)
    d=sub.add_parser("doctor-plan")
    for key in ("paper-plan","cards","asset-root","output"):
        d.add_argument("--"+key,required=True)
    r=sub.add_parser("render")
    for key in ("cycle","before","selection","plan","cards","observation","audio","asset-root","base-movie","output"):
        r.add_argument("--"+key,required=True)
    r.add_argument("--lineage")
    c=sub.add_parser("compare")
    for key in ("cycle","before","after","film-record","film-receipt","performed-movie","output-dir"):
        c.add_argument("--"+key,required=True)
    c.add_argument("--human-review")
    a=p.parse_args()
    if a.command=="doctor-plan":
        record=doctor_scene_attribution_plan(read(a.paper_plan),read(a.cards),a.asset_root)
        target=Path(a.output)
        need(not target.exists(),"attribution plan output is create-only")
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("x",encoding="utf8") as output:
            json.dump(record,output,indent=2,sort_keys=True)
        print(json.dumps({"output":str(target),"attributionPlanId":record["id"],
                          "nativeBlender008eExecution":False}))
    elif a.command=="render":
        _,file=render_selected(read(a.cycle),read(a.before),read(a.selection),
                   read(a.plan),read(a.cards),read(a.observation),a.audio,
                   a.asset_root,a.base_movie,a.output,
                   lineage=read(a.lineage) if a.lineage else None)
        print(json.dumps({"filmRecord":file,"output":a.output,"status":"trial-only"}))
    else:
        _,file=compare_selected(read(a.cycle),read(a.before),read(a.after),
                    read(a.film_record),read(a.film_receipt),a.performed_movie,
                    a.output_dir,
                    human_review=read(a.human_review) if a.human_review else None)
        print(json.dumps({"comparison":file,"status":"measurement-not-keep"}))

if __name__=="__main__":
    cli()
