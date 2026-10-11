"""Native and refusal proof for explicitly selected BAND-IQ donor doors."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from bridge import band_iq as iq
from bridge import band_iq_donors as donors


def selection(op):
    return {"schema":"vidmage/band-iq-local-selection/v1",
            "operation":op,"sourceRights":"creator-authorized",
            "operatorAttestationId":"operator-selected-synthetic",
            "allowLocalExecution":True,"allowPaidProviders":False,
            "allowNetworkUpload":False}


class NativeDoorTest(unittest.TestCase):
    def test_unsafe_authority_refused(self):
        okay=selection("harvest-008h")
        donors.authorize(okay,"harvest-008h")
        for key in ("allowPaidProviders","allowNetworkUpload"):
            bad=dict(okay,**{key:True})
            with self.assertRaisesRegex(ValueError,"external authority"):
                donors.authorize(bad,"harvest-008h")
        bad=dict(okay,allowLocalExecution=False)
        with self.assertRaisesRegex(ValueError,"explicit"):
            donors.authorize(bad,"harvest-008h")
        bad=dict(okay,sourceRights="unknown")
        with self.assertRaisesRegex(ValueError,"rights"):
            donors.authorize(bad,"harvest-008h")
        with self.assertRaisesRegex(ValueError,"mismatched"):
            donors.authorize(okay,"direct-008j")

    def test_uninstalled_optional_workers_are_not_claimed(self):
        spec=donors.describe()
        self.assertEqual({v["id"] for v in spec["operations"]},
                         {"scan-008f","harvest-008h","direct-008j","material-008l"})
        self.assertEqual(len(spec["optionalFutureNotInstalled"]),4)

    @unittest.skipUnless(os.environ.get("VIDMAGE_BLENDER_ROOT") and shutil.which("ffmpeg"),
                         "requires pinned Blender checkout and FFmpeg")
    def test_real_native_ffmpeg_doctor_scan_enters_band_iq(self):
        root=os.environ["VIDMAGE_BLENDER_ROOT"]
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            video=tmp/"original.mp4"
            subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
                            "-i","color=c=black:size=128x72:rate=4:duration=8",
                            "-an","-c:v","libx264","-pix_fmt","yuv420p",
                            str(video)],check=True)
            from haunted_blender import zero_dollar_mill
            plan={"schema":zero_dollar_mill.PLAN_SCHEMA,"id":"synthetic-plan-001",
                  "targetSeconds":8.0,
                  "slugs":[
                    {"id":"slug-1","sourceAssetId":"synthetic-a","durationSeconds":4,"sourceSha256":"f"*64,"recipe":"fit"},
                    {"id":"slug-2","sourceAssetId":"synthetic-b","durationSeconds":4,"sourceSha256":"e"*64,"recipe":"fit"},
                  ]}
            source_plan=tmp/"plan.json"
            source_plan.write_text(json.dumps(plan))
            reportdir=tmp/"scan"
            res=donors.run_selected(selection("scan-008f"),
                                    blender_root=root,source=video,output=reportdir,
                                    plan=source_plan,sample_fps=4)
            self.assertEqual(res["result"]["op"],"scan-008f")
            envelope=json.loads((reportdir/"doctor.json").read_text())
            report=envelope["report"]
            self.assertEqual(report["sourceVideoSha256"],donors.sha_file(video))
            self.assertEqual(len(report["windows"]),2)
            self.assertEqual(report["coverageRatio"],1.0)
            self.assertEqual(envelope["reportSha256"],iq.digest(report))
            context={"schema":iq.INPUT,"doctorReport":report,
                     "audioObservation":None,
                     "artistAnnotations":[{
                         "windowId":report["windows"][0]["id"],
                         "kind":"deliberate-stillness",
                         "operatorAttestationId":"human:stillness-selected",
                         "sourceVideoSha256":report["sourceVideoSha256"],
                     }]}
            cycle=iq.build_cycle(context)
            self.assertTrue(iq.verify_cycle(cycle))
            self.assertNotEqual(cycle["experiment"]["candidateWindowId"],
                                report["windows"][0]["id"])
            self.assertFalse(cycle["experiment"]["requiresOwnerSelection"] is False)
            self.assertFalse(cycle["imagine"][0]["execution"])
            self.assertTrue(Path(res["receipt"]).is_file())


    @unittest.skipUnless(os.environ.get("VIDMAGE_BLENDER_ROOT") and shutil.which("ffmpeg"),
                         "requires pinned Blender checkout and FFmpeg")
    def test_real_native_harvest_material_and_paper_director_are_separate_local_acts(self):
        from PIL import Image
        from haunted_blender import scene_growth, paper_director
        root=os.environ["VIDMAGE_BLENDER_ROOT"]
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            video=tmp/"input.mp4"
            subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
                            "-i","testsrc=size=128x72:rate=8:duration=4",
                            "-an","-c:v","libx264","-pix_fmt","yuv420p",
                            str(video)],check=True)
            original_hash=donors.sha_file(video)
            image=tmp/"original.png"
            Image.new("RGB",(96,64),(50,80,115)).save(image)

            harvest=donors.run_selected(selection("harvest-008h"),
                        blender_root=root,source=video,output=tmp/"harvest")
            self.assertTrue(Path(harvest["receipt"]).is_file())
            manifest=json.loads((tmp/"harvest"/"harvest.json").read_text())
            self.assertEqual(manifest["source"]["sha256"],original_hash)
            self.assertGreater(manifest["derivativeYieldCount"],3)

            treated=donors.run_selected(selection("material-008l"),
                        blender_root=root,source=image,output=tmp/"clay.png",material="clay")
            self.assertTrue((tmp/"clay.png").is_file())
            self.assertTrue(Path(treated["receipt"]).is_file())
            self.assertNotEqual(donors.sha_file(image),donors.sha_file(tmp/"clay.png"))

            timing=scene_growth.normalize_timing({
                "schemaVersion":"0.1","id":"synthetic-four-seconds",
                "duration":4.0,"gates":[{"id":"whole","at":0,"kind":"verse","label":"synthetic"}],
            })
            native_plan=paper_director.plan(timing)
            self.assertEqual(native_plan["schema"],paper_director.PLAN_SCHEMA)
            plan_path=tmp/"director.plan.json"
            plan_path.write_text(json.dumps(native_plan))
            directed=donors.run_selected(selection("direct-008j"),
                        blender_root=root,source=video,output=tmp/"directed.mp4",
                        plan=plan_path)
            self.assertTrue(Path(directed["receipt"]).is_file())
            self.assertTrue((tmp/"directed.mp4").is_file())
            self.assertEqual(directed["result"]["outputSha256"],donors.sha_file(tmp/"directed.mp4"))
            self.assertEqual(donors.sha_file(video),original_hash,"donor actions must not mutate input")
            with self.assertRaisesRegex(ValueError,"create-only"):
                donors.run_selected(selection("direct-008j"),
                                    blender_root=root,source=video,output=tmp/"directed.mp4",
                                    plan=plan_path)


if __name__=="__main__":
    unittest.main()
