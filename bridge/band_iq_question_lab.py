"""BAND-IQ 006 — independent measurement of one human-chosen 005 revision.

Actual native Blender 008f scans BOTH complete MP4s using each movie's own
editorial source attribution. An independent raw-pixel sampler checks temporal
change. Every conclusion remains a bounded technical observation, not
interpretation of the creator's written question or permission for another run.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
import subprocess
from pathlib import Path

from . import band_iq as iq
from . import band_iq_donors as donors
from . import band_iq_film_loop as loop
from . import band_iq_next_question as nq
from . import band_iq_review as review

SCHEMA="vidmage/band-iq-006-question-observation/v1"
SCAN_FPS=4
PIXEL_WIDTH=64
PIXEL_HEIGHT=36
WINDOW_SECONDS=2.0
COMPONENTS=("stasis","sourceOveruse","recentRepetition","noveltyDeficit","transitionJolt")
NONSTILLNESS=("sourceOveruse","recentRepetition","noveltyDeficit","transitionJolt")
WEIGHTS={"sourceOveruse":.25,"recentRepetition":.20,"noveltyDeficit":.15,"transitionJolt":.10}

def need(ok,why):
    iq.require(ok,why)

def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def native_doctor(root):
    root=donors.pinned_blender(root)
    import haunted_blender
    import haunted_blender.weakest_window_doctor as doctor
    mod=Path(doctor.__file__).resolve(strict=True)
    need(mod.is_relative_to(root),
         "actual Blender Doctor import must originate at source-pinned checkout")
    return doctor

def unchanged_shots(baseline,revision,kind,changed):
    """Structural source edit evidence; no semantic object identification."""
    old=baseline["shots"];new=revision["shots"]
    need(len(old)==len(new),"revision silently altered shot count")
    left={x["shotId"]:x for x in old}
    right={x["shotId"]:x for x in new}
    need(len(left)==len(old) and left.keys()==right.keys(),
         "revision silently changed shot identities")
    modified=[k for k in left if left[k]!=right[k]]
    if kind in ("SWAP_CARD","REFOCUS_CARD"):
        need(modified==[changed["shotId"]],"one human selected shot must be the only changed occurrence")
        need(changed["shotId"] in left,"source changed shot absent")
        need(left[changed["shotId"]]["assetId"]==changed["fromAssetId"] and
             right[changed["shotId"]]["assetId"]==changed["toAssetId"],
             "authored source substitution does not match recorded change")
    else:
        need(kind=="CHANGE_LENS" and baseline==revision,
             "lens-only experiment must not mutate any authored scene card")
    return modified

def verify_sources(bench,record,plan,cards,observation,audio,asset_root):
    nq.ensure_record(record,nq.REVISION,"revisionSha256")
    question=nq.question_set(bench,plan,cards,observation,audio,asset_root)
    need(record["sourceReviewSha256"]==question["sourceReviewSha256"] and
         record["questionSetSha256"]==question["questionSetSha256"] and
         record["humanQuestionVerbatim"]==question["humanQuestionVerbatim"],
         "human question/review mismatch; refuse invented continuity")
    proposals=[p for p in question["proposals"]
               if p["proposalSha256"]==record["chosenProposalSha256"]]
    need(len(proposals)==1 and proposals[0]["kind"]==record["experimentKind"] and
         proposals[0]["status"]=="proposal-only",
         "a previously authorized experiment must be selected")
    need(record["originalVidmageMovieSha256"]==question["sourceVidmageSha256"] and
         record["originalPlaydeckMovieSha256"]==question["sourcePlaydeckSha256"] and
         record["oldCardsSha256"]==question["sourceCardsSha256"] and
         record["nativePaperPlanSha256"]==question["sourcePlanSha256"] and
         record["nativeToasterObservationSha256"]==question["sourceAudioObservationSha256"] and
         record["actualSourceAudioSha256"]==question["sourceAudioSha256"],
         "source pins from prior question do not match proposed revision")
    need(record["nativePaperPlan"]==plan and
         record["nativeToasterObservation"]==observation and
         record["revisedCardsSha256"]==iq.digest(record["revisedCards"]) and
         record["selectionSha256"]!=question["sourceSelectionSha256"],
         "revised editable snapshot or second operator selection invalid")
    need(record["humanKeep"] is False and record["publish"] is False and
         record["automaticChainedExperiment"] is False and
         record["status"]=="performed-local-trial-not-reviewed" and
         record["originalSourcesDeleted"] is False,
         "trial must not claim KEEP, publication, or prior source erasure")
    revised=record["revisedCards"]
    changed_ids=unchanged_shots(cards,revised,record["experimentKind"],record["changed"])
    actual_old=loop.exact_asset_bindings(cards,asset_root)
    actual_new=loop.exact_asset_bindings(revised,asset_root)
    need(actual_old==question["sourceAssetSha256"] and
         actual_new==record["actualSourceAssetsSha256"],
         "existing source artwork bytes changed")
    if record["experimentKind"]=="SWAP_CARD":
        row=record["changed"]
        need(row["toAssetId"] in proposals[0]["eligibleReplacementAssetIdsByShot"][row["shotId"]] and
             actual_old[row["fromAssetId"]]!=actual_old[row["toAssetId"]],
             "unapproved source swap cannot be observed")
    elif record["experimentKind"]=="REFOCUS_CARD":
        row=record["changed"]
        need(row["shotId"] in proposals[0]["eligibleShotIds"] and
             row["sameOwnedBytes"] is True and
             actual_new[row["toAssetId"]]==actual_old[row["fromAssetId"]] and
             revised["assets"][row["toAssetId"]]["focus"]==row["newFocus"] and
             {k:v for k,v in revised["assets"].items() if k!=row["toAssetId"]}==cards["assets"],
             "reframe must preserve original media and all other source cards")
    else:
        row=record["changed"]
        need(row["fromLensId"]==question["priorCinematic"]["lensId"] and
             row["toLensId"] in proposals[0]["eligibleLensIds"] and
             row["targetWindowUnchanged"] is True,
             "unapproved camera-language mutation")
    need(record["newMediaDifferentFromPriorVidmage"]==
         (record["newMovieSha256"]!=record["originalVidmageMovieSha256"]),
         "new movie identity claim contradicts actual hashes")
    film=Path(record["outputLocalPath"]).expanduser().resolve(strict=True)
    need(film.is_file() and donors.sha_file(film)==record["newMovieSha256"],
         "new full-length trial bytes absent or modified")
    original=bench.require_unchanged("a",cryptographic=True)
    bench.require_unchanged("b",cryptographic=True)
    need(donors.sha_file(original)==record["originalVidmageMovieSha256"] and
         donors.sha_file(audio)==record["actualSourceAudioSha256"],
         "movie/audio source no longer matches human review")
    render_receipt=film.with_suffix(".receipt.json")
    need(render_receipt.is_file() and iq.digest(read(render_receipt))==
         record["nativeRenderReceiptSha256"] and
         read(render_receipt)["outputSha256"]==record["newMovieSha256"],
         "actual performed film receipt changed")
    return question,original,film,changed_ids

def sampled_frames(video):
    # One deterministic independent external observation of actual picture bytes.
    proc=subprocess.run(["ffmpeg","-nostdin","-v","error","-i",str(video),
                         "-vf",f"fps={SCAN_FPS},scale={PIXEL_WIDTH}:{PIXEL_HEIGHT},format=gray",
                         "-f","rawvideo","-pix_fmt","gray","-"],
                        capture_output=True,check=True,timeout=150)
    stride=PIXEL_WIDTH*PIXEL_HEIGHT
    need(len(proc.stdout)>=stride and len(proc.stdout)%stride==0,
         "independent pixel witness not available")
    need(len(proc.stdout)//stride<=14400,"pixel sample exceeds bounded full-song window")
    return [proc.stdout[i:i+stride] for i in range(0,len(proc.stdout),stride)]

def compare_frames(original,revision,report):
    left=sampled_frames(original);right=sampled_frames(revision)
    need(abs(len(left)-len(right))<=1,
         "matched video frames required, cannot infer a pixel difference after lost coverage")
    rows=[]
    for item in report["windows"]:
        lo=min(len(left),max(0,int(round(item["start"]*SCAN_FPS))))
        hi=min(len(left),len(right),int(round(item["end"]*SCAN_FPS)))
        mae=[];changed=[]
        for i in range(lo,hi):
            amount=sum(abs(a-b) for a,b in zip(left[i],right[i]))/(PIXEL_WIDTH*PIXEL_HEIGHT*255)
            mae.append(amount)
            changed.append(amount>.02)
        need(mae,"each timing window requires real paired sampled frames")
        rows.append({"id":item["id"],"start":item["start"],"end":item["end"],
                     "pixelMeanAbsoluteDifference":round(sum(mae)/len(mae),6),
                     "changedFrameFractionAt2PctMAE":round(sum(changed)/len(changed),6),
                     "sampledPairs":len(mae)})
    return rows

def nonstillness(components):
    return round(sum(components[k]*WEIGHTS[k] for k in NONSTILLNESS),6)

def make_questions(operation,scope,observed):
    # IMPORTANT: questions describe possible inspections, not outputs.
    # No NLP interpretation of the author's words or score optimization.
    options=[
        {"id":"VIEW_CHANGED_WINDOWS","kind":"inspection-only",
         "question":"Which measured picture changes can the creator actually see in the changed windows?",
         "scope":scope,"requiresHumanChoice":True},
        {"id":"COMPARE_ORIGINAL_TRIAL","kind":"side-by-side-review-only",
         "question":"Which performance best expresses the author's own question when watched together?",
         "scope":scope,"requiresHumanChoice":True},
        {"id":"AUTHOR_ANOTHER_SINGLE_VARIABLE","kind":"new-authorization-needed",
         "question":"What ONE source, framing, or camera variable should the creator explicitly try next?",
         "scope":scope,"requiresHumanChoice":True},
    ]
    return [{**p,"proposalSha256":iq.digest(p),"execution":False,
             "keep":False,"publication":False} for p in options]

def observe(bench,revision,plan,cards,observation,audio,asset_root,blender_root,
            destination,*,window_seconds=WINDOW_SECONDS):
    q,original,film,affected=verify_sources(
        bench,revision,plan,cards,observation,audio,asset_root)
    need(iq.finite(window_seconds,1,10),"Doctor window seconds must be 1–10")
    doctor=native_doctor(blender_root)
    old_attribution=loop.doctor_scene_attribution_plan(plan,cards,asset_root)
    new_attribution=loop.doctor_scene_attribution_plan(plan,revision["revisedCards"],asset_root)
    original_report=doctor.scan(original,old_attribution,
                                window_seconds=window_seconds,sample_fps=SCAN_FPS)
    revised_report=doctor.scan(film,new_attribution,
                               window_seconds=window_seconds,sample_fps=SCAN_FPS)
    iq.validate_report(original_report)
    iq.validate_report(revised_report)
    need(original_report["sourceVideoSha256"]==q["sourceVidmageSha256"] and
         revised_report["sourceVideoSha256"]==revision["newMovieSha256"],
         "native Blender scanned the wrong actual movies")
    need(abs(original_report["targetSeconds"]-revised_report["targetSeconds"])<.03 and
         len(original_report["windows"])==len(revised_report["windows"]) and
         abs(original_report["coverageRatio"]-1)<1e-8 and
         abs(revised_report["coverageRatio"]-1)<1e-8,
         "independent native 008f scans did not cover the same full song")
    for l,r in zip(original_report["windows"],revised_report["windows"]):
        need(l["id"]==r["id"] and abs(l["start"]-r["start"])<.03 and
             abs(l["end"]-r["end"])<.03,
             "native Doctor changed the time windows")
    pixels=compare_frames(original,film,original_report)
    scoped_windows=[]
    if revision["experimentKind"] in ("SWAP_CARD","REFOCUS_CARD"):
        affected_shot=revision["changed"]["shotId"]
        matching=[x for x in plan["shots"] if x["id"]==affected_shot]
        need(len(matching)==1,"edited shot time not present")
        scope=(matching[0]["start"],matching[0]["end"])
    else:
        scope=(q["priorCinematic"]["start"],q["priorCinematic"]["end"])
    timeline=[]
    for before,after,frame in zip(original_report["windows"],
                                   revised_report["windows"],pixels):
        overlap=max(0,min(before["end"],scope[1])-max(before["start"],scope[0]))
        core_before=nonstillness(before["components"])
        core_after=nonstillness(after["components"])
        row={
            **frame,
            "operatorEditOverlapsThisWindow":overlap>0,
            "operatorEditOverlapSeconds":round(overlap,6),
            "nativeDoctor":{
                "sourceIdsBefore":[{"assetId":x["sourceAssetId"],"sha256":x["sourceSha256"]}
                                   for x in before["sources"]],
                "sourceIdsAfter":[{"assetId":x["sourceAssetId"],"sha256":x["sourceSha256"]}
                                   for x in after["sources"]],
                "nonStillnessBefore":core_before,"nonStillnessAfter":core_after,
                "nonStillnessDelta":round(core_after-core_before,6),
                "motionEnergyBefore":before["motionEnergy"],
                "motionEnergyAfter":after["motionEnergy"],
                "stasisBefore":before["components"]["stasis"],
                "stasisAfter":after["components"]["stasis"],
                "technicalScoreBefore":before["weaknessScore"],
                "technicalScoreAfter":after["weaknessScore"],
                "componentsBefore":{k:before["components"][k] for k in NONSTILLNESS},
                "componentsAfter":{k:after["components"][k] for k in NONSTILLNESS},
            },
        }
        timeline.append(row)
        if row["operatorEditOverlapsThisWindow"]:
            scoped_windows.append(row["id"])
    need(len(scoped_windows)>0,"operator edit should overlap a real inspected time window")
    full_score=sum(x["pixelMeanAbsoluteDifference"]*x["sampledPairs"] for x in pixels) / sum(x["sampledPairs"] for x in pixels)
    body={
        "schema":SCHEMA,
        "status":"observed-local-not-reviewed",
        "blenderNativeSourceSha256":donors.BLENDER_SHA,
        "realNativeDoctor":True,
        "native008eExecution":False,
        "native008eShapeSourceAttribution":"explicit VidMage scene-card adapter",
        "actualOldFilmSha256":q["sourceVidmageSha256"],
        "actualNewFilmSha256":revision["newMovieSha256"],
        "playdeckEarlierFilmSha256":q["sourcePlaydeckSha256"],
        "sourceReviewSha256":q["sourceReviewSha256"],
        "sourceQuestionSetSha256":q["questionSetSha256"],
        "sourceRevisionSha256":revision["revisionSha256"],
        "humanQuestionVerbatim":q["humanQuestionVerbatim"],
        "questionInterpretation":"not inferred",
        "humanChosenOperation":revision["experimentKind"],
        "humanChosenEdit":revision["changed"],
        "sourcePaperPlanSha256":iq.digest(plan),
        "originalSceneCardsSha256":iq.digest(cards),
        "revisedSceneCardsSha256":iq.digest(revision["revisedCards"]),
        "nativeToasterObservationSha256":iq.digest(observation),
        "audioSha256":q["sourceAudioSha256"],
        "originalAttributionPlanSha256":iq.digest(old_attribution),
        "revisedAttributionPlanSha256":iq.digest(new_attribution),
        "nativeDoctorOriginalReportSha256":iq.digest(original_report),
        "nativeDoctorRevisionReportSha256":iq.digest(revised_report),
        "nativeDoctorCoverageOriginal":original_report["coverageRatio"],
        "nativeDoctorCoverageRevision":revised_report["coverageRatio"],
        "sampling":{"framesPerSecond":SCAN_FPS,"frameWidth":PIXEL_WIDTH,
                    "frameHeight":PIXEL_HEIGHT,"windowSeconds":window_seconds,
                    "changeThresholdMAE":.02,
                    "pixelMAEAcrossSong":round(full_score,6)},
        "selectedOperatorChangeTime":{"start":scope[0],"end":scope[1],
                                       "affectedShotIds":affected,
                                       "overlappingDoctorWindowIds":scoped_windows},
        "windows":timeline,
        "possibleNextQuestions":make_questions(revision["experimentKind"],scoped_windows,timeline),
        "technicalConclusion":"measured frame/source differences only",
        "artisticJudgment":None,
        "automaticKeep":False,"automaticExecution":False,
        "newExperimentAuthorized":False,"published":False,
        "laws":["MEASURED CHANGE != INTENDED EFFECT",
                "PIXEL DELTA != AESTHETIC IMPROVEMENT",
                "STILLNESS != WEAKNESS","NONSTILLNESS METRIC != ARTIST SELECTION",
                "WRITTEN QUESTION != MACHINE INSTRUCTION",
                "ONE HUMAN CHOSEN EDIT != AUTOMATIC NEXT EDIT",
                "NATIVE DOCTOR REPORT != NATIVE 008E FILM MILL RENDER"],
    }
    result={**body,"observationSha256":iq.digest(body)}
    path=iq.write_once(destination,result,"observationSha256")
    return result,path

def reopen(path,previous,revision,bench):
    record=nq.ensure_record(read(path),SCHEMA,"observationSha256")
    nq.ensure_record(revision,nq.REVISION,"revisionSha256")
    need(record["sourceRevisionSha256"]==revision["revisionSha256"] and
         record["sourceReviewSha256"]==bench.get_decision()["reviewSha256"] and
         record["actualOldFilmSha256"]==donors.sha_file(bench.videos["a"]) and
         record["actualNewFilmSha256"]==donors.sha_file(revision["outputLocalPath"]),
         "reopened source film or linked question changed")
    need(record["artisticJudgment"] is None and record["automaticKeep"] is False and
         record["automaticExecution"] is False and record["published"] is False,
         "reopened observation claims forbidden artistic authority")
    return {"schema":"vidmage/band-iq-006-question-reopen/v1",
            "status":"verified-observation-not-authority",
            "question":record["humanQuestionVerbatim"],
            "observationSha256":record["observationSha256"],
            "windows":record["windows"],
            "possibleNextQuestions":record["possibleNextQuestions"]}

def cli():
    p=argparse.ArgumentParser(description="BAND-IQ 006: observe ONE already human-selected local video change")
    for field in ("cycle","selection","vidmage-record","vidmage-movie",
                  "playdeck-receipt","playdeck-movie","record-dir",
                  "plan","cards","observation","audio","asset-root",
                  "revision","blender-root","output-dir"):
        p.add_argument("--"+field,required=True)
    a=p.parse_args()
    bench=review.ReviewBench(cycle=a.cycle,selection=a.selection,
         vidmage_record=a.vidmage_record,vidmage_movie=a.vidmage_movie,
         playdeck_receipt=a.playdeck_receipt,playdeck_movie=a.playdeck_movie,
         record_dir=a.record_dir)
    _,path=observe(bench,read(a.revision),read(a.plan),read(a.cards),read(a.observation),
                   a.audio,a.asset_root,a.blender_root,a.output_dir)
    print(json.dumps({"observation":path,"status":"read-only-question-measurement",
                      "authority":"no-KEEP-no-execution"}))
if __name__=="__main__":
    cli()
