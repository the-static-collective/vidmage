"""BAND-IQ 007: real separate signed A/C decision, source custody and localhost refusals."""
import contextlib
import io
import json
import threading
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen

from bridge import band_iq as iq
from bridge import band_iq_ac_review as ac
from bridge import band_iq_donors as donors
from bridge import band_iq_film_loop as film_loop
from bridge import band_iq_next_question as nxt
from bridge import band_iq_question_lab as lab
from bridge import band_iq_review as review
from tests.test_band_iq_review import make_context

def _write(path,record):
    path.write_text(json.dumps(record),encoding="utf8")
    return path

def setup_fixture(root):
    original=make_context(root)
    bench=review.ReviewBench(**original)
    earlier=bench.commit({
        "decision":"ANOTHER_EXPERIMENT",
        "operatorAttestationId":"author-chose-to-ask-first",
        "rationale":"The first cut is not the final answer.",
        "nextQuestion":"Would the second source be stronger at the opening?",
        "acknowledgedTrialOnly":True,
    })
    movie=root/"actual-edited-film.mp4"
    movie.write_bytes(b"\x00\x00\x00\x18ftypisom"+b"Actual C picture film"*100)
    audio=root/"owned-song.wav"; audio.write_bytes(b"PCM owner-only synthetic")
    (root/"a.png").write_bytes(b"synthetic original still")
    (root/"b.png").write_bytes(b"synthetic other still")
    cards={
        "schema":"vidmage/editorial-scene-cards/v1",
        "status":"proposal-only",
        "assets":{
            "a":{"path":"a.png","mode":"subject","focus":[.5,.5]},
            "b":{"path":"b.png","mode":"subject","focus":[.5,.5]},
        },
        "shots":[{"shotId":"s1","assetId":"b","kineticSafe":False}],
    }
    paper={"schema":"haunted-blender/paper-director-plan/v1",
           "durationSeconds":4.,"shots":[{"id":"s1","start":0.,"end":4.}]}
    toaster={"schema":"vidmage/toaster-lbranch-observation/v1",
             "status":"observation-only","sourceAudioSha256":donors.sha_file(audio),
             "laneBank":{"schema":"haunted-toaster/lane-bank/v1","laneBankHash":"a"*64},
             "authority":{"publish":False}}
    source_assets=film_loop.exact_asset_bindings(cards,root)
    revision_body={
       "schema":nxt.REVISION,
       "sourceReviewSha256":earlier["reviewSha256"],
       "questionSetSha256":"b"*64,
       "humanQuestionVerbatim":earlier["nextQuestion"],
       "experimentKind":"SWAP_CARD",
       "changed":{"shotId":"s1","fromAssetId":"a","toAssetId":"b"},
       "oldCardsSha256":"c"*64,
       "revisedCards":cards,
       "revisedCardsSha256":iq.digest(cards),
       "nativePaperPlan":paper,
       "nativePaperPlanSha256":iq.digest(paper),
       "nativeToasterObservation":toaster,
       "nativeToasterObservationSha256":iq.digest(toaster),
       "actualSourceAudioSha256":donors.sha_file(audio),
       "actualSourceAssetsSha256":source_assets,
       "originalVidmageMovieSha256":bench.pair["vidmageFilmSha256"],
       "originalPlaydeckMovieSha256":bench.pair["playdeckFilmSha256"],
       "newMovieSha256":donors.sha_file(movie),
       "outputLocalPath":str(movie),
       "sourceAssetRootLocalPath":str(root),
       "sourceAudioLocalPath":str(audio),
       "status":"performed-local-trial-not-reviewed",
       "humanKeep":False,"publish":False,
       "automaticChainedExperiment":False,
       "originalSourcesDeleted":False,
    }
    revision={**revision_body,"revisionSha256":iq.digest(revision_body)}
    revision_path=_write(root/"revision.json",revision)
    questions=lab.make_questions("SWAP_CARD",["window-0001"],[])
    obs_body={
        "schema":lab.SCHEMA,"status":"observed-local-not-reviewed",
        "sourceReviewSha256":earlier["reviewSha256"],
        "sourceRevisionSha256":revision["revisionSha256"],
        "sourceQuestionSetSha256":revision["questionSetSha256"],
        "humanQuestionVerbatim":earlier["nextQuestion"],
        "actualOldFilmSha256":bench.pair["vidmageFilmSha256"],
        "actualNewFilmSha256":revision["newMovieSha256"],
        "playdeckEarlierFilmSha256":bench.pair["playdeckFilmSha256"],
        "sourcePaperPlanSha256":revision["nativePaperPlanSha256"],
        "nativeToasterObservationSha256":revision["nativeToasterObservationSha256"],
        "audioSha256":revision["actualSourceAudioSha256"],
        "revisedSceneCardsSha256":revision["revisedCardsSha256"],
        "originalSceneCardsSha256":revision["oldCardsSha256"],
        "humanChosenOperation":"SWAP_CARD","humanChosenEdit":revision["changed"],
        "realNativeDoctor":True,"native008eExecution":False,
        "automaticKeep":False,"automaticExecution":False,
        "newExperimentAuthorized":False,"published":False,
        "artisticJudgment":None,"questionInterpretation":"not inferred",
        "nativeDoctorCoverageOriginal":1.0,"nativeDoctorCoverageRevision":1.0,
        "sampling":{"framesPerSecond":4,"frameWidth":64,"frameHeight":36,
                    "pixelMAEAcrossSong":.055,"changeThresholdMAE":.02},
        "selectedOperatorChangeTime":{"start":.5,"end":2.0,
                                      "overlappingDoctorWindowIds":["window-0001"]},
        "windows":[
            {"id":"window-0001","start":0.,"end":2.,
             "pixelMeanAbsoluteDifference":.01,"changedFrameFractionAt2PctMAE":.2,
             "sampledPairs":8,"operatorEditOverlapsThisWindow":True,
             "operatorEditOverlapSeconds":1.5,
             "nativeDoctor":{"nonStillnessDelta":.03}},
            {"id":"window-0002","start":2.,"end":4.,
             "pixelMeanAbsoluteDifference":.1,"changedFrameFractionAt2PctMAE":.9,
             "sampledPairs":8,"operatorEditOverlapsThisWindow":False,
             "operatorEditOverlapSeconds":0.,
             "nativeDoctor":{"nonStillnessDelta":-.05}},
        ],
        "possibleNextQuestions":questions,
    }
    observation={**obs_body,"observationSha256":iq.digest(obs_body)}
    observation_path=_write(root/"observation.json",observation)
    params={**original,"revision":revision_path,"observation":observation_path,
            "ac_record_dir":root/"human-ac"}
    return params,earlier,revision,observation

