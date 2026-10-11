"""BAND-IQ 005: an author's next question is not an inferred edit instruction.

An independently reviewed 004 ANOTHER_EXPERIMENT decision enables three bounded
*possible* experiments. Only a second source-pinned creator selection executes
one local VidMage trial. The old review and both original films survive.
No semantic claim about the question, auto-KEEP, publication or remote provider.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from . import band_iq as iq
from . import band_iq_donors as donors
from . import band_iq_film_loop as loop
from . import band_iq_review as review
from . import scene_card_film as film

PROPOSALS="vidmage/band-iq-005-next-questions/v1"
AUTH="vidmage/band-iq-005-trial-authorization/v1"
REVISION="vidmage/band-iq-005-local-revision/v1"
OPS={
    "SWAP_CARD":"Ask what happens if one authored shot uses another already-authorized image.",
    "REFOCUS_CARD":"Ask what happens if one shot reframes its existing owned image.",
    "CHANGE_LENS":"Ask what happens if the previously selected window receives a different cinematic grammar.",
}

def need(ok,message):
    iq.require(ok,message)

def load(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def ensure_record(record, schema, field):
    need(isinstance(record,dict) and record.get("schema")==schema and
         iq.sha(record.get(field)) and
         iq.digest({k:v for k,v in record.items() if k!=field})==record[field],
         "immutable evidence identity failed for "+schema)
    return record

def verify_inputs(bench,plan,cards,observation,audio,asset_root):
    receipt=bench.get_decision()
    need(receipt is not None and receipt["decision"]=="ANOTHER_EXPERIMENT" and
         receipt["chosenRenderer"] is None and
         receipt["chosenFilmSha256"] is None and
         receipt["nextExperimentPerformed"] is False and
         receipt["automaticExecution"] is False and
         receipt["publicationAuthorized"] is False,
         "an actual human ANOTHER_EXPERIMENT review is required")
    ensure_record(receipt,review.SCHEMA,"reviewSha256")
    need(receipt["comparisonSha256"]==bench.pair["comparisonSha256"] and
         receipt["sourceCycleSha256"]==bench.cycle["cycleSha256"] and
         receipt["sourceSelectionSha256"]==iq.digest(bench.selection),
         "question review belongs to a different source crossing")
    iq.bounded(receipt.get("nextQuestion"),"author-written next question required",1200)
    for side in ("a","b"):
        bench.require_unchanged(side,cryptographic=True)
    need(iq.digest(plan)==bench.selection["paperPlanSha256"]==
         bench.vidmage_record["nativeBlenderPlanSha256"],
         "paper director plan differs from reviewed film")
    need(iq.digest(cards)==bench.selection["sceneCardsSha256"],
         "editor-authored cards differ from reviewed film")
    need(iq.digest(observation)==bench.selection["audioObservationSha256"] and
         observation["sourceAudioSha256"]==bench.selection["audioSha256"]==
         donors.sha_file(audio)==bench.vidmage_record["actualAudioSha256"],
         "original native Toaster audio input changed")
    iq.validate_audio(observation)
    need(bench.cycle["perceive"]["audioSha256"]==donors.sha_file(audio) and
         bench.cycle["sourceAudioObservationSha256"]==iq.digest(observation),
         "native original audio evidence does not match BAND-IQ cycle")
    film.validate(plan,cards,observation,asset_root)
    bound=loop.exact_asset_bindings(cards,asset_root)
    need(bound==bench.selection["assetBindings"]==
         bench.vidmage_record["actualAssetSha256"],
         "source material no longer matches the reviewed film")
    old=[p for p in bench.cycle["imagine"]
         if p["proposalSha256"]==bench.selection["proposalSha256"]]
    need(len(old)==1 and old[0]["status"]=="proposal-only" and
         old[0]["targetWindowId"] in bench.cycle["relate"]["unprotectedObservedWindowIds"],
         "review source no longer binds one authorized cinematic window")
    return receipt,bound,old[0]

def question_set(bench,plan,cards,observation,audio,asset_root):
    human,assets,previous=verify_inputs(bench,plan,cards,observation,audio,asset_root)
    shots=cards["shots"]
    source_ids=sorted(cards["assets"])
    editable_shots=[s["shotId"] for s in shots
                    if cards["assets"][s["assetId"]].get("mode","subject")!="protect-text"]
    interchangeable={
        row["shotId"]:[aid for aid in source_ids
            if assets[aid]!=assets[row["assetId"]]]
        for row in shots if row["shotId"] in editable_shots
    }
    swappable=sorted(k for k,v in interchangeable.items() if v)
    alternate_lenses=sorted(k for k in iq.LENSES if k!=previous["lensId"])
    items=[
        {"kind":"SWAP_CARD","status":"proposal-only" if swappable else "HOLD-no-other-authorized-image",
         "eligibleShotIds":swappable,"eligibleReplacementAssetIdsByShot":interchangeable,
         "eligibleLensIds":[],"description":OPS["SWAP_CARD"]},
        {"kind":"REFOCUS_CARD","status":"proposal-only" if editable_shots else "HOLD-all-source-text-protected",
         "eligibleShotIds":editable_shots,"eligibleReplacementAssetIdsByShot":{},
         "eligibleLensIds":[],"description":OPS["REFOCUS_CARD"]},
        {"kind":"CHANGE_LENS","status":"proposal-only" if alternate_lenses else "HOLD-no-alternate-lens",
         "eligibleShotIds":[],"eligibleReplacementAssetIdsByShot":{},
         "eligibleLensIds":alternate_lenses,
         "description":OPS["CHANGE_LENS"]},
    ]
    options=[{**p,"proposalSha256":iq.digest(p)} for p in items]
    record={
        "schema":PROPOSALS,
        "sourceReviewSha256":human["reviewSha256"],
        "sourceComparisonSha256":bench.pair["comparisonSha256"],
        "sourceCycleSha256":bench.cycle["cycleSha256"],
        "sourceSelectionSha256":iq.digest(bench.selection),
        "sourceVidmageSha256":bench.pair["vidmageFilmSha256"],
        "sourcePlaydeckSha256":bench.pair["playdeckFilmSha256"],
        "sourcePlanSha256":iq.digest(plan),
        "sourceCardsSha256":iq.digest(cards),
        "sourceAudioObservationSha256":iq.digest(observation),
        "sourceAudioSha256":donors.sha_file(audio),
        "sourceAssetSha256":assets,
        "humanQuestionVerbatim":human["nextQuestion"],
        "questionInterpretation":"NOT inferred; these are generic operator-chosen test categories",
        "priorCinematic":{
            "lensId":previous["lensId"],"cameraMode":previous["cameraMode"],
            "start":previous["targetStart"],"end":previous["targetEnd"],
            "sourceProposalSha256":previous["proposalSha256"],
        },
        "proposals":options,
        "status":"awaits-second-explicit-human-choice",
        "automaticExecution":False,"automaticKeep":False,
        "exportAuthorized":False,"publicationAuthorized":False,
        "laws":["QUESTION != COMMAND","THREE PROPOSALS != THREE TRIALS",
                "SOURCE OBSERVATION != CREATIVE AUTHORITY",
                "SCRAPE != ERASURE","REVIEW != RUN"],
    }
    return {**record,"questionSetSha256":iq.digest(record)}

def validate_authorization(q,choice,plan,cards):
    ensure_record(q,PROPOSALS,"questionSetSha256")
    need(isinstance(choice,dict) and set(choice)=={
         "schema","questionSetSha256","proposalSha256","operatorAttestationId",
         "decision","shotId","replacementAssetId","newFocus","newLensId",
         "allowLocalExecution","allowPaidProviders","allowNetworkUpload"},
         "next trial needs an exact typed author selection")
    need(choice["schema"]==AUTH and choice["decision"]=="RENDER_ONE_LOCAL_TRIAL" and
         choice["allowLocalExecution"] is True and
         choice["allowPaidProviders"] is False and
         choice["allowNetworkUpload"] is False,
         "explicit owner-local execution authorization required; no provider work")
    iq.bounded(choice["operatorAttestationId"],"second independent operator act required",256)
    need(choice["questionSetSha256"]==q["questionSetSha256"],
         "question set changed after creator saw it")
    matches=[p for p in q["proposals"]
             if p["proposalSha256"]==choice["proposalSha256"]]
    need(len(matches)==1 and matches[0]["status"]=="proposal-only",
         "chosen experiment is not a currently offered bounded proposal")
    selected=matches[0]
    shot=next((x for x in cards["shots"] if x["shotId"]==choice["shotId"]),None)
    if selected["kind"]=="SWAP_CARD":
        need(shot is not None and choice["shotId"] in selected["eligibleShotIds"],
             "source reassignment shot not authorized")
        need(choice["replacementAssetId"] in
             selected["eligibleReplacementAssetIdsByShot"][choice["shotId"]],
             "source replacement not independently authorized")
        need(choice["newFocus"] is None and choice["newLensId"] is None,
             "swap would change more than one independent variable")
    elif selected["kind"]=="REFOCUS_CARD":
        need(shot is not None and choice["shotId"] in selected["eligibleShotIds"],
             "focus edit is outside eligible authored shot")
        point=choice["newFocus"]
        need(isinstance(point,list) and len(point)==2 and
             all(iq.finite(v,.1,.9) for v in point),
             "focus must be an explicit bounded 2D point")
        old=cards["assets"][shot["assetId"]].get("focus",[.5,.5])
        need(point!=old and choice["replacementAssetId"] is None and
             choice["newLensId"] is None,
             "focus edit requires a genuinely new point and no second edit")
    else:
        need(choice["shotId"] is None and choice["replacementAssetId"] is None and
             choice["newFocus"] is None and
             choice["newLensId"] in selected["eligibleLensIds"],
             "lens change must select one distinct predeclared native camera grammar")
    return selected

def realize_cards(cards,selected,choice,q):
    revised=copy.deepcopy(cards)
    changed={}
    if selected["kind"]=="SWAP_CARD":
        for entry in revised["shots"]:
            if entry["shotId"]==choice["shotId"]:
                changed={"shotId":entry["shotId"],
                         "fromAssetId":entry["assetId"],
                         "toAssetId":choice["replacementAssetId"]}
                entry["assetId"]=choice["replacementAssetId"]
                break
    elif selected["kind"]=="REFOCUS_CARD":
        original=next(entry for entry in revised["shots"]
                      if entry["shotId"]==choice["shotId"])
        source_id=original["assetId"]
        new_id="band-iq-005-focus-"+iq.digest({
            "question":q["questionSetSha256"],
            "choice":choice["proposalSha256"],
            "shot":choice["shotId"],"focus":choice["newFocus"],
        })[:24]
        need(new_id not in revised["assets"],"new asset alias collides")
        revised["assets"][new_id]=copy.deepcopy(revised["assets"][source_id])
        revised["assets"][new_id]["focus"]=choice["newFocus"]
        original["assetId"]=new_id
        changed={"shotId":choice["shotId"],"fromAssetId":source_id,
                 "toAssetId":new_id,"sameOwnedBytes":True,
                 "newFocus":choice["newFocus"]}
    else:
        changed={"fromLensId":q["priorCinematic"]["lensId"],
                 "toLensId":choice["newLensId"],
                 "targetWindowUnchanged":True}
    return revised,changed

def run_trial(bench, q, choice,plan,cards,observation,audio,asset_root,output):
    current=question_set(bench,plan,cards,observation,audio,asset_root)
    need(q==current,"previous human question or source evidence changed")
    selected=validate_authorization(q,choice,plan,cards)
    # No implicit cinema interpretation of the author's natural-language question.
    edited,change=realize_cards(cards,selected,choice,q)
    previous=q["priorCinematic"]
    if selected["kind"]=="CHANGE_LENS":
        lens=choice["newLensId"]
        camera=iq.LENSES[lens][0]
    else:
        lens,camera=previous["lensId"],previous["cameraMode"]
    cinematic={
        "lensId":lens,"cameraMode":camera,
        "proposalSha256":selected["proposalSha256"],
        "cycleSha256":q["sourceCycleSha256"],
        "operatorAttestationId":choice["operatorAttestationId"],
        "targetStart":previous["start"],"targetEnd":previous["end"],
    }
    output=Path(output).expanduser().resolve()
    need(not output.exists() and not output.with_suffix(".receipt.json").exists(),
         "revision must not replace a prior movie or receipt")
    render=film.render(plan,edited,observation,audio,asset_root,output,
                       kinetic=False,cinematic=cinematic)
    actual=donors.sha_file(output)
    need(actual==render["outputSha256"] and
         render["audioSha256"]==q["sourceAudioSha256"] and
         render["humanKeep"] is False and render["published"] is False and
         render["providerCredits"]==0 and render["externalGenerations"]==0,
         "source-bound local trial could not be verified")
    original_unchanged=all(
        donors.sha_file(bench.videos[side])==q[
            "sourceVidmageSha256" if side=="a" else "sourcePlaydeckSha256"]
        for side in ("a","b"))
    need(original_unchanged,"old films mutated while performing next question")
    # Retain an explicit unselected trial even when media bytes happen to match.
    modified=(actual!=q["sourceVidmageSha256"])
    project={
        "schema":REVISION,
        "sourceReviewSha256":q["sourceReviewSha256"],
        "questionSetSha256":q["questionSetSha256"],
        "chosenProposalSha256":selected["proposalSha256"],
        "selectionSha256":iq.digest(choice),
        "operatorAttestationId":choice["operatorAttestationId"],
        "humanQuestionVerbatim":q["humanQuestionVerbatim"],
        "questionInterpretation":"none; experiment explicitly chosen",
        "experimentKind":selected["kind"],
        "changed":change,
        "oldCardsSha256":q["sourceCardsSha256"],
        "revisedCards":edited,
        "revisedCardsSha256":iq.digest(edited),
        "nativePaperPlanSha256":iq.digest(plan),
        "nativePaperPlan":copy.deepcopy(plan),
        "nativeToasterObservationSha256":iq.digest(observation),
        "nativeToasterObservation":copy.deepcopy(observation),
        "actualSourceAudioSha256":donors.sha_file(audio),
        "actualSourceAssetsSha256":loop.exact_asset_bindings(edited,asset_root),
        "originalVidmageMovieSha256":q["sourceVidmageSha256"],
        "originalPlaydeckMovieSha256":q["sourcePlaydeckSha256"],
        "newMovieSha256":actual,
        "newMediaDifferentFromPriorVidmage":modified,
        "nativeRenderReceiptSha256":iq.digest(render),
        "outputLocalPath":str(output),
        "sourceAssetRootLocalPath":str(Path(asset_root).expanduser().resolve(strict=True)),
        "sourceAudioLocalPath":str(Path(audio).expanduser().resolve(strict=True)),
        "status":"performed-local-trial-not-reviewed",
        "humanKeep":False,"publish":False,"exportAuthorized":False,
        "automaticChainedExperiment":False,
        "originalSourcesDeleted":False,
        "laws":["QUESTION != EXECUTION","RENDER_ONE != KEEP",
                "NEXT REVISION != ORIGINAL FILM",
                "NO DIFFERENT BYTES != REVISED CONTENT",
                "SOURCE CONTINUITY != AUTOMATIC EXPORT"],
    }
    sealed={**project,"revisionSha256":iq.digest(project)}
    path=iq.write_once(output.parent/"band-iq-005-revisions",sealed,"revisionSha256")
    return sealed,path

def reopen_revision(path):
    record=ensure_record(load(path),REVISION,"revisionSha256")
    movie=Path(record["outputLocalPath"]).resolve(strict=True)
    need(movie.is_file() and donors.sha_file(movie)==record["newMovieSha256"],
         "reopened movie source changed")
    root=Path(record["sourceAssetRootLocalPath"]).resolve(strict=True)
    need(loop.exact_asset_bindings(record["revisedCards"],root)==
         record["actualSourceAssetsSha256"],
         "reopened authored editable scene-card source changed")
    need(donors.sha_file(record["sourceAudioLocalPath"])==
         record["actualSourceAudioSha256"],
         "reopened audio source changed")
    need(record["revisedCardsSha256"]==iq.digest(record["revisedCards"]) and
         record["nativePaperPlanSha256"]==iq.digest(record["nativePaperPlan"]) and
         record["nativeToasterObservationSha256"]==iq.digest(record["nativeToasterObservation"]) and
         record["humanKeep"] is False and record["publish"] is False,
         "reopened revision cannot fabricate KEEP or publication")
    return {"schema":"vidmage/band-iq-005-reopen/v1",
            "status":"verified-editable-snapshot",
            "revisionSha256":record["revisionSha256"],
            "sourceReviewSha256":record["sourceReviewSha256"],
            "movieSha256":record["newMovieSha256"],
            "changed":record["changed"],
            "editorCards":record["revisedCards"],
            "paperPlan":record["nativePaperPlan"],
            "toasterObservation":record["nativeToasterObservation"],
            "nextAction":"separate human review, revise again, or export only with new authorization"}

def cli():
    p=argparse.ArgumentParser(description="BAND-IQ next human question -> possible edits -> chosen local trial")
    sub=p.add_subparsers(dest="command",required=True)
    for cmd in ("propose","render"):
        s=sub.add_parser(cmd)
        for name in ("cycle","selection","vidmage-record","vidmage-movie",
                     "playdeck-receipt","playdeck-movie","record-dir",
                     "plan","cards","observation","audio","asset-root"):
            s.add_argument("--"+name,required=True)
        s.add_argument("--output",required=True)
        if cmd=="render":
            s.add_argument("--question-set",required=True)
            s.add_argument("--authorization",required=True)
    r=sub.add_parser("reopen");r.add_argument("revision")
    a=p.parse_args()
    if a.command=="reopen":
        print(json.dumps(reopen_revision(a.revision),sort_keys=True));return
    bench=review.ReviewBench(cycle=a.cycle,selection=a.selection,
         vidmage_record=a.vidmage_record,vidmage_movie=a.vidmage_movie,
         playdeck_receipt=a.playdeck_receipt,playdeck_movie=a.playdeck_movie,
         record_dir=a.record_dir)
    args=[load(a.plan),load(a.cards),load(a.observation),a.audio,a.asset_root]
    if a.command=="propose":
        proposals=question_set(bench,*args)
        target=iq.write_once(a.output,proposals,"questionSetSha256")
        print(json.dumps({"questionSet":target,"proposals":len(proposals["proposals"]),
                          "status":"awaits-human-selection"}))
    else:
        record,path=run_trial(bench,load(a.question_set),load(a.authorization),
                              *args,a.output)
        print(json.dumps({"revision":path,"movie":str(a.output),
                          "changedMovieBytes":record["newMediaDifferentFromPriorVidmage"],
                          "status":record["status"]}))
if __name__=="__main__":
    cli()
