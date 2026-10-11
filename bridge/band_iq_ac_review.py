"""BAND-IQ 007: independent, source-witnessed HUMAN A/C revision review.

A is the earlier VidMage film; C is an explicitly selected 005 revision.
006 observations remain measurements, not a chooser. A second human signature
selects local continuation (or neither) in a create-only receipt. No KEEP on
Playdeck, provider work, export, deletion, publication, or editing occurs here.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from . import band_iq as iq
from . import band_iq_donors as donors
from . import band_iq_next_question as nextq
from . import band_iq_question_lab as lab
from . import band_iq_review as first_review

SCHEMA="vidmage/band-iq-007-human-ac-review/v1"
PAIR="vidmage/band-iq-007-original-revision-pair/v1"
DECISIONS={
    "CONTINUE_ORIGINAL":"original-selected-for-local-continuation",
    "CONTINUE_REVISION":"revision-selected-for-local-continuation",
    "DECLINE_BOTH":"no-trial-selected-preserve-history",
    "ASK_ANOTHER_QUESTION":"new-human-question-only",
}

def need(ok, message):
    iq.require(ok,message)

def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def validate_choice(body):
    need(isinstance(body,dict) and set(body)=={
        "decision","operatorAttestationId","rationale",
        "nextQuestion","acknowledgedLocalOnly"},
        "explicit new A/C review requires an exact choice form")
    decision=body["decision"]
    need(decision in DECISIONS,"unknown A/C review decision")
    iq.bounded(body["operatorAttestationId"],"new human reviewer attestation required",256)
    need(isinstance(body["rationale"],str) and len(body["rationale"])<=2000,
         "review observation must be bounded author text")
    need(body["acknowledgedLocalOnly"] is True,
         "separate choice must acknowledge that no media is published, exported or overwritten")
    need(isinstance(body["nextQuestion"],str) and len(body["nextQuestion"])<=1200,
         "next question must be bounded")
    if decision=="ASK_ANOTHER_QUESTION":
        iq.bounded(body["nextQuestion"],"author must actually write a new question",1200)
    else:
        need(not body["nextQuestion"].strip(),
             "no automatic follow-up question without an explicit question choice")
    return body

def verify_observation(observation,revision,bench):
    nextq.ensure_record(observation,lab.SCHEMA,"observationSha256")
    need(observation["status"]=="observed-local-not-reviewed" and
         observation["sourceReviewSha256"]==bench.get_decision()["reviewSha256"] and
         observation["sourceRevisionSha256"]==revision["revisionSha256"] and
         observation["sourceQuestionSetSha256"]==revision["questionSetSha256"] and
         observation["humanQuestionVerbatim"]==revision["humanQuestionVerbatim"],
         "006 observation does not belong to exactly this creator question and revision")
    need(observation["actualOldFilmSha256"]==bench.pair["vidmageFilmSha256"] and
         observation["actualNewFilmSha256"]==revision["newMovieSha256"] and
         observation["playdeckEarlierFilmSha256"]==bench.pair["playdeckFilmSha256"] and
         observation["sourcePaperPlanSha256"]==revision["nativePaperPlanSha256"] and
         observation["nativeToasterObservationSha256"]==revision["nativeToasterObservationSha256"] and
         observation["audioSha256"]==revision["actualSourceAudioSha256"] and
         observation["revisedSceneCardsSha256"]==revision["revisedCardsSha256"] and
         observation["originalSceneCardsSha256"]==revision["oldCardsSha256"],
         "006 film/plan/cards/audio source evidence changed")
    need(observation["humanChosenOperation"]==revision["experimentKind"] and
         observation["humanChosenEdit"]==revision["changed"] and
         observation["realNativeDoctor"] is True and
         observation["native008eExecution"] is False and
         observation["automaticKeep"] is False and
         observation["automaticExecution"] is False and
         observation["newExperimentAuthorized"] is False and
         observation["published"] is False and
         observation["artisticJudgment"] is None and
         observation["questionInterpretation"]=="not inferred",
         "006 factual observation cannot claim author preference or downstream execution")
    need(observation["nativeDoctorCoverageOriginal"]>=.999999 and
         observation["nativeDoctorCoverageRevision"]>=.999999,
         "006 proof needs full-song native movie coverage")
    sampling=observation["sampling"]
    need(sampling["framesPerSecond"]==4 and
         sampling["frameWidth"]==64 and sampling["frameHeight"]==36 and
         iq.finite(sampling["pixelMAEAcrossSong"],0,1) and
         sampling["changeThresholdMAE"]==.02,
         "006 pixel measurements do not satisfy witnessed sampling contract")
    windows=observation["windows"]
    need(isinstance(windows,list) and 1<=len(windows)<=10000,
         "A/C review must include actual time-window evidence")
    cursor=0.
    total=0
    total_delta=0.
    actual_changed=[]
    edit_scope=observation["selectedOperatorChangeTime"]
    need(iq.finite(edit_scope["start"],0) and
         iq.finite(edit_scope["end"],edit_scope["start"]) and
         edit_scope["end"]>edit_scope["start"],
         "edited time scope invalid")
    for item in windows:
        need(isinstance(item,dict) and isinstance(item["id"],str) and
             iq.finite(item["start"],0) and iq.finite(item["end"],0) and
             item["end"]>item["start"] and abs(item["start"]-cursor)<.03 and
             iq.finite(item["pixelMeanAbsoluteDifference"],0,1) and
             iq.finite(item["changedFrameFractionAt2PctMAE"],0,1) and
             type(item["sampledPairs"])==int and item["sampledPairs"]>0,
             "006 window samples are invalid or noncontiguous")
        expected=max(0.,min(item["end"],edit_scope["end"])-
                        max(item["start"],edit_scope["start"]))
        need(item["operatorEditOverlapsThisWindow"]==(expected>0) and
             abs(item["operatorEditOverlapSeconds"]-expected)<.002,
             "006 report changed creator's selected time overlap")
        if expected>0:actual_changed.append(item["id"])
        need(iq.finite(item["nativeDoctor"]["nonStillnessDelta"],-1,1),
             "006 native Doctor delta invalid")
        total+=item["sampledPairs"]
        total_delta+=item["sampledPairs"]*item["pixelMeanAbsoluteDifference"]
        cursor=item["end"]
    need(actual_changed==edit_scope["overlappingDoctorWindowIds"] and
         len(actual_changed)>0 and
         abs(total_delta/total-sampling["pixelMAEAcrossSong"])<2e-6,
         "006 actual time windows/pixel totals do not agree")
    need(isinstance(observation["possibleNextQuestions"],list) and
         len(observation["possibleNextQuestions"])==3 and
         all(q["execution"] is False and q["keep"] is False and
             q["publication"] is False and q["requiresHumanChoice"] is True
             for q in observation["possibleNextQuestions"]),
         "006 questions are proposals, not next-run permissions")
    return observation

class ACReviewBench:
    """The 004 human question, 005 revision and 006 observation meet HERE."""
    def __init__(self, *,cycle,selection,vidmage_record,vidmage_movie,
                 playdeck_receipt,playdeck_movie,record_dir,revision,
                 observation,ac_record_dir):
        self.first=first_review.ReviewBench(
            cycle=cycle,selection=selection,vidmage_record=vidmage_record,
            vidmage_movie=vidmage_movie,playdeck_receipt=playdeck_receipt,
            playdeck_movie=playdeck_movie,record_dir=record_dir)
        earlier=self.first.get_decision()
        need(earlier is not None and earlier["decision"]=="ANOTHER_EXPERIMENT" and
             earlier["chosenRenderer"] is None and
             earlier["nextExperimentPerformed"] is False,
             "A/C is only for a 004 human-authored next-question lineage")
        self.revision=nextq.ensure_record(read(revision),nextq.REVISION,"revisionSha256")
        verified_edit=nextq.reopen_revision(revision)
        need(verified_edit["status"]=="verified-editable-snapshot" and
             verified_edit["revisionSha256"]==self.revision["revisionSha256"],
             "005 source edit cannot be re-opened and verified")
        need(self.revision["sourceReviewSha256"]==earlier["reviewSha256"] and
             self.revision["humanQuestionVerbatim"]==earlier["nextQuestion"] and
             self.revision["originalVidmageMovieSha256"]==self.first.pair["vidmageFilmSha256"] and
             self.revision["originalPlaydeckMovieSha256"]==self.first.pair["playdeckFilmSha256"],
             "original author question or original film provenance differs")
        need(self.revision["humanKeep"] is False and
             self.revision["publish"] is False and
             self.revision["status"]=="performed-local-trial-not-reviewed",
             "005 trial must remain unreviewed and unpublished")
        self.observation=verify_observation(
            read(observation),self.revision,self.first)
        self.videos={
            "a":self.first.require_unchanged("a",cryptographic=True),
            "c":Path(self.revision["outputLocalPath"]).resolve(strict=True),
        }
        need(self.videos["a"]!=self.videos["c"] and
             self.videos["c"].is_file() and
             donors.sha_file(self.videos["c"])==self.revision["newMovieSha256"],
             "original and revised media must be separate, verified files")
        self.fingerprints={
            name:first_review.ReviewBench._fingerprint(path)
            for name,path in self.videos.items()
        }
        self.root=Path(ac_record_dir).expanduser().resolve()
        self.root.mkdir(parents=True,exist_ok=True)
        body={
            "schema":PAIR,
            "source004ReviewSha256":earlier["reviewSha256"],
            "source004PairSha256":self.first.pair["comparisonSha256"],
            "source005RevisionSha256":self.revision["revisionSha256"],
            "source006ObservationSha256":self.observation["observationSha256"],
            "humanQuestionVerbatim":earlier["nextQuestion"],
            "originalVidmageFilmSha256":self.first.pair["vidmageFilmSha256"],
            "revisedVidmageFilmSha256":self.revision["newMovieSha256"],
            "historicalPlaydeckFilmSha256":self.first.pair["playdeckFilmSha256"],
            "actualAuthorOperation":self.revision["experimentKind"],
            "actualAuthorChange":self.revision["changed"],
            "sourceSameAudioSha256":self.revision["actualSourceAudioSha256"],
            "measurementsNotRatings":True,
            "creatorChoiceStatus":"awaiting-explicit-A/C-review",
            "autoKeep":False,"published":False,
            "laws":["HISTORY != ACTIVE FILM","OBSERVATION != SELECTION",
                    "ORIGINAL != REVISED","PIXELS != QUALITY",
                    "SCRAPE != ERASE","A/C KEEP != PUBLICATION"],
        }
        self.pair={**body,"comparisonSha256":iq.digest(body)}
        self.pair_path=iq.write_once(self.root/"comparisons",self.pair,"comparisonSha256")
        self.decision_path=self.root/("human-ac-"+self.pair["comparisonSha256"]+".json")
        self._mutex=threading.Lock()
        self.token=secrets.token_urlsafe(32)
        self.get_decision()

    def require_unchanged(self,side, *,cryptographic=False):
        need(side in self.videos,"unknown A/C film side")
        path=self.videos[side]
        need(first_review.ReviewBench._fingerprint(path)==self.fingerprints[side],
             "video changed during A/C review session")
        if cryptographic:
            expected=self.pair["originalVidmageFilmSha256" if side=="a" else
                               "revisedVidmageFilmSha256"]
            need(donors.sha_file(path)==expected,"actual A/C MP4 source hash changed")
        return path

    def get_decision(self):
        if not self.decision_path.exists():return None
        result=read(self.decision_path)
        need(isinstance(result,dict) and result.get("schema")==SCHEMA and
             result.get("comparisonSha256")==self.pair["comparisonSha256"] and
             iq.sha(result.get("reviewSha256")) and
             iq.digest({k:v for k,v in result.items() if k!="reviewSha256"})==result["reviewSha256"],
             "previous A/C review record is tampered")
        need(result.get("decision") in DECISIONS and
             result.get("outcome")==DECISIONS[result["decision"]] and
             result.get("source004ReviewSha256")==self.pair["source004ReviewSha256"] and
             result.get("source005RevisionSha256")==self.pair["source005RevisionSha256"] and
             result.get("source006ObservationSha256")==self.pair["source006ObservationSha256"] and
             result.get("humanQuestionVerbatim")==self.pair["humanQuestionVerbatim"] and
             result.get("measurementsUsedAsAuthorChoice") is False and
             result.get("originalReviewRewritten") is False and
             result.get("autoExecute") is False and
             result.get("autoKeep") is False and
             result.get("publicationAuthorized") is False and
             result.get("exportAuthorized") is False and
             result.get("sourceFilesModified") is False and
             result.get("nextExperimentPerformed") is False,
             "A/C review cannot cross prior evidence or silently publish/execute edits")
        iq.bounded(result.get("operatorAttestationId"),
                   "A/C review needs its own operator attestation",256)
        question=result.get("newHumanQuestion")
        need(isinstance(question,str) and len(question)<=1200,
             "recorded A/C question must remain author-authored and bounded")
        if result["decision"]=="ASK_ANOTHER_QUESTION":
            iq.bounded(question,"A/C human question cannot be empty",1200)
        else:
            need(not question.strip(),
                 "A/C review cannot smuggle an unapproved follow-up question")
        expected=(
            "a" if result["decision"]=="CONTINUE_ORIGINAL" else
            "c" if result["decision"]=="CONTINUE_REVISION" else None)
        need(result.get("chosenSide")==expected and
             result.get("chosenFilmSha256")==(
               self.pair["originalVidmageFilmSha256"] if expected=="a" else
               self.pair["revisedVidmageFilmSha256"] if expected=="c" else None),
             "A/C decision attempts another film or forged selection")
        return result

    def state(self):
        choice=self.get_decision()
        obs=self.observation
        return {
            "schema":"vidmage/band-iq-007-local-review-ui/v1",
            "status":"recorded" if choice else "awaiting-new-human-choice",
            "reviewToken":self.token,
            "question":self.pair["humanQuestionVerbatim"],
            "operation":self.revision["experimentKind"],
            "change":self.revision["changed"],
            "pairSha256":self.pair["comparisonSha256"],
            "originalReviewSha256":self.pair["source004ReviewSha256"],
            "revisionSha256":self.pair["source005RevisionSha256"],
            "observationSha256":self.pair["source006ObservationSha256"],
            "renderers":{
                "a":{"title":"A · Original VidMage",
                     "url":"/media/a","sha256":self.pair["originalVidmageFilmSha256"]},
                "c":{"title":"C · Human-revised VidMage",
                     "url":"/media/c","sha256":self.pair["revisedVidmageFilmSha256"]},
            },
            "measurements":{
                "sampling":obs["sampling"],
                "windows":[{
                    "id":w["id"],"start":w["start"],"end":w["end"],
                    "pixelMeanAbsoluteDifference":w["pixelMeanAbsoluteDifference"],
                    "changedFrameFractionAt2PctMAE":w["changedFrameFractionAt2PctMAE"],
                    "operatorEditOverlapsThisWindow":w["operatorEditOverlapsThisWindow"],
                    "nonStillnessDelta":w["nativeDoctor"]["nonStillnessDelta"],
                } for w in obs["windows"]],
                "status":"technical-source-witness-only",
                "artisticJudgment":None,
            },
            "decision":choice,
            "constraints":{"reviewIsNotPublication":True,
                           "technicalMeasurementIsNotPreference":True,
                           "newQuestionIsNotExecution":True},
        }

    def commit(self,body):
        validate_choice(body)
        with self._mutex:
            need(self.get_decision() is None,
                 "A/C already reviewed; prior creator decision is immutable")
            self.first.require_unchanged("a",cryptographic=True)
            self.first.require_unchanged("b",cryptographic=True)
            self.require_unchanged("a",cryptographic=True)
            self.require_unchanged("c",cryptographic=True)
            # Old 004 question is still the same, never mutate that history.
            need(self.first.get_decision()["reviewSha256"]==
                 self.pair["source004ReviewSha256"],
                 "source 004 human question changed since opening A/C")
            decision=body["decision"]
            chosen=("a" if decision=="CONTINUE_ORIGINAL" else
                    "c" if decision=="CONTINUE_REVISION" else None)
            result={
                "schema":SCHEMA,
                "comparisonSha256":self.pair["comparisonSha256"],
                "source004ReviewSha256":self.pair["source004ReviewSha256"],
                "source005RevisionSha256":self.pair["source005RevisionSha256"],
                "source006ObservationSha256":self.pair["source006ObservationSha256"],
                "humanQuestionVerbatim":self.pair["humanQuestionVerbatim"],
                "decision":decision,"outcome":DECISIONS[decision],
                "operatorAttestationId":body["operatorAttestationId"].strip(),
                "rationale":body["rationale"],
                "newHumanQuestion":body["nextQuestion"].strip(),
                "chosenSide":chosen,
                "chosenFilmSha256":(
                    self.pair["originalVidmageFilmSha256"] if chosen=="a" else
                    self.pair["revisedVidmageFilmSha256"] if chosen=="c" else None),
                "autoExecute":False,
                "autoKeep":False,
                "publicationAuthorized":False,
                "exportAuthorized":False,
                "nextExperimentPerformed":False,
                "sourceFilesModified":False,
                "originalReviewRewritten":False,
                "measurementsUsedAsAuthorChoice":False,
                "laws":["VIEW != SELECT","SELECT != AUTOMATED KEEP",
                        "MEASUREMENT != TASTE","REVISION != ERASURE",
                        "QUESTION != RUN","CONTINUATION != PUBLICATION"],
            }
            saved={**result,"reviewSha256":iq.digest(result)}
            try:
                with self.decision_path.open("xb") as stream:
                    stream.write((json.dumps(saved,indent=2,sort_keys=True,
                                             ensure_ascii=False)+"\n").encode("utf8"))
                    stream.flush()
                    os.fsync(stream.fileno())
            except FileExistsError as exc:
                raise ValueError("BAND-IQ HOLD: A/C already reviewed") from exc
            need(self.get_decision()==saved,"written A/C review did not independently reopen")
            return saved

class ACHandler(first_review.Handler):
    def _static(self,path):
        mapping={
            "/":"band_iq_ac_review.html",
            "/ac-review.js":"band_iq_ac_review.js",
            "/review.css":"band_iq_review.css",
            "/ac-review.css":"band_iq_ac_review.css",
        }
        name=mapping.get(path)
        if not name:
            self._error(404,"unknown fixed review resource");return
        source=self.ui_dir/name
        if not source.is_file():
            self._error(500,"review surface missing");return
        blob=source.read_bytes()
        mime=("text/html" if name.endswith(".html") else
              "text/javascript" if name.endswith(".js") else "text/css")
        self._headers(200,mime+"; charset=utf-8",len(blob))
        if self.command!="HEAD":self.wfile.write(blob)

    def do_GET(self):
        path=urlsplit(self.path).path
        if path=="/api/context":
            self._json(200,self.bench.state())
        elif path in ("/media/a","/media/c"):
            self._video(path.rsplit("/",1)[-1])
        else:self._static(path)

    def do_POST(self):
        # Inherit 004's strict exact origin/session-token POST capability,
        # but do not expose any of its earlier 005/006 execution routes.
        if urlsplit(self.path).path!="/api/decision":
            self._error(404,"not an A/C review action");return
        super().do_POST()

def serve(bench,port=8765,open_browser=False):
    need(isinstance(port,int) and 0<=port<=65535,"loopback port invalid")
    class ThisAC(ACHandler):pass
    ThisAC.bench=bench
    http=ThreadingHTTPServer(("127.0.0.1",port),ThisAC)
    if open_browser:
        import webbrowser
        webbrowser.open("http://127.0.0.1:"+str(http.server_port)+"/")
    print(json.dumps({"url":"http://127.0.0.1:"+str(http.server_port)+"/",
                      "status":"owner-local-original-versus-revised-human-review",
                      "sourceComparisonSha256":bench.pair["comparisonSha256"],
                      "alreadyReviewed":bench.get_decision() is not None}),flush=True)
    return http

def cli():
    p=argparse.ArgumentParser(description="BAND-IQ 007: immutable local human original-vs-revision A/C choice")
    for name in ("cycle","selection","vidmage-record","vidmage-movie",
                 "playdeck-receipt","playdeck-movie","record-dir","revision",
                 "observation","ac-record-dir"):
        p.add_argument("--"+name,required=True)
    p.add_argument("--port",type=int,default=8765)
    p.add_argument("--open-browser",action="store_true")
    a=p.parse_args()
    bench=ACReviewBench(cycle=a.cycle,selection=a.selection,
        vidmage_record=a.vidmage_record,vidmage_movie=a.vidmage_movie,
        playdeck_receipt=a.playdeck_receipt,playdeck_movie=a.playdeck_movie,
        record_dir=a.record_dir,revision=a.revision,observation=a.observation,
        ac_record_dir=a.ac_record_dir)
    server=serve(bench,a.port,open_browser=a.open_browser)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=="__main__":
    cli()
