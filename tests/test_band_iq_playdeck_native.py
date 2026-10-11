"""BAND-IQ 003: native Playdeck Remotion branch source and same-question second renderer."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from bridge import band_iq as iq
from bridge import band_iq_film_loop as loop
from bridge import band_iq_donors as donors
from bridge import band_iq_playdeck_native as native
from bridge import scene_card_film as film


class NativePlaydeckTest(unittest.TestCase):
    def test_pinned_grammar_has_exact_six_earlier_questions(self):
        self.assertEqual(set(native.GRAMMAR),set(iq.LENSES))
        for key,tuple_fields in native.GRAMMAR.items():
            self.assertEqual(tuple_fields,iq.LENSES[key])
        self.assertEqual(native.PLAYDECK_SHA,"012186fd67f4c4ef1c6591fc5e29cb559b5a80d0")

    @unittest.skipUnless(os.environ.get("VIDMAGE_PLAYDECK_ROOT") and
                         os.environ.get("VIDMAGE_BLENDER_ROOT") and
                         os.environ.get("VIDMAGE_TOASTER_ROOT") and
                         shutil.which("ffmpeg") and shutil.which("node"),
                         "needs installed pinned Playdeck Remotion, pinned Blender, pinned Toaster")
    def test_native_remotion_render_and_other_renderer_exact_comparison(self):
        import cv2
        import numpy as np
        from haunted_blender import paper_director, scene_growth, weakest_window_doctor
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            from PIL import Image
            from PIL import ImageDraw
            for name,color in (("a.png",(32,82,121)),("b.png",(117,63,45))):
                canvas=Image.new("RGB",(640,360),color)
                draw=ImageDraw.Draw(canvas)
                for j in range(14):
                    draw.rectangle((j*43+4, j*17%195+6,j*43+28,j*17%195+110),
                                   fill=((j*29+30)%256,(j*47+75)%256,(j*19+130)%256))
                draw.ellipse((210,80,460,300),outline=(252,238,225),width=13)
                draw.line((15,15,620,345),fill=(225,240,250),width=7)
                canvas.save(root/name)
            audio=root/"song.wav"
            subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
                            "-i","sine=frequency=510:duration=4:sample_rate=22050",
                            str(audio)],check=True)
            observation=root/"obs.json"
            subprocess.run(["node","bridge/toaster_lbranch_capture.cjs",
                            "--toaster-root",os.environ["VIDMAGE_TOASTER_ROOT"],
                            "--audio",str(audio),"--out",str(observation)],
                           check=True,capture_output=True,text=True)
            obs=json.loads(observation.read_text())
            timing=scene_growth.normalize_timing({
                "schemaVersion":"0.1","id":"real-four-second-native-song",
                "duration":4.0,"gates":[{"id":"g1","at":0,"kind":"verse","label":"source"}],
            })
            plan=paper_director.plan(timing)
            cards={"schema":"vidmage/editorial-scene-cards/v1","status":"proposal-only",
                   "assets":{
                       "a":{"path":"a.png","mode":"subject","focus":[.5,.5]},
                       "b":{"path":"b.png","mode":"subject","focus":[.5,.5]},
                   },
                   "shots":[{"shotId":row["id"],
                             "assetId":"a" if n%2==0 else "b","kineticSafe":False}
                            for n,row in enumerate(plan["shots"])]}
            attrib=loop.doctor_scene_attribution_plan(plan,cards,root)
            base=root/"base.mp4"
            film.render(plan,cards,obs,audio,root,base)
            before=weakest_window_doctor.scan(base,attrib,window_seconds=2.0)
            self.assertEqual(before["coverageRatio"],1)
            self.assertEqual(donors.sha_file(base),before["sourceVideoSha256"])
            cycle=iq.build_cycle({"schema":iq.INPUT,"doctorReport":before,
                                  "audioObservation":obs,"artistAnnotations":[]})
            self.assertTrue(iq.verify_cycle(cycle))
            self.assertTrue(cycle["experiment"]["candidateWindowId"])
            proposal=cycle["imagine"][0]
            selection={
                "schema":loop.SELECTION,
                "cycleSha256":cycle["cycleSha256"],
                "proposalSha256":proposal["proposalSha256"],
                "operatorAttestationId":"explicit-creator-chooses-landscape",
                "decision":"RENDER_TRIAL",
                "allowLocalExecution":True,
                "allowPaidProviders":False,
                "allowNetworkUpload":False,
                "sourceVideoSha256":before["sourceVideoSha256"],
                "paperPlanSha256":iq.digest(plan),
                "sceneCardsSha256":iq.digest(cards),
                "audioObservationSha256":iq.digest(obs),
                "audioSha256":donors.sha_file(audio),
                "assetBindings":loop.exact_asset_bindings(cards,root),
            }
            props,hashes,_,audio_uri=native.convert_to_native_props(
                cycle,before,selection,plan,cards,obs,audio,root,base)
            self.assertEqual(hashes[audio_uri],donors.sha_file(audio))
            self.assertEqual(props["plan"]["metadata"].get("studioFranken"),None)
            scoped=[e for e in props["plan"]["events"]
                    if isinstance(e.get("params",{}).get("franken"),dict)]
            self.assertEqual(len(scoped),1)
            self.assertAlmostEqual(scoped[0]["at"],proposal["targetStart"])
            self.assertAlmostEqual(scoped[0]["duration"],
                                   proposal["targetEnd"]-proposal["targetStart"])
            self.assertEqual(props["plan"]["fps"],12)
            self.assertEqual(len(props["deck"]["cards"]),len(cards["shots"]))

            vidmage_movie=root/"vidmage.mp4"
            vidmage_record,_=loop.render_selected(
                cycle,before,selection,plan,cards,obs,audio,root,base,vidmage_movie)
            self.assertNotEqual(donors.sha_file(vidmage_movie),donors.sha_file(base))
            vidmage_receipt=json.loads(vidmage_movie.with_suffix(".receipt.json").read_text())
            self.assertAlmostEqual(vidmage_receipt["cinematicSelection"]["targetStart"],
                                   proposal["targetStart"])

            remotion_movie=root/"native-playdeck.mp4"
            receipt,receipt_path=native.render_native(
                cycle=cycle,before=before,selection=selection,plan=plan,cards=cards,
                observation=obs,audio=audio,asset_root=root,
                baseline_movie=base,playdeck_root=os.environ["VIDMAGE_PLAYDECK_ROOT"],
                output=remotion_movie)
            self.assertTrue(remotion_movie.is_file())
            self.assertTrue(Path(receipt_path).is_file())
            self.assertTrue(receipt["nativePlaydeckRendering"])
            self.assertEqual(receipt["nativePlaydeckSourceSha"],native.PLAYDECK_SHA)
            self.assertEqual(receipt["studio011Lens"],proposal["lensId"])
            self.assertNotEqual(receipt["actualOutputSha256"],
                                vidmage_record["performedVideoSha256"])
            self.assertEqual(len(receipt["nativeStreams"]),2)
            self.assertFalse(receipt["automaticKeep"])

            pair,pair_path=native.compare_native_pair(
                cycle=cycle,selection=selection,
                vidmage_film_record=vidmage_record,vidmage_movie=vidmage_movie,
                playdeck_receipt=receipt,playdeck_movie=remotion_movie,
                output_dir=root/"paired")
            self.assertTrue(Path(pair_path).is_file())
            self.assertTrue(pair["sameSourceAudio"])
            self.assertTrue(pair["sameSourceImageSet"])
            self.assertTrue(pair["sameOperatorSelectedQuestion"])
            self.assertFalse(pair["automaticallyKept"])
            self.assertFalse(pair["samePixelOutput"])
            self.assertIsNone(pair["aestheticallyEquivalent"])

            # BAND-IQ 004: reopen the ACTUAL native two-film performance,
            # submit one attested author decision, and recheck source bytes.
            from bridge import band_iq_review as review
            paths={}
            for name,body in (
                ("cycle",cycle),
                ("selection",selection),
                ("vidmage_record",vidmage_record),
            ):
                target=root/(f"review-{name}.json")
                target.write_text(json.dumps(body))
                paths[name]=target
            paths["playdeck_receipt"]=Path(receipt_path)
            paths["vidmage_movie"]=vidmage_movie
            paths["playdeck_movie"]=remotion_movie
            paths["record_dir"]=root/"actual-movie-human-reviews"
            human_bench=review.ReviewBench(**paths)
            self.assertEqual(human_bench.state()["status"],"awaiting-human-review")
            chosen=human_bench.commit({
                "decision":"KEEP_PLAYDECK",
                "operatorAttestationId":"synthetic-proof-author-explicitly-chooses-b",
                "rationale":"Native card staging is the intended test performance.",
                "nextQuestion":"",
                "acknowledgedTrialOnly":True,
            })
            self.assertEqual(chosen["chosenFilmSha256"],donors.sha_file(remotion_movie))
            self.assertFalse(chosen["publicationAuthorized"])
            self.assertEqual(review.ReviewBench(**paths).get_decision(),chosen)
            with self.assertRaisesRegex(ValueError,"already recorded"):
                human_bench.commit({
                    "decision":"SCRAPE_BOTH",
                    "operatorAttestationId":"synthetic-opposite",
                    "rationale":"",
                    "nextQuestion":"",
                    "acknowledgedTrialOnly":True,
                })

            # BAND-IQ 005: a DIFFERENT deliberate 004 review asks a real
            # next question. Three candidate experiment types are only
            # proposals until an independent named second creator action.
            from bridge import band_iq_next_question as nxt
            next_paths={**paths,"record_dir":root/"actual-movie-next-question"}
            next_bench=review.ReviewBench(**next_paths)
            another=next_bench.commit({
                "decision":"ANOTHER_EXPERIMENT",
                "operatorAttestationId":"creator-explicit-next-question",
                "rationale":"Try a different image in the first authored shot.",
                "nextQuestion":"What if the opening shot used the other image instead?",
                "acknowledgedTrialOnly":True,
            })
            self.assertTrue(another["nextQuestion"])
            suggestions=nxt.question_set(next_bench,plan,cards,obs,audio,root)
            self.assertEqual(len(suggestions["proposals"]),3)
            self.assertTrue(all(x["status"]=="proposal-only"
                                for x in suggestions["proposals"]))
            self.assertEqual(suggestions["humanQuestionVerbatim"],
                             another["nextQuestion"])
            self.assertFalse(suggestions["automaticExecution"])
            proposals_path=iq.write_once(root/"next-questions",
                                         suggestions,"questionSetSha256")
            self.assertTrue(Path(proposals_path).is_file())
            swap=next(x for x in suggestions["proposals"]
                      if x["kind"]=="SWAP_CARD")
            shot_id=swap["eligibleShotIds"][0]
            replacement=swap["eligibleReplacementAssetIdsByShot"][shot_id][0]
            second_act={
                "schema":nxt.AUTH,
                "questionSetSha256":suggestions["questionSetSha256"],
                "proposalSha256":swap["proposalSha256"],
                "operatorAttestationId":"creator-selected-first-card-replacement",
                "decision":"RENDER_ONE_LOCAL_TRIAL",
                "shotId":shot_id,
                "replacementAssetId":replacement,
                "newFocus":None,
                "newLensId":None,
                "allowLocalExecution":True,
                "allowPaidProviders":False,
                "allowNetworkUpload":False,
            }
            original_card_hash=iq.digest(cards)
            sourceA=donors.sha_file(vidmage_movie)
            sourceB=donors.sha_file(remotion_movie)
            revision,revision_path=nxt.run_trial(
                next_bench,suggestions,second_act,plan,cards,obs,audio,root,
                root/"revised-shot.mp4")
            self.assertTrue(Path(revision_path).is_file())
            self.assertEqual(revision["experimentKind"],"SWAP_CARD")
            self.assertTrue(revision["newMediaDifferentFromPriorVidmage"])
            self.assertEqual(revision["humanQuestionVerbatim"],another["nextQuestion"])
            self.assertFalse(revision["humanKeep"])
            self.assertFalse(revision["publish"])
            self.assertEqual(donors.sha_file(vidmage_movie),sourceA)
            self.assertEqual(donors.sha_file(remotion_movie),sourceB)
            self.assertEqual(iq.digest(cards),original_card_hash)
            reopened=nxt.reopen_revision(revision_path)
            self.assertEqual(reopened["status"],"verified-editable-snapshot")
            self.assertEqual(reopened["movieSha256"],revision["newMovieSha256"])
            self.assertEqual(reopened["editorCards"]["shots"][0]["assetId"],replacement)
            self.assertEqual(reopened["paperPlan"],plan)
            self.assertEqual(reopened["toasterObservation"],obs)
            with self.assertRaisesRegex(ValueError,"create-only"):
                nxt.run_trial(next_bench,suggestions,second_act,
                              plan,cards,obs,audio,root,root/"revised-shot.mp4")
            forged=dict(second_act,allowPaidProviders=True)
            with self.assertRaisesRegex(ValueError,"authorization"):
                nxt.run_trial(next_bench,suggestions,forged,
                              plan,cards,obs,audio,root,root/"forged.mp4")
            forged=dict(second_act,replacementAssetId=cards["shots"][0]["assetId"])
            with self.assertRaisesRegex(ValueError,"independently authorized"):
                nxt.run_trial(next_bench,suggestions,forged,
                              plan,cards,obs,audio,root,root/"unchanged.mp4")
            forged_q=dict(suggestions,humanQuestionVerbatim="AI invented new question")
            with self.assertRaisesRegex(ValueError,"question or source"):
                nxt.run_trial(next_bench,forged_q,second_act,
                              plan,cards,obs,audio,root,root/"tampered-question.mp4")
            # One next-question trial does not rewrite the first review
            # or turn the original 004 KEEP B into a disposable artifact.
            self.assertEqual(human_bench.get_decision(),chosen)
            self.assertEqual(next_bench.get_decision(),another)

            # BAND-IQ 006: *actual* native 008f rescans both real films,
            # source-bound to each DIFFERENT editor card attribution. Pixel
            # deltas refer to the authored swap; no artist evaluation follows.
            from bridge import band_iq_question_lab as question_lab
            lab_result,lab_path=question_lab.observe(
                next_bench,revision,plan,cards,obs,audio,root,
                os.environ["VIDMAGE_BLENDER_ROOT"],root/"question-laboratory")
            self.assertTrue(Path(lab_path).is_file())
            self.assertEqual(lab_result["humanQuestionVerbatim"],another["nextQuestion"])
            self.assertEqual(lab_result["sourceRevisionSha256"],revision["revisionSha256"])
            self.assertTrue(lab_result["realNativeDoctor"])
            self.assertFalse(lab_result["native008eExecution"])
            self.assertEqual(lab_result["nativeDoctorCoverageOriginal"],1)
            self.assertEqual(lab_result["nativeDoctorCoverageRevision"],1)
            self.assertEqual(lab_result["humanChosenOperation"],"SWAP_CARD")
            self.assertEqual(len(lab_result["possibleNextQuestions"]),3)
            self.assertIsNone(lab_result["artisticJudgment"])
            self.assertFalse(lab_result["automaticKeep"])
            self.assertFalse(lab_result["automaticExecution"])
            self.assertFalse(lab_result["newExperimentAuthorized"])
            self.assertEqual(lab_result["actualOldFilmSha256"],sourceA)
            self.assertEqual(lab_result["actualNewFilmSha256"],revision["newMovieSha256"])
            self.assertTrue(any(w["pixelMeanAbsoluteDifference"]>0.01
                                for w in lab_result["windows"]))
            self.assertTrue(any(w["operatorEditOverlapsThisWindow"]
                                for w in lab_result["windows"]))
            reopened_lab=question_lab.reopen(
                lab_path,None,revision,next_bench)
            self.assertEqual(reopened_lab["observationSha256"],
                             lab_result["observationSha256"])
            with self.assertRaisesRegex(ValueError,"source film or linked question changed"):
                bad_revision=dict(revision,newMovieSha256="0"*64)
                question_lab.reopen(lab_path,None,bad_revision,next_bench)
            tampered=dict(revision,humanQuestionVerbatim="model hallucinated artistic question")
            with self.assertRaisesRegex(ValueError,"evidence identity"):
                question_lab.observe(next_bench,tampered,plan,cards,obs,audio,
                    root,os.environ["VIDMAGE_BLENDER_ROOT"],root/"bad-question-lab")
            self.assertEqual(next_bench.get_decision(),another)

            # 005 human-facing localhost path: obtain real proposals and
            # separately authorize a second operation over HTTP. The native
            # Playdeck/VidMage evidence remains source-pinned and unchanged.
            import contextlib
            import io
            import threading
            from urllib.request import Request,urlopen
            from urllib.error import HTTPError
            plan_file=root/"next-operator-plan.json"
            cards_file=root/"next-operator-cards.json"
            plan_file.write_text(json.dumps(plan))
            cards_file.write_text(json.dumps(cards))
            next_bench.enable_next_sources(plan=plan_file,cards=cards_file,
                observation=observation,audio=audio,asset_root=root)
            self.assertTrue(next_bench.state()["constraints"]["nextQuestionToolsConfigured"])
            next_bench.next_blender_root=os.environ["VIDMAGE_BLENDER_ROOT"]
            self.assertTrue(next_bench.state()["constraints"]["nativeQuestionDoctorConfigured"])
            with contextlib.redirect_stdout(io.StringIO()):
                server=review.serve(next_bench,port=0)
            runner=threading.Thread(target=server.serve_forever,daemon=True)
            runner.start()
            try:
                baseurl=f"http://127.0.0.1:{server.server_port}"
                with urlopen(baseurl+"/api/next/questions") as response:
                    next_page=json.load(response)
                self.assertTrue(next_page["ok"])
                self.assertEqual(next_page["questions"]["humanQuestionVerbatim"],
                                 another["nextQuestion"])
                lens=next(p for p in next_page["questions"]["proposals"]
                          if p["kind"]=="CHANGE_LENS")
                lens_authorization={
                    "schema":nxt.AUTH,
                    "questionSetSha256":next_page["questions"]["questionSetSha256"],
                    "proposalSha256":lens["proposalSha256"],
                    "operatorAttestationId":"author-explicit-second-http-trial",
                    "decision":"RENDER_ONE_LOCAL_TRIAL",
                    "shotId":None,
                    "replacementAssetId":None,
                    "newFocus":None,
                    "newLensId":lens["eligibleLensIds"][0],
                    "allowLocalExecution":True,
                    "allowPaidProviders":False,
                    "allowNetworkUpload":False,
                }
                body=json.dumps({"authorization":lens_authorization}).encode("utf8")
                bad=Request(baseurl+"/api/next/execute",data=body,headers={
                    "Content-Type":"application/json",
                    "Origin":"https://malicious.example",
                    "X-Review-Token":next_bench.token,
                })
                with self.assertRaises(HTTPError) as denied:
                    urlopen(bad)
                self.assertEqual(denied.exception.code,403)
                self.assertIsNone(next_bench.next_result)
                good=Request(baseurl+"/api/next/execute",data=body,headers={
                    "Content-Type":"application/json",
                    "Origin":baseurl,
                    "X-Review-Token":next_bench.token,
                })
                with urlopen(good) as response:
                    self.assertEqual(response.status,201)
                    trial=json.load(response)["trial"]
                self.assertTrue(Path(trial["film"]).is_file())
                opened=nxt.reopen_revision(trial["revisionRecord"])
                self.assertEqual(opened["movieSha256"],trial["movieSha256"])
                with urlopen(Request(baseurl+"/media/next",
                                     headers={"Range":"bytes=0-63"})) as response:
                    self.assertEqual(response.status,206)
                    self.assertEqual(response.read(),
                                     Path(trial["film"]).read_bytes()[:64])
                with self.assertRaises(HTTPError) as repeated:
                    urlopen(good)
                self.assertEqual(repeated.exception.code,409)
                self.assertEqual(next_bench.get_decision(),another)
                self.assertEqual(donors.sha_file(vidmage_movie),sourceA)
                self.assertEqual(donors.sha_file(remotion_movie),sourceB)
                # 006 in-room actual measurement is a SECOND explicit POST,
                # not silently triggered by the render or the question.
                self.assertIsNone(next_bench.last_observation)
                analysis=json.dumps({"inspectActualFilms":True}).encode("utf8")
                unauthorized=Request(baseurl+"/api/next/observe",
                                     data=analysis,headers={
                       "Content-Type":"application/json",
                       "Origin":"https://outside.example",
                       "X-Review-Token":next_bench.token})
                with self.assertRaises(HTTPError) as refused:
                    urlopen(unauthorized)
                self.assertEqual(refused.exception.code,403)
                self.assertIsNone(next_bench.last_observation)
                authorized=Request(baseurl+"/api/next/observe",
                                   data=analysis,headers={
                       "Content-Type":"application/json","Origin":baseurl,
                       "X-Review-Token":next_bench.token})
                with urlopen(authorized) as response:
                    self.assertEqual(response.status,200)
                    observed=json.load(response)["observation"]
                self.assertEqual(observed["humanChosenOperation"],"CHANGE_LENS")
                self.assertEqual(observed["sourceReviewSha256"],another["reviewSha256"])
                self.assertEqual(observed["actualOldFilmSha256"],sourceA)
                self.assertTrue(observed["realNativeDoctor"])
                self.assertFalse(observed["automaticKeep"])
                self.assertIsNone(observed["artisticJudgment"])
                self.assertEqual(len(observed["possibleNextQuestions"]),3)
                self.assertEqual(donors.sha_file(remotion_movie),sourceB)
            finally:
                server.shutdown()
                server.server_close()
                runner.join(timeout=3)

            # Proof of non-interchangeable receipts; no silent same-song or
            # silent selection substitution.
            with self.assertRaisesRegex(ValueError,"source material"):
                fake=dict(receipt,inputAssetSha256={"asset://band-iq-003/source-audio":
                                                     donors.sha_file(audio),
                                                     "asset://band-iq-003/a":"0"*64})
                fake["receiptSha256"]=iq.digest({k:v for k,v in fake.items()
                                                 if k!="receiptSha256"})
                native.compare_native_pair(cycle=cycle,selection=selection,
                    vidmage_film_record=vidmage_record,vidmage_movie=vidmage_movie,
                    playdeck_receipt=fake,playdeck_movie=remotion_movie,
                    output_dir=root/"bad")
            with self.assertRaisesRegex(ValueError,"create-only"):
                native.render_native(cycle=cycle,before=before,selection=selection,
                    plan=plan,cards=cards,observation=obs,audio=audio,asset_root=root,
                    baseline_movie=base,
                    playdeck_root=os.environ["VIDMAGE_PLAYDECK_ROOT"],
                    output=remotion_movie)
            tampered=dict(selection,allowPaidProviders=True)
            with self.assertRaisesRegex(ValueError,"cost"):
                native.convert_to_native_props(
                    cycle,before,tampered,plan,cards,obs,audio,root,base)
            tampered=dict(selection,proposalSha256="0"*64)
            with self.assertRaisesRegex(ValueError,"proposal"):
                native.convert_to_native_props(
                    cycle,before,tampered,plan,cards,obs,audio,root,base)

if __name__=="__main__":
    unittest.main()
