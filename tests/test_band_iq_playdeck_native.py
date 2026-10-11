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
            Image.new("RGB",(640,360),(32,82,121)).save(root/"a.png")
            Image.new("RGB",(640,360),(117,63,45)).save(root/"b.png")
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
