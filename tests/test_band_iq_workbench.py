"""BAND-IQ 008: one truthful workbench and private restartable real-file doors."""
from __future__ import annotations
import contextlib
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen

from bridge import band_iq as iq
from bridge import band_iq_workbench as workbench
from bridge import band_iq_donors as donors
from tests.test_band_iq_ac_review import setup_fixture
from tests.test_band_iq_review import make_context

def post(base,path,payload,token,*,origin=None,token_header="X-Workbench-Token"):
    return Request(base+path,data=json.dumps(payload).encode(),
                   headers={"Content-Type":"application/json",
                            "Origin":origin or base,
                            token_header:token})

class WorkshopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.core=make_context(self.root)
        self.profile=workbench.make_profile(self.core)
        self.bench=workbench.Workbench(self.profile)

    def tearDown(self):
        self.tmp.cleanup()

    def test_single_project_map_verifies_real_originals_no_fake_progress(self):
        status=self.bench.state()
        self.assertEqual(status["schema"],"vidmage/band-iq-008-workbench-status/v1")
        self.assertEqual(len(status["steps"]),7)
        self.assertEqual(status["steps"][0]["status"],"verified")
        self.assertEqual(status["steps"][2]["status"],"verified")
        self.assertEqual(status["steps"][3]["status"],"awaiting-human")
        self.assertEqual(status["steps"][-1]["status"],"not-yet")
        self.assertFalse(status["candidates"])
        self.assertIsNone(status["activePair"])
        self.assertIsNone(status["firstReviewSha256"])
        self.assertTrue(status["constraints"]["noImplicitRender"])
        self.assertEqual(self.profile["projectSha256"],iq.digest({
            k:v for k,v in self.profile.items() if k!="projectSha256"
        }))
        self.assertEqual(len(list(self.root.glob("**/*.mp4"))),2)

    def test_project_map_is_create_only_and_tamper_refusing(self):
        bad=dict(self.profile,publication=True)
        with self.assertRaisesRegex(ValueError,"execution-authorizing"):
            workbench.Workbench(bad)
        bad=dict(self.profile,original={**self.profile["original"],"extra":"file"})
        bad["projectSha256"]=iq.digest({k:v for k,v in bad.items()
                                       if k!="projectSha256"})
        with self.assertRaisesRegex(ValueError,"project map"):
            workbench.Workbench(bad)
        bad=dict(self.profile,original={
            **self.profile["original"],"vidmage_movie":str(self.root/"missing.mp4")
        })
        bad["projectSha256"]=iq.digest({k:v for k,v in bad.items()
                                       if k!="projectSha256"})
        with self.assertRaises((ValueError,FileNotFoundError)):
            workbench.Workbench(bad)

    def test_no_direct_ac_without_exact_revision_selection(self):
        with contextlib.redirect_stdout(io.StringIO()):
            http=workbench.serve(self.bench,port=0)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        try:
            base=f"http://127.0.0.1:{http.server_port}"
            with urlopen(base+"/") as response:
                html=response.read().decode()
                self.assertIn("Seven doors. One workbench.",html)
                self.assertIn("default-src 'none'",response.headers["Content-Security-Policy"])
            for path in ("/workbench.js","/workbench.css","/review.js","/review.css"):
                with urlopen(base+path) as response:
                    self.assertEqual(response.status,200)
                    self.assertGreater(len(response.read()),100)
            with urlopen(base+"/room") as response:
                self.assertIn("Two films. One human decision.",response.read().decode())
            with urlopen(base+"/api/context") as response:
                self.assertEqual(json.load(response)["schema"],
                                 "vidmage/band-iq-review-ui/v1")
            with self.assertRaises(HTTPError) as ac:
                urlopen(base+"/ac/")
            self.assertEqual(ac.exception.code,409)
            with self.assertRaises(HTTPError) as bad:
                urlopen(base+"/private/something.mp4")
            self.assertEqual(bad.exception.code,404)
        finally:
            http.shutdown();http.server_close();thread.join(timeout=3)


class ExistingArtifactsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.core,self.old,self.revision,self.observation=setup_fixture(self.root)
        record_dir=Path(self.core["record_dir"])
        self.revisions=record_dir/"next-trials"/"band-iq-005-revisions"
        self.observations=record_dir/"question-observations"
        self.revisions.mkdir(parents=True,exist_ok=True)
        self.observations.mkdir(parents=True,exist_ok=True)
        self.rpath=self.revisions/(self.revision["revisionSha256"]+".json")
        self.opath=self.observations/(self.observation["observationSha256"]+".json")
        self.rpath.write_text(json.dumps(self.revision))
        self.opath.write_text(json.dumps(self.observation))
        source={k:self.core[k] for k in workbench.CORE}
        self.profile=workbench.make_profile(source,ac_record_dir=self.root/"workbench-ac")
        self.bench=workbench.Workbench(self.profile)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reopen_actual_source_project_and_select_one_observed_revision(self):
        state=self.bench.state()
        self.assertEqual(state["firstReviewDecision"],"ANOTHER_EXPERIMENT")
        self.assertEqual(state["questionVerbatim"],self.old["nextQuestion"])
        self.assertEqual(len(state["candidates"]),1)
        item=state["candidates"][0]
        self.assertEqual(item["evidence"],"measured")
        self.assertTrue(item["selectionRequired"])
        self.assertEqual(state["steps"][4]["status"],"recorded")
        self.assertEqual(state["steps"][5]["status"],"observed")
        self.assertEqual(state["steps"][6]["status"],"available")
        self.assertIsNone(self.bench.ac_bench)
        active=self.bench.select(self.revision["revisionSha256"],
                                 self.observation["observationSha256"])
        self.assertEqual(active["question"],self.old["nextQuestion"])
        self.assertEqual(active["renderers"]["c"]["sha256"],self.revision["newMovieSha256"])
        self.assertEqual(self.bench.state()["steps"][6]["status"],"ready")
        self.assertEqual(self.bench.state()["activeRevision"],self.revision["revisionSha256"])
        self.assertEqual(self.bench.first.next_result["movieSha256"],self.revision["newMovieSha256"])
        chosen=self.bench.ac_bench.commit({
             "decision":"CONTINUE_REVISION",
             "operatorAttestationId":"actual-separate-artist-decision",
             "rationale":"A selected local continuation, not a published film",
             "nextQuestion":"",
             "acknowledgedLocalOnly":True,
        })
        self.assertEqual(chosen["chosenSide"],"c")
        self.assertEqual(self.bench.state()["steps"][6]["status"],"recorded")
        self.assertEqual(self.bench.first.get_decision(),self.old)
        # A NEW workbench process starts with no inferred A/C candidate selection.
        new=workbench.Workbench(self.profile)
        self.assertIsNone(new.ac_bench)
        new.select(self.revision["revisionSha256"],
                   self.observation["observationSha256"])
        self.assertEqual(new.ac_bench.get_decision(),chosen)

    def test_unmeasured_revision_resumes_without_starting_new_render(self):
        self.opath.unlink()
        self.assertEqual(self.bench.state()["candidates"][0]["evidence"],
                         "rendered-not-measured")
        before=donors.sha_file(self.revision["outputLocalPath"])
        recovered=self.bench.restore_revision(self.revision["revisionSha256"])
        self.assertEqual(recovered["movieSha256"],before)
        self.assertEqual(self.bench.first.next_result["movieSha256"],before)
        self.assertEqual(donors.sha_file(self.revision["outputLocalPath"]),before)
        with self.assertRaisesRegex(ValueError,"not found"):
            self.bench.select(self.revision["revisionSha256"],
                              "0"*64)

    def test_mismatched_observation_not_usable_even_with_new_hash(self):
        modified=dict(self.observation,actualNewFilmSha256="f"*64)
        modified["observationSha256"]=iq.digest({
            k:v for k,v in modified.items() if k!="observationSha256"
        })
        new=self.observations/(modified["observationSha256"]+".json")
        new.write_text(json.dumps(modified))
        # Discovery returns it as a candidate, but selecting it MUST fail
        # the 007 source-integrity contract.
        with self.assertRaisesRegex(ValueError,"film/plan/cards/audio source evidence changed"):
            self.bench.select(self.revision["revisionSha256"],
                              modified["observationSha256"])
        self.assertIsNone(self.bench.ac_bench)
        self.assertIsNone(self.bench.first.next_result)

    def test_same_origin_single_port_004_and_007_playback_and_choice(self):
        with contextlib.redirect_stdout(io.StringIO()):
            http=workbench.serve(self.bench,port=0)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        try:
            base=f"http://127.0.0.1:{http.server_port}"
            with urlopen(base+"/api/workbench/status") as response:
                first=json.load(response)
            self.assertEqual(len(first["candidates"]),1)
            rev=self.revision["revisionSha256"]
            obs=self.observation["observationSha256"]
            forged=post(base,"/api/workbench/select",{
                "revisionSha256":rev,"observationSha256":obs},
                first["token"],origin="https://untrusted.example")
            with self.assertRaises(HTTPError) as outside:
                urlopen(forged)
            self.assertEqual(outside.exception.code,403)
            with self.assertRaises(HTTPError) as invalid:
                urlopen(post(base,"/api/workbench/select",{
                    "revisionSha256":rev,"observationSha256":obs,
                    "arbitraryMoviePath":"/private/canary.mp4"},first["token"]))
            self.assertEqual(invalid.exception.code,409)
            self.assertIsNone(self.bench.ac_bench)
            with urlopen(post(base,"/api/workbench/select",{
                "revisionSha256":rev,"observationSha256":obs},first["token"])) as response:
                self.assertEqual(response.status,200)
                selected=json.load(response)
            self.assertTrue(selected["ok"])
            self.assertEqual(selected["ac"]["question"],self.old["nextQuestion"])
            with urlopen(base+"/ac/") as response:
                page=response.read().decode()
                self.assertIn("The question has two answers.",page)
            for path in ("/ac/review.css","/ac/ac-review.js","/ac/ac-review.css"):
                with urlopen(base+path) as response:
                    self.assertGreater(len(response.read()),100)
            with urlopen(base+"/ac/api/context") as response:
                ac_context=json.load(response)
            self.assertEqual(ac_context["renderers"]["c"]["url"],"media/c")
            self.assertEqual(ac_context["reviewToken"],self.bench.ac_bench.token)
            original=self.bench.ac_bench.videos["c"].read_bytes()
            with urlopen(Request(base+"/ac/media/c",
                                 headers={"Range":"bytes=0-15"})) as response:
                self.assertEqual(response.status,206)
                self.assertEqual(response.read(),original[:16])
            with self.assertRaises(HTTPError) as ac_block:
                urlopen(post(base,"/ac/api/next/execute",{},ac_context["reviewToken"],
                            token_header="X-Review-Token"))
            self.assertEqual(ac_block.exception.code,404)
            with self.assertRaises(HTTPError) as bad_origin:
                urlopen(post(base,"/ac/api/decision",{
                    "decision":"CONTINUE_REVISION","operatorAttestationId":"artist",
                    "rationale":"","nextQuestion":"","acknowledgedLocalOnly":True},
                    ac_context["reviewToken"],origin="https://bad.example",
                    token_header="X-Review-Token"))
            self.assertEqual(bad_origin.exception.code,403)
            with urlopen(post(base,"/ac/api/decision",{
                "decision":"CONTINUE_REVISION","operatorAttestationId":"artist",
                "rationale":"I chose based on the film.",
                "nextQuestion":"","acknowledgedLocalOnly":True},
                ac_context["reviewToken"],token_header="X-Review-Token")) as response:
                self.assertEqual(response.status,201)
                decision=json.load(response)["receipt"]
            self.assertEqual(decision["chosenSide"],"c")
            with urlopen(base+"/api/workbench/status") as response:
                current=json.load(response)
            self.assertEqual(current["activePair"]["decision"],"CONTINUE_REVISION")
            self.assertEqual(self.bench.first.get_decision(),self.old)
            # Browser can still load the first A/B room and original media.
            with urlopen(base+"/room") as response:
                self.assertIn("Two films. One human decision.",response.read().decode())
            with urlopen(base+"/api/next/questions") as response:
                resumed=json.load(response)
            self.assertEqual(resumed["trial"]["movieSha256"],self.revision["newMovieSha256"])
        finally:
            http.shutdown();http.server_close();thread.join(timeout=3)

if __name__=="__main__":
    unittest.main()