def choice(action="CONTINUE_REVISION",question=""):
    return {
        "decision":action,
        "operatorAttestationId":"human-second-look-author",
        "rationale":"I watched both actual films and chose intentionally.",
        "nextQuestion":question,"acknowledgedLocalOnly":True,
    }

class ACRoomTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.params,self.first_receipt,self.revision,self.observation=setup_fixture(self.root)
        self.room=ac.ACReviewBench(**self.params)
    def tearDown(self):
        self.tmp.cleanup()

    def test_earlier_review_and_both_movies_survive_new_choice(self):
        a=donors.sha_file(self.room.videos["a"])
        c=donors.sha_file(self.room.videos["c"])
        older=self.room.first.get_decision()
        self.assertEqual(older["decision"],"ANOTHER_EXPERIMENT")
        self.assertEqual(self.room.state()["status"],"awaiting-new-human-choice")
        self.assertEqual(self.room.state()["question"],older["nextQuestion"])
        self.assertEqual(len(self.room.state()["measurements"]["windows"]),2)
        selected=self.room.commit(choice())
        self.assertEqual(selected["chosenSide"],"c")
        self.assertEqual(selected["chosenFilmSha256"],c)
        self.assertFalse(selected["autoKeep"])
        self.assertFalse(selected["publicationAuthorized"])
        self.assertFalse(selected["nextExperimentPerformed"])
        self.assertEqual(self.room.get_decision(),selected)
        self.assertEqual(donors.sha_file(self.room.videos["a"]),a)
        self.assertEqual(donors.sha_file(self.room.videos["c"]),c)
        self.assertEqual(self.room.first.get_decision(),older)
        with self.assertRaisesRegex(ValueError,"already reviewed"):
            self.room.commit(choice("CONTINUE_ORIGINAL"))
        reopened=ac.ACReviewBench(**self.params)
        self.assertEqual(reopened.get_decision(),selected)
        self.assertEqual(reopened.state()["status"],"recorded")

    def test_decline_and_new_question_do_not_delete_or_execute(self):
        for action,question in (
            ("CONTINUE_ORIGINAL",""),("DECLINE_BOTH",""),
            ("ASK_ANOTHER_QUESTION","What if the camera holds a little longer?"),
        ):
            with self.subTest(action=action):
                with tempfile.TemporaryDirectory() as d:
                    room=ac.ACReviewBench(**{**self.params,"ac_record_dir":Path(d)})
                    saved=room.commit(choice(action,question))
                    self.assertEqual(saved["newHumanQuestion"],question)
                    self.assertFalse(saved["sourceFilesModified"])
                    self.assertFalse(saved["nextExperimentPerformed"])
                    self.assertEqual(saved["chosenSide"],
                                     "a" if action=="CONTINUE_ORIGINAL" else None)
        for bad in (
            dict(choice(),decision="AUTO_PUBLISH"),
            dict(choice(),acknowledgedLocalOnly=False),
            dict(choice("ASK_ANOTHER_QUESTION"),nextQuestion=""),
            dict(choice(),nextQuestion="silently launch something"),
            dict(choice(),operatorAttestationId=""),
            dict(choice(),unknownPrivilege=True),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    ac.validate_choice(bad)

    def test_observation_and_revision_tampering_refused_before_review(self):
        doc=json.loads(self.params["observation"].read_text())
        doc["humanQuestionVerbatim"]="model changed creator question"
        self.params["observation"].write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"evidence identity"):
            ac.ACReviewBench(**self.params)
        self.params["observation"].write_text(json.dumps(self.observation))
        doc=json.loads(self.params["revision"].read_text())
        doc["newMovieSha256"]="0"*64
        self.params["revision"].write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"evidence identity"):
            ac.ACReviewBench(**self.params)

    def test_existing_choice_tamper_refuses_reopen(self):
        self.room.commit(choice())
        doc=json.loads(self.room.decision_path.read_text())
        doc["decision"]="CONTINUE_ORIGINAL"
        self.room.decision_path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"tampered"):
            self.room.get_decision()
        with self.assertRaisesRegex(ValueError,"tampered"):
            ac.ACReviewBench(**self.params)

    def test_rehashed_review_claim_cannot_override_prior_receipt(self):
        saved=self.room.commit(choice("CONTINUE_REVISION"))
        forged=dict(saved,source006ObservationSha256="0"*64)
        forged["reviewSha256"]=iq.digest({
            key:value for key,value in forged.items() if key!="reviewSha256"
        })
        self.room.decision_path.write_text(json.dumps(forged))
        with self.assertRaisesRegex(ValueError,"cannot cross prior evidence"):
            self.room.get_decision()

    def test_rehashed_unapproved_next_question_refused(self):
        saved=self.room.commit(choice("CONTINUE_ORIGINAL"))
        forged=dict(saved,newHumanQuestion="secretly launch a render")
        forged["reviewSha256"]=iq.digest({
            key:value for key,value in forged.items() if key!="reviewSha256"
        })
        self.room.decision_path.write_text(json.dumps(forged))
        with self.assertRaisesRegex(ValueError,"unapproved follow-up question"):
            self.room.get_decision()

    def test_new_movie_tamper_refused_on_review(self):
        self.room.videos["c"].write_bytes(self.room.videos["c"].read_bytes()+b"forgery")
        with self.assertRaisesRegex(ValueError,"video changed"):
            self.room.commit(choice())

    def test_http_real_original_and_revision_media_and_origin_gate(self):
        with contextlib.redirect_stdout(io.StringIO()):
            http=ac.serve(self.room,port=0)
        thread=threading.Thread(target=http.serve_forever,daemon=True)
        thread.start()
        try:
            base=f"http://127.0.0.1:{http.server_port}"
            with urlopen(base+"/") as response:
                html=response.read().decode("utf8")
                self.assertIn("The question has two answers.",html)
                self.assertIn("default-src 'none'",response.headers["Content-Security-Policy"])
            for path in ("/ac-review.js","/ac-review.css","/review.css"):
                with urlopen(base+path) as response:
                    self.assertGreater(len(response.read()),100)
            with urlopen(base+"/api/context") as response:
                state=json.load(response)
            self.assertEqual(state["reviewToken"],self.room.token)
            self.assertIsNone(state["decision"])
            c=self.room.videos["c"].read_bytes()
            with urlopen(Request(base+"/media/c",
                                 headers={"Range":"bytes=0-31"})) as response:
                self.assertEqual(response.status,206)
                self.assertEqual(response.read(),c[:32])
                self.assertEqual(response.headers["Content-Range"],
                                 f"bytes 0-31/{len(c)}")
            with self.assertRaises(HTTPError) as missing:
                urlopen(base+"/media/../../secret")
            self.assertEqual(missing.exception.code,404)
            payload=json.dumps(choice("CONTINUE_ORIGINAL")).encode("utf8")
            bad=Request(base+"/api/decision",data=payload,headers={
                "Content-Type":"application/json",
                "Origin":"https://attacker.example",
                "X-Review-Token":self.room.token,
            })
            with self.assertRaises(HTTPError) as denied:
                urlopen(bad)
            self.assertEqual(denied.exception.code,403)
            self.assertIsNone(self.room.get_decision())
            # A/C room must not expose the old 005 execution door.
            with self.assertRaises(HTTPError) as no_run:
                urlopen(Request(base+"/api/next/execute",data=payload,headers={
                    "Content-Type":"application/json","Origin":base,
                    "X-Review-Token":self.room.token}))
            self.assertEqual(no_run.exception.code,404)
            good=Request(base+"/api/decision",data=payload,headers={
                "Content-Type":"application/json","Origin":base,
                "X-Review-Token":self.room.token,
            })
            with urlopen(good) as response:
                self.assertEqual(response.status,201)
                receipt=json.load(response)["receipt"]
            self.assertEqual(receipt["chosenSide"],"a")
            with self.assertRaises(HTTPError) as replay:
                urlopen(good)
            self.assertEqual(replay.exception.code,409)
            with urlopen(base+"/api/context") as response:
                self.assertEqual(json.load(response)["status"],"recorded")
        finally:
            http.shutdown();http.server_close();thread.join(timeout=3)

if __name__=="__main__":unittest.main()
