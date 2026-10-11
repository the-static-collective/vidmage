"""BAND-IQ 002: real creator-chosen camera trial, source-true parts/materials, native scan loop."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from bridge import band_iq as iq
from bridge import band_iq_donors as donor
from bridge import band_iq_film_loop as loop
from bridge import scene_card_film as film

def authorize_selection(cycle,before,proposal,plan,cards,obs,audio,root):
    return {
        "schema":loop.SELECTION,
        "cycleSha256":cycle["cycleSha256"],
        "proposalSha256":proposal["proposalSha256"],
        "operatorAttestationId":"creator-selection-of-synthetic-test",
        "decision":"RENDER_TRIAL",
        "allowLocalExecution":True,"allowPaidProviders":False,
        "allowNetworkUpload":False,
        "sourceVideoSha256":before["sourceVideoSha256"],
        "paperPlanSha256":iq.digest(plan),
        "sceneCardsSha256":iq.digest(cards),
        "audioObservationSha256":iq.digest(obs),
        "audioSha256":donor.sha_file(audio),
        "assetBindings":loop.exact_asset_bindings(cards,root),
    }

class BandIQ002PureTest(unittest.TestCase):
    def test_cinematic_modes_all_distinct_without_semantic_vision(self):
        import numpy as np
        base=np.zeros((48,84,3),dtype=np.uint8)
        base[14:28,20:52,:]=200
        hashes=set()
        for camera in film.CAMERAS:
            out=film.selected_camera(base,camera,3.61,0)
            self.assertEqual(out.shape,base.shape)
            hashes.add(iq.digest(out.tolist()))
        self.assertEqual(len(hashes),6)

    def test_doctor_scene_adapter_truthful_and_source_pinned(self):
        with tempfile.TemporaryDirectory() as td:
            import cv2
            import numpy as np
            root=Path(td)
            cv2.imwrite(str(root/"a.png"),np.full((48,84,3),80,dtype=np.uint8))
            cards={"schema":"vidmage/editorial-scene-cards/v1","status":"proposal-only",
                   "assets":{"a":{"path":"a.png","focus":[.5,.5],"mode":"subject"}},
                   "shots":[{"shotId":"shot-0001","assetId":"a","kineticSafe":False}]}
            paper={"schema":"haunted-blender/paper-director-plan/v1","id":"native-synthetic",
                   "durationSeconds":3.0,
                   "shots":[{"id":"shot-0001","start":0.0,"end":3.0}]}
            plan=loop.doctor_scene_attribution_plan(paper,cards,root)
            self.assertEqual(plan["slugs"][0]["sourceSha256"],donor.sha_file(root/"a.png"))
            self.assertFalse(plan["vidmageAdapter"]["nativeBlender008eExecution"])
            self.assertEqual(plan["targetSeconds"],3.0)
            cards["shots"][0]["assetId"]="MISSING"
            with self.assertRaisesRegex(ValueError,"shot binding"):
                loop.doctor_scene_attribution_plan(paper,cards,root)

    @unittest.skipUnless(os.environ.get("VIDMAGE_BLENDER_ROOT") and
                         os.environ.get("VIDMAGE_TOASTER_ROOT") and
                         shutil.which("ffmpeg") and shutil.which("node"),
                         "requires pinned Toaster and Blender with actual FFmpeg")
    def test_native_four_donor_executable_full_song_trial_and_rescore(self):
        from PIL import Image
        from haunted_blender import parts_harvester, material_surface, scene_growth
        from haunted_blender import paper_director, weakest_window_doctor
        blender_root=Path(os.environ["VIDMAGE_BLENDER_ROOT"])
        toaster_root=Path(os.environ["VIDMAGE_TOASTER_ROOT"])
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source_video=root/"owned-bit.mp4"
            subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
                            "-i","testsrc2=size=128x72:rate=8:duration=4",
                            "-an","-c:v","libx264","-pix_fmt","yuv420p",str(source_video)],
                           check=True)
            owned_source_hash=donor.sha_file(source_video)

            harvest=parts_harvester.harvest(source_video,root/"parts",still_count=3)
            native_still=next(item for item in harvest["artifacts"] if item["kind"]=="still")
            self.assertEqual(native_still["sourceSha256"],owned_source_hash)
            material=material_surface.materialize_asset(
                native_still["path"],root/"clay.png","clay")
            Image.new("RGB",(220,124),(34,72,110)).save(root/"quiet.png")
            cards_assets={
                "clay":{"path":"clay.png","mode":"subject","focus":[.5,.5]},
                "quiet":{"path":"quiet.png","mode":"protect-text","focus":[.5,.5]},
            }
            audio=root/"music.wav"
            subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
                            "-i","sine=frequency=350:duration=4:sample_rate=22050",
                            str(audio)],check=True)
            obs=root/"toaster.json"
            subprocess.run(["node","bridge/toaster_lbranch_capture.cjs",
                            "--toaster-root",str(toaster_root),
                            "--audio",str(audio),"--out",str(obs)],
                           check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            observation=json.loads(obs.read_text())
            iq.validate_audio(observation)
            self.assertEqual(observation["sourceAudioSha256"],donor.sha_file(audio))

            timing=scene_growth.normalize_timing({
                "schemaVersion":"0.1","id":"four-second-native-director",
                "duration":4.0,"gates":[{"id":"only","at":0,"kind":"verse","label":"synthetic-only"}],
            })
            plan=paper_director.plan(timing)
            self.assertGreaterEqual(len(plan["shots"]),2)
            cards={"schema":"vidmage/editorial-scene-cards/v1","status":"proposal-only",
                   "assets":cards_assets,
                   "shots":[{"shotId":shot["id"],
                             "assetId":"clay" if i%2==0 else "quiet",
                             "kineticSafe":False}
                            for i,shot in enumerate(plan["shots"])]}
            source_plan=loop.doctor_scene_attribution_plan(plan,cards,root)
            self.assertFalse(source_plan["vidmageAdapter"]["nativeBlender008eExecution"])
            self.assertEqual(source_plan["vidmageAdapter"]["sceneCardsSha256"],iq.digest(cards))

            base=root/"unmodified.mp4"
            base_receipt=film.render(plan,cards,observation,audio,root,base)
            self.assertFalse(base_receipt["humanKeep"])
            before=weakest_window_doctor.scan(base,source_plan,window_seconds=2.0)
            self.assertEqual(before["sourceVideoSha256"],donor.sha_file(base))
            self.assertGreater(before["coverageRatio"],.99)

            context={"schema":iq.INPUT,"doctorReport":before,
                     "audioObservation":observation,"artistAnnotations":[]}
            cycle=iq.build_cycle(context)
            iq.verify_cycle(cycle)
            self.assertIsNotNone(cycle["experiment"]["candidateWindowId"])
            proposal=cycle["imagine"][0]
            selection=authorize_selection(cycle,before,proposal,plan,cards,observation,audio,root)
            lineage={"schema":loop.LINEAGE,"harvest":harvest,
                     "materialization":material,"boundAssetId":"clay",
                     "selectedHarvestArtifactSha256":native_still["sha256"]}
            lineproof=loop.check_lineage(lineage,selection["assetBindings"])
            self.assertEqual(lineproof["harvestSourceSha256"],owned_source_hash)
            self.assertEqual(lineproof["materialOutputSha256"],donor.sha_file(root/"clay.png"))

            # No source asset or scene instruction changes across baseline and trial:
            # only the specifically chosen camera grammar changes.
            performed=root/"survey.mp4"
            film_record,receipt_path=loop.render_selected(
                cycle,before,selection,plan,cards,observation,audio,root,base,performed,
                lineage=lineage)
            self.assertTrue(Path(receipt_path).is_file())
            self.assertTrue(performed.is_file())
            self.assertNotEqual(film_record["performedVideoSha256"],
                                before["sourceVideoSha256"])
            self.assertEqual(film_record["chosenLens"],"landscape")
            self.assertFalse(film_record["playdeckDirectExecution"])
            self.assertFalse(film_record["humanKeep"])
            self.assertEqual(film_record["nativeHarvestMaterialLineage"]["boundAssetId"],"clay")

            after=weakest_window_doctor.scan(performed,source_plan,window_seconds=2.0)
            film_receipt=json.loads(performed.with_suffix(".receipt.json").read_text())
            reviewed,review_path=loop.compare_selected(
                cycle,before,after,film_record,film_receipt,performed,root/"reviews")
            self.assertTrue(Path(review_path).is_file())
            self.assertIsNone(reviewed["doctorComparison"]["humanReview"])
            self.assertFalse(reviewed["automaticKeep"])
            self.assertEqual(reviewed["trialVideoSha256"],donor.sha_file(performed))
            self.assertEqual(donor.sha_file(source_video),owned_source_hash)
            self.assertTrue(root.joinpath("clay.png").is_file())

            # Selection and evidence refusal, before any second video is generated.
            forged=dict(selection,proposalSha256="f"*64)
            with self.assertRaisesRegex(ValueError,"cinematic proposal"):
                loop.validate_selection(cycle,before,forged,plan,cards,observation,
                                        audio,root,base,lineage)
            forged=dict(selection,allowPaidProviders=True)
            with self.assertRaisesRegex(ValueError,"cost"):
                loop.validate_selection(cycle,before,forged,plan,cards,observation,
                                        audio,root,base,lineage)
            forged=dict(selection,assetBindings={**selection["assetBindings"],"clay":"0"*64})
            with self.assertRaisesRegex(ValueError,"source bytes changed"):
                loop.validate_selection(cycle,before,forged,plan,cards,observation,
                                        audio,root,base,lineage)
            bad_lineage=dict(lineage,materialization=dict(material,outputSha256="0"*64))
            with self.assertRaisesRegex(ValueError,"donor identity mismatch"):
                loop.check_lineage(bad_lineage,selection["assetBindings"])
            with self.assertRaisesRegex(ValueError,"create-only"):
                loop.render_selected(cycle,before,selection,plan,cards,observation,
                                     audio,root,base,performed,lineage=lineage)
            with self.assertRaisesRegex(ValueError,"exact performed film"):
                loop.compare_selected(cycle,before,before,film_record,film_receipt,
                                      performed,root/"bad")
            # Valid output from independent alternate camera means genuinely different bytes.
            secondproposal=cycle["imagine"][3]
            secondsel=authorize_selection(cycle,before,secondproposal,plan,cards,
                                          observation,audio,root)
            second, _=loop.render_selected(cycle,before,secondsel,plan,cards,
                                            observation,audio,root,base,root/"sigil.mp4",
                                            lineage=lineage)
            self.assertNotEqual(second["performedVideoSha256"],
                                film_record["performedVideoSha256"])

if __name__=="__main__":
    unittest.main()
