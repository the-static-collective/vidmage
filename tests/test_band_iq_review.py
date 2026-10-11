"""BAND-IQ 004: offline local review tests, immutable human decision and HTTP media controls."""
import contextlib
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen

from bridge import band_iq as iq
from bridge import band_iq_film_loop as loop
from bridge import band_iq_playdeck_native as native
from bridge import band_iq_review as review
from bridge import band_iq_donors as donors


def make_context(root):
    # Synthetic bytes only. The native 003 CI separately proves actual playable MP4s.
    film_a=root/"vidmage.mp4"; film_b=root/"playdeck.mp4"
    film_a.write_bytes(b"\x00\x00\x00\x18ftypisom"+"A BAND-IQ VIDMAGE synthetic video".encode()*40)
    film_b.write_bytes(b"\x00\x00\x00\x18ftypisom"+"B BAND-IQ PLAYDECK synthetic video".encode()*40)
    a=donors.sha_file(film_a)
    b=donors.sha_file(film_b)
    audio="c"*64
    prior="d"*64
    # Use native BAND-IQ model, not a synthetic forged cycle.
    comps={"stasis":0.1,"sourceOveruse":0.85,"recentRepetition":0.35,
           "noveltyDeficit":0.1,"transitionJolt":0.05}
    rows=[]
    for i in range(2):
        rows.append({"id":f"window-{i+1:04}","start":i*2.0,"end":(i+1)*2.0,
                     "weaknessScore":0.4,"dominantWeakness":"sourceOveruse",
                     "components":comps})
    report={"schema":iq.DOCTOR,"sourceVideoSha256":prior,"planId":"fixture-plan",
            "targetSeconds":4.0,"observedVideoSeconds":4.0,"coverageRatio":1.0,
            "windows":rows}
    cycle=iq.build_cycle({"schema":iq.INPUT,"doctorReport":report,
                          "audioObservation":None,"artistAnnotations":[]})
    proposal=cycle["imagine"][0]
    selection={"proposalSha256":proposal["proposalSha256"],
               "operatorAttestationId":"fixture-reviewed-lens"}
    img_a="e"*64; img_b="f"*64
    film_record_data={
       "schema":loop.FILM_RECORD,
       "sourceCycleSha256":cycle["cycleSha256"],
       "sourceDoctorSha256":iq.digest(report),
       "sourceVideoSha256":prior,
       "performedVideoSha256":a,
       "selectedProposalSha256":proposal["proposalSha256"],
       "selectionSha256":iq.digest(selection),
       "actualAudioSha256":audio,
       "actualAssetSha256":{"asset-a":img_a,"asset-b":img_b},
       "chosenLens":proposal["lensId"],
       "cameraMode":proposal["cameraMode"],
    }
    film_record={**film_record_data,"filmRecordSha256":iq.digest(film_record_data)}
    playdeck_data={
        "schema":native.SCHEMA,
        "sourceCycleSha256":cycle["cycleSha256"],
        "selectedProposalSha256":proposal["proposalSha256"],
        "selectionSha256":iq.digest(selection),
        "nativePlaydeckSourceSha":native.PLAYDECK_SHA,
        "nativePlaydeckRendering":True,
        "automaticKeep":False,
        "actualOutputSha256":b,
        "sourceVideoSha256":prior,
        "studio011Lens":proposal["lensId"],
        "targetStart":proposal["targetStart"],
        "targetEnd":proposal["targetEnd"],
        "inputAssetSha256":{"asset://band-iq-003/source-audio":audio,
                            "asset://band-iq-003/asset-a":img_a,
                            "asset://band-iq-003/asset-b":img_b},
    }
    playdeck={**playdeck_data,"receiptSha256":iq.digest(playdeck_data)}
    paths={}
    for key,value in (("cycle",cycle),("selection",selection),
                      ("vidmage_record",film_record),("playdeck_receipt",playdeck)):
        target=root/(key+".json")
        target.write_text(json.dumps(value))
        paths[key]=target
    paths.update(vidmage_movie=film_a,playdeck_movie=film_b,record_dir=root/"reviews")
    return paths


def form(decision="KEEP_VIDMAGE",question=""):
    return {
       "decision":decision,
       "operatorAttestationId":"creator-chose-after-watching",
       "rationale":"I prefer how this particular passage is carried.",
       "nextQuestion":question,
       "acknowledgedTrialOnly":True,
    }


class ReviewLocalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.params=make_context(self.root)
        self.bench=review.ReviewBench(**self.params)

    def tearDown(self):
        self.tmp.cleanup()

    def test_real_source_pairs_are_verified_at_startup(self):
        self.assertEqual(self.bench.pair["status"],"compared-authority-separated")
        self.assertEqual(self.bench.state()["status"],"awaiting-human-review")
        self.assertTrue(Path(self.bench.pair_path).is_file())
        self.assertIsNone(self.bench.state()["decision"])
        self.assertFalse(self.bench.state()["constraints"]["publication"])

    def test_one_human_choice_is_sealed_and_survives_reopen(self):
        a=donors.sha_file(self.params["vidmage_movie"])
        b=donors.sha_file(self.params["playdeck_movie"])
        first=self.bench.commit(form())
        self.assertEqual(first["chosenRenderer"],"a")
        self.assertEqual(first["chosenFilmSha256"],a)
        self.assertFalse(first["publicationAuthorized"])
        self.assertFalse(first["automaticExecution"])
        self.assertEqual(first["outcome"],"selected-for-local-continuation")
        self.assertTrue(self.bench.decision_path.is_file())
        self.assertEqual(donors.sha_file(self.params["vidmage_movie"]),a)
        self.assertEqual(donors.sha_file(self.params["playdeck_movie"]),b)
        with self.assertRaisesRegex(ValueError,"already recorded"):
            self.bench.commit(form("KEEP_PLAYDECK"))
        reopened=review.ReviewBench(**self.params)
        self.assertEqual(reopened.get_decision(),first)
        self.assertEqual(reopened.state()["status"],"recorded")

    def test_rejected_choices_and_next_question_without_execution(self):
        for choice,question in (("SCRAPE_BOTH",""),("ANOTHER_EXPERIMENT",
                                               "Keep the second shot's deliberate pause")):
            with self.subTest(choice=choice):
                with tempfile.TemporaryDirectory() as temp:
                    params={**self.params,"record_dir":Path(temp)}
                    candidate=review.ReviewBench(**params)
                    receipt=candidate.commit(form(choice,question))
                    self.assertIsNone(receipt["chosenRenderer"])
                    self.assertIsNone(receipt["chosenFilmSha256"])
                    self.assertFalse(receipt["nextExperimentPerformed"])
                    self.assertFalse(receipt["publicationAuthorized"])
        for invalid in [
             dict(form(),decision="PUBLISH"),
             dict(form(),acknowledgedTrialOnly=False),
             dict(form("ANOTHER_EXPERIMENT"),nextQuestion=""),
             dict(form(),operatorAttestationId=""),
             dict(form(),nextQuestion="unrequested"),
        ]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    review.validate_decision(invalid)

    def test_source_tamper_and_existing_receipt_tamper_refused(self):
        file=self.params["playdeck_movie"]
        file.write_bytes(file.read_bytes()+b"X")
        with self.assertRaisesRegex(ValueError,"media source changed"):
            self.bench.commit(form())
        file.write_bytes(file.read_bytes()[:-1])
        # Integrity check at commit still rehashes the actual source.
        self.assertTrue(self.bench.commit(form())["reviewSha256"])
        stored=json.loads(self.bench.decision_path.read_text())
        stored["decision"]="KEEP_PLAYDECK"
        self.bench.decision_path.write_text(json.dumps(stored))
        with self.assertRaisesRegex(ValueError,"readback"):
            self.bench.get_decision()
        with self.assertRaisesRegex(ValueError,"readback"):
            review.ReviewBench(**self.params)

    def test_pair_source_mismatch_refused_before_any_review(self):
        doc=json.loads(self.params["playdeck_receipt"].read_text())
        doc["actualOutputSha256"]="0"*64
        self.params["playdeck_receipt"].write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,"receipt changed"):
            review.ReviewBench(**self.params)

    def test_local_http_review_bytes_and_same_origin_capability(self):
        with contextlib.redirect_stdout(io.StringIO()):
            server=review.serve(self.bench,port=0)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            base=f"http://127.0.0.1:{server.server_port}"
            with urlopen(base+"/") as x:
                text=x.read().decode()
                self.assertIn("Two films. One human decision.",text)
                self.assertIn("default-src 'none'",x.headers["Content-Security-Policy"])
            for path in ("/review.js","/review.css"):
                with urlopen(base+path) as x:
                    self.assertEqual(x.status,200)
                    self.assertGreater(len(x.read()),100)
            with urlopen(base+"/api/context") as x:
                state=json.load(x)
            self.assertEqual(state["reviewToken"],self.bench.token)
            self.assertEqual(state["renderers"]["a"]["sha256"],
                             donors.sha_file(self.params["vidmage_movie"]))
            original=self.params["vidmage_movie"].read_bytes()
            request=Request(base+"/media/a",headers={"Range":"bytes=0-15"})
            with urlopen(request) as response:
                self.assertEqual(response.status,206)
                self.assertEqual(response.read(),original[:16])
                self.assertEqual(response.headers["Content-Range"],
                                 f"bytes 0-15/{len(original)}")
            # No arbitrary file browser, even from local client.
            with self.assertRaises(HTTPError) as caught:
                urlopen(base+"/media/%2e%2e/%2e%2e/secrets")
            self.assertEqual(caught.exception.code,404)
            request=Request(base+"/api/decision",data=json.dumps(form()).encode(),
                            headers={"Content-Type":"application/json",
                                     "Origin":"https://attacker.example",
                                     "X-Review-Token":self.bench.token})
            with self.assertRaises(HTTPError) as caught:
                urlopen(request)
            self.assertEqual(caught.exception.code,403)
            self.assertIsNone(self.bench.get_decision())
            legit=Request(base+"/api/decision",data=json.dumps(form("KEEP_PLAYDECK")).encode(),
                          headers={"Content-Type":"application/json",
                                   "Origin":base,"X-Review-Token":self.bench.token})
            with urlopen(legit) as response:
                self.assertEqual(response.status,201)
                r=json.load(response)["receipt"]
            self.assertEqual(r["chosenRenderer"],"b")
            with self.assertRaises(HTTPError) as caught:
                urlopen(legit)
            self.assertEqual(caught.exception.code,409)
            with urlopen(base+"/api/context") as response:
                self.assertEqual(json.load(response)["status"],"recorded")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

if __name__=="__main__":
    unittest.main()
